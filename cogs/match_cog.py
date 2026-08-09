import logging
import discord
from discord.ext import commands

from services.match_service import MatchService

logger = logging.getLogger("match_cog")


class MatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.match_service = MatchService(bot.db)

    @commands.Cog.listener()
    async def on_drs_match_formed(self, match_id: int, drs_level: int, participants: list[dict], queue_type: str = "DRS"):
        logger.info(f"Match {match_id} formed — {queue_type}{drs_level} — players: {[p['display_name'] for p in participants]}")

        # Always fetch fresh participants from DB so mod levels are included
        full_participants = self.bot.db.get_match_participants(match_id)

        self.bot.dispatch("drs_create_threads", match_id, drs_level, full_participants, queue_type)


async def setup(bot):
    await bot.add_cog(MatchCog(bot))

