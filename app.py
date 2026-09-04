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
            "cogs.server_emoji_cog",  # Server icon to Application Emoji sync
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
    # Ensure database connection is initialized for web queries
    bot.db.connect()

    routes = web.RouteTableDef()

    @routes.get('/health')
    @routes.get('/api/health')
    async def health_handler(request):
        return web.json_response({
            "status": "healthy",
            "bot_connected": bot.is_ready(),
            "bot_user": str(bot.user) if bot.user else None,
            "guilds_count": len(bot.guilds) if bot.is_ready() else 0,
            "database": "connected" if bot.db.connection else "disconnected",
        })

    @routes.get('/api/status')
    async def status_handler(request):
        servers = bot.db.get_all_servers()
        queue = bot.db.get_full_queue()
        return web.json_response({
            "is_ready": bot.is_ready(),
            "bot_user": str(bot.user) if bot.user else None,
            "registered_servers": len(servers),
            "active_queue_entries": len(queue),
            "discord_token_configured": bool(config.BOT_TOKEN),
        })

    @routes.get('/')
    async def index_handler(request):
        is_ready = bot.is_ready()
        bot_status = "Connected & Online" if is_ready else "Running (Waiting for Discord Token)"
        bot_user = str(bot.user) if bot.user else "Not logged in"
        status_class = "online" if is_ready else "pending"
        
        try:
            registered_servers = bot.db.get_all_servers()
            server_count = len(bot.guilds) if is_ready else len(registered_servers)
        except Exception:
            server_count = 0

        try:
            queue_items = bot.db.get_full_queue()
            queue_count = len(queue_items)
        except Exception:
            queue_items = []
            queue_count = 0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>DRS Queue Bot Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #090d16;
            color: #f1f5f9;
            min-height: 100vh;
            margin: 0;
            padding: 32px 20px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 860px;
            width: 100%;
        }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            padding-bottom: 20px;
            border-bottom: 1px solid #1e293b;
        }}
        .title-group {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .title-group h1 {{
            margin: 0;
            font-size: 1.5rem;
            font-weight: 700;
            color: #f43f5e;
            letter-spacing: -0.02em;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 0.8125rem;
            font-weight: 600;
        }}
        .badge.online {{ background: #064e3b; color: #34d399; border: 1px solid #059669; }}
        .badge.pending {{ background: #713f12; color: #fde047; border: 1px solid #ca8a04; }}
        .pulse {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: currentColor;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 20px;
        }}
        .card-label {{
            font-size: 0.75rem;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .card-value {{
            font-size: 1.375rem;
            font-weight: 700;
            color: #f9fafb;
        }}
        .card-desc {{
            font-size: 0.8125rem;
            color: #6b7280;
            margin-top: 4px;
        }}
        .section-title {{
            font-size: 1rem;
            font-weight: 600;
            color: #e5e7eb;
            margin: 28px 0 14px 0;
        }}
        .info-panel {{
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .alert-box {{
            background: #181c2e;
            border: 1px solid #2d3748;
            border-radius: 8px;
            padding: 14px 18px;
            font-size: 0.875rem;
            color: #cbd5e1;
            line-height: 1.6;
        }}
        code {{
            background: #1e293b;
            color: #38bdf8;
            padding: 2px 7px;
            border-radius: 4px;
            font-family: ui-monospace, SFMono-Regular, monospace;
            font-size: 0.8125rem;
        }}
        .table-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #1f2937;
            font-size: 0.875rem;
        }}
        .table-row:last-child {{
            border-bottom: none;
        }}
        .table-label {{ color: #9ca3af; }}
        .table-val {{ font-weight: 500; color: #f3f4f6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-group">
                <h1>🔴 DRS Queue Bot</h1>
            </div>
            <div class="badge {status_class}">
                <span class="pulse"></span>
                <span>{bot_status}</span>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-label">Bot Identity</div>
                <div class="card-value">{bot_user}</div>
                <div class="card-desc">Discord Gateway Client</div>
            </div>
            <div class="card">
                <div class="card-label">Registered Servers</div>
                <div class="card-value">{server_count}</div>
                <div class="card-desc">Configured DRS Guilds</div>
            </div>
            <div class="card">
                <div class="card-label">Active Queues</div>
                <div class="card-value">{queue_count}</div>
                <div class="card-desc">Queued Pilots Across Levels</div>
            </div>
        </div>

        <div class="section-title">System & Database Status</div>
        <div class="info-panel">
            <div class="table-row">
                <span class="table-label">Database Storage</span>
                <span class="table-val">SQLite ({config.DB_PATH}) - WAL Mode Active</span>
            </div>
            <div class="table-row">
                <span class="table-label">Web Service Port</span>
                <span class="table-val">{config.PORT}</span>
            </div>
            <div class="table-row">
                <span class="table-label">Discord Slash Commands</span>
                <span class="table-val">/drs, /officer, /stats, /add_corporation, /feedback</span>
            </div>
            <div class="table-row">
                <span class="table-label">Supported Game Modes</span>
                <span class="table-val">DRS 7-12 & RS 4-12 Matchmaking</span>
            </div>
        </div>

        <div class="section-title">Discord Connectivity</div>
        <div class="alert-box">
            The DRS Bot server is up and listening on port <code>{config.PORT}</code>.
            To connect to Discord guilds, provide your <code>DISCORD_BOT_TOKEN</code> in the workspace Settings / Environment Variables menu.
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





