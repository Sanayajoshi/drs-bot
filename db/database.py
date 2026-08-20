import sqlite3
import logging
from datetime import datetime, timezone, timedelta
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
                need_assist   INTEGER NOT NULL DEFAULT 0,
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
                drs_level   INTEGER NOT NULL CHECK (drs_level BETWEEN 4 AND 12),
                expires_at  TEXT NOT NULL,
                joined_at   TEXT NOT NULL DEFAULT (datetime('now')),
                quick_start    INTEGER NOT NULL DEFAULT 0,
                queue_guild_id INTEGER,
                queue_type     TEXT NOT NULL DEFAULT 'DRS',
                UNIQUE (discord_id, drs_level, queue_type)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_queue_drs     ON queue_entries(drs_level)",
            "CREATE INDEX IF NOT EXISTS idx_queue_expires ON queue_entries(expires_at)",
            """CREATE TABLE IF NOT EXISTS matches (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                drs_level  INTEGER NOT NULL,
                status     TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            # queue_guild_id stored here so it survives queue entry deletion
            """CREATE TABLE IF NOT EXISTS match_participants (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id       INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                discord_id     INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                queue_guild_id INTEGER,
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
            """CREATE TABLE IF NOT EXISTS feedback_reports (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id           INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                reporter_id        INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                reported_player_id INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                issue_type         TEXT NOT NULL,
                comment            TEXT,
                thread_id          INTEGER,
                created_at         TEXT NOT NULL DEFAULT (datetime('now')),
                resolved_at        TEXT,
                resolved_by        INTEGER,
                resolution_notes   TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_fr_match    ON feedback_reports(match_id)",
            "CREATE INDEX IF NOT EXISTS idx_fr_reported ON feedback_reports(reported_player_id)",
            """CREATE TABLE IF NOT EXISTS report_threads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id  INTEGER NOT NULL REFERENCES feedback_reports(id) ON DELETE CASCADE,
                match_id   INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                guild_id   INTEGER NOT NULL REFERENCES servers(guild_id) ON DELETE CASCADE,
                channel_id INTEGER NOT NULL,
                thread_id  INTEGER NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                closed_at  TEXT,
                UNIQUE (report_id, guild_id)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_rt_report ON report_threads(report_id)",
            "CREATE INDEX IF NOT EXISTS idx_rt_thread ON report_threads(thread_id)",
            # Corp bonuses — one active bonus per guild at a time
            """CREATE TABLE IF NOT EXISTS corp_bonuses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id    INTEGER NOT NULL REFERENCES servers(guild_id) ON DELETE CASCADE,
                corp_name   TEXT NOT NULL,
                bonus_pct   INTEGER NOT NULL,
                expires_at  TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (guild_id)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_cb_guild   ON corp_bonuses(guild_id)",
            "CREATE INDEX IF NOT EXISTS idx_cb_expires ON corp_bonuses(expires_at)",
                        # Add this to the stmts list in _create_tables()
            """CREATE TABLE IF NOT EXISTS tracked_corps (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                corp_id     TEXT NOT NULL UNIQUE,
                corp_name   TEXT NOT NULL,
                bonus_pct   INTEGER,
                last_fetched TEXT NOT NULL DEFAULT (datetime('now')),
                is_active   INTEGER NOT NULL DEFAULT 1,
                fetch_error TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            "CREATE INDEX IF NOT EXISTS idx_tc_corp_id ON tracked_corps(corp_id)",
            "CREATE INDEX IF NOT EXISTS idx_tc_bonus ON tracked_corps(bonus_pct DESC)",
            "CREATE INDEX IF NOT EXISTS idx_tc_active ON tracked_corps(is_active)",
        ]
        with self.connection:
            for stmt in stmts:
                self.connection.execute(stmt)

    def _migrate(self):
        migrations = [
            # existing migrations — safe no-ops if already applied
            "ALTER TABLE queue_entries ADD COLUMN quick_start INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE servers ADD COLUMN role_drs7  INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs8  INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs9  INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs10 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs11 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_drs12 INTEGER",
            "ALTER TABLE queue_entries ADD COLUMN queue_guild_id INTEGER",
            # Store queue_guild_id on match_participants so it survives queue deletion
            "ALTER TABLE match_participants ADD COLUMN queue_guild_id INTEGER",
            # feedback_reports
            """CREATE TABLE IF NOT EXISTS feedback_reports (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id           INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                reporter_id        INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                reported_player_id INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                issue_type         TEXT NOT NULL,
                comment            TEXT,
                thread_id          INTEGER,
                created_at         TEXT NOT NULL DEFAULT (datetime('now')),
                resolved_at        TEXT,
                resolved_by        INTEGER,
                resolution_notes   TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_fr_match    ON feedback_reports(match_id)",
            "ALTER TABLE matches ADD COLUMN feedback_sent_at TEXT",
            "ALTER TABLE feedback_reports ADD COLUMN resolved_at TEXT",
            "ALTER TABLE feedback_reports ADD COLUMN resolved_by INTEGER",
            "ALTER TABLE feedback_reports ADD COLUMN resolution_notes TEXT",
            """CREATE TABLE IF NOT EXISTS report_threads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id  INTEGER NOT NULL REFERENCES feedback_reports(id) ON DELETE CASCADE,
                match_id   INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                guild_id   INTEGER NOT NULL REFERENCES servers(guild_id) ON DELETE CASCADE,
                channel_id INTEGER NOT NULL,
                thread_id  INTEGER NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                closed_at  TEXT,
                UNIQUE (report_id, guild_id)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_rt_report ON report_threads(report_id)",
            "CREATE INDEX IF NOT EXISTS idx_rt_thread ON report_threads(thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_fr_reported ON feedback_reports(reported_player_id)",
            # corp_bonuses
            """CREATE TABLE IF NOT EXISTS corp_bonuses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id    INTEGER NOT NULL REFERENCES servers(guild_id) ON DELETE CASCADE,
                corp_name   TEXT NOT NULL,
                bonus_pct   INTEGER NOT NULL,
                expires_at  TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (guild_id)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_cb_guild   ON corp_bonuses(guild_id)",
            "CREATE INDEX IF NOT EXISTS idx_cb_expires ON corp_bonuses(expires_at)",
            "ALTER TABLE users ADD COLUMN need_assist INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN queue_mode TEXT NOT NULL DEFAULT 'DRS'",
            "ALTER TABLE queue_entries ADD COLUMN queue_type TEXT NOT NULL DEFAULT 'DRS'",
            "ALTER TABLE matches ADD COLUMN match_type TEXT NOT NULL DEFAULT 'DRS'",
            "ALTER TABLE servers ADD COLUMN fact_frequency_hours INTEGER NOT NULL DEFAULT 4",
            "ALTER TABLE servers ADD COLUMN last_fact_sent TEXT",
            "ALTER TABLE servers ADD COLUMN role_rs4 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_rs5 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_rs6 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_rs7 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_rs8 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_rs9 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_rs10 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_rs11 INTEGER",
            "ALTER TABLE servers ADD COLUMN role_rs12 INTEGER",
            """CREATE TABLE IF NOT EXISTS queue_wait_logs (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id            INTEGER NOT NULL,
                queue_type            TEXT NOT NULL,
                drs_level             INTEGER NOT NULL,
                joined_at             TEXT NOT NULL,
                left_at               TEXT NOT NULL DEFAULT (datetime('now')),
                wait_duration_seconds INTEGER NOT NULL DEFAULT 0,
                exit_reason           TEXT NOT NULL,
                match_id              INTEGER
            )""",
            "CREATE INDEX IF NOT EXISTS idx_qwl_discord ON queue_wait_logs(discord_id)",
        ]
        for stmt in migrations:
            try:
                self.connection.execute(stmt)
                self.connection.commit()
            except Exception:
                pass

        # Migrate queue_entries table constraint / schema if needed
        try:
            cur = self.connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='queue_entries'")
            row = cur.fetchone()
            if row and ("BETWEEN 7 AND 12" in row[0] or "queue_type" not in row[0] or "UNIQUE (discord_id, drs_level, queue_type)" not in row[0]):
                self.logger.info("Migrating queue_entries table constraint to ALLOW levels 4-12 and UNIQUE(discord_id, drs_level, queue_type)...")
                self.connection.execute("PRAGMA foreign_keys=OFF")
                self.connection.execute("""
                    CREATE TABLE queue_entries_new (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        discord_id  INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
                        drs_level   INTEGER NOT NULL CHECK (drs_level BETWEEN 4 AND 12),
                        expires_at  TEXT NOT NULL,
                        joined_at   TEXT NOT NULL DEFAULT (datetime('now')),
                        quick_start    INTEGER NOT NULL DEFAULT 0,
                        queue_guild_id INTEGER,
                        queue_type     TEXT NOT NULL DEFAULT 'DRS',
                        UNIQUE (discord_id, drs_level, queue_type)
                    )
                """)
                self.connection.execute("""
                    INSERT OR IGNORE INTO queue_entries_new (id, discord_id, drs_level, expires_at, joined_at, quick_start, queue_guild_id, queue_type)
                    SELECT id, discord_id, drs_level, expires_at, joined_at, quick_start, queue_guild_id, COALESCE(queue_type, 'DRS')
                    FROM queue_entries
                """)
                self.connection.execute("DROP TABLE queue_entries")
                self.connection.execute("ALTER TABLE queue_entries_new RENAME TO queue_entries")
                self.connection.execute("CREATE INDEX IF NOT EXISTS idx_queue_drs ON queue_entries(drs_level)")
                self.connection.execute("CREATE INDEX IF NOT EXISTS idx_queue_expires ON queue_entries(expires_at)")
                self.connection.execute("PRAGMA foreign_keys=ON")
                self.connection.commit()
                self.logger.info("Successfully migrated queue_entries table constraint!")
        except Exception as e:
            self.logger.error(f"Failed to migrate queue_entries table: {e}")

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
                      role_drs7, role_drs8, role_drs9, role_drs10, role_drs11, role_drs12,
                      fact_frequency_hours, last_fact_sent
               FROM servers WHERE guild_id = ?""",
            (guild_id,), fetch_one=True
        )

    def get_all_servers(self) -> list[dict]:
        return self._execute(
            """SELECT guild_id, queue_channel_id, queue_message_id,
                      notification_channel_id, officer_channel_id, manager_role_id, language,
                      fact_frequency_hours, last_fact_sent
               FROM servers""",
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
            "SELECT genesis_level, enrich_level, modt_level, need_assist FROM users WHERE discord_id = ?",
            (discord_id,), fetch_one=True
        )
        return row if row else {"genesis_level": None, "enrich_level": None, "modt_level": None, "need_assist": 0}

    def get_user(self, discord_id: int) -> dict | None:
        row = self._execute(
            "SELECT discord_id, display_name, genesis_level, enrich_level, modt_level, need_assist, queue_mode FROM users WHERE discord_id = ?",
            (discord_id,), fetch_one=True
        )
        if row:
            row["need_assist"] = bool(row.get("need_assist", 0))
            if not row.get("queue_mode"):
                row["queue_mode"] = "DRS"
        return row

    def get_user_queue_mode(self, discord_id: int) -> str:
        user = self.get_user(discord_id)
        if user and user.get("queue_mode"):
            return user["queue_mode"]
        return "DRS"

    def set_user_queue_mode(self, discord_id: int, mode: str, display_name: str = None) -> str:
        if display_name:
            self.upsert_user(discord_id, display_name)
        self._execute(
            "UPDATE users SET queue_mode = ? WHERE discord_id = ?",
            (mode, discord_id)
        )
        return mode

    def toggle_user_queue_mode(self, discord_id: int, display_name: str = None) -> str:
        current = self.get_user_queue_mode(discord_id)
        new_mode = "RS" if current == "DRS" else "DRS"
        return self.set_user_queue_mode(discord_id, new_mode, display_name)

    def set_need_assist(self, discord_id: int, need_assist: bool) -> bool:
        return self._execute(
            "UPDATE users SET need_assist = ? WHERE discord_id = ?",
            (1 if need_assist else 0, discord_id)
        ) is not None

    def toggle_need_assist(self, discord_id: int) -> bool:
        user = self.get_user(discord_id)
        current = user.get("need_assist", False) if user else False
        new_val = not current
        self.set_need_assist(discord_id, new_val)
        return new_val

    def log_queue_wait(self, discord_id: int, queue_type: str, drs_level: int, joined_at: str, exit_reason: str, match_id: int = None):
        if not joined_at:
            joined_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        try:
            j_dt = _parse_dt(joined_at) or datetime.utcnow().replace(tzinfo=timezone.utc)
            now_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
            duration = int((now_dt - j_dt).total_seconds())
            if duration < 0:
                duration = 0
        except Exception:
            duration = 0

        self._execute(
            """INSERT INTO queue_wait_logs 
               (discord_id, queue_type, drs_level, joined_at, left_at, wait_duration_seconds, exit_reason, match_id)
               VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?)""",
            (discord_id, queue_type, drs_level, str(joined_at), duration, exit_reason, match_id)
        )

    def join_queue(self, discord_id: int, drs_level: int, expires_at: datetime, guild_id: int = None, queue_type: str = "DRS") -> bool:
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
        joined_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return self._execute(
            """INSERT INTO queue_entries (discord_id, drs_level, queue_type, expires_at, joined_at, queue_guild_id) VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(discord_id, drs_level, queue_type) DO UPDATE SET expires_at = excluded.expires_at, queue_guild_id = excluded.queue_guild_id""",
            (discord_id, drs_level, queue_type, expires_str, joined_str, guild_id)
        ) is not None

    def leave_queue(self, discord_id: int, queue_type: str = None, reason: str = "manual_exit", match_id: int = None) -> bool:
        # Log wait times before deletion
        if queue_type:
            entries = self._execute(
                "SELECT drs_level, queue_type, joined_at FROM queue_entries WHERE discord_id = ? AND queue_type = ?",
                (discord_id, queue_type), fetch_all=True
            ) or []
        else:
            entries = self._execute(
                "SELECT drs_level, queue_type, joined_at FROM queue_entries WHERE discord_id = ?",
                (discord_id,), fetch_all=True
            ) or []

        for e in entries:
            self.log_queue_wait(discord_id, e.get("queue_type", "DRS"), e["drs_level"], e.get("joined_at"), reason, match_id)

        if queue_type:
            return self._execute("DELETE FROM queue_entries WHERE discord_id = ? AND queue_type = ?", (discord_id, queue_type)) is not None
        return self._execute("DELETE FROM queue_entries WHERE discord_id = ?", (discord_id,)) is not None

    def leave_queue_level(self, discord_id: int, drs_level: int, queue_type: str = None, reason: str = "manual_exit", match_id: int = None) -> bool:
        if queue_type:
            entries = self._execute(
                "SELECT drs_level, queue_type, joined_at FROM queue_entries WHERE discord_id = ? AND drs_level = ? AND queue_type = ?",
                (discord_id, drs_level, queue_type), fetch_all=True
            ) or []
        else:
            entries = self._execute(
                "SELECT drs_level, queue_type, joined_at FROM queue_entries WHERE discord_id = ? AND drs_level = ?",
                (discord_id, drs_level), fetch_all=True
            ) or []

        for e in entries:
            self.log_queue_wait(discord_id, e.get("queue_type", "DRS"), e["drs_level"], e.get("joined_at"), reason, match_id)

        if queue_type:
            return self._execute(
                "DELETE FROM queue_entries WHERE discord_id = ? AND drs_level = ? AND queue_type = ?",
                (discord_id, drs_level, queue_type)
            ) is not None
        return self._execute(
            "DELETE FROM queue_entries WHERE discord_id = ? AND drs_level = ?",
            (discord_id, drs_level)
        ) is not None

    def eject_player_from_all_queues(self, discord_id: int, reason: str = "matched", match_id: int = None) -> bool:
        """Ejects a player from all current incomplete queues and logs wait times."""
        return self.leave_queue(discord_id, reason=reason, match_id=match_id)

    def extend_queue(self, discord_id: int, minutes: int = 30) -> bool:
        if not self.connection:
            return False
        try:
            with self.connection:
                cur = self.connection.execute(
                    """UPDATE queue_entries
                       SET expires_at = datetime(
                           CASE WHEN expires_at < datetime('now') THEN datetime('now') ELSE expires_at END,
                           ? || ' minutes'
                       )
                       WHERE discord_id = ?""",
                    (f"+{minutes}", discord_id)
                )
                return cur.rowcount > 0
        except Exception as e:
            self.logger.error(f"extend_queue failed: {e}", exc_info=True)
            return False

    def set_quick_start(self, discord_id: int, drs_level: int, value: bool, queue_type: str = None) -> bool:
        if queue_type:
            return self._execute(
                "UPDATE queue_entries SET quick_start = ? WHERE discord_id = ? AND drs_level = ? AND queue_type = ?",
                (1 if value else 0, discord_id, drs_level, queue_type)
            ) is not None
        return self._execute(
            "UPDATE queue_entries SET quick_start = ? WHERE discord_id = ? AND drs_level = ?",
            (1 if value else 0, discord_id, drs_level)
        ) is not None

    def get_queue_for_level(self, drs_level: int, queue_type: str = "DRS") -> list[dict]:
        rows = self._execute(
            """SELECT qe.discord_id, u.display_name, qe.expires_at, qe.joined_at, qe.quick_start, qe.queue_guild_id, qe.queue_type, u.need_assist
               FROM queue_entries qe JOIN users u ON u.discord_id = qe.discord_id
               WHERE qe.drs_level = ? AND qe.queue_type = ? AND qe.expires_at > datetime('now')
               ORDER BY qe.joined_at ASC""",
            (drs_level, queue_type), fetch_all=True
        )
        if not rows:
            return []
        return [{"discord_id": r["discord_id"], "display_name": r["display_name"],
                 "expires_at": _parse_dt(r["expires_at"]), "joined_at": _parse_dt(r["joined_at"]),
                 "quick_start": bool(r["quick_start"]),
                 "queue_guild_id": r["queue_guild_id"],
                 "queue_type": r.get("queue_type", "DRS"),
                 "need_assist": bool(r.get("need_assist", 0))} for r in rows]

    def get_full_queue(self, queue_type: str = None) -> list[dict]:
        if queue_type:
            rows = self._execute(
                """SELECT qe.discord_id, u.display_name, qe.drs_level, qe.queue_type, qe.expires_at, qe.quick_start, qe.queue_guild_id,
                          u.genesis_level, u.enrich_level, u.modt_level, u.need_assist
                   FROM queue_entries qe JOIN users u ON u.discord_id = qe.discord_id
                   WHERE qe.queue_type = ? AND qe.expires_at > datetime('now')
                   ORDER BY qe.drs_level, qe.joined_at ASC""",
                (queue_type,), fetch_all=True
            )
        else:
            rows = self._execute(
                """SELECT qe.discord_id, u.display_name, qe.drs_level, qe.queue_type, qe.expires_at, qe.quick_start, qe.queue_guild_id,
                          u.genesis_level, u.enrich_level, u.modt_level, u.need_assist
                   FROM queue_entries qe JOIN users u ON u.discord_id = qe.discord_id
                   WHERE qe.expires_at > datetime('now')
                   ORDER BY qe.queue_type DESC, qe.drs_level, qe.joined_at ASC""",
                fetch_all=True
            )
        if not rows:
            return []
        return [{"discord_id": r["discord_id"], "display_name": r["display_name"],
                 "drs_level": r["drs_level"], "queue_type": r.get("queue_type", "DRS"),
                 "expires_at": _parse_dt(r["expires_at"]),
                 "quick_start": bool(r["quick_start"]),
                 "queue_guild_id": r["queue_guild_id"],
                 "genesis_level": r["genesis_level"], "enrich_level": r["enrich_level"],
                 "modt_level": r["modt_level"],
                 "need_assist": bool(r.get("need_assist", 0))} for r in rows]

    def remove_expired_entries(self) -> list[int]:
        if not self.connection:
            return []
        try:
            cur = self.connection.execute(
                "SELECT discord_id, queue_type, drs_level, joined_at FROM queue_entries WHERE expires_at <= datetime('now')"
            )
            expired = [dict(r) for r in cur.fetchall()]
            ids = [r["discord_id"] for r in expired]
            for r in expired:
                self.log_queue_wait(r["discord_id"], r.get("queue_type", "DRS"), r["drs_level"], r.get("joined_at"), "expired")
            if ids:
                self.connection.execute(
                    "DELETE FROM queue_entries WHERE expires_at <= datetime('now')"
                )
                self.connection.commit()
            return ids
        except Exception as e:
            self.logger.error(f"remove_expired_entries failed: {e}")
            return []

    def is_user_queued_for_level(self, discord_id: int, drs_level: int, queue_type: str = None) -> bool:
        if queue_type:
            row = self._execute(
                """SELECT 1 FROM queue_entries
                   WHERE discord_id = ? AND drs_level = ? AND queue_type = ? AND expires_at > datetime('now')""",
                (discord_id, drs_level, queue_type), fetch_one=True
            )
        else:
            row = self._execute(
                """SELECT 1 FROM queue_entries
                   WHERE discord_id = ? AND drs_level = ? AND expires_at > datetime('now')""",
                (discord_id, drs_level), fetch_one=True
            )
        return row is not None

    def get_user_queue_levels(self, discord_id: int) -> list[dict]:
        rows = self._execute(
            "SELECT drs_level, queue_type FROM queue_entries WHERE discord_id = ? AND expires_at > datetime('now')",
            (discord_id,), fetch_all=True
        )
        return [{"drs_level": r["drs_level"], "queue_type": r.get("queue_type", "DRS")} for r in rows] if rows else []

    def create_match(self, drs_level: int, participant_ids: list[int],
                     queue_guild_map: dict[int, int] | None = None, match_type: str = "DRS") -> int | None:
        """
        Create a match and record participants.
        queue_guild_map: {discord_id: queue_guild_id}
        """
        if not self.connection:
            return None
        try:
            with self.connection:
                cur = self.connection.execute(
                    "INSERT INTO matches (drs_level, match_type) VALUES (?, ?)", (drs_level, match_type)
                )
                match_id = cur.lastrowid
                for uid in participant_ids:
                    guild_id = (queue_guild_map or {}).get(uid)
                    self.connection.execute(
                        """INSERT INTO match_participants (match_id, discord_id, queue_guild_id)
                           VALUES (?, ?, ?)""",
                        (match_id, uid, guild_id)
                    )
            return match_id
        except Exception as e:
            self.logger.error(f"create_match failed: {e}", exc_info=True)
            return None

    def get_match_participants(self, match_id: int) -> list[dict]:
        return self._execute(
            """SELECT mp.discord_id, u.display_name, u.genesis_level, u.enrich_level, u.modt_level,
                      mp.queue_guild_id
               FROM match_participants mp JOIN users u ON u.discord_id = mp.discord_id
               WHERE mp.match_id = ?""",
            (match_id,), fetch_all=True
        ) or []

    def get_participant_queue_guilds(self, participant_ids: list[int]) -> dict[int, int]:
        """
        Returns {discord_id: queue_guild_id} sourced from match_participants.queue_guild_id.
        Falls back to user_servers if not set.
        """
        if not participant_ids:
            return {}
        placeholders = ",".join(["?"] * len(participant_ids))
        rows = self._execute(
            f"""SELECT discord_id, queue_guild_id FROM match_participants
                WHERE discord_id IN ({placeholders}) AND queue_guild_id IS NOT NULL""",
            participant_ids, fetch_all=True
        )
        result = {r["discord_id"]: r["queue_guild_id"] for r in rows} if rows else {}
        # Fill in any missing via user_servers fallback
        for pid in participant_ids:
            if pid not in result:
                guilds = self.get_user_guilds(pid)
                if guilds:
                    result[pid] = guilds[0]
        return result

    def get_user_match_count(self, discord_id: int, drs_level: int) -> int:
        row = self._execute(
            """SELECT COUNT(*) as cnt FROM match_participants mp
               JOIN matches m ON m.id = mp.match_id
               WHERE mp.discord_id = ? AND m.drs_level = ?""",
            (discord_id, drs_level), fetch_one=True
        )
        return row["cnt"] if row else 0

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

    # ------------------------------------------------------------------ feedback

    def save_feedback(self, match_id: int, discord_id: int, was_positive: bool) -> bool:
        return self._execute(
            """INSERT INTO feedback (match_id, discord_id, was_positive) VALUES (?, ?, ?)
               ON CONFLICT(match_id, discord_id) DO NOTHING""",
            (match_id, discord_id, 1 if was_positive else 0)
        ) is not None

    def has_submitted_feedback(self, match_id: int, discord_id: int) -> bool:
        row = self._execute(
            "SELECT 1 FROM feedback WHERE match_id = ? AND discord_id = ?",
            (match_id, discord_id), fetch_one=True
        )
        return row is not None

    def get_match_feedback(self, match_id: int) -> list[dict]:
        return self._execute(
            """SELECT f.discord_id, u.display_name, f.was_positive, f.submitted_at
               FROM feedback f JOIN users u ON u.discord_id = f.discord_id
               WHERE f.match_id = ?""",
            (match_id,), fetch_all=True
        ) or []

    # ------------------------------------------------------------------ feedback_reports

    def save_feedback_report(
        self,
        match_id: int,
        reporter_id: int,
        reported_player_id: int,
        issue_type: str,
        comment: str | None,
        thread_id: int | None,
    ) -> int | None:
        if not self.connection:
            return None
        try:
            with self.connection:
                cur = self.connection.execute(
                    """INSERT INTO feedback_reports
                       (match_id, reporter_id, reported_player_id, issue_type, comment, thread_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (match_id, reporter_id, reported_player_id, issue_type, comment or None, thread_id)
                )
                return cur.lastrowid
        except Exception as e:
            self.logger.error(f"save_feedback_report failed: {e}")
            return None

    def mark_match_feedback_sent(self, match_id: int) -> bool:
        return self._execute(
            "UPDATE matches SET feedback_sent_at = datetime('now') WHERE id = ?",
            (match_id,)
        ) is not None

    def get_pending_feedback_matches(self, delay_minutes: int) -> list[dict]:
        rows = self._execute(
            f"""SELECT id, drs_level, created_at FROM matches
                WHERE feedback_sent_at IS NULL
                AND datetime(created_at, '+{int(delay_minutes)} minutes') <= datetime('now')""",
            fetch_all=True
        )
        return [{"id": r["id"], "drs_level": r["drs_level"], "created_at": r["created_at"]} for r in rows] if rows else []

    def get_feedback_report(self, report_id: int) -> dict | None:
        row = self._execute(
            """SELECT fr.*, ur.display_name AS reporter_name, up.display_name AS reported_name
               FROM feedback_reports fr
               JOIN users ur ON ur.discord_id = fr.reporter_id
               JOIN users up ON up.discord_id = fr.reported_player_id
               WHERE fr.id = ?""",
            (report_id,), fetch_one=True
        )
        return dict(row) if row else None

    def resolve_feedback_report(self, report_id: int, resolved_by: int, resolution_notes: str = "") -> bool:
        return self._execute(
            """UPDATE feedback_reports
               SET resolved_at = datetime('now'), resolved_by = ?, resolution_notes = ?
               WHERE id = ?""",
            (resolved_by, resolution_notes, report_id)
        ) is not None

    # ------------------------------------------------------------------ report_threads

    def save_report_thread(self, report_id: int, match_id: int, guild_id: int, channel_id: int, thread_id: int) -> bool:
        return self._execute(
            """INSERT INTO report_threads (report_id, match_id, guild_id, channel_id, thread_id)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(report_id, guild_id) DO UPDATE SET thread_id = excluded.thread_id, closed_at = NULL""",
            (report_id, match_id, guild_id, channel_id, thread_id)
        ) is not None

    def get_report_threads(self, report_id: int) -> list[dict]:
        return self._execute(
            "SELECT guild_id, channel_id, thread_id, closed_at FROM report_threads WHERE report_id = ?",
            (report_id,), fetch_all=True
        ) or []

    def get_all_active_report_threads(self) -> list[dict]:
        return self._execute(
            "SELECT report_id, guild_id, thread_id FROM report_threads WHERE closed_at IS NULL",
            fetch_all=True
        ) or []

    def get_report_id_by_thread(self, thread_id: int) -> int | None:
        row = self._execute(
            "SELECT report_id FROM report_threads WHERE thread_id = ? AND closed_at IS NULL",
            (thread_id,), fetch_one=True
        )
        return row["report_id"] if row else None

    def close_report_threads(self, report_id: int) -> bool:
        return self._execute(
            "UPDATE report_threads SET closed_at = datetime('now') WHERE report_id = ?",
            (report_id,)
        ) is not None

    def get_feedback_reports_for_match(self, match_id: int) -> list[dict]:
        return self._execute(
            """SELECT fr.id, fr.issue_type, fr.comment, fr.thread_id, fr.created_at,
                      ur.display_name AS reporter_name,
                      up.display_name AS reported_name,
                      fr.reporter_id, fr.reported_player_id
               FROM feedback_reports fr
               JOIN users ur ON ur.discord_id = fr.reporter_id
               JOIN users up ON up.discord_id = fr.reported_player_id
               WHERE fr.match_id = ?
               ORDER BY fr.created_at ASC""",
            (match_id,), fetch_all=True
        ) or []

    # ------------------------------------------------------------------ corp_bonuses

    def upsert_corp_bonus(self, guild_id: int, corp_name: str, bonus_pct: int,
                          expires_at: datetime) -> bool:
        """Insert or replace the bonus for a guild (one bonus per guild)."""
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
        return self._execute(
            """INSERT INTO corp_bonuses (guild_id, corp_name, bonus_pct, expires_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(guild_id) DO UPDATE SET
                 corp_name  = excluded.corp_name,
                 bonus_pct  = excluded.bonus_pct,
                 expires_at = excluded.expires_at,
                 created_at = datetime('now')""",
            (guild_id, corp_name, bonus_pct, expires_str)
        ) is not None

    def get_active_corp_bonuses(self) -> list[dict]:
        """All bonuses that have not yet expired, ordered by bonus_pct descending."""
        rows = self._execute(
            """SELECT cb.guild_id, cb.corp_name, cb.bonus_pct, cb.expires_at
               FROM corp_bonuses cb
               WHERE cb.expires_at > datetime('now')
               ORDER BY cb.bonus_pct DESC""",
            fetch_all=True
        ) or []
        return [
            {
                "guild_id":  r["guild_id"],
                "corp_name": r["corp_name"],
                "bonus_pct": r["bonus_pct"],
                "expires_at": _parse_dt(r["expires_at"]),
            }
            for r in rows
        ]

    def get_all_corp_bonuses(self) -> list[dict]:
        """All bonuses including expired ones — for the /officer bonus list command."""
        rows = self._execute(
            """SELECT guild_id, corp_name, bonus_pct, expires_at
               FROM corp_bonuses
               ORDER BY bonus_pct DESC""",
            fetch_all=True
        ) or []
        return [
            {
                "guild_id":  r["guild_id"],
                "corp_name": r["corp_name"],
                "bonus_pct": r["bonus_pct"],
                "expires_at": _parse_dt(r["expires_at"]),
            }
            for r in rows
        ]
        # ------------------------------------------------------------------ tracked_corps (auto-fetch bonus system)

    def add_tracked_corp(self, corp_id: str, corp_name: str, bonus_pct: int = None) -> bool:
        """Add a corporation to track for auto-fetch bonuses."""
        return self._execute(
            """INSERT OR REPLACE INTO tracked_corps (corp_id, corp_name, bonus_pct, last_fetched, is_active)
               VALUES (?, ?, ?, datetime('now'), 1)""",
            (corp_id, corp_name, bonus_pct)
        ) is not None

    def remove_tracked_corp(self, corp_id: str) -> bool:
        """Soft delete a tracked corporation."""
        return self._execute(
            "UPDATE tracked_corps SET is_active = 0 WHERE corp_id = ?",
            (corp_id,)
        ) is not None

    def get_tracked_corps(self, active_only: bool = True) -> list[dict]:
        """Get all tracked corporations."""
        query = """SELECT corp_id, corp_name, bonus_pct, last_fetched, fetch_error
                   FROM tracked_corps
                   WHERE is_active = 1"""
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY bonus_pct DESC NULLS LAST"
        return self._execute(query, fetch_all=True) or []

    def get_active_corps_with_bonus(self) -> list[dict]:
        """Get active corps with valid bonuses, sorted by bonus descending."""
        return self._execute(
            """SELECT corp_id, corp_name, bonus_pct, last_fetched
               FROM tracked_corps
               WHERE is_active = 1 AND bonus_pct IS NOT NULL
               ORDER BY bonus_pct DESC""",
            fetch_all=True
        ) or []

    def update_corp_bonus(self, corp_id: str, bonus_pct: int) -> bool:
        """Update bonus percentage for a corporation."""
        return self._execute(
            """UPDATE tracked_corps
               SET bonus_pct = ?, last_fetched = datetime('now'), fetch_error = NULL
               WHERE corp_id = ?""",
            (bonus_pct, corp_id)
        ) is not None

    def set_corp_fetch_error(self, corp_id: str, error: str) -> bool:
        """Record an error when fetching bonus fails."""
        return self._execute(
            """UPDATE tracked_corps
               SET fetch_error = ?, last_fetched = datetime('now')
               WHERE corp_id = ?""",
            (error, corp_id)
        ) is not None

    def get_all_active_corp_ids(self) -> list[str]:
        """Get all active corporation IDs."""
        rows = self._execute(
            "SELECT corp_id FROM tracked_corps WHERE is_active = 1",
            fetch_all=True
        )
        return [r["corp_id"] for r in rows] if rows else []

    # ------------------------------------------------------------------ engagement facts & stats

    def get_fact_frequency(self, guild_id: int) -> int:
        server = self.get_server(guild_id)
        if not server or server.get("fact_frequency_hours") is None:
            return 4
        return server["fact_frequency_hours"]

    def set_fact_frequency(self, guild_id: int, hours: int) -> bool:
        return self._execute(
            "UPDATE servers SET fact_frequency_hours = ? WHERE guild_id = ?",
            (max(1, hours), guild_id)
        ) is not None

    def update_last_fact_sent(self, guild_id: int) -> bool:
        return self._execute(
            "UPDATE servers SET last_fact_sent = datetime('now') WHERE guild_id = ?",
            (guild_id,)
        ) is not None

    def get_top_dr_runners(self, limit: int = 5) -> list[dict]:
        rows = self._execute(
            """SELECT u.discord_id, u.display_name, COUNT(mp.match_id) AS run_count
               FROM match_participants mp
               JOIN users u ON u.discord_id = mp.discord_id
               GROUP BY u.discord_id
               ORDER BY run_count DESC
               LIMIT ?""",
            (limit,), fetch_all=True
        ) or []
        return [dict(r) for r in rows]

    def get_top_corps(self, limit: int = 5) -> list[dict]:
        rows = self._execute(
            """SELECT mp.queue_guild_id, COUNT(DISTINCT mp.match_id) AS total_runs
               FROM match_participants mp
               WHERE mp.queue_guild_id IS NOT NULL
               GROUP BY mp.queue_guild_id
               ORDER BY total_runs DESC
               LIMIT ?""",
            (limit,), fetch_all=True
        ) or []
        return [dict(r) for r in rows]

    def get_runs_summary_stats(self) -> dict:
        row_total = self._execute("SELECT COUNT(*) as cnt FROM matches", fetch_one=True)
        row_today = self._execute("SELECT COUNT(*) as cnt FROM matches WHERE created_at >= datetime('now', '-1 day')", fetch_one=True)
        row_week = self._execute("SELECT COUNT(*) as cnt FROM matches WHERE created_at >= datetime('now', '-7 days')", fetch_one=True)
        row_corps = self._execute("SELECT COUNT(*) as cnt FROM servers", fetch_one=True)
        return {
            "total_matches": row_total["cnt"] if row_total else 0,
            "today_matches": row_today["cnt"] if row_today else 0,
            "week_matches": row_week["cnt"] if row_week else 0,
            "total_corps": row_corps["cnt"] if row_corps else 0,
        }

    def get_drs_level_distribution_stats(self) -> list[dict]:
        rows = self._execute(
            """SELECT drs_level, COUNT(*) as cnt
               FROM matches
               GROUP BY drs_level
               ORDER BY cnt DESC""",
            fetch_all=True
        ) or []
        return [dict(r) for r in rows]

    def get_quickstart_vs_standard_stats(self) -> dict:
        row_qs = self._execute(
            f"""SELECT COUNT(*) as cnt FROM (
                   SELECT match_id, COUNT(discord_id) as p_cnt
                   FROM match_participants
                   GROUP BY match_id
                   HAVING p_cnt < ?
               )""",
            (config.MATCH_SIZE,), fetch_one=True
        )
        row_total = self._execute("SELECT COUNT(*) as cnt FROM matches", fetch_one=True)
        total = row_total["cnt"] if row_total else 0
        qs = row_qs["cnt"] if row_qs else 0
        return {"total": total, "quickstarts": qs, "standard": max(0, total - qs)}

    def get_feedback_morale_stats(self) -> dict:
        row_pos = self._execute("SELECT COUNT(*) as cnt FROM feedback WHERE was_positive = 1", fetch_one=True)
        row_all = self._execute("SELECT COUNT(*) as cnt FROM feedback", fetch_one=True)
        total = row_all["cnt"] if row_all else 0
        pos = row_pos["cnt"] if row_pos else 0
        pct = round((pos / total * 100), 1) if total > 0 else 100.0
        return {"positive": pos, "total": total, "percentage": pct}





