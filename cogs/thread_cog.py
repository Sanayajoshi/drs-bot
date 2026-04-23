import logging
import asyncio
import discord
from discord.ext import commands
import config
from services.thread_service import ThreadService
from services.i18n import get as t

logger = logging.getLogger("thread_cog")
BELL_TIMEOUT_MINS  = 15
THREAD_ARCHIVE_HRS = 24

EMOJI_GENESIS = "<:Genesis:1409872792211554365>"
EMOJI_ENRICH  = "<:Enrich:1409872795600424960>"
EMOJI_RSE     = "<:ModTRSE:1256962175398842399>"
EMOJI_LOW     = "<:modlow:1490529960899772516>"

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

        # Get which guild each participant queued from
        queue_guild_map = self.bot.db.get_participant_queue_guilds(participant_ids)

        # Collect the unique guilds where at least one participant queued from
        # and group participants per that guild (for mentions)
        guild_to_pids: dict[int, list[int]] = {}
        for pid in participant_ids:
            g = queue_guild_map.get(pid)
            if g:
                guild_to_pids.setdefault(g, []).append(pid)

        # Fallback: if nobody has a queue_guild recorded, put everyone in their first known guild
        if not guild_to_pids:
            for pid in participant_ids:
                guilds = self.bot.db.get_user_guilds(pid)
                if guilds:
                    guild_to_pids.setdefault(guilds[0], []).append(pid)

        # Build discord_id -> guild_name (corp) using user_servers display info
        id_to_corp: dict[int, str] = {}
        for pid in participant_ids:
            guilds = self.bot.db.get_user_guilds(pid)
            if guilds:
                g = self.bot.get_guild(guilds[0])
                id_to_corp[pid] = g.name if g else "Unknown"

        # GEN/ENR assignment — highest level wins each role
        gen_players = [p for p in participants if p.get("genesis_level") is not None]
        enr_players = [p for p in participants if p.get("enrich_level") is not None]
        #gen_best_id = max(gen_players, key=lambda p: p["genesis_level"])["discord_id"] if gen_players else None
        #enr_best_id = max(enr_players, key=lambda p: p["enrich_level"])["discord_id"] if enr_players else None

        # CHANGED: support ties by collecting ALL players with max level
        gen_best_ids = set()
        enr_best_ids = set()

        if gen_players:
            max_gen = max(p["genesis_level"] for p in gen_players)
            gen_best_ids = {p["discord_id"] for p in gen_players if p["genesis_level"] == max_gen}

        if enr_players:
            max_enr = max(p["enrich_level"] for p in enr_players)
            enr_best_ids = {p["discord_id"] for p in enr_players if p["enrich_level"] == max_enr}



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

                embed = self._build_match_embed(
                    match_id, drs_level, participants, id_to_corp,
                    gen_best_ids, enr_best_ids, lang
                )
                bell_view = self.thread_service.build_bell_view(match_id)

                # Plain text proceed line first — shows in push notifications
                proceed = t(lang, "match_proceed", level=drs_level)
                await thread.send(content=f"{mentions}\n{proceed}", embed=embed, view=bell_view)

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
    # Match embed — clean table format
    # ------------------------------------------------------------------

    def _build_match_embed(
        self,
        match_id: int,
        drs_level: int,
        participants: list[dict],
        id_to_corp: dict[int, str],
        gen_best_ids: set[int],  # CHANGED
        enr_best_ids: set[int],  # CHANGED
        lang: str,
    ) -> discord.Embed:
        embed = discord.Embed(
            title=t(lang, "match_title", level=drs_level, match_id=match_id),
            color=discord.Color.dark_red()
        )

        # Table header
        header = f"`{'Name':<15} {'Corp':<15}` {EMOJI_GENESIS}  {EMOJI_ENRICH}  {EMOJI_RSE}"
        rows   = [header, "`" + "─" * 38 + "`"]
        rows   = []
        for p in participants:
            pid      = p["discord_id"]
            name     = p["display_name"][:10]
            corp     = id_to_corp.get(pid, "Unknown")[:10]
            gen_lvl  = p.get("genesis_level")
            enr_lvl  = p.get("enrich_level")
            rse_lvl  = p.get("modt_level")

            gen_str = str(gen_lvl) if gen_lvl is not None else "?"
            enr_str = str(enr_lvl) if enr_lvl is not None else "?"
            rse_str = str(rse_lvl) if rse_lvl is not None else "?"

            # Role icon prefix: only show icon for assigned player
            # gen_icon = EMOJI_GENESIS if pid == gen_best_id else "🚫"
            # enr_icon = EMOJI_ENRICH  if pid == enr_best_id else "🚫"

            # CHANGED: check membership in set instead of single ID
            gen_icon = EMOJI_GENESIS if pid in gen_best_ids else EMOJI_LOW
            enr_icon = EMOJI_ENRICH  if pid in enr_best_ids else EMOJI_LOW

            row = f"**`{corp:<10}`**` {name:<10}` {gen_icon}`{gen_str:<2}`  {enr_icon}`{enr_str:<2}`  {EMOJI_RSE}`{rse_str:<2}`"
            rows.append(row)

        embed.add_field(name="\u200b", value="\n".join(rows), inline=False)

        # Compact warning — only if someone is missing tech
        missing = [p for p in participants if p.get("genesis_level") is None or p.get("enrich_level") is None]
        if missing:
            names = ", ".join(p["display_name"] for p in missing)
            key   = "match_warning_multi" if len(missing) > 1 else "match_warning"
            embed.add_field(name="\u200b", value=f"-# {t(lang, key, names=names)}", inline=False)

        embed.set_footer(text=t(lang, "match_footer"))
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
        all_threads     = self.bot.db.get_match_threads(match_id)

        for thread_info in all_threads:
            if thread_info["guild_id"] == source_guild_id:
                continue
            target_server = self.bot.db.get_server(thread_info["guild_id"])
            target_lang   = target_server.get("language", "en") if target_server else "en"
            content = message.content
            if source_lang != target_lang:
                content = await self.thread_service.translate(content, source_lang, target_lang)
            embed = discord.Embed(description=content, color=discord.Color.dark_gray())
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.set_footer(text=message.guild.name)
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
