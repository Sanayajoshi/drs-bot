import random
from datetime import datetime, timezone

import discord
import config

EMOJI_GENESIS = discord.PartialEmoji(name="Genesis", id=1519930122566635652)
EMOJI_ENRICH  = discord.PartialEmoji(name="Enrich",  id=1519930167005413466)
EMOJI_MODT    = discord.PartialEmoji(name="ModTRSE", id=1256962175398842399)
EMOJI_11      = discord.PartialEmoji(name="11",      id=1378449282688090184)
EMOJI_12      = discord.PartialEmoji(name="12",      id=1378449310831607828)

HELP_ICONS = [
    "<:penhelp:1531861262735245353>",
    "<:dinohelp:1531861260679774238>",
    "<:cutehelp:1531861255944536125>",
    "<:cathelp:1531861255214731264>",
]

# Unicode emoji for levels 7-10
LEVEL_EMOJI = {
    7:  "7️⃣",
    8:  "8️⃣",
    9:  "9️⃣",
    10: "🔟",
}


def build_queue_embed(queue_data: list[dict], lang: str = "en") -> discord.Embed:
    from services.i18n import get as t
    embed = discord.Embed(title=t(lang, "queue_title"), color=discord.Color.dark_red())

    by_level: dict[int, list[dict]] = {lvl: [] for lvl in config.DRS_LEVELS}
    for entry in queue_data:
        lvl = entry["drs_level"]
        if lvl in by_level:
            by_level[lvl].append(entry)

    has_any = False
    for level in config.DRS_LEVELS:
        entries = by_level[level]
        if not entries:
            continue
        has_any = True

        # Header row
        GEN = "<:Genesis:1519930122566635652>"
        ENR = "<:Enrich:1519930167005413466>"
        RSE = "<:ModTRSE:1256962175398842399>"
        header = f"`{'Name':<20}` {GEN} {ENR} {RSE}"
        rows   = [header]
        rows   = []
        for e in entries:
            remaining = _format_remaining(e["expires_at"])
            qs_marker = " ▶️" if e.get("quick_start") else ""
            help_marker = f" {random.choice(HELP_ICONS)}" if e.get("need_assist") else ""
            name      = e["display_name"][:15]
            gen_lvl   = e.get("genesis_level", "?") if e.get("genesis_level") is not None else "?"
            enr_lvl   = e.get("enrich_level",  "?") if e.get("enrich_level")  is not None else "?"
            rse_lvl   = e.get("modt_level",    "?") if e.get("modt_level")    is not None else "?"
            rows.append(f"`{name:<15}`{qs_marker:<2}{help_marker} {GEN} `{gen_lvl:<2}`  {ENR} `{enr_lvl:<2}`  {RSE} `{rse_lvl:<2}`  — {remaining}")

        embed.add_field(
            name=f"DRS{level}  ({len(entries)}/{config.MATCH_SIZE})",
            value="\n".join(rows),
            inline=False
        )

    if not has_any:
        embed.description = t(lang, "queue_empty")

    embed.add_field(name="\u200b", value=t(lang, "queue_legend"), inline=False)
    embed.set_footer(text=t(lang, "queue_footer"))
    return embed


def build_queue_view() -> discord.ui.View:
    """
    Row 0: 7️⃣  8️⃣  9️⃣  ▶️ QuickStart
    Row 1: 🔟  11  12  ⏳ Extend
    Row 2: GEN  ENR  RSE  ❌ Leave
    Row 3: 🆘 Need Assist
    """
    view = discord.ui.View(timeout=None)

    # Row 0: levels 7, 8, 9 + Quick Start
    for level in [7, 8, 9]:
        view.add_item(discord.ui.Button(
            label="",
            emoji=LEVEL_EMOJI[level],
            style=discord.ButtonStyle.secondary,
            custom_id=f"drs_join_{level}",
            row=0
        ))
    view.add_item(discord.ui.Button(
        label="",
        emoji="▶️",
        style=discord.ButtonStyle.secondary,
        custom_id="drs_quickstart",
        row=0
    ))

    # Row 1: levels 10, 11, 12 + Extend
    view.add_item(discord.ui.Button(
        label="",
        emoji=LEVEL_EMOJI[10],
        style=discord.ButtonStyle.secondary,
        custom_id="drs_join_10",
        row=1
    ))
    view.add_item(discord.ui.Button(
        label="",
        emoji=EMOJI_11,
        style=discord.ButtonStyle.secondary,
        custom_id="drs_join_11",
        row=1
    ))
    view.add_item(discord.ui.Button(
        label="",
        emoji=EMOJI_12,
        style=discord.ButtonStyle.secondary,
        custom_id="drs_join_12",
        row=1
    ))
    view.add_item(discord.ui.Button(
        label="",
        emoji="⏳",
        style=discord.ButtonStyle.secondary,
        custom_id="drs_extend",
        row=1
    ))

    # Row 2: GEN, ENR, RSE + Leave
    view.add_item(discord.ui.Button(
        label="",
        emoji=EMOJI_GENESIS,
        style=discord.ButtonStyle.secondary,
        custom_id="mod_set_genesis",
        row=2
    ))
    view.add_item(discord.ui.Button(
        label="",
        emoji=EMOJI_ENRICH,
        style=discord.ButtonStyle.secondary,
        custom_id="mod_set_enrich",
        row=2
    ))
    view.add_item(discord.ui.Button(
        label="",
        emoji=EMOJI_MODT,
        style=discord.ButtonStyle.secondary,
        custom_id="mod_set_modt",
        row=2
    ))
    view.add_item(discord.ui.Button(
        label="",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
        custom_id="drs_leave",
        row=2
    ))

    # Row 3: Need Assist (SOS)
    view.add_item(discord.ui.Button(
        label="",
        emoji="🆘",
        style=discord.ButtonStyle.secondary,
        custom_id="drs_need_assist",
        row=3
    ))

    return view


def _format_remaining(expires_at: datetime) -> str:
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = expires_at - now
    if delta.total_seconds() <= 0:
        return "0m"
    mins = max(1, round(delta.total_seconds() / 60))
    return f"{mins}m"

