"""Spotify album matching service. Operates at the `releases` collection level,
finding Spotify album art (legally permitted for commercial use) for each release."""
import os
import re
import time
import asyncio
import logging
from typing import Optional
import requests

from database import db, logger

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

# In-memory token cache shared across the module
_token_cache = {"token": None, "expires_at": 0}


async def get_spotify_token() -> Optional[str]:
    """Client credentials flow. Caches token and refreshes before 1-hour expiry."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["token"]
    try:
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.post(SPOTIFY_TOKEN_URL, data={
                "grant_type": "client_credentials",
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            }, timeout=10)
        )
        if resp.status_code == 200:
            data = resp.json()
            _token_cache["token"] = data["access_token"]
            _token_cache["expires_at"] = now + data.get("expires_in", 3600)
            return _token_cache["token"]
        logger.warning(f"Spotify token request failed: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Spotify token error: {e}")
    return None


def _clean_title(title: str) -> str:
    """Strip common suffixes that hurt Spotify matching."""
    title = re.sub(r"\s*\(.*?(Edition|Version|Deluxe|Remaster|Reissue|Anniversary|Pressing).*?\)", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\[.*?\]", "", title)
    return title.strip()


def _search_spotify_sync(query: str, token: str, limit: int = 5) -> list:
    """Search Spotify for albums, return list of album dicts."""
    try:
        resp = requests.get(SPOTIFY_SEARCH_URL, params={
            "q": query, "type": "album", "limit": limit,
        }, headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("albums", {}).get("items", [])
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 30))
            raise Exception(f"RATE_LIMITED:{retry_after}")
    except Exception:
        raise
    return []


def find_best_match(spotify_results: list, release: dict) -> Optional[dict]:
    """Score candidates by year match (±1yr) and track count. Return highest scorer."""
    release_year = release.get("year")
    release_tracks = len(release.get("tracklist", []))

    best = None
    best_score = -1

    for album in spotify_results:
        score = 0
        # Year match
        album_year_str = (album.get("release_date") or "")[:4]
        if release_year and album_year_str.isdigit():
            year_diff = abs(int(album_year_str) - int(release_year))
            if year_diff == 0:
                score += 3
            elif year_diff <= 1:
                score += 1
        # Track count match
        album_tracks = album.get("total_tracks", 0)
        if release_tracks and album_tracks:
            if release_tracks == album_tracks:
                score += 2
            elif abs(release_tracks - album_tracks) <= 2:
                score += 1
        if score > best_score:
            best_score = score
            best = album

    return best


async def save_spotify_match(release: dict, album: dict, match_type: str) -> None:
    """Persist Spotify image URLs and match metadata to releases collection."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    images = album.get("images", [])
    image_url = images[0]["url"] if images else None
    image_small = images[1]["url"] if len(images) > 1 else image_url

    await db.releases.update_one(
        {"discogsReleaseId": release["discogsReleaseId"]},
        {"$set": {
            "spotifyAlbumId": album["id"],
            "spotifyImageUrl": image_url,
            "spotifyImageSmall": image_small,
            "spotifyMatchType": match_type,
            "spotifyMatchStatus": "matched",
            "spotifyMatchedAt": now,
        }}
    )


async def _run_spotify_strategies(release: dict, token: str) -> tuple:
    """Execute 3-strategy Spotify search. Returns (matched_album, match_type)."""
    title = release.get("title", "")
    artists = release.get("artists", [])
    artist = artists[0] if artists else ""
    barcodes = release.get("barcode", [])
    clean = _clean_title(title)

    matched_album = None
    match_type = None

    # Strategy 1: UPC barcode
    for barcode in barcodes:
        digits = re.sub(r"[^0-9]", "", barcode)
        if len(digits) >= 10:
            results = await asyncio.get_event_loop().run_in_executor(
                None, _search_spotify_sync, f"upc:{digits}", token, 5
            )
            if results:
                matched_album = find_best_match(results, release)
                match_type = "upc"
                break

    # Strategy 2: Artist + album title
    if not matched_album and artist and title:
        results = await asyncio.get_event_loop().run_in_executor(
            None, _search_spotify_sync, f"artist:{artist} album:{clean}", token, 5
        )
        if results:
            matched_album = find_best_match(results, release)
            match_type = "artist_album"

    # Strategy 3: Simple combined search
    if not matched_album and artist and title:
        results = await asyncio.get_event_loop().run_in_executor(
            None, _search_spotify_sync, f"{artist} {clean}", token, 5
        )
        if results:
            matched_album = find_best_match(results, release)
            match_type = "simple"

    return matched_album, match_type


async def match_to_spotify(release: dict) -> None:
    """3-strategy Spotify matching. Updates releases collection in-place.
    Retries up to 2 times on 429, respecting Retry-After header."""
    if not release or not release.get("discogsReleaseId"):
        return

    token = await get_spotify_token()
    if not token:
        logger.warning("Spotify token unavailable; skipping match")
        return

    discogs_id = release["discogsReleaseId"]
    matched_album = None
    match_type = None

    for attempt in range(3):
        try:
            matched_album, match_type = await _run_spotify_strategies(release, token)
            break  # success — exit retry loop
        except Exception as e:
            if "RATE_LIMITED" in str(e):
                # Parse Retry-After from exception (format: "RATE_LIMITED:{seconds}")
                try:
                    retry_after = int(str(e).split(":")[1])
                except (IndexError, ValueError):
                    retry_after = 30
                if attempt < 2:
                    logger.warning(
                        f"Spotify rate limited for release {discogs_id} "
                        f"(attempt {attempt + 1}/3), retrying in {retry_after}s"
                    )
                    await asyncio.sleep(retry_after)
                    token = await get_spotify_token()  # refresh token after wait
                else:
                    logger.warning(
                        f"Spotify rate limited for release {discogs_id} after 3 attempts; "
                        f"will retry on next batch run"
                    )
                    return  # leave spotifyMatchStatus as "pending" for retry
            else:
                logger.warning(f"Spotify match error for release {discogs_id}: {e}")
                return

    if matched_album:
        await save_spotify_match(release, matched_album, match_type)
    else:
        await db.releases.update_one(
            {"discogsReleaseId": discogs_id},
            {"$set": {"spotifyMatchStatus": "unmatched"}}
        )


async def batch_match_releases(stop_event: asyncio.Event) -> dict:
    """Process all pending releases in batches of 5 with 3-sec delay between batches.
    Respects 429 rate limits and the stop_event signal."""
    processed = matched = unmatched = rate_limited = 0
    batch_size = 5
    delay = 3.0

    cursor = db.releases.find({"spotifyMatchStatus": "pending"}, {"_id": 0})
    batch = []

    async for release in cursor:
        if stop_event.is_set():
            break
        batch.append(release)
        if len(batch) >= batch_size:
            for r in batch:
                if stop_event.is_set():
                    break
                await match_to_spotify(r)
                processed += 1
                updated = await db.releases.find_one(
                    {"discogsReleaseId": r["discogsReleaseId"]}, {"_id": 0, "spotifyMatchStatus": 1}
                )
                status = updated.get("spotifyMatchStatus") if updated else None
                if status == "matched":
                    matched += 1
                elif status == "pending":
                    rate_limited += 1  # still pending = rate limited, will retry next run
                else:
                    unmatched += 1

            batch = []
            if not stop_event.is_set():
                await asyncio.sleep(delay)

    # Process remaining
    for r in batch:
        if stop_event.is_set():
            break
        await match_to_spotify(r)
        processed += 1
        updated = await db.releases.find_one(
            {"discogsReleaseId": r["discogsReleaseId"]}, {"_id": 0, "spotifyMatchStatus": 1}
        )
        status = updated.get("spotifyMatchStatus") if updated else None
        if status == "matched":
            matched += 1
        elif status == "pending":
            rate_limited += 1
        else:
            unmatched += 1

    return {"processed": processed, "matched": matched, "unmatched": unmatched, "rate_limited": rate_limited}
