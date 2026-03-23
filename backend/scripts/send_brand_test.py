"""Send one email per template to verify brand compliance."""
import os
import sys
import resend
from dotenv import load_dotenv

# Ensure imports resolve from backend/
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.getcwd())
load_dotenv()
load_dotenv(".env.local", override=True)

resend.api_key = os.environ.get("RESEND_API_KEY")
sender_raw = os.environ.get("SENDER_EMAIL", "hello@thehoneygroove.com")
sender = f"The Honey Groove <{sender_raw}>" if "<" not in sender_raw else sender_raw
TARGET = "kmklodnicki@gmail.com"


def send(subject, html, label):
    r = resend.Emails.send({"from": sender, "to": [TARGET], "subject": subject, "html": html})
    print(f"  [{label}] {r.get('id', r)}")


from templates.emails import (
    welcome,
    weekly_wax_ready,
    gold_welcome,
    release_updates,
    new_trade_offer,
    sale_confirmed_seller,
)

print(f"Sending brand compliance test emails to {TARGET}...\n")

# 1. Welcome
t = welcome("Katie")
send(t["subject"], t["html"], "Welcome")

# 2. Weekly Wax
t = weekly_wax_ready(
    username="Katie",
    personality_label="The Obsessive Digger",
    top_artist="Ariana Grande",
    top_spins=47,
    closing_line="You couldn\u2019t stop adding. We respect the commitment.",
    date_range="Mar 10 \u2013 Mar 16, 2026",
    records_added=12,
    avg_value="$28",
)
send(t["subject"], t["html"], "Weekly Wax")

# 3. Gold Welcome
t = gold_welcome("Katie")
send(t["subject"], t["html"], "Gold Welcome")

# 4. Release Updates
t = release_updates(
    sections=[
        {"title": "The Hive", "items": ["Redesigned Daily Prompt with share cards", "New post types: Poll and Randomizer"]},
        {"title": "Nectar", "items": ["Honeycomb Rooms are live", "Hot Right Now charts updated hourly"]},
        {"title": "The Vault", "items": ["Cleaner album art display", "Hidden Gems moved above the fold"]},
    ],
    date_str="March 20, 2026",
)
send(t["subject"], t["html"], "Release Updates")

# 5. Trade Offer
t = new_trade_offer(
    username="Katie",
    proposer="vinylkid",
    record_name="Eternal Sunshine",
    their_record="Turquoise Marble",
    sweetener="",
    trade_url="https://thehoneygroove.com/honeypot",
    profile_url="https://thehoneygroove.com/profile/vinylkid",
)
send(t["subject"], t["html"], "Trade Offer")

# 6. Sale Complete
t = sale_confirmed_seller(
    username="Katie",
    album="Eternal Sunshine",
    artist="Ariana Grande",
    price="38.00",
    fee_amount="1.52",
    payout_amount="36.48",
    fee_pct="4",
    sale_url="https://thehoneygroove.com/honeypot",
)
send(t["subject"], t["html"], "Sale Complete")

print(f"\nDone. 6 emails sent to {TARGET}")
