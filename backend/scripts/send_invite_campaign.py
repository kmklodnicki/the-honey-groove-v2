"""Generate unique invite tokens and send claim-invite emails to both groups."""

import asyncio
import os
import sys
import time
import uuid
import re
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

# ── GROUP A: Existing Users (46 real users) ──
GROUP_A = [
    "andrewhart0218@gmail.com", "angelinasmyntyna@gmail.com", "britsnail27@gmail.com",
    "cameron.fintan.reid@gmail.com", "contact.ashsvinyl@gmail.com", "contact@kathrynklodnicki.com",
    "craftingnatory123@gmail.com", "cynjean1119@yahoo.com", "daria_bensinger@aol.com",
    "emilymclean766@yahoo.com", "evanwhnenquiries@gmail.com", "gerardops2001@gmail.com",
    "gfwaters1602@gmail.com", "greg.pybus@icloud.com", "hayleyav1@gmail.com",
    "hollandgrace456@gmail.com", "jacksongamer990@gmail.com", "jaycemason11@gmail.com",
    "jordansilvers671@gmail.com", "jschildknecht@gmail.com", "kalie.kaufman@gmail.com",
    "kathryn.klodnicki@gmail.com", "katie@thehoneygroove.com", "kbstella99@gmail.com",
    "kellansvinyl@gmail.com", "kerrilgreene@gmail.com", "kimklodnicki@yahoo.com",
    "kmklodnicki@gmail.com", "konikolaou@outlook.com", "kylievonkittie@gmail.com",
    "lock.helenea@gmail.com", "marcusbyork@gmail.com", "megpug10@gmail.com",
    "messerly_tris@icloud.com", "natalivinyl@gmail.com", "patrick.seijo@gmail.com",
    "reema.malkani@gmail.com", "s.nash2965@yahoo.com", "simplyluketv@gmail.com",
    "speba507@student.otago.ac.nz", "swiftlylyric@gmail.com", "swiftlylyrical@gmail.com",
    "travis13bell@gmail.com", "usahoyt@aol.com", "wlkelly09@icloud.com", "yguindin@hotmail.com",
]

# ── GROUP B: New Users (49 beta signups) ──
GROUP_B = [
    "aarnett365@gmail.com", "alissa200@gmail.com", "angeldimick3@gmail.com",
    "appleconner@me.com", "beautybylandsel@gmail.com", "blakenjensen07@gmail.com",
    "caroline.dissing@hotmail.com", "cd1102@hotmail.com", "clementebrito355@gmail.com",
    "clsnyder1997@gmail.com", "coleevan04@gmail.com", "contact@katieintheafterglow.com",
    "danabrigoli@ymail.com", "ellaspinsvinyl@gmail.com", "gabbydoesreading@gmail.com",
    "gaperez63@gmail.com", "grace.shalee@gmail.com", "haleychilders2@gmail.com",
    "hannah.griffis77@gmail.com", "jenziboi@gmail.com", "jlpennington2014@gmail.com",
    "kaleb.mayfield@icloud.com", "karmadone2016@yahoo.com", "kayelizabeth1024@gmail.com",
    "kellanharringtonpham@gmail.com", "kevincatchall@icloud.com", "kim.klodnicki@gmail.com",
    "kylie.quinonez@gmail.com", "m.m.mendoz@gmail.com", "m.p.m.debruijn@outlook.com",
    "macdagienski@gmail.com", "mackenziedoehr63@gmail.com", "maizygrace56@gmail.com",
    "mctyler521@gmail.com", "michellereadsandspins@gmail.com", "misurecmatej@protonmail.com",
    "noidc537@gmail.com", "queennickib1tch@gmail.com", "ronjafan123@gmail.com",
    "sophiewatson2019@icloud.com", "spang714@gmail.com", "stramonte21@icloud.com",
    "sutterfield.allison@yahoo.com", "tornadosplash44@gmail.com",
    "torturedmomschairman@gmail.com", "tucker.parks190@gmail.com",
    "vinylbymarcus@gmail.com", "vinylcharms@gmail.com", "ward281@ymail.com",
]

FRONTEND_URL = "https://www.thehoneygroove.com"

# URL pattern: /invite/TOKEN (not query param)
def claim_url_for(token):
    return f"{FRONTEND_URL}/invite/{token}"

# ── Email templates ──

def existing_user_html(claim_url):
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#FAF6EE;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1A1A1A;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF6EE;">
<tr><td align="center" style="padding:24px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
<tr><td align="center" style="background-color:#FDE68A;padding:28px 24px 20px;">
<img src="https://www.thehoneygroove.com/logo-wordmark.png" alt="the Honey Groove" width="220" style="display:block;height:auto;"/>
</td></tr>
<tr><td style="padding:32px 28px 12px;">

<h1 style="font-size:22px;font-weight:700;color:#915527;margin:0 0 20px;line-height:1.3;">Hi Hive Member,</h1>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
We're popping into your inbox to apologize for the digital static. You may have received an email from us earlier today that flew out of the hive a bit too early&mdash;if you tried to click that link and hit an error, we are <strong>so sorry</strong> for the confusion!
</p>

<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;">The Hive Just Got a Massive Upgrade</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
To keep the groove going, we spent the last 24 hours performing a major infrastructure and security migration. We've moved into our permanent home to ensure the platform is faster, more secure, and ready for the thousands of spins ahead.
</p>

<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;">A Clean Press for a New Chapter</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
To ensure the highest level of stability, we've migrated to a clean slate. This means that while your account is safe and sound, some of your earlier beta posts and activity didn't make the move. Think of it like a fresh sleeve for a classic record&mdash;we're starting this next chapter with a more powerful system.
</p>

<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;">The Good News: Your Streak is Safe! &#x1F36F;</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
We know how much those daily spins matter to you. Because we were &ldquo;under the hood&rdquo; today, we've granted every active member a <strong>&lsquo;Safety Spin&rsquo;</strong> for today. Your streak is safe and sound!
</p>

<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;">Secure Your Account</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
To sync up with our new security protocols, click the button below to set a fresh password and jump back into the feed:
</p>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:0 0 28px;">
<a href="{claim_url}" target="_blank"
   style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;">
Reset Your Password &amp; Sign In
</a>
</td></tr>
</table>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="border-top:1px solid #F0E6D6;padding-top:24px;"></td></tr>
</table>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
<strong style="color:#915527;">Join the Community:</strong> We're polishing the hive every single day. If you hit a snag, come hang out with us on Discord:
<a href="https://discord.gg/rMZFGw6CPf" target="_blank" style="color:#915527;font-weight:600;text-decoration:underline;">discord.gg/rMZFGw6CPf</a>
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
Thank you for being such an essential part of our beta and for your patience while we grow. We can't wait to see what you're spinning today!
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0;">Best,<br/><strong style="color:#915527;">Katie</strong><br/><span style="font-size:13px;color:#888;">Founder, The Honey Groove&trade;</span></p>

</td></tr>
<tr><td align="center" style="padding:20px 28px 24px;border-top:1px solid #F0E6D6;">
<p style="font-size:11px;color:#AAAAAA;margin:0;line-height:1.5;">&copy; 2026 The Honey Groove&trade; &middot; the vinyl social club, finally.</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def new_user_html(claim_url):
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#FAF6EE;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1A1A1A;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF6EE;">
<tr><td align="center" style="padding:24px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
<tr><td align="center" style="background-color:#FDE68A;padding:28px 24px 20px;">
<img src="https://www.thehoneygroove.com/logo-wordmark.png" alt="the Honey Groove" width="220" style="display:block;height:auto;"/>
</td></tr>
<tr><td style="padding:32px 28px 12px;">

<h1 style="font-size:22px;font-weight:700;color:#915527;margin:0 0 20px;line-height:1.3;">Hey there,</h1>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
The wait is over. Your invite to <strong>The Honey Groove</strong> is officially here!
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
We've just moved into our permanent home with upgraded security and a faster, smoother experience. Your account has been pre-verified and is ready for you to drop the needle.
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
<strong style="color:#915527;">The Beta Journey:</strong> As one of our first Beta Testers, you're seeing the hive while the honey is still wet. This means things aren't always perfect&mdash;you might hit a snag or find a feature we're still polishing.
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
We're building this in the open, and your feedback is what will make this the ultimate home for vinyl collectors.
</p>

<p style="font-size:15px;line-height:1.7;color:#915527;font-weight:600;margin:0 0 16px;">How to Get Started:</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
Click below to set your password and claim your profile:
</p>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:0 0 28px;">
<a href="{claim_url}" target="_blank"
   style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;">
Set Your Password &amp; Join Now
</a>
</td></tr>
</table>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="border-top:1px solid #F0E6D6;padding-top:24px;"></td></tr>
</table>

<p style="font-size:15px;line-height:1.7;color:#915527;font-weight:600;margin:0 0 12px;">Inside the Hive Today:</p>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 8px;">
<tr><td width="24" valign="top" style="font-size:15px;color:#915527;padding-top:2px;">&bull;</td>
<td style="font-size:15px;line-height:1.7;color:#333;"><strong>Daily Prompts:</strong> Every day we drop a new question. Today's is live at the top of your feed&mdash;come tell us what you're spinning!</td></tr>
</table>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
<tr><td width="24" valign="top" style="font-size:15px;color:#915527;padding-top:2px;">&bull;</td>
<td style="font-size:15px;line-height:1.7;color:#333;"><strong>Feedback:</strong> If you hit a snag or have an idea, come hang out with us on our Discord:
<a href="https://discord.gg/rMZFGw6CPf" target="_blank" style="color:#915527;font-weight:600;text-decoration:underline;">discord.gg/rMZFGw6CPf</a></td></tr>
</table>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
We built this for the people who still believe in the magic of an album. Welcome to the Hive.
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0;">Best,<br/><strong style="color:#915527;">Katie</strong><br/><span style="font-size:13px;color:#888;">Founder, The Honey Groove&trade;</span></p>

</td></tr>
<tr><td align="center" style="padding:20px 28px 24px;border-top:1px solid #F0E6D6;">
<p style="font-size:11px;color:#AAAAAA;margin:0;line-height:1.5;">&copy; 2026 The Honey Groove&trade; &middot; the vinyl social club, finally.</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


async def main():
    import resend
    from motor.motor_asyncio import AsyncIOMotorClient

    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    sender = os.environ.get("SENDER_EMAIL", "The Honey Groove <hello@thehoneygroove.com>")
    if "<" not in sender:
        sender = f"The Honey Groove <{sender}>"

    # Connect to BOTH databases to insert tokens
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db_local = client[os.environ.get("DB_NAME")]
    db_prod = client["groove-social-beta-test_database"]

    now = datetime.now(timezone.utc).isoformat()

    # Step 1: Generate tokens for all users and insert into DB
    all_tokens = {}

    print(f"\n{'='*60}")
    print(f"  GENERATING INVITE TOKENS")
    print(f"{'='*60}\n")

    all_emails = []
    for email in GROUP_A:
        all_emails.append((email, True, "So sorry! Let\u2019s get you back into the groove \U0001F41D"))
    for email in GROUP_B:
        all_emails.append((email, False, "You're in! Welcome to the Beta Hive \U0001F41D"))

    for email, is_existing, _ in all_emails:
        token = str(uuid.uuid4())
        doc = {
            "token": token,
            "email": email.lower().strip(),
            "is_existing": is_existing,
            "created_at": now,
        }
        # Insert into both databases so the token works regardless of which DB production uses
        await db_local.invite_tokens.insert_one({**doc})
        await db_prod.invite_tokens.insert_one({**doc})
        all_tokens[email] = token
        print(f"  TOKEN: {email} -> {token[:8]}...")

    print(f"\n  Generated {len(all_tokens)} tokens in both databases")

    # Step 2: Send emails
    print(f"\n{'='*60}")
    print(f"  SENDING INVITE EMAILS")
    print(f"  Group A (Existing): {len(GROUP_A)}")
    print(f"  Group B (New):      {len(GROUP_B)}")
    print(f"  Total:              {len(all_emails)}")
    print(f"{'='*60}\n")

    success = 0
    failed = []
    total = len(all_emails)

    for i, (email, is_existing, subject) in enumerate(all_emails, 1):
        token = all_tokens[email]
        claim_url = claim_url_for(token)

        if is_existing:
            html = existing_user_html(claim_url)
        else:
            html = new_user_html(claim_url)

        try:
            result = resend.Emails.send({
                "from": sender,
                "to": [email],
                "subject": subject,
                "html": html,
            })
            rid = result.get("id", "?") if isinstance(result, dict) else result
            group = "A" if is_existing else "B"
            print(f"  [{i}/{total}] GROUP {group} SENT -> {email}  (id: {rid})")
            success += 1
        except Exception as e:
            print(f"  [{i}/{total}] FAIL -> {email}  ({e})")
            failed.append((email, str(e)))

        if i < total:
            time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"  CAMPAIGN COMPLETE")
    print(f"  Sent: {success}/{total}")
    if failed:
        print(f"  Failed: {len(failed)}")
        for e, err in failed:
            print(f"    - {e}: {err}")
    print(f"{'='*60}\n")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
