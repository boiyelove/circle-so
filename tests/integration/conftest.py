"""Integration test fixtures -- skip if CIRCLE_API_TOKEN isn't set.
Excluded from CI via `pytest tests/ --ignore=tests/integration`, same as
circle-so-python-sdk. Run locally with: pytest tests/integration/ -m integration
"""
import os
import pytest

CIRCLE_API_TOKEN = os.environ.get("CIRCLE_API_TOKEN")

requires_circle = pytest.mark.skipif(
    not CIRCLE_API_TOKEN, reason="CIRCLE_API_TOKEN env var not set"
)
