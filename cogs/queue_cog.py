import logging
import discord
from discord.ext import commands, tasks
import config
from services.queue_service import QueueService
from services.ui_service import build_queue_embeds, build_queue_view, CombinedTechView, QueueModeSettingsView
from services.i18n import get as t

logger = logging.getLogger("queue_cog")

# How many minutes before expiry to send the warning
EXPIRY_WARN_MINS = 5


def _build_expiry_extend_view(discord_id: int, drs_level: int, queue_type: str = "DRS", lang: str = "en") -> discord.ui.View:
    """Button only the warned player can use to add 30 min."""
    view = discord.ui.View(timeout=300)
    view.add_item(discord.ui.Button(
        label=t(lang, "expiry_extend_prompt"),
        style=discord.ButtonStyle.success,
        custom_id=f"expiry_extend_{discord_id}_{drs_level}_{queue_type}",
        emoji="⏳",
    ))
    return view


class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_service = QueueService(bot.db)
        self.queue_service.set_dispatch(bot.dispatch)
        # Track which (discord_id, drs_level, queue_type) combos have already been warned
        self._warned: set[tuple] = set()
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
        activity_stats = self.bot.db.get_global_24h_match_stats()
        embeds = build_queue_embeds(self.bot.db.get_full_queue(), lang, activity_stats=activity_stats)
        view  = build_queue_view()
        if message_id:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.edit(embeds=embeds, view=view)
                return
            except discord.NotFound:
                pass
        msg = await channel.send(embeds=embeds, view=view)
        self.bot.db.set_queue_message_id(guild_id, msg.id)

    # ------------------------------------------------------------------
    # Push update
    # ------------------------------------------------------------------

    async def _push_queue_update(self):
        queue_data = self.bot.db.get_full_queue()
        activity_stats = self.bot.db.get_global_24h_match_stats()
        view = build_queue_view()
        for server in self.bot.db.get_all_servers():
            try:
                guild   = self.bot.get_guild(server["guild_id"])
                channel = guild and guild.get_channel(server["queue_channel_id"])
                if not channel or not server.get("queue_message_id"):
                    continue
                full_server = self.bot.db.get_server(server["guild_id"])
                lang  = full_server.get("language", "en") if full_server else "en"
                embeds = build_queue_embeds(queue_data, lang, activity_stats=activity_stats)
                msg = await channel.fetch_message(server["queue_message_id"])
                await msg.edit(embeds=embeds, view=view)
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Push update error for guild {server['guild_id']}: {e}")

    # ------------------------------------------------------------------
    # Join notification — plain text, no embed
    # ------------------------------------------------------------------

    async def _notify_joined(self, discord_id: int, display_name: str, drs_level: int, queue_type: str = "DRS"):
        queue   = self.bot.db.get_queue_for_level(drs_level, queue_type=queue_type)
        current = len(queue)
        total   = config.DRS_MATCH_SIZE if queue_type == "DRS" else config.RS_MATCH_SIZE
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
            role_key = f"role_drs{drs_level}" if queue_type == "DRS" else f"role_rs{drs_level}"
            role_id = full_srv.get(role_key)
            role_mention = f"<@&{role_id}> " if role_id else ""

            line = f"{role_mention}**{display_name}** joined **{queue_type}{drs_level}** ({current}/{total})"
            try:
                await channel.send(line)
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_joined failed for guild {guild_id}: {e}")

    # ------------------------------------------------------------------
    # Leave notification
    # ------------------------------------------------------------------

    async def _notify_left(self, display_name: str, drs_level: int, queue_type: str = "DRS"):
        for srv in self.bot.db.get_all_servers():
            guild_id = srv["guild_id"]
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue
            try:
                await channel.send(f"🚪 **{display_name}** left **{queue_type}{drs_level}**.")
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_left failed for guild {guild_id}: {e}")

    async def _notify_quickstart(self, display_name: str, drs_level: int, queue_type: str = "DRS"):
        queue   = self.bot.db.get_queue_for_level(drs_level, queue_type=queue_type)
        current = len(queue)
        total   = config.DRS_MATCH_SIZE if queue_type == "DRS" else config.RS_MATCH_SIZE

        for srv in self.bot.db.get_all_servers():
            guild_id = srv["guild_id"]
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue

            role_key = f"role_drs{drs_level}" if queue_type == "DRS" else f"role_rs{drs_level}"
            role_id  = full_srv.get(role_key)
            role_mention = f"<@&{role_id}> " if role_id else ""

            line = f"⚡ {role_mention}**{display_name}** enabled **Quick Start** for **{queue_type}{drs_level}**! ({current}/{total})"
            try:
                await channel.send(line)
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_quickstart failed for guild {guild_id}: {e}")

    async def _notify_extended(self, display_name: str, level_str: str, target_guild_id: int = None):
        guilds = [target_guild_id] if target_guild_id else [s["guild_id"] for s in self.bot.db.get_all_servers()]
        for guild_id in guilds:
            if not guild_id:
                continue
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue
            try:
                await channel.send(f"⏳ **{display_name}** extended their **{level_str}** slot by 30 minutes.")
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_extended failed for guild {guild_id}: {e}")

    async def _notify_expiry_warning(self, discord_id: int, display_name: str, drs_level: int, queue_type: str = "DRS", target_guild_id: int = None):
        guilds = [target_guild_id] if target_guild_id else [s["guild_id"] for s in self.bot.db.get_all_servers()]
        for guild_id in guilds:
            if not guild_id:
                continue
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue

            lang = full_srv.get("language", "en")
            view = _build_expiry_extend_view(discord_id, drs_level, queue_type, lang)
            content = f"⏰ <@{discord_id}> (**{display_name}**) — your **{queue_type}{drs_level}** queue slot expires in ~5 minutes! Tap ⏳ below to add 30 more."
            try:
                await channel.send(content, view=view)
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_expiry_warning failed for guild {guild_id}: {e}")

    async def _notify_expired(self, discord_id: int, display_name: str, drs_level: int, queue_type: str = "DRS", target_guild_id: int = None):
        guilds = [target_guild_id] if target_guild_id else [s["guild_id"] for s in self.bot.db.get_all_servers()]
        for guild_id in guilds:
            if not guild_id:
                continue
            full_srv = self.bot.db.get_server(guild_id)
            if not full_srv or not full_srv.get("notification_channel_id"):
                continue
            guild   = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(full_srv["notification_channel_id"])
            if not channel:
                continue
            content = f"⏰ <@{discord_id}> (**{display_name}**) — your spot in **{queue_type}{drs_level}** has expired. Tap a number on the queue message to jump back in!"
            try:
                await channel.send(content)
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"notify_expired failed for guild {guild_id}: {e}")

    # ------------------------------------------------------------------
    # Match Formation Listener
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_drs_match_formed(self, match_id: int, drs_level: int, participants: list[dict], queue_type: str = "DRS"):
        full_participants = self.bot.db.get_match_participants(match_id)
        
        player_lines = []
        for p in full_participants:
            origin_guild = self.bot.get_guild(p["queue_guild_id"]) if p.get("queue_guild_id") else None
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

            embed = discord.Embed(
                title=f"⚔️ {queue_type} Level {drs_level} Formed! (Match #{match_id})",
                description=f"**Roster:**\n{roster_str}",
                color=discord.Color.gold() if queue_type == "RS" else discord.Color.red()
            )

            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"Failed to send match formed notice to guild {guild_id}: {e}")

    # ------------------------------------------------------------------
    # Interaction dispatcher
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        server    = self.bot.db.get_server(interaction.guild_id)

        if custom_id.startswith("expiry_extend_"):
            await self._handle_expiry_extend(interaction, custom_id)
            return

        if not server or interaction.message.id != server.get("queue_message_id"):
            return

        if custom_id.startswith("drs_join_"):
            await self._handle_join(interaction, int(custom_id.split("_")[-1]))
        elif custom_id == "drs_mode_switch":
            await self._handle_mode_switch(interaction)
        elif custom_id == "drs_leave":
            await self._handle_leave(interaction)
        elif custom_id == "drs_extend":
            await self._handle_extend_button(interaction)
        elif custom_id == "drs_quickstart":
            await self._handle_quickstart(interaction)
        elif custom_id == "drs_need_assist":
            await self._handle_need_assist(interaction)
        elif custom_id == "mod_set_combined":
            await self._handle_combined_tech(interaction)

    # ------------------------------------------------------------------
    # Mode Switch Handler
    # ------------------------------------------------------------------

    async def _handle_mode_switch(self, interaction: discord.Interaction):
        discord_id = interaction.user.id
        display_name = interaction.user.display_name
        self.bot.db.upsert_user(discord_id, display_name)
        current_mode = self.bot.db.get_user_queue_mode(discord_id)

        if current_mode == "DRS":
            content = "Queue Mode Settings\nYour current active mode is Dark Red Star (DRS)."
        else:
            content = "Queue Mode Settings\nYour current active mode is Red Star (RS)."

        view = QueueModeSettingsView(self.bot.db, discord_id, current_mode, display_name)
        await interaction.response.send_message(
            content,
            view=view,
            ephemeral=True
        )

    # ------------------------------------------------------------------
    # Combined Tech Modal Handler
    # ------------------------------------------------------------------

    async def _handle_combined_tech(self, interaction: discord.Interaction):
        view = CombinedTechView(self.bot.db, interaction.user.id)
        await interaction.response.send_message(
            "🛠️ **Select your tech module levels below:**",
            view=view,
            ephemeral=True
        )

    # ------------------------------------------------------------------
    # Join / leave toggle
    # ------------------------------------------------------------------

    async def _handle_join(self, interaction: discord.Interaction, level: int):
        await interaction.response.defer(ephemeral=True)
        discord_id   = interaction.user.id
        display_name = interaction.user.display_name
        guild_id     = interaction.guild_id

        self.bot.db.upsert_user(discord_id, display_name)
        self.bot.db.upsert_user_server(discord_id, guild_id, display_name)

        # Levels 4, 5, 6 are strictly RS. Levels 7-12 depend on user queue mode.
        if level in [4, 5, 6]:
            queue_type = "RS"
        else:
            queue_type = self.bot.db.get_user_queue_mode(discord_id)

        if self.bot.db.is_user_queued_for_level(discord_id, level, queue_type):
            self.bot.db.leave_queue_level(discord_id, level, queue_type)
            self._warned.discard((discord_id, level))
            await interaction.followup.send(
                f"👋 Left **{queue_type}{level}** queue.", ephemeral=True
            )
            await self._notify_left(display_name, level, queue_type)
            await self._push_queue_update()
            return

        result = await self.queue_service.join(discord_id, display_name, level, guild_id, queue_type=queue_type)

        if result == "match_formed":
            await interaction.followup.send(f"🔥 **{queue_type}{level}** match found!", ephemeral=True)
        else:
            queue = self.bot.db.get_queue_for_level(level, queue_type=queue_type)
            await interaction.followup.send(
                f"✅ Joined **{queue_type}{level}** queue! Timer set for 30m.", ephemeral=True
            )
            await self._notify_joined(discord_id, display_name, level, queue_type)

        await self._push_queue_update()

    # ------------------------------------------------------------------
    # Leave all queues
    # ------------------------------------------------------------------

    async def _handle_leave(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id = interaction.user.id
        display_name = interaction.user.display_name

        self.bot.db.eject_player_from_all_queues(discord_id, reason="user_exit")
        await interaction.followup.send("🚪 You have exited all active queues.", ephemeral=True)
        await self._push_queue_update()

    # ------------------------------------------------------------------
    # Extend Active Queues (+30 min)
    # ------------------------------------------------------------------

    async def _handle_extend_button(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id   = interaction.user.id
        display_name = interaction.user.display_name

        user_queues = self.bot.db.get_user_queue_levels(discord_id)
        if not user_queues:
            await interaction.followup.send("🤔 You are not in any queue right now.", ephemeral=True)
            return

        self.bot.db.extend_queue(discord_id, minutes=config.EXTEND_MINS)
        for q in user_queues:
            self._warned.discard((discord_id, q["drs_level"], q.get("queue_type", "DRS")))
            self._warned.discard((discord_id, q["drs_level"]))

        q_names = ", ".join(f"{q.get('queue_type', 'DRS')}{q['drs_level']}" for q in user_queues)
        await interaction.followup.send(
            f"⏳ Added 30 minutes to your active queue slot(s) (**{q_names}**)!", ephemeral=True
        )
        await self._notify_extended(display_name, q_names, target_guild_id=interaction.guild_id)
        await self._push_queue_update()

    async def _handle_expiry_extend(self, interaction: discord.Interaction, custom_id: str):
        parts = custom_id.split("_")
        # Format: expiry_extend_{discord_id}_{drs_level}_{queue_type} or expiry_extend_{discord_id}_{drs_level}
        if len(parts) < 4:
            return
        target_id = int(parts[2])
        level = int(parts[3])
        queue_type = parts[4] if len(parts) > 4 else "DRS"

        if interaction.user.id != target_id:
            await interaction.response.send_message("🤔 This extend button isn't for you.", ephemeral=True)
            return

        if not self.bot.db.is_user_queued_for_level(target_id, level, queue_type):
            await interaction.response.send_message(
                f"❌ Your slot in **{queue_type}{level}** has already expired or you left the queue.", ephemeral=True
            )
            try:
                await interaction.message.edit(view=None)
            except Exception:
                pass
            return

        self.bot.db.extend_queue(target_id, minutes=config.EXTEND_MINS)
        self._warned.discard((target_id, level, queue_type))
        self._warned.discard((target_id, level))

        await interaction.response.send_message(
            f"✅ Added 30 minutes to your **{queue_type}{level}** queue!", ephemeral=True
        )

        try:
            await interaction.message.edit(view=None)
        except Exception:
            pass

        await self._notify_extended(interaction.user.display_name, f"{queue_type}{level}", target_guild_id=interaction.guild_id)
        await self._push_queue_update()

    # ------------------------------------------------------------------
    # Quick Start
    # ------------------------------------------------------------------

    async def _handle_quickstart(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id = interaction.user.id
        queue_type = self.bot.db.get_user_queue_mode(discord_id)

        # Find level player is currently in for this queue_type
        full_q = self.bot.db.get_full_queue()
        user_entries = [e for e in full_q if e["discord_id"] == discord_id and e.get("queue_type", "DRS") == queue_type]

        if not user_entries:
            await interaction.followup.send(f"❓ You are not in any **{queue_type}** queue.", ephemeral=True)
            return

        drs_level = user_entries[0]["drs_level"]
        self.bot.db.set_quick_start(discord_id, drs_level, True, queue_type=queue_type)

        res = await self.queue_service.check_quick_start(drs_level, queue_type=queue_type)
        if res == "match_formed":
            await interaction.followup.send(f"⚡ Quick Start triggered! **{queue_type}{drs_level}** match formed!", ephemeral=True)
        else:
            await interaction.followup.send(f"▶️ Quick Start enabled for **{queue_type}{drs_level}**.", ephemeral=True)
            await self._notify_quickstart(interaction.user.display_name, drs_level, queue_type=queue_type)

        await self._push_queue_update()

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
    # Expiry loop
    # ------------------------------------------------------------------

    @tasks.loop(seconds=config.EXPIRY_INTERVAL_SECS)
    async def expiry_loop(self):
        try:
            # 1. Sweep expired entries and notify players to join back in the origin server only
            expired_entries = self.bot.db.remove_expired_entries()
            if expired_entries:
                logger.info(f"Expiry sweep removed {len(expired_entries)} expired queue entry(ies)")
                for e in expired_entries:
                    uid = e["discord_id"]
                    lvl = e["drs_level"]
                    q_type = e.get("queue_type", "DRS")
                    d_name = e.get("display_name") or f"Pilot {uid}"
                    q_guild = e.get("queue_guild_id")
                    self._warned.discard((uid, lvl, q_type))
                    self._warned.discard((uid, lvl))
                    await self._notify_expired(uid, d_name, lvl, q_type, target_guild_id=q_guild)
                await self._push_queue_update()

            # 2. Check active entries for 5-minute expiry warnings in the origin server only
            from datetime import datetime, timezone
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            full_q = self.bot.db.get_full_queue()
            for entry in full_q:
                exp_dt = entry.get("expires_at")
                if not exp_dt:
                    continue
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                remaining_secs = (exp_dt - now_utc).total_seconds()
                uid = entry["discord_id"]
                lvl = entry["drs_level"]
                q_type = entry.get("queue_type", "DRS")
                q_guild = entry.get("queue_guild_id")
                warn_key = (uid, lvl, q_type)

                if 0 < remaining_secs <= EXPIRY_WARN_MINS * 60:
                    if warn_key not in self._warned and (uid, lvl) not in self._warned:
                        self._warned.add(warn_key)
                        self._warned.add((uid, lvl))
                        await self._notify_expiry_warning(uid, entry["display_name"], lvl, q_type, target_guild_id=q_guild)

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




