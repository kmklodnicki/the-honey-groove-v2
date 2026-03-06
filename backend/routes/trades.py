from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from database import db, require_auth, get_current_user, security, logger, create_notification
from services.email_service import send_email_fire_and_forget
import templates.emails as email_tpl
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, PLATFORM_FEE_PERCENT, FRONTEND_URL
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from database import oauth_request_tokens, import_progress, EMERGENT_KEY
from models import *
import stripe as stripe_sdk

router = APIRouter()

# ============== TRADE ROUTES ==============

async def check_trade_deadlines(trade: Dict) -> Dict:
    """Lazy deadline checker - evaluates on access"""
    now = datetime.now(timezone.utc)

    if trade.get("status") == "SHIPPING" and trade.get("shipping_deadline"):
        deadline = datetime.fromisoformat(trade["shipping_deadline"])
        if now > deadline:
            shipping = trade.get("shipping") or {}
            init_shipped = shipping.get("initiator") is not None
            resp_shipped = shipping.get("responder") is not None
            if not init_shipped or not resp_shipped:
                trade["shipping_overdue"] = True

    if trade.get("status") == "CONFIRMING" and trade.get("confirmation_deadline"):
        deadline = datetime.fromisoformat(trade["confirmation_deadline"])
        if now > deadline:
            confirmations = trade.get("confirmations") or {}
            if any(confirmations.values()):
                from contextlib import suppress
                with suppress(Exception):
                    await complete_trade(trade)
                    trade["status"] = "COMPLETED"

    return trade


async def complete_trade(trade: Dict):
    """Transfer records and mark trade as completed"""
    now = datetime.now(timezone.utc).isoformat()
    initiator_id = trade["initiator_id"]
    responder_id = trade["responder_id"]
    offered_id = trade["offered_record_id"]

    listing = await db.listings.find_one({"id": trade["listing_id"]}, {"_id": 0})

    # Transfer offered record: initiator -> responder
    await db.records.update_one({"id": offered_id}, {"$set": {"user_id": responder_id}})

    # Transfer listing record: responder -> initiator
    if listing and listing.get("record_id"):
        await db.records.update_one({"id": listing["record_id"]}, {"$set": {"user_id": initiator_id}})

    # Mark trade completed
    await db.trades.update_one({"id": trade["id"]}, {"$set": {
        "status": "COMPLETED", "updated_at": now, "completed_at": now,
    }})

    # Mark listing as TRADED
    if listing:
        await db.listings.update_one({"id": listing["id"]}, {"$set": {"status": "TRADED"}})


async def build_trade_response(trade: Dict) -> Dict:
    """Populate a trade document with user and record data"""
    # Lazy deadline check
    trade = await check_trade_deadlines(trade)

    initiator = await db.users.find_one({"id": trade["initiator_id"]}, {"_id": 0, "password_hash": 0})
    responder = await db.users.find_one({"id": trade["responder_id"]}, {"_id": 0, "password_hash": 0})
    offered_record = await db.records.find_one({"id": trade["offered_record_id"]}, {"_id": 0})
    listing = await db.listings.find_one({"id": trade["listing_id"]}, {"_id": 0})

    listing_record = None
    if listing:
        listing_record = {
            "artist": listing.get("artist"),
            "album": listing.get("album"),
            "cover_url": listing.get("cover_url"),
            "year": listing.get("year"),
            "condition": listing.get("condition"),
            "photo_urls": listing.get("photo_urls", []),
        }

    counter_record = None
    if trade.get("counter") and trade["counter"].get("record_id"):
        counter_record = await db.records.find_one({"id": trade["counter"]["record_id"]}, {"_id": 0})

    def user_summary(u):
        if not u:
            return None
        return {"id": u["id"], "username": u["username"], "avatar_url": u.get("avatar_url")}

    return {
        **{k: v for k, v in trade.items() if k != "_id"},
        "initiator": user_summary(initiator),
        "responder": user_summary(responder),
        "offered_record": offered_record,
        "listing_record": listing_record,
        "counter_record": counter_record,
        "listing": listing,
    }


@router.post("/trades", response_model=TradeResponse)
async def propose_trade(data: TradePropose, user: Dict = Depends(require_auth)):
    """Propose a trade against a TRADE listing"""
    listing = await db.listings.find_one({"id": data.listing_id, "status": "ACTIVE"}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or no longer active")
    if listing["listing_type"] != "TRADE":
        raise HTTPException(status_code=400, detail="This listing is not open for trades")
    if listing["user_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot trade with yourself")

    # Verify offered record belongs to the initiator
    record = await db.records.find_one({"id": data.offered_record_id, "user_id": user["id"]}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Offered record not found in your collection")

    # Check for existing pending trade on this listing by this user
    existing = await db.trades.find_one({
        "listing_id": data.listing_id,
        "initiator_id": user["id"],
        "status": {"$in": ["PROPOSED", "COUNTERED"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending trade on this listing")

    now = datetime.now(timezone.utc).isoformat()
    trade_id = str(uuid.uuid4())

    messages = []
    if data.message:
        messages.append({"user_id": user["id"], "text": data.message, "created_at": now})

    trade_doc = {
        "id": trade_id,
        "listing_id": data.listing_id,
        "initiator_id": user["id"],
        "responder_id": listing["user_id"],
        "offered_record_id": data.offered_record_id,
        "offered_condition": data.offered_condition,
        "offered_photo_urls": data.offered_photo_urls or [],
        "listing_record_id": listing.get("record_id"),
        "boot_amount": data.boot_amount,
        "boot_direction": data.boot_direction,
        "status": "PROPOSED",
        "messages": messages,
        "counter": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.trades.insert_one(trade_doc)

    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    await create_notification(listing["user_id"], "TRADE_PROPOSED", "New trade proposal",
                              f"@{u.get('username','?')} wants to trade for your {listing.get('album','listing')}",
                              {"trade_id": trade_id})
    responder = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0})
    if responder and responder.get("email"):
        sweetener = str(data.boot_amount) if data.boot_amount else ""
        tpl = email_tpl.new_trade_offer(responder.get("username", ""), u.get("username", ""), listing.get("album", "your listing"), record.get("title", "a record"), sweetener, "https://thehoneygroove.com/honeypot")
        await send_email_fire_and_forget(responder["email"], tpl["subject"], tpl["html"])

    return await build_trade_response(trade_doc)


@router.get("/trades")
async def get_my_trades(status_filter: Optional[str] = None, user: Dict = Depends(require_auth)):
    """Get all trades where user is initiator or responder"""
    query = {"$or": [{"initiator_id": user["id"]}, {"responder_id": user["id"]}]}
    if status_filter and status_filter in TRADE_STATUSES:
        query["status"] = status_filter
    trades = await db.trades.find(query, {"_id": 0}).sort("updated_at", -1).to_list(100)
    result = []
    for trade in trades:
        result.append(await build_trade_response(trade))
    return result


@router.get("/trades/can-initiate")
async def can_initiate_trade(user: Dict = Depends(require_auth)):
    """Check if user has mandatory pending ratings blocking new trades"""
    pending = await db.trades.find({
        "$or": [{"initiator_id": user["id"]}, {"responder_id": user["id"]}],
        "status": "COMPLETED",
    }, {"_id": 0}).to_list(100)
    unrated = []
    for trade in pending:
        ratings = trade.get("ratings") or {}
        if not ratings.get(user["id"]):
            unrated.append(trade["id"])
    return {"can_trade": len(unrated) == 0, "unrated_trade_ids": unrated}


@router.get("/trades/{trade_id}")
async def get_trade(trade_id: str, user: Dict = Depends(require_auth)):
    """Get trade detail"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this trade")
    return await build_trade_response(trade)


@router.put("/trades/{trade_id}/accept")
async def accept_trade(trade_id: str, user: Dict = Depends(require_auth)):
    """Accept a trade proposal or counter"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Determine who can accept
    if trade["status"] == "PROPOSED":
        if trade["responder_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the listing owner can accept")
    elif trade["status"] == "COUNTERED":
        if trade["initiator_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the trade proposer can accept a counter")
    else:
        raise HTTPException(status_code=400, detail=f"Cannot accept a trade with status {trade['status']}")

    now = datetime.now(timezone.utc).isoformat()

    # If accepting a counter, apply counter terms
    update = {"$set": {"status": "ACCEPTED", "updated_at": now}}
    if trade["status"] == "COUNTERED" and trade.get("counter"):
        counter = trade["counter"]
        set_fields = {"status": "ACCEPTED", "updated_at": now}
        if counter.get("record_id"):
            set_fields["offered_record_id"] = counter["record_id"]
        if counter.get("boot_amount") is not None:
            set_fields["boot_amount"] = counter["boot_amount"]
        if counter.get("boot_direction"):
            set_fields["boot_direction"] = counter["boot_direction"]
        update = {"$set": set_fields}

    await db.trades.update_one({"id": trade_id}, update)

    # Mark the listing as IN_TRADE
    await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "IN_TRADE"}})

    # Set shipping deadline (5 days from now) and transition to SHIPPING
    shipping_deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    await db.trades.update_one({"id": trade_id}, {"$set": {
        "status": "SHIPPING",
        "shipping_deadline": shipping_deadline,
        "shipping": {"initiator": None, "responder": None},
        "confirmations": {},
    }})

    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})

    # Notify the other party
    other_id = trade["initiator_id"] if user["id"] == trade["responder_id"] else trade["responder_id"]
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    await create_notification(other_id, "TRADE_ACCEPTED", "Trade accepted!",
                              f"@{u.get('username','?')} accepted the trade. Ship within 5 days!",
                              {"trade_id": trade_id})
    other_user = await db.users.find_one({"id": other_id}, {"_id": 0})
    if other_user and other_user.get("email"):
        listing = await db.listings.find_one({"id": trade["listing_id"]}, {"_id": 0})
        tpl = email_tpl.trade_accepted(other_user.get("username", ""), u.get("username", ""), listing.get("album", "the record") if listing else "your record", "https://thehoneygroove.com/honeypot")
        await send_email_fire_and_forget(other_user["email"], tpl["subject"], tpl["html"])

    return await build_trade_response(updated)


@router.put("/trades/{trade_id}/counter")
async def counter_trade(trade_id: str, data: TradeCounter, user: Dict = Depends(require_auth)):
    """Counter a trade - responder suggests different record or boot"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade["status"] not in ["PROPOSED", "COUNTERED"]:
        raise HTTPException(status_code=400, detail=f"Cannot counter a trade with status {trade['status']}")

    # Only the current "other party" can counter
    if trade["status"] == "PROPOSED" and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the listing owner can counter a proposal")
    if trade["status"] == "COUNTERED" and trade["initiator_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the proposer can counter back")

    # If requesting a different record, verify it belongs to the other party
    if data.requested_record_id:
        other_id = trade["initiator_id"] if user["id"] == trade["responder_id"] else trade["responder_id"]
        rec = await db.records.find_one({"id": data.requested_record_id, "user_id": other_id}, {"_id": 0})
        if not rec:
            raise HTTPException(status_code=404, detail="Requested record not found in the other party's collection")

    now = datetime.now(timezone.utc).isoformat()
    counter_obj = {
        "record_id": data.requested_record_id,
        "boot_amount": data.boot_amount,
        "boot_direction": data.boot_direction,
        "by_user_id": user["id"],
        "created_at": now,
    }

    messages_update = {}
    if data.message:
        messages_update = {"$push": {"messages": {"user_id": user["id"], "text": data.message, "created_at": now}}}

    await db.trades.update_one({"id": trade_id}, {
        "$set": {"status": "COUNTERED", "counter": counter_obj, "updated_at": now},
        **(messages_update if messages_update else {})
    })

    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    return await build_trade_response(updated)


@router.put("/trades/{trade_id}/decline")
async def decline_trade(trade_id: str, user: Dict = Depends(require_auth)):
    """Decline a trade"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] not in ["PROPOSED", "COUNTERED"]:
        raise HTTPException(status_code=400, detail=f"Cannot decline a trade with status {trade['status']}")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    now = datetime.now(timezone.utc).isoformat()
    await db.trades.update_one({"id": trade_id}, {"$set": {"status": "DECLINED", "updated_at": now}})
    return {"message": "Trade declined"}


@router.post("/trades/{trade_id}/message")
async def add_trade_message(trade_id: str, data: Dict, user: Dict = Depends(require_auth)):
    """Add a message to a trade"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    now = datetime.now(timezone.utc).isoformat()
    msg = {"user_id": user["id"], "text": data.get("text", ""), "created_at": now}
    await db.trades.update_one({"id": trade_id}, {"$push": {"messages": msg}, "$set": {"updated_at": now}})
    return {"message": "Message added"}



# ============== TRADE PHASE 2: SHIPPING & CONFIRMATION ==============

@router.put("/trades/{trade_id}/ship")
async def ship_trade(trade_id: str, data: TradeShipInput, user: Dict = Depends(require_auth)):
    """Upload tracking number for a trade"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "SHIPPING":
        raise HTTPException(status_code=400, detail="Trade is not in shipping status")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    now = datetime.now(timezone.utc).isoformat()
    role = "initiator" if trade["initiator_id"] == user["id"] else "responder"
    shipping = trade.get("shipping") or {"initiator": None, "responder": None}

    if shipping.get(role):
        raise HTTPException(status_code=400, detail="You have already submitted tracking info")

    shipping[role] = {
        "tracking_number": data.tracking_number,
        "carrier": data.carrier,
        "shipped_at": now,
    }

    update_fields = {"shipping": shipping, "updated_at": now}

    # Check if both parties have shipped -> move to CONFIRMING
    if shipping.get("initiator") and shipping.get("responder"):
        confirmation_deadline = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
        update_fields["status"] = "CONFIRMING"
        update_fields["confirmation_deadline"] = confirmation_deadline

    await db.trades.update_one({"id": trade_id}, {"$set": update_fields})
    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})

    # Email the other party about shipment
    other_id = trade["initiator_id"] if role == "responder" else trade["responder_id"]
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    other_user = await db.users.find_one({"id": other_id}, {"_id": 0})
    if other_user and other_user.get("email"):
        tpl = email_tpl.trade_shipped(other_user.get("username", ""), u.get("username", ""), "https://thehoneygroove.com/honeypot")
        await send_email_fire_and_forget(other_user["email"], tpl["subject"], tpl["html"])

    return await build_trade_response(updated)


@router.put("/trades/{trade_id}/confirm-receipt")
async def confirm_receipt(trade_id: str, user: Dict = Depends(require_auth)):
    """Confirm record arrived as described"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "CONFIRMING":
        raise HTTPException(status_code=400, detail="Trade is not in confirming status")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    now = datetime.now(timezone.utc).isoformat()
    confirmations = trade.get("confirmations") or {}
    confirmations[user["id"]] = True

    # Check if both confirmed
    both_confirmed = (
        confirmations.get(trade["initiator_id"]) and
        confirmations.get(trade["responder_id"])
    )

    if both_confirmed:
        await db.trades.update_one({"id": trade_id}, {"$set": {"confirmations": confirmations, "updated_at": now}})
        await complete_trade(trade)
        updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})
        return await build_trade_response(updated)
    else:
        await db.trades.update_one({"id": trade_id}, {"$set": {"confirmations": confirmations, "updated_at": now}})
        updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})
        return await build_trade_response(updated)


@router.put("/trades/{trade_id}/cancel-shipping")
async def cancel_shipping(trade_id: str, user: Dict = Depends(require_auth)):
    """Cancel trade if shipping deadline passed and partner hasn't shipped"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "SHIPPING":
        raise HTTPException(status_code=400, detail="Trade is not in shipping status")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check deadline
    if trade.get("shipping_deadline"):
        deadline = datetime.fromisoformat(trade["shipping_deadline"])
        if datetime.now(timezone.utc) < deadline:
            raise HTTPException(status_code=400, detail="Shipping deadline has not passed yet")

    # Check that the requesting user has shipped but the other hasn't
    shipping = trade.get("shipping") or {}
    role = "initiator" if trade["initiator_id"] == user["id"] else "responder"
    other_role = "responder" if role == "initiator" else "initiator"

    if not shipping.get(role):
        raise HTTPException(status_code=400, detail="You must ship before cancelling")
    if shipping.get(other_role):
        raise HTTPException(status_code=400, detail="Both parties have shipped, cannot cancel")

    now = datetime.now(timezone.utc).isoformat()
    await db.trades.update_one({"id": trade_id}, {"$set": {"status": "CANCELLED", "updated_at": now}})
    # Release listing back to active
    await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "ACTIVE"}})
    return {"message": "Trade cancelled due to shipping deadline"}



# ============== TRADE PHASE 3: DISPUTES & RATINGS ==============

@router.post("/trades/{trade_id}/dispute")
async def open_dispute(trade_id: str, data: TradeDisputeInput, user: Dict = Depends(require_auth)):
    """Open a dispute on a trade"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] not in ["CONFIRMING", "SHIPPING"]:
        raise HTTPException(status_code=400, detail="Cannot dispute a trade with this status")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if trade.get("dispute"):
        raise HTTPException(status_code=400, detail="A dispute is already open on this trade")

    now = datetime.now(timezone.utc).isoformat()
    response_deadline = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    dispute = {
        "opened_by": user["id"],
        "reason": data.reason,
        "photo_urls": data.photo_urls,
        "opened_at": now,
        "response_deadline": response_deadline,
        "response": None,
        "resolution": None,
    }

    await db.trades.update_one({"id": trade_id}, {"$set": {
        "status": "DISPUTED", "dispute": dispute, "updated_at": now,
    }})
    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    return await build_trade_response(updated)


@router.put("/trades/{trade_id}/dispute/respond")
async def respond_to_dispute(trade_id: str, data: TradeDisputeResponse, user: Dict = Depends(require_auth)):
    """Respond to a dispute"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "DISPUTED":
        raise HTTPException(status_code=400, detail="Trade is not in disputed status")
    dispute = trade.get("dispute")
    if not dispute:
        raise HTTPException(status_code=400, detail="No dispute found")
    if dispute["opened_by"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot respond to your own dispute")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if dispute.get("response"):
        raise HTTPException(status_code=400, detail="Already responded to this dispute")

    now = datetime.now(timezone.utc).isoformat()
    dispute["response"] = {
        "by_user_id": user["id"],
        "text": data.response_text,
        "photo_urls": data.photo_urls,
        "responded_at": now,
    }

    await db.trades.update_one({"id": trade_id}, {"$set": {"dispute": dispute, "updated_at": now}})
    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    return await build_trade_response(updated)


@router.post("/trades/{trade_id}/rate")
async def rate_trade(trade_id: str, data: TradeRatingInput, user: Dict = Depends(require_auth)):
    """Rate the other party after trade completion"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail="Can only rate completed trades")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    ratings = trade.get("ratings") or {}
    if ratings.get(user["id"]):
        raise HTTPException(status_code=400, detail="You have already rated this trade")

    now = datetime.now(timezone.utc).isoformat()
    other_id = trade["responder_id"] if trade["initiator_id"] == user["id"] else trade["initiator_id"]
    ratings[user["id"]] = {
        "rating": data.rating,
        "review": data.review,
        "rated_user_id": other_id,
        "created_at": now,
    }

    await db.trades.update_one({"id": trade_id}, {"$set": {"ratings": ratings, "updated_at": now}})

    # Store in separate collection for profile aggregation
    rating_doc = {
        "trade_id": trade_id,
        "rater_id": user["id"],
        "rated_user_id": other_id,
        "rating": data.rating,
        "review": data.review,
        "created_at": now,
    }
    await db.trade_ratings.insert_one(rating_doc)

    return {"message": "Rating submitted", "rating": data.rating}


@router.get("/users/{username}/ratings")
async def get_user_ratings(username: str):
    """Get trade ratings for a user's profile"""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    ratings = await db.trade_ratings.find({"rated_user_id": target["id"]}).to_list(100)
    cleaned = [{k: v for k, v in r.items() if k != "_id"} for r in ratings]
    avg = sum(r.get("rating", 0) for r in cleaned) / len(cleaned) if cleaned else 0
    return {"ratings": cleaned, "average": round(avg, 1), "count": len(cleaned)}



# ============== ADMIN ROUTES ==============

async def require_admin(user: Dict = Depends(require_auth)):
    """Check if user is admin"""
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not u or not u.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/admin/disputes")
async def get_admin_disputes(user: Dict = Depends(require_admin)):
    """List all disputed trades for admin review"""
    trades = await db.trades.find({"status": "DISPUTED"}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    result = []
    for trade in trades:
        result.append(await build_trade_response(trade))
    return result


@router.get("/admin/disputes/all")
async def get_all_disputes(user: Dict = Depends(require_admin)):
    """List all trades that have had disputes (including resolved)"""
    trades = await db.trades.find({"dispute": {"$ne": None}}, {"_id": 0}).sort("updated_at", -1).to_list(200)
    result = []
    for trade in trades:
        result.append(await build_trade_response(trade))
    return result


@router.put("/admin/disputes/{trade_id}/resolve")
async def resolve_dispute(trade_id: str, data: AdminDisputeResolve, user: Dict = Depends(require_admin)):
    """Admin resolves a dispute"""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "DISPUTED":
        raise HTTPException(status_code=400, detail="Trade is not disputed")

    now = datetime.now(timezone.utc).isoformat()
    dispute = trade.get("dispute", {})
    dispute["resolution"] = {
        "outcome": data.resolution,
        "notes": data.notes,
        "partial_amount": data.partial_amount,
        "resolved_by": user["id"],
        "resolved_at": now,
    }

    if data.resolution == "COMPLETED":
        # Force complete the trade
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "dispute": dispute, "updated_at": now,
        }})
        await complete_trade(trade)
    elif data.resolution == "CANCELLED":
        # Cancel and release listings
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "status": "CANCELLED", "dispute": dispute, "updated_at": now,
        }})
        await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "ACTIVE"}})
    else:
        # PARTIAL - mark completed with notes
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "dispute": dispute, "updated_at": now,
        }})
        await complete_trade(trade)

    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    return await build_trade_response(updated)


@router.get("/users/{username}/trades")
async def get_user_trades(username: str):
    """Get completed/active trades for a user profile"""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    trades = await db.trades.find({
        "$or": [{"initiator_id": target["id"]}, {"responder_id": target["id"]}],
        "status": {"$in": ["ACCEPTED", "COMPLETED", "SHIPPING", "CONFIRMING"]}
    }, {"_id": 0}).sort("updated_at", -1).to_list(50)
    result = []
    for trade in trades:
        result.append(await build_trade_response(trade))
    return result


