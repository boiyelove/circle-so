"""Tests for DB connection and migrations."""
import sqlite3
from circle_so.db.connection import get_connection, MIGRATIONS


class TestMigrations:
    def test_creates_tables(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = get_connection(db_path)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "spaces" in tables
        assert "members" in tables
        assert "moderators" in tables
        assert "moves" in tables
        assert "cache" in tables
        assert "schema_version" in tables
        conn.close()

    def test_migration_is_idempotent(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn1 = get_connection(db_path)
        conn1.close()
        conn2 = get_connection(db_path)
        version = conn2.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        assert version == len(MIGRATIONS) - 1
        conn2.close()

    def test_schema_version_tracks(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = get_connection(db_path)
        version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        assert version >= 0
        conn.close()
