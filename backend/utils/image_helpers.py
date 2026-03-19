"""Utility to rewrite external cover URLs to route through our image proxy.
This ensures images always load in production regardless of CDN hotlink restrictions."""
from urllib.parse import quote

_DISCOGS_IMAGE_HOSTS = ("i.discogs.com", "st.discogs.com")

IMAGE_FIELDS = ("cover_url", "image_url", "imageUrl", "imageSmall", "thumb_url", "photo_url")


def is_discogs_image_url(url: str) -> bool:
    """Return True if url is a Discogs CDN image (Restricted Data — must not be served)."""
    if not url or not isinstance(url, str):
        return False
    return any(h in url for h in _DISCOGS_IMAGE_HOSTS)


def proxy_cover_url(url):
    """Rewrite a single external cover URL to route through our image proxy.
    Returns None for Discogs CDN URLs — Restricted Data per Discogs TOS."""
    if not url or not isinstance(url, str):
        return url
    if is_discogs_image_url(url):
        return None
    if '/api/image-proxy' in url:
        return url
    if url.startswith('http://') or url.startswith('https://'):
        return f"/api/image-proxy?url={quote(url, safe='')}"
    return url


def proxy_records_cover_urls(records):
    """Rewrite cover_url in a list of record dicts. Strips Discogs CDN URLs."""
    for r in records:
        if r.get("cover_url"):
            r["cover_url"] = proxy_cover_url(r["cover_url"])
    return records


def strip_discogs_image_urls(obj):
    """Recursively null out any Discogs CDN image URLs in a dict or list.
    Safety backstop — call before returning any API response."""
    if isinstance(obj, dict):
        for field in IMAGE_FIELDS:
            if is_discogs_image_url(obj.get(field)):
                obj[field] = None
        for v in obj.values():
            strip_discogs_image_urls(v)
    elif isinstance(obj, list):
        for item in obj:
            strip_discogs_image_urls(item)
    return obj
