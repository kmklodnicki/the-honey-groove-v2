"""Image proxy — serves external images with persistent cache + CORS headers."""
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
import httpx
import hashlib
import logging

from database import put_object, get_object, storage_key, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET, DISCOGS_USER_AGENT

router = APIRouter()
logger = logging.getLogger("database")

# In-memory LRU cache for proxied images (max ~200 entries)
_cache = {}
_MAX_CACHE = 200

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
}


@router.options("/image-proxy")
async def proxy_image_options():
    """Explicit CORS pre-flight for strict mobile browsers."""
    return Response(status_code=204, headers=CORS_HEADERS)


def _ext_from_content_type(ct: str) -> str:
    mapping = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
    return mapping.get(ct, ".jpg")


@router.get("/image-proxy")
async def proxy_image(url: str = Query(..., description="External image URL to proxy")):
    """Fetch an external image and serve it with CORS-safe headers.
    Persistent cache: in-memory → Emergent object storage → fetch upstream."""
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Valid http(s) URL required")

    # Force HTTPS
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)

    cache_key = hashlib.md5(url.encode()).hexdigest()
    storage_path = f"honeygroove/image-cache/{cache_key}"

    # 1. Check in-memory cache
    if cache_key in _cache:
        data, content_type = _cache[cache_key]
        return Response(
            content=data,
            media_type=content_type,
            headers={**CORS_HEADERS, "Cache-Control": "public, max-age=604800, stale-while-revalidate=86400", "X-Cache": "HIT-MEM"},
        )

    # 2. Check persistent object storage
    if storage_key:
        try:
            data, content_type = get_object(storage_path)
            if data:
                # Warm the in-memory cache
                if len(_cache) >= _MAX_CACHE:
                    _cache.pop(next(iter(_cache)))
                _cache[cache_key] = (data, content_type)
                return Response(
                    content=data,
                    media_type=content_type,
                    headers={**CORS_HEADERS, "Cache-Control": "public, max-age=604800, stale-while-revalidate=86400", "X-Cache": "HIT-STORE"},
                )
        except Exception:
            pass  # Storage unavailable, fall through to fetch

    # 3. Fetch upstream
    try:
        # Browser-like headers for image CDN requests to avoid hotlink blocking
        fetch_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        # Only add Discogs API auth for API calls, never for CDN image fetches
        if ("api.discogs.com" in url) and DISCOGS_CONSUMER_KEY and DISCOGS_CONSUMER_SECRET:
            fetch_headers["Authorization"] = f"Discogs key={DISCOGS_CONSUMER_KEY}, secret={DISCOGS_CONSUMER_SECRET}"
            fetch_headers["User-Agent"] = DISCOGS_USER_AGENT or fetch_headers["User-Agent"]

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=fetch_headers)
            # Retry with minimal headers if CDN blocks us
            if resp.status_code == 403:
                minimal_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "image/*,*/*;q=0.8",
                }
                resp = await client.get(url, headers=minimal_headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Upstream image fetch failed")
            content_type = resp.headers.get("content-type", "image/jpeg")
            data = resp.content

            # Write to in-memory cache
            if len(_cache) >= _MAX_CACHE:
                _cache.pop(next(iter(_cache)))
            _cache[cache_key] = (data, content_type)

            # Write to persistent storage (fire-and-forget)
            if storage_key:
                try:
                    put_object(storage_path, data, content_type)
                except Exception as e:
                    logger.warning(f"Image proxy: persistent cache write failed: {e}")

            return Response(
                content=data,
                media_type=content_type,
                headers={**CORS_HEADERS, "Cache-Control": "public, max-age=604800, stale-while-revalidate=86400", "X-Cache": "MISS"},
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch image")
