import asyncio
import logging
import discord
from discord.ext import commands
from aiohttp import web
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
        super().__init__(
            command_prefix=commands.when_mentioned_or(*config.COMMAND_PREFIXES),
            intents=intents,
            help_command=None
        )
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
            "cogs.stats_cog",  # Player stats cog
            "cogs.help_cog",  # Interactive queue button help & guide cog
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
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="DRS & RS Queues | .help"
        )
        await self.change_presence(activity=activity)

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


async def start_web_server(bot: DRSBot):
    routes = web.RouteTableDef()

    @routes.get('/')
    async def index_handler(request):
        is_ready = bot.is_ready()
        bot_status = "Connected & Online" if is_ready else "Running (Waiting for Discord Token)"
        bot_user = str(bot.user) if bot.user else "Not logged in"
        status_class = "online" if is_ready else "pending"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>DRS Bot Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }}
        .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 32px; max-width: 500px; width: 100%; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }}
        h1 {{ margin-top: 0; color: #f43f5e; font-size: 1.75rem; display: flex; align-items: center; gap: 10px; }}
        .status {{ display: inline-block; padding: 6px 14px; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; margin-bottom: 20px; }}
        .status.online {{ background: #065f46; color: #34d399; }}
        .status.pending {{ background: #854d0e; color: #fde047; }}
        .info-group {{ margin-bottom: 16px; background: #0f172a; padding: 12px 16px; border-radius: 8px; border: 1px solid #334155; }}
        .label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
        .value {{ font-size: 1rem; font-weight: 500; margin-top: 4px; color: #f8fafc; }}
        .note {{ font-size: 0.875rem; color: #94a3b8; margin-top: 20px; line-height: 1.5; border-top: 1px solid #334155; padding-top: 16px; }}
        code {{ background: #334155; padding: 2px 6px; border-radius: 4px; font-family: monospace; color: #f1f5f9; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🔴 DRS Bot</h1>
        <div>
            <span class="status {status_class}">
                ● {bot_status}
            </span>
        </div>
        <div class="info-group">
            <div class="label">Bot User</div>
            <div class="value">{bot_user}</div>
        </div>
        <div class="info-group">
            <div class="label">Guilds Connected</div>
            <div class="value">{len(bot.guilds) if is_ready else 0}</div>
        </div>
        <div class="note">
            DRS Bot server is active on port {config.PORT}. To connect to Discord, set your <code>DISCORD_BOT_TOKEN</code> in the environment variables / settings menu.
        </div>
    </div>
</body>
</html>"""
        return web.Response(text=html, content_type='text/html')

    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', config.PORT)
    await site.start()
    logger.info(f"Web server started successfully on port {config.PORT}")


async def main():
    bot = DRSBot()
    await start_web_server(bot)
    
    token = config.BOT_TOKEN
    if token:
        try:
            logger.info("Connecting to Discord...")
            await bot.start(token)
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}")
            while True:
                await asyncio.sleep(3600)
    else:
        logger.warning("DISCORD_BOT_TOKEN environment variable not set. Web server active on port 3000.")
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())




