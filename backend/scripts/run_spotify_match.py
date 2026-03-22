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


async def validate_spotify_credentials() -> bool:
    """Test Spotify credentials before any batch processing. Exits fast on failure."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET env var is missing.")
        print("Set both vars and re-run. Exiting without processing any records.")
        return False

    import requests
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=10,
    )
    if resp.status_code == 200:
        print(f"Spotify credentials OK (token expires in {resp.json().get('expires_in', '?')}s)")
        return True

    print(f"ERROR: Spotify token request returned {resp.status_code}.")
    if resp.status_code == 400:
        print("  400 = invalid client_id or client_secret.")
        print("  Fix: go to developer.spotify.com → your app → Settings → regenerate secret → update SPOTIFY_CLIENT_SECRET in Vercel env vars.")
    elif resp.status_code == 401:
        print("  401 = unauthorized. Credentials may be revoked or the app deleted.")
    print("Exiting without processing any records.")
    return False


async def main():
    if not await validate_spotify_credentials():
        sys.exit(1)

    pending = await db.releases.count_documents({"spotifyMatchStatus": "pending"})
    print(f"DB: {os.environ['DB_NAME']} | pending releases: {pending}")

    stop_event = asyncio.Event()
    # No run_limit or deadline — processes all pending releases.
    # Run locally (not GitHub Actions) to avoid Spotify IP rate-blocking.
    result = await batch_match_releases(stop_event)
    print(
        f"processed={result['processed']} "
        f"matched={result['matched']} "
        f"unmatched={result['unmatched']} "
        f"rate_limited={result['rate_limited']}"
    )


asyncio.run(main())
