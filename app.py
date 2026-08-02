import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()  # loads .env file

import config
from db.database import DatabaseOperations
from services.bonus_service import BonusService

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
        self.bonus_service = None  # Will be initialized in setup_hook

    async def setup_hook(self):
        # Connect to database
        if not self.db.connect():
            logger.error("Failed to connect to database — aborting.")
            await self.close()
            return

        logger.info("Database connected.")

        # Load all cogs
        cogs = [
            "cogs.setup_cog",
            "cogs.queue_cog",
            "cogs.match_cog",
            "cogs.thread_cog",
            "cogs.feedback_cog",
            "cogs.officer_cog",
            "cogs.bonus_cog",  # New bonus cog
            "cogs.engagement_cog",  # Engagement & Facts cog
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}", exc_info=True)

        # Initialize BonusService
        self.bonus_service = BonusService(self.db)
        await self.bonus_service.initialize()
        logger.info("BonusService initialized.")

        # Start background update task for bonuses
        async def hourly_bonus_update():
            await self.wait_until_ready()
            while not self.is_closed():
                try:
                    await asyncio.sleep(3600)  # Wait 1 hour
                    logger.info("Running hourly bonus update...")
                    updated = await self.bonus_service.update_all_bonuses()
                    if updated > 0:
                        logger.info(f"Updated {updated} corporation bonuses")
                except Exception as e:
                    logger.error(f"Hourly bonus update failed: {e}")

        self.loop.create_task(hourly_bonus_update())
        logger.info("Started hourly bonus update task.")

        # Sync slash commands
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
        # Clean up bonus service
        if self.bonus_service:
            await self.bonus_service.close()
        # Close database connection
        self.db.close()
        await super().close()


if __name__ == "__main__":
    if not config.BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set.")
    bot = DRSBot()
    bot.run(config.BOT_TOKEN)

