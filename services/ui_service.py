import random
from datetime import datetime, timezone

import discord
import config

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


def build_queue_embeds(full_queue_data: list[dict], lang: str = "en") -> list[discord.Embed]:
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

    # 1. Dark Red Star Queue Embed
    drs_embed = discord.Embed(title=f"{DRS_ICON} Dark Red Star Queue", color=discord.Color.dark_red())
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

        drs_embed.add_field(
            name=f"DRS{level}  ({len(entries)}/{config.DRS_MATCH_SIZE})",
            value="\n".join(rows),
            inline=False
        )

    if not has_drs:
        drs_embed.description = "*No pilots in Dark Red Star queue.*"

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
    rs_embed = discord.Embed(title=f"{RS_ICON} Red Star Queue", color=discord.Color.red())
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

        rs_embed.add_field(
            name=f"RS{level}  ({len(entries)}/{config.RS_MATCH_SIZE})",
            value="\n".join(rows),
            inline=False
        )

    embeds = [drs_embed]
    if has_rs:
        rs_embed.set_footer(text=t(lang, "queue_footer"))
        embeds.append(rs_embed)

    return embeds


def build_queue_embed(queue_data: list[dict], lang: str = "en") -> discord.Embed:
    """Fallback single embed helper for legacy callers."""
    embeds = build_queue_embeds(queue_data, lang)
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

    # Row 3: Combined Tech + SOS
    view.add_item(discord.ui.Button(
        emoji=parse_emoji(config.EMOJI_TECH),
        style=discord.ButtonStyle.secondary,
        custom_id="mod_set_combined",
        row=3
    ))
    view.add_item(discord.ui.Button(
        emoji=parse_emoji(config.EMOJI_SOS),
        style=discord.ButtonStyle.secondary,
        custom_id="drs_need_assist",
        row=3
    ))

    return view


class CombinedTechView(discord.ui.View):
    def __init__(self, db, discord_id: int):
        super().__init__(timeout=180)
        self.db = db
        self.discord_id = discord_id
        user_mods = self.db.get_user_mod_levels(discord_id)

        cur_gen = user_mods.get("genesis_level") if user_mods.get("genesis_level") is not None else 6
        cur_enr = user_mods.get("enrich_level") if user_mods.get("enrich_level") is not None else 6
        cur_rse = user_mods.get("modt_level") if user_mods.get("modt_level") is not None else 6

        self.gen_val = cur_gen
        self.enr_val = cur_enr
        self.rse_val = cur_rse

        # Genesis dropdown (levels 6-15)
        gen_options = [
            discord.SelectOption(label=f"Genesis Level {i}", value=str(i), default=(cur_gen == i))
            for i in range(6, 16)
        ]
        self.genesis_select = discord.ui.Select(
            placeholder=f"Genesis (Current: {cur_gen})",
            options=gen_options,
            row=0
        )
        self.genesis_select.callback = self.on_genesis_select
        self.add_item(self.genesis_select)

        # Enrich dropdown (levels 6-15)
        enr_options = [
            discord.SelectOption(label=f"Enrich Level {i}", value=str(i), default=(cur_enr == i))
            for i in range(6, 16)
        ]
        self.enrich_select = discord.ui.Select(
            placeholder=f"Enrich (Current: {cur_enr})",
            options=enr_options,
            row=1
        )
        self.enrich_select.callback = self.on_enrich_select
        self.add_item(self.enrich_select)

        # RSE dropdown (levels 6-15)
        rse_options = [
            discord.SelectOption(label=f"RSE Level {i}", value=str(i), default=(cur_rse == i))
            for i in range(6, 16)
        ]
        self.rse_select = discord.ui.Select(
            placeholder=f"RSE (Current: {cur_rse})",
            options=rse_options,
            row=2
        )
        self.rse_select.callback = self.on_rse_select
        self.add_item(self.rse_select)

        # Save Button
        save_btn = discord.ui.Button(
            label="Save Tech Levels",
            style=discord.ButtonStyle.success,
            emoji="💾",
            row=3
        )
        save_btn.callback = self.on_save
        self.add_item(save_btn)

    async def on_genesis_select(self, interaction: discord.Interaction):
        self.gen_val = int(self.genesis_select.values[0])
        await interaction.response.defer()

    async def on_enrich_select(self, interaction: discord.Interaction):
        self.enr_val = int(self.enrich_select.values[0])
        await interaction.response.defer()

    async def on_rse_select(self, interaction: discord.Interaction):
        self.rse_val = int(self.rse_select.values[0])
        await interaction.response.defer()

    async def on_save(self, interaction: discord.Interaction):
        self.db.set_user_mod_level(self.discord_id, "genesis", self.gen_val)
        self.db.set_user_mod_level(self.discord_id, "enrich", self.enr_val)
        self.db.set_user_mod_level(self.discord_id, "modt", self.rse_val)

        GEN = config.EMOJI_GENESIS
        ENR = config.EMOJI_ENRICH
        RSE = config.EMOJI_MODT
        await interaction.response.edit_message(
            content=f"✅ **Tech levels saved!**\n{GEN} Genesis: **{self.gen_val}** | {ENR} Enrich: **{self.enr_val}** | {RSE} RSE: **{self.rse_val}**",
            view=None
        )


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




