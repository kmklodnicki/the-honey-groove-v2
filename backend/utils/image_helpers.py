"""Utility to rewrite external cover URLs to route through our image proxy.
This ensures images always load in production regardless of CDN hotlink restrictions."""
from urllib.parse import quote


def proxy_cover_url(url):
    """Rewrite a single external cover URL to route through our image proxy."""
    if not url or not isinstance(url, str):
        return url
    if '/api/image-proxy' in url:
        return url
    if url.startswith('http://') or url.startswith('https://'):
        return f"/api/image-proxy?url={quote(url, safe='')}"
    return url


def proxy_records_cover_urls(records):
    """Rewrite cover_url in a list of record dicts."""
    for r in records:
        if r.get("cover_url"):
            r["cover_url"] = proxy_cover_url(r["cover_url"])
    return records
