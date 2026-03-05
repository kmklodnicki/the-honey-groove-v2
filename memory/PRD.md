# HoneyGroove PRD

## Problem Statement
A social platform for vinyl collectors called **The HoneyGroove** — the vinyl social club. Users track their collection, log spins, share activity, import from Discogs, hunt for records (ISO), follow friends, trade vinyl, and interact through a rich social feed.

## Branding
- Colors: Honey #F4B942, Honey Soft #F9D776, Cream #FFF6E6, Amber #D98C2F, Vinyl Black #1F1F1F
- Fonts: DM Serif Display (headings), Inter (body)

## Core Pages
1. **Landing Page** — Hero ("the vinyl social club, finally."), Features ("built for the obsessed."), CTA, Footer with About + FAQ links
2. **The Hive** — Social feed with composer bar (Now Spinning, New Haul, ISO)
3. **Explore** — Advanced discovery page with 5 sections: Trending in the Hive, Taste Match, Fresh Pressings, Most Wanted, Near You
4. **Collection** — Personal vinyl library with sorting + Discogs import + Add Record
5. **The Honeypot** — 3-tab marketplace: Shop (Buy/Offer), ISO (Hunt List + Community Hunt), Trade (Active Trades + Browse Trades)
6. **Profile** — 5 tabs: Collection, ISO, Spinning, Trades, Mood Board + Stripe Connect status
7. **Admin Disputes** — Admin-only dispute review dashboard with resolve modal
8. **Messages** — Full 1:1 DM system with inbox, threads, context cards
9. **FAQ** — Accordion-style FAQ page with all feature explanations
10. **About** — Katie's founder story, social links (Instagram, TikTok, Email)

## Navigation
The Hive — Explore — Collection — The Honeypot

## Implemented Features
1-14: Auth, Collection, Discogs Import, Feed, Composer, Post Cards, Comments/Likes, Shareable Graphics, Sorting, Profile Photos, ISO Page, Profile Tabs, Following System, Explore
15. **Vinyl Mood Overhaul** — 12 moods with emojis, dynamic backgrounds, animated selection
16. **Marketplace Photo Upload** — 1-10 required photos with gallery carousel
17. **Trade System (Complete)** — Propose/Counter/Accept/Decline, shipping, confirmation, disputes, ratings
18. **Stripe Connect Onboarding** — Seller onboarding via Stripe Connect Express
19. **In-App Notifications** — Notification bell with dropdown, unread count, mark-all-read
20. **Landing Page Redesign** — Updated hero, features (6 cards), CTA, footer
21. **Stripe Payment Execution** — Buy Now & Make Offer checkout with 4% application fee via Stripe Connect
22. **Admin Dispute Dashboard** — Full UI with Open/Resolved tabs, dispute cards, resolve modal
23. **Browser Push Notifications** — Desktop notifications via Notification API for real-time alerts
24. **The Honeypot Rebrand** — Renamed Marketplace → The Honeypot, 3-tab layout (Shop/ISO/Trade)
25. **Direct Messages** — Full 1:1 DM system with context cards, inbox badge, entry points
26. **Backend Refactor** — Split 3700-line server.py into 8 route modules + database.py + models.py
27. **Explore Page v2** — 5 sections: Trending, Taste Match, Fresh Pressings, Most Wanted, Near You
28. **About Page** — Founder story by Katie, social links
29. **FAQ Page** — Comprehensive FAQ with accordion UI
30. **Explore "See All" Pages** — Full-page views for each Explore section
31. **Discogs Market Valuation** — Collection Value banner, Hidden Gems, value badges, pricing assist, wantlist price alerts, background refresh
32. **Your Week in Wax** — Weekly vinyl report with personality label, stats, shareable PNG, scheduled Sunday background job
33. **Now Spinning + Mood Merge** — Combined Now Spinning and Vinyl Mood into single modal
34. **Trade Condition & Photo Requirements** — Trade proposals and trade-only listings now require condition selection (7 grades) and photo uploads (1-5). TradeDetailModal displays condition badges and photo galleries for both records in the exchange. (Feb 2026)
35. **ComposerBar Discogs ISO Search** — The ISO posting modal in ComposerBar now has Discogs search integration. Users can search Discogs for albums, select a result (with cover art), or enter manually. Discogs data (discogs_id, cover_url, year) is sent with ISO posts. (Feb 2026)
36. **Official Logo & Branding Update** — Replaced all HoneyGroove wordmarks with official logo assets. Full drip logo on hero + loading screen, wordmark on navbar/login/signup/footer. Updated favicon and page title. Updated all 6 feature card descriptions with final copy. (Feb 2026)
37. **Daily Prompt** — Daily rotating prompt card at top of Hive feed, buzz-in flow with Discogs high-res art, export card generation (1080x1080 Pillow), streak tracking with profile badge, admin prompt manager. 30 prompts seeded. (Mar 2026)
38. **Newsletter System** — Landing page newsletter section ("stay in the loop"), 30s delayed popup for non-logged-in visitors, Settings page toggle ("The Weekly Wax"), newsletter_subscribers collection. No 3rd party email integration yet. (Mar 2026)
39. **Landing Page Enhancements** — CTA "join the hive" (lowercase), bee bridge emoji, tightened logo-headline spacing, larger footer wordmark (180-200px). (Mar 2026)
40. **Nav Sizing Update** — Wordmark increased to h-[52px], nav height to h-[66px] for visual presence. (Mar 2026)
41. **Wax Report Story Card** — Export card updated from 1080x1080 to 1080x1920 vertical format (Instagram Stories). Redistributed layout: header, personality label, top 5 artists, stats, eras, vinyl moods, collection value, closing line, footer. Playfair Display + Cormorant Garamond typography. Warm cream background with subtle amber radial glows. (Mar 2026)
42. **The Mood Board** — Auto-generated 3x3 album art grid from most-spun records. Manual generation with time range pills (This Week, This Month, All Time). Profile page tab. 1080x1080 PNG export via Pillow. Weekly scheduler. Discogs cover caching. Backend: /api/mood-boards/* endpoints. (Mar 2026)
43. **Collector Bingo** — Weekly 5x5 bingo card with collector-themed challenges. Interactive marking, bingo detection (rows/cols/diagonals), celebration animation, free center space. 1080x1080 PNG export. Friday-to-Sunday weekly cycle. 25 seed squares. Admin square pool manager. Backend: /api/bingo/* endpoints. Explore page section. (Mar 2026)

## Code Architecture
```
/app/backend/
├── server.py          # Slim FastAPI app, registers routers, startup/shutdown
├── database.py        # Shared: db client, config, auth, storage, notifications
├── models.py          # All Pydantic models
└── routes/
    ├── auth.py        # Auth, user profiles, search, discovery
    ├── hive.py        # Feed, composer, likes, comments, share graphics
    ├── collection.py  # Records, spins, hauls, Discogs, upload, weekly
    ├── honeypot.py    # ISO, listings, Stripe Connect & payments
    ├── trades.py      # Trade lifecycle, admin disputes
    ├── notifications.py # Notification CRUD
    ├── dms.py         # DM conversations & messages
    ├── explore.py     # Trending, fresh pressings, most wanted, near you, follow, stats
    ├── valuation.py   # Discogs market value endpoints
    └── wax_reports.py # Weekly reports & image generation

/app/frontend/src/
├── pages/
│   ├── TradesPage.js        # ProposeTradeModal (condition+photos), TradeDetailModal (condition+photos display)
│   ├── ISOPage.js           # The Honeypot (3 tabs), listing modal with condition+photos
│   ├── WaxReportPage.js     # Full weekly report view
│   └── ...other pages
├── components/
│   ├── ComposerBar.js       # ISO modal with Discogs search, Now Spinning with mood
│   └── ...other components
```

## Trade Flow
```
PROPOSED → (Counter) → COUNTERED → (Accept/Decline)
PROPOSED/COUNTERED → ACCEPTED → SHIPPING (5-day deadline)
SHIPPING → CONFIRMING (both ship, 48h deadline) → COMPLETED (both confirm, records transfer)
SHIPPING/CONFIRMING → DISPUTED → Admin resolves (COMPLETED/CANCELLED/PARTIAL)
COMPLETED → Mandatory rating before next trade
```

## Upcoming Tasks
- **P1: Admin Panel** — UI for managing Daily Prompts and Bingo Squares. Streak tracking logic and nudge notifications for Daily Prompt. Integrate Daily Prompt data into Week in Wax report.
- **P1: Sweetener UI** — Frontend for trade cash payments (backend endpoint exists at /api/trades/{id}/pay-sweetener)
- **P1: Push Notifications** — Service worker-based browser push
- **P2: Discogs Import** — Bulk collection import
- **P2: Refactor ISOPage.js** — Break monolithic 3-tab component into ShopTab/TradeTab/ISOTab
- **P2: Monetization** — Pro membership, Verified Seller badge
- **P2: Hauls Enhancement** — Dedicated hauls page

## Data Model
```
users, posts, records, spins, hauls, iso_items,
listings (photo_urls[], condition),
likes, comments, followers,
trades (offered_condition, offered_photo_urls[]),
trade_messages, trade_shippings, trade_disputes, trade_ratings,
notifications, payment_transactions,
dm_conversations, dm_messages,
collection_values, wax_reports,
prompts, prompt_responses, image_cache,
newsletter_subscribers,
bingo_squares, bingo_cards, bingo_marks,
mood_boards
```

## Test Credentials
- Admin: demo@example.com / password123 (is_admin: true)
