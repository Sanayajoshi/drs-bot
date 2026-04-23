import logging
import discord
from discord import app_commands
from discord.ext import commands
import config

logger = logging.getLogger("officer_cog")


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
    # /officer stats — overall match summary
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
    # /officer match <id> — details on a specific match
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
    # /officer level <7-12> — recent matches for a DRS level
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
    # /officer players — most active players
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
    # /officer queue — current queue snapshot
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


async def setup(bot):
    await bot.add_cog(OfficerCog(bot))
