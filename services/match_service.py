import logging

logger = logging.getLogger("match_service")


class MatchService:
    """Thin wrapper for match DB operations used by MatchCog."""

    def __init__(self, db):
        self.db = db

    def get_participants(self, match_id: int) -> list[dict]:
        return self.db.get_match_participants(match_id)
