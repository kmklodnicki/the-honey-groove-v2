"""All HoneyGroove email templates. Dynamic fields use [field_name] format in docstrings."""

from templates.base import wrap_email

import os

FRONTEND = os.environ.get("FRONTEND_URL", "https://thehoneygroove.com")

H = "font-family:'Playfair Display',Georgia,serif;font-weight:700;color:#2A1A06;"
AMBER = "color:#C8861A;"
MUTED = "color:#8A6B4A;font-size:13px;"
GREETING = "color:#2A1A06;font-size:15px;"
BTN = "display:inline-block;padding:14px 28px;background:#E8A820;color:#2A1A06;text-decoration:none;border-radius:50px;font-size:14px;font-weight:700;font-family:Georgia,serif;"
SIG = f'<p style="margin:24px 0 0 0;{MUTED}">— Katie, founder of the Honey Groove<sup style="font-size:0.6em">™</sup></p>'
SIG_SHORT = f'<p style="margin:24px 0 0 0;{MUTED}">— Katie, founder</p>'


# ──────────── MARKETING EMAILS (with unsubscribe) ────────────

def newsletter_signup(first_name: str, unsub_url: str = "") -> dict:
    body = f"""
    <p style="{GREETING}">Hey {first_name},</p>
    <p>You just joined <strong>The Weekly Wax</strong> — a letter for collectors who actually live for this stuff.</p>
    <p>Every week you'll get new finds, community stories, and what's buzzing in the hive. Nothing you didn't ask for.</p>
    <p>We'll see you in your inbox soon.</p>
    {SIG}
    """
    return {
        "subject": "You're in the loop. \U0001F41D",
        "html": wrap_email(body, unsub_url),
    }


def beta_waitlist(first_name: str, unsub_url: str = "") -> dict:
    body = f"""
    <p style="{GREETING}">Hey {first_name},</p>
    <p>You made it onto the founding member list for <strong>the Honey Groove<sup style="font-size:0.6em">™</sup></strong>.</p>
    <p>We're in the final stretch of beta testing and founding members get in first. When your invite is ready I'll send it directly to this email with everything you need to get started.</p>
    <p>In the meantime follow <a href="https://www.instagram.com/thehoneygroove" style="{AMBER}text-decoration:underline;">@thehoneygroove</a> on Instagram for updates.</p>
    <p>Limited spots. You got one. \U0001F41D</p>
    {SIG}
    """
    return {
        "subject": "You're on the list. \U0001F36F",
        "html": wrap_email(body, unsub_url),
    }


def weekly_wax_ready(username: str, personality_label: str, top_artist: str, top_spins: int, closing_line: str, unsub_url: str = "") -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>Your weekly listening report just dropped.</p>
    <div style="text-align:center;padding:24px 16px;margin:16px 0;background:linear-gradient(135deg,#FFF8EE,#FFF3E0);border-radius:16px;border:1px solid #F5E6CC;">
        <p style="{H}font-size:20px;font-style:italic;line-height:1.5;margin:0;{AMBER}">"{closing_line}"</p>
    </div>
    <p>This week you were: <strong style="{AMBER}">{personality_label}</strong></p>
    <p><strong>{top_artist}</strong> was your most spun artist with <strong>{top_spins}</strong> spins.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{FRONTEND}/wax-report" style="{BTN}">read your full report</a>
    </div>
    """
    return {
        "subject": "Your Week in Wax is ready. \U0001F36F",
        "html": wrap_email(body, unsub_url),
    }


# ──────────── TRANSACTIONAL EMAILS (no unsubscribe) ────────────

def invite_code(first_name: str, invite_code: str) -> dict:
    join_url = f"https://thehoneygroove.com/join?code={invite_code}"
    body = f"""
    <p style="{GREETING}">Hey {first_name},</p>
    <p>You're officially in. Your founding member invite for the Honey Groove is ready.</p>
    <p>Use the link below to create your account &mdash; it's yours only and single use, so don't share it before you've signed up.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{join_url}" style="{BTN}">Join the Honey Groove &rarr;</a>
    </div>
    <p style="{MUTED}text-align:center;margin:-8px 0 20px 0;">thehoneygroove.com/invite/{invite_code}</p>
    <p>Quick note before you dive in &mdash; this is our first round of beta testing, which means you're getting in before everything is perfectly polished. If something doesn't work as expected or feels off please tell me immediately. That's exactly why you're here and every piece of feedback goes directly to fixing it.</p>
    <p>One thing to know &mdash; Instagram story sharing is still being worked on and isn't ready yet. Everything else is fair game.</p>
    <p style="margin:20px 0 6px 0;"><strong>Here's all you need to get started:</strong></p>
    <p><strong style="{AMBER}">1. Add at least 3 records to your collection</strong> &mdash; search by artist or album and Discogs pulls everything in automatically.</p>
    <p><strong style="{AMBER}">2. Drop your first Now Spinning</strong> from the composer bar at the top of the Hive. Takes 10 seconds.</p>
    <p><strong style="{AMBER}">3. Add anything you've been hunting to your Wantlist</strong> so we can match you with other collectors.</p>
    <p style="margin:20px 0 6px 0;"><strong>Got feedback? We want it all.</strong> Join the Discord and drop anything and everything in the #thehoneygroove channel &mdash; bugs, suggestions, first impressions, things you love, things that confused you. Nothing is too small. <a href="https://discord.gg/PKSkMhqGPv" target="_blank" style="{AMBER}text-decoration:underline;">discord.gg/PKSkMhqGPv</a> \U0001F41D</p>
    <p>You're a founding member. Your badge is permanent and will never go away no matter how big this gets.</p>
    <p>DM us on Instagram <a href="https://www.instagram.com/thehoneygroove" target="_blank" style="{AMBER}text-decoration:underline;">@thehoneygroove</a> or reply to this email if anything feels urgent.</p>
    <p>Welcome to the hive. \U0001F41D</p>
    {SIG}
    """
    return {
        "subject": "you're in. here's your invite. \U0001F36F",
        "html": wrap_email(body),
    }


def welcome(username: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p style="{H}font-size:24px;margin:16px 0 8px 0;">You made it.</p>
    <p>The Honey Groove<sup style="font-size:0.6em">™</sup> is yours now.</p>
    <p style="margin:16px 0 4px 0;"><strong>A few things to get you started:</strong></p>
    <p><strong style="{AMBER}">Add your collection.</strong> Search by artist or album, or import directly from Discogs if you already have one there.</p>
    <p><strong style="{AMBER}">Drop the needle.</strong> Post your first Now Spinning and let the hive know what's on the turntable.</p>
    <p><strong style="{AMBER}">Hunt something down.</strong> Add your most wanted record to your wantlist and we'll match you the moment it appears.</p>
    <p>The hive is just getting started. Glad you're here.</p>
    {SIG}
    """
    return {
        "subject": "Welcome to the hive. \U0001F36F",
        "html": wrap_email(body),
    }


def new_comment(username: str, post_type: str, comment_text: str, post_url: str) -> dict:
    body = f"""
    <p><strong>{username}</strong> left a comment on your <strong>{post_type}</strong>:</p>
    <div style="padding:12px 16px;background:#FFF8EE;border-left:3px solid #C8861A;border-radius:4px;margin:12px 0;">
        <p style="margin:0;font-style:italic;color:#2A1A06;">"{comment_text}"</p>
    </div>
    <div style="text-align:center;margin:20px 0;">
        <a href="{post_url}" style="{BTN}">view the conversation</a>
    </div>
    """
    return {
        "subject": f"{username} commented on your post.",
        "html": wrap_email(body),
    }


def new_like(username: str, post_type: str, post_preview: str, post_url: str) -> dict:
    body = f"""
    <p><strong>{username}</strong> liked your <strong>{post_type}</strong>.</p>
    <p style="{MUTED}">{post_preview}</p>
    <div style="text-align:center;margin:20px 0;">
        <a href="{post_url}" style="{BTN}">see your post</a>
    </div>
    """
    return {
        "subject": f"{username} liked your post.",
        "html": wrap_email(body),
    }


def new_follow(username: str, profile_url: str) -> dict:
    body = f"""
    <p><strong>{username}</strong> started following you on the Honey Groove<sup style="font-size:0.6em">™</sup>.</p>
    <p>Check out their collection and follow them back.</p>
    <div style="text-align:center;margin:20px 0;">
        <a href="{profile_url}" style="{BTN}">view their profile</a>
    </div>
    """
    return {
        "subject": f"{username} is now following you.",
        "html": wrap_email(body),
    }


def wantlist_match(username: str, album: str, artist: str, seller: str, price: str, listing_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>A record on your wantlist just appeared in the Honeypot.</p>
    <div style="text-align:center;padding:20px;margin:16px 0;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;">
        <p style="{H}font-size:22px;margin:0 0 4px 0;">{album}</p>
        <p style="{AMBER}font-size:16px;font-style:italic;margin:0;">by {artist}</p>
        <p style="{MUTED}margin:8px 0 0 0;">Listed by @{seller} for <strong>${price}</strong></p>
    </div>
    <p>This match won't last forever.</p>
    <div style="text-align:center;margin:20px 0;">
        <a href="{listing_url}" style="{BTN}">view the listing</a>
    </div>
    """
    return {
        "subject": "We found your record. \U0001F36F",
        "html": wrap_email(body),
    }


def new_trade_offer(username: str, proposer: str, record_name: str, their_record: str, sweetener: str, trade_url: str) -> dict:
    sweetener_line = f'<p style="{AMBER}font-weight:600;">Sweetener: + ${sweetener}</p>' if sweetener else ""
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p><strong>{proposer}</strong> proposed a trade for your <strong>{record_name}</strong>.</p>
    <p>They're offering: <strong>{their_record}</strong></p>
    {sweetener_line}
    <div style="text-align:center;margin:20px 0;">
        <a href="{trade_url}" style="{BTN}">view the offer</a>
    </div>
    """
    return {
        "subject": f"{proposer} wants to trade. \U0001F3B5",
        "html": wrap_email(body),
    }


def new_dm(username: str, sender: str, context_record: str, dm_url: str) -> dict:
    context_line = f'<p style="{MUTED}">Re: {context_record}</p>' if context_record else ""
    body = f"""
    <p><strong>{sender}</strong> sent you a message on the Honey Groove<sup style="font-size:0.6em">™</sup>.</p>
    {context_line}
    <div style="text-align:center;margin:20px 0;">
        <a href="{dm_url}" style="{BTN}">read it</a>
    </div>
    """
    return {
        "subject": f"{sender} sent you a message.",
        "html": wrap_email(body),
    }


def trade_accepted(username: str, acceptor: str, record_name: str, trade_url: str, hold_amount: str = "0") -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p><strong>{acceptor}</strong> accepted your trade offer for <strong>{record_name}</strong>.</p>
    <div style="padding:16px 20px;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;margin:16px 0;">
        <p style="margin:0;">Both parties have been charged a hold of <strong style="{AMBER}">${hold_amount}</strong>.</p>
        <p style="margin:8px 0 0 0;{MUTED}font-size:13px;">This will be fully reversed within 24 hours of confirmed delivery from both sides. It protects you and the person you are trading with.</p>
    </div>
    <p>Pay your hold to lock in the trade, then ship your record. Mark it as shipped once it's on its way so the trade can complete.</p>
    <div style="text-align:center;margin:20px 0;">
        <a href="{trade_url}" style="{BTN}">view the trade</a>
    </div>
    """
    return {
        "subject": "Your trade was accepted. \U0001F4E6",
        "html": wrap_email(body),
    }


def trade_shipped(username: str, shipper: str, trade_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p><strong>{shipper}</strong> has shipped their end of the trade.</p>
    <p>Keep an eye on your mailbox. Once your record arrives confirm receipt in the app to complete the trade and release payment.</p>
    <div style="text-align:center;margin:20px 0;">
        <a href="{trade_url}" style="{BTN}">view the trade</a>
    </div>
    """
    return {
        "subject": f"{shipper} shipped their record. \U0001F4EC",
        "html": wrap_email(body),
    }


def streak_nudge(username: str, streak: int, prompt_text: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>You're on a <strong style="{AMBER}">{streak} day streak</strong>. Don't break it now.</p>
    <div style="padding:16px;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;margin:12px 0;">
        <p style="{MUTED}margin:0 0 4px 0;">Today's prompt:</p>
        <p style="{H}font-size:18px;margin:0;">{prompt_text}</p>
    </div>
    <div style="text-align:center;margin:20px 0;">
        <a href="{FRONTEND}/hive" style="{BTN}">buzz in</a>
    </div>
    """
    return {
        "subject": "Today's prompt is waiting. \U0001F41D",
        "html": wrap_email(body),
    }


LISTING_TYPE_LABELS = {"BUY_NOW": "Buy It Now", "MAKE_OFFER": "Make an Offer", "TRADE": "Trade"}


def listing_confirmed(username: str, album: str, artist: str, condition: str, price: str, listing_type: str, listing_url: str) -> dict:
    type_label = LISTING_TYPE_LABELS.get(listing_type, listing_type)
    price_line = f'<p>Price: <strong>${price}</strong></p>' if listing_type != "TRADE" else ""
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p style="{H}font-size:22px;margin:16px 0 4px 0;">{album}</p>
    <p style="{AMBER}font-size:16px;font-style:italic;margin:0 0 16px 0;">by {artist}</p>
    <p>is now live in the Honeypot.</p>
    <div style="padding:16px 20px;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;margin:16px 0;">
        <p style="margin:0 0 4px 0;">Condition: <strong>{condition}</strong></p>
        {price_line}
        <p style="margin:4px 0 0 0;">Listing type: <strong>{type_label}</strong></p>
    </div>
    <p>Your record is visible to every collector in the hive. We'll notify you the moment someone makes an offer or purchases.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{listing_url}" style="{BTN}">view your listing</a>
    </div>
    <p>Good luck. \U0001F41D</p>
    <p style="margin:16px 0 0 0;{MUTED}">— The Honey Groove</p>
    """
    return {
        "subject": "Your record is listed. \U0001F36F",
        "html": wrap_email(body),
    }


def sale_confirmed_seller(username: str, album: str, artist: str, price: str, fee_amount: str, payout_amount: str, fee_pct: str, sale_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p style="{H}font-size:22px;margin:16px 0 4px 0;">{album}</p>
    <p style="{AMBER}font-size:16px;font-style:italic;margin:0 0 16px 0;">by {artist}</p>
    <p>just sold.</p>
    <div style="padding:16px 20px;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;margin:16px 0;">
        <p style="margin:0 0 4px 0;">Sale price: <strong>${price}</strong></p>
        <p style="margin:4px 0;">Platform fee ({fee_pct}%): <strong>${fee_amount}</strong></p>
        <p style="margin:4px 0 0 0;{H}font-size:16px;">Your payout: <strong style="{AMBER}">${payout_amount}</strong></p>
    </div>
    <p>Your payout will be transferred to your connected Stripe account within 2 to 5 business days.</p>
    <p>Next step — ship your record to the buyer as soon as possible. Once you've shipped mark it as shipped in the app so the buyer knows it's on the way.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{sale_url}" style="{BTN}">view the sale</a>
    </div>
    <p>Thank you for being part of the hive. \U0001F36F</p>
    <p style="margin:16px 0 0 0;{MUTED}">— The Honey Groove</p>
    """
    return {
        "subject": "Your record sold. \U0001F389",
        "html": wrap_email(body),
    }


def sale_confirmed_buyer(username: str, album: str, artist: str, seller_username: str, price: str, purchase_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>You just bought <strong style="{H}font-size:18px;">{album}</strong> <span style="{AMBER}font-style:italic;">by {artist}</span> from <strong>@{seller_username}</strong>.</p>
    <div style="padding:16px 20px;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;margin:16px 0;">
        <p style="margin:0;">Amount paid: <strong>${price}</strong></p>
    </div>
    <p>The seller has been notified and will ship your record shortly. You'll get another email the moment they mark it as shipped.</p>
    <p>Keep an eye on your messages in the app — you can contact the seller directly if you have any questions about the order.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{purchase_url}" style="{BTN}">view your purchase</a>
    </div>
    <p>Welcome to your collection. \U0001F36F</p>
    <p style="margin:16px 0 0 0;{MUTED}">— The Honey Groove</p>
    """
    return {
        "subject": "Your record is on its way. \U0001F3B5",
        "html": wrap_email(body),
    }


def hold_activated(username: str, other_username: str, hold_amount: str, trade_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>Both holds are now active on your Mutual Hold trade with <strong>@{other_username}</strong>.</p>
    <div style="text-align:center;padding:20px;margin:16px 0;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;">
        <p style="{H}font-size:28px;margin:0;">${hold_amount}</p>
        <p style="{MUTED}margin:4px 0 0 0;">held from each party</p>
    </div>
    <p>Ship your record and confirm receipt to release the hold. Both parties are protected.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{trade_url}" style="{BTN}">view the trade</a>
    </div>
    """
    return {
        "subject": "Hold activated — both parties protected. \U0001F6E1\uFE0F",
        "html": wrap_email(body),
    }


def hold_delivery_confirmed(username: str, hold_amount: str, trade_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>Both records have been marked as delivered. You now have <strong>24 hours</strong> to confirm receipt.</p>
    <div style="text-align:center;padding:16px;margin:16px 0;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;">
        <p style="margin:0;"><strong style="{AMBER}">Your hold: ${hold_amount}</strong></p>
        <p style="{MUTED}margin:4px 0 0 0;">will be released once you confirm</p>
    </div>
    <p>Confirm that the record arrived as described, or open a dispute if there's an issue.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{trade_url}" style="{BTN}">confirm receipt</a>
    </div>
    """
    return {
        "subject": "Delivery confirmed — 24 hour window open. \U0001F4E6",
        "html": wrap_email(body),
    }


def hold_reversed(username: str, hold_amount: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>Your hold has been released.</p>
    <div style="text-align:center;padding:20px;margin:16px 0;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;">
        <p style="{H}font-size:28px;margin:0;{AMBER}">${hold_amount}</p>
        <p style="{MUTED}margin:4px 0 0 0;">refund on its way</p>
    </div>
    <p>The refund will appear on your card within 2 to 5 business days depending on your card issuer.</p>
    <p>Thanks for keeping the trade safe. \U0001F36F</p>
    <p style="margin:16px 0 0 0;{MUTED}">— The Honey Groove</p>
    """
    return {
        "subject": "Hold reversed — refund on its way. \U0001F36F",
        "html": wrap_email(body),
    }


def hold_dispute_filed(username: str, other_username: str, hold_amount: str, trade_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>A dispute has been filed on your Mutual Hold trade with <strong>@{other_username}</strong>.</p>
    <div style="text-align:center;padding:16px;margin:16px 0;background:#FFF8EE;border-radius:12px;border:1px solid #F5E6CC;">
        <p style="margin:0;font-weight:600;color:#B91C1C;">Hold frozen — ${hold_amount}</p>
        <p style="{MUTED}margin:4px 0 0 0;">Neither hold will be released until the dispute is resolved</p>
    </div>
    <p>Our team has been notified and will review the details. We'll reach out if we need anything from you.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{trade_url}" style="{BTN}">view the trade</a>
    </div>
    """
    return {
        "subject": "Hold frozen — dispute in progress. \U0001F6E1\uFE0F",
        "html": wrap_email(body),
    }


def verified_seller_renewal(username: str, expiry_date: str, days_left: int) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>Your <strong>Verified Seller</strong> badge expires on <strong>{expiry_date}</strong> — that's {days_left} days from now.</p>
    <p>Renew for another year at <strong>$25</strong> to keep your badge and trust signal on all your listings.</p>
    <div style="text-align:center;margin:20px 0;">
        <a href="{FRONTEND}/settings" style="{BTN}">renew now</a>
    </div>
    """
    return {
        "subject": "Your Verified Seller badge renews soon.",
        "html": wrap_email(body),
    }
