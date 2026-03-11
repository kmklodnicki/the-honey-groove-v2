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
import asyncio

router = APIRouter()

TRADE_URL = f"{FRONTEND_URL}/honeypot"


async def _refund_hold(payment_intent_id: str) -> bool:
    """Refund a captured hold payment via Stripe."""
    if not payment_intent_id or not STRIPE_API_KEY:
        return False
    try:
        stripe_sdk.api_key = STRIPE_API_KEY
        stripe_sdk.Refund.create(payment_intent=payment_intent_id)
        return True
    except Exception as e:
        logger.error(f"Hold refund failed for {payment_intent_id}: {e}")
        return False


async def _send_hold_emails(trade: Dict, template_fn, **extra_kwargs):
    """Send a hold-related email to both parties of a trade."""
    initiator = await db.users.find_one({"id": trade["initiator_id"]}, {"_id": 0})
    responder = await db.users.find_one({"id": trade["responder_id"]}, {"_id": 0})
    hold_amount = f"{trade.get('hold_amount', 0):.2f}"
    for user_obj in [initiator, responder]:
        if user_obj and user_obj.get("email"):
            tpl = template_fn(user_obj.get("username", ""), hold_amount=hold_amount, **extra_kwargs)
            await send_email_fire_and_forget(user_obj["email"], tpl["subject"], tpl["html"])


async def _auto_expire_shipping(trade: Dict):
    """Auto-expire a trade when shipping deadline passes and at least one party hasn't shipped."""
    now_str = datetime.now(timezone.utc).isoformat()

    # Release mutual holds
    if trade.get("hold_enabled") and trade.get("hold_status") == "active":
        charges = trade.get("hold_charges") or {}
        for role in ["initiator", "responder"]:
            pi_id = (charges.get(role) or {}).get("payment_intent_id")
            if pi_id:
                await _refund_hold(pi_id)
        await db.trades.update_one({"id": trade["id"]}, {"$set": {"hold_status": "refunded"}})

    # Mark trade as EXPIRED
    await db.trades.update_one({"id": trade["id"]}, {"$set": {
        "status": "EXPIRED",
        "updated_at": now_str,
        "expired_at": now_str,
        "expired_reason": "shipping_deadline",
    }})

    # Release listing back to active
    await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "ACTIVE"}})

    # Notify both users
    for uid in [trade["initiator_id"], trade["responder_id"]]:
        await create_notification(
            uid, "TRADE_EXPIRED",
            "Trade expired",
            "Your trade expired because one or both parties did not ship within the 3-day deadline. Mutual holds have been released.",
            {"trade_id": trade["id"]},
        )

    logger.info(f"Trade auto-expired: {trade['id']} — shipping deadline passed")

# ============== TRADE ROUTES ==============

async def check_trade_deadlines(trade: Dict) -> Dict:
    """Lazy deadline checker - evaluates on access"""
    now = datetime.now(timezone.utc)

    if trade.get("status") == "SHIPPING" and trade.get("shipping_deadline"):
        deadline = datetime.fromisoformat(trade["shipping_deadline"])
        grace_expiry = deadline + timedelta(hours=24)  # 96h total
        nudge_time = deadline - timedelta(hours=48)  # 24h after trade accepted

        # At 24h: send "Preparing to ship?" nudge (once)
        if now > nudge_time and not trade.get("ship_nudge_sent"):
            shipping = trade.get("shipping") or {}
            nudge_users = []
            if not shipping.get("initiator"):
                nudge_users.append(trade["initiator_id"])
            if not shipping.get("responder"):
                nudge_users.append(trade["responder_id"])
            if nudge_users:
                for uid in nudge_users:
                    await create_notification(
                        uid, "SHIP_NUDGE",
                        "Preparing to ship?",
                        "Friendly reminder — you have 48 hours left to ship your trade. Don't forget to add a tracking number!",
                        {"trade_id": trade["id"]}
                    )
                await db.trades.update_one({"id": trade["id"]}, {"$set": {"ship_nudge_sent": True}})
                trade["ship_nudge_sent"] = True

        if now > deadline:
            shipping = trade.get("shipping") or {}
            init_shipped = shipping.get("initiator") is not None
            resp_shipped = shipping.get("responder") is not None
            if not init_shipped or not resp_shipped:
                trade["shipping_overdue"] = True
                # At deadline (72h): send Late Shipping alert (once)
                if not trade.get("late_shipping_alerted"):
                    late_users = []
                    if not init_shipped:
                        late_users.append(trade["initiator_id"])
                    if not resp_shipped:
                        late_users.append(trade["responder_id"])
                    for uid in late_users:
                        await create_notification(
                            uid, "LATE_SHIPPING",
                            "Late Shipping Alert",
                            "Your trade shipment is overdue. Please ship immediately to avoid cancellation.",
                            {"trade_id": trade["id"]}
                        )
                    await db.trades.update_one({"id": trade["id"]}, {"$set": {"late_shipping_alerted": True}})
                    trade["late_shipping_alerted"] = True

                # At 96h (deadline + 24h grace): auto-expire
                if now > grace_expiry:
                    from contextlib import suppress
                    with suppress(Exception):
                        await _auto_expire_shipping(trade)
                        trade["status"] = "EXPIRED"

    if trade.get("status") == "CONFIRMING" and trade.get("delivery_marked_at"):
        delivery_time = datetime.fromisoformat(trade["delivery_marked_at"])
        elapsed = now - delivery_time
        confirmations = trade.get("confirmations") or {}
        init_confirmed = confirmations.get(trade.get("initiator_id"))
        resp_confirmed = confirmations.get(trade.get("responder_id"))

        # Scenario 3: Neither confirmed within 48h, no dispute
        if elapsed > timedelta(hours=48) and not init_confirmed and not resp_confirmed and trade.get("status") != "DISPUTED":
            from contextlib import suppress
            with suppress(Exception):
                await _auto_complete_no_confirmation(trade)
                trade["status"] = "COMPLETED"

        # Scenario 2: At least one confirmed, deadline passed
        elif elapsed > timedelta(hours=48) and (init_confirmed or resp_confirmed):
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

    # International shipping check
    if not listing.get("international_shipping"):
        seller = await db.users.find_one({"id": listing["user_id"]}, {"_id": 0, "country": 1})
        seller_country = seller.get("country") if seller else None
        buyer_country = user.get("country")
        if seller_country and buyer_country and seller_country != buyer_country:
            raise HTTPException(status_code=400, detail="This seller only ships domestically. International shipping is not available for this listing.")

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
        "hold_enabled": True,
        "hold_amount": max(data.hold_amount or 10, 10),
        "hold_status": None,
        "hold_charges": None,
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
        tpl = email_tpl.new_trade_offer(responder.get("username", ""), u.get("username", ""), listing.get("album", "your listing"), record.get("title", "a record"), sweetener, TRADE_URL)
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
    """Accept a trade proposal or counter. All trades require mutual hold."""
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
    set_fields = {"status": "ACCEPTED", "updated_at": now}
    if trade["status"] == "COUNTERED" and trade.get("counter"):
        counter = trade["counter"]
        if counter.get("record_id"):
            set_fields["offered_record_id"] = counter["record_id"]
        if counter.get("boot_amount") is not None:
            set_fields["boot_amount"] = counter["boot_amount"]
        if counter.get("boot_direction"):
            set_fields["boot_direction"] = counter["boot_direction"]

    await db.trades.update_one({"id": trade_id}, {"$set": set_fields})

    # Mark the listing as IN_TRADE
    await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "IN_TRADE"}})

    # All trades require mutual hold — move to HOLD_PENDING
    await db.trades.update_one({"id": trade_id}, {"$set": {
        "status": "HOLD_PENDING",
        "hold_enabled": True,
        "hold_status": "awaiting_payment",
        "hold_charges": {"initiator": None, "responder": None},
    }})

    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})

    # Notify the other party
    other_id = trade["initiator_id"] if user["id"] == trade["responder_id"] else trade["responder_id"]
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    msg = f"@{u.get('username','?')} accepted the trade. Pay your hold to start shipping."
    await create_notification(other_id, "TRADE_ACCEPTED", "Trade accepted!", msg, {"trade_id": trade_id})
    other_user = await db.users.find_one({"id": other_id}, {"_id": 0})
    if other_user and other_user.get("email"):
        listing = await db.listings.find_one({"id": trade["listing_id"]}, {"_id": 0})
        hold_amt = f"{trade.get('hold_amount', 0):.2f}"
        tpl = email_tpl.trade_accepted(other_user.get("username", ""), u.get("username", ""), listing.get("album", "the record") if listing else "your record", TRADE_URL, hold_amt)
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


# ============== SHIPPING ADDRESS EXCHANGE ==============

@router.put("/trades/{trade_id}/shipping-address")
async def update_shipping_address(trade_id: str, data: Dict, user: Dict = Depends(require_auth)):
    """Save shipping address for a trade party. Only visible to the other party."""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if trade["status"] not in ("HOLD_PENDING", "SHIPPING", "CONFIRMING"):
        raise HTTPException(status_code=400, detail="Shipping address can only be set after trade is accepted")

    role = "initiator" if user["id"] == trade["initiator_id"] else "responder"
    address = data.get("address", "").strip()
    if not address:
        raise HTTPException(status_code=400, detail="Address is required")

    now = datetime.now(timezone.utc).isoformat()
    await db.trades.update_one({"id": trade_id}, {
        "$set": {f"shipping_addresses.{role}": address, "updated_at": now}
    })
    return {"message": "Shipping address saved"}


@router.get("/trades/{trade_id}/shipping-address")
async def get_shipping_address(trade_id: str, user: Dict = Depends(require_auth)):
    """Get the OTHER party's shipping address (your own is shown as editable)."""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    my_role = "initiator" if user["id"] == trade["initiator_id"] else "responder"
    other_role = "responder" if my_role == "initiator" else "initiator"
    addrs = trade.get("shipping_addresses", {})

    return {
        "my_address": addrs.get(my_role, ""),
        "other_address": addrs.get(other_role, ""),
    }


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

    # Validate tracking number
    tracking = data.tracking_number.strip()
    if len(tracking) < 6:
        raise HTTPException(status_code=400, detail="Tracking number must be at least 6 characters")
    if not any(c.isalnum() for c in tracking):
        raise HTTPException(status_code=400, detail="Tracking number must contain alphanumeric characters")

    # Validate carrier if provided
    carrier_val = (data.carrier or "").strip()
    if not carrier_val:
        raise HTTPException(status_code=400, detail="Carrier is required (e.g. USPS, UPS, FedEx)")

    shipping[role] = {
        "tracking_number": tracking,
        "carrier": carrier_val,
        "shipped_at": now,
    }

    update_fields = {"shipping": shipping, "updated_at": now}

    # Check if both parties have shipped -> move to CONFIRMING
    if shipping.get("initiator") and shipping.get("responder"):
        confirmation_deadline = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
        update_fields["status"] = "CONFIRMING"
        update_fields["confirmation_deadline"] = confirmation_deadline
        update_fields["delivery_marked_at"] = now  # Timer start for auto-completion
        # For hold trades, set a 48h hold confirmation deadline
        if trade.get("hold_enabled") and trade.get("hold_status") == "active":
            hold_deadline = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
            update_fields["hold_confirmation_deadline"] = hold_deadline

    await db.trades.update_one({"id": trade_id}, {"$set": update_fields})
    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})

    # Email the other party about shipment
    other_id = trade["initiator_id"] if role == "responder" else trade["responder_id"]
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    other_user = await db.users.find_one({"id": other_id}, {"_id": 0})
    if other_user and other_user.get("email"):
        tpl = email_tpl.trade_shipped(other_user.get("username", ""), u.get("username", ""), TRADE_URL)
        await send_email_fire_and_forget(other_user["email"], tpl["subject"], tpl["html"])

    # Send hold delivery-confirmed emails when both shipped (hold trades)
    if updated.get("status") == "CONFIRMING" and trade.get("hold_enabled") and trade.get("hold_status") == "active":
        hold_amt = f"{trade.get('hold_amount', 0):.2f}"
        initiator = await db.users.find_one({"id": trade["initiator_id"]}, {"_id": 0})
        responder = await db.users.find_one({"id": trade["responder_id"]}, {"_id": 0})
        for u_obj in [initiator, responder]:
            if u_obj and u_obj.get("email"):
                tpl = email_tpl.hold_delivery_confirmed(u_obj.get("username", ""), hold_amt, TRADE_URL)
                await send_email_fire_and_forget(u_obj["email"], tpl["subject"], tpl["html"])

    return await build_trade_response(updated)


@router.put("/trades/{trade_id}/confirm-receipt")
async def confirm_receipt(trade_id: str, user: Dict = Depends(require_auth)):
    """Confirm record arrived as described. For hold trades, both confirmations trigger auto-refund."""
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

    both_confirmed = (
        confirmations.get(trade["initiator_id"]) and
        confirmations.get(trade["responder_id"])
    )

    await db.trades.update_one({"id": trade_id}, {"$set": {"confirmations": confirmations, "updated_at": now}})

    if both_confirmed:
        await complete_trade(trade)
        # If mutual hold trade, refund both holds
        if trade.get("hold_enabled") and trade.get("hold_status") == "active":
            charges = trade.get("hold_charges") or {}
            for role in ["initiator", "responder"]:
                pi_id = (charges.get(role) or {}).get("payment_intent_id")
                if pi_id:
                    await _refund_hold(pi_id)
            await db.trades.update_one({"id": trade_id}, {"$set": {"hold_status": "refunded"}})
            # Send hold reversed emails
            updated_trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
            await _send_hold_emails(updated_trade, email_tpl.hold_reversed)

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



# ============== MUTUAL HOLD TRADE ENDPOINTS ==============


@router.get("/trades/{trade_id}/hold-suggestion")
async def get_hold_suggestion(trade_id: str, user: Dict = Depends(require_auth)):
    """Calculate suggested hold amount from Discogs median values of both records."""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    offered_record = await db.records.find_one({"id": trade["offered_record_id"]}, {"_id": 0})
    listing = await db.listings.find_one({"id": trade["listing_id"]}, {"_id": 0})

    val_a, val_b = 0, 0
    if offered_record and offered_record.get("discogs_id"):
        cv = await db.collection_values.find_one({"release_id": offered_record["discogs_id"]}, {"_id": 0})
        if cv and cv.get("median_value"):
            val_a = float(cv["median_value"])
    if listing and listing.get("discogs_id"):
        cv = await db.collection_values.find_one({"release_id": listing["discogs_id"]}, {"_id": 0})
        if cv and cv.get("median_value"):
            val_b = float(cv["median_value"])

    if val_a > 0 and val_b > 0:
        suggested = round((val_a + val_b) / 2, 2)
    elif val_a > 0:
        suggested = round(val_a, 2)
    elif val_b > 0:
        suggested = round(val_b, 2)
    else:
        suggested = 50.0  # fallback when no Discogs data

    suggested = max(suggested, 10.0)  # enforce $10 minimum

    return {
        "suggested_hold": suggested,
        "record_a_value": val_a,
        "record_b_value": val_b,
        "label": f"Suggested hold: ${suggested:.2f} — roughly the estimated value of the records being traded.",
    }


@router.put("/trades/{trade_id}/hold/respond")
async def respond_to_hold(trade_id: str, data: HoldAccept, user: Dict = Depends(require_auth)):
    """Respond to a mutual hold amount: accept or counter. All trades require a hold."""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] not in ["PROPOSED", "COUNTERED"]:
        raise HTTPException(status_code=400, detail="Trade is not in a negotiable status")

    now = datetime.now(timezone.utc).isoformat()

    if data.action == "accept":
        return {"message": "Hold terms accepted. Accept the trade to proceed.", "hold_amount": trade.get("hold_amount")}
    elif data.action == "counter":
        if not data.hold_amount or data.hold_amount < 10:
            raise HTTPException(status_code=400, detail="Hold amount must be at least $10")
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "hold_amount": round(data.hold_amount, 2),
            "updated_at": now,
        }})
        return {"message": f"Hold amount updated to ${data.hold_amount:.2f}", "hold_amount": data.hold_amount}
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use: accept, counter")


@router.post("/trades/{trade_id}/hold/checkout")
async def create_hold_checkout(trade_id: str, request: Request, user: Dict = Depends(require_auth)):
    """Create a Stripe checkout session for a party's hold payment."""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "HOLD_PENDING":
        raise HTTPException(status_code=400, detail="Trade is not awaiting hold payment")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    role = "initiator" if trade["initiator_id"] == user["id"] else "responder"
    charges = trade.get("hold_charges") or {}
    if charges.get(role) and charges[role].get("status") == "paid":
        raise HTTPException(status_code=400, detail="You have already paid your hold")

    hold_amount = float(trade.get("hold_amount", 0))
    if hold_amount < 10:
        raise HTTPException(status_code=400, detail="Hold amount is below $10 minimum")

    amount_cents = int(round(hold_amount * 100))
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    host_url = body.get("origin_url", str(request.base_url).rstrip("/"))
    success_url = f"{host_url}/honeypot?hold_payment=success&trade_id={trade_id}&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host_url}/honeypot?hold_payment=cancelled&trade_id={trade_id}"

    stripe_sdk.api_key = STRIPE_API_KEY
    try:
        listing = await db.listings.find_one({"id": trade["listing_id"]}, {"_id": 0})
        album_name = listing.get("album", "Trade") if listing else "Trade"
        session = stripe_sdk.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Mutual Hold — {album_name}"},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "trade_id": trade_id, "role": role, "user_id": user["id"],
                "type": "mutual_hold",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe checkout error: {str(e)}")

    # Store the session in hold_charges
    charges[role] = {"session_id": session.id, "payment_intent_id": None, "status": "pending"}
    now = datetime.now(timezone.utc).isoformat()
    await db.trades.update_one({"id": trade_id}, {"$set": {"hold_charges": charges, "updated_at": now}})

    return {"url": session.url, "session_id": session.id}


@router.get("/trades/{trade_id}/hold/status")
async def check_hold_status(trade_id: str, user: Dict = Depends(require_auth)):
    """Check hold payment status for both parties. If both paid, transition to SHIPPING."""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "HOLD_PENDING":
        return {"status": trade["status"], "hold_status": trade.get("hold_status")}

    charges = trade.get("hold_charges") or {}
    updated = False

    stripe_sdk.api_key = STRIPE_API_KEY
    for role in ["initiator", "responder"]:
        charge = charges.get(role)
        if charge and charge.get("session_id") and charge.get("status") != "paid":
            try:
                session = stripe_sdk.checkout.Session.retrieve(charge["session_id"])
                if session.payment_status == "paid":
                    charge["status"] = "paid"
                    charge["payment_intent_id"] = session.payment_intent
                    updated = True
            except Exception:
                pass

    now = datetime.now(timezone.utc).isoformat()
    if updated:
        await db.trades.update_one({"id": trade_id}, {"$set": {"hold_charges": charges, "updated_at": now}})

    # Check if both parties have paid
    init_paid = (charges.get("initiator") or {}).get("status") == "paid"
    resp_paid = (charges.get("responder") or {}).get("status") == "paid"

    if init_paid and resp_paid:
        # Both paid — transition to SHIPPING
        shipping_deadline = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "status": "SHIPPING",
            "hold_status": "active",
            "shipping_deadline": shipping_deadline,
            "shipping": {"initiator": None, "responder": None},
            "confirmations": {},
        }})
        # Send hold activated emails
        updated_trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
        initiator = await db.users.find_one({"id": trade["initiator_id"]}, {"_id": 0})
        responder = await db.users.find_one({"id": trade["responder_id"]}, {"_id": 0})
        hold_amt = f"{trade.get('hold_amount', 0):.2f}"
        for u_obj, other_obj in [(initiator, responder), (responder, initiator)]:
            if u_obj and u_obj.get("email"):
                tpl = email_tpl.hold_activated(u_obj.get("username", ""), other_obj.get("username", ""), hold_amt, TRADE_URL)
                await send_email_fire_and_forget(u_obj["email"], tpl["subject"], tpl["html"])

        return {"status": "SHIPPING", "hold_status": "active", "initiator_paid": True, "responder_paid": True}

    return {
        "status": "HOLD_PENDING",
        "hold_status": "awaiting_payment",
        "initiator_paid": init_paid,
        "responder_paid": resp_paid,
    }


# ============== TRADE PHASE 3: DISPUTES & RATINGS ==============

@router.post("/trades/{trade_id}/dispute")
async def open_dispute(trade_id: str, data: TradeDisputeInput, user: Dict = Depends(require_auth)):
    """Open a dispute on a trade. For hold trades, freezes both holds instantly."""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] not in ["CONFIRMING", "SHIPPING"]:
        raise HTTPException(status_code=400, detail="Cannot dispute a trade with this status")
    if trade["initiator_id"] != user["id"] and trade["responder_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if trade.get("dispute"):
        raise HTTPException(status_code=400, detail="A dispute is already open on this trade")

    # Validate dispute is within 48h of delivery
    if trade.get("delivery_marked_at"):
        delivery_time = datetime.fromisoformat(trade["delivery_marked_at"])
        if datetime.now(timezone.utc) > delivery_time + timedelta(hours=48):
            raise HTTPException(status_code=400, detail="The 48-hour dispute window has expired")

    # Validate reason
    valid_reasons = ["record_not_as_described", "damaged_during_shipping", "wrong_record_sent", "missing_item", "counterfeit_fake_pressing"]
    if data.reason not in valid_reasons:
        raise HTTPException(status_code=400, detail=f"Invalid reason. Must be one of: {valid_reasons}")

    # Require photo evidence
    if not data.photo_urls or len(data.photo_urls) == 0:
        raise HTTPException(status_code=400, detail="Photo evidence is required to open a dispute")

    now = datetime.now(timezone.utc).isoformat()
    evidence_deadline = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    dispute = {
        "opened_by": user["id"],
        "reason": data.reason,
        "photo_urls": data.photo_urls,
        "opened_at": now,
        "evidence_deadline": evidence_deadline,
        "response_deadline": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
        "response": None,
        "resolution": None,
    }

    update_fields = {"status": "DISPUTED", "dispute": dispute, "updated_at": now}
    # Freeze holds if mutual hold trade
    if trade.get("hold_enabled") and trade.get("hold_status") == "active":
        update_fields["hold_status"] = "frozen"

    await db.trades.update_one({"id": trade_id}, {"$set": update_fields})

    # Send hold dispute emails to both parties
    if trade.get("hold_enabled") and trade.get("hold_amount"):
        updated_trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
        initiator = await db.users.find_one({"id": trade["initiator_id"]}, {"_id": 0})
        responder = await db.users.find_one({"id": trade["responder_id"]}, {"_id": 0})
        hold_amt = f"{trade.get('hold_amount', 0):.2f}"
        for u_obj, other_obj in [(initiator, responder), (responder, initiator)]:
            if u_obj and u_obj.get("email"):
                tpl = email_tpl.hold_dispute_filed(u_obj.get("username", ""), other_obj.get("username", ""), hold_amt, TRADE_URL)
                await send_email_fire_and_forget(u_obj["email"], tpl["subject"], tpl["html"])

    # Notify admin
    await create_notification("admin", "HOLD_DISPUTE", "Mutual Hold dispute filed",
                              f"Trade {trade_id[:8]} — hold frozen, admin review needed",
                              {"trade_id": trade_id})

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

    # Send in-app notifications to both parties
    outcome_labels = {
        "COMPLETED": "Your trade dispute has been resolved. The trade is now complete.",
        "CANCELLED": "Your trade dispute has been resolved. The trade has been cancelled.",
    }
    outcome_msg = outcome_labels.get(data.resolution, "Your trade dispute has been resolved.")
    for uid in [trade["initiator_id"], trade["responder_id"]]:
        await create_notification(uid, "DISPUTE_RESOLVED", "Trade Dispute Resolved", outcome_msg, {"trade_id": trade_id})

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
        "status": {"$in": ["ACCEPTED", "COMPLETED", "SHIPPING", "CONFIRMING", "HOLD_PENDING"]}
    }, {"_id": 0}).sort("updated_at", -1).to_list(50)
    result = []
    for trade in trades:
        result.append(await build_trade_response(trade))
    return result


# ============== ADMIN: MUTUAL HOLD DISPUTES ==============

@router.get("/admin/hold-disputes")
async def get_hold_disputes(user: Dict = Depends(require_admin)):
    """List all disputed trades with active/frozen mutual holds for admin review."""
    trades = await db.trades.find({
        "hold_enabled": True,
        "hold_status": {"$in": ["frozen", "active"]},
        "status": "DISPUTED",
    }, {"_id": 0}).sort("updated_at", -1).to_list(100)
    result = []
    for trade in trades:
        result.append(await build_trade_response(trade))
    return result


@router.put("/admin/hold-disputes/{trade_id}/resolve")
async def resolve_hold_dispute(trade_id: str, data: AdminHoldResolve, user: Dict = Depends(require_admin)):
    """Admin resolves a mutual hold dispute with one of three outcomes."""
    trade = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade["status"] != "DISPUTED":
        raise HTTPException(status_code=400, detail="Trade is not disputed")
    if not trade.get("hold_enabled"):
        raise HTTPException(status_code=400, detail="This trade does not have a mutual hold")

    now = datetime.now(timezone.utc).isoformat()
    charges = trade.get("hold_charges") or {}
    init_pi = (charges.get("initiator") or {}).get("payment_intent_id")
    resp_pi = (charges.get("responder") or {}).get("payment_intent_id")

    dispute = trade.get("dispute", {})
    dispute["resolution"] = {
        "outcome": data.resolution,
        "notes": data.notes,
        "resolved_by": user["id"],
        "resolved_at": now,
    }

    initiator = await db.users.find_one({"id": trade["initiator_id"]}, {"_id": 0})
    responder = await db.users.find_one({"id": trade["responder_id"]}, {"_id": 0})
    hold_amt = f"{trade.get('hold_amount', 0):.2f}"

    if data.resolution == "full_reversal":
        # Refund both parties
        if init_pi:
            await _refund_hold(init_pi)
        if resp_pi:
            await _refund_hold(resp_pi)
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "status": "CANCELLED", "hold_status": "refunded", "dispute": dispute, "updated_at": now,
        }})
        await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "ACTIVE"}})
        # Email both: hold reversed
        for u_obj in [initiator, responder]:
            if u_obj and u_obj.get("email"):
                tpl = email_tpl.hold_reversed(u_obj.get("username", ""), hold_amt)
                await send_email_fire_and_forget(u_obj["email"], tpl["subject"], tpl["html"])

    elif data.resolution == "penalize_initiator":
        # Keep initiator's hold (platform revenue), refund responder
        if resp_pi:
            await _refund_hold(resp_pi)
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "status": "CANCELLED", "hold_status": "penalized_initiator", "dispute": dispute, "updated_at": now,
        }})
        await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "ACTIVE"}})
        if responder and responder.get("email"):
            tpl = email_tpl.hold_reversed(responder.get("username", ""), hold_amt)
            await send_email_fire_and_forget(responder["email"], tpl["subject"], tpl["html"])

    elif data.resolution == "penalize_responder":
        # Keep responder's hold, refund initiator
        if init_pi:
            await _refund_hold(init_pi)
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "status": "CANCELLED", "hold_status": "penalized_responder", "dispute": dispute, "updated_at": now,
        }})
        await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "ACTIVE"}})
        if initiator and initiator.get("email"):
            tpl = email_tpl.hold_reversed(initiator.get("username", ""), hold_amt)
            await send_email_fire_and_forget(initiator["email"], tpl["subject"], tpl["html"])

    elif data.resolution == "partial":
        # Custom split — admin sets specific refund amounts
        if data.partial_refund_initiator and init_pi:
            try:
                stripe_sdk.api_key = STRIPE_API_KEY
                stripe_sdk.Refund.create(payment_intent=init_pi, amount=int(round(data.partial_refund_initiator * 100)))
            except Exception as e:
                logger.error(f"Partial refund failed for initiator: {e}")
        if data.partial_refund_responder and resp_pi:
            try:
                stripe_sdk.api_key = STRIPE_API_KEY
                stripe_sdk.Refund.create(payment_intent=resp_pi, amount=int(round(data.partial_refund_responder * 100)))
            except Exception as e:
                logger.error(f"Partial refund failed for responder: {e}")
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "status": "CANCELLED", "hold_status": "partial_resolved", "dispute": dispute, "updated_at": now,
        }})
        await db.listings.update_one({"id": trade["listing_id"]}, {"$set": {"status": "ACTIVE"}})
        for u_obj in [initiator, responder]:
            if u_obj and u_obj.get("email"):
                tpl = email_tpl.hold_reversed(u_obj.get("username", ""), hold_amt)
                await send_email_fire_and_forget(u_obj["email"], tpl["subject"], tpl["html"])

    elif data.resolution == "extend_investigation":
        # Keep holds frozen, extend investigation period
        extended_deadline = (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat()
        dispute["investigation_extended"] = True
        dispute["extended_deadline"] = extended_deadline
        await db.trades.update_one({"id": trade_id}, {"$set": {
            "dispute": dispute, "updated_at": now,
        }})
        # Notify both parties
        for u_obj in [initiator, responder]:
            if u_obj:
                await create_notification(
                    u_obj["id"], "DISPUTE_EXTENDED",
                    "Dispute Under Extended Review",
                    f"Your trade dispute is under extended investigation by a Honey Groove moderator. Holds remain frozen.",
                    {"trade_id": trade_id}
                )
                if u_obj.get("email"):
                    tpl = email_tpl.hold_dispute_filed(u_obj.get("username", ""), "The Honey Groove Team", hold_amt, TRADE_URL)
                    await send_email_fire_and_forget(u_obj["email"], "Your dispute is under extended review", tpl["html"])

    # Send in-app notifications for all resolutions (except extend which is handled above)
    if data.resolution != "extend_investigation":
        outcome_labels = {
            "full_reversal": "Both holds have been released. Trade cancelled.",
            "penalize_initiator": "Dispute resolved. The offender's hold has been captured.",
            "penalize_responder": "Dispute resolved. The offender's hold has been captured.",
            "partial": "Dispute resolved with a custom settlement.",
        }
        outcome_msg = outcome_labels.get(data.resolution, "Dispute resolved.")
        for u_obj in [initiator, responder]:
            if u_obj:
                await create_notification(
                    u_obj["id"], "DISPUTE_RESOLVED",
                    "Trade Dispute Resolved",
                    outcome_msg,
                    {"trade_id": trade_id}
                )

    updated = await db.trades.find_one({"id": trade_id}, {"_id": 0})
    return await build_trade_response(updated)


# ============== HOLD AUTO-REVERSAL & SCENARIO 3 AUTO-COMPLETION ==============

async def _auto_complete_no_confirmation(trade: Dict):
    """Scenario 3: Auto-complete trade when NEITHER user confirms within 48h.

    Preconditions (must be validated by caller):
    - Both packages marked delivered (trade is CONFIRMING)
    - Neither user has confirmed
    - No dispute is open
    - 48h have passed since delivery_marked_at

    Actions:
    - Mark trade as COMPLETED (transfer records)
    - Release both mutual hold payments
    - Leave ratings as null
    - Notify both users
    """
    now_str = datetime.now(timezone.utc).isoformat()

    # Release both mutual hold payments first (before completing)
    if trade.get("hold_enabled") and trade.get("hold_status") == "active":
        charges = trade.get("hold_charges") or {}
        for role in ["initiator", "responder"]:
            pi_id = (charges.get(role) or {}).get("payment_intent_id")
            if pi_id:
                await _refund_hold(pi_id)
        await db.trades.update_one({"id": trade["id"]}, {"$set": {
            "hold_status": "refunded",
            "updated_at": now_str,
        }})

    # Complete the trade (transfer records, mark COMPLETED)
    await complete_trade(trade)

    # Set auto-completion metadata
    await db.trades.update_one({"id": trade["id"]}, {"$set": {
        "confirmations": {
            trade["initiator_id"]: "auto",
            trade["responder_id"]: "auto",
        },
        "auto_completed": True,
        "auto_completed_at": now_str,
    }})

    # Notify both users
    for uid in [trade["initiator_id"], trade["responder_id"]]:
        await create_notification(
            uid, "TRADE_AUTO_COMPLETED",
            "Trade completed automatically",
            "Your trade was completed automatically after 48 hours. Your mutual holds have been released.",
            {"trade_id": trade["id"]},
        )
        user_obj = await db.users.find_one({"id": uid}, {"_id": 0})
        if user_obj and user_obj.get("email"):
            hold_amt = f"{trade.get('hold_amount', 0):.2f}"
            tpl = email_tpl.trade_auto_completed(user_obj.get("username", ""), hold_amt, TRADE_URL)
            await send_email_fire_and_forget(user_obj["email"], tpl["subject"], tpl["html"])

    logger.info(f"Scenario 3 auto-complete: trade {trade['id']} — neither party confirmed, holds released")


async def auto_reverse_expired_holds():
    """Background task: auto-complete trades where neither user confirmed within 48h,
    and auto-reverse holds for partially confirmed trades past deadline."""
    now = datetime.now(timezone.utc)

    # Find CONFIRMING trades past 48h delivery window
    trades = await db.trades.find({
        "status": "CONFIRMING",
        "delivery_marked_at": {"$exists": True},
    }, {"_id": 0}).to_list(200)

    for trade in trades:
        try:
            delivery_time = datetime.fromisoformat(trade["delivery_marked_at"])
            if now <= delivery_time + timedelta(hours=48):
                continue  # Not yet past 48h

            confirmations = trade.get("confirmations") or {}
            init_confirmed = confirmations.get(trade["initiator_id"])
            resp_confirmed = confirmations.get(trade["responder_id"])

            # Safeguard: skip disputed trades
            if trade.get("status") == "DISPUTED":
                continue

            # Scenario 3: NEITHER confirmed → auto-complete with hold release
            if not init_confirmed and not resp_confirmed:
                await _auto_complete_no_confirmation(trade)
                continue

            # Scenario 2: At least ONE confirmed → complete trade, handle holds
            if init_confirmed or resp_confirmed:
                charges = trade.get("hold_charges") or {}
                hold_amt = f"{trade.get('hold_amount', 0):.2f}"

                if trade.get("hold_enabled") and trade.get("hold_status") == "active":
                    # Refund holds for unconfirmed parties
                    for uid, role in [(trade["initiator_id"], "initiator"), (trade["responder_id"], "responder")]:
                        if not confirmations.get(uid):
                            pi_id = (charges.get(role) or {}).get("payment_intent_id")
                            if pi_id:
                                await _refund_hold(pi_id)
                            confirmations[uid] = "auto"
                            user_obj = await db.users.find_one({"id": uid}, {"_id": 0})
                            if user_obj and user_obj.get("email"):
                                tpl = email_tpl.hold_reversed(user_obj.get("username", ""), hold_amt)
                                await send_email_fire_and_forget(user_obj["email"], tpl["subject"], tpl["html"])

                    await db.trades.update_one({"id": trade["id"]}, {"$set": {
                        "confirmations": confirmations, "hold_status": "refunded",
                        "updated_at": now.isoformat(),
                    }})

                await complete_trade(trade)
                logger.info(f"Scenario 2 auto-complete: trade {trade['id']} — partial confirmation, holds released")

        except Exception as e:
            logger.error(f"Trade auto-completion failed for {trade['id']}: {e}")