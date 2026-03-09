"""
BLOCK 3.2: Automated Payout Cron
72-hour auto-payout post-delivery for standard sellers.
24-hour auto-payout for sellers with 4.5+ star ratings.
"""
import logging
from datetime import datetime, timezone, timedelta
from database import db

logger = logging.getLogger("payout_cron")


async def get_seller_avg_rating(seller_id: str) -> float:
    """Calculate the average rating for a seller from their reviews."""
    pipeline = [
        {"$match": {"seller_id": seller_id, "rating": {"$exists": True}}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}}},
    ]
    result = await db.seller_reviews.aggregate(pipeline).to_list(1)
    return result[0]["avg"] if result else 0.0


async def run_auto_payouts():
    """
    Check for DELIVERED orders with PENDING payouts and auto-release them.
    - 72h for standard sellers
    - 24h for sellers with avg rating >= 4.5
    """
    now = datetime.now(timezone.utc)
    pending = await db.payment_transactions.find(
        {
            "shipping_status": "DELIVERED",
            "payout_status": "PENDING",
            "delivered_at": {"$exists": True},
        },
        {"_id": 0}
    ).to_list(500)

    released = 0
    for txn in pending:
        try:
            delivered_at = datetime.fromisoformat(txn["delivered_at"])
            if delivered_at.tzinfo is None:
                delivered_at = delivered_at.replace(tzinfo=timezone.utc)

            seller_id = txn.get("seller_id")
            avg_rating = await get_seller_avg_rating(seller_id)
            threshold_hours = 24 if avg_rating >= 4.5 else 72
            elapsed = (now - delivered_at).total_seconds() / 3600

            if elapsed >= threshold_hours:
                await db.payment_transactions.update_one(
                    {"id": txn["id"]},
                    {"$set": {
                        "payout_status": "RELEASED",
                        "payout_released_at": now.isoformat(),
                        "payout_threshold_hours": threshold_hours,
                        "seller_avg_rating_at_payout": round(avg_rating, 2),
                    }}
                )
                released += 1
                logger.info(
                    f"Auto-payout released for order {txn['id']} "
                    f"(seller={seller_id}, rating={avg_rating:.1f}, threshold={threshold_hours}h)"
                )
        except Exception as e:
            logger.error(f"Payout error for order {txn.get('id')}: {e}")

    logger.info(f"Auto-payout cron: {released}/{len(pending)} payouts released")
    return {"released": released, "total_pending": len(pending)}
