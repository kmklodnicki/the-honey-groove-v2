#!/usr/bin/env python3
"""Standalone CC0 backfill script.

Fetches Discogs CC0 metadata for all vault records that don't yet have
a releases document, then queues them for Spotify matching.

Usage:
    cd backend
    MONGO_URL=... DB_NAME=... python3 scripts/run_cc0_backfill.py

Progress is printed live. Safe to re-run — skips releases that already exist.
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN", "")
DISCOGS_USER_AGENT = os.environ.get("DISCOGS_USER_AGENT", "HoneyGroove/1.0")

from motor.motor_asyncio import AsyncIOMotorClient
import requests
from datetime import datetime, timezone

client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=10000)
db = client[DB_NAME]

session = requests.Session()
session.headers.update({"User-Agent": DISCOGS_USER_AGENT})


def fetch_discogs_release(discogs_id: int):
    params = {}
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN
    for attempt in range(5):
        try:
            resp = session.get(
                f"https://api.discogs.com/releases/{discogs_id}",
                params=params, timeout=15
            )
            if resp.status_code == 429:
                wait = min(int(resp.headers.get("Retry-After", 60)), 120)
                print(f"  ⏳ Rate limited — waiting {wait}s (attempt {attempt+1}/5)")
                time.sleep(wait)
                continue
            if resp.status_code != 200:
                return None
            break
        except Exception as e:
            print(f"  ⚠ Discogs error for {discogs_id}: {e}")
            return None
    else:
        print(f"  ✗ Gave up on {discogs_id} after 5 rate-limit retries")
        return None
    try:
        data = resp.json()

        artists = ", ".join(a.get("name", "") for a in data.get("artists", []))
        labels = [l.get("name", "") for l in data.get("labels", [])]
        barcodes = [
            i["value"].strip()
            for i in data.get("identifiers", [])
            if i.get("type") == "Barcode" and i.get("value")
        ]
        tracklist = [
            {"position": t.get("position"), "title": t.get("title"), "duration": t.get("duration")}
            for t in data.get("tracklist", [])
        ]
        formats = [f.get("name", "") for f in data.get("formats", [])]

        return {
            "title": data.get("title"),
            "artist": artists or "Unknown",
            "label": labels,
            "format": formats,
            "tracklist": tracklist,
            "year": data.get("year"),
            "country": data.get("country"),
            "genre": data.get("genres", []),
            "style": data.get("styles", []),
            "barcode": barcodes,
            "notes": data.get("notes"),
        }
    except Exception as e:
        print(f"  ⚠ Discogs error for {discogs_id}: {e}")
        return None


async def upsert_cc0(discogs_id: int, data: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    artists = data.get("artist", "")
    if isinstance(artists, str):
        artists = [a.strip() for a in artists.split(",") if a.strip()]

    doc = {
        "discogsReleaseId": discogs_id,
        "title": data.get("title"),
        "artists": artists,
        "labels": data.get("label", []),
        "formats": data.get("format", []),
        "tracklist": data.get("tracklist", []),
        "year": data.get("year"),
        "country": data.get("country"),
        "genres": data.get("genre", []),
        "styles": data.get("style", []),
        "barcode": data.get("barcode", []),
        "notes": data.get("notes"),
        "discogsUrl": f"https://www.discogs.com/release/{discogs_id}",
        "dataFetchedAt": now,
        "spotifyMatchStatus": "pending",
    }
    await db.releases.update_one(
        {"discogsReleaseId": discogs_id},
        {"$set": doc},
        upsert=True
    )


async def main():
    print("=== THG CC0 Backfill ===\n")

    # Distinct discogs_ids from records
    all_ids = await db.records.distinct("discogs_id", {"discogs_id": {"$ne": None}})
    all_ids = [i for i in all_ids if i]
    print(f"Total distinct discogs IDs in vault: {len(all_ids)}")

    # Already in releases collection
    existing_cursor = db.releases.find({}, {"_id": 0, "discogsReleaseId": 1})
    existing = {r["discogsReleaseId"] async for r in existing_cursor}
    print(f"Already in releases collection:      {len(existing)}")

    missing = [i for i in all_ids if i not in existing]
    print(f"Need to fetch:                       {len(missing)}\n")

    if not missing:
        print("✓ Nothing to do — all releases already populated.")
        return

    fetched = skipped = errors = 0
    start = time.time()

    for idx, discogs_id in enumerate(missing, 1):
        eta_str = ""
        if idx > 1:
            elapsed = time.time() - start
            rate = (idx - 1) / elapsed
            remaining = (len(missing) - idx + 1) / rate
            m, s = divmod(int(remaining), 60)
            eta_str = f"  ETA ~{m}m{s:02d}s"

        print(f"[{idx}/{len(missing)}] {discogs_id}{eta_str}", end="\r", flush=True)

        data = fetch_discogs_release(discogs_id)
        if data:
            await upsert_cc0(discogs_id, data)
            fetched += 1
        else:
            skipped += 1
            errors += 1

        time.sleep(1.05)  # ~1 req/sec, stay under Discogs rate limit

    elapsed_total = time.time() - start
    m, s = divmod(int(elapsed_total), 60)
    print(f"\n\n{'='*40}")
    print(f"✓ Done in {m}m{s:02d}s")
    print(f"  Fetched & saved: {fetched}")
    print(f"  Skipped (errors): {errors}")
    pending = await db.releases.count_documents({"spotifyMatchStatus": "pending"})
    print(f"  Pending Spotify match: {pending}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
