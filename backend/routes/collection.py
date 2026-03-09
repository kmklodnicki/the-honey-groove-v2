from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import Response
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import os

from database import db, require_auth, get_current_user, security, logger, create_notification
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, PLATFORM_FEE_PERCENT, FRONTEND_URL
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from database import oauth_request_tokens, import_progress, EMERGENT_KEY, APP_NAME
from models import *
from fastapi import UploadFile, File
from requests_oauthlib import OAuth1Session
import asyncio
import requests

router = APIRouter()

# ============== DISCOGS ROUTES ==============

@router.get("/discogs/search", response_model=List[DiscogsSearchResult])
async def search_records_discogs(q: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    results = search_discogs(q)
    return [DiscogsSearchResult(**r) for r in results]

@router.get("/discogs/release/{release_id}")
async def get_discogs_release_info(release_id: int, user: Dict = Depends(require_auth)):
    result = get_discogs_release(release_id)
    if not result:
        raise HTTPException(status_code=404, detail="Release not found")
    return result


# ============== COLLECTION/RECORDS ROUTES ==============

@router.post("/records", response_model=RecordResponse)
async def add_record(record_data: RecordCreate, user: Dict = Depends(require_auth)):
    record_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    record_doc = {
        "id": record_id,
        "user_id": user["id"],
        "discogs_id": record_data.discogs_id,
        "title": record_data.title,
        "artist": record_data.artist,
        "cover_url": record_data.cover_url,
        "year": record_data.year,
        "format": record_data.format,
        "notes": record_data.notes,
        "color_variant": record_data.color_variant,
        "created_at": now
    }
    
    await db.records.insert_one(record_doc)
    
    # Create activity post
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "ADDED_TO_COLLECTION",
        "caption": f"Added {record_data.title} by {record_data.artist} to their collection",
        "record_id": record_id,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    return RecordResponse(
        id=record_id,
        discogs_id=record_data.discogs_id,
        title=record_data.title,
        artist=record_data.artist,
        cover_url=record_data.cover_url,
        year=record_data.year,
        format=record_data.format,
        notes=record_data.notes,
        color_variant=record_data.color_variant,
        user_id=user["id"],
        created_at=now,
        spin_count=0
    )


@router.get("/records/check-ownership")
async def check_record_ownership(
    discogs_id: Optional[int] = None,
    artist: Optional[str] = None,
    title: Optional[str] = None,
    user: Dict = Depends(require_auth),
):
    """Check if the current user has a record in their collection."""
    if not discogs_id and not (artist and title):
        return {"in_collection": False, "record_id": None}

    query = {"user_id": user["id"]}
    if discogs_id:
        query["discogs_id"] = discogs_id
    else:
        query["artist"] = {"$regex": f"^{artist}$", "$options": "i"}
        query["title"] = {"$regex": f"^{title}$", "$options": "i"}

    record = await db.records.find_one(query, {"_id": 0, "id": 1})
    if record:
        return {"in_collection": True, "record_id": record["id"]}
    return {"in_collection": False, "record_id": None}


@router.get("/records", response_model=List[RecordResponse])
async def get_my_records(user: Dict = Depends(require_auth)):
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$sort": {"created_at": -1}},
        {"$limit": 1000},
        {"$lookup": {
            "from": "spins",
            "localField": "id",
            "foreignField": "record_id",
            "as": "_spins"
        }},
        {"$addFields": {"spin_count": {"$size": "$_spins"}}},
        {"$project": {"_spins": 0, "_id": 0}}
    ]
    records = await db.records.aggregate(pipeline).to_list(1000)
    return [RecordResponse(**r) for r in records]

@router.get("/records/{record_id}", response_model=RecordResponse)
async def get_record(record_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    record = await db.records.find_one({"id": record_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    spin_count = await db.spins.count_documents({"record_id": record_id})
    
    return RecordResponse(**record, spin_count=spin_count)


@router.get("/records/{record_id}/detail")
async def get_record_detail(record_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    """Enriched record detail: community stats, market value, related posts, owners."""
    record = await db.records.find_one({"id": record_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    spin_count = await db.spins.count_documents({"record_id": record_id})

    # Find all copies of this record across the platform (by discogs_id or artist+title)
    sibling_query = {}
    if record.get("discogs_id"):
        sibling_query = {"discogs_id": record["discogs_id"]}
    else:
        sibling_query = {"artist": record["artist"], "title": record["title"]}

    siblings = await db.records.find(sibling_query, {"_id": 0}).to_list(500)
    sibling_ids = [s["id"] for s in siblings]
    owner_ids = list({s["user_id"] for s in siblings})

    # Community stats
    total_owners = len(owner_ids)
    total_community_spins = await db.spins.count_documents({"record_id": {"$in": sibling_ids}})

    # Owners list (up to 12)
    owners = []
    if owner_ids:
        users_list = await db.users.find(
            {"id": {"$in": owner_ids[:12]}},
            {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
        ).to_list(12)
        owners = users_list

    # Related posts (Now Spinning, ADDED_TO_COLLECTION for this record)
    related_posts = await db.posts.find(
        {"record_id": {"$in": sibling_ids}},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)

    # Enrich posts with user info
    post_user_ids = list({p["user_id"] for p in related_posts})
    if post_user_ids:
        ul = await db.users.find(
            {"id": {"$in": post_user_ids}},
            {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
        ).to_list(50)
        users_map = {u["id"]: u for u in ul}
        for p in related_posts:
            p["user"] = users_map.get(p["user_id"])

    # Market value (from cache or Discogs)
    market_value = None
    if record.get("discogs_id"):
        cached = await db.discogs_values.find_one(
            {"discogs_id": record["discogs_id"]}, {"_id": 0}
        )
        if cached:
            market_value = {
                "low": cached.get("low_value"),
                "median": cached.get("median_value"),
                "high": cached.get("high_value"),
                "currency": "USD",
            }

    # ISO/wantlist count (how many people want this)
    wantlist_count = 0
    if record.get("discogs_id"):
        wantlist_count = await db.iso_items.count_documents({
            "$or": [
                {"discogs_id": record["discogs_id"]},
                {"artist": record["artist"], "title": record["title"]},
            ]
        })
    else:
        wantlist_count = await db.iso_items.count_documents({
            "artist": record["artist"], "title": record["title"]
        })

    # Owner info
    owner_user = await db.users.find_one(
        {"id": record["user_id"]},
        {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
    )

    return {
        "record": {**record, "spin_count": spin_count},
        "owner": owner_user,
        "community": {
            "total_owners": total_owners,
            "total_spins": total_community_spins,
            "wantlist_count": wantlist_count,
            "owners": owners,
        },
        "market_value": market_value,
        "related_posts": related_posts,
    }

@router.get("/users/{username}/records", response_model=List[RecordResponse])
async def get_user_records(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Block check
    if current_user and current_user["id"] != user["id"]:
        block = await db.blocks.find_one({"$or": [{"blocker_id": user["id"], "blocked_id": current_user["id"]}, {"blocker_id": current_user["id"], "blocked_id": user["id"]}]})
        if block:
            raise HTTPException(status_code=403, detail="This profile is not available.")
    
    records = await db.records.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    result = []
    for record in records:
        spin_count = await db.spins.count_documents({"record_id": record["id"]})
        result.append(RecordResponse(**record, spin_count=spin_count))
    
    return result

@router.delete("/records/{record_id}")
async def delete_record(record_id: str, user: Dict = Depends(require_auth)):
    record = await db.records.find_one({"id": record_id, "user_id": user["id"]})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    await db.records.delete_one({"id": record_id})
    await db.spins.delete_many({"record_id": record_id})
    await db.posts.delete_many({"record_id": record_id})
    
    return {"message": "Record deleted"}


@router.post("/records/{record_id}/move-to-wishlist")
async def move_to_wishlist(record_id: str, user: Dict = Depends(require_auth)):
    """Move a collection record to the passive wishlist (ISO with WISHLIST status)."""
    record = await db.records.find_one({"id": record_id, "user_id": user["id"]})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    now = datetime.now(timezone.utc).isoformat()
    iso_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "artist": record.get("artist", ""),
        "album": record.get("title", ""),
        "discogs_id": record.get("discogs_id"),
        "cover_url": record.get("cover_url"),
        "year": record.get("year"),
        "status": "WISHLIST",
        "priority": "LOW",
        "created_at": now,
    }
    await db.iso_items.insert_one(iso_doc)
    await db.records.delete_one({"id": record_id})
    await db.spins.delete_many({"record_id": record_id})
    return {"message": f"{record.get('title')} moved to wishlist."}

@router.post("/records/{record_id}/move-to-iso")
async def move_to_iso(record_id: str, user: Dict = Depends(require_auth)):
    """Move a collection record back to the active ISO hunt list."""
    record = await db.records.find_one({"id": record_id, "user_id": user["id"]})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    now = datetime.now(timezone.utc).isoformat()
    iso_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "artist": record.get("artist", ""),
        "album": record.get("title", ""),
        "discogs_id": record.get("discogs_id"),
        "cover_url": record.get("cover_url"),
        "year": record.get("year"),
        "status": "OPEN",
        "priority": "MED",
        "tags": ["Seeking Upgrade"],
        "created_at": now,
    }
    await db.iso_items.insert_one(iso_doc)
    await db.records.delete_one({"id": record_id})
    await db.spins.delete_many({"record_id": record_id})
    return {"message": f"{record.get('title')} is back on the hunt.", "title": record.get("title")}


class BulkMoveRequest(BaseModel):
    record_ids: List[str]


@router.post("/records/bulk-move-to-wishlist")
async def bulk_move_to_wishlist(body: BulkMoveRequest, user: Dict = Depends(require_auth)):
    """Bulk move collection records to the passive wishlist."""
    moved = 0
    for rid in body.record_ids:
        record = await db.records.find_one({"id": rid, "user_id": user["id"]})
        if not record:
            continue
        now = datetime.now(timezone.utc).isoformat()
        await db.iso_items.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "artist": record.get("artist", ""),
            "album": record.get("title", ""),
            "discogs_id": record.get("discogs_id"),
            "cover_url": record.get("cover_url"),
            "year": record.get("year"),
            "status": "WISHLIST",
            "priority": "LOW",
            "created_at": now,
        })
        await db.records.delete_one({"id": rid})
        await db.spins.delete_many({"record_id": rid})
        moved += 1
    return {"message": f"{moved} record{'s' if moved != 1 else ''} moved to Dreaming.", "moved": moved}


@router.post("/records/bulk-move-to-iso")
async def bulk_move_to_iso(body: BulkMoveRequest, user: Dict = Depends(require_auth)):
    """Bulk move collection records to the active hunt list."""
    moved = 0
    for rid in body.record_ids:
        record = await db.records.find_one({"id": rid, "user_id": user["id"]})
        if not record:
            continue
        now = datetime.now(timezone.utc).isoformat()
        await db.iso_items.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "artist": record.get("artist", ""),
            "album": record.get("title", ""),
            "discogs_id": record.get("discogs_id"),
            "cover_url": record.get("cover_url"),
            "year": record.get("year"),
            "status": "OPEN",
            "priority": "MED",
            "tags": ["Seeking Upgrade"],
            "created_at": now,
        })
        await db.records.delete_one({"id": rid})
        await db.spins.delete_many({"record_id": rid})
        moved += 1
    return {"message": f"{moved} record{'s' if moved != 1 else ''} moved to The Hunt.", "moved": moved}



# ============== SPIN ROUTES ==============

@router.post("/spins", response_model=SpinResponse)
async def log_spin(spin_data: SpinCreate, user: Dict = Depends(require_auth)):
    record = await db.records.find_one({"id": spin_data.record_id, "user_id": user["id"]}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found in your collection")
    
    spin_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    spin_doc = {
        "id": spin_id,
        "user_id": user["id"],
        "record_id": spin_data.record_id,
        "notes": spin_data.notes,
        "created_at": now
    }
    
    await db.spins.insert_one(spin_doc)
    
    # Create activity post
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "NOW_SPINNING",
        "caption": f"Spinning {record['title']} by {record['artist']}",
        "record_id": spin_data.record_id,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    return SpinResponse(
        id=spin_id,
        record_id=spin_data.record_id,
        user_id=user["id"],
        notes=spin_data.notes,
        created_at=now,
        record=RecordResponse(**record, spin_count=0)
    )

@router.get("/spins", response_model=List[SpinResponse])
async def get_my_spins(user: Dict = Depends(require_auth), limit: int = 50):
    spins = await db.spins.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for spin in spins:
        record = await db.records.find_one({"id": spin["record_id"]}, {"_id": 0})
        result.append(SpinResponse(
            **spin,
            record=RecordResponse(**record, spin_count=0) if record else None
        ))
    
    return result


# ============== HAUL ROUTES ==============

@router.post("/hauls", response_model=HaulResponse)
async def create_haul(haul_data: HaulCreate, user: Dict = Depends(require_auth)):
    haul_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Add each record to collection
    items_with_ids = []
    for item in haul_data.items:
        record_id = str(uuid.uuid4())
        record_doc = {
            "id": record_id,
            "user_id": user["id"],
            "discogs_id": item.discogs_id,
            "title": item.title,
            "artist": item.artist,
            "cover_url": item.cover_url,
            "year": item.year,
            "format": "Vinyl",
            "notes": item.notes,
            "created_at": now
        }
        await db.records.insert_one(record_doc)
        items_with_ids.append({**item.model_dump(), "record_id": record_id})
    
    haul_doc = {
        "id": haul_id,
        "user_id": user["id"],
        "title": haul_data.title,
        "description": haul_data.description,
        "image_url": haul_data.image_url,
        "items": items_with_ids,
        "created_at": now
    }
    
    await db.hauls.insert_one(haul_doc)
    
    # Create activity post
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "NEW_HAUL",
        "caption": f"Added {len(haul_data.items)} new records: {haul_data.title}",
        "haul_id": haul_id,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")}
    
    return HaulResponse(
        id=haul_id,
        user_id=user["id"],
        title=haul_data.title,
        description=haul_data.description,
        image_url=haul_data.image_url,
        items=items_with_ids,
        created_at=now,
        user=user_data
    )

@router.get("/hauls", response_model=List[HaulResponse])
async def get_my_hauls(user: Dict = Depends(require_auth)):
    hauls = await db.hauls.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")}
    
    return [HaulResponse(**haul, user=user_data) for haul in hauls]

@router.get("/hauls/{haul_id}", response_model=HaulResponse)
async def get_haul(haul_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    haul = await db.hauls.find_one({"id": haul_id}, {"_id": 0})
    if not haul:
        raise HTTPException(status_code=404, detail="Haul not found")
    
    user = await db.users.find_one({"id": haul["user_id"]}, {"_id": 0, "password_hash": 0})
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")} if user else None
    
    return HaulResponse(**haul, user=user_data)


# ============== WEEKLY SUMMARY ROUTES ==============

@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(user: Dict = Depends(require_auth)):
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).isoformat()
    week_end = now.isoformat()
    
    # Get spins from last week
    spins = await db.spins.find({
        "user_id": user["id"],
        "created_at": {"$gte": week_start}
    }, {"_id": 0}).to_list(1000)
    
    total_spins = len(spins)
    
    # Calculate top artist and album
    artist_counts = {}
    album_counts = {}
    
    for spin in spins:
        record = await db.records.find_one({"id": spin["record_id"]}, {"_id": 0})
        if record:
            artist = record.get("artist", "Unknown")
            album = record.get("title", "Unknown")
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
            album_key = f"{artist} - {album}"
            album_counts[album_key] = album_counts.get(album_key, 0) + 1
    
    top_artist = max(artist_counts, key=artist_counts.get) if artist_counts else None
    top_album_key = max(album_counts, key=album_counts.get) if album_counts else None
    top_album = top_album_key.split(" - ", 1)[1] if top_album_key and " - " in top_album_key else top_album_key
    
    # Determine listening mood (honey themed)
    moods = ["Buzzing", "Mellow", "Golden", "Sweet", "Warm", "Groovy"]
    listening_mood = moods[total_spins % len(moods)] if total_spins > 0 else "Quiet week"
    
    # Count records added
    records_added = await db.records.count_documents({
        "user_id": user["id"],
        "created_at": {"$gte": week_start}
    })
    
    summary_id = str(uuid.uuid4())
    
    # Check if summary already exists for this week
    existing = await db.weekly_summaries.find_one({
        "user_id": user["id"],
        "week_start": {"$gte": week_start}
    }, {"_id": 0})
    
    if existing:
        return WeeklySummaryResponse(**existing)
    
    summary_doc = {
        "id": summary_id,
        "user_id": user["id"],
        "week_start": week_start,
        "week_end": week_end,
        "total_spins": total_spins,
        "top_artist": top_artist,
        "top_album": top_album,
        "listening_mood": listening_mood,
        "records_added": records_added,
        "created_at": now.isoformat()
    }
    
    await db.weekly_summaries.insert_one(summary_doc)
    
    # Create activity post for weekly summary
    if total_spins > 0:
        post_id = str(uuid.uuid4())
        post_doc = {
            "id": post_id,
            "user_id": user["id"],
            "post_type": "WEEKLY_WRAP",
            "caption": f"HoneyGroove Weekly: {total_spins} spins this week. Top artist: {top_artist or 'N/A'}",
            "weekly_wrap_id": summary_id,
            "created_at": now.isoformat()
        }
        await db.posts.insert_one(post_doc)
    
    return WeeklySummaryResponse(**summary_doc)


# ============== FILE UPLOAD ROUTES ==============

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif",
}
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "heic", "heif"}
MAX_DIMENSION = 1200
JPEG_QUALITY = 85


def process_image(data: bytes, content_type: str, filename: str) -> tuple:
    """Convert HEIC/HEIF to JPEG, resize to max 1200px, compress to 85% JPEG quality.
    Returns (processed_bytes, final_content_type, final_extension)."""
    from PIL import Image, ImageOps
    import io

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    is_heic = ext in ("heic", "heif") or content_type in ("image/heic", "image/heif")

    if is_heic:
        import pillow_heif
        pillow_heif.register_heif_opener()

    img = Image.open(io.BytesIO(data))

    # Apply EXIF orientation so photos display correctly regardless of rotation metadata
    img = ImageOps.exif_transpose(img)

    # Convert palette/RGBA modes for JPEG compatibility
    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize if larger than MAX_DIMENSION on longest side
    w, h = img.size
    if max(w, h) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue(), "image/jpeg", "jpg"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: Dict = Depends(require_auth)):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    ct = (file.content_type or "").lower()

    if ext not in ALLOWED_EXTENSIONS and ct not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are allowed (jpg, png, webp, heic)")

    data = await file.read()

    try:
        processed_data, final_ct, final_ext = process_image(data, ct, file.filename)
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise HTTPException(status_code=400, detail="Could not process image. Please upload a jpg, png, or webp file.")

    path = f"{APP_NAME}/uploads/{user['id']}/{uuid.uuid4()}.{final_ext}"

    try:
        result = put_object(path, processed_data, final_ct)
        
        # Store file reference
        file_id = str(uuid.uuid4())
        await db.files.insert_one({
            "id": file_id,
            "user_id": user["id"],
            "storage_path": result["path"],
            "original_filename": file.filename,
            "content_type": final_ct,
            "size": result.get("size", len(processed_data)),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Build a public URL that routes through our proxy endpoint
        public_url = f"{FRONTEND_URL}/api/files/serve/{result['path']}"
        
        return {"file_id": file_id, "path": result["path"], "url": public_url}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/admin/reprocess-heic")
async def reprocess_heic_files(user: Dict = Depends(require_auth)):
    """Admin: find and reprocess any HEIC/HEIF files stored in the DB."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    reprocessed = []
    # Check listings photo_urls, users avatar_url, posts image_url, files
    for coll_name, field in [("listings", "photo_urls"), ("users", "avatar_url"), ("posts", "image_url")]:
        docs = await db[coll_name].find({}, {"_id": 0}).to_list(5000)
        for doc in docs:
            val = doc.get(field)
            urls_to_check = val if isinstance(val, list) else ([val] if val else [])
            for url in urls_to_check:
                if not url or not isinstance(url, str):
                    continue
                if not any(url.lower().endswith(ext) for ext in (".heic", ".heif")):
                    continue
                # Extract storage path
                serve_marker = "/api/files/serve/"
                idx = url.find(serve_marker)
                storage_path = url[idx + len(serve_marker):] if idx != -1 else url
                if not storage_path.startswith(f"{APP_NAME}/"):
                    continue
                try:
                    raw_data, _ = get_object(storage_path)
                    if raw_data is None:
                        continue
                    processed_data, final_ct, final_ext = process_image(raw_data, "image/heic", storage_path)
                    new_path = storage_path.rsplit(".", 1)[0] + f".{final_ext}"
                    put_object(new_path, processed_data, final_ct)
                    new_url = url[:idx] + serve_marker + new_path if idx != -1 else new_path
                    # Update the DB record
                    if isinstance(val, list):
                        new_list = [new_url if u == url else u for u in val]
                        await db[coll_name].update_one({"id": doc["id"]}, {"$set": {field: new_list}})
                    else:
                        await db[coll_name].update_one({"id": doc["id"]}, {"$set": {field: new_url}})
                    reprocessed.append({"collection": coll_name, "id": doc.get("id"), "old": url, "new": new_url})
                except Exception as e:
                    logger.error(f"Reprocess HEIC failed for {coll_name}/{doc.get('id')}: {e}")

    return {"reprocessed": len(reprocessed), "details": reprocessed}

@router.get("/files/{file_id}")
async def get_file(file_id: str, user: Dict = Depends(require_auth)):
    file_record = await db.files.find_one({"id": file_id}, {"_id": 0})
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        data, content_type = get_object(file_record["storage_path"])
        return Response(content=data, media_type=content_type)
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.get("/files/serve/{path:path}")
async def serve_file(path: str):
    """Public proxy endpoint to serve uploaded images from storage."""
    if not path.startswith(f"{APP_NAME}/"):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        data, content_type = get_object(path)
        if data is None:
            raise HTTPException(status_code=404, detail="File not found")
        return Response(
            content=data,
            media_type=content_type or "image/jpeg",
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Serve file failed: {e}")
        raise HTTPException(status_code=500, detail="File not found")


# ============== DISCOGS OAUTH & IMPORT ROUTES ==============

@router.get("/discogs/oauth/start")
async def discogs_oauth_start(user: Dict = Depends(require_auth)):
    """Step 1: Get request token and return authorization URL"""
    if not DISCOGS_CONSUMER_KEY or not DISCOGS_CONSUMER_SECRET:
        raise HTTPException(status_code=400, detail="Discogs OAuth not configured. Please add Consumer Key and Secret in settings.")
    
    frontend_url = "https://thehoneygroove.com"
    callback_url = f"{frontend_url}/api/discogs/oauth/callback"
    
    try:
        oauth = OAuth1Session(
            client_key=DISCOGS_CONSUMER_KEY,
            client_secret=DISCOGS_CONSUMER_SECRET,
            callback_uri=callback_url
        )
        
        response = oauth.fetch_request_token(
            DISCOGS_REQUEST_TOKEN_URL,
            headers={"User-Agent": DISCOGS_USER_AGENT}
        )
        
        oauth_token = response.get('oauth_token')
        oauth_token_secret = response.get('oauth_token_secret')
        
        # Store the request token secret (keyed by oauth_token)
        oauth_request_tokens[oauth_token] = oauth_token_secret
        
        # Also store user_id mapping so we know who initiated this
        await db.discogs_oauth_pending.update_one(
            {"oauth_token": oauth_token},
            {"$set": {
                "oauth_token": oauth_token,
                "oauth_token_secret": oauth_token_secret,
                "user_id": user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        authorization_url = f"{DISCOGS_AUTHORIZE_URL}?oauth_token={oauth_token}"
        
        return {"authorization_url": authorization_url}
    
    except Exception as e:
        logger.error(f"Discogs OAuth start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start Discogs OAuth: {str(e)}")


@router.get("/discogs/oauth/callback")
async def discogs_oauth_callback(oauth_token: str = Query(...), oauth_verifier: str = Query(...)):
    """Step 2: Handle callback from Discogs, exchange for access token"""
    try:
        # Look up the stored request token secret
        pending = await db.discogs_oauth_pending.find_one({"oauth_token": oauth_token}, {"_id": 0})
        if not pending:
            # Try in-memory fallback
            oauth_token_secret = oauth_request_tokens.get(oauth_token)
            if not oauth_token_secret:
                raise HTTPException(status_code=400, detail="Invalid or expired OAuth token")
            user_id = None
        else:
            oauth_token_secret = pending["oauth_token_secret"]
            user_id = pending["user_id"]
        
        # Exchange for access token
        oauth = OAuth1Session(
            client_key=DISCOGS_CONSUMER_KEY,
            client_secret=DISCOGS_CONSUMER_SECRET,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
            verifier=oauth_verifier
        )
        
        access_tokens = oauth.fetch_access_token(
            DISCOGS_ACCESS_TOKEN_URL,
            headers={"User-Agent": DISCOGS_USER_AGENT}
        )
        
        access_token = access_tokens.get('oauth_token')
        access_token_secret = access_tokens.get('oauth_token_secret')
        
        # Get user identity from Discogs
        identity_oauth = OAuth1Session(
            client_key=DISCOGS_CONSUMER_KEY,
            client_secret=DISCOGS_CONSUMER_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        identity_resp = identity_oauth.get(
            f"{DISCOGS_API_BASE}/oauth/identity",
            headers={"User-Agent": DISCOGS_USER_AGENT}
        )
        identity_resp.raise_for_status()
        identity = identity_resp.json()
        discogs_username = identity.get("username", "")
        
        # Store the access tokens for this user
        if user_id:
            await db.discogs_tokens.update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "oauth_token": access_token,
                    "oauth_token_secret": access_token_secret,
                    "discogs_username": discogs_username,
                    "connected_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
            
            # Clean up pending
            await db.discogs_oauth_pending.delete_one({"oauth_token": oauth_token})
            oauth_request_tokens.pop(oauth_token, None)
        
        # Redirect to frontend import page with success
        from fastapi.responses import RedirectResponse
        frontend_base = "https://thehoneygroove.com"
        return RedirectResponse(url=f"{frontend_base}/collection?discogs=connected&username={discogs_username}")
    
    except Exception as e:
        logger.error(f"Discogs OAuth callback failed: {e}")
        frontend_base = "https://thehoneygroove.com"
        return RedirectResponse(url=f"{frontend_base}/collection?discogs=error&message={str(e)}")


@router.get("/discogs/status")
async def discogs_connection_status(user: Dict = Depends(require_auth)):
    """Check if user has connected their Discogs account"""
    token_doc = await db.discogs_tokens.find_one({"user_id": user["id"]}, {"_id": 0})
    
    if not token_doc:
        return {
            "connected": False,
            "discogs_username": None,
            "last_synced": None
        }
    
    # Check import progress
    progress = import_progress.get(user["id"])
    
    # Get last sync time
    last_import = await db.discogs_imports.find_one(
        {"user_id": user["id"]},
        {"_id": 0},
    )
    
    return {
        "connected": True,
        "discogs_username": token_doc.get("discogs_username"),
        "connected_at": token_doc.get("connected_at"),
        "last_synced": last_import.get("completed_at") if last_import else None,
        "import_status": progress if progress else None
    }


@router.post("/discogs/import")
async def start_discogs_import(user: Dict = Depends(require_auth)):
    """Start importing the user's Discogs collection"""
    token_doc = await db.discogs_tokens.find_one({"user_id": user["id"]}, {"_id": 0})
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Discogs account not connected. Please authorize first.")
    
    # Check if import is already in progress
    current = import_progress.get(user["id"])
    if current and current.get("status") == "in_progress":
        return current
    
    # Initialize progress
    import_progress[user["id"]] = {
        "status": "in_progress",
        "total": 0,
        "imported": 0,
        "skipped": 0,
        "error_message": None,
        "discogs_username": token_doc.get("discogs_username"),
        "started_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Run import in background
    auth_type = token_doc.get("auth_type", "oauth")
    asyncio.create_task(_run_discogs_import(
        user["id"],
        token_doc.get("oauth_token"),
        token_doc.get("oauth_token_secret"),
        token_doc["discogs_username"],
        auth_type
    ))
    
    return import_progress[user["id"]]


@router.get("/discogs/import/progress")
async def get_import_progress(user: Dict = Depends(require_auth)):
    """Get current import progress"""
    progress = import_progress.get(user["id"])
    if not progress:
        # Check if there was a past import
        last_import = await db.discogs_imports.find_one(
            {"user_id": user["id"]},
            {"_id": 0},
        )
        if last_import:
            return {
                "status": "completed",
                "total": last_import.get("total", 0),
                "imported": last_import.get("imported", 0),
                "skipped": last_import.get("skipped", 0),
                "errors": last_import.get("errors", 0),
                "error_message": None,
                "discogs_username": last_import.get("discogs_username"),
                "sample_covers": last_import.get("sample_covers", []),
                "skipped_records": last_import.get("skipped_records", []),
                "last_synced": last_import.get("completed_at")
            }
        return {"status": "idle", "total": 0, "imported": 0, "skipped": 0, "errors": 0, "sample_covers": []}
    return progress


async def _run_discogs_import(user_id: str, oauth_token: str, oauth_token_secret: str, discogs_username: str, auth_type: str = "oauth"):
    """Background task to import Discogs collection"""
    try:
        # Set up the appropriate session based on auth type
        if auth_type == "personal_token":
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Discogs token={DISCOGS_TOKEN}",
                "User-Agent": DISCOGS_USER_AGENT
            })
        else:
            session = OAuth1Session(
                client_key=DISCOGS_CONSUMER_KEY,
                client_secret=DISCOGS_CONSUMER_SECRET,
                resource_owner_key=oauth_token,
                resource_owner_secret=oauth_token_secret
            )
            session.headers.update({"User-Agent": DISCOGS_USER_AGENT})
        
        # First, get the total count from folder 0 (All)
        first_page_url = f"{DISCOGS_API_BASE}/users/{discogs_username}/collection/folders/0/releases"
        first_resp = session.get(first_page_url, params={"page": 1, "per_page": 100})
        
        if first_resp.status_code == 403:
            import_progress[user_id]["status"] = "error"
            import_progress[user_id]["error_message"] = f"Collection for '{discogs_username}' is private. Update your Discogs privacy settings or connect via OAuth."
            return
        
        if first_resp.status_code == 404:
            import_progress[user_id]["status"] = "error"
            import_progress[user_id]["error_message"] = f"Discogs user '{discogs_username}' not found."
            return
        
        if first_resp.status_code != 200:
            import_progress[user_id]["status"] = "error"
            import_progress[user_id]["error_message"] = f"Failed to fetch collection (HTTP {first_resp.status_code}). Please try again."
            return
        
        first_data = first_resp.json()
        pagination = first_data.get("pagination", {})
        total_items = pagination.get("items", 0)
        total_pages = pagination.get("pages", 1)
        
        import_progress[user_id]["total"] = total_items
        
        if total_items == 0:
            import_progress[user_id]["status"] = "completed"
            import_progress[user_id]["error_message"] = "No releases found in your Discogs collection."
            return
        
        # Process all pages
        all_releases = first_data.get("releases", [])
        
        for page in range(2, total_pages + 1):
            remaining = int(first_resp.headers.get('X-Discogs-Ratelimit-Remaining', 60))
            if remaining < 5:
                await asyncio.sleep(30)
            else:
                await asyncio.sleep(1.1)
            
            page_resp = session.get(
                first_page_url,
                params={"page": page, "per_page": 100}
            )
            
            if page_resp.status_code == 429:
                await asyncio.sleep(60)
                page_resp = session.get(
                    first_page_url,
                    params={"page": page, "per_page": 100}
                )
            
            if page_resp.status_code == 200:
                page_data = page_resp.json()
                all_releases.extend(page_data.get("releases", []))
                first_resp = page_resp
            else:
                logger.warning(f"Failed to fetch page {page}: {page_resp.status_code}")
        
        # Now import each release into the user's collection
        imported = 0
        skipped = 0
        errors = 0
        imported_discogs_ids = []
        sample_covers = []
        skipped_records = []
        now = datetime.now(timezone.utc).isoformat()
        
        for release in all_releases:
            try:
                basic_info = release.get("basic_information", {})
                discogs_id = basic_info.get("id")
                
                # Extract title/artist early for skip logging
                artists = basic_info.get("artists", [])
                release_title = basic_info.get("title", "Unknown Title")
                release_artist = ", ".join(a.get("name", "") for a in artists) if artists else "Unknown Artist"
                
                if not discogs_id:
                    skipped += 1
                    import_progress[user_id]["skipped"] = skipped
                    skipped_records.append({"title": release_title, "artist": release_artist, "discogs_id": None, "reason": "missing_data"})
                    continue
                
                # Check if already exists in user's collection
                existing = await db.records.find_one({
                    "user_id": user_id,
                    "discogs_id": discogs_id
                })
                
                if existing:
                    skipped += 1
                    import_progress[user_id]["skipped"] = skipped
                    import_progress[user_id]["imported"] = imported
                    skipped_records.append({"title": release_title, "artist": release_artist, "discogs_id": discogs_id, "reason": "duplicate"})
                    continue
                
                cover_url = basic_info.get("cover_image") or basic_info.get("thumb")
                formats = basic_info.get("formats", [])
                format_name = formats[0].get("name", "Vinyl") if formats else "Vinyl"
                
                record_id = str(uuid.uuid4())
                record_doc = {
                    "id": record_id,
                    "user_id": user_id,
                    "discogs_id": discogs_id,
                    "title": release_title,
                    "artist": release_artist,
                    "cover_url": cover_url,
                    "year": basic_info.get("year"),
                    "format": format_name,
                    "notes": "Imported from Discogs",
                    "source": "discogs_import",
                    "created_at": now
                }
                
                await db.records.insert_one(record_doc)
                imported += 1
                imported_discogs_ids.append(discogs_id)
                import_progress[user_id]["imported"] = imported
                
                # Collect sample covers for summary (first 12)
                if cover_url and len(sample_covers) < 12:
                    sample_covers.append({"title": record_doc["title"], "artist": release_artist, "cover_url": cover_url})
                
            except Exception as e:
                logger.error(f"Failed to import release: {e}")
                errors += 1
                skipped += 1
                import_progress[user_id]["skipped"] = skipped
                skipped_records.append({"title": release_title, "artist": release_artist, "discogs_id": discogs_id, "reason": "error", "error_detail": str(e)[:120]})
        
        # Mark complete with enriched summary
        import_progress[user_id]["status"] = "completed"
        import_progress[user_id]["imported"] = imported
        import_progress[user_id]["skipped"] = skipped
        import_progress[user_id]["errors"] = errors
        import_progress[user_id]["sample_covers"] = sample_covers
        import_progress[user_id]["skipped_records"] = skipped_records
        
        # Store import record
        await db.discogs_imports.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "discogs_username": discogs_username,
                "total": total_items,
                "imported": imported,
                "skipped": skipped,
                "errors": errors,
                "sample_covers": sample_covers,
                "skipped_records": skipped_records,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        # Mark user as having completed a Discogs import (for welcome dashboard)
        if imported > 0:
            # Calculate and cache welcome stats
            records = await db.records.find(
                {"user_id": user_id},
                {"_id": 0, "discogs_id": 1, "artist": 1}
            ).to_list(10000)
            discogs_ids_all = list({r["discogs_id"] for r in records if r.get("discogs_id")})
            total_value = 0.0
            if discogs_ids_all:
                values = await db.collection_values.find(
                    {"release_id": {"$in": discogs_ids_all}}, {"_id": 0}
                ).to_list(10000)
                for v in values:
                    total_value += v.get("median_value") or v.get("low_value") or 0
            artist_counts = {}
            for r in records:
                a = r.get("artist", "Unknown Artist")
                if a and a != "Unknown Artist":
                    artist_counts[a] = artist_counts.get(a, 0) + 1
            top_artist = max(artist_counts, key=artist_counts.get) if artist_counts else None
            
            await db.users.update_one({"id": user_id}, {"$set": {
                "discogs_import_completed": True,
                "has_seen_welcome_hive_dashboard": False,
                "last_imported_record_count": imported,
                "last_imported_collection_value": round(total_value, 2),
                "last_imported_artist_count": len(artist_counts),
                "last_imported_top_artist": top_artist,
            }})
        
        # Create activity post for the import
        if imported > 0:
            post_id = str(uuid.uuid4())
            post_doc = {
                "id": post_id,
                "user_id": user_id,
                "post_type": "record_added",
                "content": f"Imported {imported} records from Discogs",
                "record_id": None,
                "haul_id": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.posts.insert_one(post_doc)
        
        # Background: fetch collection values for newly imported records
        if imported_discogs_ids:
            asyncio.create_task(_post_import_value_refresh(user_id, imported_discogs_ids))
        
        logger.info(f"Discogs import complete for {user_id}: {imported} imported, {skipped} skipped, {errors} errors out of {total_items}")
        
    except Exception as e:
        logger.error(f"Discogs import failed for {user_id}: {e}")
        import_progress[user_id]["status"] = "error"
        import_progress[user_id]["error_message"] = str(e)


async def _post_import_value_refresh(user_id: str, discogs_ids: list):
    """After import, fetch Discogs market values for newly imported records."""
    from database import get_discogs_market_data
    fetched = 0
    for did in discogs_ids:
        try:
            cached = await db.collection_values.find_one({"release_id": did})
            if cached:
                continue  # Already valued
            data = get_discogs_market_data(did)
            if data:
                now = datetime.now(timezone.utc).isoformat()
                await db.collection_values.update_one(
                    {"release_id": did},
                    {"$set": {
                        "release_id": did,
                        "median_value": data["median_value"],
                        "low_value": data["low_value"],
                        "high_value": data["high_value"],
                        "last_updated": now,
                    }},
                    upsert=True
                )
                fetched += 1
        except Exception as e:
            logger.error(f"Post-import value fetch failed for {did}: {e}")
        await asyncio.sleep(1.1)  # Rate limit
    logger.info(f"Post-import value refresh for {user_id}: {fetched}/{len(discogs_ids)} valued")


@router.delete("/discogs/disconnect")
async def disconnect_discogs(user: Dict = Depends(require_auth)):
    """Disconnect Discogs account"""
    await db.discogs_tokens.delete_one({"user_id": user["id"]})
    await db.discogs_oauth_pending.delete_many({"user_id": user["id"]})
    import_progress.pop(user["id"], None)
    return {"message": "Discogs account disconnected"}


@router.get("/discogs/import/summary")
async def get_import_summary(user: Dict = Depends(require_auth)):
    """Get a rich summary of the last completed import including collection value."""
    last_import = await db.discogs_imports.find_one({"user_id": user["id"]}, {"_id": 0})
    if not last_import:
        return {"has_import": False}
    
    # Get collection value
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1}
    ).to_list(5000)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    
    total_value = 0.0
    valued_count = 0
    if discogs_ids:
        values = await db.collection_values.find(
            {"release_id": {"$in": discogs_ids}}, {"_id": 0}
        ).to_list(5000)
        for v in values:
            if v.get("median_value"):
                total_value += v["median_value"]
                valued_count += 1
    
    total_records = await db.records.count_documents({"user_id": user["id"]})
    
    return {
        "has_import": True,
        "imported": last_import.get("imported", 0),
        "skipped": last_import.get("skipped", 0),
        "errors": last_import.get("errors", 0),
        "total": last_import.get("total", 0),
        "discogs_username": last_import.get("discogs_username"),
        "sample_covers": last_import.get("sample_covers", []),
        "skipped_records": last_import.get("skipped_records", []),
        "completed_at": last_import.get("completed_at"),
        "collection_stats": {
            "total_records": total_records,
            "total_value": round(total_value, 2),
            "valued_count": valued_count,
        }
    }


class DiscogsTokenConnect(BaseModel):
    discogs_username: str

@router.post("/discogs/connect-token")
async def connect_discogs_with_token(data: DiscogsTokenConnect, user: Dict = Depends(require_auth)):
    """Connect Discogs using the app's personal access token (no OAuth needed)"""
    if not DISCOGS_TOKEN:
        raise HTTPException(status_code=400, detail="Discogs token not configured")
    
    username = data.discogs_username.strip()
    headers = {
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": DISCOGS_USER_AGENT
    }
    # Verify the username exists on Discogs
    try:
        resp = requests.get(
            f"{DISCOGS_API_BASE}/users/{username}",
            headers=headers, timeout=10
        )
        if resp.status_code == 404:
            raise HTTPException(status_code=400, detail=f"Discogs user '{username}' not found. Please check the spelling.")
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Could not verify Discogs user (status {resp.status_code})")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify Discogs user: {str(e)}")
    
    # Verify collection is accessible (not private)
    try:
        col_resp = requests.get(
            f"{DISCOGS_API_BASE}/users/{username}/collection/folders/0/releases",
            params={"page": 1, "per_page": 1},
            headers=headers, timeout=10
        )
        if col_resp.status_code == 403:
            raise HTTPException(status_code=400, detail=f"The collection for '{username}' is private. Ask them to make it public in Discogs settings, or use OAuth to connect.")
        if col_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Could not access collection for '{username}' (status {col_resp.status_code})")
        col_data = col_resp.json()
        collection_count = col_data.get("pagination", {}).get("items", 0)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to access collection: {str(e)}")
    
    # Store as token-based connection
    await db.discogs_tokens.update_one(
        {"user_id": user["id"]},
        {"$set": {
            "user_id": user["id"],
            "auth_type": "personal_token",
            "discogs_username": username,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": f"Connected as {username}", "discogs_username": username, "collection_count": collection_count}



@router.get("/welcome-hive-data")
async def get_welcome_hive_data(user: Dict = Depends(require_auth)):
    """Return data for the Welcome to the Hive dashboard."""
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # If cached values exist, use them; otherwise compute fresh
    cached_value = u.get("last_imported_collection_value")
    cached_records = u.get("last_imported_record_count")
    cached_artists = u.get("last_imported_artist_count")
    cached_top = u.get("last_imported_top_artist")

    if cached_records is not None and cached_value is not None:
        return {
            "total_collection_value": cached_value,
            "total_records_imported": cached_records,
            "total_unique_artists": cached_artists or 0,
            "top_artist_by_count": cached_top,
            "has_seen": u.get("has_seen_welcome_hive_dashboard", False),
        }

    # Compute fresh
    records = await db.records.find(
        {"user_id": user["id"]},
        {"_id": 0, "discogs_id": 1, "artist": 1}
    ).to_list(10000)
    total_records = len(records)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})

    total_value = 0.0
    if discogs_ids:
        values = await db.collection_values.find(
            {"release_id": {"$in": discogs_ids}}, {"_id": 0}
        ).to_list(10000)
        for v in values:
            total_value += v.get("median_value") or v.get("low_value") or 0

    artist_counts = {}
    for r in records:
        a = r.get("artist", "Unknown Artist")
        if a and a != "Unknown Artist":
            artist_counts[a] = artist_counts.get(a, 0) + 1
    top_artist = max(artist_counts, key=artist_counts.get) if artist_counts else None

    # Cache on user
    await db.users.update_one({"id": user["id"]}, {"$set": {
        "last_imported_collection_value": round(total_value, 2),
        "last_imported_record_count": total_records,
        "last_imported_artist_count": len(artist_counts),
        "last_imported_top_artist": top_artist,
    }})

    return {
        "total_collection_value": round(total_value, 2),
        "total_records_imported": total_records,
        "total_unique_artists": len(artist_counts),
        "top_artist_by_count": top_artist,
        "has_seen": u.get("has_seen_welcome_hive_dashboard", False),
    }


@router.post("/mark-welcome-seen")
async def mark_welcome_seen(user: Dict = Depends(require_auth)):
    """Mark the Welcome to the Hive dashboard as seen."""
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"has_seen_welcome_hive_dashboard": True}}
    )
    return {"ok": True}
