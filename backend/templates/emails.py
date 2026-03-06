"""All HoneyGroove email templates. Dynamic fields use [field_name] format in docstrings."""

from templates.base import wrap_email

FRONTEND = "https://thehoneygroove.com"

H = "font-family:'Playfair Display',Georgia,serif;font-weight:700;color:#2A1A06;"
AMBER = "color:#C8861A;"
MUTED = "color:#8A6B4A;font-size:13px;"
BTN = "display:inline-block;padding:14px 28px;background:#E8A820;color:#2A1A06;text-decoration:none;border-radius:50px;font-size:14px;font-weight:700;font-family:Georgia,serif;"
SIG = f'<p style="margin:24px 0 0 0;{MUTED}">— Katie, founder of the Honey Groove</p>'
SIG_SHORT = f'<p style="margin:24px 0 0 0;{MUTED}">— Katie, founder</p>'


# ──────────── MARKETING EMAILS (with unsubscribe) ────────────

def newsletter_signup(first_name: str, unsub_url: str = "") -> dict:
    body = f"""
    <p style="{MUTED}">Hey {first_name},</p>
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
    <p style="{MUTED}">Hey {first_name},</p>
    <p>You made it onto the founding member list for <strong>the Honey Groove</strong>.</p>
    <p>We're in the final stretch of beta testing and founding members get in first. When your invite is ready I'll send it directly to this email with everything you need to get started.</p>
    <p>In the meantime follow <a href="https://instagram.com/katieintheafterglow" style="{AMBER}text-decoration:underline;">@katieintheafterglow</a> on Instagram for updates.</p>
    <p>Limited spots. You got one. \U0001F41D</p>
    {SIG}
    """
    return {
        "subject": "You're on the list. \U0001F36F",
        "html": wrap_email(body, unsub_url),
    }


def weekly_wax_ready(username: str, personality_label: str, top_artist: str, top_spins: int, closing_line: str, unsub_url: str = "") -> dict:
    body = f"""
    <p style="{MUTED}">Hey {username},</p>
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
    join_url = f"{FRONTEND}/join?code={invite_code}"
    body = f"""
    <p style="{MUTED}">Hey {first_name},</p>
    <p style="{H}font-size:24px;margin:16px 0 8px 0;">You're in.</p>
    <p>Click the link below to create your founding member account. This link is yours and yours only — it expires after one use.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{join_url}" style="{BTN}">join the Honey Groove</a>
    </div>
    <p style="{MUTED}">{join_url}</p>
    <p>Once you're in you'll get a permanent <strong>founding member badge</strong> on your profile that never goes away. You were here first and that means something.</p>
    <p>I'll be watching for your first Now Spinning. \U0001F36F</p>
    {SIG_SHORT}
    <p style="{MUTED}margin-top:12px;">Questions? Reply to this email.</p>
    """
    return {
        "subject": "Your invite to the Honey Groove is here. \U0001F41D",
        "html": wrap_email(body),
    }


def welcome(username: str) -> dict:
    body = f"""
    <p style="{MUTED}">Hey {username},</p>
    <p style="{H}font-size:24px;margin:16px 0 8px 0;">You made it.</p>
    <p>The Honey Groove is yours now.</p>
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
    <p><strong>{username}</strong> started following you on the Honey Groove.</p>
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
    <p style="{MUTED}">Hey {username},</p>
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
    <p style="{MUTED}">Hey {username},</p>
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
    <p><strong>{sender}</strong> sent you a message on the Honey Groove.</p>
    {context_line}
    <div style="text-align:center;margin:20px 0;">
        <a href="{dm_url}" style="{BTN}">read it</a>
    </div>
    """
    return {
        "subject": f"{sender} sent you a message.",
        "html": wrap_email(body),
    }


def trade_accepted(username: str, acceptor: str, record_name: str, trade_url: str) -> dict:
    body = f"""
    <p style="{MUTED}">Hey {username},</p>
    <p><strong>{acceptor}</strong> accepted your trade offer for <strong>{record_name}</strong>.</p>
    <p>Time to ship your end. Mark it as shipped once it's on its way so the trade can complete.</p>
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
    <p style="{MUTED}">Hey {username},</p>
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
    <p style="{MUTED}">Hey {username},</p>
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


def verified_seller_renewal(username: str, expiry_date: str, days_left: int) -> dict:
    body = f"""
    <p style="{MUTED}">Hey {username},</p>
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
