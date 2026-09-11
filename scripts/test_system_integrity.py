import asyncio
import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

# Ensure workspace is on sys.path
sys.path.insert(0, os.path.abspath("."))

import config
import db.database as db_mod
import services.i18n as i18n
import services.ui_service as ui_service
from services.queue_service import QueueService
from services.bonus_service import BonusService
from services.investigation_service import InvestigationService
from services.facts_service import FactsService
from cogs.help_cog import build_main_help_embed, EphemeralHelpView
from cogs.feedback_cog import build_feedback_view, build_resolve_view
import discord
from discord.ext import commands

print("=== STARTING DRS BOT INTEGRITY SUITE ===")

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        self.db = db_mod.DatabaseOperations(":memory:")
        self.assertTrue(self.db.connect())

    def tearDown(self):
        self.db.close()

    def test_users_and_servers(self):
        # 1. Upsert user
        self.db.upsert_user(1001, "PlayerOne")
        user = self.db.get_user(1001)
        self.assertIsNotNone(user)
        self.assertEqual(user["display_name"], "PlayerOne")

        # 2. Queue mode toggle
        self.assertEqual(self.db.get_user_queue_mode(1001), "DRS")
        self.assertEqual(self.db.toggle_user_queue_mode(1001), "RS")
        self.assertEqual(self.db.get_user_queue_mode(1001), "RS")
        self.assertEqual(self.db.toggle_user_queue_mode(1001), "DRS")

        # 3. Server configuration
        self.db.upsert_server(
            9999,
            queue_channel_id=111,
            notification_channel_id=222,
            officer_channel_id=333,
            manager_role_id=444,
            language="de"
        )
        srv = self.db.get_server(9999)
        self.assertIsNotNone(srv)
        self.assertEqual(srv["queue_channel_id"], 111)
        self.assertEqual(srv["language"], "de")

        # 4. Update language to Japanese
        self.db.upsert_server(9999, language="ja")
        srv = self.db.get_server(9999)
        self.assertEqual(srv["language"], "ja")

    def test_queue_lifecycle(self):
        # Join players into DRS9
        expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        self.db.upsert_user(101, "Alice")
        self.db.upsert_user(102, "Bob")
        self.db.upsert_user(103, "Charlie")

        self.db.join_queue(101, 9, expires, 9999, queue_type="DRS")
        self.db.join_queue(102, 9, expires, 9999, queue_type="DRS")

        q_entries = self.db.get_queue_for_level(9, queue_type="DRS")
        self.assertEqual(len(q_entries), 2)
        self.assertTrue(self.db.is_user_queued_for_level(101, 9, "DRS"))
        self.assertFalse(self.db.is_user_queued_for_level(103, 9, "DRS"))

        # Need assist toggle
        self.assertTrue(self.db.toggle_need_assist(101))
        entries = self.db.get_queue_for_level(9, queue_type="DRS")
        self.assertEqual(entries[0]["need_assist"], 1)
        self.assertFalse(self.db.toggle_need_assist(101))

        # Quick start toggle
        self.assertTrue(self.db.set_quick_start(101, 9, True, queue_type="DRS"))
        entries = self.db.get_queue_for_level(9, queue_type="DRS")
        self.assertEqual(entries[0]["quick_start"], 1)

        # Extend queue
        self.db.extend_queue(101, minutes=30)

        # Leave queue level
        self.db.leave_queue_level(102, 9, "DRS")
        self.assertEqual(len(self.db.get_queue_for_level(9, queue_type="DRS")), 1)

        # Eject from all
        self.db.eject_player_from_all_queues(101)
        self.assertEqual(len(self.db.get_queue_for_level(9, queue_type="DRS")), 0)

    def test_matches_and_feedback(self):
        self.db.upsert_server(9999)
        self.db.upsert_user(201, "P1")
        self.db.upsert_user(202, "P2")
        self.db.upsert_user(203, "P3")

        match_id = self.db.create_match(
            drs_level=9,
            participant_ids=[201, 202, 203],
            queue_guild_map={201: 9999, 202: 9999, 203: 9999},
            match_type="DRS"
        )
        self.assertIsNotNone(match_id)
        self.assertGreater(match_id, 0)

        match = self.db.get_match(match_id)
        self.assertIsNotNone(match)
        self.assertEqual(match["drs_level"], 9)
        participants = self.db.get_match_participants(match_id)
        self.assertEqual(len(participants), 3)

        # Save match thread
        self.db.save_match_thread(match_id, 9999, 55555)

        # Feedback: good run
        self.db.save_feedback(match_id, 201, True)

        # Feedback: report
        report_id = self.db.save_feedback_report(
            match_id=match_id,
            reporter_id=201,
            reported_player_id=202,
            issue_type="behavior",
            thread_id=55555,
            comment="AFK during battleship engagement"
        )
        self.assertIsNotNone(report_id)

        # Check investigation report
        reports = self.db.get_feedback_reports_for_match(match_id)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["issue_type"], "behavior")


class TestI18nAndUI(unittest.TestCase):
    def setUp(self):
        self.db = db_mod.DatabaseOperations(":memory:")
        self.db.connect()
        self.db.seed_i18n_defaults()
        i18n.sync_from_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_all_languages_and_core_keys(self):
        languages = ["en", "de", "hi", "pl", "fr", "es", "ja"]
        required_keys = [
            "queue_title_drs",
            "queue_title_rs",
            "queue_empty",
            "queue_footer",
            "notify_joined",
            "notify_left",
            "notify_extend",
            "notify_qs",
            "notify_expiry_warning",
            "notify_expired",
            "notify_left_all",
            "notify_assist",
            "match_title",
            "match_proceed",
            "match_footer",
            "ephemeral_joined",
            "ephemeral_left",
            "ephemeral_extended",
            "ephemeral_left_all",
            "not_in_queue",
            "qs_confirmed",
            "ephemeral_assist_on",
            "ephemeral_assist_off"
        ]

        for lang in languages:
            for key in required_keys:
                text = i18n.get(
                    lang,
                    key,
                    pilot="Commander",
                    queue="DRS9",
                    queues="DRS9, DRS10",
                    icon="<:corp:123> ",
                    count="(1/3)",
                    users="<@1001>",
                    user_id=1001,
                    minutes=30,
                    time_left=5,
                    level=9,
                    match_id=42,
                    names="Player1, Player2"
                )
                self.assertIsNotNone(text, f"Key '{key}' in lang '{lang}' returned None")
                self.assertFalse(text.startswith("[") and text.endswith("]"), f"Key '{key}' missing translation in '{lang}': {text}")
                # Ensure no raw format specifiers like {pilot} or {queue} were unreplaced
                self.assertNotIn("{pilot}", text)
                self.assertNotIn("{queue}", text)
                self.assertNotIn("{icon}", text)

        # Test lang_set with keyword argument 'lang' and 'language' without TypeError
        for lang_code in languages:
            formatted_lang = i18n.get(lang_code, "lang_set", lang="TestLang")
            self.assertIn("TestLang", formatted_lang)
            formatted_synonym = i18n.get(lang_code, "lang_set", language="TestLang2")
            self.assertIn("TestLang2", formatted_synonym)

    def test_embed_builders_across_all_languages(self):
        languages = ["en", "de", "hi", "pl", "fr", "es", "ja"]
        queue_types = ["DRS", "RS"]

        mock_entries = [
            {
                "discord_id": 1001,
                "display_name": "StarPilot",
                "drs_level": 9,
                "queue_type": "DRS",
                "need_assist": 1,
                "quick_start": 1,
                "genesis_level": 12,
                "enrich_level": 11,
                "modt_level": 10,
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=25)).isoformat(),
                "joined_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
                "queue_guild_id": None
            }
        ]

        for lang in languages:
            # Test empty queue
            empty_embeds = ui_service.build_queue_embeds([], lang=lang)
            self.assertGreaterEqual(len(empty_embeds), 1)
            self.assertIsNotNone(empty_embeds[0].title)

            # Test populated queue
            pop_embeds = ui_service.build_queue_embeds(mock_entries, lang=lang)
            self.assertGreaterEqual(len(pop_embeds), 1)
            self.assertIsNotNone(pop_embeds[0].title)

    def test_queue_views(self):
        # 4x4 Grid view
        view = ui_service.build_queue_view()
        self.assertIsNotNone(view)
        ids = [item.custom_id for item in view.children if hasattr(item, "custom_id")]
        self.assertIn("drs_join_4", ids)
        self.assertIn("drs_join_9", ids)
        self.assertIn("drs_join_12", ids)
        self.assertIn("drs_mode_switch", ids)
        self.assertIn("drs_quickstart", ids)
        self.assertIn("drs_need_assist", ids)
        self.assertIn("drs_extend", ids)
        self.assertIn("drs_leave", ids)


class TestServicesAndCogs(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = db_mod.DatabaseOperations(":memory:")
        self.db.connect()
        self.db.seed_i18n_defaults()
        i18n.sync_from_db(self.db)

        intents = discord.Intents.default()
        self.bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
        self.bot.db = self.db
        self.bot.bonus_service = BonusService(self.db)
        
        # Mock wait_until_ready to avoid needing full Discord websocket login in unit test
        self.ready_event = asyncio.Event()
        self.bot.wait_until_ready = self.ready_event.wait
        self.bot.is_ready = lambda: True

    async def asyncTearDown(self):
        for cog in list(self.bot.cogs.values()):
            for attr_name in dir(cog):
                try:
                    attr = getattr(cog, attr_name)
                    if hasattr(attr, "cancel"):
                        attr.cancel()
                except Exception:
                    pass
        self.ready_event.set()
        await self.bot.close()
        self.db.close()

    async def test_queue_service_matchmaking(self):
        dispatched_events = []
        def mock_dispatch(event_name, *args):
            dispatched_events.append((event_name, args))

        qs = QueueService(self.db, dispatch_fn=mock_dispatch)

        self.db.upsert_user(301, "Alpha")
        self.db.upsert_user(302, "Bravo")
        self.db.upsert_user(303, "Charlie")

        # Join player 1
        res1 = await qs.join(301, "Alpha", 9, 9999, queue_type="DRS")
        self.assertEqual(res1, "joined")
        self.assertEqual(len(dispatched_events), 0)

        # Join player 2
        res2 = await qs.join(302, "Bravo", 9, 9999, queue_type="DRS")
        self.assertEqual(res2, "joined")

        # Quick start with only 1 QS player -> no match yet
        self.db.set_quick_start(301, 9, True, queue_type="DRS")
        qs_res = await qs.check_quick_start(9, "DRS")
        self.assertEqual(qs_res, "quick_start_updated")
        self.assertEqual(len(dispatched_events), 0)

        # Player 2 enables QS -> match forms!
        self.db.set_quick_start(302, 9, True, queue_type="DRS")
        qs_res2 = await qs.check_quick_start(9, "DRS")
        self.assertEqual(qs_res2, "match_formed")
        self.assertEqual(len(dispatched_events), 1)
        self.assertEqual(dispatched_events[0][0], "drs_match_formed")

    async def test_all_cogs_loadable(self):
        cog_modules = [
            "cogs.setup_cog",
            "cogs.queue_cog",
            "cogs.match_cog",
            "cogs.thread_cog",
            "cogs.feedback_cog",
            "cogs.officer_cog",
            "cogs.bonus_cog",
            "cogs.engagement_cog",
            "cogs.stats_cog",
            "cogs.investigation_cog",
            "cogs.help_cog",
            "cogs.server_emoji_cog",
        ]
        for cog_name in cog_modules:
            try:
                await self.bot.load_extension(cog_name)
                print(f"  [OK] Successfully loaded {cog_name}")
            except Exception as e:
                self.fail(f"Failed to load {cog_name}: {e}")

    def test_facts_service(self):
        facts_svc = FactsService(self.db)
        embed = facts_svc.get_random_fact_embed()
        self.assertIsNotNone(embed)
        self.assertIsNotNone(embed.title)

    def test_investigation_service(self):
        inv_svc = InvestigationService(self.db)
        dossier = inv_svc.get_player_dossier(1001)
        self.assertIn("player_id", dossier)
        self.assertIn("total_reports_against", dossier)
        embed = inv_svc.build_player_dossier_embed(dossier)
        self.assertIsNotNone(embed)

    async def test_queue_cog_forbidden_handling(self):
        from unittest.mock import MagicMock, AsyncMock
        from cogs.queue_cog import QueueCog
        import discord

        cog = QueueCog(self.bot)

        # Mock forbidden response
        mock_resp = MagicMock()
        mock_resp.status = 403
        mock_resp.reason = "Forbidden"

        # Mock channel with missing access
        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.id = 8888
        mock_channel.name = "drs-queue"
        mock_channel.permissions_for.return_value = discord.Permissions.all()
        mock_channel.fetch_message = AsyncMock(side_effect=discord.Forbidden(mock_resp, "Missing Access"))
        mock_channel.send = AsyncMock(side_effect=discord.Forbidden(mock_resp, "Missing Access"))

        mock_guild = MagicMock(spec=discord.Guild)
        mock_guild.id = 7777
        mock_guild.name = "Test Guild"
        mock_guild.get_channel.return_value = mock_channel
        self.bot.get_guild = MagicMock(return_value=mock_guild)

        server_dict = {
            "guild_id": 7777,
            "queue_channel_id": 8888,
            "queue_message_id": 9999
        }

        # Should handle Forbidden without raising exception
        try:
            await cog._ensure_queue_message(server_dict)
            await cog._push_queue_update()
        except discord.Forbidden:
            self.fail("QueueCog failed to catch discord.Forbidden gracefully")
        finally:
            cog.cog_unload()

if __name__ == "__main__":
    unittest.main(verbosity=2)
