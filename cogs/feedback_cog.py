"""
feedback_cog.py — Post-match feedback and structured issue reports.

Flow:
  1. Feedback prompt sent to match threads (scheduled / loop recovery across restarts).
  2. ✅ Good Run  → ephemeral thanks, saved to DB.
  3. ⚠️ Report    → Modal opens to select reported player, issue type, and comment.
  4. Negative report creates linked officer investigation threads in all involved servers' officer channels.
  5. Messages in officer investigation threads are relayed cross-server.
  6. Officers can click "Resolve & Close" to archive linked threads across servers.
"""

import logging
import discord
from discord.ext import commands, tasks
from discord import ui
from services.i18n import get as t
import config

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

ALERT_ISSUE_TYPES = {"no_show", "behavior", "performance", "other"}


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


def build_resolve_view(report_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(
        label="Resolve & Close Investigation 🔒",
        style=discord.ButtonStyle.secondary,
        custom_id=f"fb_resolve_{report_id}",
        row=0,
    ))
    return view


# ---------------------------------------------------------------------------
# Report modal
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
            logger.error(f"ReportModal on_submit failed: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"ReportModal error: {error}", exc_info=True)
        await interaction.response.send_message("❌ Something went wrong. Try again.", ephemeral=True)


class ResolveModal(ui.Modal, title="Resolve Incident"):
    notes = ui.TextInput(
        label="Resolution Notes (optional)",
        placeholder="How was this incident resolved?",
        required=False,
        max_length=400,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, report_id: int):
        super().__init__()
        self.report_id = report_id

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.cogs.get("FeedbackCog")
        if cog:
            await cog._resolve_report_action(interaction, self.report_id, self.notes.value.strip() or "No notes provided.")
        else:
            await interaction.response.send_message("❌ Internal error.", ephemeral=True)


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class FeedbackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.feedback_recovery_loop.start()

    def cog_unload(self):
        self.feedback_recovery_loop.cancel()

    def _lang(self, guild_id: int) -> str:
        server = self.bot.db.get_server(guild_id)
        return server.get("language", "en") if server else "en"

    # ------------------------------------------------------------------
    # Periodic check to ensure feedback is sent even after bot restarts
    # ------------------------------------------------------------------

    @tasks.loop(minutes=1.0)
    async def feedback_recovery_loop(self):
        try:
            pending_matches = self.bot.db.get_pending_feedback_matches(config.FEEDBACK_DELAY_MINS)
            for m in pending_matches:
                match_id = m["id"]
                logger.info(f"Feedback loop: dispatching feedback prompt for Match #{match_id}")
                await self.send_match_feedback_prompt(match_id)
        except Exception as e:
            logger.error(f"Error in feedback_recovery_loop: {e}")

    @feedback_recovery_loop.before_loop
    async def before_feedback_recovery(self):
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------
    # Dispatch listener
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_drs_send_feedback(self, match_id: int, threads: list[dict] = None):
        await self.send_match_feedback_prompt(match_id, threads)

    async def send_match_feedback_prompt(self, match_id: int, threads: list[dict] = None):
        """Sends feedback prompt to all active match threads and marks DB atomically."""
        # Atomically claim sending feedback for this match
        if not self.bot.db.mark_match_feedback_sent(match_id):
            logger.info(f"Feedback already sent for Match #{match_id}, skipping duplicate.")
            return

        if not threads:
            db_threads = self.bot.db.get_match_threads(match_id)
            threads = [{"guild_id": t["guild_id"], "thread_id": t["thread_id"], "lang": self._lang(t["guild_id"])} for t in db_threads]

        if not threads:
            return

        view = build_feedback_view(match_id)

        for thread_info in threads:
            lang = thread_info.get("lang") or self._lang(thread_info.get("guild_id", 0))
            try:
                thread = await self.bot.fetch_channel(thread_info["thread_id"])
                if isinstance(thread, discord.Thread) and not thread.archived:
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

        elif custom_id.startswith("fb_resolve_"):
            report_id = int(custom_id.split("_")[-1])
            await self._handle_resolve_button(interaction, report_id)

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
        report_id = self.bot.db.save_feedback_report(
            match_id           = match_id,
            reporter_id        = interaction.user.id,
            reported_player_id = reported_id,
            issue_type         = issue_type,
            comment            = comment,
            thread_id          = thread_id,
        )
        if not report_id:
            await interaction.response.send_message(t(lang, "feedback_error"), ephemeral=True)
            return

        await interaction.response.send_message(
            t(lang, "report_thanks", name=reported_name),
            ephemeral=True,
        )

        if issue_type in ALERT_ISSUE_TYPES:
            await self._create_officer_investigation_threads(
                report_id     = report_id,
                match_id      = match_id,
                reporter_id   = interaction.user.id,
                reporter_name = interaction.user.display_name,
                reported_id   = reported_id,
                reported_name = reported_name,
                issue_type    = issue_type,
                comment       = comment,
                thread_id     = thread_id,
                reporter_guild_id = interaction.guild_id,
            )

    # ------------------------------------------------------------------
    # Officer investigation thread creation across all involved servers
    # ------------------------------------------------------------------

    async def _create_officer_investigation_threads(
        self,
        report_id: int,
        match_id: int,
        reporter_id: int,
        reporter_name: str,
        reported_id: int,
        reported_name: str,
        issue_type: str,
        comment: str | None,
        thread_id: int | None,
        reporter_guild_id: int | None,
    ):
        participants = self.bot.db.get_match_participants(match_id)
        involved_guild_ids = {p["queue_guild_id"] for p in participants if p.get("queue_guild_id")}
        if reporter_guild_id:
            involved_guild_ids.add(reporter_guild_id)

        match_info = self.bot.db._execute("SELECT drs_level FROM matches WHERE id = ?", (match_id,), fetch_one=True)
        drs_level = match_info["drs_level"] if match_info else "?"
        issue_label = ISSUE_LABELS.get(issue_type, issue_type)
        thread_ref = f"<#{thread_id}>" if thread_id else "*(no thread)*"

        thread_name = f"🚨-report-{report_id}-m{match_id}-{issue_type[:8]}"

        for guild_id in involved_guild_ids:
            server = self.bot.db.get_server(guild_id)
            if not server or not server.get("officer_channel_id"):
                continue

            guild = self.bot.get_guild(guild_id)
            channel = guild and guild.get_channel(server["officer_channel_id"])
            if not channel and server.get("officer_channel_id"):
                try:
                    channel = await self.bot.fetch_channel(server["officer_channel_id"])
                except Exception:
                    channel = None
            if not channel:
                continue

            lang = server.get("language", "en")

            embed = discord.Embed(
                title=f"🚨 Officer Investigation — Match #{match_id} (DRS{drs_level})",
                color=discord.Color.red(),
                description=(
                    f"A negative report was filed for **Match #{match_id}**.\n"
                    f"💬 *Messages sent in this thread are automatically relayed to officer channels in all participating servers.*"
                ),
            )
            embed.add_field(name="Reported Player", value=f"**{reported_name}** (<@{reported_id}>)", inline=True)
            embed.add_field(name="Reported By", value=f"{reporter_name} (<@{reporter_id}>)", inline=True)
            embed.add_field(name="Issue", value=issue_label, inline=True)
            embed.add_field(name="Original Thread", value=thread_ref, inline=True)
            embed.add_field(name="Report ID", value=f"#{report_id}", inline=True)

            if comment:
                embed.add_field(name="Comment", value=comment[:1024], inline=False)

            view = build_resolve_view(report_id)

            try:
                # Create thread in the officer channel
                thread = await channel.create_thread(
                    name=thread_name,
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=1440,
                )
                await thread.send(embed=embed, view=view)
                self.bot.db.save_report_thread(report_id, match_id, guild_id, channel.id, thread.id)
                logger.info(f"Created officer report thread {thread.id} in guild {guild_id} for report #{report_id}")
            except discord.Forbidden:
                logger.warning(f"Forbidden to create officer report thread in guild {guild_id}")
            except Exception as e:
                logger.error(f"Failed to create officer thread in guild {guild_id}: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Resolution Handling
    # ------------------------------------------------------------------

    async def _handle_resolve_button(self, interaction: discord.Interaction, report_id: int):
        # Check permissions
        server = self.bot.db.get_server(interaction.guild_id) if interaction.guild_id else None
        manager_role_id = server.get("manager_role_id") if server else None
        is_admin = interaction.user.guild_permissions.administrator
        is_manager = manager_role_id and any(r.id == manager_role_id for r in getattr(interaction.user, "roles", []))

        if not (is_admin or is_manager):
            await interaction.response.send_message("❌ Only officers/managers can resolve investigations.", ephemeral=True)
            return

        await interaction.response.send_modal(ResolveModal(report_id))

    async def _resolve_report_action(self, interaction: discord.Interaction, report_id: int, notes: str):
        report = self.bot.db.get_feedback_report(report_id)
        if not report:
            await interaction.response.send_message("❌ Report not found.", ephemeral=True)
            return

        self.bot.db.resolve_feedback_report(report_id, interaction.user.id, notes)
        report_threads = self.bot.db.get_report_threads(report_id)

        resolution_embed = discord.Embed(
            title=f"🔒 Investigation Resolved — Report #{report_id}",
            description=(
                f"Resolved by **{interaction.user.display_name}** (<@{interaction.user.id}>) "
                f"from **{interaction.guild.name if interaction.guild else 'Unknown'}**.\n\n"
                f"**Resolution Notes:**\n{notes}\n\n"
                f"*This thread and linked officer threads are now archived.*"
            ),
            color=discord.Color.green(),
        )

        await interaction.response.send_message("✅ Investigation resolved. Archiving threads...", ephemeral=True)

        for t_info in report_threads:
            try:
                thread = await self.bot.fetch_channel(t_info["thread_id"])
                if isinstance(thread, discord.Thread) and not thread.archived:
                    await thread.send(embed=resolution_embed)
                    await thread.edit(archived=True, locked=True)
            except Exception as e:
                logger.error(f"Failed to archive report thread {t_info['thread_id']}: {e}")

        self.bot.db.close_report_threads(report_id)


async def setup(bot):
    await bot.add_cog(FeedbackCog(bot))


