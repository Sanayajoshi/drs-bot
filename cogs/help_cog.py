import logging
import discord
from discord import app_commands
from discord.ext import commands

import config
from services.ui_service import parse_emoji

logger = logging.getLogger("drs_bot.help_cog")

# Data structure detailing all queue and match interactions using custom emojis
BUTTON_HELP_DATA = {
    "level_drs": {
        "title": f"{config.EMOJI_DRS} 7️⃣–{config.EMOJI_12} DRS Level Buttons (Row 1 & 2)",
        "emoji": parse_emoji(config.EMOJI_DRS),
        "category": "Queue Controls",
        "description": (
            "Toggle entry into **Dark Red Star (DRS 7–12)** queues.\n\n"
            f"• **Levels**: 7️⃣, 8️⃣, 9️⃣, 🔟, {config.EMOJI_11}, {config.EMOJI_12}\n"
            "• **Join/Leave**: Click a number button to join that level's queue. Click it again to leave.\n"
            "• **Multi-Queueing**: You can queue for multiple levels at once to find a match faster!\n"
            f"• **Capacity**: DRS queues trigger automatically when **3 players** join (or **2 players** if both opt into QuickStart {config.EMOJI_QUICKSTART})."
        ),
        "tips": [
            "Your queue entry stays active for 30 minutes before expiring.",
            "You'll get an alert in the notification channel 5 minutes before your queue spot expires."
        ],
        "color": discord.Color.dark_red(),
    },
    "level_rs": {
        "title": f"{config.EMOJI_RS} 4️⃣–{config.EMOJI_12} Regular RS Level Buttons (Row 0)",
        "emoji": parse_emoji(config.EMOJI_RS),
        "category": "Queue Controls",
        "description": (
            "Toggle entry into **Regular Red Star (RS 4–12)** queues.\n\n"
            f"• **Levels**: 4️⃣, 5️⃣, 6️⃣, 7️⃣, 8️⃣, 9️⃣, 🔟, {config.EMOJI_11}, {config.EMOJI_12}\n"
            "• **Join/Leave**: Click a number button to queue for Regular Red Stars.\n"
            f"• **Capacity**: Regular RS queues require **4 players** for a standard launch (or **2 to 3 players** with unanimous QuickStart {config.EMOJI_QUICKSTART})."
        ),
        "tips": [
            f"Use the Mode Switch {config.EMOJI_SWITCH} button to view RS 4–12 vs DRS 7–12 tables."
        ],
        "color": discord.Color.red(),
    },
    "mode_switch": {
        "title": f"{config.EMOJI_SWITCH} Mode Switch Button (Row 0)",
        "emoji": parse_emoji(config.EMOJI_SWITCH),
        "category": "View Controls",
        "description": (
            f"Switch the main queue display and interactions between **DRS {config.EMOJI_DRS}** and **RS {config.EMOJI_RS}** modes.\n\n"
            "• **DRS Mode**: Shows Dark Red Star 7–12 status with 3-player capacity.\n"
            "• **RS Mode**: Shows standard Red Star 4–12 queues with 4-player capacity.\n"
            "• **Queue Persistence**: Switching the view does **NOT** kick you out of queues you are already waiting in."
        ),
        "tips": [
            "Use this button to quickly glance at active players across both game modes without losing your spot."
        ],
        "color": discord.Color.blue(),
    },
    "quickstart": {
        "title": f"{config.EMOJI_QUICKSTART} QuickStart Button (Row 1)",
        "emoji": parse_emoji(config.EMOJI_QUICKSTART),
        "category": "Matchmaking",
        "description": (
            "Signal that you are ready to launch **immediately with fewer players** rather than waiting for a full group.\n\n"
            f"• **How it triggers**: Requires at least **2 players** in the queue, and **100% unanimous consent** (every queued player must have {config.EMOJI_QUICKSTART} toggled on).\n"
            f"• **DRS**: Launches with **2 players** (duo run) if both click {config.EMOJI_QUICKSTART}.\n"
            f"• **RS**: Launches with **2 or 3 players** if everyone in queue clicks {config.EMOJI_QUICKSTART}.\n"
            f"• **Solo Click**: If you are alone in queue and click {config.EMOJI_QUICKSTART}, a ⚡ icon appears next to your name and stays active until someone joins and also clicks {config.EMOJI_QUICKSTART}."
        ),
        "tips": [
            f"Clicking {config.EMOJI_QUICKSTART} again will untoggle your QuickStart readiness.",
            "Great for experienced pilots with strong fleets who don't want to wait for a 3rd or 4th teammate!"
        ],
        "color": discord.Color.gold(),
    },
    "exit": {
        "title": f"{config.EMOJI_EXIT} Exit All Queues Button (Row 2)",
        "emoji": parse_emoji(config.EMOJI_EXIT),
        "category": "Queue Controls",
        "description": (
            "Instantly removes you from **all active queues** across both DRS and RS levels.\n\n"
            "• **One-Click Leave**: Perfect when you need to step away, got busy, or found a match outside the bot.\n"
            "• **Preserves Tech**: Exiting queues does **NOT** reset your saved Genesis / Enrich / ModT module levels."
        ),
        "tips": [
            f"Always click {config.EMOJI_EXIT} if you are going AFK to avoid creating ghost matches for your teammates."
        ],
        "color": discord.Color.dark_grey(),
    },
    "tech": {
        "title": f"{config.EMOJI_TECH} Set Tech Modules ({config.EMOJI_GENESIS} {config.EMOJI_ENRICH} {config.EMOJI_MODT})",
        "emoji": parse_emoji(config.EMOJI_TECH),
        "category": "Pilot Profile",
        "description": (
            "Opens an interactive setup menu to configure your pilot's module levels:\n\n"
            f"• **Genesis ({config.EMOJI_GENESIS})**: Levels 6–15 (Generates hydrogen/asteroids)\n"
            f"• **Enrich ({config.EMOJI_ENRICH})**: Levels 6–15 (Enriches hydrogen sector)\n"
            f"• **ModT / RSE ({config.EMOJI_MODT})**: Levels 6–15 (Red Star Extender / module tech)\n\n"
            "When a match forms, the bot generates a strategic overview comparing your team's tech so you immediately know who should run Genesis or Enrich!"
        ),
        "tips": [
            "Your module levels are saved globally across all Discord servers using the bot.",
            "You only need to update this when you upgrade your modules in Hades' Star."
        ],
        "color": discord.Color.teal(),
    },
    "extend": {
        "title": "⏳ Extend Time (+30m) Button (Row 3)",
        "emoji": "⏳",
        "category": "Queue Controls",
        "description": (
            "Extends your queue expiration timer by **+30 minutes**.\n\n"
            "• **Prevent Timeout**: Queues automatically expire after 30 minutes to keep queues fresh.\n"
            "• **Warning Notification**: The bot sends a 5-minute reminder with a one-click ⏳ button in your server's notification channel before removing you."
        ),
        "tips": [
            "Click ⏳ anytime while in queue to refresh your timer back up to 30+ minutes."
        ],
        "color": discord.Color.purple(),
    },
    "sos": {
        "title": f"{config.EMOJI_SOS} Need Assist / SOS Button (Row 3)",
        "emoji": parse_emoji(config.EMOJI_SOS),
        "category": "Pilot Profile",
        "description": (
            f"Toggles an **{config.EMOJI_SOS} Need Assist** badge next to your name in queue listings and match thread cards.\n\n"
            "• **When to use**: If you are trying a higher DRS/RS level for the first time, have lower ship tech, or want experienced squadmates to help guide or carry the run.\n"
            f"• **Friendly Community**: Experienced pilots often look for {config.EMOJI_SOS} badges to offer support and guidance during matches."
        ),
        "tips": [
            f"Click {config.EMOJI_SOS} again anytime to toggle the badge off."
        ],
        "color": discord.Color.orange(),
    },
    "bell_ping": {
        "title": "🔔 Bell Ping / Ready-Up Button (Match Thread)",
        "emoji": "🔔",
        "category": "Match Coordination",
        "description": (
            "Located inside the **private match thread** created when your run forms.\n\n"
            "• **Alert Teammates**: Pings all matched participants in their respective Discord server threads.\n"
            "• **Cross-Server Sync**: Works across multiple Discord servers seamlessly!\n"
            "• **Use Case**: Use it when you are in-game with the Red Star scanner open and ready to jump."
        ),
        "tips": [
            "Only matched participants can use the 🔔 Bell Ping button inside the match thread."
        ],
        "color": discord.Color.green(),
    },
}

# Ordered emojis added as reactions to the help message
HELP_REACTIONS = [
    parse_emoji(config.EMOJI_DRS),
    parse_emoji(config.EMOJI_RS),
    parse_emoji(config.EMOJI_SWITCH),
    "▶️",
    "❌",
    "🛠️",
    "⏳",
    "🆘",
    "🔔",
    "🏠",
]


class HelpSelect(discord.ui.Select):
    """Interactive dropdown component for help embeds (especially ephemeral views)."""
    def __init__(self):
        options = [
            discord.SelectOption(
                label="🏠 Overview & Controls",
                value="home",
                description="Return to main queue overview",
            ),
            discord.SelectOption(
                label="DRS Levels (7–12)",
                value="level_drs",
                description="Dark Red Star 7-12 queue buttons",
                emoji=parse_emoji(config.EMOJI_DRS),
            ),
            discord.SelectOption(
                label="Regular RS Levels (4–12)",
                value="level_rs",
                description="Regular Red Star queue buttons",
                emoji=parse_emoji(config.EMOJI_RS),
            ),
            discord.SelectOption(
                label="Mode Switch",
                value="mode_switch",
                description="Toggle display between DRS and RS",
                emoji=parse_emoji(config.EMOJI_SWITCH),
            ),
            discord.SelectOption(
                label="QuickStart",
                value="quickstart",
                description="Early match launch (2-3 player consensus)",
                emoji=parse_emoji(config.EMOJI_QUICKSTART),
            ),
            discord.SelectOption(
                label="Exit Queues",
                value="exit",
                description="Leave all active queues in one click",
                emoji=parse_emoji(config.EMOJI_EXIT),
            ),
            discord.SelectOption(
                label="Set Tech Modules",
                value="tech",
                description="Configure Genesis, Enrich, and ModT levels",
                emoji=parse_emoji(config.EMOJI_TECH),
            ),
            discord.SelectOption(
                label="Extend Time (+30m)",
                value="extend",
                description="Refresh your 30-minute queue timer",
                emoji="⏳",
            ),
            discord.SelectOption(
                label="Need Assist / SOS",
                value="sos",
                description="Request squad assistance or beginner support",
                emoji=parse_emoji(config.EMOJI_SOS),
            ),
            discord.SelectOption(
                label="Bell Ping (Match Thread)",
                value="bell_ping",
                description="Alert your teammates in the match thread",
                emoji="🔔",
            ),
        ]
        super().__init__(
            placeholder="🔍 Select any button or topic to read full guide & tips...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        if selected_key == "home":
            embed = build_main_help_embed()
        else:
            embed = build_detail_embed(selected_key)
        await interaction.response.edit_message(embed=embed, view=self.view)


class EphemeralHelpView(discord.ui.View):
    """View containing the interactive dropdown for ephemeral help responses."""
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(HelpSelect())


def match_reaction_key(emoji: discord.PartialEmoji | str) -> str | None:
    """Helper to match user emoji reactions against help sections."""
    if isinstance(emoji, str):
        name = emoji
        eid = None
    else:
        name = emoji.name
        eid = emoji.id

    if eid:
        if str(eid) in config.EMOJI_DRS or name == "drs":
            return "level_drs"
        if str(eid) in config.EMOJI_RS or name == "rs":
            return "level_rs"
        if str(eid) in config.EMOJI_SWITCH or name == "switch":
            return "mode_switch"
        if str(eid) in config.EMOJI_GENESIS or name == "Genesis":
            return "tech"
        if str(eid) in config.EMOJI_ENRICH or name == "Enrich":
            return "tech"
        if str(eid) in config.EMOJI_MODT or name == "ModTRSE":
            return "tech"

    if name in ["▶️", "▶"]:
        return "quickstart"
    if name in ["❌", "✖️", "✖"]:
        return "exit"
    if name in ["🛠️", "🛠", "🔧"]:
        return "tech"
    if name in ["⏳", "⌛"]:
        return "extend"
    if name in ["🆘"]:
        return "sos"
    if name in ["🔔", "🔕"]:
        return "bell_ping"
    if name in ["🏠", "📋", "❓", "❔", "ℹ️", "ℹ"]:
        return "home"

    return None


def build_detail_embed(key: str) -> discord.Embed:
    """Builds a focused, in-depth embed for a specific button or control."""
    data = BUTTON_HELP_DATA.get(key)
    if not data:
        return build_main_help_embed()

    embed = discord.Embed(
        title=data["title"],
        description=data["description"],
        color=data["color"],
    )
    embed.add_field(
        name="💡 Tactical Tips & Rules",
        value="\n".join(f"• {tip}" for tip in data["tips"]),
        inline=False,
    )
    embed.set_footer(text=f"Category: {data['category']} • React with 🏠 to return to Overview")
    return embed


def build_main_help_embed() -> discord.Embed:
    """Builds the comprehensive main queue interface guide embed."""
    embed = discord.Embed(
        title=f"🎮 {config.EMOJI_DRS} DRS & {config.EMOJI_RS} RS Queue Interface Guide",
        description=(
            "Welcome to the **DRS Bot Matchmaking Guide**!\n\n"
            "The bot connects pilots across multiple Discord servers for **Dark Red Star (DRS 7–12)** "
            "and **Red Star (RS 4–12)** missions.\n\n"
            "👇 **React with any emoji below** to learn how each button works, including tips and matchmaking rules:"
        ),
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="🔘 Queue Panel Controls",
        value=(
            f"• {config.EMOJI_DRS} **DRS 7–{config.EMOJI_12}**: Toggle entry into DRS queues (3-player matches)\n"
            f"• {config.EMOJI_RS} **RS 4–{config.EMOJI_12}**: Toggle entry into Regular RS queues (4-player matches)\n"
            f"• {config.EMOJI_SWITCH} **Mode**: Switch between DRS and RS queue boards\n"
            f"• {config.EMOJI_QUICKSTART} **QuickStart**: Launch early with 2 or 3 players if everyone agrees\n"
            f"• {config.EMOJI_EXIT} **Exit**: Instantly leave all active queues"
        ),
        inline=False,
    )

    embed.add_field(
        name="🛠️ Profile & Coordination",
        value=(
            f"• {config.EMOJI_TECH} **Tech**: Set your Genesis ({config.EMOJI_GENESIS}), Enrich ({config.EMOJI_ENRICH}), and ModT ({config.EMOJI_MODT}) levels\n"
            "• ⏳ **Extend**: Add +30 mins to your queue expiry timer\n"
            f"• {config.EMOJI_SOS} **SOS**: Request squad guidance or carry support\n"
            "• 🔔 **Bell Ping**: Alert all teammates inside the private match thread"
        ),
        inline=False,
    )

    embed.set_footer(text="Tip: React with any emoji below to view its guide! React with 🏠 to return here.")
    return embed


class HelpCog(commands.Cog):
    """Cog handling emoji reaction-based guide and explanations for DRS / RS queues."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Track message IDs that should respond to reaction navigation
        self._tracked_help_messages: set[int] = set()

    # Standalone slash command /queuehelp
    @app_commands.command(name="queuehelp", description="Interactive guide explaining how all queue buttons and features work")
    async def queuehelp_cmd(self, interaction: discord.Interaction):
        """Displays interactive guide with emoji dropdown ephemerally in interaction response."""
        embed = build_main_help_embed()
        view = EphemeralHelpView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # Prefix commands: .help, .queuehelp, .drshelp, .buttons, .guide
    @commands.command(name="help", aliases=["queuehelp", "drshelp", "buttons", "guide"])
    async def prefix_help_cmd(self, ctx: commands.Context):
        """Prefix-based interactive guide using emoji reactions."""
        embed = build_main_help_embed()
        msg = await ctx.send(embed=embed)
        self._tracked_help_messages.add(msg.id)

        # Automatically react with all navigation emojis
        for emoji in HELP_REACTIONS:
            try:
                await msg.add_reaction(emoji)
            except Exception as e:
                logger.debug(f"Failed to add reaction {emoji}: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Listens for user reactions on help messages, removes their reaction, and updates the embed."""
        if payload.user_id == self.bot.user.id:
            return

        if payload.message_id not in self._tracked_help_messages:
            return

        key = match_reaction_key(payload.emoji)
        if not key:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except Exception:
                return

        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return

        # Remove the user's reaction so it stays clean and can be clicked again
        if payload.guild_id:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id) if guild else None
            if not member and guild:
                try:
                    member = await guild.fetch_member(payload.user_id)
                except Exception:
                    member = None
        else:
            member = self.bot.get_user(payload.user_id)

        if member:
            try:
                await message.remove_reaction(payload.emoji, member)
            except Exception:
                pass

        # Update message embed based on reaction
        if key == "home":
            updated_embed = build_main_help_embed()
        else:
            updated_embed = build_detail_embed(key)

        try:
            await message.edit(embed=updated_embed)
        except Exception as e:
            logger.error(f"Failed to update help embed on reaction: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))



