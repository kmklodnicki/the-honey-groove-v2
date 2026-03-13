"""Send clean test emails with verified clickable CTA buttons."""
import os
import resend
from dotenv import load_dotenv

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

resend.api_key = os.environ.get("RESEND_API_KEY")
sender = os.environ.get("SENDER_EMAIL", "")
if "<" not in sender:
    sender = f"The Honey Groove <{sender}>"

TARGET = "kmklodnicki@gmail.com"
TOKEN = "test-golden-ticket-kmk"

# ── TEST EMAIL 1: Group A (Existing User) ──────────────────────
SUBJECT_A = "So sorry! Let\u2019s get you back into the groove \U0001F41D"
HTML_A = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#FAF6EE;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1A1A1A;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF6EE;">
<tr>
<td align="center" style="padding:24px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06);">

<tr>
<td align="center" style="background-color:#FDE68A;padding:28px 24px 20px;">
<img src="https://www.thehoneygroove.com/logo-wordmark.png" alt="the Honey Groove" width="220" style="display:block;height:auto;">
</td>
</tr>

<tr>
<td style="padding:32px 28px 12px;">
<h1 style="font-size:22px;font-weight:700;color:#915527;margin:0 0 20px;line-height:1.3;">Hi Katie,</h1>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">We're popping into your inbox to apologize for the digital static earlier today. To ensure your account is airtight following our major security upgrades, we've migrated to a permanent, faster home.</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">To sync your profile and protect your streak, please use the link below to verify your account and set a fresh password:</p>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="center" style="padding:0 0 28px;">
<!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="https://www.thehoneygroove.com/forgot-password" style="height:48px;v-text-anchor:middle;width:300px;" arcsize="50%" fillcolor="#915527">
<w:anchorlock/>
<center style="color:#FDE68A;font-family:'Helvetica Neue',sans-serif;font-size:16px;font-weight:bold;">Reset Your Password &amp; Sign In</center>
</v:roundrect>
<![endif]-->
<!--[if !mso]><!-->
<a href="https://www.thehoneygroove.com/forgot-password" target="_blank" style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;mso-hide:all;">Reset Your Password &amp; Sign In</a>
<!--<![endif]-->
</td>
</tr>
</table>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
<tr>
<td style="background:#FEF9E7;border-radius:12px;padding:16px 20px;border:1px solid rgba(145,85,39,0.1);">
<p style="font-size:15px;line-height:1.7;color:#915527;margin:0;font-weight:600;">&#x1F36F; Your Streak is Safe!</p>
<p style="font-size:14px;line-height:1.6;color:#333;margin:6px 0 0;">Because of the downtime, we've granted you a 'Safety Spin' for today. Welcome back!</p>
</td>
</tr>
</table>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0;">Best,<br><strong style="color:#915527;">Katie</strong><br><span style="font-size:13px;color:#888;">Founder, The Honey Groove&#8482;</span></p>
</td>
</tr>

<tr>
<td align="center" style="padding:20px 28px 24px;border-top:1px solid #F0E6D6;">
<p style="font-size:11px;color:#AAAAAA;margin:0;line-height:1.5;">&copy; 2026 The Honey Groove&#8482; &middot; the vinyl social club, finally.</p>
</td>
</tr>

</table>
</td>
</tr>
</table>
</body>
</html>"""

# ── TEST EMAIL 2: Group B (New Beta Invitee) ──────────────────
SUBJECT_B = "Your Golden Ticket to The Honey Groove \U0001F3AB"
HTML_B = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#FAF6EE;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1A1A1A;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF6EE;">
<tr>
<td align="center" style="padding:24px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06);">

<tr>
<td align="center" style="background-color:#FDE68A;padding:28px 24px 20px;">
<img src="https://www.thehoneygroove.com/logo-wordmark.png" alt="the Honey Groove" width="220" style="display:block;height:auto;">
</td>
</tr>

<tr>
<td style="padding:32px 28px 12px;">
<h1 style="font-size:22px;font-weight:700;color:#915527;margin:0 0 20px;line-height:1.3;">Hi Katie,</h1>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">The wait is over. Your invite to <strong>The Honey Groove</strong> is officially ready!</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 24px;">As a Beta Tester, you're getting early access to the hive. We've generated a unique invite link just for you so you can skip the friction and get straight to the music:</p>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="center" style="padding:0 0 28px;">
<!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="https://www.thehoneygroove.com/invite/{TOKEN}" style="height:48px;v-text-anchor:middle;width:300px;" arcsize="50%" fillcolor="#915527">
<w:anchorlock/>
<center style="color:#FDE68A;font-family:'Helvetica Neue',sans-serif;font-size:16px;font-weight:bold;">Claim Your Beta Invite</center>
</v:roundrect>
<![endif]-->
<!--[if !mso]><!-->
<a href="https://www.thehoneygroove.com/invite/{TOKEN}" target="_blank" style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;mso-hide:all;">Claim Your Beta Invite</a>
<!--<![endif]-->
</td>
</tr>
</table>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">Things aren't perfect yet, so your feedback on our Discord is encouraged: <a href="https://discord.gg/rMZFGw6CPf" target="_blank" style="color:#915527;font-weight:600;text-decoration:underline;">discord.gg/rMZFGw6CPf</a>. Come join the daily prompt!</p>

<p style="font-size:15px;line-height:1.7;color:#333;margin:0;">Best,<br><strong style="color:#915527;">Katie</strong><br><span style="font-size:13px;color:#888;">Founder, The Honey Groove&#8482;</span></p>
</td>
</tr>

<tr>
<td align="center" style="padding:20px 28px 24px;border-top:1px solid #F0E6D6;">
<p style="font-size:11px;color:#AAAAAA;margin:0;line-height:1.5;">&copy; 2026 The Honey Groove&#8482; &middot; the vinyl social club, finally.</p>
</td>
</tr>

</table>
</td>
</tr>
</table>
</body>
</html>"""

# ── SEND ──
print("Sending Test Email 1 (Group A)...")
r1 = resend.Emails.send({"from": sender, "to": [TARGET], "subject": SUBJECT_A, "html": HTML_A})
print(f"  SENT: {r1.get('id', r1)}")

print("Sending Test Email 2 (Group B)...")
r2 = resend.Emails.send({"from": sender, "to": [TARGET], "subject": SUBJECT_B, "html": HTML_B})
print(f"  SENT: {r2.get('id', r2)}")

print("\nDone! Check kmklodnicki@gmail.com for both emails.")
print(f"  Group A CTA: https://www.thehoneygroove.com/forgot-password")
print(f"  Group B CTA: https://www.thehoneygroove.com/invite/{TOKEN}")
