# HoneyGroove PRD

## Problem Statement
A social platform for vinyl collectors called **The HoneyGroove** — the vinyl social club. Users track their collection, log spins, share activity, import from Discogs, hunt for records (ISO), follow friends, trade vinyl, and interact through a rich social feed.

## Branding
- **Colors:** Honey #c8861a, Honey Light #e8a820, Honey Dark #7a5008, Cream #faf6ee, Parchment #f5efe2
- **Fonts:** Playfair Display (headings), Cormorant Garamond (body) — planned design update

## Core Pages
1. **The Hive** — Social feed with composer bar (Now Spinning, New Haul, ISO, Vinyl Mood)
2. **Explore** — Discovery page with Feed tab and People tab (search + suggestions)
3. **Collection** — Personal vinyl library with sorting + Discogs import + Add Record
4. **ISO & Market** — Vinyl wish list (ISO), peer-to-peer marketplace listings with photos
5. **My Trades** — Trade management with Active/History tabs, trade detail modal
6. **Profile** — 4 tabs: Collection, ISO, Spinning, Trades

## Implemented Features
1. User auth (register, login, JWT, demo account)
2. Vinyl collection tracking via Discogs search
3. Import from Discogs (OAuth 1.0a or personal token, progress UI, Sync Now)
4. Unified posts system — 6 post types
5. Composer bar with 4 chip modals
6. Post-type-specific card layouts in feed
7. Comments & Likes on all posts
8. Shareable graphics (square + story)
9. Collection sorting (10 options)
10. Profile photos (upload or default bee avatar)
11. ISO standalone page with tags, search, filters, stats
12. Profile 4 tabs (Collection, ISO, Spinning, Trades)
13. Friends/Following — follow/unfollow, follower/following list modals, suggested users, user search
14. Explore People tab with search and suggestions
15. **Vinyl Mood Overhaul** — 12 moods with emojis, dynamic modal background colors, animated selection, mood-specific button text/color/placeholder, mood-colored feed cards
16. **Marketplace Photo Upload** — Listings require 1-10 uploaded photos with gallery carousel
17. **Trade System Phase 1** — Full trade status machine (PROPOSED → COUNTERED → ACCEPTED → DECLINED), propose trade from TRADE listings, accept/counter/decline, boot field (settled directly between traders), messaging, Trades page, Profile Trades tab

## Trade System (Phase 1 — Implemented)
- **Propose:** Buyer selects a record from their collection to offer against a TRADE listing. Optional boot (cash on top) and message.
- **Respond:** Seller can Accept, Counter (pick different record from buyer's collection or adjust boot), or Decline.
- **Counter:** Either party can counter back. Counter allows requesting a different record and/or changing boot amount/direction.
- **Accept:** On accept, listing status changes to IN_TRADE (delisted from marketplace).
- **Boot:** Display/agreement field only — "settled directly between traders" — no Stripe connection yet.
- **Messages:** In-trade messaging between parties.

## Upcoming
- **P0: Trade System Phase 2** — Shipping window (5 days), tracking numbers, live status, auto-cancel, confirmation window (48h), auto-complete, record transfer on completion
- **P0: Trade System Phase 3** — Dispute flow (photo upload, 24h response, admin review dashboard), mandatory ratings before next trade
- **P1: Stripe Connect** — Escrow payments for Buy Now / Make Offer marketplace listings
- **P1: Notifications** — ISO matches, likes, offers, trade updates, payouts
- **P2: Explore Enhancements** — Trending records, active ISO listings alongside People tab
- **P2: Hauls Feature** — Dedicated hauls page beyond the composer post
- **P2: HoneyGroove Weekly** — Weekly summary aggregation + display
- **P2: Monetization** — Pro membership, 4% transaction fee, Verified Seller badge

## Data Model
```
posts, records, spins, hauls, iso_items, listings (with photo_urls[]),
likes, comments, followers,
trades: {id, listing_id, initiator_id, responder_id, offered_record_id,
         listing_record_id, boot_amount, boot_direction, status, messages[],
         counter: {record_id, boot_amount, boot_direction, by_user_id},
         created_at, updated_at}
```

## Test Credentials
- Email: demo@example.com / Password: password123
- Email: trader@example.com / Password: password123
