import random
import discord


# Fun community lore / memes (strictly NO hydro mentioned)
LORE_MEMES = [
    {
        "title": "🌌 Sci-Fi Tactical Insight #1",
        "desc": "Did you know? Sector scanners report that 94% of failed Dark Red Stars were caused by someone forgetting their flagship shield booster, not enemy battleships."
    },
    {
        "title": "🛰️ Shipyard Wisdom #42",
        "desc": "A ancient pilot adage: 'A transport with Genesis is a blessing, but a transport moving without escort into a Cerberus sector is a donation.'"
    },
    {
        "title": "🛸 Sector Communication Log",
        "desc": "Corporation chatter overheard: 'QuickStart enabled! The Cerberus dreadnoughts didn't even have time to power their lasers.'"
    },
    {
        "title": "⚡ Quantum Warp Tip",
        "desc": "Using QuickStart in the DRS Queue increases team response efficiency by over 300%. Don't leave your squad waiting at the jump gate!"
    },
    {
        "title": "🚀 Pilot Pro-Tip",
        "desc": "Check your Genesis & Enrich levels before warping into high DRS sectors. A well-placed Enrich tile turns barren asteroids into economic glory."
    },
    {
        "title": "☄️ Interstellar Fun Fact",
        "desc": "Dark Red Star Cerberus fleets are programmed to fear coordinated team play. Jump in together, stay together!"
    }
]


class FactsService:
    def __init__(self, db):
        self.db = db

    def get_random_fact_embed(self) -> discord.Embed:
        generators = [
            self._top_runners_embed,
            self._top_corps_embed,
            self._activity_radar_embed,
            self._drs_distribution_embed,
            self._quickstart_embed,
            self._morale_embed,
            self._lore_meme_embed,
        ]
        chosen = random.choice(generators)
        return chosen()

    def _top_runners_embed(self) -> discord.Embed:
        runners = self.db.get_top_dr_runners(5)
        embed = discord.Embed(
            title="🏆 Top DRS Pilots Across the Network",
            color=discord.Color.gold(),
            description="Honoring our most active commanders warp-jumping into Dark Red Stars:"
        )
        if not runners:
            embed.add_field(name="Status", value="No recorded runs yet! Be the first to top the leaderboard.")
        else:
            lines = []
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for idx, r in enumerate(runners):
                m = medals[idx] if idx < len(medals) else "▫️"
                lines.append(f"{m} **{r['display_name']}** — `{r['run_count']}` runs")
            embed.add_field(name="Leaderboard", value="\n".join(lines), inline=False)
        
        embed.set_footer(text="DRS Engagement Network • Updated live")
        return embed

    def _top_corps_embed(self) -> discord.Embed:
        corps = self.db.get_top_corps(5)
        embed = discord.Embed(
            title="🏛️ Top Corporations by DRS Operations",
            color=discord.Color.blue(),
            description="Corporations with the highest total Dark Red Star deployments:"
        )
        if not corps:
            embed.add_field(name="Status", value="No corporation statistics accumulated yet.")
        else:
            lines = []
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for idx, c in enumerate(corps):
                m = medals[idx] if idx < len(medals) else "▫️"
                lines.append(f"{m} **Guild ID `{c['queue_guild_id']}`** — `{c['total_runs']}` operations")
            embed.add_field(name="Top Squadrons", value="\n".join(lines), inline=False)

        embed.set_footer(text="DRS Engagement Network • Guild Ranking")
        return embed

    def _activity_radar_embed(self) -> discord.Embed:
        stats = self.db.get_runs_summary_stats()
        embed = discord.Embed(
            title="📊 Network Tactical Activity Radar",
            color=discord.Color.teal(),
            description="Current network-wide operational statistics:"
        )
        embed.add_field(name="Runs Today", value=f"`{stats['today_matches']}` matches", inline=True)
        embed.add_field(name="Runs This Week", value=f"`{stats['week_matches']}` matches", inline=True)
        embed.add_field(name="Total Lifetime Runs", value=f"`{stats['total_matches']}` matches", inline=True)
        embed.add_field(name="Connected Corps", value=f"`{stats['total_corps']}` servers", inline=True)

        embed.set_footer(text="DRS Engagement Network • Realtime Metrics")
        return embed

    def _drs_distribution_embed(self) -> discord.Embed:
        dist = self.db.get_drs_level_distribution_stats()
        embed = discord.Embed(
            title="🎯 DRS Sector Level Popularity Spectrum",
            color=discord.Color.purple(),
            description="Distribution of runs across Dark Red Star levels (7–12):"
        )
        if not dist:
            embed.add_field(name="Sector Status", value="No sector data available yet.")
        else:
            lines = []
            for item in dist:
                lines.append(f"• **DRS{item['drs_level']}**: `{item['cnt']}` matches completed")
            embed.add_field(name="Sector Breakdown", value="\n".join(lines), inline=False)

        embed.set_footer(text="DRS Engagement Network • Sector Analytics")
        return embed

    def _quickstart_embed(self) -> discord.Embed:
        qs = self.db.get_quickstart_vs_standard_stats()
        embed = discord.Embed(
            title="⚡ QuickStart Tactical Report",
            color=discord.Color.orange(),
            description="Comparing instant quickstarts vs standard queue formations:"
        )
        embed.add_field(name="Total Matches", value=f"`{qs['total']}`", inline=True)
        embed.add_field(name="QuickStart Formations", value=f"`{qs['quickstarts']}`", inline=True)
        embed.add_field(name="Standard Formations", value=f"`{qs['standard']}`", inline=True)

        embed.set_footer(text="Tip: Use the ▶️ QuickStart button when you're ready to jump early!")
        return embed

    def _morale_embed(self) -> discord.Embed:
        morale = self.db.get_feedback_morale_stats()
        embed = discord.Embed(
            title="💖 Fleet Morale & Community Rating",
            color=discord.Color.green(),
            description="Post-match player feedback index:"
        )
        embed.add_field(name="Positive Rating", value=f"**{morale['percentage']}%** 👍", inline=True)
        embed.add_field(name="Positive Reviews", value=f"`{morale['positive']}`", inline=True)
        embed.add_field(name="Total Reviews", value=f"`{morale['total']}`", inline=True)

        embed.set_footer(text="DRS Engagement Network • High Morale Equals High Victory Rates!")
        return embed

    def _lore_meme_embed(self) -> discord.Embed:
        item = random.choice(LORE_MEMES)
        embed = discord.Embed(
            title=item["title"],
            description=item["desc"],
            color=discord.Color.dark_theme()
        )
        embed.set_footer(text="Hades Star Community Transmission • DRS Engagement")
        return embed

