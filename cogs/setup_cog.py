import logging
import discord
from discord import app_commands
from discord.ext import commands
import config
from services.i18n import get as t

logger = logging.getLogger("setup_cog")


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _is_authorized(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in config.DEV_USER_IDS:
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        server = self.bot.db.get_server(interaction.guild_id)
        if server and server.get("manager_role_id"):
            role_ids = [r.id for r in interaction.user.roles]
            return server["manager_role_id"] in role_ids
        return False

    def _lang(self, guild_id: int) -> str:
        server = self.bot.db.get_server(guild_id)
        return server.get("language", "en") if server else "en"

    drs = app_commands.Group(name="drs", description="DRS Queue Bot commands")

    @drs.command(name="setup", description="Configure the DRS queue bot for this server")
    @app_commands.describe(
        queue_channel="Channel where the queue message will be posted",
        notification_channel="Channel where match threads will be created",
        officer_channel="Channel where negative run reports are sent",
        manager_role="Role allowed to manage the bot",
    )
    async def setup(
        self,
        interaction: discord.Interaction,
        queue_channel:        discord.TextChannel,
        notification_channel: discord.TextChannel,
        officer_channel:      discord.TextChannel,
        manager_role:         discord.Role,
    ):
        lang = self._lang(interaction.guild_id)
        if not self._is_authorized(interaction):
            await interaction.response.send_message(t(lang, "setup_no_auth"), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        self.bot.db.upsert_server(
            interaction.guild_id,
            queue_channel_id        = queue_channel.id,
            notification_channel_id = notification_channel.id,
            officer_channel_id      = officer_channel.id,
            manager_role_id         = manager_role.id,
        )

        server = self.bot.db.get_server(interaction.guild_id)
        queue_cog = self.bot.cogs.get("QueueCog")
        if queue_cog:
            await queue_cog._ensure_queue_message(server)

        embed = discord.Embed(title=t(lang, "setup_success_title"), color=discord.Color.green())
        embed.add_field(name="Queue channel",        value=queue_channel.mention,        inline=False)
        embed.add_field(name="Notification channel", value=notification_channel.mention, inline=False)
        embed.add_field(name="Officer channel",      value=officer_channel.mention,      inline=False)
        embed.add_field(name="Manager role",         value=manager_role.mention,         inline=False)
        embed.set_footer(text=t(lang, "setup_footer"))

        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info(f"Server {interaction.guild_id} configured by {interaction.user}")

    @drs.command(name="roles", description="Set ping roles for each DRS and RS level (all optional)")
    @app_commands.describe(
        drs7="Role to ping when someone joins DRS7",
        drs8="Role to ping when someone joins DRS8",
        drs9="Role to ping when someone joins DRS9",
        drs10="Role to ping when someone joins DRS10",
        drs11="Role to ping when someone joins DRS11",
        drs12="Role to ping when someone joins DRS12",
        rs4="Role to ping when someone joins RS4",
        rs5="Role to ping when someone joins RS5",
        rs6="Role to ping when someone joins RS6",
        rs7="Role to ping when someone joins RS7",
        rs8="Role to ping when someone joins RS8",
        rs9="Role to ping when someone joins RS9",
        rs10="Role to ping when someone joins RS10",
        rs11="Role to ping when someone joins RS11",
        rs12="Role to ping when someone joins RS12",
    )
    async def roles(
        self,
        interaction: discord.Interaction,
        drs7:  discord.Role | None = None,
        drs8:  discord.Role | None = None,
        drs9:  discord.Role | None = None,
        drs10: discord.Role | None = None,
        drs11: discord.Role | None = None,
        drs12: discord.Role | None = None,
        rs4:   discord.Role | None = None,
        rs5:   discord.Role | None = None,
        rs6:   discord.Role | None = None,
        rs7:   discord.Role | None = None,
        rs8:   discord.Role | None = None,
        rs9:   discord.Role | None = None,
        rs10:  discord.Role | None = None,
        rs11:  discord.Role | None = None,
        rs12:  discord.Role | None = None,
    ):
        lang = self._lang(interaction.guild_id)
        if not self._is_authorized(interaction):
            await interaction.response.send_message(t(lang, "setup_no_auth"), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        updates = {}
        drs_role_map = {7: drs7, 8: drs8, 9: drs9, 10: drs10, 11: drs11, 12: drs12}
        rs_role_map = {4: rs4, 5: rs5, 6: rs6, 7: rs7, 8: rs8, 9: rs9, 10: rs10, 11: rs11, 12: rs12}

        for level, role in drs_role_map.items():
            if role is not None:
                updates[f"role_drs{level}"] = role.id
        for level, role in rs_role_map.items():
            if role is not None:
                updates[f"role_rs{level}"] = role.id

        if updates:
            self.bot.db.upsert_server(interaction.guild_id, **updates)

        embed = discord.Embed(title=t(lang, "setup_roles_success"), color=discord.Color.green())
        for level, role in drs_role_map.items():
            if role is not None:
                embed.add_field(name=f"DRS{level}", value=role.mention, inline=True)
        for level, role in rs_role_map.items():
            if role is not None:
                embed.add_field(name=f"RS{level}", value=role.mention, inline=True)

        server = self.bot.db.get_server(interaction.guild_id)
        for level in config.VALID_DRS_LEVELS:
            role_id = server.get(f"role_drs{level}") if server else None
            if role_id and drs_role_map.get(level) is None:
                embed.add_field(name=f"DRS{level}", value=f"<@&{role_id}> (existing)", inline=True)
        for level in config.VALID_RS_LEVELS:
            role_id = server.get(f"role_rs{level}") if server else None
            if role_id and rs_role_map.get(level) is None:
                embed.add_field(name=f"RS{level}", value=f"<@&{role_id}> (existing)", inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @drs.command(name="language", description="Set the display language for this server")
    @app_commands.describe(language="Choose a language")
    @app_commands.choices(language=[
        app_commands.Choice(name="English",  value="en"),
        app_commands.Choice(name="Japanese", value="ja"),
        app_commands.Choice(name="Spanish",  value="es"),
        app_commands.Choice(name="German",   value="de"),
        app_commands.Choice(name="Hindi",    value="hi"),
        app_commands.Choice(name="Polish",   value="pl"),
        app_commands.Choice(name="French",   value="fr"),
    ])
    async def language(self, interaction: discord.Interaction, language: app_commands.Choice[str]):
        lang = self._lang(interaction.guild_id)
        if not self._is_authorized(interaction):
            await interaction.response.send_message(t(lang, "setup_no_auth"), ephemeral=True)
            return
        self.bot.db.upsert_server(interaction.guild_id, language=language.value)
        await interaction.response.send_message(
            t(language.value, "lang_set", lang=language.name), ephemeral=True
        )

    @drs.command(name="status", description="Show current bot configuration for this server")
    async def status(self, interaction: discord.Interaction):
        lang = self._lang(interaction.guild_id)
        if not self._is_authorized(interaction):
            await interaction.response.send_message(t(lang, "setup_no_auth"), ephemeral=True)
            return

        server = self.bot.db.get_server(interaction.guild_id)
        if not server:
            await interaction.response.send_message(t(lang, "status_not_setup"), ephemeral=True)
            return

        def fmt_channel(cid): return f"<#{cid}>" if cid else "*(not set)*"
        def fmt_role(rid):    return f"<@&{rid}>" if rid else "*(not set)*"

        embed = discord.Embed(title=t(lang, "status_title"), color=discord.Color.blurple())
        embed.add_field(name="Queue channel",        value=fmt_channel(server["queue_channel_id"]),        inline=False)
        embed.add_field(name="Notification channel", value=fmt_channel(server["notification_channel_id"]), inline=False)
        embed.add_field(name="Officer channel",      value=fmt_channel(server["officer_channel_id"]),      inline=False)
        embed.add_field(name="Manager role",         value=fmt_role(server["manager_role_id"]),            inline=False)
        embed.add_field(name="Language",             value=server.get("language", "en"),                   inline=False)

        ping_roles = []
        for level in config.DRS_LEVELS:
            role_id = server.get(f"role_drs{level}")
            if role_id:
                ping_roles.append(f"DRS{level}: <@&{role_id}>")
        if ping_roles:
            embed.add_field(name="Ping roles", value="\n".join(ping_roles), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SetupCog(bot))

