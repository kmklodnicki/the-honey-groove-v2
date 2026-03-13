"""
RELEASE THE HIVE — Campaign Go-Live Script
Group A: Existing users → "Smooth Honey" recovery email → /forgot-password
Group B: New beta signups → "Fresh Invite" email → /invite/[token]
Throttle: 1 second between each send
"""
import asyncio
import csv
import io
import os
import sys
import uuid
from datetime import datetime, timezone

import aiohttp
import resend

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from motor.motor_asyncio import AsyncIOMotorClient

resend.api_key = os.environ.get("RESEND_API_KEY", "")
SENDER = "The Honey Groove <hello@thehoneygroove.com>"
REPLY_TO = "hello@thehoneygroove.com"
FRONTEND = "https://www.thehoneygroove.com"

# Test-account patterns to exclude
EXCLUDE_PATTERNS = [
    "@test.com", "@testuser.com", "@nottest.org", "@honey.io",
    "@testflow.com", "@example.com", "test_", "curltest",
    "testadmin", "testcomment", "testdelete", "testregister",
    "feeduser", "navtest", "pricetest", "checkouttest",
    "albumtest", "discoveryb", "demo@", "feat1@",
    "invitetest", "regtest", "noverify", "fta@test",
    "katie@test.com",
]

def is_test_email(email: str) -> bool:
    e = email.lower()
    return any(p in e for p in EXCLUDE_PATTERNS)


# ── Group A: "Smooth Honey" recovery email ──
def group_a_html():
    forgot_url = f"{FRONTEND}/forgot-password"
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

<h1 style="font-size:22px;font-weight:700;color:#915527;margin:0 0 20px;line-height:1.3;">We owe you an apology.</h1>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
During our recent upgrade, some things didn't go as smoothly as we'd planned. Your experience was affected, and for that, we're truly sorry.
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
The good news? We've moved into our permanent home with upgraded security and a faster, smoother experience. Your account is safe and waiting for you.
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
To get back in, just reset your password below:
</p>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:0 0 28px;">
<a href="{forgot_url}" target="_blank"
   style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;">
Reset Password &amp; Sign In
</a>
</td></tr>
</table>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
We're building this in the open, and your patience and feedback mean everything. Welcome back to the Hive.
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


# ── Group B: "Fresh Invite" email ──
def group_b_html(claim_url: str):
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
Join Now
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
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[os.environ.get("DB_NAME")]

    # ── Load CSVs ──
    group_a_raw = []
    group_b_raw = []

    async with aiohttp.ClientSession() as session:
        async with session.get("https://customer-assets.emergentagent.com/job_d71d3f29-74d5-4805-bba7-0c90dcdc827a/artifacts/93ji5j52_GROUPA.csv") as r:
            text = await r.text()
            reader = csv.reader(io.StringIO(text))
            for row in reader:
                if row and row[0].strip() and "@" in row[0]:
                    group_a_raw.append(row[0].strip().lower())

        async with session.get("https://customer-assets.emergentagent.com/job_d71d3f29-74d5-4805-bba7-0c90dcdc827a/artifacts/92cugt38_groupB.csv") as r:
            text = await r.text()
            reader = csv.reader(io.StringIO(text))
            for row in reader:
                if row and row[0].strip() and "@" in row[0]:
                    group_b_raw.append(row[0].strip().lower())

    # Filter test accounts from Group A
    group_a = [e for e in group_a_raw if not is_test_email(e)]
    group_b = [e for e in group_b_raw if not is_test_email(e)]

    # Deduplicate
    group_a = list(dict.fromkeys(group_a))
    group_b = list(dict.fromkeys(group_b))

    excluded_a = len(group_a_raw) - len(group_a)
    excluded_b = len(group_b_raw) - len(group_b)

    print("=" * 60)
    print("RELEASE THE HIVE — Campaign Summary")
    print("=" * 60)
    print(f"Group A (Existing Users → Recovery): {len(group_a)} emails ({excluded_a} test accounts filtered)")
    print(f"Group B (New Signups → Fresh Invite): {len(group_b)} emails ({excluded_b} test accounts filtered)")
    print(f"Total emails to send: {len(group_a) + len(group_b)}")
    print(f"Domain: {FRONTEND}")
    print(f"Throttle: 1 second between sends")
    print("=" * 60)

    success_a, fail_a = 0, 0
    success_b, fail_b = 0, 0

    # ── GROUP A: Smooth Honey Recovery ──
    print(f"\n--- GROUP A: Sending 'Smooth Honey' recovery to {len(group_a)} users ---")
    a_html = group_a_html()
    for i, email in enumerate(group_a, 1):
        try:
            params = {
                "from": SENDER,
                "to": [email],
                "reply_to": REPLY_TO,
                "subject": "We owe you an apology (and a smoother Hive)",
                "html": a_html,
            }
            result = resend.Emails.send(params)
            success_a += 1
            print(f"  [{i}/{len(group_a)}] SENT → {email} (id: {result.get('id', 'n/a')[:12]})")
        except Exception as ex:
            fail_a += 1
            print(f"  [{i}/{len(group_a)}] FAIL → {email} — {ex}")
        await asyncio.sleep(1)

    # ── GROUP B: Fresh Invite ──
    print(f"\n--- GROUP B: Sending 'Fresh Invite' to {len(group_b)} users ---")
    for i, email in enumerate(group_b, 1):
        try:
            # Invalidate old tokens & generate fresh one
            await db.invite_tokens.delete_many({"email": email})
            new_token = str(uuid.uuid4())
            await db.invite_tokens.insert_one({
                "token": new_token,
                "email": email,
                "is_existing": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            claim_url = f"{FRONTEND}/invite/{new_token}"

            params = {
                "from": SENDER,
                "to": [email],
                "reply_to": REPLY_TO,
                "subject": "Your invite to The Honey Groove is here!",
                "html": group_b_html(claim_url),
            }
            result = resend.Emails.send(params)
            success_b += 1
            print(f"  [{i}/{len(group_b)}] SENT → {email} (id: {result.get('id', 'n/a')[:12]})")
        except Exception as ex:
            fail_b += 1
            print(f"  [{i}/{len(group_b)}] FAIL → {email} — {ex}")
        await asyncio.sleep(1)

    # ── Final Report ──
    print("\n" + "=" * 60)
    print("CAMPAIGN COMPLETE")
    print("=" * 60)
    print(f"Group A: {success_a} sent / {fail_a} failed (of {len(group_a)})")
    print(f"Group B: {success_b} sent / {fail_b} failed (of {len(group_b)})")
    print(f"TOTAL:   {success_a + success_b} sent / {fail_a + fail_b} failed")
    print(f"All links point to: {FRONTEND}")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
