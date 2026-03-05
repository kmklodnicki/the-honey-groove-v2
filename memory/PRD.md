# HoneyGroove PRD

## Problem Statement
A social platform for vinyl collectors called **The HoneyGroove** — the vinyl social club. Users track their collection, log spins, share activity, import from Discogs, hunt for records (ISO), follow friends, trade vinyl, and interact through a rich social feed.

## Branding
- Colors: Honey #c8861a, Honey Light #e8a820, Honey Dark #7a5008, Cream #faf6ee, Parchment #f5efe2
- Fonts: Playfair Display (headings), Cormorant Garamond (body) — planned design update

## Core Pages
1. **The Hive** — Social feed with composer bar (Now Spinning, New Haul, ISO, Vinyl Mood)
2. **Explore** — Discovery page with Feed/People tabs
3. **Collection** — Personal vinyl library with sorting + Discogs import + Add Record
4. **ISO & Market** — Vinyl wish list, peer-to-peer marketplace with required photos
5. **My Trades** — Full trade management (Active/History tabs, detail modal)
6. **Profile** — 4 tabs: Collection, ISO, Spinning, Trades
7. **Admin Disputes** — Admin-only dispute review dashboard

## Implemented Features
1-14: Auth, Collection, Discogs Import, Feed, Composer, Post Cards, Comments/Likes, Shareable Graphics, Sorting, Profile Photos, ISO Page, Profile Tabs, Following System, Explore
15. **Vinyl Mood Overhaul** — 12 moods with emojis, dynamic backgrounds, animated selection, per-mood button/placeholder
16. **Marketplace Photo Upload** — 1-10 required photos with gallery carousel
17. **Trade System (Complete)**:
    - Phase 1: Propose/Counter/Accept/Decline with boot (cash on top, settled directly)
    - Phase 2: 5-day shipping window, tracking upload, live status, 48h confirmation, auto-complete, record transfer
    - Phase 3: Dispute flow (photos, 24h response, admin review), mandatory 1-5 star ratings, admin disputes dashboard

## Trade Status Machine
```
PROPOSED → (Counter) → COUNTERED → (Accept/Decline)
PROPOSED/COUNTERED → ACCEPTED → SHIPPING (5-day deadline)
SHIPPING → CONFIRMING (both ship, 48h deadline) → COMPLETED (both confirm, records transfer)
SHIPPING/CONFIRMING → DISPUTED → Admin resolves (COMPLETED/CANCELLED/PARTIAL)
COMPLETED → Mandatory rating before next trade
```

## Upcoming (User's Roadmap)
- **P1: Stripe Connect** — Escrow payments for Buy Now / Make Offer marketplace listings
- **P1: Notifications** — ISO matches, trade updates, likes, follows
- **P2: Explore Enhancements** — Trending records, active ISO listings
- **P2: Hauls Feature** — Dedicated hauls page
- **P2: HoneyGroove Weekly** — Weekly summary aggregation + display
- **P2: Monetization** — Pro membership, 4% transaction fee, Verified Seller badge

## Data Model
```
users, posts, records, spins, hauls, iso_items,
listings (photo_urls[]),
likes, comments, followers,
trades: {id, listing_id, initiator_id, responder_id, offered_record_id,
         boot_amount, boot_direction, status, messages[], counter,
         shipping: {initiator: {tracking, carrier, shipped_at}, responder: {...}},
         shipping_deadline, confirmation_deadline, confirmations: {user_id: bool},
         dispute: {opened_by, reason, photo_urls, response, resolution},
         ratings: {user_id: {rating, review, rated_user_id}},
         created_at, updated_at}
trade_ratings: {trade_id, rater_id, rated_user_id, rating, review}
```

## Test Credentials
- Admin: demo@example.com / password123 (is_admin: true)
- Trader: trader@example.com / password123
