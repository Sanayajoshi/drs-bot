import logging
import discord
from discord import app_commands
from discord.ext import commands
import config
from services.investigation_service import InvestigationService

logger = logging.getLogger("investigation_cog")

ALLOWED_SERVER_ID = getattr(config, "INVESTIGATION_SERVER_ID", 536065295828254732)
ALLOWED_CHANNEL_ID = getattr(config, "INVESTIGATION_CHANNEL_ID", 1542296884872486993)
ALLOWED_ROLE_ID = getattr(config, "INVESTIGATION_ROLE_ID", 1541597375502749838)


def is_investigation_authorized(interaction: discord.Interaction) -> tuple[bool, str]:
    """
    Validates that the interaction is executed:
    1. Inside the designated Discord server (536065295828254732)
    2. Inside the designated channel (1542296884872486993)
    3. By a user with the required role (1541597375502749838) or super admin
    """
    if interaction.guild_id != ALLOWED_SERVER_ID:
        return False, "❌ **Unauthorized Server**: This command is strictly restricted to the designated investigation server."

    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return False, f"❌ **Unauthorized Channel**: This command can only be executed in <#{ALLOWED_CHANNEL_ID}>."

    # Check for designated role
    member_roles = getattr(interaction.user, "roles", [])
    has_role = any(r.id == ALLOWED_ROLE_ID for r in member_roles)

    # Super admin / Dev fallback
    super_admin_ids = getattr(config, "SUPER_ADMIN_IDS", [])
    dev_user_ids = getattr(config, "DEV_USER_IDS", [])
    is_admin = interaction.user.id in super_admin_ids or interaction.user.id in dev_user_ids

    if not (has_role or is_admin):
        return False, f"❌ **Access Denied**: You require the designated Officer role (<@&{ALLOWED_ROLE_ID}>) to run investigation commands."

    return True, ""


class InvestigationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.service = InvestigationService(bot.db)

    investigate_group = app_commands.Group(
        name="investigate",
        description="Officer incident auditing, player investigation, and conduct reporting"
    )

    # ------------------------------------------------------------------
    # /investigate player <player>
    # ------------------------------------------------------------------
    @investigate_group.command(
        name="player",
        description="Audit an individual player's full incident dossier, conduct history, and ticket records."
    )
    @app_commands.describe(player="The player or member to investigate")
    async def player_cmd(self, interaction: discord.Interaction, player: discord.User):
        authorized, err_msg = is_investigation_authorized(interaction)
        if not authorized:
            await interaction.response.send_message(err_msg, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        try:
            dossier = self.service.get_player_dossier(player.id)
            # If interaction target has display name, prefer it
            if hasattr(player, "display_name") and player.display_name:
                dossier["display_name"] = player.display_name

            embed = self.service.build_player_dossier_embed(dossier)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error executing /investigate player for {player.id}: {e}", exc_info=True)
            await interaction.followup.send("❌ An error occurred while generating the player dossier.", ephemeral=True)

    # ------------------------------------------------------------------
    # /investigate log [timeframe] [issue_type] [status] [limit]
    # ------------------------------------------------------------------
    @investigate_group.command(
        name="log",
        description="View filtered incident report ledger by timeframe, issue category, and status."
    )
    @app_commands.describe(
        timeframe="Timeframe filter (default: Last 30 Days)",
        issue_type="Filter by specific infraction category",
        status="Filter by investigation status (Open or Resolved)",
        limit="Maximum number of tickets to display (default: 10, max: 25)"
    )
    @app_commands.choices(
        timeframe=[
            app_commands.Choice(name="Last 30 Days", value="30d"),
            app_commands.Choice(name="Last 7 Days", value="7d"),
            app_commands.Choice(name="Last Month (Calendar)", value="last_month"),
            app_commands.Choice(name="All Time", value="all"),
        ],
        issue_type=[
            app_commands.Choice(name="All Types", value="all"),
            app_commands.Choice(name="No Show 👻", value="no_show"),
            app_commands.Choice(name="Behavior 🚨", value="behavior"),
            app_commands.Choice(name="Performance 📉", value="performance"),
            app_commands.Choice(name="Other ❓", value="other"),
        ],
        status=[
            app_commands.Choice(name="All Statuses", value="all"),
            app_commands.Choice(name="🔴 Open Only", value="open"),
            app_commands.Choice(name="🟢 Resolved Only", value="resolved"),
        ]
    )
    async def log_cmd(
        self,
        interaction: discord.Interaction,
        timeframe: app_commands.Choice[str] | None = None,
        issue_type: app_commands.Choice[str] | None = None,
        status: app_commands.Choice[str] | None = None,
        limit: int = 10
    ):
        authorized, err_msg = is_investigation_authorized(interaction)
        if not authorized:
            await interaction.response.send_message(err_msg, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        tf_val = timeframe.value if timeframe else "30d"
        type_val = issue_type.value if issue_type else "all"
        status_val = status.value if status else "all"
        limit_val = min(max(limit, 1), 25)

        try:
            tickets, tf_label = self.service.get_incident_logs(
                timeframe=tf_val,
                issue_type=type_val,
                status=status_val,
                limit=limit_val
            )
            embed = self.service.build_incident_logs_embed(
                tickets=tickets,
                tf_label=tf_label,
                issue_type=type_val,
                status=status_val
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error executing /investigate log: {e}", exc_info=True)
            await interaction.followup.send("❌ An error occurred while retrieving incident logs.", ephemeral=True)

    # ------------------------------------------------------------------
    # /investigate summary [timeframe]
    # ------------------------------------------------------------------
    @investigate_group.command(
        name="summary",
        description="High-level metrics summary: incident volume, breakdown, resolution rate, and repeat subjects."
    )
    @app_commands.describe(timeframe="Timeframe for the metrics summary (default: Last 30 Days)")
    @app_commands.choices(
        timeframe=[
            app_commands.Choice(name="Last 30 Days", value="30d"),
            app_commands.Choice(name="Last 7 Days", value="7d"),
            app_commands.Choice(name="Last Month (Calendar)", value="last_month"),
            app_commands.Choice(name="All Time", value="all"),
        ]
    )
    async def summary_cmd(
        self,
        interaction: discord.Interaction,
        timeframe: app_commands.Choice[str] | None = None
    ):
        authorized, err_msg = is_investigation_authorized(interaction)
        if not authorized:
            await interaction.response.send_message(err_msg, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        tf_val = timeframe.value if timeframe else "30d"

        try:
            summary, tf_label = self.service.get_incident_summary(timeframe=tf_val)
            embed = self.service.build_incident_summary_embed(summary=summary, tf_label=tf_label)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error executing /investigate summary: {e}", exc_info=True)
            await interaction.followup.send("❌ An error occurred while calculating the incident summary.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(InvestigationCog(bot))

