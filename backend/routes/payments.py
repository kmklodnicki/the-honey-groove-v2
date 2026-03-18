"""Buyer payment setup routes — Stripe Customer + saved payment methods."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict

from database import db, require_auth, logger, STRIPE_API_KEY
import stripe as stripe_sdk

router = APIRouter()


async def _ensure_customer(user: Dict) -> str:
    """Return existing stripe_customer_id or create one and persist it."""
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "stripe_customer_id": 1, "email": 1})
    if u and u.get("stripe_customer_id"):
        return u["stripe_customer_id"]

    stripe_sdk.api_key = STRIPE_API_KEY
    customer = stripe_sdk.Customer.create(
        email=u.get("email", user.get("email", "")),
        metadata={"thg_user_id": user["id"]},
    )
    await db.users.update_one({"id": user["id"]}, {"$set": {"stripe_customer_id": customer.id}})
    return customer.id


@router.post("/payments/customer")
async def create_customer(user: Dict = Depends(require_auth)):
    """Create (or retrieve) a Stripe Customer for the authenticated user."""
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    cid = await _ensure_customer(user)
    return {"customer_id": cid}


@router.post("/payments/setup-intent")
async def create_setup_intent(user: Dict = Depends(require_auth)):
    """Create a SetupIntent so the frontend can save a card off-session."""
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    cid = await _ensure_customer(user)
    stripe_sdk.api_key = STRIPE_API_KEY
    si = stripe_sdk.SetupIntent.create(
        customer=cid,
        usage="off_session",
    )
    return {"client_secret": si.client_secret}


@router.post("/payments/payment-methods/confirm")
async def confirm_payment_method(body: Dict, user: Dict = Depends(require_auth)):
    """Attach a confirmed PaymentMethod to the customer and optionally set as default."""
    pm_id = body.get("payment_method_id")
    set_as_default = body.get("set_as_default", True)
    if not pm_id:
        raise HTTPException(status_code=400, detail="payment_method_id required")
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    cid = await _ensure_customer(user)
    stripe_sdk.api_key = STRIPE_API_KEY

    try:
        pm = stripe_sdk.PaymentMethod.attach(pm_id, customer=cid)
    except stripe_sdk.error.InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))

    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "default_payment_method_id": 1})
    if set_as_default or not u.get("default_payment_method_id"):
        stripe_sdk.Customer.modify(
            cid,
            invoice_settings={"default_payment_method": pm_id},
        )
        await db.users.update_one({"id": user["id"]}, {"$set": {"default_payment_method_id": pm_id}})

    card = pm.card or {}
    return {
        "id": pm.id,
        "brand": card.get("brand"),
        "last4": card.get("last4"),
        "exp_month": card.get("exp_month"),
        "exp_year": card.get("exp_year"),
    }


@router.get("/payments/payment-methods")
async def list_payment_methods(user: Dict = Depends(require_auth)):
    """List saved cards for the authenticated user."""
    if not STRIPE_API_KEY:
        return {"payment_methods": []}

    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "stripe_customer_id": 1, "default_payment_method_id": 1})
    if not u or not u.get("stripe_customer_id"):
        return {"payment_methods": []}

    stripe_sdk.api_key = STRIPE_API_KEY
    try:
        pms = stripe_sdk.PaymentMethod.list(customer=u["stripe_customer_id"], type="card")
    except Exception as e:
        logger.error(f"list_payment_methods error: {e}")
        return {"payment_methods": []}

    default_pm = u.get("default_payment_method_id")
    result = []
    for pm in pms.data:
        card = pm.card or {}
        result.append({
            "id": pm.id,
            "brand": card.get("brand"),
            "last4": card.get("last4"),
            "exp_month": card.get("exp_month"),
            "exp_year": card.get("exp_year"),
            "is_default": pm.id == default_pm,
        })
    return {"payment_methods": result}


@router.delete("/payments/payment-methods/{pm_id}")
async def delete_payment_method(pm_id: str, user: Dict = Depends(require_auth)):
    """Detach a saved card from the customer."""
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "stripe_customer_id": 1, "default_payment_method_id": 1})
    if not u or not u.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="No payment methods on file")

    stripe_sdk.api_key = STRIPE_API_KEY
    try:
        stripe_sdk.PaymentMethod.detach(pm_id)
    except stripe_sdk.error.InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))

    update = {}
    if u.get("default_payment_method_id") == pm_id:
        update["default_payment_method_id"] = None
    if update:
        await db.users.update_one({"id": user["id"]}, {"$set": update})

    return {"deleted": True}


@router.post("/payments/payment-methods/{pm_id}/set-default")
async def set_default_payment_method(pm_id: str, user: Dict = Depends(require_auth)):
    """Set a saved card as the invoice default."""
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    cid = await _ensure_customer(user)
    stripe_sdk.api_key = STRIPE_API_KEY
    stripe_sdk.Customer.modify(
        cid,
        invoice_settings={"default_payment_method": pm_id},
    )
    await db.users.update_one({"id": user["id"]}, {"$set": {"default_payment_method_id": pm_id}})
    return {"default": pm_id}
