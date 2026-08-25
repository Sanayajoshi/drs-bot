import logging
import discord
import aiohttp
from discord import app_commands, ui
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import config

logger = logging.getLogger("officer_cog")


# ---------------------------------------------------------------------------
# Corp Bonus Modal
# ---------------------------------------------------------------------------

class BonusModal(ui.Modal, title="Set Corp Bonus"):
    bonus_pct = ui.TextInput(
        label="Bonus Percentage (whole number, e.g. 15)",
        placeholder="15",
        min_length=1,
        max_length=3,
        required=True,
    )
    expires_days = ui.TextInput(
        label="Expires in — Days",
        placeholder="0",
        min_length=1,
        max_length=3,
        required=True,
    )
    expires_hours = ui.TextInput(
        label="Expires in — Hours (0–23)",
        placeholder="12",
        min_length=1,
        max_length=2,
        required=True,
    )

    def __init__(self, guild_id: int, corp_name: str):
        super().__init__()
        self.guild_id  = guild_id
        self.corp_name = corp_name

    async def on_submit(self, interaction: discord.Interaction):
        # Validate bonus_pct
        try:
            pct = int(self.bonus_pct.value.strip())
            if pct <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Bonus percentage must be a positive whole number.", ephemeral=True
            )
            return

        # Validate days and hours
        try:
            days  = int(self.expires_days.value.strip())
            hours = int(self.expires_hours.value.strip())
            if days < 0 or hours < 0 or hours > 23:
                raise ValueError
            if days == 0 and hours == 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Enter valid days (≥0) and hours (0–23). Total must be at least 1 hour.", ephemeral=True
            )
            return

        expires_at = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(days=days, hours=hours)

        saved = interaction.client.db.upsert_corp_bonus(
            guild_id   = self.guild_id,
            corp_name  = self.corp_name,
            bonus_pct  = pct,
            expires_at = expires_at,
        )

        if not saved:
            await interaction.response.send_message("❌ Failed to save bonus. Try again.", ephemeral=True)
            return

        # Discord timestamp for expiry
        ts = int(expires_at.timestamp())
        await interaction.response.send_message(
            f"✅ **{self.corp_name}** bonus set to **{pct}%** — expires <t:{ts}:R> (<t:{ts}:f>).",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"BonusModal error: {error}", exc_info=True)
        await interaction.response.send_message("❌ Something went wrong.", ephemeral=True)


# ---------------------------------------------------------------------------
# Corp selector view — shown before the modal
# ---------------------------------------------------------------------------

class CorpSelectView(ui.View):
    def __init__(self, guilds: list[discord.Guild]):
        super().__init__(timeout=60)
        # Limit to 20 corps
        options = [
            discord.SelectOption(label=g.name[:100], value=str(g.id))
            for g in guilds[:20]
        ]
        select = ui.Select(
            placeholder="Select a corp to set bonus for…",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="corp_bonus_select",
        )
        select.callback = self._on_select
        self.add_item(select)
        self._guilds = {str(g.id): g for g in guilds}

    async def _on_select(self, interaction: discord.Interaction):
        guild_id  = int(interaction.data["values"][0])
        guild     = self._guilds.get(str(guild_id))
        corp_name = guild.name if guild else "Unknown"
        modal     = BonusModal(guild_id=guild_id, corp_name=corp_name)
        await interaction.response.send_modal(modal)


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class OfficerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _is_authorized(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in config.DEV_USER_IDS:
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        server = self.bot.db.get_server(interaction.guild_id)
        if server and server.get("manager_role_id"):
            return server["manager_role_id"] in [r.id for r in interaction.user.roles]
        return False

    drs = app_commands.Group(name="officer", description="DRS officer commands")

    # ------------------------------------------------------------------
    # /officer stats
    # ------------------------------------------------------------------

    @drs.command(name="stats", description="Overall match statistics")
    async def stats(self, interaction: discord.Interaction):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        rows = self.bot.db._execute(
            """SELECT drs_level, COUNT(*) as cnt FROM matches GROUP BY drs_level ORDER BY drs_level""",
            fetch_all=True
        ) or []
        total_row = self.bot.db._execute(
            "SELECT COUNT(*) as cnt FROM matches", fetch_one=True
        )
        feedback_row = self.bot.db._execute(
            """SELECT SUM(was_positive) as pos, COUNT(*) as total FROM feedback""",
            fetch_one=True
        )

        total   = total_row["cnt"] if total_row else 0
        pos     = feedback_row["pos"] or 0 if feedback_row else 0
        fb_tot  = feedback_row["total"] or 0 if feedback_row else 0
        rating  = f"{pos}/{fb_tot}" if fb_tot else "no ratings yet"

        embed = discord.Embed(title="📊 DRS Match Statistics", color=discord.Color.blurple())
        embed.add_field(name="Total Matches", value=str(total), inline=True)
        embed.add_field(name="Positive Ratings", value=rating, inline=True)

        breakdown = "\n".join(f"DRS{r['drs_level']}: **{r['cnt']}** matches" for r in rows) or "No matches yet"
        embed.add_field(name="By Level", value=breakdown, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /officer servers  — FIX: language now read from get_all_servers()
    # ------------------------------------------------------------------

    @drs.command(name="servers", description="List all servers the bot is installed on")
    async def servers(self, interaction: discord.Interaction):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        guilds = self.bot.guilds
        # get_all_servers now returns language among its columns
        db_servers = {s["guild_id"]: s for s in self.bot.db.get_all_servers()}

        embed = discord.Embed(
            title=f"🌐 Bot Servers — {len(guilds)} installed",
            color=discord.Color.blurple(),
        )

        lines = []
        for guild in sorted(guilds, key=lambda g: g.name.lower()):
            db  = db_servers.get(guild.id, {})
            configured = "✅" if db.get("queue_channel_id") else "⚠️"
            lang = db.get("language", "en") if db else "—"
            lines.append(
                f"{configured} **{guild.name}** `({guild.id})`\n"
                f"-# {guild.member_count:,} members · lang: `{lang}`"
            )

        chunk, chunks = [], []
        for line in lines:
            chunk.append(line)
            if len("\n\n".join(chunk)) > 900:
                chunks.append("\n\n".join(chunk[:-1]))
                chunk = [line]
        chunks.append("\n\n".join(chunk))

        for i, block in enumerate(chunks):
            embed.add_field(
                name=f"Servers {i + 1}" if len(chunks) > 1 else "Servers",
                value=block or "—",
                inline=False,
            )

        embed.set_footer(text="✅ = queue configured  ·  ⚠️ = setup not run")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /officer match <id>
    # ------------------------------------------------------------------

    @drs.command(name="match", description="Details for a specific match ID")
    @app_commands.describe(match_id="The match ID to look up")
    async def match(self, interaction: discord.Interaction, match_id: int):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        match_row = self.bot.db._execute(
            "SELECT * FROM matches WHERE id = ?", (match_id,), fetch_one=True
        )
        if not match_row:
            await interaction.followup.send(f"❌ Match #{match_id} not found.", ephemeral=True)
            return

        participants = self.bot.db.get_match_participants(match_id)
        feedback     = self.bot.db.get_match_feedback(match_id)
        reports      = self.bot.db.get_feedback_reports_for_match(match_id)
        threads      = self.bot.db.get_match_threads(match_id)

        embed = discord.Embed(
            title=f"🔍 Match #{match_id} — DRS{match_row['drs_level']}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Created", value=match_row["created_at"], inline=True)
        embed.add_field(name="Status",  value=match_row["status"],     inline=True)

        player_lines = []
        for p in participants:
            gen = p["genesis_level"] or "?"
            enr = p["enrich_level"]  or "?"
            rse = p["modt_level"]    or "?"
            player_lines.append(f"**{p['display_name']}** — GEN:{gen} ENR:{enr} RSE:{rse}")
        embed.add_field(name="Players", value="\n".join(player_lines) or "None", inline=False)

        if feedback:
            fb_lines = [f"{'✅' if f['was_positive'] else '❌'} {f['display_name']}" for f in feedback]
            embed.add_field(name="Ratings", value="\n".join(fb_lines), inline=False)

        if reports:
            rpt_blocks = []
            for r in reports:
                issue_raw = r.get("issue_type", "other")
                issue_map = {
                    "no_show": "No Show 👻",
                    "behavior": "Behavior 🚨",
                    "performance": "Performance 📉",
                    "other": "Other ❓",
                }
                issue = issue_map.get(issue_raw, issue_raw.replace("_", " ").title())

                created_ts_str = ""
                if r.get("created_at"):
                    try:
                        dt = datetime.strptime(str(r["created_at"]), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                        ts = int(dt.timestamp())
                        created_ts_str = f" · <t:{ts}:R>"
                    except Exception:
                        pass

                lines = [
                    f"🎫 **Ticket #{r['id']}** — **{issue}**{created_ts_str}",
                    f"   • **Reported Player:** **{r['reported_name']}** (<@{r['reported_player_id']}>)",
                    f"   • **Filed By:** {r['reporter_name']} (<@{r['reporter_id']}>)"
                ]

                if r.get("comment"):
                    lines.append(f"   • **Reason / Comment:** *\"{r['comment']}\"*")

                # Check resolution / closure status
                if r.get("resolved_at"):
                    res_ts_str = r["resolved_at"]
                    try:
                        res_dt = datetime.strptime(str(r["resolved_at"]), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                        res_ts = int(res_dt.timestamp())
                        res_ts_str = f"<t:{res_ts}:f> (<t:{res_ts}:R>)"
                    except Exception:
                        pass

                    resolver_label = r.get("resolver_name")
                    resolver_id = r.get("resolved_by")
                    if resolver_label and resolver_id:
                        resolver_str = f"**{resolver_label}** (<@{resolver_id}>)"
                    elif resolver_id:
                        resolver_str = f"<@{resolver_id}>"
                    else:
                        resolver_str = "Officer"

                    lines.append(f"   • **Status:** 🟢 **Resolved / Closed**")
                    lines.append(f"   • **Resolved By:** {resolver_str}")
                    lines.append(f"   • **Resolved At:** {res_ts_str}")

                    if r.get("resolution_notes"):
                        lines.append(f"   • **Resolution Notes:** {r['resolution_notes']}")
                else:
                    lines.append(f"   • **Status:** 🔴 **Open Investigation / Unresolved**")

                # Associated officer investigation threads
                r_threads = self.bot.db.get_report_threads(r["id"])
                if r_threads:
                    t_refs = [f"<#{t['thread_id']}>" for t in r_threads]
                    lines.append(f"   • **Investigation Threads:** {' '.join(t_refs)}")

                rpt_blocks.append("\n".join(lines))

            embed.add_field(name=f"⚠️ Reports & Tickets ({len(reports)})", value="\n\n".join(rpt_blocks), inline=False)

        if threads:
            thread_refs = [f"<#{t['thread_id']}>" for t in threads]
            embed.add_field(name="Threads", value=" ".join(thread_refs), inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /officer trigger_feedback <match_id> (Testing / manual trigger)
    # ------------------------------------------------------------------

    @drs.command(name="trigger_feedback", description="Immediately trigger the feedback prompt for a match (for testing)")
    @app_commands.describe(match_id="The match ID to trigger feedback for")
    async def trigger_feedback(self, interaction: discord.Interaction, match_id: int):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return

        match_row = self.bot.db._execute("SELECT id FROM matches WHERE id = ?", (match_id,), fetch_one=True)
        if not match_row:
            await interaction.response.send_message(f"❌ Match #{match_id} not found.", ephemeral=True)
            return

        feedback_cog = self.bot.get_cog("FeedbackCog")
        if not feedback_cog:
            await interaction.response.send_message("❌ FeedbackCog not loaded.", ephemeral=True)
            return

        await feedback_cog.send_match_feedback_prompt(match_id)
        await interaction.response.send_message(f"✅ Feedback prompt dispatched for **Match #{match_id}**.", ephemeral=True)

    # ------------------------------------------------------------------
    # /officer resolve_report <report_id> [notes]
    # ------------------------------------------------------------------

    @drs.command(name="resolve_report", description="Resolve and close an officer incident report investigation")
    @app_commands.describe(report_id="The ID of the report to resolve", notes="Optional resolution notes")
    async def resolve_report(self, interaction: discord.Interaction, report_id: int, notes: str = None):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return

        report = self.bot.db.get_feedback_report(report_id)
        if not report:
            await interaction.response.send_message(f"❌ Report #{report_id} not found.", ephemeral=True)
            return

        feedback_cog = self.bot.get_cog("FeedbackCog")
        if not feedback_cog:
            await interaction.response.send_message("❌ FeedbackCog not loaded.", ephemeral=True)
            return

        await feedback_cog._resolve_report_action(interaction, report_id, notes or "Resolved by officer command.")

    # ------------------------------------------------------------------
    # /officer level
    # ------------------------------------------------------------------

    @drs.command(name="level", description="Recent matches for a specific DRS level")
    @app_commands.describe(drs_level="DRS level (7-12)", count="Number of matches to show (default 5)")
    @app_commands.choices(drs_level=[app_commands.Choice(name=str(l), value=l) for l in range(7,13)])
    async def level(self, interaction: discord.Interaction,
                    drs_level: app_commands.Choice[int], count: int = 5):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        count = min(max(count, 1), 20)
        rows  = self.bot.db._execute(
            "SELECT id, created_at, status FROM matches WHERE drs_level = ? ORDER BY created_at DESC LIMIT ?",
            (drs_level.value, count), fetch_all=True
        ) or []

        embed = discord.Embed(
            title=f"📋 Recent DRS{drs_level.value} Matches",
            color=discord.Color.blurple()
        )
        if not rows:
            embed.description = "No matches found for this level."
        else:
            lines = []
            for r in rows:
                participants = self.bot.db.get_match_participants(r["id"])
                names = ", ".join(p["display_name"] for p in participants)
                lines.append(f"**#{r['id']}** — {r['created_at'][:16]}\n↳ {names}")
            embed.description = "\n\n".join(lines)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /officer players
    # ------------------------------------------------------------------

    @drs.command(name="players", description="Most active players by match count")
    @app_commands.describe(count="Number of players to show (default 10)")
    async def players(self, interaction: discord.Interaction, count: int = 10):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        count = min(max(count, 1), 25)
        rows  = self.bot.db._execute(
            """SELECT u.display_name, COUNT(mp.id) as match_count,
                      GROUP_CONCAT(DISTINCT m.drs_level) as levels
               FROM match_participants mp
               JOIN users u ON u.discord_id = mp.discord_id
               JOIN matches m ON m.id = mp.match_id
               GROUP BY mp.discord_id
               ORDER BY match_count DESC
               LIMIT ?""",
            (count,), fetch_all=True
        ) or []

        embed = discord.Embed(title="🏆 Most Active Pilots", color=discord.Color.gold())
        if not rows:
            embed.description = "No match data yet."
        else:
            lines = []
            medals = ["🥇","🥈","🥉"]
            for i, r in enumerate(rows):
                medal  = medals[i] if i < 3 else f"{i+1}."
                levels = ", ".join(f"DRS{l}" for l in sorted(int(x) for x in r["levels"].split(",")))
                lines.append(f"{medal} **{r['display_name']}** — {r['match_count']} runs ({levels})")
            embed.description = "\n".join(lines)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /officer queue
    # ------------------------------------------------------------------

    @drs.command(name="queue", description="Snapshot of the current queue across all levels")
    async def queue(self, interaction: discord.Interaction):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(title="🔭 Current Queue Snapshot", color=discord.Color.blurple())
        any_found = False
        for level in config.DRS_LEVELS:
            entries = self.bot.db.get_queue_for_level(level)
            if not entries:
                continue
            any_found = True
            lines = [f"**{e['display_name']}** — expires {e['expires_at'].strftime('%H:%M UTC') if e['expires_at'] else '?'}"
                     for e in entries]
            embed.add_field(name=f"DRS{level} ({len(entries)}/{config.MATCH_SIZE})",
                            value="\n".join(lines), inline=False)
        if not any_found:
            embed.description = "Queue is empty."

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /officer bonus set — select corp from dropdown, then fill modal
    # ------------------------------------------------------------------

    bonus_group = app_commands.Group(
        name="bonus",
        description="Manage corp bonuses",
        parent=None,  # will be nested under /officer
    )

    @drs.command(name="bonus_set", description="Set or update a corp's active bonus")
    async def bonus_set(self, interaction: discord.Interaction):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return

        guilds = self.bot.guilds
        if not guilds:
            await interaction.response.send_message("❌ No corps (servers) found.", ephemeral=True)
            return

        view = CorpSelectView(list(guilds))
        await interaction.response.send_message(
            "Select the corp to set a bonus for:",
            view=view,
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # /officer bonus_list — show all bonuses (active + expired)
    # ------------------------------------------------------------------

    @drs.command(name="bonus_list", description="List all corp bonuses (active and expired)")
    async def bonus_list(self, interaction: discord.Interaction):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ Officer access only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        bonuses = self.bot.db.get_all_corp_bonuses()
        now     = datetime.utcnow().replace(tzinfo=timezone.utc)

        embed = discord.Embed(title="🌟 Corp Bonuses", color=discord.Color.gold())
        if not bonuses:
            embed.description = "No bonuses have been set yet."
        else:
            active_lines  = []
            expired_lines = []
            for b in bonuses:
                expires_at = b["expires_at"]
                if expires_at and expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                ts = int(expires_at.timestamp()) if expires_at else 0
                line = f"**{b['corp_name']}** — **{b['bonus_pct']}%** · expires <t:{ts}:R>"
                if expires_at and expires_at > now:
                    active_lines.append("🟢 " + line)
                else:
                    expired_lines.append("🔴 " + line)

            if active_lines:
                embed.add_field(
                    name="Active",
                    value="\n".join(active_lines),
                    inline=False,
                )
            if expired_lines:
                embed.add_field(
                    name="Expired",
                    value="\n".join(expired_lines),
                    inline=False,
                )

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # Super Admin: /list_servers — list all configured servers, member count & join date
    # Allowed IDs: 508209182374363137, 702623662531936356, 670486428743892993
    # ------------------------------------------------------------------

    @app_commands.command(name="list_servers", description="[Admin Only] List all configured servers, member counts, and bot join dates")
    async def top_level_list_servers(self, interaction: discord.Interaction):
        await self.execute_list_servers(interaction)

    @drs.command(name="list_servers", description="[Admin Only] List all configured servers, member counts, and bot join dates")
    async def list_servers(self, interaction: discord.Interaction):
        await self.execute_list_servers(interaction)

    async def execute_list_servers(self, interaction: discord.Interaction):
        allowed_ids = getattr(config, "SUPER_ADMIN_IDS", [508209182374363137, 702623662531936356, 670486428743892993])
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message(
                "❌ Unauthorized: This command can only be executed by designated Bot Super Administrators.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        db_servers = self.bot.db.get_all_servers()
        guilds_map = {g.id: g for g in self.bot.guilds}

        embed = discord.Embed(
            title="🌐 Configured Discord Servers List",
            description=f"Total Configured Servers in DB: **{len(db_servers)}** | Active Bot Guilds: **{len(guilds_map)}**",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )

        if not db_servers and not guilds_map:
            embed.description = "No servers are currently registered or connected."
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Combine servers from DB and bot active guilds
        all_guild_ids = list(dict.fromkeys([s["guild_id"] for s in db_servers] + list(guilds_map.keys())))
        
        server_lines = []
        for idx, g_id in enumerate(all_guild_ids, start=1):
            guild = guilds_map.get(g_id)
            db_server = next((s for s in db_servers if s["guild_id"] == g_id), None)

            name = guild.name if guild else (f"Guild {g_id}")
            members_str = f"{guild.member_count:,} members" if guild and guild.member_count else "Unknown members"
            
            # Determine join date
            joined_str = "Unknown"
            if guild and guild.me and guild.me.joined_at:
                ts = int(guild.me.joined_at.timestamp())
                joined_str = f"<t:{ts}:f> (<t:{ts}:R>)"
            elif db_server and db_server.get("created_at"):
                created_at = db_server["created_at"]
                joined_str = f"`{created_at}`"

            # Determine Queue & Notification Channels + Direct Discord Links
            q_chan_id = db_server.get("queue_channel_id") if db_server else None
            n_chan_id = db_server.get("notification_channel_id") if db_server else None

            queue_link_str = f"<#{q_chan_id}> ([Jump to Queue Channel](https://discord.com/channels/{g_id}/{q_chan_id}))" if q_chan_id else "Not set"
            notif_link_str = f"<#{n_chan_id}>" if n_chan_id else "Not set"

            # Try to fetch/generate an invite link if bot has permissions in guild
            invite_str = "No invite perm"
            if guild:
                target_chan = None
                if q_chan_id:
                    target_chan = guild.get_channel(q_chan_id)
                if not target_chan and guild.system_channel:
                    target_chan = guild.system_channel
                if not target_chan and guild.text_channels:
                    target_chan = guild.text_channels[0]

                if target_chan and hasattr(target_chan, "create_invite"):
                    try:
                        invites = await target_chan.invites()
                        if invites:
                            invite_str = f"[Server Invite]({invites[0].url})"
                        else:
                            inv = await target_chan.create_invite(max_age=86400, max_uses=0, reason="Super Admin server list")
                            invite_str = f"[Server Invite]({inv.url})"
                    except Exception:
                        invite_str = f"[Direct Channel Link](https://discord.com/channels/{g_id}/{target_chan.id})"

            server_lines.append(
                f"**{idx}. {name}**\n"
                f"   • **Members:** {members_str}\n"
                f"   • **Bot Joined:** {joined_str}\n"
                f"   • **Queue Channel:** {queue_link_str}\n"
                f"   • **Invite / Link:** {invite_str}\n"
                f"   • **Guild ID:** `{g_id}`"
            )

        # Split into chunked fields if description overflows
        full_text = "\n\n".join(server_lines)
        if len(full_text) <= 4000:
            embed.description += f"\n\n{full_text}"
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # Send in fields or multiple messages
            chunks = []
            curr_chunk = []
            curr_len = 0
            for line in server_lines:
                if curr_len + len(line) > 1000:
                    chunks.append("\n\n".join(curr_chunk))
                    curr_chunk = [line]
                    curr_len = len(line)
                else:
                    curr_chunk.append(line)
                    curr_len += len(line)
            if curr_chunk:
                chunks.append("\n\n".join(curr_chunk))

            for i, chunk in enumerate(chunks):
                if i == 0:
                    embed.description += f"\n\n{chunk}"
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    sub_embed = discord.Embed(
                        title=f"🌐 Server List (Part {i+1})",
                        description=chunk,
                        color=discord.Color.blue()
                    )
                    await interaction.followup.send(embed=sub_embed, ephemeral=True)

    # ------------------------------------------------------------------
    # Live Mod Chat Relay (With Automatic Translation)
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Relays and translates messages typed in designated officer channels to other servers."""
        # Avoid processing bot messages or direct messages
        if message.author.bot or not message.guild:
            return

        # Fetch the server configuration for the sender's guild
        source_guild_id = message.guild.id
        source_server = self.bot.db.get_server(source_guild_id)
        if not source_server or not source_server.get("officer_channel_id"):
            return

        # Ensure the message was typed in the designated officer channel
        if message.channel.id != source_server["officer_channel_id"]:
            return

        # Ensure the message has text content to relay
        content = message.content.strip()
        if not content:
            return

        source_lang = source_server.get("language", "en")
        author_label = f"👮 {message.author.display_name} [{message.guild.name}]"

        # Relay to all other configured servers
        for srv in self.bot.db.get_all_servers():
            target_guild_id = srv["guild_id"]
            if target_guild_id == source_guild_id:
                continue

            # Fetch target config to verify they have an officer channel
            target_server = self.bot.db.get_server(target_guild_id)
            if not target_server or not target_server.get("officer_channel_id"):
                continue

            target_guild = self.bot.get_guild(target_guild_id)
            target_channel = target_guild and target_guild.get_channel(target_server["officer_channel_id"])
            if not target_channel:
                continue

            target_lang = target_server.get("language", "en")
            
            # Translate message if languages differ
            display_content = content
            footer_text = None
            
            if source_lang != target_lang:
                translated = await self._translate_mod_message(content, source_lang, target_lang)
                if translated and translated != content:
                    display_content = translated
                    # Show preview of original text in footer
                    truncated_original = content[:150] + ("..." if len(content) > 150 else "")
                    footer_text = f"Original: {truncated_original}"

            # Build a simple, clean message embed
            embed = discord.Embed(
                description=display_content,
                color=discord.Color.blue()
            )
            embed.set_author(name=author_label, icon_url=message.author.display_avatar.url)
            
            if footer_text:
                embed.set_footer(text=footer_text)

            try:
                await target_channel.send(embed=embed)
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"Failed to relay and translate mod message to guild {target_guild_id}: {e}")

    async def _translate_mod_message(self, text: str, source_lang: str, target_lang: str) -> str:
        """Helper to call translation API (MyMemory) asynchronously."""
        url = "https://api.mymemory.translated.net/get"
        lang_codes = {"en": "en-US", "ja": "ja-JP"}
        
        src = lang_codes.get(source_lang, source_lang)
        tgt = lang_codes.get(target_lang, target_lang)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"q": text, "langpair": f"{src}|{tgt}"}) as resp:
                    if resp.status != 200:
                        return text
                    data = await resp.json()
                    if data.get("responseStatus") != 200:
                        return text
                    return data["responseData"]["translatedText"]
        except Exception as e:
            logger.error(f"Mod translation failed: {e}")
            return text


async def setup(bot):
    await bot.add_cog(OfficerCog(bot))


