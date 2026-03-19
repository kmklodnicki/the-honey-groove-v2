"""Single source of truth for album image resolution.
Priority: user_upload → spotify → community → placeholder.
Always call this before returning record data to the frontend."""


def resolve_album_image(record: dict, release: dict) -> dict:
    """Resolve image fields for a record based on priority chain.

    Args:
        record: The record document from MongoDB.
        release: The corresponding releases document, or None.

    Returns a dict with keys: imageUrl, imageSmall, imageSource,
    needsCoverPhoto, hasUserPhoto, spotifyAlbumId, discogsUrl.
    """
    discogs_id = record.get("discogs_id")
    discogs_url = f"https://www.discogs.com/release/{discogs_id}" if discogs_id else None
    spotify_album_id = (release or {}).get("spotifyAlbumId")

    # 1. User-uploaded photo (highest priority)
    if record.get("userPhotoUrl"):
        return {
            "imageUrl": record["userPhotoUrl"],
            "imageSmall": record.get("userPhotoSmall") or record["userPhotoUrl"],
            "imageSource": "user_upload",
            "needsCoverPhoto": False,
            "hasUserPhoto": True,
            "spotifyAlbumId": spotify_album_id,
            "discogsUrl": discogs_url,
        }

    # 2. Spotify CDN art
    if release and release.get("spotifyImageUrl"):
        return {
            "imageUrl": release["spotifyImageUrl"],
            "imageSmall": release.get("spotifyImageSmall") or release["spotifyImageUrl"],
            "imageSource": "spotify",
            "needsCoverPhoto": False,
            "hasUserPhoto": False,
            "spotifyAlbumId": spotify_album_id,
            "discogsUrl": discogs_url,
        }

    # 3. Community-uploaded cover
    if release and release.get("communityCoverUrl"):
        return {
            "imageUrl": release["communityCoverUrl"],
            "imageSmall": release.get("communityCoverSmall") or release["communityCoverUrl"],
            "imageSource": "community",
            "needsCoverPhoto": False,
            "hasUserPhoto": False,
            "spotifyAlbumId": spotify_album_id,
            "discogsUrl": discogs_url,
        }

    # 4. Placeholder — needs a cover photo
    return {
        "imageUrl": None,
        "imageSmall": None,
        "imageSource": "placeholder",
        "needsCoverPhoto": True,
        "hasUserPhoto": False,
        "spotifyAlbumId": spotify_album_id,
        "discogsUrl": discogs_url,
    }
