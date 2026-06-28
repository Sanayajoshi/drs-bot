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
            embed.add_field(name="Feedback", value="\n".join(fb_lines), inline=False)

        if threads:
            thread_refs = [f"<#{t['thread_id']}>" for t in threads]
            embed.add_field(name="Threads", value=" ".join(thread_refs), inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

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
        if not