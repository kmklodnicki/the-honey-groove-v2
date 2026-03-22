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

# Per-request rate limiter — enforces a minimum gap between every Spotify API call.
# 5.0s per request = ~12 req/min. Conservative enough to avoid sustained bans.
_MIN_REQUEST_INTERVAL = 5.0  # seconds between individual Spotify search requests
_request_lock = asyncio.Lock()
_last_request_at: float = 0.0


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
            retry_after = int(resp.headers.get("Retry-After", 60))
            # If value looks like milliseconds (>3600), convert to seconds
            if retry_after > 3600:
                retry_after = retry_after // 1000
            # Respect Spotify's window up to 15 minutes; floor at 60s
            retry_after = max(60, min(retry_after, 900))
            raise Exception(f"RATE_LIMITED:{retry_after}")
    except Exception:
        raise
    return []


async def _rate_limited_search(query: str, token: str, limit: int = 5) -> list:
    """Enforce _MIN_REQUEST_INTERVAL between every Spotify API request, then search.

    All search calls funnel through here so the rate limiter is a single choke
    point regardless of how many strategies or barcodes a release has.
    """
    global _last_request_at
    async with _request_lock:
        elapsed = time.monotonic() - _last_request_at
        wait = _MIN_REQUEST_INTERVAL - elapsed
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request_at = time.monotonic()
        return await asyncio.get_event_loop().run_in_executor(
            None, _search_spotify_sync, query, token, limit
        )


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
            results = await _rate_limited_search(f"upc:{digits}", token)
            if results:
                matched_album = find_best_match(results, release)
                match_type = "upc"
                break

    # Strategy 2: Artist + album title
    if not matched_album and artist and title:
        results = await _rate_limited_search(f"artist:{artist} album:{clean}", token)
        if results:
            matched_album = find_best_match(results, release)
            match_type = "artist_album"

    # Strategy 3: Simple combined search
    if not matched_album and artist and title:
        results = await _rate_limited_search(f"{artist} {clean}", token)
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
                        f"cooling down {retry_after}s before next release"
                    )
                    await asyncio.sleep(retry_after)  # respect the window before moving on
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


async def batch_match_releases(
    stop_event: asyncio.Event,
    run_limit: Optional[int] = None,
    deadline_secs: Optional[float] = None,
) -> dict:
    """Process pending releases in batches of 5 with adaptive delay.

    Pre-loads release IDs upfront so the MongoDB cursor closes immediately —
    this avoids the 30-minute cursor timeout that previously capped runs at ~300.
    Fetches the full document for each release at processing time.
    Adapts inter-batch delay upward when 429s are seen, and resets when clear.

    run_limit: if set, stop after processing this many releases. Intended for
    Vercel Cron Job invocations that must complete within maxDuration.
    deadline_secs: if set, stop processing after this many wall-clock seconds
    (checked before each batch). Use this to guarantee the function returns
    well before a hard serverless timeout (e.g. pass 240 for a 5-min limit).
    """
    processed = matched = unmatched = rate_limited = 0
    batch_size = 5
    base_delay = 1.0   # per-request throttle is the primary limiter; batch delay is secondary insurance
    delay = base_delay
    started_at = time.monotonic()

    # Pre-load only IDs — cursor opens and closes in one fast query.
    # Processing can now run for hours without hitting cursor timeout.
    pending_ids = await db.releases.distinct(
        "discogsReleaseId", {"spotifyMatchStatus": "pending"}
    )
    logger.info(f"Spotify batch: {len(pending_ids)} pending releases")

    for i in range(0, len(pending_ids), batch_size):
        if stop_event.is_set():
            break
        if deadline_secs is not None and (time.monotonic() - started_at) >= deadline_secs:
            logger.info(f"Spotify batch: deadline reached after {time.monotonic() - started_at:.1f}s, stopping")
            break

        batch_ids = pending_ids[i:i + batch_size]
        batch_rate_limited = 0

        for discogs_id in batch_ids:
            if stop_event.is_set():
                break
            if run_limit is not None and processed >= run_limit:
                break
            if deadline_secs is not None and (time.monotonic() - started_at) >= deadline_secs:
                break
            # Re-fetch full document — re-checks status so already-processed
            # items (e.g. from a parallel run) are safely skipped.
            release = await db.releases.find_one(
                {"discogsReleaseId": discogs_id, "spotifyMatchStatus": "pending"},
                {"_id": 0},
            )
            if not release:
                continue

            try:
                # 130s allows one full 60s rate-limit sleep + retry overhead
                await asyncio.wait_for(match_to_spotify(release), timeout=130.0)
            except asyncio.TimeoutError:
                logger.warning(f"match_to_spotify timed out for {discogs_id}, pausing 65s for rate limit")
                processed += 1
                rate_limited += 1
                batch_rate_limited += 1
                await asyncio.sleep(65)  # let the Spotify rate limit window expire
                continue
            processed += 1

            updated = await db.releases.find_one(
                {"discogsReleaseId": discogs_id}, {"_id": 0, "spotifyMatchStatus": 1}
            )
            status = updated.get("spotifyMatchStatus") if updated else None
            if status == "matched":
                matched += 1
            elif status == "pending":
                rate_limited += 1
                batch_rate_limited += 1
            else:
                unmatched += 1

            logger.info(f"[{processed}/{len(pending_ids)}] id={discogs_id} → {status}")

        if not stop_event.is_set():
            # Adaptive delay: back off hard when rate-limited, recover slowly when clear.
            # Per-request throttle already spaces calls; this adds extra breathing room.
            if batch_rate_limited > 0:
                delay = min(delay * 3, 120.0)
                logger.info(f"Spotify rate limits in batch; backing off to {delay:.1f}s")
            else:
                delay = max(delay * 0.9, base_delay)
            await asyncio.sleep(delay)

    return {"processed": processed, "matched": matched, "unmatched": unmatched, "rate_limited": rate_limited}
