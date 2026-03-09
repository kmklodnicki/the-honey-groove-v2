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

# Off-platform payment keywords to detect
OFFPLATFORM_KEYWORDS = ["venmo", "paypal", "cashapp", "zelle", "wire transfer", "western union", "bank transfer"]


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
        "status": data.status or "WISHLIST",
        "priority": data.priority or "LOW",
        "created_at": now,
    }
    await db.iso_items.insert_one(iso_doc)
    return ISOResponse(**iso_doc)

@router.get("/iso", response_model=List[ISOResponse])
async def get_my_isos(user: Dict = Depends(require_auth)):
    isos = await db.iso_items.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    result = []
    for iso in isos:
        record_data = None
        if iso.get("record_id"):
            record_data = await db.records.find_one({"id": iso["record_id"]}, {"_id": 0})
        result.append(ISOResponse(**iso, record=record_data))
    return result

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

    # Off-platform payment detection — scan description
    offplatform_flagged = False
    offplatform_keywords_found = []
    if data.description:
        desc_lower = data.description.lower()
        for kw in OFFPLATFORM_KEYWORDS:
            if kw in desc_lower:
                offplatform_flagged = True
                offplatform_keywords_found.append(kw)
    
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
        "offplatform_flagged": offplatform_flagged,
        "status": "ACTIVE",
        "created_at": now
    }
    await db.listings.insert_one(listing_doc)

    # Log off-platform alert for admin
    if offplatform_flagged:
        await db.offplatform_alerts.insert_one({
            "id": str(uuid.uuid4()),
            "listing_id": listing_id,
            "user_id": user["id"],
            "username": user.get("username", ""),
            "keywords": offplatform_keywords_found,
            "description_snippet": (data.description[:200] + "...") if len(data.description) > 200 else data.description,
            "status": "open",
            "created_at": now,
        })
    
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
                tpl = wantlist_match(iso_user.get("username", ""), data.album or "", data.artist or "", user.get("username", ""), str(data.price or ""), f"https://thehoneygroove.com/honeypot/listing/{listing_id}")
                await send_email_fire_and_forget(iso_user["email"], tpl["subject"], tpl["html"])
    
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
            listing_url=f"https://thehoneygroove.com/honeypot/listing/{listing_id}",
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
        user_data = {"id": seller["id"], "username": seller["username"], "avatar_url": seller.get("avatar_url"), "country": seller.get("country"), "title_label": seller.get("title_label")} if seller else None
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
        s_user = {"id": s_seller["id"], "username": s_seller["username"], "avatar_url": s_seller.get("avatar_url"), "country": s_seller.get("country"), "title_label": s_seller.get("title_label")} if s_seller else None
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
    return resp

@router.delete("/listings/{listing_id}")
async def delete_listing(listing_id: str, user: Dict = Depends(require_auth)):
    listing = await db.listings.find_one({"id": listing_id, "user_id": user["id"]})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    await db.listings.delete_one({"id": listing_id})
    return {"message": "Listing deleted"}


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
    frontend_url = FRONTEND_URL or "https://thehoneygroove.com"
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
    frontend_url = FRONTEND_URL or "https://thehoneygroove.com"
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=f"{frontend_url}/stripe/connect/return?user_id={user_id}")


@router.get("/stripe/connect/refresh")
async def stripe_connect_refresh(user_id: str, request: Request):
    """Legacy refresh endpoint — redirects to frontend refresh page."""
    frontend_url = FRONTEND_URL or "https://thehoneygroove.com"
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=f"{frontend_url}/stripe/connect/refresh?user_id={user_id}")


@router.get("/stripe/connect/refresh-link")
async def stripe_connect_refresh_link(user_id: str):
    """Generate a new onboarding link for an existing account."""
    u = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not u or not u.get("stripe_account_id"):
        raise HTTPException(status_code=404, detail="User not found or no Stripe account")

    stripe_sdk.api_key = STRIPE_API_KEY
    frontend_url = FRONTEND_URL or "https://thehoneygroove.com"
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
    if listing["listing_type"] == "BUY_NOW":
        amount = float(listing["price"])
    elif listing["listing_type"] == "MAKE_OFFER" and offer_amount:
        amount = float(offer_amount)
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
                    "unit_amount": amount_cents,
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
                "application_fee_amount": fee_cents,
                "transfer_data": {"destination": seller["stripe_account_id"]},
            },
            metadata={
                "listing_id": listing_id, "buyer_id": user["id"],
                "seller_id": listing["user_id"], "type": "marketplace_purchase",
                "buyer_country": user.get("country", ""),
            },
        )
    except Exception as e:
        # ── ROLLBACK on Stripe failure ──
        await db.listings.update_one({"id": listing_id}, {"$set": {"status": "ACTIVE"}, "$unset": {"locked_at": "", "locked_by": ""}})
        logger.error(f"Stripe checkout error, listing {listing_id} rolled back to ACTIVE: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe checkout error: {str(e)}")

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


@router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request, user: Dict = Depends(require_auth)):
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn["payment_status"] in ["PAID", "FAILED", "EXPIRED"]:
        return {"status": txn["payment_status"], "amount": txn["amount"], "session_id": session_id}

    stripe_sdk.api_key = STRIPE_API_KEY
    try:
        session = stripe_sdk.checkout.Session.retrieve(session_id)
        now = datetime.now(timezone.utc).isoformat()
        new_status = "PENDING"
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
            await db.listings.update_one({"id": txn["listing_id"]}, {"$set": {"status": "SOLD"}})
            listing = await db.listings.find_one({"id": txn["listing_id"]}, {"_id": 0})
            buyer = await db.users.find_one({"id": txn["buyer_id"]}, {"_id": 0})
            seller = await db.users.find_one({"id": txn["seller_id"]}, {"_id": 0})
            await create_notification(txn["seller_id"], "SALE_COMPLETED", "You made a sale!",
                                      f"@{buyer.get('username','?')} bought {listing.get('album','?')} for ${txn['amount']}. Payout: ${txn['seller_payout']}",
                                      {"listing_id": txn["listing_id"], "amount": txn["amount"]})
            await create_notification(txn["buyer_id"], "PURCHASE_COMPLETED", "Purchase confirmed!",
                                      f"Your payment of ${txn['amount']} for {listing.get('album','?')} is confirmed.",
                                      {"listing_id": txn["listing_id"]})
            # Send sale confirmed emails
            if listing and seller and buyer and txn.get("type") == "marketplace_purchase":
                fee_pct = await _get_platform_fee_percent()
                amount = float(txn.get("amount", 0))
                fee_amount = round(amount * fee_pct / 100, 2)
                payout_amount = round(amount - fee_amount, 2)
                listing_url = f"https://thehoneygroove.com/honeypot/listing/{txn['listing_id']}"
                from templates.emails import sale_confirmed_seller, sale_confirmed_buyer
                if seller.get("email"):
                    tpl_s = sale_confirmed_seller(seller.get("username",""), listing.get("album",""), listing.get("artist",""), f"{amount:.2f}", f"{fee_amount:.2f}", f"{payout_amount:.2f}", f"{fee_pct:g}", listing_url)
                    await send_email_fire_and_forget(seller["email"], tpl_s["subject"], tpl_s["html"])
                if buyer.get("email"):
                    tpl_b = sale_confirmed_buyer(buyer.get("username",""), listing.get("album",""), listing.get("artist",""), seller.get("username",""), f"{amount:.2f}", listing_url)
                    await send_email_fire_and_forget(buyer["email"], tpl_b["subject"], tpl_b["html"])

    return {"status": new_status, "amount": txn["amount"], "session_id": session_id}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body_bytes = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    webhook_url = f"{str(request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_secret=STRIPE_WEBHOOK_SECRET, webhook_url=webhook_url)
    try:
        event = await stripe_checkout.handle_webhook(body_bytes, sig)
        if event.payment_status == "paid" and event.session_id:
            now = datetime.now(timezone.utc).isoformat()
            txn = await db.payment_transactions.find_one({"session_id": event.session_id}, {"_id": 0})
            if txn and txn["payment_status"] != "PAID":
                await db.payment_transactions.update_one({"session_id": event.session_id}, {"$set": {
                    "payment_status": "PAID", "updated_at": now,
                }})
                listing_id = txn.get("listing_id")
                if listing_id:
                    await db.listings.update_one({"id": listing_id}, {"$set": {"status": "SOLD"}})

                # Send sale confirmed emails to seller and buyer
                if txn.get("type") == "marketplace_purchase" and listing_id:
                    listing = await db.listings.find_one({"id": listing_id}, {"_id": 0})
                    seller = await db.users.find_one({"id": txn["seller_id"]}, {"_id": 0})
                    buyer = await db.users.find_one({"id": txn["buyer_id"]}, {"_id": 0})
                    if listing and seller and buyer:
                        fee_pct = await _get_platform_fee_percent()
                        amount = float(txn.get("amount", 0))
                        fee_amount = round(amount * fee_pct / 100, 2)
                        payout_amount = round(amount - fee_amount, 2)
                        album = listing.get("album", "")
                        artist = listing.get("artist", "")
                        listing_url = f"https://thehoneygroove.com/honeypot/listing/{listing_id}"

                        from templates.emails import sale_confirmed_seller, sale_confirmed_buyer
                        if seller.get("email"):
                            tpl_s = sale_confirmed_seller(
                                username=seller.get("username", ""),
                                album=album, artist=artist,
                                price=f"{amount:.2f}",
                                fee_amount=f"{fee_amount:.2f}",
                                payout_amount=f"{payout_amount:.2f}",
                                fee_pct=f"{fee_pct:g}",
                                sale_url=listing_url,
                            )
                            await send_email_fire_and_forget(seller["email"], tpl_s["subject"], tpl_s["html"])
                        if buyer.get("email"):
                            tpl_b = sale_confirmed_buyer(
                                username=buyer.get("username", ""),
                                album=album, artist=artist,
                                seller_username=seller.get("username", ""),
                                price=f"{amount:.2f}",
                                purchase_url=listing_url,
                            )
                            await send_email_fire_and_forget(buyer["email"], tpl_b["subject"], tpl_b["html"])
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return {"received": True}


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
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            payment_intent_data={
                "application_fee_amount": fee_cents,
                "transfer_data": {"destination": recipient["stripe_account_id"]},
            },
            metadata={
                "trade_id": trade_id, "payer_id": payer_id,
                "recipient_id": recipient_id, "type": "trade_sweetener",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe checkout error: {str(e)}")

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
        if perspective == "buyer":
            other_id = t.get("seller_id")
        else:
            other_id = t.get("buyer_id")
        if other_id:
            other_user = await db.users.find_one({"id": other_id}, {"_id": 0, "username": 1, "avatar_url": 1})
            item["counterparty"] = other_user or {}

        # Defaults
        item.setdefault("shipping_status", "NOT_SHIPPED")
        item.setdefault("tracking_number", None)
        item.setdefault("shipping_carrier", None)
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
        await db.payment_transactions.update_one(
            {"id": order_id, "delivered_at": {"$exists": False}},
            {"$set": {"delivered_at": datetime.now(timezone.utc).isoformat(), "payout_status": "PENDING"}}
        )

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
