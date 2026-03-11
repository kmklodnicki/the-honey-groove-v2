from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import os
import logging

from database import db, require_auth, get_current_user, security, logger, create_notification, get_hidden_user_ids

# ---------- HONEY Order ID Generator ----------
HONEY_ORDER_START = 134208789

async def _next_honey_order_id() -> str:
    """Atomically increment a counter and return HONEY-XXXXXXXXX."""
    doc = await db.counters.find_one_and_update(
        {"_id": "order_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"] + HONEY_ORDER_START - 1
    return f"HONEY-{seq}"
from services.email_service import send_email_fire_and_forget
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, PLATFORM_FEE_PERCENT, FRONTEND_URL
from emergentintegrations.payments.stripe import StripeCheckout
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from database import oauth_request_tokens, import_progress, EMERGENT_KEY
from models import *
from pydantic import BaseModel
import stripe as stripe_sdk
from fastapi.responses import Response

import re

router = APIRouter()

# Off-platform payment keywords to detect (fuzzy engine)
from util.content_filter import detect_offplatform_payment, BLOCK_MESSAGE as OFFPLATFORM_BLOCK_MESSAGE


async def _get_seller_transaction_count(user_id: str) -> int:
    """Count completed trades + sold listings for a user."""
    completed_trades = await db.trades.count_documents({
        "$or": [{"initiator_id": user_id}, {"responder_id": user_id}],
        "status": "COMPLETED"
    })
    completed_sales = await db.listings.count_documents({"user_id": user_id, "status": "SOLD"})
    return completed_trades + completed_sales

async def _get_platform_fee_percent() -> float:
    """Get the current platform fee % from settings, fallback to default."""
    settings = await db.platform_settings.find_one({"key": "platform_fee_percent"}, {"_id": 0})
    if settings and settings.get("value") is not None:
        return float(settings["value"])
    return PLATFORM_FEE_PERCENT


@router.get("/platform-fee")
async def get_platform_fee():
    """Public endpoint to get the current platform fee percentage."""
    fee = await _get_platform_fee_percent()
    return {"platform_fee_percent": fee}


# ============== ISO ROUTES ==============

# Model for creating ISO items directly (e.g., from AddRecordPage dreaming mode)
class ISODirectCreate(BaseModel):
    artist: str
    album: str
    discogs_id: Optional[int] = None
    cover_url: Optional[str] = None
    year: Optional[int] = None
    color_variant: Optional[str] = None
    notes: Optional[str] = None
    preferred_number: Optional[int] = None
    status: Optional[str] = "WISHLIST"
    priority: Optional[str] = "LOW"

@router.post("/iso", response_model=ISOResponse)
async def create_iso_direct(data: ISODirectCreate, user: Dict = Depends(require_auth)):
    """Create an ISO item directly (for Dreaming/wishlist mode in AddRecordPage)."""
    now = datetime.now(timezone.utc).isoformat()
    iso_id = str(uuid.uuid4())
    
    iso_doc = {
        "id": iso_id,
        "user_id": user["id"],
        "artist": data.artist,
        "album": data.album,
        "discogs_id": data.discogs_id,
        "cover_url": data.cover_url,
        "year": data.year,
        "color_variant": data.color_variant,
        "pressing_notes": data.notes,
        "preferred_number": data.preferred_number,
        "status": data.status or "WISHLIST",
        "priority": data.priority or "LOW",
        "created_at": now,
    }
    await db.iso_items.insert_one(iso_doc)
    return ISOResponse(**iso_doc)

@router.get("/iso", response_model=List[ISOResponse])
async def get_my_isos(user: Dict = Depends(require_auth)):
    isos = await db.iso_items.find({"user_id": user["id"], "status": {"$ne": "WISHLIST"}}, {"_id": 0}).sort("created_at", -1).to_list(100)
    result = []
    for iso in isos:
        record_data = None
        if iso.get("record_id"):
            record_data = await db.records.find_one({"id": iso["record_id"]}, {"_id": 0})
        result.append(ISOResponse(**iso, record=record_data))
    return result


@router.get("/iso/dreamlist")
async def get_my_dreamlist(user: Dict = Depends(require_auth)):
    """Return all Dream List (WISHLIST) items for the current user, enriched with 3-tier values."""
    isos = await db.iso_items.find(
        {"user_id": user["id"], "status": "WISHLIST"}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)

    # Batch-fetch median values for all discogs_ids
    discogs_ids = [i["discogs_id"] for i in isos if i.get("discogs_id")]
    value_map = {}
    community_map = {}
    if discogs_ids:
        values = await db.collection_values.find(
            {"release_id": {"$in": discogs_ids}}, {"_id": 0, "release_id": 1, "median_value": 1}
        ).to_list(len(discogs_ids))
        value_map = {v["release_id"]: v.get("median_value") for v in values if v.get("median_value")}
        # Community valuations for items missing Discogs data
        missing = [d for d in discogs_ids if d not in value_map]
        if missing:
            cvs = await db.community_valuations.find(
                {"release_id": {"$in": missing}}, {"_id": 0, "release_id": 1, "average_value": 1}
            ).to_list(len(missing))
            community_map = {c["release_id"]: c.get("average_value") for c in cvs if c.get("average_value")}

    for item in isos:
        did = item.get("discogs_id")
        discogs_val = value_map.get(did)
        community_val = community_map.get(did)
        manual_val = item.get("manual_price")
        # Set resolved median_value using 3-tier priority
        item["median_value"] = discogs_val or community_val or (manual_val if manual_val and manual_val > 0 else None)
        item["value_source"] = "discogs" if discogs_val else ("community" if community_val else ("manual" if manual_val and manual_val > 0 else "pending"))

    return isos

@router.put("/iso/{iso_id}/found")
async def mark_iso_found(iso_id: str, user: Dict = Depends(require_auth)):
    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]})
    if not iso:
        raise HTTPException(status_code=404, detail="ISO not found")
    
    now = datetime.now(timezone.utc).isoformat()
    await db.iso_items.update_one({"id": iso_id}, {"$set": {"status": "FOUND", "found_at": now}})
    return {"message": "ISO marked as found"}

@router.put("/iso/{iso_id}/promote")
async def promote_to_active(iso_id: str, user: Dict = Depends(require_auth)):
    """Promote a WISHLIST item to active OPEN ISO ('Ready to Buy' flow)."""
    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]})
    if not iso:
        raise HTTPException(status_code=404, detail="ISO not found")
    await db.iso_items.update_one({"id": iso_id}, {"$set": {"status": "OPEN", "priority": "HIGH"}})
    return {"message": f"{iso.get('album', 'Record')} is now on the hunt."}



@router.put("/iso/{iso_id}/demote")
async def demote_to_dreaming(iso_id: str, user: Dict = Depends(require_auth)):
    """Revert an active OPEN ISO back to WISHLIST (Dreaming)."""
    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]})
    if not iso:
        raise HTTPException(status_code=404, detail="ISO not found")
    await db.iso_items.update_one({"id": iso_id}, {"$set": {"status": "WISHLIST", "priority": "LOW"}})
    return {"message": f"{iso.get('album', 'Record')} moved back to Dreams."}



@router.post("/iso/{iso_id}/convert-to-collection")
async def convert_iso_to_collection(iso_id: str, user: Dict = Depends(require_auth)):
    """Convert an ISO item to a collection record ('I Found It!' flow)."""
    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]})
    if not iso:
        raise HTTPException(status_code=404, detail="ISO not found")

    now = datetime.now(timezone.utc).isoformat()
    record_id = str(uuid.uuid4())

    record_doc = {
        "id": record_id,
        "user_id": user["id"],
        "discogs_id": iso.get("discogs_id"),
        "title": iso.get("album", "Unknown Album"),
        "artist": iso.get("artist", "Unknown Artist"),
        "cover_url": iso.get("cover_url"),
        "year": iso.get("year"),
        "format": "Vinyl",
        "notes": "Found via ISO",
        "source": "iso",
        "created_at": now,
    }
    await db.records.insert_one(record_doc)

    # Mark ISO as found then delete
    await db.iso_items.update_one({"id": iso_id}, {"$set": {"status": "FOUND", "found_at": now}})
    await db.iso_items.delete_one({"id": iso_id})

    # Also update linked post if any
    await db.posts.update_many({"iso_id": iso_id}, {"$set": {"iso_status": "FOUND"}})

    return {
        "message": f"{iso.get('album')} is now in your Hive.",
        "record_id": record_id,
        "title": iso.get("album"),
        "artist": iso.get("artist"),
    }


class ISOAcquireRequest(BaseModel):
    media_condition: Optional[str] = None
    sleeve_condition: Optional[str] = None
    price_paid: Optional[float] = None


@router.post("/iso/{iso_id}/acquire")
async def acquire_iso(iso_id: str, body: ISOAcquireRequest, user: Dict = Depends(require_auth)):
    """Upgrade to Reality: move an ISO/Hunt item into the collection with condition & price details."""
    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]})
    if not iso:
        raise HTTPException(status_code=404, detail="ISO not found")

    now = datetime.now(timezone.utc).isoformat()
    record_id = str(uuid.uuid4())

    notes_parts = ["Found via The Hunt"]
    if body.media_condition:
        notes_parts.append(f"Media: {body.media_condition}")
    if body.sleeve_condition:
        notes_parts.append(f"Sleeve: {body.sleeve_condition}")
    if body.price_paid is not None:
        notes_parts.append(f"Paid: ${body.price_paid:.2f}")

    record_doc = {
        "id": record_id,
        "user_id": user["id"],
        "discogs_id": iso.get("discogs_id"),
        "title": iso.get("album", "Unknown Album"),
        "artist": iso.get("artist", "Unknown Artist"),
        "cover_url": iso.get("cover_url"),
        "year": iso.get("year"),
        "format": "Vinyl",
        "notes": " | ".join(notes_parts),
        "color_variant": iso.get("color_variant"),
        "source": "iso",
        "media_condition": body.media_condition,
        "sleeve_condition": body.sleeve_condition,
        "price_paid": body.price_paid,
        "created_at": now,
    }
    await db.records.insert_one(record_doc)

    # Mark ISO as found then delete
    await db.iso_items.update_one({"id": iso_id}, {"$set": {"status": "FOUND", "found_at": now}})
    await db.iso_items.delete_one({"id": iso_id})

    # Update linked post if any
    await db.posts.update_many({"iso_id": iso_id}, {"$set": {"iso_status": "FOUND"}})

    return {
        "message": f"{iso.get('album')} is now in your Collection.",
        "record_id": record_id,
        "title": iso.get("album"),
        "artist": iso.get("artist"),
    }


@router.delete("/iso/{iso_id}")
async def delete_iso(iso_id: str, user: Dict = Depends(require_auth)):
    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]})
    if not iso:
        raise HTTPException(status_code=404, detail="ISO not found")
    await db.iso_items.delete_one({"id": iso_id})
    return {"message": "ISO deleted"}


@router.get("/iso/community")
async def get_community_isos(limit: int = 50, user: Dict = Depends(require_auth)):
    """Get ISO items from all users except the current user"""
    hidden_ids = await get_hidden_user_ids()
    exclude_ids = list(set([user["id"]] + hidden_ids))
    isos = await db.iso_items.find(
        {"user_id": {"$nin": exclude_ids}, "status": "OPEN"}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    user_ids = list({iso["user_id"] for iso in isos})
    users = {u["id"]: u for u in await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(100)} if user_ids else {}
    result = []
    for iso in isos:
        iso_user = users.get(iso["user_id"])
        iso["user"] = {"id": iso_user["id"], "username": iso_user.get("username"), "avatar_url": iso_user.get("avatar_url"), "country": iso_user.get("country"), "title_label": iso_user.get("title_label"), "golden_hive": iso_user.get("golden_hive", False)} if iso_user else None
        result.append(iso)
    return result



# ============== MARKETPLACE LISTING ROUTES ==============

@router.post("/listings", response_model=ListingResponse)
async def create_listing(data: ListingCreate, user: Dict = Depends(require_auth)):
    """Create a marketplace listing"""
    if not data.photo_urls or len(data.photo_urls) == 0:
        raise HTTPException(status_code=400, detail="At least 1 photo is required")
    if not data.condition:
        raise HTTPException(status_code=400, detail="Condition is required")

    # New seller listing restriction: <3 transactions can't list above $150
    if data.price and data.price > 150:
        tx_count = await _get_seller_transaction_count(user["id"])
        if tx_count < 3:
            raise HTTPException(
                status_code=400,
                detail="New sellers can list items up to $150. Complete 3 transactions to unlock higher value listings."
            )

    now = datetime.now(timezone.utc).isoformat()
    listing_id = str(uuid.uuid4())

    # Off-platform payment detection — fuzzy scan description
    offplatform_flagged = False
    offplatform_keywords_found = []
    if data.description:
        offplatform_flagged, offplatform_keywords_found = detect_offplatform_payment(data.description)
    if offplatform_flagged:
        raise HTTPException(status_code=400, detail=OFFPLATFORM_BLOCK_MESSAGE)
    
    listing_doc = {
        "id": listing_id,
        "user_id": user["id"],
        "record_id": data.record_id,
        "discogs_id": data.discogs_id,
        "artist": data.artist,
        "album": data.album,
        "cover_url": data.cover_url,
        "year": data.year,
        "condition": data.condition,
        "pressing_notes": data.pressing_notes,
        "listing_type": data.listing_type,
        "price": data.price,
        "shipping_cost": data.shipping_cost,
        "description": data.description,
        "photo_urls": data.photo_urls,
        "insured": data.insured,
        "international_shipping": data.international_shipping or False,
        "international_shipping_cost": data.international_shipping_cost if (data.international_shipping) else None,
        "offplatform_flagged": offplatform_flagged,
        "status": "ACTIVE",
        "created_at": now
    }
    await db.listings.insert_one(listing_doc)

    # Check for ISO matches and notify
    iso_matches = await db.iso_items.find({
        "status": "OPEN",
        "user_id": {"$ne": user["id"]},
        "$or": [
            {"discogs_id": data.discogs_id} if data.discogs_id else {"_id": None},
            {"artist": {"$regex": data.artist, "$options": "i"}, "album": {"$regex": data.album, "$options": "i"}}
        ]
    }, {"_id": 0}).to_list(100)

    for iso in iso_matches:
        iso_user = await db.users.find_one({"id": iso["user_id"]}, {"_id": 0})
        if iso_user:
            await create_notification(iso_user["id"], "WANTLIST_MATCH", "Record found!",
                                      f"{data.album} by {data.artist} is now listed in the Honeypot",
                                      {"listing_id": listing_id})
            if iso_user.get("email"):
                from templates.emails import wantlist_match
                tpl = wantlist_match(iso_user.get("username", ""), data.album or "", data.artist or "", user.get("username", ""), str(data.price or ""), f"{FRONTEND_URL}/honeypot/listing/{listing_id}")
                await send_email_fire_and_forget(iso_user["email"], tpl["subject"], tpl["html"])

    # BLOCK 425: Listing Alert matching — notify users who subscribed for this release
    if data.discogs_id:
        alerts = await db.listing_alerts.find({
            "discogs_id": data.discogs_id, "status": "ACTIVE", "user_id": {"$ne": user["id"]}
        }, {"_id": 0}).to_list(100)
        for alert in alerts:
            alert_user = await db.users.find_one({"id": alert["user_id"]}, {"_id": 0})
            if alert_user:
                album_display = alert.get("album_name") or data.album or "a record"
                await create_notification(
                    alert_user["id"], "LISTING_ALERT",
                    "Good news!",
                    f"{album_display} is now available in the Honeypot.",
                    {"listing_id": listing_id, "discogs_id": data.discogs_id}
                )
                if alert_user.get("email"):
                    from templates.emails import listing_alert_email
                    tpl = listing_alert_email(
                        username=alert_user.get("username", ""),
                        album=data.album or "",
                        artist=data.artist or "",
                        cover_url=data.cover_url or alert.get("cover_url", ""),
                        listing_url=f"{FRONTEND_URL}/honeypot/listing/{listing_id}",
                    )
                    await send_email_fire_and_forget(alert_user["email"], tpl["subject"], tpl["html"])
            # Mark as fulfilled — one-time trigger
            await db.listing_alerts.update_one(
                {"id": alert["id"]}, {"$set": {"status": "FULFILLED", "fulfilled_at": datetime.now(timezone.utc).isoformat()}}
            )
    
    # Send listing confirmed email to seller
    if user.get("email"):
        from templates.emails import listing_confirmed
        tpl = listing_confirmed(
            username=user.get("username", ""),
            album=data.album or "",
            artist=data.artist or "",
            condition=data.condition or "",
            price=str(data.price or ""),
            listing_type=data.listing_type or "",
            listing_url=f"{FRONTEND_URL}/honeypot/listing/{listing_id}",
        )
        await send_email_fire_and_forget(user["email"], tpl["subject"], tpl["html"])

    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url"), "country": user.get("country"), "title_label": user.get("title_label"), "golden_hive": user.get("golden_hive", False)}
    
    # Auto-create a Hive post for this listing
    post_id = str(uuid.uuid4())
    post_type = "listing_sale" if data.listing_type == "BUY_NOW" or data.listing_type == "MAKE_OFFER" else "listing_trade"
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": post_type,
        "content": f"Just listed {data.album} by {data.artist} {'for sale' if 'sale' in post_type else 'for trade'} on the Honeypot",
        "record_title": data.album,
        "record_artist": data.artist,
        "cover_url": data.photo_urls[0] if data.photo_urls else None,
        "listing_id": listing_id,
        "created_at": now,
        "is_pinned": False,
    }
    await db.posts.insert_one(post_doc)
    
    return ListingResponse(**{k: v for k, v in listing_doc.items() if k != '_id'}, user=user_data)

@router.get("/listings", response_model=List[ListingResponse])
async def get_listings(listing_type: Optional[str] = None, search: Optional[str] = None, limit: int = 50, skip: int = 0, current_user: Optional[Dict] = Depends(get_current_user)):
    """Browse marketplace listings"""
    hidden_ids = await get_hidden_user_ids()
    query = {"status": "ACTIVE"}
    if hidden_ids:
        query["user_id"] = {"$nin": hidden_ids}
    if listing_type and listing_type in LISTING_TYPES:
        query["listing_type"] = listing_type
    if search:
        query["$or"] = [
            {"artist": {"$regex": search, "$options": "i"}},
            {"album": {"$regex": search, "$options": "i"}}
        ]
    
    listings = await db.listings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    buyer_country = current_user.get("country") if current_user else None
    
    result = []
    for listing in listings:
        seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0, "password_hash": 0})
        user_data = None
        if seller:
            # Filter: if no intl shipping, seller has country, buyer has country, and they differ → skip
            seller_country = seller.get("country")
            if not listing.get("international_shipping") and seller_country and buyer_country and seller_country != buyer_country:
                continue
            tx_count = await _get_seller_transaction_count(seller["id"])
            user_data = {
                "id": seller["id"],
                "username": seller["username"],
                "avatar_url": seller.get("avatar_url"),
                "rating": seller.get("rating", 5.0),
                "completed_sales": tx_count,
                "country": seller.get("country"),
                "title_label": seller.get("title_label"),
                "golden_hive": seller.get("golden_hive", False),
            }
        result.append(ListingResponse(**listing, user=user_data))
    
    return result

@router.get("/listings/my", response_model=List[ListingResponse])
async def get_my_listings(user: Dict = Depends(require_auth)):
    """Get current user's listings"""
    listings = await db.listings.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url"), "country": user.get("country"), "title_label": user.get("title_label"), "golden_hive": user.get("golden_hive", False)}
    return [ListingResponse(**l, user=user_data) for l in listings]

@router.get("/listings/iso-matches")
async def get_iso_matches(user: Dict = Depends(require_auth)):
    """Get listings that match the user's active ISOs"""
    my_isos = await db.iso_items.find({"user_id": user["id"], "status": "OPEN"}, {"_id": 0}).to_list(100)
    
    if not my_isos:
        return []
    
    # Build match conditions
    or_conditions = []
    for iso in my_isos:
        cond = {"artist": {"$regex": iso["artist"], "$options": "i"}, "album": {"$regex": iso["album"], "$options": "i"}}
        or_conditions.append(cond)
        if iso.get("discogs_id"):
            or_conditions.append({"discogs_id": iso["discogs_id"]})
    
    matches = await db.listings.find({
        "status": "ACTIVE",
        "user_id": {"$ne": user["id"]},
        "$or": or_conditions
    }, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    result = []
    for listing in matches:
        seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0, "password_hash": 0})
        user_data = {"id": seller["id"], "username": seller["username"], "avatar_url": seller.get("avatar_url"), "country": seller.get("country"), "title_label": seller.get("title_label"), "golden_hive_verified": seller.get("golden_hive_verified", False)} if seller else None
        result.append(ListingResponse(**listing, user=user_data))
    
    return result

@router.get("/listings/{listing_id}")
async def get_listing(listing_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    listing = await db.listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0, "password_hash": 0})
    seller_data = None
    if seller:
        completed_trades = await db.trades.count_documents({"$or": [{"initiator_id": seller["id"]}, {"responder_id": seller["id"]}], "status": "COMPLETED"})
        completed_sales = await db.listings.count_documents({"user_id": seller["id"], "status": "SOLD"})
        total_completed = completed_trades + completed_sales
        seller_data = {
            "id": seller["id"],
            "username": seller["username"],
            "avatar_url": seller.get("avatar_url"),
            "rating": seller.get("rating", 5.0),
            "completed_sales": total_completed,
            "city": seller.get("city"),
            "region": seller.get("region"),
            "country": seller.get("country"),
            "title_label": seller.get("title_label"),
        }

    # Similar listings by the same artist (max 5, exclude current)
    similar = await db.listings.find(
        {"artist": {"$regex": listing["artist"], "$options": "i"}, "status": "ACTIVE", "id": {"$ne": listing_id}},
        {"_id": 0}
    ).limit(5).to_list(5)
    similar_enriched = []
    for s in similar:
        s_seller = await db.users.find_one({"id": s["user_id"]}, {"_id": 0, "password_hash": 0})
        s_user = {"id": s_seller["id"], "username": s_seller["username"], "avatar_url": s_seller.get("avatar_url"), "country": s_seller.get("country"), "title_label": s_seller.get("title_label"), "golden_hive_verified": s_seller.get("golden_hive_verified", False)} if s_seller else None
        similar_enriched.append({**{k: v for k, v in s.items()}, "user": s_user})

    # Check wantlist status for current user
    on_wantlist = False
    if current_user and listing.get("artist") and listing.get("album"):
        wl = await db.iso_items.find_one({
            "user_id": current_user["id"],
            "artist": {"$regex": f"^{listing['artist']}$", "$options": "i"},
            "album": {"$regex": f"^{listing['album']}$", "$options": "i"},
        })
        on_wantlist = wl is not None

    resp = {k: v for k, v in listing.items()}
    resp["user"] = seller_data
    resp["similar_listings"] = similar_enriched
    resp["on_wantlist"] = on_wantlist
    # Ensure international_shipping_cost is always present (legacy data may not have it)
    if "international_shipping_cost" not in resp:
        resp["international_shipping_cost"] = None
    if "shipping_cost" not in resp:
        resp["shipping_cost"] = None
    return resp

@router.delete("/listings/{listing_id}")
async def delete_listing(listing_id: str, user: Dict = Depends(require_auth)):
    listing = await db.listings.find_one({"id": listing_id, "user_id": user["id"]})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    await db.listings.delete_one({"id": listing_id})
    return {"message": "Listing deleted"}


@router.put("/listings/{listing_id}", response_model=ListingResponse)
async def update_listing(listing_id: str, data: ListingUpdate, user: Dict = Depends(require_auth)):
    """Update a listing. Only the owner can edit. Only ACTIVE listings can be edited."""
    listing = await db.listings.find_one({"id": listing_id, "user_id": user["id"]}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("status") != "ACTIVE":
        raise HTTPException(status_code=400, detail="Only active listings can be edited")

    update_fields = {}
    if data.price is not None:
        # New seller restriction
        if data.price > 150:
            tx_count = await _get_seller_transaction_count(user["id"])
            if tx_count < 3:
                raise HTTPException(status_code=400, detail="New sellers can list items up to $150. Complete 3 transactions to unlock higher value listings.")
        update_fields["price"] = data.price
    if data.shipping_cost is not None:
        update_fields["shipping_cost"] = data.shipping_cost
    if data.description is not None:
        # Fuzzy off-platform detection — block save if detected
        offplatform_flagged, offplatform_keywords_found = detect_offplatform_payment(data.description)
        if offplatform_flagged:
            raise HTTPException(status_code=400, detail=OFFPLATFORM_BLOCK_MESSAGE)
        update_fields["description"] = data.description
        update_fields["offplatform_flagged"] = False
    if data.condition is not None:
        update_fields["condition"] = data.condition
    if data.pressing_notes is not None:
        update_fields["pressing_notes"] = data.pressing_notes
    if data.listing_type is not None:
        update_fields["listing_type"] = data.listing_type
    if data.photo_urls is not None:
        if len(data.photo_urls) == 0:
            raise HTTPException(status_code=400, detail="At least 1 photo is required")
        update_fields["photo_urls"] = data.photo_urls
    if data.insured is not None:
        update_fields["insured"] = data.insured
    if data.international_shipping is not None:
        update_fields["international_shipping"] = data.international_shipping
        if not data.international_shipping:
            update_fields["international_shipping_cost"] = None
    if data.international_shipping_cost is not None:
        update_fields["international_shipping_cost"] = data.international_shipping_cost
    if data.color_variant is not None:
        update_fields["color_variant"] = data.color_variant

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.listings.update_one({"id": listing_id}, {"$set": update_fields})

    updated = await db.listings.find_one({"id": listing_id}, {"_id": 0})
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url"), "country": user.get("country"), "title_label": user.get("title_label"), "golden_hive": user.get("golden_hive", False)}
    return ListingResponse(**{k: v for k, v in updated.items() if k != '_id'}, user=user_data)


# ============== STRIPE CONNECT & PAYMENTS ==============


@router.post("/stripe/connect")
async def stripe_connect_onboarding(user: Dict = Depends(require_auth)):
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if u.get("stripe_connected") and u.get("stripe_charges_enabled"):
        raise HTTPException(status_code=400, detail="Stripe already connected")

    stripe_sdk.api_key = STRIPE_API_KEY
    now = datetime.now(timezone.utc).isoformat()

    # Reuse existing account or create a new Express account
    account_id = u.get("stripe_account_id")
    if not account_id or account_id.startswith("acct_sim_"):
        try:
            account = stripe_sdk.Account.create(
                type="express",
                email=u.get("email"),
                metadata={"user_id": user["id"], "username": u.get("username", "")},
            )
            account_id = account.id
        except stripe_sdk.error.InvalidRequestError as e:
            if "signed up for Connect" in str(e):
                raise HTTPException(status_code=400,
                    detail="Stripe Connect is not enabled on this platform. The account owner must enable Connect at https://dashboard.stripe.com/connect before sellers can onboard.")
            raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
        await db.users.update_one({"id": user["id"]}, {"$set": {
            "stripe_account_id": account_id,
            "stripe_connected": False,
            "stripe_charges_enabled": False,
            "stripe_onboarding_started": now,
        }})

    # Create an account link for onboarding — always use production URL
    frontend_url = FRONTEND_URL
    account_link = stripe_sdk.AccountLink.create(
        account=account_id,
        refresh_url=f"{frontend_url}/stripe/connect/refresh?user_id={user['id']}",
        return_url=f"{frontend_url}/stripe/connect/return?user_id={user['id']}",
        type="account_onboarding",
    )

    return {"url": account_link.url, "account_id": account_id}


@router.get("/stripe/connect/verify")
async def stripe_connect_verify(user_id: str):
    """Called by frontend after Stripe redirects back. Verifies account and updates DB."""
    u = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    stripe_sdk.api_key = STRIPE_API_KEY
    account_id = u.get("stripe_account_id")
    charges_enabled = False
    if account_id:
        try:
            account = stripe_sdk.Account.retrieve(account_id)
            charges_enabled = account.charges_enabled
        except Exception as e:
            logger.error(f"Stripe account retrieve failed: {e}")

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": user_id}, {"$set": {
        "stripe_connected": True,
        "stripe_charges_enabled": charges_enabled,
        "stripe_connected_at": now,
    }})

    if charges_enabled:
        await create_notification(user_id, "STRIPE_CONNECTED", "Stripe Connected!",
                                  "Your Stripe account is now active. You can receive payments for marketplace sales.")

    return {"charges_enabled": charges_enabled, "account_id": account_id}


@router.get("/stripe/connect/return")
async def stripe_connect_return(user_id: str):
    """Legacy return endpoint — redirects to frontend return page."""
    frontend_url = FRONTEND_URL
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=f"{frontend_url}/stripe/connect/return?user_id={user_id}")


@router.get("/stripe/connect/refresh")
async def stripe_connect_refresh(user_id: str, request: Request):
    """Legacy refresh endpoint — redirects to frontend refresh page."""
    frontend_url = FRONTEND_URL
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=f"{frontend_url}/stripe/connect/refresh?user_id={user_id}")


@router.get("/stripe/connect/refresh-link")
async def stripe_connect_refresh_link(user_id: str):
    """Generate a new onboarding link for an existing account."""
    u = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not u or not u.get("stripe_account_id"):
        raise HTTPException(status_code=404, detail="User not found or no Stripe account")

    stripe_sdk.api_key = STRIPE_API_KEY
    frontend_url = FRONTEND_URL
    account_link = stripe_sdk.AccountLink.create(
        account=u["stripe_account_id"],
        refresh_url=f"{frontend_url}/stripe/connect/refresh?user_id={user_id}",
        return_url=f"{frontend_url}/stripe/connect/return?user_id={user_id}",
        type="account_onboarding",
    )
    return {"url": account_link.url}


@router.get("/stripe/status")
async def stripe_connect_status(user: Dict = Depends(require_auth)):
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})

    # Re-check charges_enabled from Stripe if account exists but not yet enabled
    account_id = u.get("stripe_account_id")
    charges_enabled = u.get("stripe_charges_enabled", False)
    if account_id and not charges_enabled:
        try:
            stripe_sdk.api_key = STRIPE_API_KEY
            account = stripe_sdk.Account.retrieve(account_id)
            charges_enabled = account.charges_enabled
            if charges_enabled:
                await db.users.update_one({"id": user["id"]}, {"$set": {"stripe_charges_enabled": True}})
        except Exception:
            pass

    return {
        "stripe_connected": charges_enabled,
        "stripe_account_id": account_id,
    }


@router.post("/stripe/disconnect")
async def stripe_disconnect(user: Dict = Depends(require_auth)):
    """Disconnect the user's Stripe account from HoneyGroove."""
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not u or not u.get("stripe_account_id"):
        raise HTTPException(status_code=400, detail="No Stripe account connected")
    # Check for active listings or pending payouts
    active_listings = await db.listings.count_documents({"user_id": user["id"], "status": "ACTIVE"})
    if active_listings > 0:
        raise HTTPException(status_code=400, detail=f"Please remove your {active_listings} active listing(s) before disconnecting Stripe.")
    await db.users.update_one({"id": user["id"]}, {"$set": {
        "stripe_connected": False,
        "stripe_charges_enabled": False,
        "stripe_account_id": None,
    }})
    return {"message": "Stripe disconnected"}



@router.post("/payments/checkout")
async def create_payment_checkout(request: Request, body: Dict, user: Dict = Depends(require_auth)):
    listing_id = body.get("listing_id")
    offer_amount = body.get("offer_amount")

    # ── ATOMIC INVENTORY LOCK ──
    # Atomically claim the listing: only succeeds if status is still ACTIVE
    listing = await db.listings.find_one_and_update(
        {"id": listing_id, "status": "ACTIVE"},
        {"$set": {"status": "PENDING", "locked_at": datetime.now(timezone.utc).isoformat(), "locked_by": user["id"]}},
        return_document=False,  # returns the BEFORE-update doc
    )
    if listing:
        listing.pop("_id", None)
    if not listing:
        raise HTTPException(status_code=409, detail="This honey has already been claimed!")
    if listing["user_id"] == user["id"]:
        # Rollback — can't buy your own listing
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        raise HTTPException(status_code=400, detail="Cannot buy your own listing")
    if listing["listing_type"] in ("BUY_NOW", "SALE"):
        amount = float(listing.get("price") or 0)
        if amount < 0.01:
            await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
            raise HTTPException(status_code=400, detail="Listing price is invalid. Minimum price is $0.01.")
    elif listing["listing_type"] == "MAKE_OFFER" and offer_amount:
        amount = float(offer_amount)
        if amount < 0.01:
            await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
            raise HTTPException(status_code=400, detail="Offer amount must be at least $0.01.")
    else:
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        raise HTTPException(status_code=400, detail="Invalid listing type or missing offer amount")

    # Verify seller has Stripe Connect account with charges enabled
    seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0})
    if not seller or not seller.get("stripe_account_id"):
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        raise HTTPException(status_code=400, detail="Seller has not connected their Stripe account")
    if not seller.get("stripe_charges_enabled"):
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        raise HTTPException(status_code=400, detail="Seller's Stripe account is not fully set up yet")
    
    # International shipping check
    if not listing.get("international_shipping"):
        seller_country = seller.get("country")
        buyer_country = user.get("country")
        if seller_country and buyer_country and seller_country != buyer_country:
            await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
            raise HTTPException(status_code=400, detail="This seller only ships domestically. International shipping is not available for this listing.")

    fee_pct = await _get_platform_fee_percent()
    platform_fee = round(amount * fee_pct / 100, 2)
    amount_cents = int(round(amount * 100))
    fee_cents = int(round(platform_fee * 100))

    # Stripe requires a minimum of $0.50 USD — pad sub-$0.50 transactions
    stripe_amount_cents = max(amount_cents, 50)
    stripe_fee_cents = max(fee_cents, 1) if stripe_amount_cents > amount_cents else fee_cents

    host_url = body.get("origin_url", str(request.base_url).rstrip("/"))
    success_url = f"{host_url}/honeypot?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host_url}/honeypot?payment=cancelled"

    stripe_sdk.api_key = STRIPE_API_KEY
    try:
        session = stripe_sdk.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"{listing['album']} by {listing['artist']}"},
                    "unit_amount": stripe_amount_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            shipping_address_collection={
                "allowed_countries": [user.get("country", "US")] if user.get("country") else ["US", "GB", "CA", "AU", "DE", "FR", "JP", "NL", "SE", "IT", "ES", "BR", "MX", "NZ", "IE", "NO", "DK", "FI", "BE", "AT", "CH", "PT", "PL", "CZ", "KR", "TW", "SG", "ZA", "AR", "CL", "CO", "PH", "IN", "IL", "GR", "HU", "RO", "HR", "SK", "BG", "RS", "UA", "TH", "MY", "ID", "VN", "HK", "AE", "SA"],
            },
            payment_intent_data={
                "application_fee_amount": stripe_fee_cents,
                "transfer_data": {"destination": seller["stripe_account_id"]},
            },
            metadata={
                "listing_id": listing_id, "buyer_id": user["id"],
                "seller_id": listing["user_id"], "type": "marketplace_purchase",
                "buyer_country": user.get("country", ""),
                "original_amount_cents": str(amount_cents),
            },
        )
    except stripe_sdk.error.InvalidRequestError as e:
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        logger.error(f"Stripe validation error for listing {listing_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Payment could not be processed: {e.user_message or str(e)}")
    except stripe_sdk.error.CardError as e:
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        logger.error(f"Card error for listing {listing_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Card declined: {e.user_message or 'Please check your card details and try again.'}")
    except Exception as e:
        # ── ROLLBACK on Stripe failure ──
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        logger.error(f"Stripe checkout error, listing {listing_id} rolled back to ACTIVE: {e}")
        err_str = str(e)
        if "amount" in err_str.lower():
            raise HTTPException(status_code=400, detail="The transaction amount is too low for card processing. Please try a higher price.")
        raise HTTPException(status_code=500, detail=f"Payment processing failed. Please try again or contact support.")

    now = datetime.now(timezone.utc).isoformat()
    honey_id = await _next_honey_order_id()
    await db.payment_transactions.insert_one({
        "id": honey_id, "session_id": session.id,
        "listing_id": listing_id, "buyer_id": user["id"],
        "seller_id": listing["user_id"], "amount": amount,
        "platform_fee": platform_fee, "seller_payout": round(amount - platform_fee, 2),
        "currency": "usd", "payment_status": "PENDING",
        "type": "marketplace_purchase",
        "metadata": {"listing_id": listing_id, "seller_stripe_account": seller["stripe_account_id"]},
        "created_at": now, "updated_at": now,
    })
    return {"url": session.url, "session_id": session.id}


@router.post("/payments/create-intent")
async def create_payment_intent(request: Request, body: Dict, user: Dict = Depends(require_auth)):
    """Create a PaymentIntent for Express Checkout (Apple Pay / Google Pay) via Stripe Elements."""
    listing_id = body.get("listing_id")
    offer_amount = body.get("offer_amount")

    listing = await db.listings.find_one_and_update(
        {"id": listing_id, "status": "ACTIVE"},
        {"$set": {"status": "PENDING", "locked_at": datetime.now(timezone.utc).isoformat(), "locked_by": user["id"]}},
        return_document=False,
    )
    if listing:
        listing.pop("_id", None)
    if not listing:
        raise HTTPException(status_code=409, detail="This honey has already been claimed!")
    if listing["user_id"] == user["id"]:
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        raise HTTPException(status_code=400, detail="Cannot buy your own listing")

    if listing["listing_type"] in ("BUY_NOW", "SALE"):
        amount = float(listing.get("price") or 0)
    elif listing["listing_type"] == "MAKE_OFFER" and offer_amount:
        amount = float(offer_amount)
    else:
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        raise HTTPException(status_code=400, detail="Invalid listing type or missing offer amount")

    if amount < 0.01:
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        raise HTTPException(status_code=400, detail="Amount must be at least $0.01")

    seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0})
    if not seller or not seller.get("stripe_account_id") or not seller.get("stripe_charges_enabled"):
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        raise HTTPException(status_code=400, detail="Seller's Stripe account is not ready")

    fee_pct = await _get_platform_fee_percent()
    platform_fee = round(amount * fee_pct / 100, 2)
    amount_cents = max(int(round(amount * 100)), 50)
    fee_cents = max(int(round(platform_fee * 100)), 1)

    stripe_sdk.api_key = STRIPE_API_KEY
    try:
        intent = stripe_sdk.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            automatic_payment_methods={"enabled": True},
            application_fee_amount=fee_cents,
            transfer_data={"destination": seller["stripe_account_id"]},
            metadata={
                "listing_id": listing_id, "buyer_id": user["id"],
                "seller_id": listing["user_id"], "type": "express_purchase",
            },
        )
    except Exception as e:
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        logger.error(f"PaymentIntent creation failed for {listing_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not initialize payment. Please try again.")

    now = datetime.now(timezone.utc).isoformat()
    honey_id = await _next_honey_order_id()
    await db.payment_transactions.insert_one({
        "id": honey_id, "session_id": intent.id,
        "listing_id": listing_id, "buyer_id": user["id"],
        "seller_id": listing["user_id"], "amount": amount,
        "platform_fee": platform_fee, "seller_payout": round(amount - platform_fee, 2),
        "currency": "usd", "payment_status": "PENDING",
        "type": "express_purchase",
        "metadata": {"listing_id": listing_id, "seller_stripe_account": seller["stripe_account_id"]},
        "created_at": now, "updated_at": now,
    })

    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "amount": amount,
        "seller_stripe_account": seller["stripe_account_id"],
        "publishable_key": os.environ.get("STRIPE_PUBLISHABLE_KEY", ""),
    }


async def _finalize_payment(txn: dict):
    """Mark listing as SOLD, send notifications and emails for a completed payment."""
    listing_id = txn.get("listing_id")
    if listing_id:
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "SOLD"}})

    listing = await db.listings.find_one({"id": listing_id}, {"_id": 0}) if listing_id else None
    buyer = await db.users.find_one({"id": txn["buyer_id"]}, {"_id": 0})
    seller = await db.users.find_one({"id": txn["seller_id"]}, {"_id": 0})

    await create_notification(txn["seller_id"], "SALE_COMPLETED", "You made a sale!",
                              f"@{buyer.get('username','?')} bought {listing.get('album','?') if listing else '?'} for ${txn['amount']}. Payout: ${txn.get('seller_payout', 0)}",
                              {"listing_id": listing_id, "amount": txn["amount"]})
    await create_notification(txn["buyer_id"], "PURCHASE_COMPLETED", "Purchase confirmed!",
                              f"Your payment of ${txn['amount']} for {listing.get('album','?') if listing else '?'} is confirmed.",
                              {"listing_id": listing_id})

    if listing and seller and buyer and txn.get("type") in ("marketplace_purchase", "express_purchase"):
        fee_pct = await _get_platform_fee_percent()
        amount = float(txn.get("amount", 0))
        fee_amount = round(amount * fee_pct / 100, 2)
        payout_amount = round(amount - fee_amount, 2)
        listing_url = f"{FRONTEND_URL}/honeypot/listing/{listing_id}"
        from templates.emails import sale_confirmed_seller, sale_confirmed_buyer
        if seller.get("email"):
            tpl_s = sale_confirmed_seller(seller.get("username",""), listing.get("album",""), listing.get("artist",""), f"{amount:.2f}", f"{fee_amount:.2f}", f"{payout_amount:.2f}", f"{fee_pct:g}", listing_url)
            await send_email_fire_and_forget(seller["email"], tpl_s["subject"], tpl_s["html"])
        if buyer.get("email"):
            tpl_b = sale_confirmed_buyer(buyer.get("username",""), listing.get("album",""), listing.get("artist",""), seller.get("username",""), f"{amount:.2f}", listing_url)
            await send_email_fire_and_forget(buyer["email"], tpl_b["subject"], tpl_b["html"])



@router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request, user: Dict = Depends(require_auth)):
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn["payment_status"] in ["PAID", "FAILED", "EXPIRED"]:
        return {"status": txn["payment_status"], "amount": txn["amount"], "session_id": session_id}

    stripe_sdk.api_key = STRIPE_API_KEY
    now = datetime.now(timezone.utc).isoformat()
    new_status = "PENDING"

    try:
        if session_id.startswith("pi_"):
            # PaymentIntent-based flow (Express Checkout)
            intent = stripe_sdk.PaymentIntent.retrieve(session_id)
            if intent.status == "succeeded":
                new_status = "PAID"
            elif intent.status in ("canceled", "requires_payment_method"):
                new_status = "FAILED"
        else:
            # Checkout Session-based flow (legacy redirect)
            session = stripe_sdk.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                new_status = "PAID"
            elif session.status == "expired":
                new_status = "EXPIRED"
    except Exception:
        return {"status": txn["payment_status"], "amount": txn["amount"], "session_id": session_id}

    if new_status != txn["payment_status"]:
        await db.payment_transactions.update_one({"session_id": session_id}, {"$set": {
            "payment_status": new_status, "updated_at": now,
        }})
        if new_status == "PAID":
            await _finalize_payment(txn)

    return {"status": new_status, "amount": txn["amount"], "session_id": session_id}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body_bytes = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    now = datetime.now(timezone.utc).isoformat()

    # --- Handle PaymentIntent events (Express Checkout) via raw Stripe SDK ---
    try:
        raw_event = stripe_sdk.Webhook.construct_event(body_bytes, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        logging.error(f"Webhook signature verification failed: {e}")
        return {"received": True}

    event_type = raw_event.get("type", "")

    # PaymentIntent succeeded (Express Checkout flow)
    if event_type == "payment_intent.succeeded":
        pi = raw_event["data"]["object"]
        pi_id = pi["id"]
        txn = await db.payment_transactions.find_one({"session_id": pi_id}, {"_id": 0})
        if txn and txn["payment_status"] != "PAID":
            await db.payment_transactions.update_one({"session_id": pi_id}, {"$set": {
                "payment_status": "PAID", "updated_at": now,
            }})
            await _finalize_payment(txn)
        return {"received": True}

    # Checkout Session completed (legacy redirect flow)
    if event_type == "checkout.session.completed":
        session = raw_event["data"]["object"]
        session_id = session.get("id", "")
        payment_status = session.get("payment_status", "")
        if payment_status == "paid" and session_id:
            txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            if txn and txn["payment_status"] != "PAID":
                await db.payment_transactions.update_one({"session_id": session_id}, {"$set": {
                    "payment_status": "PAID", "updated_at": now,
                }})
                await _finalize_payment(txn)

            # Handle Golden Hive verification payments
            golden_txn = await db.golden_hive_payments.find_one({"session_id": session_id}, {"_id": 0})
            if golden_txn and golden_txn.get("payment_status") != "PAID":
                await db.golden_hive_payments.update_one(
                    {"session_id": session_id},
                    {"$set": {"payment_status": "PAID", "paid_at": now}}
                )
                await db.users.update_one(
                    {"id": golden_txn["user_id"]},
                    {"$set": {"golden_hive_status": "PAID_PENDING_UPLOAD", "golden_hive_payment_at": now}}
                )

    return {"received": True}


# ============== GOLDEN HIVE ID ==============

GOLDEN_HIVE_PRICE_CENTS = 999  # $9.99


@router.get("/golden-hive/status")
async def golden_hive_status(user: Dict = Depends(require_auth)):
    """Return the current user's Golden Hive ID verification status."""
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "golden_hive_status": 1, "golden_hive_verified": 1, "golden_hive_verified_at": 1, "golden_hive": 1, "golden_hive_payment_at": 1})
    # Check for approved via verification system
    if u.get("golden_hive"):
        return {"golden_hive_verified": True, "golden_hive_status": "APPROVED", "golden_hive_verified_at": u.get("golden_hive_verified_at")}
    return {
        "golden_hive_verified": u.get("golden_hive_verified", False),
        "golden_hive_status": u.get("golden_hive_status"),
        "golden_hive_verified_at": u.get("golden_hive_verified_at"),
        "golden_hive_payment_at": u.get("golden_hive_payment_at"),
    }


@router.post("/golden-hive/checkout")
async def golden_hive_checkout(request: Request, user: Dict = Depends(require_auth)):
    """Create a Stripe Checkout Session for Golden Hive ID verification ($9.99)."""
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if u.get("golden_hive_verified"):
        raise HTTPException(status_code=400, detail="You are already a verified Golden Hive member")
    if u.get("golden_hive_status") == "pending":
        raise HTTPException(status_code=400, detail="Your verification is already pending review")

    stripe_sdk.api_key = STRIPE_API_KEY

    # Derive redirect base URL from the request origin (handles preview + production)
    origin = request.headers.get("origin") or request.headers.get("referer", "")
    if origin:
        # Strip trailing path from referer
        from urllib.parse import urlparse
        parsed = urlparse(origin)
        redirect_base = f"{parsed.scheme}://{parsed.netloc}"
    else:
        redirect_base = FRONTEND_URL

    username = u.get("username", "")
    try:
        session = stripe_sdk.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Golden Hive ID Verification",
                        "description": "One-time identity verification for The Honey Groove",
                    },
                    "unit_amount": GOLDEN_HIVE_PRICE_CENTS,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{redirect_base}/profile/{username}?golden_hive=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{redirect_base}/profile/{username}?golden_hive=cancelled",
            metadata={"type": "golden_hive_verification", "user_id": user["id"]},
        )
    except Exception as e:
        logger.error(f"Golden Hive Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=f"Could not create checkout session. Please try again.")

    if not session.url:
        raise HTTPException(status_code=500, detail="Stripe did not return a checkout URL. Please try again.")

    now = datetime.now(timezone.utc).isoformat()
    await db.golden_hive_payments.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "session_id": session.id,
        "amount_cents": GOLDEN_HIVE_PRICE_CENTS,
        "payment_status": "PENDING",
        "created_at": now,
    })

    return {"url": session.url, "session_id": session.id}


@router.get("/golden-hive/verify-payment")
async def golden_hive_verify_payment(session_id: str, user: Dict = Depends(require_auth)):
    """Verify a Golden Hive checkout session after redirect."""
    stripe_sdk.api_key = STRIPE_API_KEY
    try:
        session = stripe_sdk.checkout.Session.retrieve(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session")

    if session.payment_status != "paid":
        return {"status": "unpaid"}

    now = datetime.now(timezone.utc).isoformat()
    # Update payment record
    await db.golden_hive_payments.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": "PAID", "stripe_payment_id": session.payment_intent, "paid_at": now}}
    )
    # Set user to paid-pending-upload (ID upload required next)
    await db.users.update_one({"id": user["id"]}, {"$set": {
        "golden_hive_status": "PAID_PENDING_UPLOAD",
        "golden_hive_payment_id": session.payment_intent,
        "golden_hive_payment_at": now,
    }})

    return {"status": "PAID_PENDING_UPLOAD", "message": "Payment confirmed. Please upload your ID to complete verification."}



@router.post("/trades/{trade_id}/pay-sweetener")
async def pay_trade_sweetener(trade_id: str, request: Request, body: Dict, user: Dict = Depends(require_auth)):
    """Create a Stripe checkout session for the sweetener payment on a trade"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "ACCEPTED":
        raise HTTPException(status_code=400, detail="Trade must be in ACCEPTED status for sweetener payment")

    boot_amount = trade.get("boot_amount")
    boot_direction = trade.get("boot_direction")
    if not boot_amount or boot_amount <= 0:
        raise HTTPException(status_code=400, detail="This trade has no sweetener")

    # Determine payer and recipient
    if boot_direction == "TO_SELLER":
        payer_id = trade["initiator_id"]
        recipient_id = trade["responder_id"]
    else:
        payer_id = trade["responder_id"]
        recipient_id = trade["initiator_id"]

    if user["id"] != payer_id:
        raise HTTPException(status_code=403, detail="You are not the sweetener payer for this trade")

    recipient = await db.users.find_one({"id": recipient_id}, {"_id": 0})
    if not recipient or not recipient.get("stripe_account_id"):
        raise HTTPException(status_code=400, detail="Recipient has not connected their Stripe account")
    if not recipient.get("stripe_charges_enabled"):
        raise HTTPException(status_code=400, detail="Recipient's Stripe account is not fully set up yet")

    amount = float(boot_amount)
    fee_pct = await _get_platform_fee_percent()
    platform_fee = round(amount * fee_pct / 100, 2)
    amount_cents = int(round(amount * 100))
    fee_cents = int(round(platform_fee * 100))

    # Stripe requires a minimum of $0.50 USD — pad sub-$0.50 transactions
    stripe_amount_cents = max(amount_cents, 50)
    stripe_fee_cents = max(fee_cents, 1) if stripe_amount_cents > amount_cents else fee_cents

    host_url = body.get("origin_url", str(request.base_url).rstrip("/"))
    success_url = f"{host_url}/honeypot?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host_url}/honeypot?payment=cancelled"

    stripe_sdk.api_key = STRIPE_API_KEY
    try:
        session = stripe_sdk.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Trade sweetener — Trade #{trade_id[:8]}"},
                    "unit_amount": stripe_amount_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            payment_intent_data={
                "application_fee_amount": stripe_fee_cents,
                "transfer_data": {"destination": recipient["stripe_account_id"]},
            },
            metadata={
                "trade_id": trade_id, "payer_id": payer_id,
                "recipient_id": recipient_id, "type": "trade_sweetener",
            },
        )
    except stripe_sdk.error.InvalidRequestError as e:
        logger.error(f"Stripe validation error for sweetener on trade {trade_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Payment could not be processed: {e.user_message or str(e)}")
    except Exception as e:
        logger.error(f"Stripe sweetener checkout error for trade {trade_id}: {e}")
        raise HTTPException(status_code=500, detail="Payment processing failed. Please try again or contact support.")

    now = datetime.now(timezone.utc).isoformat()
    honey_trade_id = await _next_honey_order_id()
    await db.payment_transactions.insert_one({
        "id": honey_trade_id, "session_id": session.id,
        "trade_id": trade_id, "buyer_id": payer_id,
        "seller_id": recipient_id, "amount": amount,
        "platform_fee": platform_fee, "seller_payout": round(amount - platform_fee, 2),
        "currency": "usd", "payment_status": "PENDING",
        "type": "trade_sweetener",
        "metadata": {"trade_id": trade_id, "recipient_stripe_account": recipient["stripe_account_id"]},
        "created_at": now, "updated_at": now,
    })
    return {"url": session.url, "session_id": session.id}


@router.get("/payments/my-sales")
async def get_my_sales(user: Dict = Depends(require_auth)):
    txns = await db.payment_transactions.find({"seller_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    total_earned = sum(t.get("seller_payout", 0) for t in txns if t.get("payment_status") == "PAID")
    total_fees = sum(t.get("platform_fee", 0) for t in txns if t.get("payment_status") == "PAID")
    return {
        "transactions": txns,
        "total_earned": round(total_earned, 2),
        "total_fees": round(total_fees, 2),
        "total_sales": sum(1 for t in txns if t.get("payment_status") == "PAID"),
    }


# ============== ORDERS (ENRICHED) ==============

async def _enrich_transactions(txns, perspective: str):
    """Enrich transactions with listing/user details for the orders page."""
    enriched = []
    for t in txns:
        item = {}
        # Copy base transaction fields
        for k in ("id", "session_id", "listing_id", "trade_id", "buyer_id", "seller_id",
                   "amount", "platform_fee", "seller_payout", "currency", "payment_status",
                   "type", "created_at", "updated_at", "shipping_status", "tracking_number",
                   "shipping_carrier"):
            if k in t:
                item[k] = t[k]

        # Order number — use HONEY-ID directly for new orders, truncate for legacy UUIDs
        order_id = t.get("id", "")
        item["order_number"] = order_id if order_id.startswith("HONEY-") else order_id[:8].upper()

        # Fetch listing details
        listing_id = t.get("listing_id")
        if listing_id:
            listing = await db.listings.find_one({"id": listing_id}, {"_id": 0, "album": 1, "artist": 1, "cover_url": 1, "photo_urls": 1, "condition": 1, "pressing_variant": 1, "price": 1, "description": 1, "listing_type": 1, "year": 1})
            if listing:
                item["album"] = listing.get("album")
                item["artist"] = listing.get("artist")
                item["cover_url"] = (listing.get("photo_urls") or [None])[0] or listing.get("cover_url")
                item["condition"] = listing.get("condition")
                item["pressing_variant"] = listing.get("pressing_variant")
                item["listing_price"] = listing.get("price")
                item["description"] = listing.get("description")
                item["listing_type"] = listing.get("listing_type")
                item["photo_urls"] = listing.get("photo_urls", [])
                item["year"] = listing.get("year")

        # Fetch counterparty user
        if perspective == "admin":
            # Admin needs both buyer and seller usernames
            buyer_user = await db.users.find_one({"id": t.get("buyer_id")}, {"_id": 0, "username": 1, "avatar_url": 1})
            seller_user = await db.users.find_one({"id": t.get("seller_id")}, {"_id": 0, "username": 1, "avatar_url": 1})
            item["buyer_username"] = buyer_user["username"] if buyer_user else t.get("buyer_id")
            item["seller_username"] = seller_user["username"] if seller_user else t.get("seller_id")
            item["counterparty"] = {}
        elif perspective == "buyer":
            other_id = t.get("seller_id")
        else:
            other_id = t.get("buyer_id")
        if perspective != "admin" and other_id:
            other_user = await db.users.find_one({"id": other_id}, {"_id": 0, "username": 1, "avatar_url": 1})
            item["counterparty"] = other_user or {}

        # Defaults
        item.setdefault("shipping_status", "NOT_SHIPPED")
        item.setdefault("tracking_number", None)
        item.setdefault("shipping_carrier", None)

        # Rating & delivery fields
        item["delivered_at"] = t.get("delivered_at")
        item["rating_deadline"] = t.get("rating_deadline")
        item["buyer_rating"] = t.get("buyer_rating")
        item["seller_rating"] = t.get("seller_rating")
        item["order_status"] = t.get("order_status")
        item["payout_status"] = t.get("payout_status")
        item["dispute"] = t.get("dispute")
        item["total"] = t.get("amount")

        # Auto-complete if rating deadline has passed and not yet completed (skip disputed orders)
        if (t.get("shipping_status") == "DELIVERED"
            and t.get("rating_deadline")
            and not t.get("order_status")
            and not t.get("dispute")
            and datetime.now(timezone.utc) > datetime.fromisoformat(t["rating_deadline"])):
            await db.payment_transactions.update_one(
                {"id": t["id"], "order_status": {"$exists": False}},
                {"$set": {"order_status": "COMPLETED", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            item["order_status"] = "COMPLETED"

        enriched.append(item)
    return enriched


@router.get("/orders/purchases")
async def get_my_purchases(user: Dict = Depends(require_auth)):
    """Get current user's purchases (as buyer)."""
    txns = await db.payment_transactions.find(
        {"buyer_id": user["id"], "type": "marketplace_purchase"}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return await _enrich_transactions(txns, "buyer")


@router.get("/orders/sales")
async def get_my_orders_sales(user: Dict = Depends(require_auth)):
    """Get current user's sales (as seller)."""
    txns = await db.payment_transactions.find(
        {"seller_id": user["id"], "type": "marketplace_purchase"}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return await _enrich_transactions(txns, "seller")


@router.put("/orders/{order_id}/shipping")
async def update_order_shipping(order_id: str, body: Dict, user: Dict = Depends(require_auth)):
    """Seller updates shipping status and tracking info for an order."""
    txn = await db.payment_transactions.find_one({"id": order_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Order not found")
    if txn["seller_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the seller can update shipping")

    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if "shipping_status" in body:
        allowed = ["NOT_SHIPPED", "SHIPPED", "DELIVERED"]
        if body["shipping_status"] not in allowed:
            raise HTTPException(status_code=400, detail=f"shipping_status must be one of: {allowed}")
        update["shipping_status"] = body["shipping_status"]
    if "tracking_number" in body:
        update["tracking_number"] = body["tracking_number"]
    if "shipping_carrier" in body:
        update["shipping_carrier"] = body["shipping_carrier"]

    await db.payment_transactions.update_one({"id": order_id}, {"$set": update})

    # Record delivered_at timestamp for auto-payout cron
    if update.get("shipping_status") == "DELIVERED":
        now_dt = datetime.now(timezone.utc)
        rating_deadline = (now_dt + timedelta(hours=48)).isoformat()
        await db.payment_transactions.update_one(
            {"id": order_id, "delivered_at": {"$exists": False}},
            {"$set": {
                "delivered_at": now_dt.isoformat(),
                "payout_status": "PENDING",
                "rating_deadline": rating_deadline,
            }}
        )
        # Notify both buyer and seller
        listing = await db.listings.find_one({"id": txn.get("listing_id")}, {"_id": 0, "album": 1})
        album_name = listing.get("album", "your order") if listing else "your order"
        await create_notification(txn["buyer_id"], "ORDER_DELIVERED",
            "Your order was delivered!",
            f"{album_name} has been delivered. Please rate the seller within 48 hours.",
            {"order_id": order_id})
        await create_notification(txn["seller_id"], "ORDER_DELIVERED",
            "Your sale was delivered!",
            f"{album_name} has been delivered to the buyer. Please rate the buyer within 48 hours.",
            {"order_id": order_id})

    # Notify buyer if shipped
    if update.get("shipping_status") == "SHIPPED":
        listing = await db.listings.find_one({"id": txn.get("listing_id")}, {"_id": 0, "album": 1})
        album_name = listing.get("album", "your order") if listing else "your order"
        tracking = body.get("tracking_number")
        msg = f"{album_name} has been shipped!"
        if tracking:
            msg += f" Tracking: {tracking}"
        await create_notification(txn["buyer_id"], "ORDER_SHIPPED", "Your order shipped!", msg, {"order_id": order_id})

    return {"message": "Shipping updated"}


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, user: Dict = Depends(require_auth)):
    """Seller cancels an order and issues a Stripe refund to the buyer."""
    txn = await db.payment_transactions.find_one({"id": order_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Order not found")
    if txn["seller_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the seller can cancel an order")
    if txn.get("payment_status") == "CANCELLED":
        raise HTTPException(status_code=400, detail="Order is already cancelled")
    if txn.get("payment_status") not in ("PAID", "PENDING"):
        raise HTTPException(status_code=400, detail="Order cannot be cancelled in its current state")

    now = datetime.now(timezone.utc).isoformat()
    refund_id = None

    # Attempt Stripe refund if payment was completed
    if txn.get("payment_status") == "PAID" and txn.get("session_id"):
        stripe_sdk.api_key = STRIPE_API_KEY
        try:
            session = stripe_sdk.checkout.Session.retrieve(txn["session_id"])
            if session.payment_intent:
                refund = stripe_sdk.Refund.create(
                    payment_intent=session.payment_intent,
                    reverse_transfer=True,
                )
                refund_id = refund.id
        except Exception as e:
            logger.error(f"Stripe refund failed for order {order_id}: {e}")
            raise HTTPException(status_code=500, detail="Refund failed. Please try again or contact support.")

    # Update transaction status
    await db.payment_transactions.update_one({"id": order_id}, {"$set": {
        "payment_status": "CANCELLED",
        "shipping_status": "NOT_SHIPPED",
        "refund_id": refund_id,
        "cancelled_at": now,
        "updated_at": now,
    }})

    # Re-activate the listing so it can be sold again
    if txn.get("listing_id"):
        await db.listings.update_one({"id": txn["listing_id"]}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})

    # Notify buyer
    listing = await db.listings.find_one({"id": txn.get("listing_id")}, {"_id": 0, "album": 1})
    album_name = listing.get("album", "your order") if listing else "your order"
    await create_notification(
        txn["buyer_id"], "ORDER_CANCELLED",
        "Order cancelled",
        f"The seller cancelled your order for {album_name}. A refund has been initiated.",
        {"order_id": order_id}
    )

    return {"message": "Order cancelled and refund initiated", "refund_id": refund_id}


@router.post("/orders/{order_id}/rate")
async def rate_order(order_id: str, body: Dict, user: Dict = Depends(require_auth)):
    """Rate a completed order. Both buyer and seller can rate within 48 hours of delivery."""
    txn = await db.payment_transactions.find_one({"id": order_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Order not found")

    is_buyer = txn["buyer_id"] == user["id"]
    is_seller = txn["seller_id"] == user["id"]
    if not is_buyer and not is_seller:
        raise HTTPException(status_code=403, detail="Not a party to this order")

    if txn.get("shipping_status") != "DELIVERED" and txn.get("order_status") != "COMPLETED":
        raise HTTPException(status_code=400, detail="Order must be delivered before rating")

    role = "buyer" if is_buyer else "seller"
    rating_key = f"{role}_rating"
    if txn.get(rating_key):
        raise HTTPException(status_code=400, detail="You have already rated this order")

    # Check rating window
    rating_deadline = txn.get("rating_deadline")
    if rating_deadline:
        deadline_dt = datetime.fromisoformat(rating_deadline)
        if datetime.now(timezone.utc) > deadline_dt:
            raise HTTPException(status_code=400, detail="The 48-hour rating window has expired")

    # Validate rating
    stars = body.get("stars")
    if not stars or not (1 <= int(stars) <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5 stars")

    now = datetime.now(timezone.utc).isoformat()
    rating_data = {
        "stars": int(stars),
        "comment": (body.get("comment") or "").strip()[:500],
        "rated_at": now,
    }

    update_fields = {rating_key: rating_data, "updated_at": now}

    # Check if both parties have now rated → auto-complete
    other_key = "seller_rating" if is_buyer else "buyer_rating"
    if txn.get(other_key):
        update_fields["order_status"] = "COMPLETED"

    await db.payment_transactions.update_one({"id": order_id}, {"$set": update_fields})

    # Notify the other party
    other_id = txn["seller_id"] if is_buyer else txn["buyer_id"]
    await create_notification(other_id, "ORDER_RATED",
        "You received a rating",
        f"{'The buyer' if is_buyer else 'The seller'} rated your transaction {stars} stars.",
        {"order_id": order_id})

    return {"message": "Rating submitted", "rating": rating_data}


# ============== SALE DISPUTE SYSTEM ==============

SALE_DISPUTE_REASONS = [
    "record_not_as_described",
    "damaged_during_shipping",
    "wrong_record_sent",
    "missing_item",
    "counterfeit_fake_pressing",
]

@router.post("/orders/{order_id}/dispute")
async def open_sale_dispute(order_id: str, body: Dict, user: Dict = Depends(require_auth)):
    """Buyer opens a dispute on a sale within 48 hours of delivery."""
    txn = await db.payment_transactions.find_one({"id": order_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only buyer can dispute a sale
    if txn["buyer_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the buyer can open a dispute")

    # Must be delivered
    if txn.get("shipping_status") != "DELIVERED":
        raise HTTPException(status_code=400, detail="Order must be delivered before opening a dispute")

    # Check if already disputed
    if txn.get("dispute"):
        raise HTTPException(status_code=400, detail="A dispute is already open on this order")

    # Check 48-hour window
    delivered_at = txn.get("delivered_at")
    if delivered_at:
        delivery_time = datetime.fromisoformat(delivered_at)
        if datetime.now(timezone.utc) > delivery_time + timedelta(hours=48):
            raise HTTPException(status_code=400, detail="The 48-hour dispute window has expired")

    # Validate reason
    reason = body.get("reason", "")
    if reason not in SALE_DISPUTE_REASONS:
        raise HTTPException(status_code=400, detail=f"Invalid reason. Must be one of: {SALE_DISPUTE_REASONS}")

    # Require photo evidence
    photo_urls = body.get("photo_urls", [])
    if not photo_urls or len(photo_urls) == 0:
        raise HTTPException(status_code=400, detail="Photo evidence is required to open a dispute")

    now = datetime.now(timezone.utc).isoformat()
    evidence_deadline = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    dispute = {
        "opened_by": user["id"],
        "reason": reason,
        "photo_urls": photo_urls,
        "description": (body.get("description") or "").strip()[:1000],
        "opened_at": now,
        "evidence_deadline": evidence_deadline,
        "response": None,
        "resolution": None,
    }

    # Freeze payout and set dispute status
    await db.payment_transactions.update_one({"id": order_id}, {"$set": {
        "dispute": dispute,
        "order_status": "DISPUTE_OPEN",
        "payout_status": "PAYOUT_ON_HOLD",
        "updated_at": now,
    }})

    # Notify both parties
    listing = await db.listings.find_one({"id": txn.get("listing_id")}, {"_id": 0, "album": 1})
    album_name = listing.get("album", "your order") if listing else "your order"

    await create_notification(txn["buyer_id"], "SALE_DISPUTE_OPENED",
        "Dispute opened",
        f"Your dispute for {album_name} has been filed. Funds are on hold while we review.",
        {"order_id": order_id})
    await create_notification(txn["seller_id"], "SALE_DISPUTE_OPENED",
        "A dispute has been opened",
        f"The buyer has opened a dispute for {album_name}. Payout is temporarily on hold.",
        {"order_id": order_id})

    # Notify admin
    await create_notification("admin", "SALE_DISPUTE",
        "Sale dispute filed",
        f"Order {txn.get('order_number', order_id[:8])} — payout frozen, admin review needed",
        {"order_id": order_id})

    return {"message": "Dispute opened. Payout is on hold pending review.", "dispute": dispute}


@router.post("/orders/{order_id}/dispute/respond")
async def respond_sale_dispute(order_id: str, body: Dict, user: Dict = Depends(require_auth)):
    """Seller responds to a sale dispute with their side."""
    txn = await db.payment_transactions.find_one({"id": order_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Order not found")

    if txn["seller_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the seller can respond to a dispute")

    dispute = txn.get("dispute")
    if not dispute:
        raise HTTPException(status_code=400, detail="No dispute found")
    if dispute.get("response"):
        raise HTTPException(status_code=400, detail="Already responded to this dispute")

    now = datetime.now(timezone.utc).isoformat()
    dispute["response"] = {
        "by_user_id": user["id"],
        "text": (body.get("response_text") or "").strip()[:1000],
        "photo_urls": body.get("photo_urls", []),
        "responded_at": now,
    }

    await db.payment_transactions.update_one({"id": order_id}, {"$set": {
        "dispute": dispute, "updated_at": now,
    }})

    return {"message": "Response submitted"}


@router.get("/admin/sale-disputes")
async def get_admin_sale_disputes(user: Dict = Depends(require_auth)):
    """List all open sale disputes for admin review."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    txns = await db.payment_transactions.find(
        {"order_status": "DISPUTE_OPEN"}, {"_id": 0}
    ).sort("updated_at", -1).to_list(100)
    return await _enrich_transactions(txns, "admin")


@router.get("/admin/sale-disputes/all")
async def get_all_sale_disputes(user: Dict = Depends(require_auth)):
    """List all sales that have had disputes (including resolved)."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    txns = await db.payment_transactions.find(
        {"dispute": {"$ne": None}}, {"_id": 0}
    ).sort("updated_at", -1).to_list(200)
    return await _enrich_transactions(txns, "admin")


@router.post("/admin/sale-disputes/{order_id}/resolve")
async def resolve_sale_dispute(order_id: str, body: Dict, user: Dict = Depends(require_auth)):
    """Admin resolves a sale dispute. Outcome: approved (buyer wins) or rejected (seller wins)."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    txn = await db.payment_transactions.find_one({"id": order_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Order not found")
    if txn.get("order_status") != "DISPUTE_OPEN":
        raise HTTPException(status_code=400, detail="Order does not have an open dispute")

    outcome = body.get("outcome")  # "approved" or "rejected"
    if outcome not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Outcome must be 'approved' or 'rejected'")

    now = datetime.now(timezone.utc).isoformat()
    notes = (body.get("notes") or "").strip()

    dispute = txn.get("dispute", {})
    dispute["resolution"] = {
        "outcome": outcome,
        "notes": notes,
        "resolved_by": user["id"],
        "resolved_at": now,
    }

    listing = await db.listings.find_one({"id": txn.get("listing_id")}, {"_id": 0, "album": 1})
    album_name = listing.get("album", "the order") if listing else "the order"

    if outcome == "approved":
        # Buyer wins — issue refund, seller does not get payout
        refund_id = None
        if txn.get("session_id"):
            stripe_sdk.api_key = STRIPE_API_KEY
            try:
                session = stripe_sdk.checkout.Session.retrieve(txn["session_id"])
                if session.payment_intent:
                    refund = stripe_sdk.Refund.create(
                        payment_intent=session.payment_intent,
                        reverse_transfer=True,
                    )
                    refund_id = refund.id
            except Exception as e:
                logger.error(f"Dispute refund failed for order {order_id}: {e}")

        await db.payment_transactions.update_one({"id": order_id}, {"$set": {
            "dispute": dispute,
            "order_status": "DISPUTE_RESOLVED",
            "payout_status": "CANCELLED",
            "refund_id": refund_id,
            "updated_at": now,
        }})

        # Notify buyer: refund
        await create_notification(txn["buyer_id"], "SALE_DISPUTE_RESOLVED",
            "Dispute resolved in your favor",
            f"Your dispute for {album_name} was approved. A refund has been initiated.",
            {"order_id": order_id})
        # Notify seller: no payout
        await create_notification(txn["seller_id"], "SALE_DISPUTE_RESOLVED",
            "Dispute resolved",
            f"The dispute for {album_name} was resolved in favor of the buyer. No payout will be issued.",
            {"order_id": order_id})

        # Flag seller for abuse tracking
        await db.users.update_one({"id": txn["seller_id"]}, {"$inc": {"dispute_losses": 1}})

    else:
        # Seller wins — payout proceeds
        await db.payment_transactions.update_one({"id": order_id}, {"$set": {
            "dispute": dispute,
            "order_status": "COMPLETED",
            "payout_status": "PENDING",
            "updated_at": now,
        }})

        await create_notification(txn["buyer_id"], "SALE_DISPUTE_RESOLVED",
            "Dispute resolved",
            f"Your dispute for {album_name} was reviewed. The seller's listing was found to be accurate.",
            {"order_id": order_id})
        await create_notification(txn["seller_id"], "SALE_DISPUTE_RESOLVED",
            "Dispute resolved in your favor",
            f"The dispute for {album_name} was resolved in your favor. Payout will proceed.",
            {"order_id": order_id})

        # Flag buyer for abuse tracking
        await db.users.update_one({"id": txn["buyer_id"]}, {"$inc": {"dispute_losses": 1}})

    return {"message": f"Dispute resolved: {outcome}", "dispute": dispute}


@router.get("/seller/stats")
async def get_seller_stats(user: Dict = Depends(require_auth)):
    """Get current user's seller stats (transaction count) for listing restriction checks."""
    tx_count = await _get_seller_transaction_count(user["id"])
    return {"completed_transactions": tx_count}


# ============== PAYOUT ESTIMATOR ==============

@router.post("/estimate-payout")
async def estimate_payout(body: Dict, user: Dict = Depends(require_auth)):
    """
    Calculate Take Home Honey for a seller.
    Inner Hive sellers (founding_member) → 4% fee, all others → 6%.
    """
    price = float(body.get("price", 0))
    shipping_cost = float(body.get("shipping_cost", 0))
    if price <= 0:
        return {"price": 0, "fee_percent": 0, "fee_amount": 0, "shipping_cost": 0, "take_home": 0}

    is_inner_hive = user.get("founding_member", False)
    fee_percent = 4.0 if is_inner_hive else await _get_platform_fee_percent()
    fee_amount = round(price * fee_percent / 100, 2)
    take_home = round(price - fee_amount - shipping_cost, 2)

    return {
        "price": price,
        "fee_percent": fee_percent,
        "fee_amount": fee_amount,
        "shipping_cost": shipping_cost,
        "take_home": max(take_home, 0),
        "is_inner_hive": is_inner_hive,
    }


# ============== ADMIN OFF-PLATFORM ALERTS ==============

@router.get("/admin/offplatform-alerts")
async def get_offplatform_alerts(user: Dict = Depends(require_auth)):
    """Get all off-platform payment alerts for admin review."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    alerts = await db.offplatform_alerts.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return alerts


@router.put("/admin/offplatform-alerts/{alert_id}/dismiss")
async def dismiss_offplatform_alert(alert_id: str, user: Dict = Depends(require_auth)):
    """Dismiss an off-platform alert."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.offplatform_alerts.update_one(
        {"id": alert_id},
        {"$set": {"status": "dismissed", "dismissed_by": user["id"], "dismissed_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "dismissed"}





# ============== ADMIN PLATFORM SETTINGS ==============

@router.get("/admin/platform-settings")
async def admin_get_settings(user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    fee = await _get_platform_fee_percent()
    return {"platform_fee_percent": fee}


@router.put("/admin/platform-settings")
async def admin_update_settings(data: dict, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    fee = data.get("platform_fee_percent")
    if fee is None or not (0 <= float(fee) <= 50):
        raise HTTPException(status_code=400, detail="Fee must be between 0 and 50")
    await db.platform_settings.update_one(
        {"key": "platform_fee_percent"},
        {"$set": {"key": "platform_fee_percent", "value": float(fee)}},
        upsert=True,
    )
    return {"platform_fee_percent": float(fee), "message": "Fee updated successfully"}
