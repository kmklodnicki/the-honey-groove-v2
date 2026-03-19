"""Spotify deep-linking — resolve Discogs releases to Spotify album URLs."""
import os
import time
import re
import urllib.parse
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
import requests
from database import db, get_discogs_release, logger, get_current_user

router = APIRouter(prefix="/spotify", tags=["spotify"])

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

# In-memory token cache
_token_cache: Dict = {"token": None, "expires_at": 0}


def _get_spotify_token() -> Optional[str]:
    """Get a valid Spotify access token via Client Credentials flow."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["token"]
    try:
        resp = requests.post(SPOTIFY_TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            _token_cache["token"] = data["access_token"]
            _token_cache["expires_at"] = now + data.get("expires_in", 3600)
            return _token_cache["token"]
        logger.warning(f"Spotify token request failed: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Spotify token error: {e}")
    return None


def _search_spotify(query: str, token: str) -> Optional[Dict]:
    """Search Spotify for an album, return first match or None."""
    try:
        resp = requests.get(SPOTIFY_SEARCH_URL, params={
            "q": query, "type": "album", "limit": 1,
        }, headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if resp.status_code == 200:
            items = resp.json().get("albums", {}).get("items", [])
            if items:
                album = items[0]
                return {
                    "spotify_id": album["id"],
                    "spotify_url": album["external_urls"].get("spotify"),
                    "spotify_uri": album["uri"],
                    "name": album["name"],
                    "artist": ", ".join(a["name"] for a in album.get("artists", [])),
                }
    except Exception as e:
        logger.warning(f"Spotify search error: {e}")
    return None


def _clean_title(title: str) -> str:
    """Strip common suffixes that hurt Spotify matching."""
    title = re.sub(r"\s*\(.*?(Edition|Version|Deluxe|Remaster|Reissue|Anniversary|Pressing).*?\)", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\[.*?\]", "", title)
    return title.strip()


async def resolve_spotify_link(discogs_id: int) -> Dict:
    """Resolve a Discogs release to a Spotify link. Uses DB cache."""
    # Check cache
    cached = await db.spotify_links.find_one({"discogs_id": discogs_id}, {"_id": 0})
    if cached:
        return cached

    # Get Discogs release data
    discogs = get_discogs_release(discogs_id)
    if not discogs:
        return await _fallback(discogs_id, None, None, persist=True)

    artist = discogs.get("artist", "")
    title = discogs.get("title", "")
    barcode = None
    for identifier in discogs.get("identifiers", []):
        if identifier.get("type") == "Barcode":
            barcode = re.sub(r"[^0-9]", "", identifier.get("value", ""))
            if barcode and len(barcode) >= 10:
                break
            barcode = None

    token = _get_spotify_token()
    if not token:
        return await _fallback(discogs_id, artist, title, persist=True)

    result = None

    # Strategy 1: UPC barcode search
    if barcode:
        result = _search_spotify(f"upc:{barcode}", token)

    # Strategy 2: Structured artist + album search
    if not result and artist and title:
        clean = _clean_title(title)
        result = _search_spotify(f"artist:{artist} album:{clean}", token)

    # Strategy 3: Simpler combined search
    if not result and artist and title:
        result = _search_spotify(f"{artist} {_clean_title(title)}", token)

    if result:
        doc = {
            "discogs_id": discogs_id,
            "spotify_id": result["spotify_id"],
            "spotify_url": result["spotify_url"],
            "spotify_uri": result["spotify_uri"],
            "matched": True,
            "artist": artist,
            "title": title,
        }
        await db.spotify_links.update_one(
            {"discogs_id": discogs_id}, {"$set": doc}, upsert=True
        )
        return doc

    return await _fallback(discogs_id, artist, title, persist=True)


async def _fallback(discogs_id: int, artist: str, title: str, persist: bool = False) -> Dict:
    """Generate a generic Spotify search URL as fallback."""
    search_term = f"{artist or ''} {title or ''}".strip()
    fallback_url = f"https://open.spotify.com/search/{urllib.parse.quote(search_term)}" if search_term else "https://open.spotify.com"
    doc = {
        "discogs_id": discogs_id,
        "spotify_url": fallback_url,
        "spotify_id": None,
        "spotify_uri": None,
        "matched": False,
        "artist": artist or "",
        "title": title or "",
    }
    if persist:
        await db.spotify_links.update_one(
            {"discogs_id": discogs_id}, {"$set": doc}, upsert=True
        )
    return doc


@router.get("/link/{discogs_id}")
async def get_spotify_link(discogs_id: int, user: Dict = Depends(get_current_user)):
    """Get the Spotify link for a Discogs release.
    Checks releases collection first (new pipeline), falls back to spotify_links cache."""
    # Check releases collection (new Spotify matching pipeline)
    release = await db.releases.find_one(
        {"discogsReleaseId": discogs_id, "spotifyMatchStatus": "matched"},
        {"_id": 0, "spotifyAlbumId": 1}
    )
    if release and release.get("spotifyAlbumId"):
        album_id = release["spotifyAlbumId"]
        return {
            "discogs_id": discogs_id,
            "spotify_id": album_id,
            "spotify_url": f"https://open.spotify.com/album/{album_id}",
            "spotify_uri": f"spotify:album:{album_id}",
            "matched": True,
        }
    return await resolve_spotify_link(discogs_id)


@router.delete("/link/{discogs_id}/cache")
async def clear_spotify_cache(discogs_id: int, user: Dict = Depends(get_current_user)):
    """Clear cached Spotify link to force re-resolution."""
    await db.spotify_links.delete_one({"discogs_id": discogs_id})
    return await resolve_spotify_link(discogs_id)
