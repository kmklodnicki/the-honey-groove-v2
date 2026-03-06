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
41. **Wax Report Story Card** — Export card updated from 1080x1080 to 1080x1920 vertical format (Instagram Stories). Now fully redesigned in v2 (see item 54). (Mar 2026)
42. **The Mood Board** — Auto-generated 3x3 album art grid from most-spun records. Manual generation with time range pills (This Week, This Month, All Time). Profile page tab. 1080x1080 PNG export via Pillow. Weekly scheduler. Discogs cover caching. Backend: /api/mood-boards/* endpoints. (Mar 2026)
43. **Collector Bingo** — Weekly 5x5 bingo card with collector-themed challenges. Interactive marking, bingo detection (rows/cols/diagonals), celebration animation, free center space. 1080x1920 PNG export (Instagram Story). Friday-to-Sunday weekly cycle. 25 seed squares. Admin square pool manager. Community stats (% of the hive) after lock. Compact preview widget + full-screen modal. Locked state: greyed card + countdown to next Friday. Active state: countdown strip with urgency styling (24h/1h thresholds). Auto-lock animation. Backend: /api/bingo/* endpoints. Explore page section. (Mar 2026)
44. **A Note Post Type** — Free-form 280-char text post on The Hive. Minimal composer with optional record tag and single image upload. No category badge on feed. Fourth chip on composer bar (outlined pill, feather icon). Backend: POST /api/composer/note. Likeable, commentable, shareable. (Mar 2026)
45. **Global Search** — Nav search dialog with 3 tabs (Records via Discogs, Collectors via user search, Posts via caption search). Live search after 2 chars, recent searches (localStorage, max 8). Desktop: Explore button opens dialog. (Mar 2026)
46. **Onboarding Flow** — 3-step modal for new users: Step 1 (add 3 records from Discogs), Step 2 (follow 1 collector from suggestions), Step 3 (optional first Now Spinning post). Welcome banner on first Hive visit. (Mar 2026)
47. **Profile Fields** — Bio (160 chars), Setup (100 chars, turntable/gear), Location (city/country), Favorite Genre (20 genres dropdown). Editable from Settings, displayed on public profile. (Mar 2026)
48. **Founding Member Badge** — Auto-assigned to first 500 users. Honeycomb icon next to username in Hive posts. Founding member italic badge on profile. Permanent. (Mar 2026)
49. **Report & Block System** — POST /api/reports with type (post/listing/user), reason, notes. Admin queue at GET /api/reports/admin with status toggle. (Mar 2026)
50. **Empty States** — Thoughtful empty states for Hive, Collection, Wantlist, Honeypot, Notifications, DMs, Search with CTAs. (Mar 2026)
51. **Dynamic Platform Fee** — Platform fee is now configurable (default 6%) via admin API. Stored in platform_settings collection. Admin endpoints: GET/POST /api/admin/settings. (Mar 2026)
52. **Navigation Fix** — Separated Explore (globe icon) and Global Search (magnifying glass) in navbar. (Mar 2026)
53. **Search UI Polish** — Removed X close button from search popup, replaced with Cancel text button only. (Mar 2026)
54. **Wax Report Card v2 Redesign** — Complete redesign of the 1080x1920 export card. Removed collection value section entirely. Added Top Record section with Discogs album art hero. Personality labels now data-driven (uses top artist, era, mood, spin count — no generic phrases). No quotation marks. Artist bars redesigned: dark text on low-opacity amber bars with proportional width, spin counts right-aligned italic. Visual hierarchy: rank 1 at 72px scaling down to 38px. Stats tiles: spins, unique records, unique artists (no empty mood dashes). Era pills enlarged. Closing line is poetic and data-driven, auto-sizes to fit within canvas. Footer: left/center/right layout. Thin amber gradient dividers between all sections. (Mar 2026)
55. **Auth Lockdown** — All routes require authentication except: / (landing), /beta, /about, /faq, /login, /join. Logged-out users redirected to landing page (not /login). Admin routes (/admin/*) require is_admin role; non-admin users redirected to /hive. Session expiry also redirects to landing. No app content visible to logged-out users. (Mar 2026)
56. **Closed Beta / Invite Code System** — Public signup disabled entirely. Landing page "join the hive" opens a waitlist modal linking to /beta. All "sign up" / "create account" links removed site-wide. Invite-only registration at /join?code=XXXXXX. Admin generates single-use invite codes (individual or batch 10/25/50). Each code: unused → used → expired. Accounts created via invite code auto-receive founding member badge. Backend: /api/auth/register-invite, /api/admin/invite-codes/*. (Mar 2026)
57. **Beta Signup Page** — Public standalone page at /beta. Mobile-optimized, no nav/footer. Cream background, HoneyGroove logo, "you found it." headline. Form: first name, email, Instagram handle (@prefix), feature interest dropdown (7 options). Saves to beta_signups collection. Confirmation message replaces form on submit ("you're on the list."). Email notification to hello@thehoneygroove.com via Resend (RESEND_API_KEY required). SEO meta tags + og:image. (Mar 2026)
58. **Admin Beta & Invites Panel** — Admin page at /admin/beta with two tabs: Beta Signups (table with name, IG, email, feature, date, editable notes, CSV export) and Invite Codes (generate 1/10/25/50, status badges, copy invite link, used-by info). Accessible from Navbar dropdown for admin users. (Mar 2026)
59. **Unified Admin Panel** — Consolidated admin panel at /admin with 5 tabbed sections: Beta & Invites, Daily Prompts (list/create/edit/toggle active), Bingo Squares (list/create/edit/toggle), Reports Review Queue (filter by status, change status), Platform Settings (fee %). Tab nav with ?section= URL param. Admin-only access. Old separate admin pages redirected. (Mar 2026)
60. **Record Detail Page** — Fully populated page at /record/:recordId. Hero with album art, title, artist, year, format, Discogs external link. Log a Spin button (owner-only). Stats grid: Your Spins, Community Spins, Collectors, Wanted. Market value card (low/median/high from Discogs cache). Community owners list with avatars. Hive Activity feed showing related posts with type badges. Backend: GET /records/{record_id}/detail aggregates record, owner, community stats, market value, and related posts. (Mar 2026)
61. **Daily Prompt Streak Tracking** — Streak counter on profile page with fire icon in stats row. Backend: GET /prompts/streak/{username} returns streak and longest_streak. Nudge notification scheduler runs hourly at 19:00 UTC (streak >= 3, first nudge) and 22:00 UTC (streak >= 7, urgent nudge). Wax Report closing line appends "and a perfect prompt streak to prove it" for perfect weekly streaks (7/7). (Mar 2026)
62. **Sweetener Payments UI** — Enhanced sweetener display on trade cards (prominent badge with amount, payer label, 4% fee indicator). Trade detail modal shows full breakdown (amount, payer, fee, recipient amount, explanation tooltip). Propose modal includes fee preview and tooltip explanation. Accept flow triggers confirmation dialog with fee disclosure. Stripe charge via POST /trades/{id}/pay-sweetener with 4% platform fee on sweetener amount only. (Mar 2026)
63. **Dynamic Sweetener Fee Fix** — Sweetener fee corrected from hardcoded 4% to dynamic platform fee (6%) from settings. New public endpoint GET /api/platform-fee. ISOPage.js fee text now fetches dynamically. STRIPE_WEBHOOK_SECRET configured. (Mar 2026)
64. **Discogs Collection Import (Enhanced)** — Full-featured import with two entry points: Collection page header (DiscogsImport card) and Onboarding Step 1. Username-based connection with validation (rejects invalid users, private collections). Background import with real-time progress polling. Duplicate handling by discogs_id. Summary modal on completion showing: stats grid (imported/skipped/total), sample album covers, collection value. Post-import background task fetches Discogs market values for all new records. New endpoints: GET /api/discogs/import/summary, enhanced /api/discogs/connect-token with collection accessibility check. (Mar 2026)
65. **Google Analytics & Custom Events** — GA4 (G-KEL18TSP0N) loaded via JS from REACT_APP_GA_MEASUREMENT_ID env var. 13 custom events tracked: beta_signup, invite_used, now_spinning_posted, haul_posted, iso_posted, trade_proposed, trade_completed, purchase_completed, wantlist_added, collection_record_added, daily_prompt_answered, export_card_generated, discogs_import_completed. Utility: utils/analytics.js with trackEvent(). (Mar 2026)
66. **Listing Detail Modal** — Clicking a listing card in The Honeypot opens a full detail modal (not a page nav). Shows: album art, artist (Playfair Display Bold #2A1A06 32px), album (Cormorant Garamond Italic #C8861A 26px), condition pill, seller info (avatar, rating stars, completed sales), seller photos (horizontal scroll, tappable fullscreen), price (Playfair Display Bold #996012 52px), description (Cormorant Garamond, Read more toggle), shipping info, CTA buttons (Buy Now / Make Offer + Buy at asking / Trade + Trade instead), wantlist toggle, similar listings by artist. URL deep links to /honeypot/listing/:id. Back button dismisses modal. Backend enriched with seller.rating, seller.completed_sales, similar_listings, on_wantlist. (Mar 2026)
67. **N+1 Query Optimization** — Collection records and Explore trending now use MongoDB aggregation pipelines ($lookup) instead of N+1 individual queries. (Mar 2026)
68. **Email & Env Updates** — Beta signup notifications now sent from hello@thehoneygroove.com to contact@kathrynklodnicki.com. Resend API key configured. Emergent badge hidden. (Mar 2026)

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
    ├── wax_reports.py # Weekly reports & image generation
    ├── reports.py     # User-driven content reporting
    └── admin.py       # Platform settings, invite codes, beta signups

/app/frontend/src/
├── pages/
│   ├── BetaSignupPage.js    # Public beta waitlist signup
│   ├── JoinPage.js          # Invite-only registration
│   ├── AdminBetaPage.js     # Admin panel for beta/invites
│   ├── TradesPage.js        # ProposeTradeModal (condition+photos), TradeDetailModal (condition+photos display)
│   ├── ISOPage.js           # The Honeypot (3 tabs), listing modal with condition+photos
│   ├── WaxReportPage.js     # Full weekly report view
│   └── ...other pages
├── components/
│   ├── auth/
│   │   └── ProtectedRoute.js # ProtectedRoute + AdminRoute wrappers
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

69. **Landing Page Hero Polish** — Reduced hero top padding from 144px to 32px mobile / 48px desktop. Added subtle 3s ease-in-out honey drip animation (5px vertical float) on logo-drip.png. (Mar 2026)

## Upcoming Tasks
- **P0: Complete Email System** — Wire remaining 2 email triggers (newsletter_signup, weekly_wax_ready), verify all 13 existing triggers
- **P1: Stripe Webhook Verification** — Test /api/webhook/stripe with real Stripe event
- **P2: Hauls Enhancement** — Dedicated hauls page with richer functionality
- **P2: Refactor ISOPage.js** — Break monolithic 3-tab component
- **P2: Monetization** — Pro membership, Verified Seller badge

## Data Model
```
users (bio, setup, location, favorite_genre, founding_member, onboarding_completed),
posts, records, spins, hauls, iso_items,
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
mood_boards,
reports (type, target_id, reason, status)
```

## Test Credentials
- Admin: demo@example.com / password123 (is_admin: true)
