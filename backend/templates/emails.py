"""All HoneyGroove email templates. Dynamic fields use [field_name] format in docstrings."""

from templates.base import wrap_email

import os

FRONTEND = os.environ.get("FRONTEND_URL", "https://thehoneygroove.com")

H = "font-family:'Playfair Display',Georgia,serif;font-weight:700;color:#1E2A3A;"
AMBER = "color:#D4A828;"
MUTED = "color:#7A8694;font-size:13px;"
GREETING = "color:#1E2A3A;font-size:13px;"
BTN = "display:inline-block;padding:12px 28px;background:#D4A828;color:#FFFFFF;text-decoration:none;border-radius:8px;font-size:14px;font-weight:700;font-family:'DM Sans',-apple-system,sans-serif;box-shadow:0 2px 4px rgba(212,168,40,0.28),0 4px 12px rgba(212,168,40,0.20);"
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


def gold_welcome(username: str) -> dict:
    FEATURE_DOT = "display:inline-block;width:8px;height:8px;border-radius:50%;background:#D4A828;margin-right:10px;vertical-align:middle;flex-shrink:0;"
    features = [
        ("Vault Analytics", "Full value trends, genre breakdowns, and collection insights"),
        ("4% Marketplace Fees", "Reduced from 6% on every sale through the Honeypot"),
        ("Unlimited Rooms", "Join every room that matches your taste, plus create your own"),
        ("Price Alerts", "Get notified when Dream List records hit your target price"),
        ("Gold Collector Badge", "Visible on your profile, posts, and share cards"),
    ]
    feature_rows = ""
    for title, desc in features:
        feature_rows += f"""
    <div style="display:flex;align-items:flex-start;padding:12px 16px;background:#FFFBF2;border-radius:8px;border:1px solid #E5DBC8;margin:0 0 8px 0;">
        <span style="{FEATURE_DOT}margin-top:5px;"></span>
        <div>
            <p style="color:#1E2A3A;font-size:13px;font-weight:700;margin:0 0 2px 0;">{title}</p>
            <p style="color:#3A4D63;font-size:12px;margin:0;">{desc}</p>
        </div>
    </div>"""
    body = f"""
    <div style="background:#1E2A3A;border-radius:12px;padding:24px 20px;text-align:center;margin:0 0 24px 0;">
        <p style="margin:0 0 12px 0;font-size:10px;font-style:italic;color:#D4A828;font-family:'DM Sans',-apple-system,sans-serif;">the</p>
        <p style="margin:0 0 14px 0;font-size:20px;font-weight:700;font-family:'Playfair Display',Georgia,serif;"><span style="color:#FFFFFF;">Honey</span><span style="color:#D4A828;">Groove</span></p>
        <span style="display:inline-block;padding:4px 14px;background:rgba(212,168,40,0.15);color:#D4A828;border:1px solid rgba(212,168,40,0.25);border-radius:50px;font-size:10px;font-weight:700;font-family:'DM Sans',-apple-system,sans-serif;letter-spacing:0.08em;">GOLD COLLECTOR</span>
    </div>
    <p style="{H}font-size:26px;text-align:center;margin:0 0 6px 0;">Welcome to Gold</p>
    <p style="color:#3A4D63;font-size:13px;text-align:center;margin:0 0 24px 0;">You just unlocked the full Honey Groove experience.</p>
    {feature_rows}
    <div style="text-align:center;margin:24px 0;">
        <a href="{FRONTEND}/gold" style="{BTN}">Explore Your Gold Features</a>
    </div>
    """
    return {
        "subject": "You're Gold. Welcome to the full experience. \U0001F36F",
        "html": wrap_email(body),
    }


def release_updates(sections: list, date_str: str = "") -> dict:
    """sections: list of dicts with 'title' (str) and 'items' (list of str)"""
    date_line = f'<p style="color:#3A4D63;font-size:12px;text-align:center;margin:-8px 0 20px 0;">{date_str}</p>' if date_str else ""
    sections_html = ""
    for section in sections:
        items_html = "".join(
            f'<li style="color:#1E2A3A;font-size:13px;line-height:1.7;margin:0 0 4px 0;">{item}</li>'
            for item in section.get("items", [])
        )
        sections_html += f"""
    <p style="{AMBER}font-size:13px;font-weight:700;margin:16px 0 8px 0;">{section["title"]}</p>
    <ul style="margin:0 0 8px 0;padding-left:20px;">{items_html}</ul>"""
    body = f"""
    <p style="{H}font-size:26px;text-align:center;margin:0 0 6px 0;">Release Updates</p>
    {date_line}
    <p style="{GREETING}">Hey Hive,</p>
    <p>Big week. Here&#8217;s what&#8217;s new:</p>
    {sections_html}
    <div style="height:1px;background:#E5DBC8;margin:24px 0;"></div>
    <p style="font-style:italic;color:#3A4D63;font-size:13px;">More coming soon. Thank you for being here while we build this together.</p>
    <p style="margin:16px 0 2px 0;font-weight:700;color:#1E2A3A;">Katie</p>
    <p style="margin:0;font-style:italic;color:#3A4D63;font-size:12px;">Founder, The Honey Groove</p>
    """
    return {
        "subject": "What\u2019s new in the Hive. \U0001F41D",
        "html": wrap_email(body),
    }


def weekly_wax_ready(username: str, personality_label: str, top_artist: str, top_spins: int, closing_line: str, unsub_url: str = "", date_range: str = "", records_added: int = 0, avg_value: str = "") -> dict:
    date_line = f'<p style="color:#3A4D63;font-size:12px;margin:4px 0 0 0;">{date_range}</p>' if date_range else ""
    body = f"""
    <div style="text-align:center;padding:20px 16px 16px;background:linear-gradient(135deg,#FFFBF2,#F3EBE0);border-radius:12px;border:1px solid #E5DBC8;margin:0 0 20px 0;">
        <p style="color:#D4A828;font-size:10px;font-weight:700;letter-spacing:0.12em;margin:0;font-family:'DM Sans',-apple-system,sans-serif;">YOUR WEEK IN WAX</p>
        {date_line}
    </div>
    <div style="text-align:center;padding:24px 20px;background:#FFFFFF;border-radius:12px;border:1px solid #E5DBC8;margin:0 0 16px 0;">
        <p style="color:#3A4D63;font-size:11px;margin:0 0 8px 0;">This week you were</p>
        <p style="{H}font-size:24px;margin:0 0 10px 0;">{personality_label}</p>
        <p style="{H}font-size:13px;font-style:italic;font-weight:400;{AMBER}margin:0;">&#8220;{closing_line}&#8221;</p>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 20px 0;">
    <tr>
        <td width="33%" style="padding:0 4px 0 0;">
            <div style="background:#FFFBF2;border-radius:10px;border:1px solid #E5DBC8;padding:14px 8px;text-align:center;">
                <p style="{AMBER}font-size:22px;font-weight:700;font-family:'Playfair Display',Georgia,serif;margin:0 0 4px 0;">{records_added}</p>
                <p style="color:#3A4D63;font-size:9px;font-weight:700;letter-spacing:0.08em;margin:0;text-transform:uppercase;">Records Added</p>
            </div>
        </td>
        <td width="33%" style="padding:0 2px;">
            <div style="background:#FFFBF2;border-radius:10px;border:1px solid #E5DBC8;padding:14px 8px;text-align:center;">
                <p style="{AMBER}font-size:22px;font-weight:700;font-family:'Playfair Display',Georgia,serif;margin:0 0 4px 0;">{top_spins}</p>
                <p style="color:#3A4D63;font-size:9px;font-weight:700;letter-spacing:0.08em;margin:0;text-transform:uppercase;">Total Spins</p>
            </div>
        </td>
        <td width="33%" style="padding:0 0 0 4px;">
            <div style="background:#FFFBF2;border-radius:10px;border:1px solid #E5DBC8;padding:14px 8px;text-align:center;">
                <p style="{AMBER}font-size:22px;font-weight:700;font-family:'Playfair Display',Georgia,serif;margin:0 0 4px 0;">{avg_value}</p>
                <p style="color:#3A4D63;font-size:9px;font-weight:700;letter-spacing:0.08em;margin:0;text-transform:uppercase;">Avg. Value</p>
            </div>
        </td>
    </tr>
    </table>
    <div style="text-align:center;margin:24px 0;">
        <a href="{FRONTEND}/wax-report" style="{BTN}">View Full Report</a>
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
    <p><strong style="{AMBER}">3. Add anything you've been hunting to your Dream List</strong> so we can match you with other collectors.</p>
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
    STEP = "display:inline-block;width:24px;height:24px;line-height:24px;border-radius:50%;background:#D4A828;color:#FFFFFF;font-size:12px;font-weight:700;text-align:center;font-family:'DM Sans',-apple-system,sans-serif;vertical-align:middle;margin-right:10px;flex-shrink:0;"
    body = f"""
    <div style="text-align:center;margin:0 0 20px 0;">
        <p style="{H}font-size:28px;margin:0 0 6px 0;">Welcome to the Hive</p>
        <p style="color:#3A4D63;font-size:13px;margin:0;">Your vinyl collection just found its home.</p>
    </div>
    <p style="{GREETING}">Hey {username},</p>
    <p>Welcome to The Honey Groove. You just joined a community of collectors who care about the music they own, not just the music they stream.</p>
    <p style="margin:16px 0 12px 0;">Here&#8217;s how to get started:</p>
    <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="padding:0 0 10px 0;">
        <table cellpadding="0" cellspacing="0"><tr>
        <td style="vertical-align:top;padding-right:10px;"><div style="{STEP}">1</div></td>
        <td style="color:#1E2A3A;font-size:13px;line-height:1.6;vertical-align:middle;">Import your collection from Discogs or add records manually</td>
        </tr></table>
    </td></tr>
    <tr><td style="padding:0 0 10px 0;">
        <table cellpadding="0" cellspacing="0"><tr>
        <td style="vertical-align:top;padding-right:10px;"><div style="{STEP}">2</div></td>
        <td style="color:#1E2A3A;font-size:13px;line-height:1.6;vertical-align:middle;">Share what you&#8217;re spinning in The Hive</td>
        </tr></table>
    </td></tr>
    <tr><td style="padding:0 0 10px 0;">
        <table cellpadding="0" cellspacing="0"><tr>
        <td style="vertical-align:top;padding-right:10px;"><div style="{STEP}">3</div></td>
        <td style="color:#1E2A3A;font-size:13px;line-height:1.6;vertical-align:middle;">Answer the Daily Prompt and keep your streak alive</td>
        </tr></table>
    </td></tr>
    <tr><td style="padding:0 0 10px 0;">
        <table cellpadding="0" cellspacing="0"><tr>
        <td style="vertical-align:top;padding-right:10px;"><div style="{STEP}">4</div></td>
        <td style="color:#1E2A3A;font-size:13px;line-height:1.6;vertical-align:middle;">Explore rooms and find collectors who share your taste</td>
        </tr></table>
    </td></tr>
    </table>
    <div style="text-align:center;margin:24px 0;">
        <a href="{FRONTEND}" style="{BTN}">Open The Honey Groove</a>
    </div>
    <p style="margin:20px 0 4px 0;">See you in the Hive,</p>
    <p style="margin:0 0 2px 0;font-weight:700;color:#1E2A3A;">Katie</p>
    <p style="margin:0;font-style:italic;color:#3A4D63;font-size:12px;">Founder, The Honey Groove</p>
    """
    return {
        "subject": "Welcome to the hive. \U0001F36F",
        "html": wrap_email(body),
    }


def new_comment(username: str, post_type: str, comment_text: str, post_url: str) -> dict:
    body = f"""
    <p><strong>{username}</strong> left a comment on your <strong>{post_type}</strong>:</p>
    <div style="padding:12px 16px;background:#FFFBF2;border-left:3px solid #D4A828;border-radius:4px;margin:12px 0;">
        <p style="margin:0;font-style:italic;color:#1E2A3A;">"{comment_text}"</p>
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
    <p>A record on your Dream List just appeared in the Honeypot.</p>
    <div style="text-align:center;padding:20px;margin:16px 0;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;">
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


def new_trade_offer(username: str, proposer: str, record_name: str, their_record: str, sweetener: str, trade_url: str, their_album_art_url: str = "", your_album_art_url: str = "", profile_url: str = "") -> dict:
    sweetener_line = f'<p style="text-align:center;{AMBER}font-weight:600;font-size:12px;margin:8px 0 0 0;">+ ${sweetener} sweetener</p>' if sweetener else ""
    ALBUM_ART = "width:80px;height:80px;object-fit:cover;border-radius:8px;display:block;"
    ALBUM_PLACEHOLDER = f"width:80px;height:80px;border-radius:8px;background:#F3EBE0;display:flex;align-items:center;justify-content:center;"
    their_art = f'<img src="{their_album_art_url}" alt="{their_record}" style="{ALBUM_ART}" />' if their_album_art_url else f'<div style="{ALBUM_PLACEHOLDER}"></div>'
    your_art = f'<img src="{your_album_art_url}" alt="{record_name}" style="{ALBUM_ART}" />' if your_album_art_url else f'<div style="{ALBUM_PLACEHOLDER}"></div>'
    BTN_OUTLINE = f"display:inline-block;padding:12px 24px;background:transparent;color:#1E2A3A;text-decoration:none;border-radius:8px;font-size:13px;font-weight:700;font-family:'DM Sans',-apple-system,sans-serif;border:1.5px solid #1E2A3A;"
    profile_btn = f'<a href="{profile_url}" style="{BTN_OUTLINE}">View Profile</a>' if profile_url else ""
    body = f"""
    <p style="{H}font-size:22px;text-align:center;margin:0 0 20px 0;">You&#8217;ve got a trade offer</p>
    <div style="background:#FFFBF2;border-radius:12px;border:1px solid #E5DBC8;padding:20px 16px;margin:0 0 20px 0;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td width="44%" style="text-align:center;vertical-align:top;">
                <p style="color:#3A4D63;font-size:9px;font-weight:700;letter-spacing:0.1em;margin:0 0 10px 0;text-transform:uppercase;">They Send</p>
                <div style="margin:0 auto 10px auto;width:80px;">{their_art}</div>
                <p style="{H}font-size:12px;margin:0 0 2px 0;">{their_record}</p>
                <p style="color:#3A4D63;font-size:11px;font-style:italic;margin:0;">@{proposer}</p>
            </td>
            <td width="12%" style="text-align:center;vertical-align:middle;padding-top:30px;">
                <span style="color:#D4A828;font-size:18px;">&#8644;</span>
            </td>
            <td width="44%" style="text-align:center;vertical-align:top;">
                <p style="color:#3A4D63;font-size:9px;font-weight:700;letter-spacing:0.1em;margin:0 0 10px 0;text-transform:uppercase;">You Send</p>
                <div style="margin:0 auto 10px auto;width:80px;">{your_art}</div>
                <p style="{H}font-size:12px;margin:0 0 2px 0;">{record_name}</p>
            </td>
        </tr>
        </table>
        <p style="text-align:center;color:#3A4D63;font-size:12px;margin:12px 0 0 0;">from @{proposer}</p>
        {sweetener_line}
    </div>
    <div style="text-align:center;margin:20px 0;">
        <a href="{trade_url}" style="{BTN}margin-right:8px;">Review Trade</a>{profile_btn}
    </div>
    """
    return {
        "subject": f"{proposer} wants to trade. \U0001F3B5",
        "html": wrap_email(body),
    }


def listing_alert_email(username: str, album: str, artist: str, cover_url: str, listing_url: str) -> dict:
    cover_html = f'<img src="{cover_url}" alt="{album}" style="width:120px;height:120px;object-fit:cover;border-radius:8px;margin:0 auto 12px auto;display:block;" />' if cover_url else ""
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>A record you were watching just landed in the Honeypot!</p>
    <div style="text-align:center;padding:20px;margin:16px 0;background:#FFFBF2;border-radius:12px;border:2px solid #D4A828;">
        {cover_html}
        <p style="{H}font-size:22px;margin:0 0 4px 0;">{album}</p>
        <p style="{AMBER}font-size:16px;font-style:italic;margin:0;">by {artist}</p>
    </div>
    <p>Don't wait — these tend to go fast.</p>
    <div style="text-align:center;margin:20px 0;">
        <a href="{listing_url}" style="{BTN}">view the listing</a>
    </div>
    {SIG_SHORT}
    """
    return {
        "subject": f"Good news! {album} is now in the Honeypot. \U0001F36F",
        "html": wrap_email(body),
    }


def new_dm(username: str, sender: str, context_record: str, dm_url: str) -> dict:
    context_line = f'<p style="{MUTED}">Re: {context_record}</p>' if context_record else ""
    settings_url = f"{FRONTEND}/settings"
    body = f"""
    <p><strong>{sender}</strong> sent you a message on the Honey Groove<sup style="font-size:0.6em">™</sup>.</p>
    {context_line}
    <div style="text-align:center;margin:20px 0;">
        <a href="{dm_url}" style="{BTN}">read it</a>
    </div>
    """
    unsub_line = f'<p style="margin:8px 0 0 0;"><a href="{settings_url}" style="color:#D4A828;text-decoration:underline;font-size:12px;">manage email preferences</a></p>'
    return {
        "subject": f"{sender} sent you a message.",
        "html": wrap_email(body, settings_url),
    }


def trade_accepted(username: str, acceptor: str, record_name: str, trade_url: str, hold_amount: str = "0") -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p><strong>{acceptor}</strong> accepted your trade offer for <strong>{record_name}</strong>.</p>
    <div style="padding:16px 20px;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;margin:16px 0;">
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
    <div style="padding:16px;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;margin:12px 0;">
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
    <div style="padding:16px 20px;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;margin:16px 0;">
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
    <div style="padding:16px 20px;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;margin:16px 0;">
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
    <div style="padding:16px 20px;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;margin:16px 0;">
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
    <div style="text-align:center;padding:20px;margin:16px 0;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;">
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
    <div style="text-align:center;padding:16px;margin:16px 0;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;">
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
    <div style="text-align:center;padding:20px;margin:16px 0;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;">
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
    <div style="text-align:center;padding:16px;margin:16px 0;background:#FFFBF2;border-radius:12px;border:1px solid #F3EBE0;">
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


def trade_auto_completed(username: str, hold_amount: str, trade_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>Your trade has been <strong>completed automatically</strong> after 24 hours with no disputes filed.</p>
    <div style="text-align:center;padding:16px;margin:16px 0;background:#F0FFF4;border-radius:12px;border:1px solid #C6F6D5;">
        <p style="margin:0;font-weight:600;color:#2F8F6B;">Trade completed</p>
        <p style="{MUTED}margin:4px 0 0 0;">Your mutual hold of ${hold_amount} has been released back to you.</p>
    </div>
    <p>Your records have been exchanged. If you'd like to leave a rating, you still can from the trade page.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{trade_url}" style="{BTN}">view trade</a>
    </div>
    {SIG_SHORT}
    """
    return {
        "subject": "Trade completed automatically — holds released.",
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



def honeypot_launch(username: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {username},</p>
    <p>You asked us to let you know. <strong>The Honeypot is officially live.</strong></p>
    <p>Buy and sell vinyl at <strong style="{AMBER}">6% fees</strong> (the lowest in the game).
    Trade records with <strong>Mutual Hold protection</strong>.
    Post what you're seeking and get matched instantly.</p>
    <p>You're one of the first to know. List a record, make an offer, or start a trade.</p>
    <div style="text-align:center;margin:24px 0;">
        <a href="{FRONTEND}/honeypot" style="{BTN}">enter the Honeypot</a>
    </div>
    <p>The hive is buzzing. 🐝</p>
    {SIG}
    """
    return {"subject": "The Honeypot is open. 🍯", "html": wrap_email(body)}


def maintenance_notice(first_name: str) -> dict:
    body = f"""
    <p style="{GREETING}">Hey {first_name},</p>
    <p>Heads up that <strong>The Honey Groove will be down for scheduled maintenance tomorrow afternoon and evening from 2PM to 12AM ET.</strong></p>
    <p>I'm working through some important compliance updates to make sure the platform is solid before we open up to everyone. These aren't glamorous changes, but they're the right ones to make, and I want to get them right.</p>
    <p>You'll see the site come back online by midnight tomorrow. If anything runs long I'll send an update.</p>
    <p>Thank you for your patience while we build this the right way!</p>
    {SIG}
    """
    return {
        "subject": "We're Busy Bees! Scheduled Maintenance",
        "html": wrap_email(body),
    }


def email_change_confirmation(username: str, confirm_url: str) -> dict:
    body = f"""
    <p style="{GREETING}">hey @{username},</p>
    <p style="font-size:14px;color:#1E2A3A;">
        you requested to change your email address on the Honey Groove.
        click the button below to confirm your new email.
    </p>
    <div style="text-align:center;margin:28px 0;">
        <a href="{confirm_url}" style="{BTN}">confirm new email</a>
    </div>
    <p style="{MUTED}">if you didn't request this, you can safely ignore this email. your current email will remain unchanged.</p>
    {SIG_SHORT}
    """
    return {
        "subject": "Confirm your new email — The Honey Groove",
        "html": wrap_email(body),
    }
