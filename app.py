import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()  # loads .env file

import config
from db.database import DatabaseOperations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("drs_bot")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class DRSBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.db = DatabaseOperations()

    async def setup_hook(self):
        if not self.db.connect():
            logger.error("Failed to connect to database — aborting.")
            await self.close()
            return

        logger.info("Database connected.")

        cogs = [
            "cogs.setup_cog",
            "cogs.queue_cog",
            "cogs.match_cog",
            "cogs.thread_cog",
            "cogs.feedback_cog",
            "cogs.officer_cog",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}", exc_info=True)

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s).")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (id: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s).")

    async def on_guild_join(self, guild: discord.Guild):
        self.db.upsert_server(guild.id)
        logger.info(f"Joined new guild: {guild.name} ({guild.id})")

    async def close(self):
        self.db.close()
        await super().close()


if __name__ == "__main__":
    if not config.BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set.")
    bot = DRSBot()
    bot.run(config.BOT_TOKEN)
