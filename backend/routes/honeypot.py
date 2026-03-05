from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from database import db, require_auth, get_current_user, security, logger, create_notification
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, PLATFORM_FEE_PERCENT, FRONTEND_URL
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from database import oauth_request_tokens, import_progress, EMERGENT_KEY
from models import *
import stripe as stripe_sdk
from fastapi.responses import Response

router = APIRouter()

# ============== ISO ROUTES ==============

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
    isos = await db.iso_items.find(
        {"user_id": {"$ne": user["id"]}, "status": "OPEN"}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    user_ids = list({iso["user_id"] for iso in isos})
    users = {u["id"]: u for u in await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(100)} if user_ids else {}
    result = []
    for iso in isos:
        iso_user = users.get(iso["user_id"])
        iso["user"] = {"id": iso_user["id"], "username": iso_user.get("username"), "avatar_url": iso_user.get("avatar_url")} if iso_user else None
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
    now = datetime.now(timezone.utc).isoformat()
    listing_id = str(uuid.uuid4())
    
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
        "description": data.description,
        "photo_urls": data.photo_urls,
        "status": "ACTIVE",
        "created_at": now
    }
    await db.listings.insert_one(listing_doc)
    
    # Check for ISO matches
    iso_matches = await db.iso_items.find({
        "status": "OPEN",
        "user_id": {"$ne": user["id"]},
        "$or": [
            {"discogs_id": data.discogs_id} if data.discogs_id else {"_id": None},
            {"artist": {"$regex": data.artist, "$options": "i"}, "album": {"$regex": data.album, "$options": "i"}}
        ]
    }, {"_id": 0}).to_list(100)
    
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")}
    return ListingResponse(**{k: v for k, v in listing_doc.items() if k != '_id'}, user=user_data)

@router.get("/listings", response_model=List[ListingResponse])
async def get_listings(listing_type: Optional[str] = None, search: Optional[str] = None, limit: int = 50, skip: int = 0):
    """Browse marketplace listings"""
    query = {"status": "ACTIVE"}
    if listing_type and listing_type in LISTING_TYPES:
        query["listing_type"] = listing_type
    if search:
        query["$or"] = [
            {"artist": {"$regex": search, "$options": "i"}},
            {"album": {"$regex": search, "$options": "i"}}
        ]
    
    listings = await db.listings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    result = []
    for listing in listings:
        seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0, "password_hash": 0})
        user_data = {"id": seller["id"], "username": seller["username"], "avatar_url": seller.get("avatar_url")} if seller else None
        result.append(ListingResponse(**listing, user=user_data))
    
    return result

@router.get("/listings/my", response_model=List[ListingResponse])
async def get_my_listings(user: Dict = Depends(require_auth)):
    """Get current user's listings"""
    listings = await db.listings.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")}
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
        user_data = {"id": seller["id"], "username": seller["username"], "avatar_url": seller.get("avatar_url")} if seller else None
        result.append(ListingResponse(**listing, user=user_data))
    
    return result

@router.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str):
    listing = await db.listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0, "password_hash": 0})
    user_data = {"id": seller["id"], "username": seller["username"], "avatar_url": seller.get("avatar_url")} if seller else None
    return ListingResponse(**listing, user=user_data)

@router.delete("/listings/{listing_id}")
async def delete_listing(listing_id: str, user: Dict = Depends(require_auth)):
    listing = await db.listings.find_one({"id": listing_id, "user_id": user["id"]})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    await db.listings.delete_one({"id": listing_id})
    return {"message": "Listing deleted"}


# ============== STRIPE CONNECT & PAYMENTS ==============


@router.post("/stripe/connect")
async def stripe_connect_onboarding(request: Request, user: Dict = Depends(require_auth)):
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if u.get("stripe_connected"):
        raise HTTPException(status_code=400, detail="Stripe already connected")

    host_url = str(request.base_url).rstrip("/")
    account_id = f"acct_sim_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc).isoformat()

    await db.users.update_one({"id": user["id"]}, {"$set": {
        "stripe_account_id": account_id,
        "stripe_connected": False,
        "stripe_onboarding_started": now,
    }})

    return_url = f"{host_url}/api/stripe/connect/return?user_id={user['id']}"
    return {"url": return_url, "account_id": account_id}


@router.get("/stripe/connect/return")
async def stripe_connect_return(user_id: str):
    u = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": user_id}, {"$set": {
        "stripe_connected": True,
        "stripe_connected_at": now,
    }})
    await create_notification(user_id, "STRIPE_CONNECTED", "Stripe Connected!",
                              "Your Stripe account is now active. You can receive payments for marketplace sales.")
    frontend_url = os.environ.get("FRONTEND_URL", "")
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=f"{frontend_url}/profile/{u['username']}?stripe=connected")


@router.get("/stripe/status")
async def stripe_connect_status(user: Dict = Depends(require_auth)):
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    return {
        "stripe_connected": u.get("stripe_connected", False),
        "stripe_account_id": u.get("stripe_account_id"),
    }


@router.post("/payments/checkout")
async def create_payment_checkout(request: Request, body: Dict, user: Dict = Depends(require_auth)):
    listing_id = body.get("listing_id")
    offer_amount = body.get("offer_amount")
    listing = await db.listings.find_one({"id": listing_id, "status": "ACTIVE"}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or not active")
    if listing["user_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot buy your own listing")
    if listing["listing_type"] == "BUY_NOW":
        amount = float(listing["price"])
    elif listing["listing_type"] == "MAKE_OFFER" and offer_amount:
        amount = float(offer_amount)
    else:
        raise HTTPException(status_code=400, detail="Invalid listing type or missing offer amount")

    # Verify seller has Stripe Connect account
    seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0})
    if not seller or not seller.get("stripe_account_id"):
        raise HTTPException(status_code=400, detail="Seller has not connected their Stripe account")

    platform_fee = round(amount * PLATFORM_FEE_PERCENT / 100, 2)
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
            payment_intent_data={
                "application_fee_amount": fee_cents,
                "transfer_data": {"destination": seller["stripe_account_id"]},
            },
            metadata={
                "listing_id": listing_id, "buyer_id": user["id"],
                "seller_id": listing["user_id"], "type": "marketplace_purchase",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe checkout error: {str(e)}")

    now = datetime.now(timezone.utc).isoformat()
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()), "session_id": session.id,
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
            await create_notification(txn["seller_id"], "SALE_COMPLETED", "You made a sale!",
                                      f"@{buyer.get('username','?')} bought {listing.get('album','?')} for ${txn['amount']}. Payout: ${txn['seller_payout']}",
                                      {"listing_id": txn["listing_id"], "amount": txn["amount"]})
            await create_notification(txn["buyer_id"], "PURCHASE_COMPLETED", "Purchase confirmed!",
                                      f"Your payment of ${txn['amount']} for {listing.get('album','?')} is confirmed.",
                                      {"listing_id": txn["listing_id"]})

    return {"status": new_status, "amount": txn["amount"], "session_id": session_id}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body_bytes = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    webhook_url = f"{str(request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    try:
        event = await stripe_checkout.handle_webhook(body_bytes, sig)
        if event.payment_status == "paid" and event.session_id:
            now = datetime.now(timezone.utc).isoformat()
            txn = await db.payment_transactions.find_one({"session_id": event.session_id}, {"_id": 0})
            if txn and txn["payment_status"] != "PAID":
                await db.payment_transactions.update_one({"session_id": event.session_id}, {"$set": {
                    "payment_status": "PAID", "updated_at": now,
                }})
                await db.listings.update_one({"id": txn["listing_id"]}, {"$set": {"status": "SOLD"}})
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
        payer_id = trade["proposer_id"]
        recipient_id = trade["receiver_id"]
    else:
        payer_id = trade["receiver_id"]
        recipient_id = trade["proposer_id"]

    if user["id"] != payer_id:
        raise HTTPException(status_code=403, detail="You are not the sweetener payer for this trade")

    recipient = await db.users.find_one({"id": recipient_id}, {"_id": 0})
    if not recipient or not recipient.get("stripe_account_id"):
        raise HTTPException(status_code=400, detail="Recipient has not connected their Stripe account")

    amount = float(boot_amount)
    platform_fee = round(amount * PLATFORM_FEE_PERCENT / 100, 2)
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
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()), "session_id": session.id,
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


