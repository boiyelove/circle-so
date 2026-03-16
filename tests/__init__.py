"""Test fixtures."""
import os
import pytest
import sqlite3
from click.testing import CliRunner
from circle_so.cli import main
from circle_so.config import Config
from circle_so.db.connection import get_connection


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    yield db_path, conn
    conn.close()


@pytest.fixture(autouse=True)
def env_setup(tmp_path, monkeypatch):
    monkeypatch.setenv("CIRCLE_API_TOKEN", "test_token")
    monkeypatch.setenv("CIRCLE_SO_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("CIRCLE_SO_DATA_DIR", str(tmp_path))
