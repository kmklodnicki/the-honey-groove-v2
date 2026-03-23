"""Base HTML email wrapper for all HoneyGroove emails."""


def wrap_email(body_html: str, unsubscribe_url: str = "") -> str:
    """Wrap email body in the standard HoneyGroove template."""
    unsub_href = unsubscribe_url if unsubscribe_url else "https://thehoneygroove.com/settings"

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#FFFBF2;font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#FFFBF2;">

<!-- Content area with side padding -->
<tr><td align="center" style="padding:32px 16px 32px 16px;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;">

<!-- Logo — inline text (email-safe) -->
<tr><td align="center" style="padding:0 0 16px 0;">
  <p style="margin:0;line-height:1;">
    <span style="color:#D4A828;font-style:italic;font-family:'DM Sans',-apple-system,sans-serif;font-size:11px;">the </span><span style="font-size:22px;font-weight:700;font-family:'Playfair Display',Georgia,serif;letter-spacing:0.01em;"><span style="color:#1E2A3A;">Honey</span><span style="color:#D4A828;">Groove</span></span>
  </p>
</td></tr>

<!-- Gold divider -->
<tr><td style="padding:0 0 24px 0;">
<div style="height:2px;background:#D4A828;"></div>
</td></tr>

<!-- Body -->
<tr><td style="color:#1E2A3A;font-size:13px;line-height:1.7;font-family:'DM Sans',-apple-system,sans-serif;">
{body_html}
</td></tr>

<!-- Footer -->
<tr><td align="center" style="padding:32px 0 0 0;">
<div style="background:#1E2A3A;border-radius:0 0 12px 12px;padding:24px 20px 20px 20px;text-align:center;">
<p style="margin:0 0 6px 0;">
  <span style="color:#D4A828;font-style:italic;font-family:'DM Sans',-apple-system,sans-serif;font-size:10px;">the </span><span style="font-size:16px;font-weight:700;font-family:'Playfair Display',Georgia,serif;letter-spacing:0.01em;"><span style="color:#FFFFFF;">Honey</span><span style="color:#D4A828;">Groove</span></span>
</p>
<p style="color:#3A4D63;font-size:11px;margin:0 0 10px 0;">The social marketplace for vinyl collectors</p>
<p style="margin:0;font-size:9px;">
  <a href="{unsub_href}" style="color:#3A4D63;text-decoration:underline;">Unsubscribe</a>
  <span style="color:#3A4D63;"> | </span>
  <a href="https://thehoneygroove.com/settings" style="color:#3A4D63;text-decoration:underline;">Preferences</a>
  <span style="color:#3A4D63;"> | </span>
  <a href="https://thehoneygroove.com/privacy" style="color:#3A4D63;text-decoration:underline;">Privacy</a>
</p>
<p style="color:#3A4D63;font-size:8px;margin:8px 0 0 0;opacity:0.6;">The Honey Groove LLC &copy; 2026 &mdash; hello@thehoneygroove.com</p>
</div>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
