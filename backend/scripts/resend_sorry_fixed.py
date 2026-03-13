"""EMERGENCY FIX: Resend So Sorry emails with corrected /forgot-password link."""

import asyncio
import os
import time

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

# Same 46 real users from original campaign
RECIPIENTS = [
    "andrewhart0218@gmail.com",
    "angelinasmyntyna@gmail.com",
    "britsnail27@gmail.com",
    "cameron.fintan.reid@gmail.com",
    "contact.ashsvinyl@gmail.com",
    "contact@kathrynklodnicki.com",
    "craftingnatory123@gmail.com",
    "cynjean1119@yahoo.com",
    "daria_bensinger@aol.com",
    "emilymclean766@yahoo.com",
    "evanwhnenquiries@gmail.com",
    "gerardops2001@gmail.com",
    "gfwaters1602@gmail.com",
    "greg.pybus@icloud.com",
    "hayleyav1@gmail.com",
    "hollandgrace456@gmail.com",
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
    "patrick.seijo@gmail.com",
    "reema.malkani@gmail.com",
    "s.nash2965@yahoo.com",
    "simplyluketv@gmail.com",
    "speba507@student.otago.ac.nz",
    "swiftlylyric@gmail.com",
    "swiftlylyrical@gmail.com",
    "travis13bell@gmail.com",
    "usahoyt@aol.com",
    "wlkelly09@icloud.com",
    "yguindin@hotmail.com",
]

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

<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;line-height:1.3;">
The Hive Just Got a Massive Upgrade
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
To keep the groove going, we spent the last 24 hours performing a major infrastructure and security migration. We've moved into our permanent home to ensure the platform is faster, more secure, and ready for the thousands of spins ahead.
</p>

<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;line-height:1.3;">
A Clean Press for a New Chapter
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
To ensure the highest level of stability, we've migrated to a clean slate. This means that while your account is safe and sound, some of your earlier beta posts and activity didn't make the move. Think of it like a fresh sleeve for a classic record&mdash;we're starting this next chapter with a more powerful system.
</p>

<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;line-height:1.3;">
The Good News: Your Streak is Safe! &#x1F36F;
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
We know how much those daily spins matter to you. Because we were &ldquo;under the hood&rdquo; today, we've granted every active member a <strong>&lsquo;Safety Spin&rsquo;</strong> for today. Your streak is safe and sound!
</p>

<p style="font-size:17px;font-weight:700;color:#915527;margin:0 0 8px;line-height:1.3;">
Secure Your Account
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
To sync up with our new security protocols, please use the link below to set a fresh password and jump back into the feed:
</p>

<!-- CTA Button — FIXED: uses /forgot-password which exists in production -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:0 0 28px;">
<a href="https://www.thehoneygroove.com/forgot-password" target="_blank"
   style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;">
Reset Your Password &amp; Sign In
</a>
</td></tr>
</table>

<!-- Divider -->
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
    print(f"  EMERGENCY RESEND: So Sorry (fixed CTA)")
    print(f"  Link: /forgot-password (was /set-password)")
    print(f"  Sending to {total} recipients")
    print(f"{'='*60}\n")

    for i, email in enumerate(RECIPIENTS, 1):
        try:
            result = resend.Emails.send({
                "from": sender,
                "to": [email],
                "subject": SUBJECT,
                "html": HTML_TEMPLATE,
            })
            rid = result.get("id", "?") if isinstance(result, dict) else result
            print(f"  [{i}/{total}] SENT -> {email}  (id: {rid})")
            success += 1
        except Exception as e:
            print(f"  [{i}/{total}] FAIL -> {email}  ({e})")
            failed.append((email, str(e)))
        if i < total:
            time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"  RESEND COMPLETE: {success}/{total}")
    if failed:
        print(f"  Failed: {len(failed)}")
        for e, err in failed:
            print(f"    - {e}: {err}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())
