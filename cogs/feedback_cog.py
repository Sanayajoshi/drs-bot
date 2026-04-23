import logging
import discord
from discord.ext import commands
from services.i18n import get as t

logger = logging.getLogger("feedback_cog")


def build_feedback_view(match_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="✅", style=discord.ButtonStyle.success, custom_id=f"feedback_good_{match_id}"))
    view.add_item(discord.ui.Button(label="❌", style=discord.ButtonStyle.danger,  custom_id=f"feedback_bad_{match_id}"))
    return view


class FeedbackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _lang(self, guild_id: int) -> str:
        server = self.bot.db.get_server(guild_id)
        return server.get("language", "en") if server else "en"

    @commands.Cog.listener()
    async def on_drs_send_feedback(self, match_id: int, threads: list[dict]):
        for thread_info in threads:
            lang = thread_info.get("lang", "en")
            view = build_feedback_view(match_id)
            try:
                thread = await self.bot.fetch_channel(thread_info["thread_id"])
                await thread.send(t(lang, "feedback_prompt"), view=view)
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Failed to send feedback prompt to thread {thread_info['thread_id']}: {e}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("feedback_good_") or custom_id.startswith("feedback_bad_"):
            await self._handle_feedback(interaction, custom_id)

    async def _handle_feedback(self, interaction: discord.Interaction, custom_id: str):
        await interaction.response.defer(ephemeral=True)
        lang = self._lang(interaction.guild_id)
        parts        = custom_id.split("_")
        sentiment    = parts[1]
        match_id     = int(parts[2])
        was_positive = (sentiment == "good")

        saved = self.bot.db.save_feedback(match_id, interaction.user.id, was_positive)
        if not saved:
            await interaction.followup.send(t(lang, "feedback_error"), ephemeral=True)
            return

        await interaction.followup.send(t(lang, "feedback_thanks"), ephemeral=True)
        if not was_positive:
            await self._send_officer_alert(interaction, match_id)

    async def _send_officer_alert(self, interaction: discord.Interaction, match_id: int):
        lang   = self._lang(interaction.guild_id)
        server = self.bot.db.get_server(interaction.guild_id)
        if not server or not server.get("officer_channel_id"):
            return
        guild   = self.bot.get_guild(interaction.guild_id)
        channel = guild and guild.get_channel(server["officer_channel_id"])
        if not channel:
            return
        participants = self.bot.db.get_match_participants(match_id)
        player_names = ", ".join(p["display_name"] for p in participants)
        thread_info  = next(
            (th for th in self.bot.db.get_match_threads(match_id) if th["guild_id"] == interaction.guild_id),
            None
        )
        thread_ref = f"<#{thread_info['thread_id']}>" if thread_info else "unknown thread"
        embed = discord.Embed(title=t(lang, "officer_alert_title"), color=discord.Color.red())
        embed.add_field(name="Match ID",     value=str(match_id),                    inline=True)
        embed.add_field(name="Reported by",  value=interaction.user.display_name,    inline=True)
        embed.add_field(name="Participants", value=player_names,                     inline=False)
        embed.add_field(name="Thread",       value=thread_ref,                       inline=False)
        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send officer alert: {e}")


async def setup(bot):
    await bot.add_cog(FeedbackCog(bot))
