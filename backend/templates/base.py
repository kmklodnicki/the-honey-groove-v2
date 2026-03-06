"""Base HTML email wrapper for all HoneyGroove emails."""

LOGO_URL = "https://collector-nest.preview.emergentagent.com/logo.png"


def wrap_email(body_html: str, unsubscribe_url: str = "") -> str:
    """Wrap email body in the standard HoneyGroove template."""
    unsub = ""
    if unsubscribe_url:
        unsub = f'<p style="margin:8px 0 0 0;"><a href="{unsubscribe_url}" style="color:#C8861A;text-decoration:underline;font-size:12px;">unsubscribe</a></p>'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#FAF6EE;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#FAF6EE;">
<tr><td align="center" style="padding:32px 16px;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;">

<!-- Logo -->
<tr><td align="center" style="padding:0 0 16px 0;">
<p style="font-family:'Playfair Display',Georgia,serif;font-size:22px;font-weight:700;color:#2A1A06;margin:0;letter-spacing:0.5px;">the honey groove</p>
</td></tr>

<!-- Amber divider -->
<tr><td style="padding:0 0 24px 0;">
<div style="height:1px;background:#C8861A;opacity:0.4;"></div>
</td></tr>

<!-- Body -->
<tr><td style="color:#2A1A06;font-size:15px;line-height:1.7;">
{body_html}
</td></tr>

<!-- Footer -->
<tr><td align="center" style="padding:32px 0 0 0;">
<div style="height:1px;background:#C8861A;opacity:0.2;margin-bottom:16px;"></div>
<p style="color:#8A6B4A;font-size:12px;margin:0;"><a href="https://thehoneygroove.com" style="color:#8A6B4A;text-decoration:none;">thehoneygroove.com</a></p>
{unsub}
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
