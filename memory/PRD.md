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
4. **ISO & Market** — Vinyl wish list (ISO), peer-to-peer marketplace listings with photos
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
15. **Vinyl Mood Overhaul** — 12 moods with emojis, dynamic modal background colors, animated selection (scale bounce), mood-specific button text/color/placeholder, mood-colored feed cards
16. **Marketplace Photo Upload** — Listings require 1-10 uploaded photos with gallery carousel in listing cards

## Upcoming
- **P0: Stripe Connect** — Escrow payments, seller identity verification, payout release for marketplace
- **P1: Trades Feature** — Full backend + UI for Trades tab (propose, accept/decline, history)
- **P1: Notifications** — ISO matches, likes, offers, payouts
- **P2: Explore Enhancements** — Trending records, active ISO listings alongside People tab
- **P2: Hauls Feature** — Dedicated hauls page beyond the composer post
- **P2: HoneyGroove Weekly** — Weekly summary aggregation + display
- **P2: Monetization** — Pro membership, 4% transaction fee, Verified Seller badge
- **P2: Design Overhaul** — New color palette, fonts (Playfair Display, Cormorant Garamond), color-coded badges

## Data Model
```
posts: id, user_id, post_type, caption, image_url, share_card_square_url, share_card_story_url, record_id, haul_id, iso_id, weekly_wrap_id, track, mood, created_at
records: id, user_id, discogs_id, artist, title, cover_url, year, format, notes, source, created_at
spins: id, user_id, record_id, notes, created_at
hauls: id, user_id, store_name, title, description, image_url, items[], created_at
iso_items: id, user_id, artist, album, tags[], pressing_notes, condition_pref, target_price_min, target_price_max, status, created_at, found_at
listings: id, user_id, artist, album, discogs_id, cover_url, year, condition, pressing_notes, listing_type, price, description, photo_urls[], status, created_at
likes: id, user_id, post_id, created_at
comments: id, user_id, post_id, content, created_at
followers: follower_id, following_id, created_at
```

## Test Credentials
- Email: demo@example.com / Password: password123
- Demo user: 148 records, 7 spins, 5+ ISOs, following 5 users

## Vinyl Mood Config (12 Moods)
| Mood | Emoji | Background | Button Color | Placeholder |
|------|-------|-----------|-------------|-------------|
| Late Night | 🕯️ | #1a1230 | #6a3a9a | what are you listening to at this hour? |
| Sunday Morning | ☀️ | #fff8e8 | #e8a820 | slow mornings, good records, nowhere to be... |
| Rainy Day | 🌧️ | #1a2a3a | #4a7aaa | set the scene... |
| Road Trip | 🚗 | #1a2a1a | #4a8a4a | where are you headed? |
| Golden Hour | 🌅 | #2a1a08 | #c8861a | the light is perfect right now... |
| Deep Focus | 🎧 | #0a1a0a | #2a6a2a | what are you working on? |
| Party Mode | 🥂 | #1a0a2a | #aa3a8a | who's coming over? |
| Lazy Afternoon | 🛋️ | #2a1a0a | #aa7a3a | not moving from this spot... |
| Melancholy | 💔 | #1a1a2a | #5a5a8a | some records just hit different... |
| Upbeat Vibes | ✨ | #1a2a1a | #3a9a5a | what's got you feeling good? |
| Cozy Evening | 🧸 | #2a1808 | #aa5a2a | candles lit, record spinning... |
| Workout | 🔥 | #2a0a0a | #cc3a2a | what's keeping you going? |
