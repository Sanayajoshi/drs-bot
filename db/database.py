import sqlite3
import logging
from datetime import datetime, timezone
import config


def _now_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _parse_dt(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        dt = datetime.strptime(str(val), "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


class DatabaseOperations:
    def __init__(self, db_path: str = None):
        self.logger = logging.getLogger("drs_database")
        self.db_path = db_path or config.DB_PATH
        self.connection: sqlite3.Connection | None = None

    def connect(self) -> bool:
        try:
            self.connection = sqlite3.connect(
                self.db_path, check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA foreign_keys=ON")
            self._create_tables()
            self._migrate()
            self.logger.info(f"SQLite connected: {self.db_path}")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def close(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                self.logger.error(f"Error closing: {e}")

    def _create_tables(self):
        stmts = [
            """CREATE TABLE IF NOT EXISTS servers (
                guild_id                INTEGER PRIMARY KEY,
                queue_channel_id        INTEGER,
                queue_message_id        INTEGER,
                notification_channel_id INTEGER,
                officer_channel_id      INTEGER,
                manager_role_id         INTEGER,
                language                TEXT NOT NULL DEFAULT 'en',
                role_drs7               INTEGER,
                role_drs8               INTEGER,
                role_drs9               INTEGER,
                role_drs10              INTEGER,
                role_drs11              INTEGER,
                role_drs12              INTEGER,
                created_at              TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            """CREATE TABLE IF NOT EXISTS users (
                discord_id    INTEGER PRIMARY KEY,
                display_name  TEXT NOT NULL,
                genesis_level INTEGER CHECK (genesis_level BETWEEN 6 AND 15),
                enrich_level  INTEGER CHECK (enrich_level  BETWEEN 6 AND 15),
                modt_level    INTEGER CHECK (modt_level    BETWEEN 6 AND 15),
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            """CREATE TABLE IF NOT EXISTS user_servers (
                discord_id   INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                guild_id     INTEGER NOT NULL REFERENCES servers(guild_id) ON DELETE CASCADE,
                display_name TEXT NOT NULL,
                last_seen    TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (discord_id, guild_id)
            )""",
            """CREATE TABLE IF NOT EXISTS queue_entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id  INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                drs_level   INTEGER NOT NULL CHECK (drs_level BETWEEN 7 AND 12),
                expires_at  TEXT NOT NULL,
                joined_at   TEXT NOT NULL DEFAULT (datetime('now')),
                quick_start    INTEGER NOT NULL DEFAULT 0,
                queue_guild_id INTEGER,
                UNIQUE (discord_id, drs_level)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_queue_drs     ON queue_entries(drs_level)",
            "CREATE INDEX IF NOT EXISTS idx_queue_expires ON queue_entries(expires_at)",
            """CREATE TABLE IF NOT EXISTS matches (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                drs_level  INTEGER NOT NULL,
                status     TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            """CREATE TABLE IF NOT EXISTS match_participants (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id   INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                discord_id INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                UNIQUE (match_id, discord_id)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_mp_match ON match_participants(match_id)",
            """CREATE TABLE IF NOT EXISTS match_threads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id   INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                guild_id   INTEGER NOT NULL REFERENCES servers(guild_id) ON DELETE CASCADE,
                thread_id  INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (match_id, guild_id)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_mt_match ON match_threads(match_id)",
            """CREATE TABLE IF NOT EXISTS feedback (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id     INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                discord_id   INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                was_positive INTEGER NOT NULL,
                submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (match_id, discord_id)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_fb_match ON feedback(match_id)",
        ]
        with self.connection:
            for stmt in stmts:
                self.connection.execute(stmt)

    def _migrate(self):
        migrations = [
            "ALTER TABLE queue_entries ADD COLUMN quick_start INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE servers ADD COLUMN role_drs7  INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs8  INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs9  INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs10 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs11 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs12 INTEGER",
            "ALTER TABLE queue_entries ADD COLUMN queue_guild_id INTEGER",
        ]
        for stmt in migrations:
            try:
                self.connection.execute(stmt)
                self.connection.commit()
            except Exception:
                pass

    def _execute(self, query, params=(), fetch_one=False, fetch_all=False):
        if not self.connection:
            self.logger.warning("No active connection")
            return None
        try:
            cur = self.connection.execute(query, params)
            self.connection.commit()
            if fetch_one:
                row = cur.fetchone()
                return dict(row) if row else None
            if fetch_all:
                rows = cur.fetchall()
                return [dict(r) for r in rows]
            return True
        except Exception as e:
            self.logger.error(f"Query error: {e} | SQL: {query[:120]}", exc_info=True)
            try:
                self.connection.rollback()
            except Exception:
                pass
            return None

    def upsert_server(self, guild_id: int, **kwargs) -> bool:
        fields = ["queue_channel_id", "queue_message_id", "notification_channel_id",
                  "officer_channel_id", "manager_role_id", "language",
                  "role_drs7", "role_drs8", "role_drs9", "role_drs10", "role_drs11", "role_drs12"]
        updates = {k: v for k, v in kwargs.items() if k in fields}
        if not updates:
            return self._execute(
                "INSERT OR IGNORE INTO servers (guild_id) VALUES (?)", (guild_id,)
            ) is not None
        cols   = ", ".join(updates.keys())
        vals   = ", ".join(["?"] * len(updates))
        upsert = ", ".join(f"{k} = excluded.{k}" for k in updates)
        query  = f"INSERT INTO servers (guild_id, {cols}) VALUES (?, {vals}) ON CONFLICT(guild_id) DO UPDATE SET {upsert}"
        return self._execute(query, [guild_id] + list(updates.values())) is not None

    def get_server(self, guild_id: int) -> dict | None:
        return self._execute(
            """SELECT guild_id, queue_channel_id, queue_message_id,
                      notification_channel_id, officer_channel_id, manager_role_id, language,
                      role_drs7, role_drs8, role_drs9, role_drs10, role_drs11, role_drs12
               FROM servers WHERE guild_id = ?""",
            (guild_id,), fetch_one=True
        )

    def get_all_servers(self) -> list[dict]:
        return self._execute(
            "SELECT guild_id, queue_channel_id, queue_message_id FROM servers",
            fetch_all=True
        ) or []

    def set_queue_message_id(self, guild_id: int, message_id: int) -> bool:
        return self._execute(
            "UPDATE servers SET queue_message_id = ? WHERE guild_id = ?",
            (message_id, guild_id)
        ) is not None

    def get_ping_role_for_level(self, guild_id: int, drs_level: int) -> int | None:
        server = self.get_server(guild_id)
        if not server:
            return None
        return server.get(f"role_drs{drs_level}")

    def upsert_user(self, discord_id: int, display_name: str) -> bool:
        return self._execute(
            """INSERT INTO users (discord_id, display_name) VALUES (?, ?)
               ON CONFLICT(discord_id) DO UPDATE SET display_name = excluded.display_name""",
            (discord_id, display_name)
        ) is not None

    def upsert_user_server(self, discord_id: int, guild_id: int, display_name: str) -> bool:
        return self._execute(
            """INSERT INTO user_servers (discord_id, guild_id, display_name, last_seen)
               VALUES (?, ?, ?, datetime('now'))
               ON CONFLICT(discord_id, guild_id) DO UPDATE
               SET display_name = excluded.display_name, last_seen = datetime('now')""",
            (discord_id, guild_id, display_name)
        ) is not None

    def get_user_guilds(self, discord_id: int) -> list[int]:
        rows = self._execute(
            "SELECT guild_id FROM user_servers WHERE discord_id = ?",
            (discord_id,), fetch_all=True
        )
        return [r["guild_id"] for r in rows] if rows else []

    def set_user_mod_level(self, discord_id: int, mod: str, level: int) -> bool:
        allowed = {"genesis": "genesis_level", "enrich": "enrich_level", "modt": "modt_level"}
        col = allowed.get(mod)
        if not col:
            return False
        return self._execute(
            f"UPDATE users SET {col} = ? WHERE discord_id = ?",
            (level, discord_id)
        ) is not None

    def get_user_mod_levels(self, discord_id: int) -> dict:
        row = self._execute(
            "SELECT genesis_level, enrich_level, modt_level FROM users WHERE discord_id = ?",
            (discord_id,), fetch_one=True
        )
        return row if row else {"genesis_level": None, "enrich_level": None, "modt_level": None}

    def join_queue(self, discord_id: int, drs_level: int, expires_at: datetime, guild_id: int = None) -> bool:
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
        return self._execute(
            """INSERT INTO queue_entries (discord_id, drs_level, expires_at, queue_guild_id) VALUES (?, ?, ?, ?)
               ON CONFLICT(discord_id, drs_level) DO UPDATE SET expires_at = excluded.expires_at, queue_guild_id = excluded.queue_guild_id""",
            (discord_id, drs_level, expires_str, guild_id)
        ) is not None

    def leave_queue(self, discord_id: int) -> bool:
        return self._execute(
            "DELETE FROM queue_entries WHERE discord_id = ?", (discord_id,)
        ) is not None

    def leave_queue_level(self, discord_id: int, drs_level: int) -> bool:
        return self._execute(
            "DELETE FROM queue_entries WHERE discord_id = ? AND drs_level = ?",
            (discord_id, drs_level)
        ) is not None

    def extend_queue(self, discord_id: int, minutes: int = 30) -> bool:
        return self._execute(
            """UPDATE queue_entries SET expires_at = datetime(expires_at, ? || ' minutes')
               WHERE discord_id = ?""",
            (f"+{minutes}", discord_id)
        ) is not None

    def set_quick_start(self, discord_id: int, drs_level: int, value: bool) -> bool:
        return self._execute(
            "UPDATE queue_entries SET quick_start = ? WHERE discord_id = ? AND drs_level = ?",
            (1 if value else 0, discord_id, drs_level)
        ) is not None

    def get_queue_for_level(self, drs_level: int) -> list[dict]:
        rows = self._execute(
            """SELECT qe.discord_id, u.display_name, qe.expires_at, qe.joined_at, qe.quick_start
               FROM queue_entries qe JOIN users u ON u.discord_id = qe.discord_id
               WHERE qe.drs_level = ? AND qe.expires_at > datetime('now')
               ORDER BY qe.joined_at ASC""",
            (drs_level,), fetch_all=True
        )
        if not rows:
            return []
        return [{"discord_id": r["discord_id"], "display_name": r["display_name"],
                 "expires_at": _parse_dt(r["expires_at"]), "joined_at": _parse_dt(r["joined_at"]),
                 "quick_start": bool(r["quick_start"])} for r in rows]

    def get_full_queue(self) -> list[dict]:
        rows = self._execute(
            """SELECT qe.discord_id, u.display_name, qe.drs_level, qe.expires_at, qe.quick_start,
                      u.genesis_level, u.enrich_level, u.modt_level
               FROM queue_entries qe JOIN users u ON u.discord_id = qe.discord_id
               WHERE qe.expires_at > datetime('now')
               ORDER BY qe.drs_level, qe.joined_at ASC""",
            fetch_all=True
        )
        if not rows:
            return []
        return [{"discord_id": r["discord_id"], "display_name": r["display_name"],
                 "drs_level": r["drs_level"], "expires_at": _parse_dt(r["expires_at"]),
                 "quick_start": bool(r["quick_start"]),
                 "genesis_level": r["genesis_level"], "enrich_level": r["enrich_level"],
                 "modt_level": r["modt_level"]} for r in rows]

    def remove_expired_entries(self) -> list[int]:
        if not self.connection:
            return []
        try:
            cur = self.connection.execute(
                "SELECT discord_id FROM queue_entries WHERE expires_at <= datetime('now')"
            )
            ids = [r[0] for r in cur.fetchall()]
            if ids:
                self.connection.execute(
                    "DELETE FROM queue_entries WHERE expires_at <= datetime('now')"
                )
                self.connection.commit()
            return ids
        except Exception as e:
            self.logger.error(f"remove_expired_entries failed: {e}")
            return []

    def is_user_queued_for_level(self, discord_id: int, drs_level: int) -> bool:
        row = self._execute(
            """SELECT 1 FROM queue_entries
               WHERE discord_id = ? AND drs_level = ? AND expires_at > datetime('now')""",
            (discord_id, drs_level), fetch_one=True
        )
        return row is not None

    def get_user_queue_levels(self, discord_id: int) -> list[int]:
        rows = self._execute(
            "SELECT drs_level FROM queue_entries WHERE discord_id = ? AND expires_at > datetime('now')",
            (discord_id,), fetch_all=True
        )
        return [r["drs_level"] for r in rows] if rows else []

    def create_match(self, drs_level: int, participant_ids: list[int]) -> int | None:
        if not self.connection:
            return None
        try:
            with self.connection:
                cur = self.connection.execute(
                    "INSERT INTO matches (drs_level) VALUES (?)", (drs_level,)
                )
                match_id = cur.lastrowid
                self.connection.executemany(
                    "INSERT INTO match_participants (match_id, discord_id) VALUES (?, ?)",
                    [(match_id, uid) for uid in participant_ids]
                )
            return match_id
        except Exception as e:
            self.logger.error(f"create_match failed: {e}", exc_info=True)
            return None

    def get_match_participants(self, match_id: int) -> list[dict]:
        return self._execute(
            """SELECT mp.discord_id, u.display_name, u.genesis_level, u.enrich_level, u.modt_level
               FROM match_participants mp JOIN users u ON u.discord_id = mp.discord_id
               WHERE mp.match_id = ?""",
            (match_id,), fetch_all=True
        ) or []

    def get_user_match_count(self, discord_id: int, drs_level: int) -> int:
        row = self._execute(
            """SELECT COUNT(*) as cnt FROM match_participants mp
               JOIN matches m ON m.id = mp.match_id
               WHERE mp.discord_id = ? AND m.drs_level = ?""",
            (discord_id, drs_level), fetch_one=True
        )
        return row["cnt"] if row else 0

    def get_participant_queue_guilds(self, participant_ids: list[int]) -> dict[int, int]:
        """Returns {discord_id: queue_guild_id} for each participant — the guild they queued from."""
        if not participant_ids:
            return {}
        placeholders = ",".join(["?"] * len(participant_ids))
        rows = self._execute(
            f"SELECT discord_id, queue_guild_id FROM queue_entries WHERE discord_id IN ({placeholders})",
            participant_ids, fetch_all=True
        )
        if not rows:
            # Fallback: use user_servers last_seen
            result = {}
            for pid in participant_ids:
                guilds = self.get_user_guilds(pid)
                if guilds:
                    result[pid] = guilds[0]
            return result
        return {r["discord_id"]: r["queue_guild_id"] for r in rows if r["queue_guild_id"]}

    def save_match_thread(self, match_id: int, guild_id: int, thread_id: int) -> bool:
        return self._execute(
            """INSERT INTO match_threads (match_id, guild_id, thread_id) VALUES (?, ?, ?)
               ON CONFLICT(match_id, guild_id) DO UPDATE SET thread_id = excluded.thread_id""",
            (match_id, guild_id, thread_id)
        ) is not None

    def get_match_threads(self, match_id: int) -> list[dict]:
        return self._execute(
            "SELECT guild_id, thread_id FROM match_threads WHERE match_id = ?",
            (match_id,), fetch_all=True
        ) or []

    def get_match_id_by_thread(self, thread_id: int) -> int | None:
        row = self._execute(
            "SELECT match_id FROM match_threads WHERE thread_id = ?",
            (thread_id,), fetch_one=True
        )
        return row["match_id"] if row else None

    def save_feedback(self, match_id: int, discord_id: int, was_positive: bool) -> bool:
        return self._execute(
            """INSERT INTO feedback (match_id, discord_id, was_positive) VALUES (?, ?, ?)
               ON CONFLICT(match_id, discord_id) DO NOTHING""",
            (match_id, discord_id, 1 if was_positive else 0)
        ) is not None

    def get_match_feedback(self, match_id: int) -> list[dict]:
        return self._execute(
            """SELECT f.discord_id, u.display_name, f.was_positive, f.submitted_at
               FROM feedback f JOIN users u ON u.discord_id = f.discord_id
               WHERE f.match_id = ?""",
            (match_id,), fetch_all=True
        ) or []
