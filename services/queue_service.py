import logging
from datetime import datetime, timedelta, timezone

import config
from db.database import _parse_dt

logger = logging.getLogger("queue_service")


class QueueService:
    def __init__(self, db, dispatch_fn=None):
        self.db = db
        self._dispatch = dispatch_fn

    def set_dispatch(self, dispatch_fn):
        self._dispatch = dispatch_fn

    def remove_expired(self) -> list[int]:
        return self.db.remove_expired_entries()

    def remove_expired_entries(self) -> list[int]:
        return self.db.remove_expired_entries()

    async def join(self, discord_id: int, display_name: str, drs_level: int, guild_id: int, queue_type: str = "DRS") -> str:
        if self.db.is_user_queued_for_level(discord_id, drs_level, queue_type):
            return "already_queued_for_level"

        expires_at = datetime.utcnow() + timedelta(minutes=config.DEFAULT_EXPIRY_MINS)
        self.db.join_queue(discord_id, drs_level, expires_at, guild_id, queue_type=queue_type)

        target_size = config.DRS_MATCH_SIZE if queue_type == "DRS" else config.RS_MATCH_SIZE
        entries = self.db.get_queue_for_level(drs_level, queue_type=queue_type)
        if len(entries) >= target_size:
            await self._form_match(drs_level, entries[:target_size], queue_type=queue_type)
            return "match_formed"

        return "joined"

    async def check_quick_start(self, drs_level: int, queue_type: str = "DRS") -> str:
        """
        Check if quick start conditions are met:
        - DRS (max 3): 2 players in queue and both accept quick start.
        - RS (max 4): 2 or 3 players in queue and ALL players in queue accept quick start.
        """
        entries = self.db.get_queue_for_level(drs_level, queue_type=queue_type)
        count = len(entries)
        if count < 2:
            return "not_enough_players"

        target_size = config.DRS_MATCH_SIZE if queue_type == "DRS" else config.RS_MATCH_SIZE
        if count >= target_size:
            # Full match should be formed
            await self._form_match(drs_level, entries[:target_size], queue_type=queue_type)
            return "match_formed"

        # Check if all currently queued players have quick_start set
        if all(e.get("quick_start") for e in entries):
            await self._form_match(drs_level, entries, queue_type=queue_type)
            return "match_formed"

        return "quick_start_updated"

    async def _form_match(self, drs_level: int, entries: list[dict], queue_type: str = "DRS"):
        participant_ids = [e["discord_id"] for e in entries]

        # Calculate player wait times and total queue formation duration
        now_dt = datetime.now(timezone.utc)
        wait_times_map: dict[int, int] = {}
        earliest_joined = None

        for e in entries:
            j_at = e.get("joined_at")
            if isinstance(j_at, datetime):
                j_dt = j_at if j_at.tzinfo else j_at.replace(tzinfo=timezone.utc)
            elif j_at:
                j_dt = _parse_dt(j_at)
            else:
                j_dt = now_dt

            if j_dt:
                wait_sec = max(0, int((now_dt - j_dt).total_seconds()))
                if earliest_joined is None or j_dt < earliest_joined:
                    earliest_joined = j_dt
            else:
                wait_sec = 0

            wait_times_map[e["discord_id"]] = wait_sec

        queue_duration_seconds = max(0, int((now_dt - earliest_joined).total_seconds())) if earliest_joined else 0

        # Capture queue_guild_id BEFORE deleting entries
        queue_guild_map = self._capture_queue_guilds(participant_ids, drs_level, queue_type)

        # Create match in DB
        match_id = self.db.create_match(
            drs_level, participant_ids, queue_guild_map,
            match_type=queue_type,
            wait_times_map=wait_times_map,
            queue_duration_seconds=queue_duration_seconds
        )
        if not match_id:
            logger.error(f"Failed to create match record for {queue_type} Level {drs_level}")
            return

        # Eject players from ALL incomplete queues they joined and log wait times
        for pid in participant_ids:
            self.db.eject_player_from_all_queues(pid, reason="matched", match_id=match_id)

        participants = [
            {"discord_id": e["discord_id"], "display_name": e["display_name"]}
            for e in entries
        ]

        if self._dispatch:
            self._dispatch("drs_match_formed", match_id, drs_level, participants, queue_type)
        else:
            logger.error("QueueService has no dispatch function — match event lost!")

    def _capture_queue_guilds(self, participant_ids: list[int], drs_level: int, queue_type: str = "DRS") -> dict[int, int]:
        """
        Read queue_guild_id from queue_entries for each participant RIGHT NOW,
        before the entries are deleted. Returns {discord_id: queue_guild_id}.
        """
        if not participant_ids:
            return {}
        placeholders = ",".join(["?"] * len(participant_ids))
        rows = self.db._execute(
            f"""SELECT discord_id, queue_guild_id FROM queue_entries
                WHERE discord_id IN ({placeholders}) AND drs_level = ? AND queue_type = ?""",
            participant_ids + [drs_level, queue_type],
            fetch_all=True,
        )
        result = {}
        if rows:
            for r in rows:
                if r.get("queue_guild_id"):
                    result[r["discord_id"]] = r["queue_guild_id"]
        return result


