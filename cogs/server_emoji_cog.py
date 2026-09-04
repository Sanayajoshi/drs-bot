import io
import logging
import re
import discord
from discord import app_commands
from discord.ext import commands

import config

logger = logging.getLogger("drs_bot.server_emoji_cog")


def sanitize_emoji_name(name: str, guild_id: int) -> str:
    """
    Generate a concise, clean Discord-compliant application emoji name.
    Target length: 7-12 characters (e.g., c_popi_428, c_rest_789, c_nexus_321).
    Format: c_{short_slug}_{last3digits}
    """
    words = re.findall(r"[a-zA-Z0-9]+", name.strip())
    if len(words) >= 2:
        # Multi-word: take first 2 letters of first two words, or initials
        if len(words[0]) >= 2 and len(words[1]) >= 2:
            base = (words[0][:2] + words[1][:2]).lower()
        else:
            base = "".join(w[0].lower() for w in words[:4])
    elif len(words) == 1:
        base = words[0][:5].lower()
    else:
        base = "hub"

    base = re.sub(r"[^a-zA-Z0-9]", "", base) or "hub"
    suffix = str(guild_id)[-3:]
    return f"c_{base}_{suffix}"[:16]


def add_chunked_fields(embed: discord.Embed, title: str, lines: list[str], max_len: int = 900):
    """Safely adds fields to a Discord embed without ever exceeding the 1024-character limit."""
    if not lines:
        return

    current_chunk = []
    current_len = 0
    part = 1

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > max_len and current_chunk:
            field_name = title if part == 1 else f"{title} (Part {part})"
            embed.add_field(name=field_name[:256], value="\n".join(current_chunk)[:1024], inline=False)
            current_chunk = [line]
            current_len = line_len
            part += 1
            if len(embed.fields) >= 24:
                break
        else:
            current_chunk.append(line)
            current_len += line_len

    if current_chunk and len(embed.fields) < 25:
        field_name = title if part == 1 else f"{title} (Part {part})"
        embed.add_field(name=field_name[:256], value="\n".join(current_chunk)[:1024], inline=False)


class ServerEmojiCog(commands.Cog, name="ServerEmojis"):
    """Manages syncing registered Discord server icons into Bot Application Emojis."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_super_admin(self, user_id: int) -> bool:
        allowed = getattr(config, "SUPER_ADMIN_IDS", [508209182374363137, 702623662531936356, 670486428743892993])
        return user_id in allowed

    async def _sync_emojis_internal(self, force_update: bool = True, clean_legacy: bool = True) -> dict:
        """
        1. Safely removes ONLY legacy emojis (prefix 'g_' or containing 'pyrex') or existing hub records.
        2. Leaves all other user-created bot application emojis completely untouched.
        3. Downloads icons for registered guilds.
        4. Uploads concise application emojis (e.g. c_popi_428).
        5. Updates the server_emojis database table with guild-to-emoji mapping.
        """
        results = {
            "deleted_old_count": 0,
            "deleted_names": [],
            "created": [],
            "updated": [],
            "unchanged": [],
            "no_icon": [],
            "errors": [],
            "total": 0,
            "total_app_emojis": 0,
        }

        # ------------------------------------------------------------------
        # Step 1: Query database for currently known servers & tracked emoji IDs
        # ------------------------------------------------------------------
        db_servers = self.bot.db.get_all_servers()
        target_guild_ids = {s["guild_id"] for s in db_servers}
        for g in self.bot.guilds:
            target_guild_ids.add(g.id)

        results["total"] = len(target_guild_ids)

        db_emojis = self.bot.db.get_all_server_emojis()
        db_emoji_ids = {r["emoji_id"] for r in db_emojis if r.get("emoji_id")}

        # ------------------------------------------------------------------
        # Step 2: Fetch current application emojis
        # ------------------------------------------------------------------
        try:
            app_emojis = await self.bot.fetch_application_emojis()
        except Exception as e:
            logger.error(f"Failed to fetch application emojis: {e}", exc_info=True)
            raise RuntimeError(f"Could not retrieve application emojis from Discord API: {e}")

        logger.info(f"Bot currently has {len(app_emojis)} application emojis before cleanup.")

        # ------------------------------------------------------------------
        # Step 3: Strictly targeted removal of ONLY g_ and pyrex emojis
        # ------------------------------------------------------------------
        deleted_count = 0
        deleted_names = []

        if clean_legacy:
            for emoji in list(app_emojis):
                name_lower = emoji.name.lower()
                # STRICT CRITERIA:
                # 1. Names starting with "g_" (created by our earlier script run)
                # 2. Names containing "pyrex" (legacy emojis specified by user)
                # 3. Emoji ID previously recorded in server_emojis database table
                #
                # ANY OTHER EMOJI IS 100% PRESERVED AND NEVER TOUCHED!
                is_g_prefix = emoji.name.startswith("g_")
                is_pyrex = "pyrex" in name_lower
                is_tracked_hub = emoji.id in db_emoji_ids

                if is_g_prefix or is_pyrex or is_tracked_hub:
                    try:
                        logger.info(f"Safely removing legacy application emoji: '{emoji.name}' (ID: {emoji.id})")
                        await emoji.delete(reason="One-time cleanup of g_ / pyrex server emojis")
                        deleted_count += 1
                        deleted_names.append(emoji.name)
                    except Exception as del_err:
                        logger.warning(f"Could not delete legacy emoji {emoji.name}: {del_err}")

        results["deleted_old_count"] = deleted_count
        results["deleted_names"] = deleted_names
        logger.info(f"Safely purged {deleted_count} legacy (g_ / pyrex) application emoji(s). All other emojis were preserved.")

        # ------------------------------------------------------------------
        # Step 4: Refresh application emoji cache
        # ------------------------------------------------------------------
        try:
            app_emojis = await self.bot.fetch_application_emojis()
            existing_by_name = {e.name: e for e in app_emojis}
            existing_by_id = {e.id: e for e in app_emojis}
        except Exception as e:
            logger.warning(f"Error re-fetching application emojis: {e}")
            existing_by_name = {}
            existing_by_id = {}

        # ------------------------------------------------------------------
        # Step 5: Sync registered guild icons as concise application emojis
        # ------------------------------------------------------------------
        logger.info(f"Starting server emoji sync for {len(target_guild_ids)} registered guild(s)...")

        for guild_id in target_guild_ids:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                try:
                    guild = await self.bot.fetch_guild(guild_id)
                except Exception:
                    guild = None

            guild_name = guild.name if guild else f"Server {guild_id}"
            member_count = getattr(guild, "member_count", None)

            # Retrieve associated corp name if known
            corp_bonus = self.bot.db.get_corp_bonus(guild_id)
            corp_name = corp_bonus.get("corp_name") if corp_bonus else guild_name

            # Check if guild has an icon
            if not guild or not guild.icon:
                logger.warning(f"Guild {guild_name} ({guild_id}) has no icon.")
                self.bot.db.upsert_server_emoji(
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
                results["no_icon"].append({"name": guild_name, "id": guild_id, "corp": corp_name})
                continue

            icon_url = str(guild.icon.url)
            icon_hash = guild.icon.key
            short_emoji_name = sanitize_emoji_name(corp_name or guild_name, guild_id)

            # Check if matching emoji already exists for this guild
            existing_emoji = existing_by_name.get(short_emoji_name)
            if not existing_emoji:
                db_record = self.bot.db.get_server_emoji(guild_id)
                if db_record and db_record.get("emoji_id"):
                    existing_emoji = existing_by_id.get(db_record["emoji_id"])

            try:
                # Read icon bytes scaled to 128px
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
                        logger.info(f"Refreshing application emoji {short_emoji_name} for guild {guild_name}...")
                        try:
                            await existing_emoji.delete(reason=f"Refreshing icon for guild {guild_id}")
                        except Exception as del_err:
                            logger.warning(f"Failed to delete existing emoji {existing_emoji.id}: {del_err}")

                        final_emoji = await self.bot.create_application_emoji(
                            name=short_emoji_name,
                            image=image_bytes
                        )
                        results["updated"].append({
                            "name": guild_name,
                            "corp": corp_name,
                            "id": guild_id,
                            "emoji_tag": str(final_emoji),
                            "emoji_name": final_emoji.name,
                        })
                    else:
                        final_emoji = existing_emoji
                        results["unchanged"].append({
                            "name": guild_name,
                            "corp": corp_name,
                            "id": guild_id,
                            "emoji_tag": str(final_emoji),
                            "emoji_name": final_emoji.name,
                        })
                else:
                    logger.info(f"Creating short application emoji {short_emoji_name} for guild {guild_name}...")
                    final_emoji = await self.bot.create_application_emoji(
                        name=short_emoji_name,
                        image=image_bytes
                    )
                    results["created"].append({
                        "name": guild_name,
                        "corp": corp_name,
                        "id": guild_id,
                        "emoji_tag": str(final_emoji),
                        "emoji_name": final_emoji.name,
                    })

                # Persist updated mapping into server_emojis table
                self.bot.db.upsert_server_emoji(
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

            except Exception as e:
                logger.error(f"Error processing emoji for guild {guild_name} ({guild_id}): {e}", exc_info=True)
                results["errors"].append({"name": guild_name, "id": guild_id, "error": str(e)})

        # Final count
        try:
            current_app_emojis = await self.bot.fetch_application_emojis()
            results["total_app_emojis"] = len(current_app_emojis)
        except Exception:
            results["total_app_emojis"] = len(results["created"]) + len(results["updated"]) + len(results["unchanged"])

        return results

    def _build_sync_embed(self, results: dict, force_update: bool, clean_legacy: bool) -> discord.Embed:
        """Construct a clean, well-formatted embed guaranteed to respect Discord limits."""
        created_count = len(results["created"])
        updated_count = len(results["updated"])
        unchanged_count = len(results["unchanged"])
        no_icon_count = len(results["no_icon"])
        error_count = len(results["errors"])
        deleted_count = results.get("deleted_old_count", 0)
        total_synced = created_count + updated_count + unchanged_count

        embed = discord.Embed(
            title="🌐 Bot Application Emoji Synchronization",
            description=(
                f"Processed **{results['total']}** registered Discord server(s).\n"
                f"**Legacy Cleanup:** {'Enabled (Purged g_ & pyrex emojis)' if clean_legacy else 'Disabled (Preserved all)'}\n"
                f"**Application Emojis In Use:** `{results['total_app_emojis']} / 2,000`"
            ),
            color=0x3498DB if error_count == 0 else 0xE67E22,
        )

        # Overview Metrics
        embed.add_field(
            name="📊 Sync Status",
            value=(
                f"✨ **Created:** `{created_count}`\n"
                f"🔄 **Updated:** `{updated_count}`\n"
                f"🗑️ **Legacy Cleaned:** `{deleted_count}`\n"
                f"⏸️ **Unchanged:** `{unchanged_count}`\n"
                f"⚠️ **No Icon:** `{no_icon_count}`\n"
                f"❌ **Errors:** `{error_count}`"
            ),
            inline=True
        )

        # Capacity
        slots_remaining = max(0, 2000 - results["total_app_emojis"])
        embed.add_field(
            name="📦 Application Pool",
            value=(
                f"• Active Emojis: **{results['total_app_emojis']}**\n"
                f"• Slots Available: **{slots_remaining:,}**\n"
                f"• Success Rate: **{round((total_synced / max(1, results['total'])) * 100, 1)}%**"
            ),
            inline=True
        )

        # Itemized listings of created / updated emojis with safe chunking
        all_active = results["created"] + results["updated"] + results["unchanged"]
        if all_active:
            lines = []
            for item in all_active:
                tag = item["emoji_tag"]
                corp = f" (*{item['corp']}*)" if item["corp"] != item["name"] else ""
                lines.append(f"{tag} **{item['name']}**{corp} — `{item['emoji_name']}`")
            add_chunked_fields(embed, "🏛️ Registered Hub Emojis", lines, max_len=850)

        if results["no_icon"]:
            no_icon_lines = [f"• **{item['name']}** (`{item['id']}`)" for item in results["no_icon"][:10]]
            add_chunked_fields(embed, "⚠️ Servers Without Icon", no_icon_lines, max_len=850)

        if results["errors"]:
            err_lines = [f"• **{item['name']}**: {item['error'][:60]}" for item in results["errors"][:5]]
            add_chunked_fields(embed, "❌ Errors Encountered", err_lines, max_len=850)

        embed.set_footer(text="Table 'server_emojis' updated. Non-hub emojis remain 100% preserved.")
        return embed

    # ------------------------------------------------------------------ Slash Command
    @app_commands.command(
        name="sync_server_emojis",
        description="[Super Admin] Clean g_/pyrex icons, upload short Application Emojis & update table."
    )
    @app_commands.describe(
        clean_legacy="One-time purge of old g_ and pyrex emojis only (defaults to True)",
        force_update="Whether to re-upload and refresh hub icons (defaults to True)"
    )
    async def sync_server_emojis_slash(
        self,
        interaction: discord.Interaction,
        clean_legacy: bool = True,
        force_update: bool = True
    ):
        if not self._is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                "❌ **Access Restricted**: Only Super Admins can execute server emoji synchronization.",
                ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=False)

        try:
            results = await self._sync_emojis_internal(force_update=force_update, clean_legacy=clean_legacy)
            embed = self._build_sync_embed(results, force_update=force_update, clean_legacy=clean_legacy)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to sync server emojis: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ **Sync Failed**: An error occurred while syncing application emojis: `{e}`"
            )

    # ------------------------------------------------------------------ Prefix Command
    @commands.command(name="syncicons", aliases=["syncemojis", "synchubicons"])
    async def sync_server_emojis_prefix(self, ctx: commands.Context, *args):
        """[Super Admin] Upload all registered server icons as Bot Application Emojis."""
        if not self._is_super_admin(ctx.author.id):
            await ctx.send("❌ **Access Restricted**: Only Super Admins can run this command.")
            return

        force_update = True
        clean_legacy = True
        if "noclean" in args:
            clean_legacy = False
        if "noforce" in args or "incremental" in args:
            force_update = False

        status_msg = await ctx.send("⏳ Safely cleaning legacy g_/pyrex icons, downloading server icons, and registering Application Emojis...")

        try:
            results = await self._sync_emojis_internal(force_update=force_update, clean_legacy=clean_legacy)
            embed = self._build_sync_embed(results, force_update=force_update, clean_legacy=clean_legacy)
            await status_msg.edit(content=None, embed=embed)
        except Exception as e:
            logger.error(f"Failed to sync server emojis via prefix command: {e}", exc_info=True)
            await status_msg.edit(content=f"❌ **Sync Failed**: `{e}`")

    # ------------------------------------------------------------------ View/List Command
    @app_commands.command(
        name="list_server_emojis",
        description="[Super Admin] View all server icons mapped in the server_emojis table."
    )
    async def list_server_emojis_slash(self, interaction: discord.Interaction):
        if not self._is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                "❌ **Access Restricted**: Only Super Admins can view this report.",
                ephemeral=True
            )
            return

        rows = self.bot.db.get_all_server_emojis()
        if not rows:
            await interaction.response.send_message(
                "ℹ️ No server emojis recorded in the database yet. Run `/sync_server_emojis` to initialize them.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📋 Synced Server Application Emojis",
            description=f"Showing **{len(rows)}** server(s) mapped in `server_emojis` database table:",
            color=0x2ECC71
        )

        lines = []
        for r in rows:
            tag = r.get("emoji_tag") or "*(No Icon)*"
            corp = f" · Corp: **{r['corp_name']}**" if r.get("corp_name") else ""
            lines.append(f"{tag} **{r['guild_name']}**{corp} (`{r['guild_id']}`) — `{r.get('emoji_name') or 'N/A'}`")

        add_chunked_fields(embed, "🏛️ Mapped Servers", lines, max_len=850)
        embed.set_footer(text="Run /sync_server_emojis to refresh images & mappings.")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerEmojiCog(bot))

