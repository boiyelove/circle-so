"""DB connection and schema migrations."""
import sqlite3

MIGRATIONS = [
    # v1: core tables
    """
    CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
    INSERT OR IGNORE INTO schema_version VALUES (0);
    """,
    # v1: spaces
    """
    CREATE TABLE IF NOT EXISTS spaces (
        id INTEGER PRIMARY KEY,
        plg TEXT UNIQUE,
        space_id INTEGER,
        slug TEXT
    );
    """,
    # v2: members
    """
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        email TEXT UNIQUE,
        country TEXT,
        plg TEXT,
        space_id INTEGER,
        in_community BOOLEAN,
        in_space BOOLEAN,
        community_member_id INTEGER
    );
    """,
    # v3: moderators
    """
    CREATE TABLE IF NOT EXISTS moderators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        name TEXT,
        plg TEXT,
        space_id INTEGER,
        in_space BOOLEAN,
        is_moderator BOOLEAN,
        UNIQUE(email, plg)
    );
    """,
    # v4: moves
    """
    CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        name TEXT,
        community_member_id INTEGER,
        from_space_id INTEGER,
        from_plg TEXT,
        to_space_id INTEGER,
        to_plg TEXT,
        status TEXT DEFAULT 'planned'
    );
    """,
    # v5: cache
    """
    CREATE TABLE IF NOT EXISTS cache (
        key TEXT PRIMARY KEY,
        data TEXT,
        fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS space_members_cache (
        id INTEGER PRIMARY KEY,
        space_id INTEGER,
        email TEXT,
        community_member_id INTEGER,
        moderator BOOLEAN,
        access_type TEXT,
        status TEXT,
        created_at TEXT,
        UNIQUE(space_id, email)
    );
    """,
    # v6: engaged users
    """
    CREATE TABLE IF NOT EXISTS engaged_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        space_id INTEGER,
        community_member_id INTEGER,
        engagement_type TEXT,
        UNIQUE(space_id, community_member_id, engagement_type)
    );
    """,
]


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
    conn.execute("INSERT OR IGNORE INTO schema_version VALUES (0)")
    current = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]

    for i, sql in enumerate(MIGRATIONS):
        if i <= current:
            continue
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_version VALUES (?)", (i,))
        conn.commit()
