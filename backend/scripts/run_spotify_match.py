"""Standalone Spotify batch match runner for GitHub Actions.

Mocks the database module so we only need motor + requests installed —
no FastAPI, bcrypt, or other server dependencies required.
"""
import asyncio
import logging
import os
import sys
import types

# ── minimal logging ──────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("spotify_match")

# ── minimal database mock ─────────────────────────────────────────────────────
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    os.environ["MONGO_URL"],
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
)
db = client[os.environ["DB_NAME"]]

db_mock = types.ModuleType("database")
db_mock.db = db
db_mock.logger = logger
sys.modules["database"] = db_mock

# ── now safe to import spotify_service ───────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.spotify_service import batch_match_releases


async def main():
    pending = await db.releases.count_documents({"spotifyMatchStatus": "pending"})
    print(f"DB: {os.environ['DB_NAME']} | pending releases: {pending}")

    stop_event = asyncio.Event()
    result = await batch_match_releases(stop_event, run_limit=5, deadline_secs=780)
    print(
        f"processed={result['processed']} "
        f"matched={result['matched']} "
        f"unmatched={result['unmatched']} "
        f"rate_limited={result['rate_limited']}"
    )


asyncio.run(main())
