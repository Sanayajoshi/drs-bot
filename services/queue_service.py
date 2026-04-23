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

        for pid in participant_ids:
            self.db.leave_queue(pid)

        match_id = self.db.create_match(drs_level, participant_ids)
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

        for pid in participant_ids:
            self.db.leave_queue(pid)

        match_id = self.db.create_match(drs_level, participant_ids)
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
