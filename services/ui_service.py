import random
import logging
from datetime import datetime, timezone

import discord
import config

logger = logging.getLogger("drs_bot.ui_service")

def parse_emoji(emoji_str: str):
    if isinstance(emoji_str, str) and emoji_str.startswith("<") and emoji_str.endswith(">"):
        return discord.PartialEmoji.from_str(emoji_str)
    return emoji_str

HELP_ICONS = [
    "<:penhelp:1531861262735245353>",
    "<:dinohelp:1531861260679774238>",
    "<:cutehelp:1531861255944536125>",
    "<:cathelp:1531861255214731264>",
]

LEVEL_EMOJI = {
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟",
    11: parse_emoji(config.EMOJI_11),
    12: parse_emoji(config.EMOJI_12),
}


def _format_last_run(last_match: dict | None) -> str:
    if not last_match:
        return "*None yet*"
    m_type = last_match.get("match_type", "DRS")
    level = last_match.get("drs_level", "")
    created_at_str = last_match.get("created_at")
    level_tag = f"**{m_type}{level}**"
    if not created_at_str:
        return level_tag
    try:
        dt = datetime.strptime(str(created_at_str), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        ts = int(dt.timestamp())
        return f"{level_tag} <t:{ts}:R>"
    except Exception:
        return level_tag


def build_queue_embeds(full_queue_data: list[dict], lang: str = "en", activity_stats: dict | None = None) -> list[discord.Embed]:
    from services.i18n import get as t

    GEN = config.EMOJI_GENESIS
    ENR = config.EMOJI_ENRICH
    RSE = config.EMOJI_MODT
    DRS_ICON = config.EMOJI_DRS
    RS_ICON = config.EMOJI_RS

    HINTS = [
        f"4️⃣–{config.EMOJI_12} - Join/Leave Queue",
        f"{config.EMOJI_SWITCH} - Switch Mode (DRS / RS)",
        f"{config.EMOJI_QUICKSTART} - Quick Start",
        f"{config.EMOJI_EXIT} - Exit All Queues",
        f"{config.EMOJI_TECH} - Set Tech",
        f"{config.EMOJI_SOS} - Need Assist On/Off",
    ]

    # Activity header banner
    activity_header = ""
    if activity_stats:
        total_24h = activity_stats.get("total_24h", 0)
        last_match = activity_stats.get("last_match")
        last_run_str = _format_last_run(last_match)
        activity_header = f"📊 `{total_24h} runs (24h)`  |  🚀 *Last run:* {last_run_str}\n\n"

    # 1. Dark Red Star Queue Embed
    drs_embed = discord.Embed(
        title=f"{DRS_ICON} Dark Red Star Queue",
        color=discord.Color.dark_red(),
        description=activity_header if activity_header else None
    )
    drs_by_level = {lvl: [] for lvl in config.VALID_DRS_LEVELS}
    for entry in full_queue_data:
        if entry.get("queue_type", "DRS") == "DRS":
            lvl = entry["drs_level"]
            if lvl in drs_by_level:
                drs_by_level[lvl].append(entry)

    has_drs = False
    for level in config.VALID_DRS_LEVELS:
        entries = drs_by_level[level]
        if not entries:
            continue
        has_drs = True
        rows = []
        for e in entries:
            remaining = _format_remaining(e["expires_at"])
            qs_marker = f" {config.EMOJI_QUICKSTART}" if e.get("quick_start") else ""
            help_marker = f" {random.choice(HELP_ICONS)}" if e.get("need_assist") else ""
            name = e["display_name"][:15]
            gen_lvl = e.get("genesis_level", "?") if e.get("genesis_level") is not None else "?"
            enr_lvl = e.get("enrich_level", "?") if e.get("enrich_level") is not None else "?"
            rse_lvl = e.get("modt_level", "?") if e.get("modt_level") is not None else "?"
            rows.append(f"`{name:<15}`{qs_marker:<2}{help_marker} {GEN} `{gen_lvl:<2}`  {ENR} `{enr_lvl:<2}`  {RSE} `{rse_lvl:<2}` — {remaining}")

        filled = min(len(entries), config.DRS_MATCH_SIZE)
        empty = config.DRS_MATCH_SIZE - filled
        progress_bar = f"[{'▰' * filled}{'▱' * empty}]"

        drs_embed.add_field(
            name=f"DRS{level}  {progress_bar}  ({len(entries)}/{config.DRS_MATCH_SIZE})",
            value="\n".join(rows),
            inline=False
        )

    if not has_drs:
        drs_embed.description = (activity_header if activity_header else "") + "*No pilots in Dark Red Star queue.*"

    # Add random Hint section
    hint_idx = random.randint(0, len(HINTS) - 1)
    hint_num = hint_idx + 1
    hint_text = HINTS[hint_idx]
    drs_embed.add_field(
        name="\u200b",
        value=f"-----\n> -# 💡 ┃ {hint_text}",
        inline=False
    )
    drs_embed.set_footer(text=t(lang, "queue_footer"))

    # 2. Red Star Queue Embed (only shown when there is a player in RS queue)
    rs_embed = discord.Embed(
        title=f"{RS_ICON} Red Star Queue",
        color=discord.Color.red(),
        description=activity_header if activity_header else None
    )
    rs_by_level = {lvl: [] for lvl in config.VALID_RS_LEVELS}
    for entry in full_queue_data:
        if entry.get("queue_type", "DRS") == "RS":
            lvl = entry["drs_level"]
            if lvl in rs_by_level:
                rs_by_level[lvl].append(entry)

    has_rs = False
    for level in config.VALID_RS_LEVELS:
        entries = rs_by_level[level]
        if not entries:
            continue
        has_rs = True
        rows = []
        for e in entries:
            remaining = _format_remaining(e["expires_at"])
            qs_marker = f" {config.EMOJI_QUICKSTART}" if e.get("quick_start") else ""
            help_marker = f" {random.choice(HELP_ICONS)}" if e.get("need_assist") else ""
            name = e["display_name"][:15]
            gen_lvl = e.get("genesis_level", "?") if e.get("genesis_level") is not None else "?"
            enr_lvl = e.get("enrich_level", "?") if e.get("enrich_level") is not None else "?"
            rse_lvl = e.get("modt_level", "?") if e.get("modt_level") is not None else "?"
            rows.append(f"`{name:<15}`{qs_marker:<2}{help_marker} {GEN} `{gen_lvl:<2}`  {ENR} `{enr_lvl:<2}`  {RSE} `{rse_lvl:<2}` — {remaining}")

        filled = min(len(entries), config.RS_MATCH_SIZE)
        empty = config.RS_MATCH_SIZE - filled
        progress_bar = f"[{'▰' * filled}{'▱' * empty}]"

        rs_embed.add_field(
            name=f"RS{level}  {progress_bar}  ({len(entries)}/{config.RS_MATCH_SIZE})",
            value="\n".join(rows),
            inline=False
        )

    embeds = [drs_embed]
    if has_rs:
        rs_embed.set_footer(text=t(lang, "queue_footer"))
        embeds.append(rs_embed)

    return embeds


def build_queue_embed(queue_data: list[dict], lang: str = "en", activity_stats: dict | None = None) -> discord.Embed:
    """Fallback single embed helper for legacy callers."""
    embeds = build_queue_embeds(queue_data, lang, activity_stats=activity_stats)
    return embeds[0]


def build_queue_view() -> discord.ui.View:
    """
    4x4 Control Grid View:
    Row 0: 4️⃣  5️⃣  6️⃣  ModeSwitch
    Row 1: 7️⃣  8️⃣  9️⃣  ▶️ QuickStart
    Row 2: 🔟  11  12  ❌ Exit
    Row 3: 🛠️ Tech  🆘 SOS
    """
    view = discord.ui.View(timeout=None)

    # Row 0: levels 4, 5, 6 + ModeSwitch
    for level in [4, 5, 6]:
        view.add_item(discord.ui.Button(
            emoji=LEVEL_EMOJI[level],
            style=discord.ButtonStyle.secondary,
            custom_id=f"drs_join_{level}",
            row=0
        ))
    view.add_item(discord.ui.Button(
        emoji=parse_emoji(config.EMOJI_SWITCH),
        style=discord.ButtonStyle.secondary,
        custom_id="drs_mode_switch",
        row=0
    ))

    # Row 1: levels 7, 8, 9 + QuickStart
    for level in [7, 8, 9]:
        view.add_item(discord.ui.Button(
            emoji=LEVEL_EMOJI[level],
            style=discord.ButtonStyle.secondary,
            custom_id=f"drs_join_{level}",
            row=1
        ))
    view.add_item(discord.ui.Button(
        emoji=parse_emoji(config.EMOJI_QUICKSTART),
        style=discord.ButtonStyle.secondary,
        custom_id="drs_quickstart",
        row=1
    ))

    # Row 2: levels 10, 11, 12 + Exit
    for level in [10, 11, 12]:
        view.add_item(discord.ui.Button(
            emoji=LEVEL_EMOJI[level],
            style=discord.ButtonStyle.secondary,
            custom_id=f"drs_join_{level}",
            row=2
        ))
    view.add_item(discord.ui.Button(
        emoji=parse_emoji(config.EMOJI_EXIT),
        style=discord.ButtonStyle.secondary,
        custom_id="drs_leave",
        row=2
    ))

    # Row 3: Combined Tech + Extend (+30m) + SOS + Help
    view.add_item(discord.ui.Button(
        emoji=parse_emoji(config.EMOJI_TECH),
        style=discord.ButtonStyle.secondary,
        custom_id="mod_set_combined",
        row=3
    ))
    view.add_item(discord.ui.Button(
        emoji="⏳",
        style=discord.ButtonStyle.secondary,
        custom_id="drs_extend",
        row=3
    ))
    view.add_item(discord.ui.Button(
        emoji=parse_emoji(config.EMOJI_SOS),
        style=discord.ButtonStyle.secondary,
        custom_id="drs_need_assist",
        row=3
    ))
    view.add_item(discord.ui.Button(
        emoji="❓",
        style=discord.ButtonStyle.secondary,
        custom_id="drs_help_btn",
        row=3
    ))

    return view


class EditProfileModal(discord.ui.Modal):
    def __init__(self, db, discord_id: int, profile_id: int, current_name: str, cur_gen: int | None, cur_enr: int | None, cur_rse: int | None):
        super().__init__(title=f"Edit Profile: {current_name[:15]}")
        self.db = db
        self.discord_id = discord_id
        self.profile_id = profile_id

        self.name_input = discord.ui.TextInput(
            label="Profile / Account Name (or IGN)",
            default=current_name,
            max_length=20,
            required=True
        )
        self.add_item(self.name_input)

        self.gen_input = discord.ui.TextInput(
            label="Genesis Level (6-15 or blank)",
            default=str(cur_gen) if cur_gen is not None else "",
            placeholder="6-15",
            max_length=2,
            required=False
        )
        self.add_item(self.gen_input)

        self.enr_input = discord.ui.TextInput(
            label="Enrich Level (6-15 or blank)",
            default=str(cur_enr) if cur_enr is not None else "",
            placeholder="6-15",
            max_length=2,
            required=False
        )
        self.add_item(self.enr_input)

        self.rse_input = discord.ui.TextInput(
            label="RSE / ModT Level (6-15 or blank)",
            default=str(cur_rse) if cur_rse is not None else "",
            placeholder="6-15",
            max_length=2,
            required=False
        )
        self.add_item(self.rse_input)

    async def on_submit(self, interaction: discord.Interaction):
        def parse_lvl(val_str):
            s = (val_str or "").strip()
            if not s:
                return None
            try:
                n = int(s)
                if 6 <= n <= 15:
                    return n
            except ValueError:
                pass
            return None

        name = self.name_input.value.strip() or "Profile"
        gen = parse_lvl(self.gen_input.value)
        enr = parse_lvl(self.enr_input.value)
        rse = parse_lvl(self.rse_input.value)

        self.db.save_user_profile(
            self.discord_id,
            profile_name=name,
            genesis_level=gen,
            enrich_level=enr,
            modt_level=rse,
            profile_id=self.profile_id
        )

        view = CombinedTechView(self.db, self.discord_id, selected_profile_id=self.profile_id)
        embed = view.build_embed(status_msg=f"✅ Saved tech and details for **{name}**!")
        await interaction.response.edit_message(embed=embed, view=view)


class CreateProfileModal(discord.ui.Modal):
    def __init__(self, db, discord_id: int):
        super().__init__(title="Create New Game Profile")
        self.db = db
        self.discord_id = discord_id

        self.name_input = discord.ui.TextInput(
            label="Profile / Account Name (or IGN)",
            placeholder="e.g. Alt 1, HydroAlt, CombatAlt",
            max_length=20,
            required=True
        )
        self.add_item(self.name_input)

        self.gen_input = discord.ui.TextInput(
            label="Genesis Level (6-15 or blank)",
            placeholder="e.g. 9",
            max_length=2,
            required=False
        )
        self.add_item(self.gen_input)

        self.enr_input = discord.ui.TextInput(
            label="Enrich Level (6-15 or blank)",
            placeholder="e.g. 8",
            max_length=2,
            required=False
        )
        self.add_item(self.enr_input)

        self.rse_input = discord.ui.TextInput(
            label="RSE / ModT Level (6-15 or blank)",
            placeholder="e.g. 7",
            max_length=2,
            required=False
        )
        self.add_item(self.rse_input)

    async def on_submit(self, interaction: discord.Interaction):
        def parse_lvl(val_str):
            s = (val_str or "").strip()
            if not s:
                return None
            try:
                n = int(s)
                if 6 <= n <= 15:
                    return n
            except ValueError:
                pass
            return None

        name = self.name_input.value.strip() or "Alt"
        gen = parse_lvl(self.gen_input.value)
        enr = parse_lvl(self.enr_input.value)
        rse = parse_lvl(self.rse_input.value)

        new_id = self.db.save_user_profile(
            self.discord_id,
            profile_name=name,
            genesis_level=gen,
            enrich_level=enr,
            modt_level=rse,
            set_active=False
        )

        view = CombinedTechView(self.db, self.discord_id, selected_profile_id=new_id)
        embed = view.build_embed(status_msg=f"🎉 Created profile **{name}**! Click **⭐ Set as Active** whenever you play with it.")
        await interaction.response.edit_message(embed=embed, view=view)


class CombinedTechView(discord.ui.View):
    """View allowing players to manage multiple game profiles/alts and configure tech levels."""

    def __init__(self, db, discord_id: int, selected_profile_id: int | None = None, display_name: str | None = None):
        super().__init__(timeout=240)
        self.db = db
        self.discord_id = discord_id
        self.display_name = display_name

        self.profiles = self.db.get_user_profiles(discord_id, display_name=display_name)
        active_p = self.db.get_active_profile(discord_id)

        # Determine currently selected profile
        self.selected_profile = None
        if selected_profile_id:
            self.selected_profile = next((p for p in self.profiles if p["id"] == selected_profile_id), None)
        if not self.selected_profile:
            self.selected_profile = active_p
        if not self.selected_profile:
            self.selected_profile = {
                "id": None,
                "discord_id": discord_id,
                "profile_name": "Main",
                "genesis_level": None,
                "enrich_level": None,
                "modt_level": None,
                "is_active": 1,
            }

        cur_gen = self.selected_profile.get("genesis_level")
        cur_enr = self.selected_profile.get("enrich_level")
        cur_rse = self.selected_profile.get("modt_level")

        # Row 0: Profile Selector Dropdown
        profile_options = []
        for p in self.profiles:
            is_active = bool(p.get("is_active"))
            is_selected = (p["id"] == self.selected_profile["id"])
            g_str = p["genesis_level"] if p["genesis_level"] is not None else "?"
            e_str = p["enrich_level"] if p["enrich_level"] is not None else "?"
            r_str = p["modt_level"] if p["modt_level"] is not None else "?"

            prefix = "⭐ " if is_active else ""
            desc = f"{'Active | ' if is_active else ''}Gen: {g_str} / Enr: {e_str} / RSE: {r_str}"
            profile_options.append(
                discord.SelectOption(
                    label=f"{prefix}{p['profile_name']}"[:100],
                    value=f"prof_{p['id']}",
                    description=desc[:100],
                    default=is_selected,
                    emoji="⭐" if is_active else "👤"
                )
            )

        # Option to create a new profile directly in dropdown
        profile_options.append(
            discord.SelectOption(
                label="➕ Create New Account / Profile",
                value="action_new_profile",
                description="Add an Alt account or secondary game profile",
                emoji="➕"
            )
        )

        self.profile_select = discord.ui.Select(
            placeholder="Switch or select account profile...",
            options=profile_options,
            row=0
        )
        self.profile_select.callback = self.on_profile_select
        self.add_item(self.profile_select)

        # Row 1: Genesis dropdown (6-15)
        gen_options = [
            discord.SelectOption(label=f"Genesis Level {i}", value=str(i), default=(cur_gen == i))
            for i in range(6, 16)
        ]
        self.genesis_select = discord.ui.Select(
            placeholder=f"Genesis (Current: {cur_gen or 'Not set'})",
            options=gen_options,
            row=1
        )
        self.genesis_select.callback = self.on_genesis_select
        self.add_item(self.genesis_select)

        # Row 2: Enrich dropdown (6-15)
        enr_options = [
            discord.SelectOption(label=f"Enrich Level {i}", value=str(i), default=(cur_enr == i))
            for i in range(6, 16)
        ]
        self.enrich_select = discord.ui.Select(
            placeholder=f"Enrich (Current: {cur_enr or 'Not set'})",
            options=enr_options,
            row=2
        )
        self.enrich_select.callback = self.on_enrich_select
        self.add_item(self.enrich_select)

        # Row 3: RSE dropdown (6-15)
        rse_options = [
            discord.SelectOption(label=f"RSE Level {i}", value=str(i), default=(cur_rse == i))
            for i in range(6, 16)
        ]
        self.rse_select = discord.ui.Select(
            placeholder=f"RSE / ModT (Current: {cur_rse or 'Not set'})",
            options=rse_options,
            row=3
        )
        self.rse_select.callback = self.on_rse_select
        self.add_item(self.rse_select)

        # Row 4: Action Buttons
        is_already_active = bool(self.selected_profile.get("is_active"))

        # Set Active Button
        self.set_active_btn = discord.ui.Button(
            label="Active Account" if is_already_active else "Set as Active",
            style=discord.ButtonStyle.success if is_already_active else discord.ButtonStyle.primary,
            emoji="⭐",
            disabled=is_already_active,
            row=4
        )
        self.set_active_btn.callback = self.on_set_active
        self.add_item(self.set_active_btn)

        # Edit/Rename Modal Button
        self.edit_btn = discord.ui.Button(
            label="Rename & Edit",
            style=discord.ButtonStyle.secondary,
            emoji="✏️",
            row=4
        )
        self.edit_btn.callback = self.on_edit_modal
        self.add_item(self.edit_btn)

        # New Profile Button
        self.new_btn = discord.ui.Button(
            label="New Profile",
            style=discord.ButtonStyle.secondary,
            emoji="➕",
            row=4
        )
        self.new_btn.callback = self.on_new_modal
        self.add_item(self.new_btn)

        # Delete Profile Button (disabled if only 1 profile)
        self.delete_btn = discord.ui.Button(
            label="Delete",
            style=discord.ButtonStyle.danger,
            emoji="🗑️",
            disabled=(len(self.profiles) <= 1),
            row=4
        )
        self.delete_btn.callback = self.on_delete
        self.add_item(self.delete_btn)

    def build_embed(self, status_msg: str | None = None) -> discord.Embed:
        GEN = config.EMOJI_GENESIS
        ENR = config.EMOJI_ENRICH
        RSE = config.EMOJI_MODT

        embed = discord.Embed(
            title="🛠️ Tech Modules & Account Profiles",
            color=discord.Color.dark_teal(),
        )

        if status_msg:
            embed.description = f"{status_msg}\n\n"
        else:
            embed.description = ""

        embed.description += (
            "Manage your main and alt accounts. When you join queues or match into a DRS / RS run, "
            "the bot automatically applies your **Active Profile**'s tech levels.\n"
        )

        # List all profiles
        profile_lines = []
        for p in self.profiles:
            active_tag = " `⭐ ACTIVE`" if p.get("is_active") else ""
            selected_tag = " 👈 *(editing)*" if (p["id"] == self.selected_profile["id"]) else ""
            g_val = p["genesis_level"] if p["genesis_level"] is not None else "?"
            e_val = p["enrich_level"] if p["enrich_level"] is not None else "?"
            r_val = p["modt_level"] if p["modt_level"] is not None else "?"
            profile_lines.append(
                f"• **{p['profile_name']}**{active_tag}{selected_tag}\n"
                f"  └ {GEN} Genesis: `{g_val}`  |  {ENR} Enrich: `{e_val}`  |  {RSE} RSE: `{r_val}`"
            )

        embed.add_field(
            name="📋 Your Account Profiles",
            value="\n".join(profile_lines) if profile_lines else "*No profiles found.*",
            inline=False
        )

        sel = self.selected_profile
        g = sel.get("genesis_level", "?") or "?"
        e = sel.get("enrich_level", "?") or "?"
        r = sel.get("modt_level", "?") or "?"
        is_act = "⭐ Active (Queues & Matches)" if sel.get("is_active") else "⚪ Inactive (Switch active below)"

        embed.add_field(
            name=f"⚙️ Selected: {sel['profile_name']}",
            value=(
                f"• **Status:** {is_act}\n"
                f"• **Tech:** {GEN} Genesis: **{g}**  |  {ENR} Enrich: **{e}**  |  {RSE} RSE: **{r}**\n\n"
                "👇 *Use the dropdowns below to quickly change levels, or click **Rename & Edit**.*"
            ),
            inline=False
        )

        embed.set_footer(text="Tip: Click 'Set as Active' to switch which account you are bringing to missions.")
        return embed

    async def on_profile_select(self, interaction: discord.Interaction):
        selected_val = self.profile_select.values[0]
        if selected_val == "action_new_profile":
            modal = CreateProfileModal(self.db, self.discord_id)
            await interaction.response.send_modal(modal)
            return

        if selected_val.startswith("prof_"):
            try:
                p_id = int(selected_val.split("_")[1])
                view = CombinedTechView(self.db, self.discord_id, selected_profile_id=p_id)
                embed = view.build_embed()
                await interaction.response.edit_message(embed=embed, view=view)
            except Exception as e:
                logger.error(f"Error selecting profile: {e}")
                await interaction.response.defer()

    async def on_genesis_select(self, interaction: discord.Interaction):
        gen_val = int(self.genesis_select.values[0])
        self.db.save_user_profile(
            self.discord_id,
            profile_name=self.selected_profile["profile_name"],
            genesis_level=gen_val,
            enrich_level=self.selected_profile.get("enrich_level"),
            modt_level=self.selected_profile.get("modt_level"),
            profile_id=self.selected_profile["id"]
        )
        view = CombinedTechView(self.db, self.discord_id, selected_profile_id=self.selected_profile["id"])
        embed = view.build_embed(status_msg=f"✅ Updated Genesis to **Level {gen_val}** for **{self.selected_profile['profile_name']}**!")
        await interaction.response.edit_message(embed=embed, view=view)

    async def on_enrich_select(self, interaction: discord.Interaction):
        enr_val = int(self.enrich_select.values[0])
        self.db.save_user_profile(
            self.discord_id,
            profile_name=self.selected_profile["profile_name"],
            genesis_level=self.selected_profile.get("genesis_level"),
            enrich_level=enr_val,
            modt_level=self.selected_profile.get("modt_level"),
            profile_id=self.selected_profile["id"]
        )
        view = CombinedTechView(self.db, self.discord_id, selected_profile_id=self.selected_profile["id"])
        embed = view.build_embed(status_msg=f"✅ Updated Enrich to **Level {enr_val}** for **{self.selected_profile['profile_name']}**!")
        await interaction.response.edit_message(embed=embed, view=view)

    async def on_rse_select(self, interaction: discord.Interaction):
        rse_val = int(self.rse_select.values[0])
        self.db.save_user_profile(
            self.discord_id,
            profile_name=self.selected_profile["profile_name"],
            genesis_level=self.selected_profile.get("genesis_level"),
            enrich_level=self.selected_profile.get("enrich_level"),
            modt_level=rse_val,
            profile_id=self.selected_profile["id"]
        )
        view = CombinedTechView(self.db, self.discord_id, selected_profile_id=self.selected_profile["id"])
        embed = view.build_embed(status_msg=f"✅ Updated RSE to **Level {rse_val}** for **{self.selected_profile['profile_name']}**!")
        await interaction.response.edit_message(embed=embed, view=view)

    async def on_set_active(self, interaction: discord.Interaction):
        self.db.set_active_profile(self.discord_id, self.selected_profile["id"])
        view = CombinedTechView(self.db, self.discord_id, selected_profile_id=self.selected_profile["id"])
        embed = view.build_embed(status_msg=f"⭐ **{self.selected_profile['profile_name']}** is now your active account for all queues and runs!")
        await interaction.response.edit_message(embed=embed, view=view)

    async def on_edit_modal(self, interaction: discord.Interaction):
        modal = EditProfileModal(
            self.db,
            self.discord_id,
            self.selected_profile["id"],
            self.selected_profile["profile_name"],
            self.selected_profile.get("genesis_level"),
            self.selected_profile.get("enrich_level"),
            self.selected_profile.get("modt_level"),
        )
        await interaction.response.send_modal(modal)

    async def on_new_modal(self, interaction: discord.Interaction):
        modal = CreateProfileModal(self.db, self.discord_id)
        await interaction.response.send_modal(modal)

    async def on_delete(self, interaction: discord.Interaction):
        if len(self.profiles) <= 1:
            await interaction.response.send_message("❌ You must keep at least one profile.", ephemeral=True)
            return

        deleted_name = self.selected_profile["profile_name"]
        self.db.delete_user_profile(self.discord_id, self.selected_profile["id"])

        view = CombinedTechView(self.db, self.discord_id)
        embed = view.build_embed(status_msg=f"🗑️ Deleted profile **{deleted_name}**.")
        await interaction.response.edit_message(embed=embed, view=view)


class QueueModeSettingsView(discord.ui.View):
    def __init__(self, db, discord_id: int, current_mode: str, display_name: str = None):
        super().__init__(timeout=120)
        self.db = db
        self.discord_id = discord_id
        self.current_mode = current_mode
        self.display_name = display_name

        if current_mode == "DRS":
            keep_btn = discord.ui.Button(
                label="Keep DRS (Active)",
                style=discord.ButtonStyle.success,
                emoji=parse_emoji(config.EMOJI_DRS),
                custom_id="drs_mode_keep"
            )
            keep_btn.callback = self.on_keep
            self.add_item(keep_btn)

            switch_btn = discord.ui.Button(
                label="Switch to Red Star (RS)",
                style=discord.ButtonStyle.danger,
                emoji=parse_emoji(config.EMOJI_RS),
                custom_id="drs_mode_switch_to_rs"
            )
            switch_btn.callback = self.on_switch_rs
            self.add_item(switch_btn)
        else:
            keep_btn = discord.ui.Button(
                label="Keep RS (Active)",
                style=discord.ButtonStyle.success,
                emoji=parse_emoji(config.EMOJI_RS),
                custom_id="rs_mode_keep"
            )
            keep_btn.callback = self.on_keep
            self.add_item(keep_btn)

            switch_btn = discord.ui.Button(
                label="Switch to Dark Red Star (DRS)",
                style=discord.ButtonStyle.danger,
                emoji=parse_emoji(config.EMOJI_DRS),
                custom_id="rs_mode_switch_to_drs"
            )
            switch_btn.callback = self.on_switch_drs
            self.add_item(switch_btn)

    async def on_keep(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except Exception:
            pass

    async def on_switch_rs(self, interaction: discord.Interaction):
        self.db.set_user_queue_mode(self.discord_id, "RS", self.display_name)
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except Exception:
            pass

    async def on_switch_drs(self, interaction: discord.Interaction):
        self.db.set_user_queue_mode(self.discord_id, "DRS", self.display_name)
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except Exception:
            pass


def _format_remaining(expires_at: datetime) -> str:
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = expires_at - now
    if delta.total_seconds() <= 0:
        return "0m"
    mins = max(1, round(delta.total_seconds() / 60))
    return f"{mins}m"







