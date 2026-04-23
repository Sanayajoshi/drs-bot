import logging
import aiohttp

import discord

logger = logging.getLogger("thread_service")

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
LANG_CODES   = {"en": "en-US", "ja": "ja-JP"}

_INTROS = {
    "en": "**DRS{level} match formed!** Good luck everyone.",
    "ja": "**DRS{level}のマッチが成立しました！** 皆さん、頑張ってください。",
}


class ThreadService:
    def __init__(self, db):
        self.db = db

    def build_match_embed(
        self,
        match_id: int,
        drs_level: int,
        participants: list[dict],
        guild_participant_map: dict[int, str],  # discord_id → guild_name
    ) -> discord.Embed:
        """
        Build the rich match intro embed.
        participants: list of {discord_id, display_name, genesis_level, enrich_level, modt_level}
        guild_participant_map: {discord_id: guild_name} for the server this embed is posted in
        """
        embed = discord.Embed(
            title=f"⭐ Dark Red Star {drs_level} — Match #{match_id}",
            color=discord.Color.dark_red()
        )

        # --- Players section ---
        player_lines = []
        for p in participants:
            guild_name = guild_participant_map.get(p["discord_id"], "Unknown Server")
            player_lines.append(f"**{p['display_name']}** · {guild_name}")
        embed.add_field(name="👥 Players", value="\n".join(player_lines), inline=False)

        # --- RSE section — all players ---
        rse_lines = []
        for p in participants:
            lvl = p["modt_level"]
            rse_lines.append(f"{p['display_name']} — {lvl if lvl else '?'}")
        embed.add_field(name="🔴 RSE", value="\n".join(rse_lines), inline=False)

        # --- Genesis — highest only ---
        gen_players = [p for p in participants if p["genesis_level"] is not None]
        if gen_players:
            best = max(gen_players, key=lambda p: p["genesis_level"])
            embed.add_field(
                name="🟢 Genesis",
                value=f"{best['display_name']} — {best['genesis_level']}",
                inline=False
            )

        # --- Enrich — highest only ---
        enr_players = [p for p in participants if p["enrich_level"] is not None]
        if enr_players:
            best = max(enr_players, key=lambda p: p["enrich_level"])
            embed.add_field(
                name="🔵 Enrich",
                value=f"{best['display_name']} — {best['enrich_level']}",
                inline=False
            )

        # --- Warning if any player is missing gen/enr ---
        missing = [
            p for p in participants
            if p["genesis_level"] is None or p["enrich_level"] is None
        ]
        if missing:
            missing_names = ", ".join(p["display_name"] for p in missing)
            embed.add_field(
                name="⚠️ Tech levels incomplete",
                value=(
                    f"**{missing_names}** haven't set their GEN and/or ENR levels yet.\n"
                    "Since not everyone's tech is filled in, make sure to sort out "
                    "who's running Genesis and Enrich before heading in!"
                ),
                inline=False
            )

        return embed

    def build_bell_view(self, match_id: int) -> discord.ui.View:
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="🔔 Ping Players",
            style=discord.ButtonStyle.secondary,
            custom_id=f"bell_ping_{match_id}",
        ))
        return view

    def build_intro_message(self, drs_level: int, participants: list[dict], lang: str) -> str:
        """Simple text intro — used as fallback."""
        template = _INTROS.get(lang, _INTROS["en"])
        names    = ", ".join(p["display_name"] for p in participants)
        return template.format(level=drs_level) + f"\n**Players:** {names}"

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if source_lang == target_lang:
            return text
        src = LANG_CODES.get(source_lang, source_lang)
        tgt = LANG_CODES.get(target_lang, target_lang)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(MYMEMORY_URL, params={"q": text, "langpair": f"{src}|{tgt}"}) as resp:
                    if resp.status != 200:
                        return text
                    data = await resp.json()
                    if data.get("responseStatus") != 200:
                        return text
                    return data["responseData"]["translatedText"]
        except Exception as e:
            logger.error(f"Translation failed: {e}", exc_info=True)
            return text
