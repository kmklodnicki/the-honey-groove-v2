# HoneyGroove PRD

## Problem Statement
A social platform for vinyl collectors called **The HoneyGroove** — the vinyl social club. Users track their collection, log spins, share activity, import from Discogs, hunt for records (ISO), follow friends, trade vinyl, and interact through a rich social feed.

## Branding
- Colors: Honey #F4B942, Honey Soft #F9D776, Cream #FFF6E6, Amber #D98C2F, Vinyl Black #1F1F1F
- Fonts: DM Serif Display (headings), Inter (body)

## Core Pages
1. **Landing Page** — Hero ("the vinyl social club, finally."), Features ("built for the obsessed."), CTA, Footer with About + FAQ links
2. **The Hive** — Social feed with composer bar (Now Spinning, New Haul, ISO, Vinyl Mood)
3. **Explore** — Advanced discovery page with 5 sections: Trending in the Hive, Taste Match, Fresh Pressings, Most Wanted, Near You
4. **Collection** — Personal vinyl library with sorting + Discogs import + Add Record
5. **The Honeypot** — 3-tab marketplace: Shop (Buy/Offer), ISO (Hunt List + Community Hunt), Trade (Active Trades + Browse Trades)
6. **Profile** — 4 tabs: Collection, ISO, Spinning, Trades + Stripe Connect status
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
20. **Landing Page Redesign** — Updated hero, features (6 cards), CTA, footer (© 2026)
21. **Stripe Payment Execution** — Buy Now & Make Offer checkout with 4% application fee via Stripe Connect
22. **Admin Dispute Dashboard** — Full UI with Open/Resolved tabs, dispute cards, resolve modal
23. **Browser Push Notifications** — Desktop notifications via Notification API for real-time alerts
24. **The Honeypot Rebrand** — Renamed Marketplace → The Honeypot, 3-tab layout (Shop/ISO/Trade)
25. **Direct Messages** — Full 1:1 DM system with context cards, inbox badge, entry points
26. **Backend Refactor** — Split 3700-line server.py into 8 route modules + database.py + models.py
27. **Explore Page v2** — 5 sections: Trending (14-day spins with modal), Taste Match (collection overlap), Fresh Pressings (Discogs current year), Most Wanted (wantlist aggregation), Near You (city/region matching)
28. **About Page** — Founder story by Katie, social links (Instagram, TikTok, Email), linked from landing footer
29. **FAQ Page** — Comprehensive FAQ with accordion UI covering all features
30. **Explore "See All" Pages** — Full-page views for each Explore section (/explore/trending, /explore/taste-match, /explore/fresh-pressings, /explore/most-wanted, /explore/near-you) with grid/list layouts and higher data limits
31. **Discogs Market Valuation** — Collection Value banner, Hidden Gems (top 3 most valuable), value badges on record cards, "Highest Value" sort, pricing assist in listing modal ("recent sales: $X — $Y on Discogs"), wantlist price alerts, background 24h refresh with rate limiting. Cache in collection_values table.
32. **Taste Report PNG** — Shareable 1080×1920 Instagram Story image generated via Pillow. Includes: total collection value, most valuable record with cover art, hidden gems top 3, stats, HoneyGroove branding. Downloadable via modal on Collection page.

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
    └── explore.py     # Trending, fresh pressings, most wanted, near you, follow, stats

/app/frontend/src/pages/
├── ExploreSeeAllPage.js # See All pages for each Explore section
├── AboutPage.js       # Founder story + social links
├── ExplorePage.js     # 5-section discovery page
├── FAQPage.js         # Accordion FAQ
├── ISOPage.js         # The Honeypot (3 tabs)
├── MessagesPage.js    # DM inbox + threads
├── LandingPage.js     # Hero + features + CTA + footer
└── ...other pages
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
- **P1: Sweetener UI** — Frontend for trade cash payments (backend endpoint exists)
- **P1: Push Notifications** — Service worker-based browser push
- **P2: Discogs Import** — Bulk collection import
- **P2: Discogs Import** — Bulk collection import
- **P2: Refactor ISOPage.jsx** — Break monolithic 3-tab component into ShopTab/TradeTab/ISOTab
- **P2: Monetization** — Pro membership, Verified Seller badge
- **P2: Hauls Enhancement** — Dedicated hauls page

## Data Model
```
users, posts, records, spins, hauls, iso_items,
listings (photo_urls[]),
likes, comments, followers,
trades, trade_messages, trade_shippings, trade_disputes, trade_ratings,
notifications, payment_transactions,
dm_conversations (participant_ids[], context, last_message),
dm_messages (conversation_id, sender_id, text, read),
collection_values (release_id, median_value, low_value, high_value, last_updated)
```

## Test Credentials
- Admin: demo@example.com / password123 (is_admin: true)
