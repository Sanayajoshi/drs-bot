import discord
from discord.ext import commands
from discord import app_commands
import logging
import re

logger = logging.getLogger("bonus_cog")

# Allowed user IDs for admin commands
ALLOWED_IDS = {508209182374363137, 670486428743892993, 702623662531936356}


class BonusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bonus_service = None  # Will be set after initialization
    
    @app_commands.command(
        name="add_corporation",
        description="Add a corporation to auto-fetch its bonus (Admin only)"
    )
    @app_commands.describe(
        corp_id="The corporation ID (64 hex characters from the URL)",
        name="Optional custom name (if not auto-detected)"
    )
    async def add_corporation(
        self, 
        interaction: discord.Interaction,
        corp_id: str,
        name: str = None
    ):
        """Add a new corporation to track bonuses."""
        if interaction.user.id not in ALLOWED_IDS:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Validate corp_id format
        if not re.match(r'^[a-f0-9]{64}$', corp_id):
            await interaction.followup.send(
                "❌ Invalid corporation ID. Must be exactly 64 hexadecimal characters.\n"
                "Example: `b6e23a3f1f3a3c735c694624b273dcd7da2f8bd13a5ac2b36a8ad39737b1d062`",
                ephemeral=True
            )
            return
        
        result = await self.bot.bonus_service.add_corp(corp_id, name)
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Corporation Added",
                color=discord.Color.green(),
                description=result["message"]
            )
            embed.add_field(
                name="Corporation ID",
                value=f"`{corp_id[:32]}...`",
                inline=False
            )
            if result.get("bonus") is not None:
                embed.add_field(
                    name="Current Bonus",
                    value=f"{result['bonus']}%",
                    inline=True
                )
            embed.set_footer(text="Bonuses will be updated hourly")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                f"❌ {result['message']}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="remove_corporation",
        description="Remove a corporation from auto-fetch (Admin only)"
    )
    @app_commands.describe(
        corp_id="The corporation ID to remove"
    )
    async def remove_corporation(
        self,
        interaction: discord.Interaction,
        corp_id: str
    ):
        """Remove a corporation from tracking."""
        if interaction.user.id not in ALLOWED_IDS:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        result = await self.bot.bonus_service.remove_corp(corp_id)
        
        if result["success"]:
            await interaction.followup.send(
                f"✅ {result['message']}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ {result['message']}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="list_corporations",
        description="List all tracked corporations with their bonuses"
    )
    async def list_corporations(self, interaction: discord.Interaction):
        """List all tracked corporations."""
        corps = self.bot.bonus_service.get_active_bonuses()
        
        if not corps:
            # Check if any tracked corps exist at all
            all_tracked = self.bot.bonus_service.get_all_tracked()
            if not all_tracked:
                await interaction.response.send_message(
                    "📭 No corporations are currently being tracked.\n"
                    "Use `/add_corporation` to start tracking.",
                    ephemeral=True
                )
                return
            else:
                await interaction.response.send_message(
                    "📭 No active bonuses found. Check back after the next update.",
                    ephemeral=True
                )
                return
        
        embed = discord.Embed(
            title="🏢 Tracked Corporations",
            color=discord.Color.gold()
        )
        
        description = []
        for corp in corps[:15]:  # Show up to 15
            bonus_str = f"{corp['bonus_pct']}%" if corp['bonus_pct'] else "❌ Not found"
            last_fetched = corp['last_fetched'][:16] if corp['last_fetched'] else "Never"
            description.append(
                f"**{corp['corp_name']}** — `{bonus_str}`\n"
                f"  └ Updated: {last_fetched}"
            )
        
        embed.description = "\n\n".join(description)
        embed.set_footer(text=f"Total: {len(corps)} corporations with bonuses")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="force_update_bonuses",
        description="Force an immediate update of all bonuses (Admin only)"
    )
    async def force_update_bonuses(self, interaction: discord.Interaction):
        """Manually trigger bonus update."""
        if interaction.user.id not in ALLOWED_IDS:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        updated = await self.bot.bonus_service.update_all_bonuses()
        
        await interaction.followup.send(
            f"✅ Updated bonuses for **{updated}** corporations.\n"
            f"Use `/list_corporations` to see the results.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(BonusCog(bot))
