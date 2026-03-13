"""Beta Welcome Email Campaign — Send individually via Resend."""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

RECIPIENTS = [
    "aarnett365@gmail.com",
    "alissa200@gmail.com",
    "angeldimick3@gmail.com",
    "appleconner@me.com",
    "beautybylandsel@gmail.com",
    "blakenjensen07@gmail.com",
    "caroline.dissing@hotmail.com",
    "cd1102@hotmail.com",
    "clementebrito355@gmail.com",
    "clsnyder1997@gmail.com",
    "coleevan04@gmail.com",
    "contact@katieintheafterglow.com",
    "danabrigoli@ymail.com",
    "ellaspinsvinyl@gmail.com",
    "gabbydoesreading@gmail.com",
    "gaperez63@gmail.com",
    "grace.shalee@gmail.com",
    "haleychilders2@gmail.com",
    "hannah.griffis77@gmail.com",
    "jenziboi@gmail.com",
    "jlpennington2014@gmail.com",
    "kaleb.mayfield@icloud.com",
    "karmadone2016@yahoo.com",
    "kayelizabeth1024@gmail.com",
    "kellanharringtonpham@gmail.com",
    "kevincatchall@icloud.com",
    "kim.klodnicki@gmail.com",
    "kylie.quinonez@gmail.com",
    "m.m.mendoz@gmail.com",
    "m.p.m.debruijn@outlook.com",
    "macdagienski@gmail.com",
    "mackenziedoehr63@gmail.com",
    "maizygrace56@gmail.com",
    "mctyler521@gmail.com",
    "michellereadsandspins@gmail.com",
    "misurecmatej@protonmail.com",
    "noidc537@gmail.com",
    "queennickib1tch@gmail.com",
    "ronjafan123@gmail.com",
    "sophiewatson2019@icloud.com",
    "spang714@gmail.com",
    "stramonte21@icloud.com",
    "sutterfield.allison@yahoo.com",
    "tornadosplash44@gmail.com",
    "torturedmomschairman@gmail.com",
    "tucker.parks190@gmail.com",
    "vinylbymarcus@gmail.com",
    "vinylcharms@gmail.com",
    "ward281@ymail.com",
]

SUBJECT = "You're in! Welcome to the Beta Hive \U0001F41D"

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Welcome to The Honey Groove</title>
</head>
<body style="margin:0;padding:0;background-color:#FAF6EE;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1A1A1A;">

<!-- Wrapper -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF6EE;">
<tr><td align="center" style="padding:24px 16px;">

<!-- Card -->
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
Hey there,
</h1>

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

<p style="font-size:15px;line-height:1.7;color:#915527;font-weight:600;margin:0 0 16px;">
How to Get Started:
</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
Set your password and claim your profile to join the community:
</p>

<!-- CTA Button -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:0 0 28px;">
<a href="https://www.thehoneygroove.com/set-password" target="_blank"
   style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;">
Set Your Password &amp; Sign In
</a>
</td></tr>
</table>

<!-- Divider -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="border-top:1px solid #F0E6D6;padding-top:24px;"></td></tr>
</table>

<p style="font-size:15px;line-height:1.7;color:#915527;font-weight:600;margin:0 0 12px;">
Inside the Hive Today:
</p>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 8px;">
<tr>
<td width="24" valign="top" style="font-size:15px;color:#915527;padding-top:2px;">&bull;</td>
<td style="font-size:15px;line-height:1.7;color:#333;">
<strong>Daily Prompts:</strong> Every day we drop a new question. Today's is live at the top of your feed&mdash;come tell us what you're spinning!
</td>
</tr>
</table>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
<tr>
<td width="24" valign="top" style="font-size:15px;color:#915527;padding-top:2px;">&bull;</td>
<td style="font-size:15px;line-height:1.7;color:#333;">
<strong>Feedback:</strong> If you hit a snag or have an idea, come hang out with us on our Discord:
<a href="https://discord.gg/rMZFGw6CPf" target="_blank" style="color:#915527;font-weight:600;text-decoration:underline;">discord.gg/rMZFGw6CPf</a>
</td>
</tr>
</table>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">
We built this for the people who still believe in the magic of an album. Welcome to the Hive.
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
<!-- /Card -->

</td></tr>
</table>
<!-- /Wrapper -->

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
    print(f"  BETA WELCOME CAMPAIGN")
    print(f"  Sending to {total} recipients")
    print(f"  From: {sender}")
    print(f"  Subject: {SUBJECT}")
    print(f"{'='*60}\n")

    for i, email in enumerate(RECIPIENTS, 1):
        try:
            params = {
                "from": sender,
                "to": [email],
                "subject": SUBJECT,
                "html": HTML_TEMPLATE,
            }
            result = resend.Emails.send(params)
            print(f"  [{i}/{total}] SENT -> {email}  (id: {result.get('id', '?') if isinstance(result, dict) else result})")
            success += 1
        except Exception as e:
            print(f"  [{i}/{total}] FAIL -> {email}  ({e})")
            failed.append((email, str(e)))

        # Delay between sends to avoid rate limits
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
