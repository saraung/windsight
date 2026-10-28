"""Pytest configuration.

Environment variables are set here so they are in place before any test
imports ``app.config`` (which instantiates ``Settings`` at import time).
"""

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("ELEXON_BASE_URL", "http://127.0.0.1:9999")
