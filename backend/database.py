import os
import json
import sqlite3
import datetime
from pathlib import Path
from contextlib import contextmanager

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None

class Database:
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///bgo_dev.db")
        self.is_mysql = self.db_url.startswith("mysql:") or self.db_url.startswith("mysql+pymysql:")
        self.base_dir = Path(__file__).resolve().parent.parent

    def init_app(self, app):
        self.db_url = app.config.get("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL", "sqlite:///bgo_dev.db")
        self.is_mysql = self.db_url.startswith("mysql:") or self.db_url.startswith("mysql+pymysql:")
        self.create_tables()

    def get_connection(self):
        if self.is_mysql:
            url_clean = self.db_url.replace("mysql+pymysql://", "").replace("mysql://", "")
            auth_part, host_db_part = url_clean.split("@")
            user, password = auth_part.split(":") if ":" in auth_part else (auth_part, "")
            host_port, dbname = host_db_part.split("/")
            host, port = host_port.split(":") if ":" in host_port else (host_port, 3306)

            return pymysql.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=dbname,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        else:
            sqlite_path = self.db_url.replace("sqlite:///", "")
            if sqlite_path == ":memory:":
                conn = sqlite3.connect(":memory:", check_same_thread=False)
            else:
                db_file = self.base_dir / sqlite_path if not os.path.isabs(sqlite_path) else Path(sqlite_path)
                conn = sqlite3.connect(str(db_file), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    @contextmanager
    def session(self):
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _format_sql(self, sql: str) -> str:
        """Standardize placeholders: input uses %s, converts to ? for SQLite."""
        if not self.is_mysql:
            return sql.replace("%s", "?")
        return sql

    def execute(self, sql: str, params: tuple = ()) -> int:
        """Executes a query and returns lastrowid for INSERT."""
        with self.session() as conn:
            cursor = conn.cursor()
            formatted_sql = self._format_sql(sql)
            cursor.execute(formatted_sql, params)
            last_id = cursor.lastrowid
            return last_id

    def fetch_one(self, sql: str, params: tuple = ()) -> dict:
        with self.session() as conn:
            cursor = conn.cursor()
            formatted_sql = self._format_sql(sql)
            cursor.execute(formatted_sql, params)
            row = cursor.fetchone()
            if not row:
                return None
            if isinstance(row, sqlite3.Row):
                return dict(row)
            return row

    def fetch_all(self, sql: str, params: tuple = ()) -> list:
        with self.session() as conn:
            cursor = conn.cursor()
            formatted_sql = self._format_sql(sql)
            cursor.execute(formatted_sql, params)
            rows = cursor.fetchall()
            if not rows:
                return []
            if isinstance(rows[0], sqlite3.Row):
                return [dict(r) for r in rows]
            return list(rows)

    def create_all(self):
        self.create_tables()

    def create_tables(self):
        with self.session() as conn:
            cursor = conn.cursor()
            if self.is_mysql:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(12) NOT NULL UNIQUE,
                    game_type VARCHAR(32) NOT NULL DEFAULT 'caro',
                    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
                    max_players INT NOT NULL DEFAULT 2,
                    min_players INT NOT NULL DEFAULT 2,
                    is_local BOOLEAN DEFAULT FALSE,
                    host_token VARCHAR(64),
                    state_version INT DEFAULT 0,
                    game_state_data LONGTEXT,
                    winner_data TEXT,
                    session_scores_data TEXT,
                    rematch_votes_data TEXT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    INDEX idx_rooms_code (code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                try:
                    cursor.execute("ALTER TABLE rooms ADD COLUMN session_scores_data TEXT;")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE rooms ADD COLUMN rematch_votes_data TEXT;")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE rooms ADD COLUMN settings_data TEXT;")
                except Exception:
                    pass

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_players (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    room_id INT NOT NULL,
                    participant_token VARCHAR(64) NOT NULL,
                    player_index INT NOT NULL,
                    name VARCHAR(64) NOT NULL,
                    color VARCHAR(32) NOT NULL,
                    symbol VARCHAR(16) NOT NULL,
                    is_host BOOLEAN DEFAULT FALSE,
                    is_ready BOOLEAN DEFAULT FALSE,
                    is_connected BOOLEAN DEFAULT TRUE,
                    is_spectator BOOLEAN DEFAULT FALSE,
                    socket_id VARCHAR(64),
                    joined_at DATETIME,
                    last_active DATETIME,
                    INDEX idx_rp_room (room_id),
                    INDEX idx_rp_token (participant_token),
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                try:
                    cursor.execute("ALTER TABLE room_players ADD COLUMN is_spectator BOOLEAN DEFAULT FALSE;")
                except Exception:
                    pass

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS match_events (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    room_id INT NOT NULL,
                    sequence_number INT NOT NULL,
                    player_index INT NOT NULL,
                    action_type VARCHAR(64) NOT NULL,
                    payload_data LONGTEXT,
                    created_at DATETIME,
                    INDEX idx_me_room (room_id),
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    room_id INT NOT NULL,
                    player_index INT,
                    sender_name VARCHAR(64) NOT NULL,
                    color VARCHAR(32) NOT NULL,
                    message TEXT NOT NULL,
                    msg_type VARCHAR(16) NOT NULL DEFAULT 'user',
                    sender_role VARCHAR(16) NOT NULL DEFAULT 'player',
                    created_at DATETIME,
                    INDEX idx_rm_room (room_id),
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                try:
                    cursor.execute("ALTER TABLE room_messages ADD COLUMN sender_role VARCHAR(16) DEFAULT 'player';")
                except Exception:
                    pass
            else:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    game_type TEXT NOT NULL DEFAULT 'caro',
                    status TEXT NOT NULL DEFAULT 'waiting',
                    max_players INTEGER NOT NULL DEFAULT 2,
                    min_players INTEGER NOT NULL DEFAULT 2,
                    is_local INTEGER DEFAULT 0,
                    host_token TEXT,
                    state_version INTEGER DEFAULT 0,
                    game_state_data TEXT,
                    winner_data TEXT,
                    session_scores_data TEXT DEFAULT '{}',
                    rematch_votes_data TEXT DEFAULT '[]',
                    created_at TEXT,
                    updated_at TEXT
                );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_rooms_code ON rooms(code);")

                try:
                    cursor.execute("ALTER TABLE rooms ADD COLUMN session_scores_data TEXT DEFAULT '{}';")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE rooms ADD COLUMN rematch_votes_data TEXT DEFAULT '[]';")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE rooms ADD COLUMN settings_data TEXT DEFAULT '{}';")
                except Exception:
                    pass

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL,
                    participant_token TEXT NOT NULL,
                    player_index INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    color TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    is_host INTEGER DEFAULT 0,
                    is_ready INTEGER DEFAULT 0,
                    is_connected INTEGER DEFAULT 1,
                    is_spectator INTEGER DEFAULT 0,
                    socket_id TEXT,
                    joined_at TEXT,
                    last_active TEXT,
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_rp_room ON room_players(room_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_rp_token ON room_players(participant_token);")

                try:
                    cursor.execute("ALTER TABLE room_players ADD COLUMN is_spectator INTEGER DEFAULT 0;")
                except Exception:
                    pass

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS match_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    player_index INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    payload_data TEXT,
                    created_at TEXT,
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_me_room ON match_events(room_id);")

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL,
                    player_index INTEGER,
                    sender_name TEXT NOT NULL,
                    color TEXT NOT NULL,
                    message TEXT NOT NULL,
                    msg_type TEXT NOT NULL DEFAULT 'user',
                    sender_role TEXT NOT NULL DEFAULT 'player',
                    created_at TEXT,
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_rm_room ON room_messages(room_id);")

                try:
                    cursor.execute("ALTER TABLE room_messages ADD COLUMN sender_role TEXT DEFAULT 'player';")
                except Exception:
                    pass

db = Database()
