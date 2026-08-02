import logging
import discord
from discord.ext import commands, tasks
import config
from services.queue_service import QueueService
from services.ui_service import build_queue_embed, build_queue_view
from services.i18n import get as t

logger = logging.getLogger("queue_cog")

MOD_MAP = {
    "mod_set_genesis": ("genesis", "GEN"),
    "mod_set_enrich":  ("enrich",  "ENR"),
    "mod_set_modt":    ("modt",    "RSE"),
}

# How many minutes before expiry to send the warning
EXPIRY_WARN_MINS = 5


def _build_level_select(mod_key: str, mod_label: str) -> discord.ui.View:
    view = discord.ui.View(timeout=60)
    options = [discord.SelectOption(label=str(lvl), value=str(lvl)) for lvl in range(6, 16)]
    select = discord.ui.Select(
        placeholder=f"Select your {mod_label} level (6–15)",
        options=options,
        custom_id=f"mod_level_{mod_key}",
    )
    view.add_item(select)
    return view


def _build_expiry_extend_view(discord_id: int, drs_level: int, lang: str) -> discord.ui.View:
    """Button only the warned player can use to add 30 min."""
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(
        label=t(lang, "expiry_extend_prompt"),
        style=discord.ButtonStyle.success,
        custom_id=f"expiry_extend_{discord_id}_{drs_level}",
        emoji="⏳",
    ))
    return view


class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_service = QueueService(bot.db)
        self.queue_service.set_dispatch(bot.dispatch)
        # Track which (discord_id, drs_level) combos have already been warned
        self._warned: set[tuple[int, int]] = set()
        self.expiry_loop.start()
        self.sync_loop.start()

    def cog_unload(self):
        self.expiry_loop.cancel()
        self.sync_loop.cancel()

    def _lang(self, guild_id: int) -> str:
        server = self.bot.db.get_server(guild_id)
        return server.get("language", "en") if server else "en"

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_ready(self):
        for server in self.bot.db.get_all_servers():
            await self._ensure_queue_message(server)

    async def _ensure_queue_message(self, server: dict):
        guild_id   = server["guild_id"]
        channel_id = server.get("queue_channel_id")
        message_id = server.get("queue_message_id")
        if not channel_id:
            return
        guild   = self.bot.get_guild(guild_id)
        channel = guild and guild.get_channel(channel_id)
        if not channel:
            return
        full_server = self.bot.db.get_server(guild_id)
        lang  = full_server.get("language", "en") if full_server else "en"
        embed = build_queue_embed(self.bot.db.get_full_queue(), lang)
        view  = build_queue_view()
        if message_id:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.edit(embed=embed, view=view)
                return
            except discord.NotFound:
                pass
        msg = await channel.send(embed=embed, view=view)
        self.bot.db.set_queue_message_id(guild_id, msg.id)

    # ------------------------------------------------------------------
    # Push update
    # ------------------------------------------------------------------

    async def _push_queue_update(self):
        queue_data = self.bot.db.get_full_queue()
        view = build_queue_view()
        for server in self.bot.db.get_all_servers():
            try:
                guild   = self.bot.get_guild(server["guild_id"])
                channel = guild and guild.get_channel(server["queue_channel_id"])
                if not channel or not server.get("queue_message_id"):
                    continue
                full_server = self.bot.db.get_server(server["guild_id"])
                lang  = full_server.get("language", "en") if full_server else "en"
                embed = build_queue_embed(queue_data, lang)
                msg = await channel.fetch_message(server["queue_message_id"])
                await msg.edit(embed=embed, view=view)
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Push update error for guild {server['guild_id']}: {e}")

    # ------------------------------------------------------------------
    # Join notification — plain text, no embed
    # ------------------------------------------------------------------

    async def _notify_joined(self, discord_id: int, display_name: str, drs_level: int):
        queue   = self.bot.db.get_queue_for_level(drs_level)
        current = len(queue)
        total   = config.MATCH_SIZE
        if current > total:
            return

        for srv in self.bot.db.get_all_servers():
            guild_id = srv["guild_id"]
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue

            lang    = full_srv.get("language", "en")
            role_id = full_srv.get(f"role_drs{drs_level}")
            role_mention = f"<@&{role_id}> " if role_id else ""

            line = f"{role_mention}**{display_name}** joined **DRS{drs_level}** ({current}/{total})"
            try:
                await channel.send(line)
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_joined failed for guild {guild_id}: {e}")

    # ------------------------------------------------------------------
    # Leave notification — plain text, no embed, no role ping
    # ------------------------------------------------------------------

    async def _notify_left(self, display_name: str, drs_level: int):
        for srv in self.bot.db.get_all_servers():
            guild_id = srv["guild_id"]
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue
            lang = full_srv.get("language", "en")
            try:
                await channel.send(t(lang, "notify_left", name=display_name, level=drs_level))
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_left failed for guild {guild_id}: {e}")

    # ------------------------------------------------------------------
    # Extend notification — role mention re-fires for the level
    # ------------------------------------------------------------------

    async def _notify_extend(self, discord_id: int, display_name: str, drs_level: int):
        """Notify every server's notification channel that a player extended, with role ping."""
        for srv in self.bot.db.get_all_servers():
            guild_id = srv["guild_id"]
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue
            lang    = full_srv.get("language", "en")
            role_id = full_srv.get(f"role_drs{drs_level}")
            role_mention = f"<@&{role_id}> " if role_id else ""
            try:
                await channel.send(
                    t(lang, "notify_extend", role=role_mention, name=display_name, level=drs_level)
                )
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_extend failed for guild {guild_id}: {e}")

    # ------------------------------------------------------------------
    # Match Formation Listener (Prominent, Cross-Server Embed)
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_drs_match_formed(self, match_id: int, drs_level: int, participants: list[dict]):
        """
        Listens for match formation, compiles a player list indicating home corporations (servers),
        and broadcasts a compact, formatted embed announcement across all registered servers.
        """
        # Fetch detailed participant records from the database
        full_participants = self.bot.db.get_match_participants(match_id)
        
        # Compile player list with guild name mapping
        player_lines = []
        for p in full_participants:
            origin_guild = self.bot.get_guild(p["queue_guild_id"])
            corp_name = origin_guild.name if origin_guild else "Unknown"
            player_lines.append(f"• **{p['display_name']}** (*{corp_name}*)")
            
        roster_str = "\n".join(player_lines)

        for srv in self.bot.db.get_all_servers():
            guild_id = srv["guild_id"]
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue

            # Local server level role mention
            role_id = full_srv.get(f"role_drs{drs_level}")
            role_mention = f"<@&{role_id}>" if role_id else ""
            role_mention = ""

            # Compact, clean styling
            embed = discord.Embed(
                title=f"⚔️ DRS {drs_level} Formed! (Match #{match_id})",
                description=f"**Roster:**\n{roster_str}",
                color=discord.Color.red()
            )

            try:
                await channel.send(content=role_mention, embed=embed)
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"Failed to send match formed notice to guild {guild_id}: {e}")

    # ------------------------------------------------------------------
    # Expiry warning — tag the player, player-only extend button
    # ------------------------------------------------------------------

    async def _warn_expiring(self, discord_id: int, display_name: str, drs_level: int):
        """Send a 5-minute expiry warning to the player in every server they belong to."""
        guild_ids = self.bot.db.get_user_guilds(discord_id)
        sent = False
        for guild_id in guild_ids:
            server = self.bot.db.get_server(guild_id)
            if not server or not server.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(server["notification_channel_id"])
            if not channel:
                continue
            lang = server.get("language", "en")
            view = _build_expiry_extend_view(discord_id, drs_level, lang)
            msg_text = t(lang, "expiry_warning", name=f"<@{discord_id}>", level=drs_level)
            try:
                await channel.send(msg_text, view=view)
                sent = True
                break  # warn once — in first valid server found
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"warn_expiring failed for guild {guild_id}: {e}")
        return sent

    # ------------------------------------------------------------------
    # Interaction dispatcher
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        server    = self.bot.db.get_server(interaction.guild_id)

        # Expiry extend button — handled before queue message check
        if custom_id.startswith("expiry_extend_"):
            await self._handle_expiry_extend(interaction, custom_id)
            return

        if custom_id.startswith("mod_level_mod_set_"):
            await self._handle_mod_level_select(interaction, custom_id)
            return

        if not server or interaction.message.id != server.get("queue_message_id"):
            return

        if custom_id.startswith("drs_join_"):
            await self._handle_join(interaction, int(custom_id.split("_")[-1]))
        elif custom_id == "drs_leave":
            await self._handle_leave(interaction)
        elif custom_id == "drs_extend":
            await self._handle_extend(interaction)
        elif custom_id == "drs_quickstart":
            await self._handle_quickstart(interaction)
        elif custom_id == "drs_need_assist":
            await self._handle_need_assist(interaction)
        elif custom_id in MOD_MAP:
            await self._handle_mod_button(interaction, custom_id)

    # ------------------------------------------------------------------
    # Expiry extend button handler
    # ------------------------------------------------------------------

    async def _handle_expiry_extend(self, interaction: discord.Interaction, custom_id: str):
        await interaction.response.defer(ephemeral=True)
        # custom_id: expiry_extend_{discord_id}_{drs_level}
        parts      = custom_id.split("_")
        owner_id   = int(parts[2])
        drs_level  = int(parts[3])
        lang       = self._lang(interaction.guild_id)

        if interaction.user.id != owner_id:
            await interaction.followup.send(t(lang, "expiry_not_yours"), ephemeral=True)
            return

        self.bot.db.extend_queue(owner_id, config.EXTEND_MINS)
        # Clear the warning so they can be warned again next time
        self._warned.discard((owner_id, drs_level))

        await interaction.followup.send(
            t(lang, "expiry_extended_ok", level=drs_level), ephemeral=True
        )

        # Re-fire role mention notification
        await self._notify_extend(owner_id, interaction.user.display_name, drs_level)
        await self._push_queue_update()

    # ------------------------------------------------------------------
    # Join / leave toggle
    # ------------------------------------------------------------------

    async def _handle_join(self, interaction: discord.Interaction, level: int):
        await interaction.response.defer(ephemeral=True)
        discord_id   = interaction.user.id
        display_name = interaction.user.display_name
        guild_id     = interaction.guild_id
        lang         = self._lang(guild_id)

        self.bot.db.upsert_user(discord_id, display_name)
        self.bot.db.upsert_user_server(discord_id, guild_id, display_name)

        if self.bot.db.is_user_queued_for_level(discord_id, level):
            self.bot.db.leave_queue_level(discord_id, level)
            self._warned.discard((discord_id, level))
            remaining = self.bot.db.get_user_queue_levels(discord_id)
            if remaining:
                level_str = ", ".join(f"DRS{l}" for l in sorted(remaining))
                await interaction.followup.send(
                    t(lang, "left_level", level=level, levels=level_str), ephemeral=True
                )
            else:
                await interaction.followup.send(
                    t(lang, "left_level_all_gone", level=level), ephemeral=True
                )
            await self._notify_left(display_name, level)
            await self._push_queue_update()
            return

        result = await self.queue_service.join(discord_id, display_name, level, guild_id)

        if result == "match_formed":
            await interaction.followup.send(t(lang, "match_formed", level=level), ephemeral=True)
        else:
            levels    = self.bot.db.get_user_queue_levels(discord_id)
            level_str = ", ".join(f"DRS{l}" for l in sorted(levels))
            queue     = self.bot.db.get_queue_for_level(level)
            await interaction.followup.send(
                t(lang, "joined", level=level, time="30m", levels=level_str), ephemeral=True
            )
            if len(queue) <= 2:
                await self._notify_joined(discord_id, display_name, level)

        await self._push_queue_update()

    # ------------------------------------------------------------------
    # Leave all
    # ------------------------------------------------------------------

    async def _handle_leave(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        lang   = self._lang(interaction.guild_id)
        levels = self.bot.db.get_user_queue_levels(interaction.user.id)
        if not levels:
            await interaction.followup.send(t(lang, "not_in_queue"), ephemeral=True)
            return

        display_name = interaction.user.display_name
        self.bot.db.leave_queue(interaction.user.id)
        for lvl in levels:
            self._warned.discard((interaction.user.id, lvl))

        level_str = ", ".join(f"DRS{l}" for l in sorted(levels))
        await interaction.followup.send(t(lang, "left_all", levels=level_str), ephemeral=True)

        for lvl in levels:
            await self._notify_left(display_name, lvl)

        await self._push_queue_update()

    # ------------------------------------------------------------------
    # Extend all — now fires role mention notification per level
    # ------------------------------------------------------------------

    async def _handle_extend(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        lang   = self._lang(interaction.guild_id)
        levels = self.bot.db.get_user_queue_levels(interaction.user.id)
        if not levels:
            await interaction.followup.send(t(lang, "not_in_queue"), ephemeral=True)
            return

        self.bot.db.extend_queue(interaction.user.id, config.EXTEND_MINS)
        for lvl in levels:
            self._warned.discard((interaction.user.id, lvl))

        level_str = ", ".join(f"DRS{l}" for l in sorted(levels))
        await interaction.followup.send(
            t(lang, "extended", mins=config.EXTEND_MINS, levels=level_str), ephemeral=True
        )

        # Fire role-mention notification for each extended level
        for lvl in levels:
            await self._notify_extend(interaction.user.id, interaction.user.display_name, lvl)

        await self._push_queue_update()

    # ------------------------------------------------------------------
    # Quick Start
    # ------------------------------------------------------------------

    async def _handle_quickstart(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id   = interaction.user.id
        display_name = interaction.user.display_name
        lang         = self._lang(interaction.guild_id)

        levels = self.bot.db.get_user_queue_levels(discord_id)
        if not levels:
            await interaction.followup.send(t(lang, "qs_not_queued"), ephemeral=True)
            return
        if len(levels) > 1:
            level_str = ", ".join(f"DRS{l}" for l in sorted(levels))
            await interaction.followup.send(t(lang, "qs_multi_queue", levels=level_str), ephemeral=True)
            return

        drs_level = levels[0]
        queue     = self.bot.db.get_queue_for_level(drs_level)

        if len(queue) < 2:
            await interaction.followup.send(t(lang, "qs_alone", level=drs_level), ephemeral=True)
            return

        my_entry = next((e for e in queue if e["discord_id"] == discord_id), None)
        if my_entry and my_entry.get("quick_start"):
            await interaction.followup.send(t(lang, "qs_already"), ephemeral=True)
            return

        others_ready = [e for e in queue if e["discord_id"] != discord_id and e.get("quick_start")]

        if others_ready:
            result = await self.queue_service.quick_start_match(drs_level, queue[:2])
            if result == "match_formed":
                await interaction.followup.send(t(lang, "qs_confirmed", level=drs_level), ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong forming the match.", ephemeral=True)
        else:
            self.bot.db.set_quick_start(discord_id, drs_level, True)
            await self._notify_quickstart(discord_id, display_name, drs_level, queue)
            await interaction.followup.send(t(lang, "qs_sent", level=drs_level), ephemeral=True)

        await self._push_queue_update()

    async def _notify_quickstart(self, requester_id, requester_name, drs_level, queue):
        other_ids = [e["discord_id"] for e in queue if e["discord_id"] != requester_id]
        for target_id in other_ids:
            for guild_id in self.bot.db.get_user_guilds(target_id):
                server = self.bot.db.get_server(guild_id)
                if not server or not server.get("notification_channel_id"):
                    continue
                guild   = self.bot.get_guild(guild_id)
                channel = guild and guild.get_channel(server["notification_channel_id"])
                if not channel:
                    continue
                lang = server.get("language", "en")
                msg = f"<@{target_id}> {t(lang, 'notify_qs', name=requester_name, level=drs_level)}"
                try:
                    await channel.send(msg)
                    break
                except Exception as e:
                    logger.error(f"QS notify failed for guild {guild_id}: {e}")

    # ------------------------------------------------------------------
    # Mod buttons
    # ------------------------------------------------------------------

    async def _handle_mod_button(self, interaction: discord.Interaction, custom_id: str):
        mod_key, mod_label = MOD_MAP[custom_id]
        lang    = self._lang(interaction.guild_id)
        mods    = self.bot.db.get_user_mod_levels(interaction.user.id)
        current = mods.get(f"{mod_key}_level") or t(lang, "mod_not_set")
        prompt  = t(lang, "mod_prompt", mod=mod_label, current=current)
        view    = _build_level_select(custom_id, mod_label)
        await interaction.response.send_message(prompt, view=view, ephemeral=True)

    async def _handle_mod_level_select(self, interaction: discord.Interaction, custom_id: str):
        await interaction.response.defer(ephemeral=True)
        lang       = self._lang(interaction.guild_id)
        mod_custom = custom_id.replace("mod_level_", "")
        mod_key, mod_label = MOD_MAP.get(mod_custom, (None, None))
        if not mod_key:
            await interaction.followup.send("Unknown mod type.", ephemeral=True)
            return
        selected_level = int(interaction.data["values"][0])
        self.bot.db.set_user_mod_level(interaction.user.id, mod_key, selected_level)
        await interaction.followup.send(
            t(lang, "mod_set", mod=mod_label, level=selected_level), ephemeral=True
        )

    # ------------------------------------------------------------------
    # Need Assist toggle
    # ------------------------------------------------------------------

    async def _handle_need_assist(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id   = interaction.user.id
        display_name = interaction.user.display_name
        guild_id     = interaction.guild_id

        self.bot.db.upsert_user(discord_id, display_name)
        if guild_id:
            self.bot.db.upsert_user_server(discord_id, guild_id, display_name)

        new_status = self.bot.db.toggle_need_assist(discord_id)
        status_text = "ENABLED 🆘" if new_status else "DISABLED ❌"
        await interaction.followup.send(
            f"Need Assist status is now **{status_text}**.", ephemeral=True
        )
        await self._push_queue_update()

    # ------------------------------------------------------------------
    # Expiry loop — sweeps + sends 5-min warnings
    # ------------------------------------------------------------------

    @tasks.loop(seconds=config.EXPIRY_INTERVAL_SECS)
    async def expiry_loop(self):
        try:
            from datetime import datetime, timezone, timedelta
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            warn_threshold = now + timedelta(minutes=EXPIRY_WARN_MINS)

            all_entries = self.bot.db.get_full_queue()
            for entry in all_entries:
                key = (entry["discord_id"], entry["drs_level"])
                if key in self._warned:
                    continue
                expires_at = entry["expires_at"]
                if expires_at and expires_at <= warn_threshold:
                    warned = await self._warn_expiring(
                        entry["discord_id"], entry["display_name"], entry["drs_level"]
                    )
                    if warned:
                        self._warned.add(key)

            removed_ids = self.bot.db.remove_expired_entries()
            if removed_ids:
                self._warned = {k for k in self._warned if k[0] not in removed_ids}
                logger.info(f"Expiry sweep removed entries for {len(removed_ids)} user(s)")
                await self._push_queue_update()
        except Exception as e:
            logger.error(f"Expiry loop error: {e}", exc_info=True)

    @expiry_loop.before_loop
    async def before_expiry_loop(self):
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------
    # Sync loop
    # ------------------------------------------------------------------

    @tasks.loop(seconds=60)
    async def sync_loop(self):
        try:
            await self._push_queue_update()
        except Exception as e:
            logger.error(f"Sync loop error: {e}", exc_info=True)

    @sync_loop.before_loop
    async def before_sync_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(QueueCog(bot))
