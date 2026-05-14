import logging
from datetime import datetime, timedelta

import config

logger = logging.getLogger("queue_service")


class QueueService:
    def __init__(self, db, dispatch_fn=None):
        self.db = db
        self._dispatch = dispatch_fn

    def set_dispatch(self, dispatch_fn):
        self._dispatch = dispatch_fn

    async def join(self, discord_id: int, display_name: str, drs_level: int, guild_id: int) -> str:
        if self.db.is_user_queued_for_level(discord_id, drs_level):
            return "already_queued_for_level"

        expires_at = datetime.utcnow() + timedelta(minutes=config.DEFAULT_QUEUE_MINS)
        self.db.join_queue(discord_id, drs_level, expires_at, guild_id)

        entries = self.db.get_queue_for_level(drs_level)
        if len(entries) >= config.MATCH_SIZE:
            await self._form_match(drs_level, entries[:config.MATCH_SIZE])
            return "match_formed"

        return "joined"

    async def quick_start_match(self, drs_level: int, entries: list[dict]) -> str:
        """Force a match with exactly 2 players — both must have quick_start set."""
        if len(entries) < 2:
            return "not_enough_players"

        two = entries[:2]
        participant_ids = [e["discord_id"] for e in two]

        # Capture queue_guild_id BEFORE deleting entries
        queue_guild_map = self._capture_queue_guilds(participant_ids, drs_level)

        for pid in participant_ids:
            self.db.leave_queue(pid)

        match_id = self.db.create_match(drs_level, participant_ids, queue_guild_map)
        if not match_id:
            logger.error(f"quick_start_match: failed to create match for DRS{drs_level}")
            return "db_error"

        participants = [
            {"discord_id": e["discord_id"], "display_name": e["display_name"]}
            for e in two
        ]

        if self._dispatch:
            self._dispatch("drs_match_formed", match_id, drs_level, participants)
        else:
            logger.error("QueueService has no dispatch function — match event lost!")

        return "match_formed"

    async def _form_match(self, drs_level: int, entries: list[dict]):
        participant_ids = [e["discord_id"] for e in entries]

        # Capture queue_guild_id BEFORE deleting entries
        queue_guild_map = self._capture_queue_guilds(participant_ids, drs_level)

        for pid in participant_ids:
            self.db.leave_queue(pid)

        match_id = self.db.create_match(drs_level, participant_ids, queue_guild_map)
        if not match_id:
            logger.error(f"Failed to create match record for DRS{drs_level}")
            return

        participants = [
            {"discord_id": e["discord_id"], "display_name": e["display_name"]}
            for e in entries
        ]

        if self._dispatch:
            self._dispatch("drs_match_formed", match_id, drs_level, participants)
        else:
            logger.error("QueueService has no dispatch function — match event lost!")

    def _capture_queue_guilds(self, participant_ids: list[int], drs_level: int) -> dict[int, int]:
        """
        Read queue_guild_id from queue_entries for each participant RIGHT NOW,
        before the entries are deleted. Returns {discord_id: queue_guild_id}.
        """
        if not participant_ids:
            return {}
        placeholders = ",".join(["?"] * len(participant_ids))
        rows = self.db._execute(
            f"""SELECT discord_id, queue_guild_id FROM queue_entries
                WHERE discord_id IN ({placeholders}) AND drs_level = ?""",
            participant_ids + [drs_level],
            fetch_all=True,
        )
        result = {}
        if rows:
            for r in rows:
                if r.get("queue_guild_id"):
                    result[r["discord_id"]] = r["queue_guild_id"]
        return result
