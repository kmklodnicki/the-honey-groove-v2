"""External price scraper — eBay Sold listings & Google Shopping for records with no Discogs history.
Used as a fallback when Discogs market data returns $0."""
import httpx
import re
import logging
from typing import Optional, Dict, List
from urllib.parse import quote_plus
from datetime import datetime, timezone

logger = logging.getLogger("database")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _extract_prices(text: str) -> List[float]:
    """Pull dollar prices from scraped HTML."""
    matches = re.findall(r'\$(\d{1,5}(?:\.\d{2})?)', text)
    return [float(m) for m in matches if 0.50 < float(m) < 50000]


async def scrape_ebay_sold(artist: str, album: str, catno: str = "") -> Optional[Dict]:
    """Search eBay completed/sold listings for a vinyl record."""
    query_parts = [artist, album, "vinyl"]
    if catno:
        query_parts.append(catno)
    query = quote_plus(" ".join(query_parts))
    url = f"https://www.ebay.com/sch/i.html?_nkw={query}&LH_Sold=1&LH_Complete=1&_sacat=176985"

    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
            })
            if resp.status_code != 200:
                logger.warning(f"eBay scrape: HTTP {resp.status_code} for {artist} - {album}")
                return None

            prices = _extract_prices(resp.text)
            record_prices = [p for p in prices if p >= 5.0]

            if not record_prices:
                return None

            record_prices.sort()
            mid = len(record_prices) // 2
            median = record_prices[mid] if len(record_prices) % 2 else (record_prices[mid - 1] + record_prices[mid]) / 2

            return {
                "source": "eBay Sold",
                "median_value": round(median, 2),
                "low_value": round(min(record_prices), 2),
                "high_value": round(max(record_prices), 2),
                "sample_count": len(record_prices),
            }
    except Exception as e:
        logger.warning(f"eBay scrape error for {artist} - {album}: {e}")
        return None


async def scrape_google_shopping(artist: str, album: str, catno: str = "") -> Optional[Dict]:
    """Search Google Shopping for current retail listings of a vinyl record."""
    query_parts = [artist, album, "vinyl record price"]
    if catno:
        query_parts.append(catno)
    query = quote_plus(" ".join(query_parts))
    # Use regular Google search (Shopping tab requires JS)
    url = f"https://www.google.com/search?q={query}"

    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
            })
            if resp.status_code != 200:
                return None

            prices = _extract_prices(resp.text)
            record_prices = [p for p in prices if p >= 5.0]

            if not record_prices:
                return None

            record_prices.sort()
            mid = len(record_prices) // 2
            median = record_prices[mid] if len(record_prices) % 2 else (record_prices[mid - 1] + record_prices[mid]) / 2

            return {
                "source": "Google Market",
                "median_value": round(median, 2),
                "low_value": round(min(record_prices), 2),
                "high_value": round(max(record_prices), 2),
                "sample_count": len(record_prices),
            }
    except Exception as e:
        logger.warning(f"Google scrape error for {artist} - {album}: {e}")
        return None


async def hunt_external_price(artist: str, album: str, catno: str = "", db=None) -> Optional[Dict]:
    """Try eBay first, then Google. Returns best result with source attribution.
    Caches results in MongoDB for 7 days to avoid rate limits."""

    # Check cache first (if db provided)
    cache_key = f"{artist}|{album}|{catno}".lower().strip()
    if db:
        cached = await db.price_cache.find_one({"cache_key": cache_key}, {"_id": 0})
        if cached:
            # Cache valid for 7 days
            cached_at = cached.get("cached_at", "")
            try:
                from datetime import timedelta
                if cached_at and datetime.fromisoformat(cached_at) > datetime.now(timezone.utc) - timedelta(days=7):
                    return cached.get("result")
            except (ValueError, TypeError):
                pass

    # Try eBay sold listings
    ebay_result = await scrape_ebay_sold(artist, album, catno)
    if ebay_result and ebay_result["sample_count"] >= 2:
        if db:
            await db.price_cache.update_one(
                {"cache_key": cache_key},
                {"$set": {"cache_key": cache_key, "result": ebay_result, "cached_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
        return ebay_result

    # Try Google
    google_result = await scrape_google_shopping(artist, album, catno)
    if google_result:
        if db:
            await db.price_cache.update_one(
                {"cache_key": cache_key},
                {"$set": {"cache_key": cache_key, "result": google_result, "cached_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
        return google_result

    # If eBay had at least 1 result, use it
    if ebay_result:
        if db:
            await db.price_cache.update_one(
                {"cache_key": cache_key},
                {"$set": {"cache_key": cache_key, "result": ebay_result, "cached_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
        return ebay_result

    return None
