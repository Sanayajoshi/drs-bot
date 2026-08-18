import logging
import discord
from discord import app_commands
from discord.ext import commands

import config
from services.stats_service import StatsService

logger = logging.getLogger("drs_bot.stats_cog")


class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stats_service = StatsService(bot.db)

    @app_commands.command(name="playerstats", description="[Admin Only] View detailed player stats and queue analytics.")
    @app_commands.describe(player="Select a player to view stats for (defaults to yourself)")
    async def playerstats_cmd(self, interaction: discord.Interaction, player: discord.Member | None = None):
        # Restriction: Only SUPER_ADMIN_IDS can run for now
        if interaction.user.id not in config.SUPER_ADMIN_IDS:
            await interaction.response.send_message(
                "❌ **Access Restricted**: This command is currently restricted to Super Admins.",
                ephemeral=True
            )
            return

        target = player or interaction.user
        await interaction.response.defer(ephemeral=False)

        try:
            stats = self.stats_service.get_player_stats(target.id)
            # Override display name if discord.Member display_name is available
            if hasattr(target, "display_name") and target.display_name:
                stats["display_name"] = target.display_name

            embed = self.stats_service.build_player_stats_embed(stats)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error generating player stats for {target.id}: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ An error occurred while generating the player stats card.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))

