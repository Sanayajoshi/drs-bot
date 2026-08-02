import logging
import discord
from datetime import datetime, timezone, timedelta
from discord import app_commands
from discord.ext import commands, tasks
import config
from services.facts_service import FactsService

logger = logging.getLogger("engagement_cog")


class EngagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.facts_service = FactsService(bot.db)
        self.auto_facts_loop.start()

    def cog_unload(self):
        self.auto_facts_loop.cancel()

    def _is_super_admin(self, user_id: int) -> bool:
        return user_id in config.SUPER_ADMIN_IDS

    def _is_authorized_officer(self, interaction: discord.Interaction) -> bool:
        if self._is_super_admin(interaction.user.id):
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        server = self.bot.db.get_server(interaction.guild_id)
        if server and server.get("manager_role_id"):
            role_ids = [r.id for r in getattr(interaction.user, "roles", [])]
            return server["manager_role_id"] in role_ids
        return False

    # ------------------------------------------------------------------
    # Slash Commands
    # ------------------------------------------------------------------

    @app_commands.command(name="postfact", description="Immediately post a random engagement fact (Super Admin only)")
    async def post_fact_slash(self, interaction: discord.Interaction):
        if not self._is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                "❌ Only Super Admins can execute this command.", ephemeral=True
            )
            return

        embed = self.facts_service.get_random_fact_embed()
        await interaction.channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )
        await interaction.response.send_message(
            "✅ Random engagement fact posted immediately to this channel!", ephemeral=True
        )

    @app_commands.command(name="setfactfrequency", description="Set engagement fact posting frequency in hours")
    @app_commands.describe(hours="Frequency in hours (default: 4)")
    async def set_fact_frequency_slash(self, interaction: discord.Interaction, hours: int):
        if not self._is_authorized_officer(interaction):
            await interaction.response.send_message(
                "❌ You do not have permission to change facts frequency.", ephemeral=True
            )
            return

        hours = max(1, min(168, hours))
        self.bot.db.set_fact_frequency(interaction.guild_id, hours)
        await interaction.response.send_message(
            f"✅ Engagement facts frequency set to every **{hours} hour(s)** for this server.",
            ephemeral=True
        )

    # ------------------------------------------------------------------
    # Prefix Commands (!postfact & !setfactfrequency)
    # ------------------------------------------------------------------

    @commands.command(name="postfact")
    async def post_fact_prefix(self, ctx: commands.Context):
        if not self._is_super_admin(ctx.author.id):
            await ctx.send("❌ Only Super Admins can execute this command.")
            return

        embed = self.facts_service.get_random_fact_embed()
        await ctx.channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @commands.command(name="setfactfrequency")
    async def set_fact_frequency_prefix(self, ctx: commands.Context, hours: int = 4):
        if not self._is_super_admin(ctx.author.id) and not getattr(ctx.author.guild_permissions, "administrator", False):
            await ctx.send("❌ You do not have permission to execute this command.")
            return

        hours = max(1, min(168, hours))
        self.bot.db.set_fact_frequency(ctx.guild.id, hours)
        await ctx.send(f"✅ Engagement facts frequency set to every **{hours} hour(s)** for this server.")

    # ------------------------------------------------------------------
    # Automated Facts Loop (default 4 hours)
    # ------------------------------------------------------------------

    @tasks.loop(minutes=30)
    async def auto_facts_loop(self):
        try:
            now = datetime.now(timezone.utc)
            servers = self.bot.db.get_all_servers()
            for srv in servers:
                guild_id = srv["guild_id"]
                notif_channel_id = srv.get("notification_channel_id")
                if not notif_channel_id:
                    continue

                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                channel = guild.get_channel(notif_channel_id)
                if not channel:
                    continue

                freq_hours = srv.get("fact_frequency_hours") or 4
                last_sent_str = srv.get("last_fact_sent")

                should_send = False
                if not last_sent_str:
                    should_send = True
                else:
                    try:
                        last_sent = datetime.strptime(last_sent_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                        if (now - last_sent) >= timedelta(hours=freq_hours):
                            should_send = True
                    except Exception:
                        should_send = True

                if should_send:
                    embed = self.facts_service.get_random_fact_embed()
                    try:
                        await channel.send(
                            embed=embed,
                            allowed_mentions=discord.AllowedMentions.none()
                        )
                        self.bot.db.update_last_fact_sent(guild_id)
                        logger.info(f"Posted automated fact to guild {guild_id}")
                    except Exception as e:
                        logger.error(f"Failed to post automated fact to guild {guild_id}: {e}")
        except Exception as e:
            logger.error(f"Error in auto_facts_loop: {e}", exc_info=True)

    @auto_facts_loop.before_loop
    async def before_auto_facts_loop(self):
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------
    # New Corp (Guild) Joined Announcement
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.db.upsert_server(guild.id)
        logger.info(f"EngagementCog: Joined new guild {guild.name} ({guild.id})")

        # Find target channel to post announcement
        target_channel = guild.system_channel
        if not target_channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    target_channel = ch
                    break

        if not target_channel:
            return

        # Check for super admins present in this guild
        admin_members = [
            m for uid in config.SUPER_ADMIN_IDS
            if (m := guild.get_member(uid)) is not None
        ]

        if admin_members:
            admin_pings = " ".join([m.mention for m in admin_members])
            announcement = (
                f"🎉 **New Corporation Connected!** Welcome **{guild.name}** to the Dark Red Star Network!\n"
                f"Honored to have Super Admin(s) present: {admin_pings}"
            )
        else:
            announcement = (
                f"🎉 **New Corporation Connected!** Welcome **{guild.name}** to the Dark Red Star Network!"
            )

        embed = discord.Embed(
            title="🚀 DRS Dispatch Engine Online",
            description=(
                f"The DRS Queue Bot is now active in **{guild.name}**!\n\n"
                "• **Queues & Matchmaking**: Configurable DRS7–DRS12 queues\n"
                "• **Engagement & Stats**: Automatic stats dispatches every 4 hours\n"
                "• **Commands**: Use `/drs setup` to configure channels, `/postfact` to share stats, or `/setfactfrequency` to adjust timing!"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="DRS Engagement Network • Super Admin Alert")

        try:
            await target_channel.send(content=announcement, embed=embed)
        except Exception as e:
            logger.error(f"Failed to send on_guild_join announcement in {guild.id}: {e}")


async def setup(bot):
    await bot.add_cog(EngagementCog(bot))

