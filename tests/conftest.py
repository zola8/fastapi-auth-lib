# conftest.py — runs before any test imports
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
