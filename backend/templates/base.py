"""Base HTML email wrapper for all HoneyGroove emails."""

LOGO_URL = "https://thehoneygroove.com/logo-wordmark.png"
DRIP_URL = "https://thehoneygroove.com/honey-drip.png"


def wrap_email(body_html: str, unsubscribe_url: str = "") -> str:
    """Wrap email body in the standard HoneyGroove template."""
    unsub = ""
    if unsubscribe_url:
        unsub = f'<p style="margin:8px 0 0 0;"><a href="{unsubscribe_url}" style="color:#3A4D63;text-decoration:underline;font-size:12px;">unsubscribe</a></p>'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#FFFBF2;font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#FFFBF2;">

<!-- Honey Drip — full width, flush to very top edge, no padding anywhere -->
<tr><td align="center" style="padding:0;margin:0;line-height:0;font-size:0;">
<img src="{DRIP_URL}" alt="" width="520" style="display:block;width:100%;max-width:520px;height:auto;margin:0;padding:0;" />
</td></tr>

<!-- Content area with side padding -->
<tr><td align="center" style="padding:0 16px 32px 16px;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;">

<!-- Logo — below drip -->
<tr><td align="center" style="padding:16px 0 8px 0;">
<img src="{LOGO_URL}" alt="the Honey Groove" width="200" style="display:block;max-width:200px;height:auto;" />
</td></tr>

<!-- Gold divider -->
<tr><td style="padding:0 0 24px 0;">
<div style="height:2px;background:#D4A828;"></div>
</td></tr>

<!-- Body -->
<tr><td style="color:#1E2A3A;font-size:15px;line-height:1.7;font-family:'DM Sans',-apple-system,sans-serif;">
{body_html}
</td></tr>

<!-- Footer -->
<tr><td align="center" style="padding:32px 0 0 0;">
<div style="background:#1E2A3A;border-radius:0 0 12px 12px;padding:24px 20px 20px 20px;">
<p style="margin:0 0 8px 0;font-size:16px;font-weight:700;font-family:'Playfair Display',Georgia,serif;letter-spacing:0.01em;">
<span style="color:#FFFFFF;">Honey</span><span style="color:#D4A828;">Groove</span>
</p>
<p style="color:#7A8694;font-size:11px;margin:0 0 8px 0;">the HoneyGroove LLC &mdash; a community for vinyl collectors.</p>
<p style="margin:0;"><a href="https://thehoneygroove.com" style="color:#3A4D63;text-decoration:none;font-size:12px;">thehoneygroove.com</a></p>
{unsub}
</div>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
