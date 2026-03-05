# HoneyGroove PRD

## Problem Statement
A social platform for vinyl collectors called **The Honey Groove** — the vinyl social club. Users track their collection, log spins, share activity, import from Discogs, hunt for records (ISO), follow friends, and interact through a rich social feed.

## Branding
- **Colors:** Honey #c8861a, Honey Light #e8a820, Honey Dark #7a5008, Cream #faf6ee, Parchment #f5efe2
- **Fonts:** Playfair Display (headings), Cormorant Garamond (body) — planned design update
- **Logo:** HoneyGroove wordmark with bee and dotted spiral

## Core Pages
1. **The Hive** — Social feed with composer bar (Now Spinning, New Haul, ISO, Vinyl Mood)
2. **Explore** — Discovery page with Feed tab and People tab (search + suggestions)
3. **Collection** — Personal vinyl library with sorting + Discogs import
4. **ISO** — Standalone vinyl wish list with tags, filters, stats
5. **Profile** — 4 tabs: Collection, ISO, Spinning, Trades

## Implemented Features
1. User auth (register, login, JWT, demo account)
2. Vinyl collection tracking via Discogs search
3. Import from Discogs (OAuth 1.0a or personal token, progress UI, Sync Now)
4. Unified posts system — 6 post types: NOW_SPINNING, NEW_HAUL, ISO, ADDED_TO_COLLECTION, WEEKLY_WRAP, VINYL_MOOD
5. Composer bar with 4 chip modals
6. Post-type-specific card layouts in feed
7. Comments & Likes on all posts
8. Shareable graphics (square 1080x1080 + story 1080x1920)
9. Collection sorting (10 options)
10. Profile photos (upload or default bee avatar)
11. ISO standalone page with tags (OG Press, Factory Sealed, Any, Promo), search, filters, stats
12. Profile 4 tabs (Collection, ISO, Spinning, Trades)
13. Friends/Following — follow/unfollow, follower/following list modals, suggested users, user search
14. Explore People tab with search and suggestions

## Upcoming
- **P3: The Market** — Peer-to-peer marketplace (ISO Matches, Browse All, Buy/Offer/Trade)
- **P3: Design Overhaul** — New color palette, fonts (Playfair Display, Cormorant Garamond), color-coded badges
- **P4: Stripe Connect** — Escrow payments, identity verification, tracking, disputes
- **P5: Notifications** — ISO matches, likes, offers, payouts
- **P5: Monetization** — Pro membership flag, 4% transaction fee, verified seller badge

## Data Model
```
posts: id, user_id, post_type, caption, image_url, share_card_square_url, share_card_story_url, record_id, haul_id, iso_id, weekly_wrap_id, track, mood, created_at
records: id, user_id, discogs_id, artist, title, cover_url, year, format, notes, source, created_at
spins: id, user_id, record_id, notes, created_at
hauls: id, user_id, store_name, title, description, image_url, items[], created_at
iso_items: id, user_id, artist, album, tags[], pressing_notes, condition_pref, target_price_min, target_price_max, status, created_at, found_at
likes: id, user_id, post_id, created_at
comments: id, user_id, post_id, content, created_at
followers: follower_id, following_id, created_at
```

## Test Credentials
- Email: demo@example.com / Password: password123
- Demo user: 148 records, 7 spins, 5+ ISOs, following 3 users
