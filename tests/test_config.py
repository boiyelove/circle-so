"""Tests for config."""
import os
from circle_so.config import Config


class TestConfig:
    def test_defaults(self, monkeypatch):
        monkeypatch.setenv("CIRCLE_API_TOKEN", "tok123")
        c = Config()
        assert c.api_token == "tok123"
        assert c.rate_limit == 5
        assert c.cache_ttl == 3600

    def test_overrides(self):
        c = Config(api_token="override", rate_limit=20, db_path="/tmp/test.db")
        assert c.api_token == "override"
        assert c.rate_limit == 20
        assert c.db_path == "/tmp/test.db"

    def test_env_vars(self, monkeypatch):
        monkeypatch.setenv("CIRCLE_API_TOKEN", "env_tok")
        monkeypatch.setenv("CIRCLE_SO_RATE_LIMIT", "15")
        monkeypatch.setenv("CIRCLE_SO_CACHE_TTL", "7200")
        c = Config()
        assert c.api_token == "env_tok"
        assert c.rate_limit == 15
        assert c.cache_ttl == 7200
