#!/usr/bin/env python3
"""
Standalone command-line tool to safely clean legacy (g_ and pyrex) emojis, sync registered server
icons to concise Bot Application Emojis, and update the server_emojis table.

Usage:
    python3 scripts/sync_server_emojis.py [--no-force] [--no-clean]
"""
import sys
import os
import asyncio
import logging

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from dotenv import load_dotenv
load_dotenv()

import config
from db.database import DatabaseOperations
from cogs.server_emoji_cog import sanitize_emoji_name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sync_emojis_cli")


async def run_sync(force_update: bool = True, clean_legacy: bool = True):
    token = config.BOT_TOKEN
    if not token:
        logger.error("DISCORD_BOT_TOKEN is not configured in environment or config.py!")
        sys.exit(1)

    db = DatabaseOperations()
    if not db.connect():
        logger.error("Failed to connect to the database.")
        sys.exit(1)

    intents = discord.Intents.default()
    intents.guilds = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger.info(f"Connected to Discord as {client.user} (ID: {client.user.id})")
        logger.info(f"Discovered {len(client.guilds)} connected guild(s).")

        try:
            # 1. Fetch current application emojis
            app_emojis = await client.fetch_application_emojis()
            logger.info(f"Bot currently has {len(app_emojis)} / 2,000 Application Emojis before cleanup.")

            # 2. Identify target guilds
            db_servers = db.get_all_servers()
            target_guild_ids = {s["guild_id"] for s in db_servers}
            for g in client.guilds:
                target_guild_ids.add(g.id)

            logger.info(f"Targeting {len(target_guild_ids)} registered guild(s)...")

            db_emojis = db.get_all_server_emojis()
            db_emoji_ids = {r["emoji_id"] for r in db_emojis if r.get("emoji_id")}

            # 3. Strictly targeted removal of ONLY legacy emojis: g_ or pyrex
            deleted_old_count = 0
            if clean_legacy:
                for emoji in list(app_emojis):
                    name_lower = emoji.name.lower()
                    # STRICT CRITERIA:
                    # 1. Starts with "g_" (created by earlier run)
                    # 2. Contains "pyrex"
                    # 3. ID in db_emoji_ids
                    #
                    # All other emojis are 100% preserved!
                    is_g_prefix = emoji.name.startswith("g_")
                    is_pyrex = "pyrex" in name_lower
                    is_tracked_hub = emoji.id in db_emoji_ids

                    if is_g_prefix or is_pyrex or is_tracked_hub:
                        try:
                            logger.info(f"[X] Safely removing legacy emoji '{emoji.name}' ({emoji.id})...")
                            await emoji.delete(reason="One-time cleanup of g_ / pyrex server emojis")
                            deleted_old_count += 1
                        except Exception as del_err:
                            logger.warning(f"Could not delete legacy emoji {emoji.name}: {del_err}")

                logger.info(f"Safely purged {deleted_old_count} legacy (g_ / pyrex) application emoji(s). All other emojis were preserved.")

            # 4. Refresh list of emojis after cleanup
            app_emojis = await client.fetch_application_emojis()
            existing_by_name = {e.name: e for e in app_emojis}
            existing_by_id = {e.id: e for e in app_emojis}

            created_count = 0
            updated_count = 0
            unchanged_count = 0
            no_icon_count = 0

            for guild_id in target_guild_ids:
                guild = client.get_guild(guild_id)
                if not guild:
                    try:
                        guild = await client.fetch_guild(guild_id)
                    except Exception:
                        guild = None

                guild_name = guild.name if guild else f"Server {guild_id}"
                member_count = getattr(guild, "member_count", None)

                corp_bonus = db.get_corp_bonus(guild_id)
                corp_name = corp_bonus.get("corp_name") if corp_bonus else guild_name

                if not guild or not guild.icon:
                    logger.warning(f"[-] Guild '{guild_name}' ({guild_id}) has no icon set.")
                    db.upsert_server_emoji(
                        guild_id=guild_id,
                        guild_name=guild_name,
                        corp_name=corp_name,
                        icon_url=None,
                        icon_hash=None,
                        emoji_id=None,
                        emoji_name=None,
                        emoji_tag=None,
                        member_count=member_count,
                        is_active=1 if guild else 0,
                    )
                    no_icon_count += 1
                    continue

                icon_url = str(guild.icon.url)
                icon_hash = guild.icon.key
                short_emoji_name = sanitize_emoji_name(corp_name or guild_name, guild_id)

                existing_emoji = existing_by_name.get(short_emoji_name)
                if not existing_emoji:
                    db_record = db.get_server_emoji(guild_id)
                    if db_record and db_record.get("emoji_id"):
                        existing_emoji = existing_by_id.get(db_record["emoji_id"])

                # Read icon scaled to 128px
                try:
                    icon_asset = guild.icon.with_size(128)
                    if not guild.icon.is_animated():
                        icon_asset = icon_asset.with_format("png")
                    image_bytes = await icon_asset.read()
                except Exception:
                    image_bytes = await guild.icon.read()

                final_emoji = None

                if existing_emoji:
                    if force_update:
                        logger.info(f"[~] Refreshing emoji '{short_emoji_name}' for '{guild_name}'...")
                        try:
                            await existing_emoji.delete(reason=f"CLI refresh for guild {guild_id}")
                        except Exception as del_err:
                            logger.warning(f"Could not delete old emoji: {del_err}")

                        final_emoji = await client.create_application_emoji(
                            name=short_emoji_name,
                            image=image_bytes
                        )
                        updated_count += 1
                    else:
                        logger.info(f"[=] Emoji '{short_emoji_name}' unchanged for '{guild_name}'.")
                        final_emoji = existing_emoji
                        unchanged_count += 1
                else:
                    logger.info(f"[+] Creating short emoji '{short_emoji_name}' for '{guild_name}'...")
                    final_emoji = await client.create_application_emoji(
                        name=short_emoji_name,
                        image=image_bytes
                    )
                    created_count += 1

                # Update database table
                db.upsert_server_emoji(
                    guild_id=guild_id,
                    guild_name=guild_name,
                    corp_name=corp_name,
                    icon_url=icon_url,
                    icon_hash=icon_hash,
                    emoji_id=final_emoji.id if final_emoji else None,
                    emoji_name=final_emoji.name if final_emoji else None,
                    emoji_tag=str(final_emoji) if final_emoji else None,
                    member_count=member_count,
                    is_active=1,
                )

            logger.info("========================================")
            logger.info("Synchronization Complete!")
            logger.info(f"• Total Guilds:    {len(target_guild_ids)}")
            logger.info(f"• Cleaned Legacy:  {deleted_old_count}")
            logger.info(f"• Created:         {created_count}")
            logger.info(f"• Updated:         {updated_count}")
            logger.info(f"• Unchanged:       {unchanged_count}")
            logger.info(f"• No Icon:         {no_icon_count}")
            logger.info("Database table 'server_emojis' updated with all mappings.")
            logger.info("========================================")

        except Exception as e:
            logger.error(f"Fatal error during sync: {e}", exc_info=True)
        finally:
            await client.close()
            db.close()

    try:
        await client.start(token)
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user.")
    except Exception as e:
        logger.error(f"Client failure: {e}")


if __name__ == "__main__":
    force = True
    clean = True
    if "--no-force" in sys.argv:
        force = False
    if "--no-clean" in sys.argv:
        clean = False
    asyncio.run(run_sync(force_update=force, clean_legacy=clean))

