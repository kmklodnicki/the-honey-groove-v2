"""So Sorry Campaign — Send individually via Resend to existing real users."""

import asyncio
import os
import time
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

ALL_EMAILS = [
    "admin@thehoneygroove.com",
    "albumtest@test.com",
    "andrewhart0218@gmail.com",
    "angelinasmyntyna@gmail.com",
    "britsnail27@gmail.com",
    "cameron.fintan.reid@gmail.com",
    "checkouttest@test.com",
    "contact.ashsvinyl@gmail.com",
    "contact@kathrynklodnicki.com",
    "craftingnatory123@gmail.com",
    "curltest74_fe6dd8a0@nottest.org",
    "cynjean1119@yahoo.com",
    "daria_bensinger@aol.com",
    "demo@example.com",
    "demo@test.com",
    "discoveryb@test.com",
    "emilymclean766@yahoo.com",
    "evanwhnenquiries@gmail.com",
    "feat1@test.com",
    "feeduser26ea28d5@gmail.com",
    "follow1@honey.io",
    "fta@test.com",
    "gb_buyer_test@honey.io",
    "gerardops2001@gmail.com",
    "gfwaters1602@gmail.com",
    "greg.pybus@icloud.com",
    "hayleyav1@gmail.com",
    "hollandgrace456@gmail.com",
    "intlship@honey.io",
    "invitetest@testflow.com",
    "jacksongamer990@gmail.com",
    "jaycemason11@gmail.com",
    "jordansilvers671@gmail.com",
    "jschildknecht@gmail.com",
    "kalie.kaufman@gmail.com",
    "kathryn.klodnicki@gmail.com",
    "katie@thehoneygroove.com",
    "kbstella99@gmail.com",
    "kellansvinyl@gmail.com",
    "kerrilgreene@gmail.com",
    "kimklodnicki@yahoo.com",
    "kmklodnicki@gmail.com",
    "konikolaou@outlook.com",
    "kylievonkittie@gmail.com",
    "lock.helenea@gmail.com",
    "marcusbyork@gmail.com",
    "megpug10@gmail.com",
    "messerly_tris@icloud.com",
    "natalivinyl@gmail.com",
    "navtest@test.com",
    "newtest@example.com",
    "noverify2@honey.io",
    "noverify@honey.io",
    "patrick.seijo@gmail.com",
    "pricetest@test.com",
    "reema.malkani@gmail.com",
    "regtest2@gmail.com",
    "s.nash2965@yahoo.com",
    "simplyluketv@gmail.com",
    "speba507@student.otago.ac.nz",
    "swiftlylyric@gmail.com",
    "swiftlylyrical@gmail.com",
    "test_1772858402@testuser.com",
    "test_block_user1_2bf82954@test.com",
    "test_block_user2_6c0b977d@test.com",
    "test_edit_listing_8f89b3c6@test.com",
    "test_invite_199c43@test.com",
    "test_prod_1772858473@testflow.com",
    "test_prod_1772858666@testflow.com",
    "test_public_43da63_user1@test.com",
    "test_public_b88c5b_user1@test.com",
    "test_us_seller_1772916796@honey.io",
    "test_verify_flow@example.com",
    "testadmin74_83ef3ce4@nottest.org",
    "testcomment74_0807e31b@nottest.org",
    "testcomment74_2f36398c@nottest.org",
    "testdelete65@test.com",
    "testregister@gmail.com",
    "travis13bell@gmail.com",
    "usahoyt@aol.com",
    "vinylcollector@honey.io",
    "wlkelly09@icloud.com",
    "yguindin@hotmail.com",
]

# Filter out test/demo/admin accounts
TEST_PATTERNS = [
    r"@test\.com$",
    r"@testuser\.com$",
    r"@testflow\.com$",
    r"@example\.com$",
    r"@nottest\.org$",
    r"@honey\.io$",
    r"^test_",
    r"^test[a-z]",
    r"^demo@",
    r"^admin@",
    r"^albumtest",
    r"^checkouttest",
    r"^curltest",
    r"^feat\d+@",
    r"^fta@",
    r"^navtest",
    r"^newtest",
    r"^pricetest",
    r"^regtest",
    r"^feeduser[a-f0-9]",
    r"^discoveryb@",
]

def is_test_email(email):
    for pat in TEST_PATTERNS:
        if re.search(pat, email, re.IGNORECASE):
            return True
    return False

RECIPIENTS = [e for e in ALL_EMAILS if not is_test_email(e)]

SUBJECT = "So sorry! Let\u2019s get you back into the groove \U0001F41D"

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>So Sorry — The Honey Groove</title>
</head>
<body style="margin:0;padding:0;background-color:#FAF6EE;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1A1A1A;">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF6EE;">
<tr><td align="center" style="padding:24px 16px;">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06);">

<!-- Header -->
<tr>
<td align="center" style="background-color:#FDE68A;padding:28px 24px 20px;">
<img src="https://www.thehoneygroove.com/logo-wordmark.png" alt="the Honey Groove" width="220" style="display:block;height:auto;"/>
</td>
</tr>

<!-- Body -->
<tr>
<td style="padding:32px 28px 12px;">

<h1 style="font-size:22px;font-weight:700;color:#915527;margin:0 0 20px;line-height:1.3;">
Hi Hive Member,
</h1>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
We're popping into your inbox to apologize for the digital static. You may have received an email from us earlier today that flew out of the hive a bit too early&mdash;if you tried to click that link and hit an error, we are <strong>so sorry</strong> for the confusion!
</p>

<!-- Upgrade Section -->
<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;line-height:1.3;">
The Hive Just Got a Massive Upgrade
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
To keep the groove going, we spent the last 24 hours performing a major infrastructure and security migration. We've moved into our permanent home to ensure the platform is faster, more secure, and ready for the thousands of spins ahead.
</p>

<!-- Clean Press Section -->
<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;line-height:1.3;">
A Clean Press for a New Chapter
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
To ensure the highest level of stability, we've migrated to a clean slate. This means that while your account is safe and sound, some of your earlier beta posts and activity didn't make the move. Think of it like a fresh sleeve for a classic record&mdash;we're starting this next chapter with a more powerful system.
</p>

<!-- Streak Section -->
<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;line-height:1.3;">
The Good News: Your Streak is Safe! &#x1F36F;
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
We know how much those daily spins matter to you. Because we were &ldquo;under the hood&rdquo; today, we've granted every active member a <strong>&lsquo;Safety Spin&rsquo;</strong> for today. Your streak is safe and sound!
</p>

<!-- Secure Account Section -->
<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;line-height:1.3;">
Secure Your Account
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
To sync up with our new security protocols, please use the link below to set a fresh password and jump back into the feed:
</p>

<!-- CTA Button -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:0 0 28px;">
<a href="https://www.thehoneygroove.com/set-password" target="_blank"
   style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;">
Reset Your Password &amp; Sign In
</a>
</td></tr>
</table>

<!-- Divider -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="border-top:1px solid #F0E6D6;padding-top:24px;"></td></tr>
</table>

<!-- Discord -->
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
<strong style="color:#915527;">Join the Community:</strong> We're polishing the hive every single day. If you hit a snag, come hang out with us on Discord:
<a href="https://discord.gg/rMZFGw6CPf" target="_blank" style="color:#915527;font-weight:600;text-decoration:underline;">discord.gg/rMZFGw6CPf</a>
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
Thank you for being such an essential part of our beta and for your patience while we grow. We can't wait to see what you're spinning today!
</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0;">
Best,<br/>
<strong style="color:#915527;">Katie</strong><br/>
<span style="font-size:13px;color:#888;">Founder, The Honey Groove&trade;</span>
</p>

</td>
</tr>

<!-- Footer -->
<tr>
<td align="center" style="padding:20px 28px 24px;border-top:1px solid #F0E6D6;">
<p style="font-size:11px;color:#AAAAAA;margin:0;line-height:1.5;">
&copy; 2026 The Honey Groove&trade; &middot; the vinyl social club, finally.
</p>
</td>
</tr>

</table>

</td></tr>
</table>

</body>
</html>
"""


async def main():
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    sender = os.environ.get("SENDER_EMAIL", "The Honey Groove <hello@thehoneygroove.com>")
    if "<" not in sender:
        sender = f"The Honey Groove <{sender}>"

    total = len(RECIPIENTS)
    success = 0
    failed = []

    print(f"\n{'='*60}")
    print(f"  SO SORRY CAMPAIGN")
    print(f"  Sending to {total} real users (filtered from {len(ALL_EMAILS)} total)")
    print(f"  Skipped: {len(ALL_EMAILS) - total} test/demo accounts")
    print(f"  From: {sender}")
    print(f"  Subject: {SUBJECT}")
    print(f"{'='*60}")
    print(f"\n  Recipients:")
    for e in RECIPIENTS:
        print(f"    - {e}")
    print()

    for i, email in enumerate(RECIPIENTS, 1):
        try:
            params = {
                "from": sender,
                "to": [email],
                "subject": SUBJECT,
                "html": HTML_TEMPLATE,
            }
            result = resend.Emails.send(params)
            rid = result.get("id", "?") if isinstance(result, dict) else result
            print(f"  [{i}/{total}] SENT -> {email}  (id: {rid})")
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
        for email, err in failed:
            print(f"    - {email}: {err}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
