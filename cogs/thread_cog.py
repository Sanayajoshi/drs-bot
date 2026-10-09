import logging
import asyncio
import discord
from discord.ext import commands
import config
from services.thread_service import ThreadService
from services.stats_service import format_duration
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
        self._msg_to_group: dict[int, str] = {}
        self._message_groups: dict[str, dict] = {}

    def _register_message(self, group_id: str, match_id: int, guild_id: int, channel_id: int, message_id: int):
        if group_id not in self._message_groups:
            if len(self._message_groups) > 500:
                old_keys = list(self._message_groups.keys())[:100]
                for ok in old_keys:
                    old_grp = self._message_groups.pop(ok, None)
                    if old_grp:
                        for m in old_grp.get("messages", {}).values():
                            self._msg_to_group.pop(m["message_id"], None)
            self._message_groups[group_id] = {
                "match_id": match_id,
                "messages": {},
                "reactions": {},
                "notices": {},
            }
        self._message_groups[group_id]["messages"][guild_id] = {
            "channel_id": channel_id,
            "message_id": message_id,
        }
        self._msg_to_group[message_id] = group_id

    def _lang(self, guild_id: int) -> str:
        server = self.bot.db.get_server(guild_id)
        return server.get("language", "en") if server else "en"

    # ------------------------------------------------------------------
    # Thread creation — only in the guild each participant queued from
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_drs_create_threads(self, match_id: int, drs_level: int, participants: list[dict], queue_type: str = "DRS"):
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

        # discord_id → corp name (the guild name they queued from) and server emoji
        id_to_corp: dict[int, str] = {}
        id_to_emoji: dict[int, str] = {}
        for pid in participant_ids:
            g_id = queue_guild_map.get(pid)
            if not g_id:
                guilds = self.bot.db.get_user_guilds(pid)
                g_id = guilds[0] if guilds else None
            g = self.bot.get_guild(g_id) if g_id else None
            id_to_corp[pid] = g.name if g else "Unknown"
            id_to_emoji[pid] = self.bot.db.get_server_emoji_tag(g_id)

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

        match_row = self.bot.db.get_match(match_id)
        queue_duration_seconds = match_row.get("queue_duration_seconds", 0) if match_row else 0

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
            thread_name = f"{queue_type}{drs_level} Match #{match_id}"

            try:
                thread = await channel.create_thread(
                    name=thread_name,
                    type=discord.ChannelType.public_thread,
                )

                match_embed = self._build_match_embed(
                    match_id, drs_level, participants, id_to_corp,
                    gen_best_ids, enr_best_ids, lang, queue_type=queue_type,
                    queue_duration_seconds=queue_duration_seconds,
                    id_to_emoji=id_to_emoji,
                )
                bell_view = self.thread_service.build_bell_view(match_id)

                proceed = t(lang, "match_proceed", queue=f"{queue_type}{drs_level}", level=drs_level)

                # SOS / Escort alert as a dedicated, high-visibility 1-line embed
                sos_participants = [p for p in participants if p.get("need_assist")]
                sos_embed = None
                if sos_participants:
                    sos_mentions = " ".join(f"<@{p['discord_id']}>" for p in sos_participants)
                    sos_text = t(lang, "match_sos_alert", names=sos_mentions)
                    sos_embed = discord.Embed(
                        description=sos_text,
                        color=discord.Color.from_rgb(239, 68, 68)
                    )

                # Build bonus embed if there are active bonuses
                bonus_embed = self._build_bonus_embed(lang)
                #bonus_embed = self._build_bonus_embed(active_bonuses, lang)

                embeds = []
                if sos_embed:
                    embeds.append(sos_embed)
                embeds.append(match_embed)
                if bonus_embed:
                    embeds.append(bonus_embed)

                intro_msg = await thread.send(
                    content=f"{mentions}\n{proceed}",
                    embeds=embeds,
                    view=bell_view,
                )
                self._register_message(f"intro_{match_id}", match_id, guild_id, thread.id, intro_msg.id)

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
        queue_type: str = "DRS",
        queue_duration_seconds: int = 0,
        id_to_emoji: dict[int, str] | None = None,
    ) -> discord.Embed:
        prefix = "🔴" if queue_type == "RS" else "⭐"
        color = discord.Color.red() if queue_type == "RS" else discord.Color.dark_red()
        title = t(lang, "match_title", queue=f"{queue_type}{drs_level}", level=drs_level, match_id=match_id)
        if not title.startswith("⭐") and not title.startswith("🔴"):
            title = f"{prefix} {title}"

        queue_time_str = format_duration(queue_duration_seconds)
        embed = discord.Embed(
            title=title,
            description=f"⏱️ **Queue formed in:** {queue_time_str}",
            color=color
        )

        rows = []
        for p in participants:
            pid     = p["discord_id"]
            name    = p["display_name"][:16]
            server_icon = (id_to_emoji.get(pid) if id_to_emoji else None) or self.bot.db.get_server_emoji_tag(p.get("queue_guild_id"))
            gen_lvl = p.get("genesis_level")
            enr_lvl = p.get("enrich_level")
            rse_lvl = p.get("modt_level")

            gen_str = str(gen_lvl) if gen_lvl is not None else "?"
            enr_str = str(enr_lvl) if enr_lvl is not None else "?"
            rse_str = str(rse_lvl) if rse_lvl is not None else "?"

            gen_icon = EMOJI_GENESIS if pid in gen_best_ids else EMOJI_LOW_GEN
            enr_icon = EMOJI_ENRICH  if pid in enr_best_ids else EMOJI_LOW_ENR

            wait_sec = p.get("wait_seconds", 0) or 0
            wait_min = max(0, int(round(wait_sec / 60)))
            wait_str = f"({wait_min}m)"

            sos_badge = " 🆘" if p.get("need_assist") else ""
            row = f"{server_icon} ` {wait_str:<6}{name:<16}`{sos_badge} {gen_icon}`{gen_str:<2}`  {enr_icon}`{enr_str:<2}`  {EMOJI_RSE}`{rse_str:<2}`"
            rows.append(row)

        embed.add_field(name="\u200b", value="\n".join(rows), inline=False)

        # SOS / Escort Carry Notice in embed
        sos_players = [p for p in participants if p.get("need_assist")]
        if sos_players:
            sos_names = ", ".join(f"**{p['display_name']}**" for p in sos_players)
            embed.add_field(
                name="🆘 Fleet Escort / Carry Notice",
                value=f"⚠️ {sos_names} signed up as **SOS** and will need a carry for this run!",
                inline=False
            )

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
        participants = self.bot.db.get_match_participants(match_id)
        participant_ids = [p["discord_id"] for p in participants]
        if interaction.user.id not in participant_ids:
            await interaction.followup.send("Only match participants can use this.", ephemeral=True)
            return

        # Map each participant to the guild they queued/signed up from
        queue_guild_map = self.bot.db.get_participant_queue_guilds(participant_ids)

        all_threads = self.bot.db.get_match_threads(match_id)
        for thread_info in all_threads:
            guild_id = thread_info["guild_id"]
            try:
                target_thread = await self.bot.fetch_channel(thread_info["thread_id"])
                # Ping players only in the server thread they signed up from, excluding the clicker
                mentions = [
                    f"<@{pid}>" for pid in participant_ids
                    if queue_guild_map.get(pid) == guild_id and pid != interaction.user.id
                ]
                if mentions:
                    await target_thread.send(f"🔔 {' '.join(mentions)}")
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Bell ping failed for thread {thread_info['thread_id']}: {e}")
        await interaction.followup.send("Teammates pinged! 🔔", ephemeral=True)

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
    # Message relay between servers (for both match threads and officer report threads)
    # Format: author = "PlayerName[CorpName]", footer = original text
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.Thread):
            return

        # Check if match thread
        match_id = self.bot.db.get_match_id_by_thread(message.channel.id)
        if match_id:
            await self._relay_match_message(message, match_id)
            return

        # Check if officer report thread
        report_id = self.bot.db.get_report_id_by_thread(message.channel.id)
        if report_id:
            await self._relay_report_message(message, report_id)
            return

    async def _relay_match_message(self, message: discord.Message, match_id: int):
        source_guild_id = message.guild.id
        source_server   = self.bot.db.get_server(source_guild_id)
        source_lang     = source_server.get("language", "en") if source_server else "en"

        # Server emoji and corp name for sender
        source_icon  = self.bot.db.get_server_emoji_tag(source_guild_id)
        source_guild = self.bot.get_guild(source_guild_id)
        corp_name    = source_guild.name if source_guild else "Unknown"
        author_label = f"{message.author.display_name} [{corp_name}]"

        all_threads = self.bot.db.get_match_threads(match_id)
        group_id = f"m_{match_id}_{message.id}"
        self._register_message(group_id, match_id, source_guild_id, message.channel.id, message.id)

        for thread_info in all_threads:
            if thread_info["guild_id"] == source_guild_id:
                continue

            target_server = self.bot.db.get_server(thread_info["guild_id"])
            target_lang   = target_server.get("language", "en") if target_server else "en"

            content = message.content

            # Translate only if languages differ
            if source_lang != target_lang:
                translated = await self.thread_service.translate(content, source_lang, target_lang)
                if translated and translated != content:
                    embed = discord.Embed(
                        description=f"{source_icon} **[{target_lang.upper()}]** {translated}",
                        color=discord.Color.dark_gray()
                    )
                    embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)
                    orig_preview = content if len(content) <= 1000 else (content[:995] + "...")
                    embed.add_field(name=f"📜 Original ({source_lang.upper()})", value=orig_preview, inline=False)
                    if len(content) > 1000:
                        embed.add_field(name="📜 Original (Cont.)", value=content[995:1995], inline=False)
                else:
                    embed = discord.Embed(description=f"{source_icon} {content}", color=discord.Color.dark_gray())
                    embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)
            else:
                embed = discord.Embed(description=f"{source_icon} {content}", color=discord.Color.dark_gray())
                embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)

            try:
                target_thread = await self.bot.fetch_channel(thread_info["thread_id"])
                relayed_msg = await target_thread.send(embed=embed)
                self._register_message(group_id, match_id, thread_info["guild_id"], target_thread.id, relayed_msg.id)
            except discord.NotFound:
                logger.warning(f"Thread {thread_info['thread_id']} not found — skipping relay")
            except Exception as e:
                logger.error(f"Relay failed to thread {thread_info['thread_id']}: {e}", exc_info=True)

    async def _relay_report_message(self, message: discord.Message, report_id: int):
        source_guild_id = message.guild.id
        source_server   = self.bot.db.get_server(source_guild_id)
        source_lang     = source_server.get("language", "en") if source_server else "en"

        source_icon  = self.bot.db.get_server_emoji_tag(source_guild_id)
        source_guild = self.bot.get_guild(source_guild_id)
        corp_name    = source_guild.name if source_guild else "Unknown"
        author_label = f"🛡️ {message.author.display_name} [{corp_name}]"

        all_threads = self.bot.db.get_report_threads(report_id)

        for thread_info in all_threads:
            if thread_info["guild_id"] == source_guild_id or thread_info.get("closed_at"):
                continue

            target_server = self.bot.db.get_server(thread_info["guild_id"])
            target_lang   = target_server.get("language", "en") if target_server else "en"

            content = message.content

            if source_lang != target_lang:
                translated = await self.thread_service.translate(content, source_lang, target_lang)
                if translated and translated != content:
                    embed = discord.Embed(
                        description=f"🛡️ {source_icon} **[{target_lang.upper()}]** {translated}",
                        color=discord.Color.red()
                    )
                    embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)
                    orig_preview = content if len(content) <= 1000 else (content[:995] + "...")
                    embed.add_field(name=f"📜 Original ({source_lang.upper()})", value=orig_preview, inline=False)
                    if len(content) > 1000:
                        embed.add_field(name="📜 Original (Cont.)", value=content[995:1995], inline=False)
                else:
                    embed = discord.Embed(description=f"🛡️ {source_icon} {content}", color=discord.Color.red())
                    embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)
            else:
                embed = discord.Embed(description=f"🛡️ {source_icon} {content}", color=discord.Color.red())
                embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)

            try:
                target_thread = await self.bot.fetch_channel(thread_info["thread_id"])
                await target_thread.send(embed=embed)
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Report relay failed to thread {thread_info['thread_id']}: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Cross-Server Reaction Pass-through (In-Place Linked Replies)
    # ------------------------------------------------------------------

    async def _sync_reaction_reply(self, group_id: str):
        group = self._message_groups.get(group_id)
        if not group:
            return

        reactions = group.get("reactions", {})

        # If all reactions removed, clean up notices across all threads
        if not reactions:
            for g_id, notice_info in list(group.get("notices", {}).items()):
                try:
                    chan = self.bot.get_channel(notice_info["channel_id"]) or await self.bot.fetch_channel(notice_info["channel_id"])
                    n_msg = await chan.fetch_message(notice_info["message_id"])
                    await n_msg.delete()
                except Exception:
                    pass
            group["notices"] = {}
            return

        # Update or send reply in each thread, filtering out local reactions
        for guild_id, msg_ref in list(group.get("messages", {}).items()):
            # Only show reactions that originated from OTHER servers to this thread
            external_reactions = [r for r in reactions.values() if r.get("guild_id") != guild_id]
            existing_notice = group.get("notices", {}).get(guild_id)

            if not external_reactions:
                # If there are no cross-server reactions for this thread, remove any existing notice
                if existing_notice:
                    try:
                        chan = self.bot.get_channel(msg_ref["channel_id"]) or await self.bot.fetch_channel(msg_ref["channel_id"])
                        n_msg = await chan.fetch_message(existing_notice["message_id"])
                        await n_msg.delete()
                    except Exception:
                        pass
                    group["notices"].pop(guild_id, None)
                continue

            # Build compact reaction line specifically for external reactions
            tokens = [f"{r['emoji']} by {r['pilot']}" for r in external_reactions]
            reactions_str = "  •  ".join(tokens)
            embed = discord.Embed(
                description=reactions_str,
                color=discord.Color.from_rgb(47, 49, 54)
            )

            if existing_notice:
                try:
                    chan = self.bot.get_channel(msg_ref["channel_id"]) or await self.bot.fetch_channel(msg_ref["channel_id"])
                    notice_msg = await chan.fetch_message(existing_notice["message_id"])
                    await notice_msg.edit(embed=embed)
                    continue
                except Exception:
                    group["notices"].pop(guild_id, None)

            try:
                chan = self.bot.get_channel(msg_ref["channel_id"]) or await self.bot.fetch_channel(msg_ref["channel_id"])
                parent_msg = await chan.fetch_message(msg_ref["message_id"])
                notice_msg = await parent_msg.reply(embed=embed, mention_author=False)
                group.setdefault("notices", {})[guild_id] = {
                    "channel_id": chan.id,
                    "message_id": notice_msg.id,
                }
            except Exception as e:
                logger.error(f"Failed to post reaction reply in thread {msg_ref['channel_id']}: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Passes emoji reactions across match threads as an in-place updated reply linked to the original message."""
        if payload.user_id == self.bot.user.id:
            return

        match_id = self.bot.db.get_match_id_by_thread(payload.channel_id)
        if not match_id:
            return

        group_id = self._msg_to_group.get(payload.message_id)
        if not group_id:
            group_id = f"m_{match_id}_{payload.message_id}"
            self._register_message(group_id, match_id, payload.guild_id, payload.channel_id, payload.message_id)

        group = self._message_groups.get(group_id)
        if not group:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = payload.member or (guild and guild.get_member(payload.user_id))
        if not member and guild:
            try:
                member = await guild.fetch_member(payload.user_id)
            except Exception:
                member = None

        if not member or member.bot:
            return

        corp_name = guild.name if guild else "Unknown"
        emoji_str = str(payload.emoji)
        group["reactions"][(payload.user_id, emoji_str)] = {
            "pilot": member.display_name,
            "corp": corp_name,
            "emoji": emoji_str,
            "guild_id": payload.guild_id,
        }
        await self._sync_reaction_reply(group_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Updates or removes the reaction reply when a user removes their reaction."""
        if payload.user_id == self.bot.user.id:
            return

        match_id = self.bot.db.get_match_id_by_thread(payload.channel_id)
        if not match_id:
            return

        group_id = self._msg_to_group.get(payload.message_id)
        if not group_id:
            return

        group = self._message_groups.get(group_id)
        if not group:
            return

        emoji_str = str(payload.emoji)
        if (payload.user_id, emoji_str) in group.get("reactions", {}):
            del group["reactions"][(payload.user_id, emoji_str)]
            await self._sync_reaction_reply(group_id)

    # ------------------------------------------------------------------
    # Feedback scheduler
    # ------------------------------------------------------------------

    async def _schedule_feedback(self, match_id: int, threads: list[dict]):
        await asyncio.sleep(config.FEEDBACK_DELAY_MINS * 60)
        self.bot.dispatch("drs_send_feedback", match_id, threads)


async def setup(bot):
    await bot.add_cog(ThreadCog(bot))





