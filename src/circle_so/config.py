"""Configuration management. Reads from env vars, .env file, and CLI flags."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self, **overrides):
        self.api_token = overrides.get("api_token") or os.environ.get("CIRCLE_API_TOKEN")
        self.community_url = overrides.get("community_url") or os.environ.get("CIRCLE_COMMUNITY_URL")
        self.db_path = overrides.get("db_path") or os.environ.get("CIRCLE_SO_DB", "./circle-so.db")
        self.data_dir = overrides.get("data_dir") or os.environ.get("CIRCLE_SO_DATA_DIR", ".")
        self.rate_limit = int(overrides.get("rate_limit") or os.environ.get("CIRCLE_SO_RATE_LIMIT", "5"))
        self.cache_ttl = int(overrides.get("cache_ttl") or os.environ.get("CIRCLE_SO_CACHE_TTL", "3600"))

    def get_client(self):
        from circle import CircleClient
        return CircleClient(
            api_token=self.api_token,
            community_url=self.community_url,
            rate_limit=self.rate_limit,
        )

    def get_db(self):
        from circle_so.db.connection import get_connection
        return get_connection(self.db_path)
