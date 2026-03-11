"""Image proxy — serves external images with proper CORS headers for canvas export."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
import httpx
import hashlib

router = APIRouter()

# In-memory LRU cache for proxied images (max ~50 entries)
_cache = {}
_MAX_CACHE = 50


@router.get("/image-proxy")
async def proxy_image(url: str = Query(..., description="External image URL to proxy")):
    """Fetch an external image and serve it with CORS-safe headers."""
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Valid http(s) URL required")

    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in _cache:
        data, content_type = _cache[cache_key]
        return Response(
            content=data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*",
            },
        )

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "HoneyGroove/1.0"})
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Upstream image fetch failed")
            content_type = resp.headers.get("content-type", "image/jpeg")
            data = resp.content

            # Cache it
            if len(_cache) >= _MAX_CACHE:
                _cache.pop(next(iter(_cache)))
            _cache[cache_key] = (data, content_type)

            return Response(
                content=data,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*",
                },
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch image")
