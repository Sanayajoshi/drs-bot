import logging
import asyncio
import discord
from discord.ext import commands
import config
from services.thread_service import ThreadService
from services.i18n import get as t
from datetime import datetime, timezone

logger = logging.getLogger("thread_cog")
BELL_TIMEOUT_MINS  = 15
THREAD_ARCHIVE_HRS = 24

EMOJI_GENESIS = "<:Genesis:1519930122566635652>"
EMOJI_ENRICH  = "<:Enrich:1519930167005413466>"
EMOJI_RSE     = "<:ModTRSE:1256962175398842399>"
EMOJI_LOW     = "<:modlow:1490529960899772516>"
EMOJI_LOW_GEN = "<:lowgenesis:1521752341865299978>"
EMOJI_LOW_ENR = "<:lowenrich:1521713961601339402>"


def _format_timedelta(expires_at: datetime) -> str:
    """Return a human-friendly remaining time string, e.g. '2h 15m'."""
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = expires_at - now
    total_secs = max(0, int(delta.total_seconds()))
    hours, remainder = divmod(total_secs, 3600)
    mins = remainder // 60
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


class ThreadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.thread_service = ThreadService(bot.db)

    def _lang(self, guild_id: int) -> str:
        server = self.bot.db.get_server(guild_id)
        return server.get("language", "en") if server else "en"

    # ------------------------------------------------------------------
    # Thread creation — only in the guild each participant queued from
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_drs_create_threads(self, match_id: int, drs_level: int, participants: list[dict]):
        participant_ids = [p["discord_id"] for p in participants]

        # queue_guild_id is now stored on match_participants — reliable after queue deletion
        queue_guild_map = self.bot.db.get_participant_queue_guilds(participant_ids)

        # Group participants by the guild they queued from (with per-player fallback)
        guild_to_pids: dict[int, list[int]] = {}
        for pid in participant_ids:
            g = queue_guild_map.get(pid)
            if not g:
                guilds = self.bot.db.get_user_guilds(pid)
                g = guilds[0] if guilds else None
            if g:
                guild_to_pids.setdefault(g, []).append(pid)

        # discord_id → corp name (the guild name they queued from)
        id_to_corp: dict[int, str] = {}
        for pid in participant_ids:
            g_id = queue_guild_map.get(pid)
            if g_id:
                g = self.bot.get_guild(g_id)
                id_to_corp[pid] = g.name if g else "Unknown"
            else:
                guilds = self.bot.db.get_user_guilds(pid)
                g = self.bot.get_guild(guilds[0]) if guilds else None
                id_to_corp[pid] = g.name if g else "Unknown"

        # GEN/ENR assignment — all players tied at the highest level get the role icon
        gen_players = [p for p in participants if p.get("genesis_level") is not None]
        enr_players = [p for p in participants if p.get("enrich_level") is not None]

        gen_best_ids: set[int] = set()
        enr_best_ids: set[int] = set()

        if gen_players:
            max_gen = max(p["genesis_level"] for p in gen_players)
            gen_best_ids = {p["discord_id"] for p in gen_players if p["genesis_level"] == max_gen}

        if enr_players:
            max_enr = max(p["enrich_level"] for p in enr_players)
            enr_best_ids = {p["discord_id"] for p in enr_players if p["enrich_level"] == max_enr}

        # Fetch active corp bonuses once for all threads
        #active_bonuses = self.bot.db.get_active_corp_bonuses()

        created_threads: list[dict] = []

        for guild_id, present_ids in guild_to_pids.items():
            server  = self.bot.db.get_server(guild_id)
            if not server or not server.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(server["notification_channel_id"])
            if not channel:
                continue

            lang        = server.get("language", "en")
            mentions    = " ".join(f"<@{uid}>" for uid in present_ids)
            thread_name = f"DRS{drs_level} Match #{match_id}"

            try:
                thread = await channel.create_thread(
                    name=thread_name,
                    type=discord.ChannelType.public_thread,
                )

                match_embed = self._build_match_embed(
                    match_id, drs_level, participants, id_to_corp,
                    gen_best_ids, enr_best_ids, lang
                )
                bell_view = self.thread_service.build_bell_view(match_id)

                proceed = t(lang, "match_proceed", level=drs_level)

                # Build bonus embed if there are active bonuses
                bonus_embed = self._build_bonus_embed(lang)
                #bonus_embed = self._build_bonus_embed(active_bonuses, lang)

                embeds = [match_embed]
                if bonus_embed:
                    embeds.append(bonus_embed)

                await thread.send(
                    content=f"{mentions}\n{proceed}",
                    embeds=embeds,
                    view=bell_view,
                )

                self.bot.db.save_match_thread(match_id, guild_id, thread.id)
                created_threads.append({"guild_id": guild_id, "thread_id": thread.id, "lang": lang})
                logger.info(f"Created thread {thread.id} in guild {guild_id} for match {match_id}")

            except discord.Forbidden:
                logger.error(f"Missing permission to create thread in guild {guild_id}")
            except Exception as e:
                logger.error(f"Thread creation failed for guild {guild_id}: {e}", exc_info=True)

        if created_threads:
            self.bot.loop.create_task(self._remove_bell(match_id, created_threads))
            self.bot.loop.create_task(self._archive_thread(match_id, created_threads))
            self.bot.loop.create_task(self._schedule_feedback(match_id, created_threads))

    # ------------------------------------------------------------------
    # Match embed
    # ------------------------------------------------------------------

    def _build_match_embed(
        self,
        match_id: int,
        drs_level: int,
        participants: list[dict],
        id_to_corp: dict[int, str],
        gen_best_ids: set[int],
        enr_best_ids: set[int],
        lang: str,
    ) -> discord.Embed:
        embed = discord.Embed(
            title=t(lang, "match_title", level=drs_level, match_id=match_id),
            color=discord.Color.dark_red()
        )

        rows = []
        for p in participants:
            pid     = p["discord_id"]
            name    = p["display_name"][:10]
            corp    = id_to_corp.get(pid, "Unknown")[:10]
            gen_lvl = p.get("genesis_level")
            enr_lvl = p.get("enrich_level")
            rse_lvl = p.get("modt_level")

            gen_str = str(gen_lvl) if gen_lvl is not None else "?"
            enr_str = str(enr_lvl) if enr_lvl is not None else "?"
            rse_str = str(rse_lvl) if rse_lvl is not None else "?"

            gen_icon = EMOJI_GENESIS if pid in gen_best_ids else EMOJI_LOW_GEN
            enr_icon = EMOJI_ENRICH  if pid in enr_best_ids else EMOJI_LOW_ENR

            row = f"**`{corp:<10}`**` {name:<10}` {gen_icon}`{gen_str:<2}`  {enr_icon}`{enr_str:<2}`  {EMOJI_RSE}`{rse_str:<2}`"
            rows.append(row)

        embed.add_field(name="\u200b", value="\n".join(rows), inline=False)

        missing = [p for p in participants if p.get("genesis_level") is None or p.get("enrich_level") is None]
        if missing:
            names = ", ".join(p["display_name"] for p in missing)
            key   = "match_warning_multi" if len(missing) > 1 else "match_warning"
            embed.add_field(name="\u200b", value=f"-# {t(lang, key, names=names)}", inline=False)

        embed.set_footer(text=t(lang, "match_footer"))
        return embed

    # ------------------------------------------------------------------
    # Corp bonus embed — top 3 active bonuses, warns if < 1 hour
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Corp bonus embed — from auto-fetch system
    # ------------------------------------------------------------------

    def _build_bonus_embed(self, lang: str) -> discord.Embed | None:
        """Build bonus embed from auto-fetch system."""
        # Get bonuses from the new tracked_corps table
        corps = self.bot.bonus_service.get_active_bonuses()

        if not corps:
            return None

        embed = discord.Embed(
            title="🌟 Active Corporation Bonuses",
            color=discord.Color.gold(),
        )

        lines = []
        for corp in corps[:5]:  # Show top 5
            lines.append(
                f"**{corp['corp_name']}** — **{corp['bonus_pct']}%** bonus"
            )

        embed.description = "\n".join(lines)

        if corps:
            last_updated = corps[0]['last_fetched']
            if last_updated:
                embed.set_footer(text=f"Last updated: {last_updated[:16]}")

        return embed
    def _build_bonus_embed1(self, active_bonuses: list[dict], lang: str) -> discord.Embed | None:
        if not active_bonuses:
            return None

        top3 = active_bonuses[:3]
        embed = discord.Embed(
            title="🌟 Active Corp Bonuses",
            color=discord.Color.gold(),
        )

        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        lines = []
        for b in top3:
            expires_at = b["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            remaining_secs = (expires_at - now).total_seconds()
            time_str = _format_timedelta(expires_at)
            warning  = " ⚠️ expiring soon!" if remaining_secs < 3600 else ""
            lines.append(
                f"**{b['corp_name']}** — **{b['bonus_pct']}%** bonus · expires in {time_str}{warning}"
            )

        embed.description = "\n".join(lines)
        return embed

    # ------------------------------------------------------------------
    # Bell ping
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("bell_ping_"):
            return
        match_id = int(custom_id.split("_")[-1])
        await self._handle_bell_ping(interaction, match_id)

    async def _handle_bell_ping(self, interaction: discord.Interaction, match_id: int):
        await interaction.response.defer(ephemeral=True)
        participants    = self.bot.db.get_match_participants(match_id)
        participant_ids = {p["discord_id"] for p in participants}
        if interaction.user.id not in participant_ids:
            await interaction.followup.send("Only match participants can use this.", ephemeral=True)
            return
        all_threads = self.bot.db.get_match_threads(match_id)
        for thread_info in all_threads:
            guild_id = thread_info["guild_id"]
            try:
                target_thread = await self.bot.fetch_channel(thread_info["thread_id"])
                mentions = [f"<@{pid}>" for pid in participant_ids
                            if guild_id in self.bot.db.get_user_guilds(pid)]
                if mentions:
                    await target_thread.send(" ".join(mentions))
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Bell ping failed for thread {thread_info['thread_id']}: {e}")
        await interaction.followup.send("Players pinged! 🔔", ephemeral=True)

    # ------------------------------------------------------------------
    # Bell removal after 15 min
    # ------------------------------------------------------------------

    async def _remove_bell(self, match_id: int, threads: list[dict]):
        await asyncio.sleep(BELL_TIMEOUT_MINS * 60)
        for thread_info in threads:
            try:
                thread = await self.bot.fetch_channel(thread_info["thread_id"])
                async for msg in thread.history(limit=5, oldest_first=True):
                    if msg.author.id == self.bot.user.id and msg.embeds:
                        await msg.edit(view=None)
                        break
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Bell removal failed for thread {thread_info['thread_id']}: {e}")

    # ------------------------------------------------------------------
    # Thread archive after 24 hours
    # ------------------------------------------------------------------

    async def _archive_thread(self, match_id: int, threads: list[dict]):
        await asyncio.sleep(THREAD_ARCHIVE_HRS * 3600)
        for thread_info in threads:
            try:
                thread = await self.bot.fetch_channel(thread_info["thread_id"])
                if isinstance(thread, discord.Thread) and not thread.archived:
                    await thread.edit(archived=True, locked=True)
                    logger.info(f"Archived thread {thread_info['thread_id']} for match {match_id}")
            except discord.NotFound:
                pass
            except discord.Forbidden:
                logger.warning(f"No permission to archive thread {thread_info['thread_id']}")
            except Exception as e:
                logger.error(f"Archive failed for thread {thread_info['thread_id']}: {e}")

    # ------------------------------------------------------------------
    # Message relay between servers
    # Format: author = "PlayerName[CorpName]", footer = original text
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.Thread):
            return
        match_id = self.bot.db.get_match_id_by_thread(message.channel.id)
        if not match_id:
            return

        source_guild_id = message.guild.id
        source_server   = self.bot.db.get_server(source_guild_id)
        source_lang     = source_server.get("language", "en") if source_server else "en"

        # Corp name for the sender = the guild name they're posting from
        source_guild = self.bot.get_guild(source_guild_id)
        corp_name    = source_guild.name if source_guild else "Unknown"
        author_label = f"{message.author.display_name}[{corp_name}]"

        all_threads = self.bot.db.get_match_threads(match_id)

        for thread_info in all_threads:
            if thread_info["guild_id"] == source_guild_id:
                continue

            target_server = self.bot.db.get_server(thread_info["guild_id"])
            target_lang   = target_server.get("language", "en") if target_server else "en"

            content = message.content

            # Translate only if languages differ
            if source_lang != target_lang:
                translated = await self.thread_service.translate(content, source_lang, target_lang)
                embed = discord.Embed(description=translated, color=discord.Color.dark_gray())
                embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)
                # Show original message in footer when translation happened
                if translated != content:
                    footer_text = content[:200] + ("…" if len(content) > 200 else "")
                    embed.set_footer(text=f"Original: {footer_text}")
            else:
                embed = discord.Embed(description=content, color=discord.Color.dark_gray())
                embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)

            try:
                target_thread = await self.bot.fetch_channel(thread_info["thread_id"])
                await target_thread.send(embed=embed)
            except discord.NotFound:
                logger.warning(f"Thread {thread_info['thread_id']} not found — skipping relay")
            except Exception as e:
                logger.error(f"Relay failed to thread {thread_info['thread_id']}: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Feedback scheduler
    # ------------------------------------------------------------------

    async def _schedule_feedback(self, match_id: int, threads: list[dict]):
        await asyncio.sleep(config.FEEDBACK_DELAY_MINS * 60)
        self.bot.dispatch("drs_send_feedback", match_id, threads)


async def setup(bot):
    await bot.add_cog(ThreadCog(bot))

