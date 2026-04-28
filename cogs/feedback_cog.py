"""
feedback_cog.py — Post-match feedback and structured issue reports.

Flow:
  1. Bot sends feedback message in match thread after FEEDBACK_DELAY_MINS.
  2. ✅ Good Run  → ephemeral thanks, saved to DB.
  3. ⚠️ Report    → Modal opens with:
                     - Select: which player?   (ui.Label + ui.Select)
                     - Select: what issue?     (ui.Label + ui.Select)
                     - TextInput: optional comment
  4. Submit       → saved to feedback_reports, mod alert if applicable.

Mod alerts fire for: Behavior, Performance, Other (not No Show).
One submission per participant per match. Ephemeral throughout.
"""

import logging
import discord
from discord.ext import commands
from discord import ui
from services.i18n import get as t

logger = logging.getLogger("feedback_cog")


# ---------------------------------------------------------------------------
# Issue config
# ---------------------------------------------------------------------------

ISSUE_LABELS = {
    "no_show":     "No Show 👻",
    "behavior":    "Behavior 🚨",
    "performance": "Performance 📉",
    "other":       "Other ❓",
}

# No Show is logged only — no mod alert
ALERT_ISSUE_TYPES = {"behavior", "performance", "other"}


# ---------------------------------------------------------------------------
# Step 1 — feedback view posted in the match thread
# ---------------------------------------------------------------------------

def build_feedback_view(match_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(
        label="Good Run ✅",
        style=discord.ButtonStyle.success,
        custom_id=f"fb_good_{match_id}",
        row=0,
    ))
    view.add_item(discord.ui.Button(
        label="Report Issue ⚠️",
        style=discord.ButtonStyle.danger,
        custom_id=f"fb_report_{match_id}",
        row=0,
    ))
    return view


# ---------------------------------------------------------------------------
# Report modal — uses ui.Label + ui.Select pattern (same as reference code)
# ---------------------------------------------------------------------------

class ReportModal(ui.Modal):
    def __init__(self, match_id: int, participants: list[dict]):
        super().__init__(title="DRS Match Report")
        self.match_id = match_id

        player_options = [
            discord.SelectOption(
                label=p["display_name"][:100],
                value=str(p["discord_id"]),
            )
            for p in participants
        ]

        self.player_select_label = ui.Label(
            text="Who are you reporting?",
            component=ui.Select(
                placeholder="Select a player…",
                options=player_options,
                min_values=1,
                max_values=1,
            )
        )

        self.issue_select_label = ui.Label(
            text="What is the issue?",
            component=ui.Select(
                placeholder="Select issue type…",
                options=[
                    discord.SelectOption(label="No Show",     value="no_show",     emoji="👻",
                                         description="Player didn't appear for the match"),
                    discord.SelectOption(label="Behavior",    value="behavior",    emoji="🚨",
                                         description="Unsportsmanlike or abusive conduct"),
                    discord.SelectOption(label="Performance", value="performance", emoji="📉",
                                         description="Poor performance or hindered the run"),
                    discord.SelectOption(label="Other",       value="other",       emoji="❓",
                                         description="Something else — add details below"),
                ],
                min_values=1,
                max_values=1,
            )
        )

        self.comment = ui.TextInput(
            label="Additional Comments (optional)",
            placeholder="Describe what happened…",
            required=False,
            max_length=500,
            style=discord.TextStyle.paragraph,
        )

        self.add_item(self.player_select_label)
        self.add_item(self.issue_select_label)
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            reported_id = int(self.player_select_label.component.values[0])
            issue_type  = self.issue_select_label.component.values[0]
            comment     = self.comment.value.strip() or None
            thread_id   = (
                interaction.channel_id
                if isinstance(interaction.channel, discord.Thread)
                else None
            )

            cog = interaction.client.cogs.get("FeedbackCog")
            if cog:
                await cog._submit_report(
                    interaction,
                    match_id    = self.match_id,
                    reported_id = reported_id,
                    issue_type  = issue_type,
                    comment     = comment,
                    thread_id   = thread_id,
                )
            else:
                await interaction.response.send_message("❌ Internal error.", ephemeral=True)

        except Exception as e:
            import traceback; traceback.print_exc()
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"ReportModal error: {error}", exc_info=True)
        await interaction.response.send_message("❌ Something went wrong. Try again.", ephemeral=True)


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class FeedbackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _lang(self, guild_id: int) -> str:
        server = self.bot.db.get_server(guild_id)
        return server.get("language", "en") if server else "en"

    # ------------------------------------------------------------------
    # Dispatch listener — called by thread_cog after FEEDBACK_DELAY_MINS
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Interaction router
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("fb_good_"):
            match_id = int(custom_id.split("_")[-1])
            await self._handle_good(interaction, match_id)

        elif custom_id.startswith("fb_report_"):
            match_id = int(custom_id.split("_")[-1])
            await self._handle_report(interaction, match_id)

    # ------------------------------------------------------------------
    # ✅ Good run
    # ------------------------------------------------------------------

    async def _handle_good(self, interaction: discord.Interaction, match_id: int):
        await interaction.response.defer(ephemeral=True)
        lang = self._lang(interaction.guild_id)

        participants    = self.bot.db.get_match_participants(match_id)
        participant_ids = {p["discord_id"] for p in participants}

        if interaction.user.id not in participant_ids:
            await interaction.followup.send(t(lang, "feedback_not_participant"), ephemeral=True)
            return

        if self.bot.db.has_submitted_feedback(match_id, interaction.user.id):
            await interaction.followup.send(t(lang, "feedback_already_submitted"), ephemeral=True)
            return

        saved = self.bot.db.save_feedback(match_id, interaction.user.id, was_positive=True)
        if not saved:
            await interaction.followup.send(t(lang, "feedback_error"), ephemeral=True)
            return

        await interaction.followup.send(t(lang, "feedback_thanks"), ephemeral=True)

    # ------------------------------------------------------------------
    # ⚠️ Report — open modal directly
    # ------------------------------------------------------------------

    async def _handle_report(self, interaction: discord.Interaction, match_id: int):
        lang = self._lang(interaction.guild_id)

        participants    = self.bot.db.get_match_participants(match_id)
        participant_ids = {p["discord_id"] for p in participants}

        if interaction.user.id not in participant_ids:
            await interaction.response.send_message(
                t(lang, "feedback_not_participant"), ephemeral=True
            )
            return

        if self.bot.db.has_submitted_feedback(match_id, interaction.user.id):
            await interaction.response.send_message(
                t(lang, "feedback_already_submitted"), ephemeral=True
            )
            return

        others = [p for p in participants if p["discord_id"] != interaction.user.id]
        if not others:
            await interaction.response.send_message(
                t(lang, "feedback_no_others"), ephemeral=True
            )
            return

        await interaction.response.send_modal(ReportModal(match_id, others))

    # ------------------------------------------------------------------
    # Submit — called from ReportModal.on_submit
    # ------------------------------------------------------------------

    async def _submit_report(
        self,
        interaction: discord.Interaction,
        match_id: int,
        reported_id: int,
        issue_type: str,
        comment: str | None,
        thread_id: int | None,
    ):
        lang = self._lang(interaction.guild_id)

        participants  = self.bot.db.get_match_participants(match_id)
        reported      = next((p for p in participants if p["discord_id"] == reported_id), None)
        reported_name = reported["display_name"] if reported else "Unknown"

        # Save to main feedback table (was_positive=False blocks re-submission)
        self.bot.db.save_feedback(match_id, interaction.user.id, was_positive=False)

        # Save structured report
        saved = self.bot.db.save_feedback_report(
            match_id           = match_id,
            reporter_id        = interaction.user.id,
            reported_player_id = reported_id,
            issue_type         = issue_type,
            comment            = comment,
            thread_id          = thread_id,
        )
        if not saved:
            await interaction.response.send_message(t(lang, "feedback_error"), ephemeral=True)
            return

        await interaction.response.send_message(
            t(lang, "report_thanks", name=reported_name),
            ephemeral=True,
        )

        if issue_type in ALERT_ISSUE_TYPES:
            await self._send_officer_alert(
                interaction   = interaction,
                match_id      = match_id,
                reported_id   = reported_id,
                reported_name = reported_name,
                issue_type    = issue_type,
                comment       = comment,
                thread_id     = thread_id,
            )

    # ------------------------------------------------------------------
    # Officer alert
    # ------------------------------------------------------------------

    async def _send_officer_alert(
        self,
        interaction: discord.Interaction,
        match_id: int,
        reported_id: int,
        reported_name: str,
        issue_type: str,
        comment: str | None,
        thread_id: int | None,
    ):
        lang   = self._lang(interaction.guild_id)
        server = self.bot.db.get_server(interaction.guild_id)
        if not server or not server.get("officer_channel_id"):
            return

        guild   = self.bot.get_guild(interaction.guild_id)
        channel = guild and guild.get_channel(server["officer_channel_id"])
        if not channel:
            return

        match_info  = self.bot.db._execute(
            "SELECT drs_level FROM matches WHERE id = ?", (match_id,), fetch_one=True
        )
        drs_level   = match_info["drs_level"] if match_info else "?"
        issue_label = ISSUE_LABELS.get(issue_type, issue_type)
        thread_ref  = f"<#{thread_id}>" if thread_id else "*(no thread)*"

        embed = discord.Embed(
            title       = t(lang, "officer_alert_title"),
            color       = discord.Color.red(),
            description = f"A pilot filed a report for **Match #{match_id}** (DRS{drs_level}).",
        )
        embed.add_field(name="Reported Player", value=f"**{reported_name}** (<@{reported_id}>)",                     inline=True)
        embed.add_field(name="Reported By",     value=f"{interaction.user.display_name} (<@{interaction.user.id}>)", inline=True)
        embed.add_field(name="Issue",           value=issue_label,                                                   inline=True)
        embed.add_field(name="Thread",          value=thread_ref,                                                    inline=True)
        embed.add_field(name="Match ID",        value=str(match_id),                                                 inline=True)

        if comment:
            embed.add_field(name="Comment", value=comment[:1024], inline=False)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send officer alert: {e}")


async def setup(bot):
    await bot.add_cog(FeedbackCog(bot))
