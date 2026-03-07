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

## Upcoming Tasks
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

70. **Listing & Sale Confirmed Emails** — 3 new transactional emails via Resend: (1) Listing Confirmed sent to seller on listing creation with album/artist/condition/price/type, (2) Sale Confirmed Seller with dynamic fee calculation and payout amount, (3) Sale Confirmed Buyer with seller info and amount. Triggered on both Stripe webhook and polling fallback. (Mar 2026)

71. **Mutual Hold Trade — Phase 1 Backend** — 9 new endpoints: hold-suggestion (100% avg Discogs value, $50 fallback, $10 min), hold/respond (accept/counter/decline), hold/checkout (Stripe), hold/status, enhanced confirm-receipt (auto-refund), enhanced dispute (freeze holds), admin hold-disputes (list + resolve with 4 options). 4 hold email templates. Auto-reversal scheduler (10 min interval). 19/19 tests passed. (Mar 2026)

72. **Mandatory Mutual Hold** — All trades now require hold (no straight trades). Removed toggle/decline option. Accept always → HOLD_PENDING. Trade accepted email updated with hold explanation. FAQ updated: new "What is a Mutual Hold Trade?" entry, fee policy clarifies 6% on sweeteners only, hold not subject to fee. (Mar 2026)

73. **Mutual Hold Phase 3 Frontend** — TradesPage routing fixed (/trades renders instead of redirect). Trade cards: shield icon + tooltip, hold amount badge, "Pay hold" indicator. Trade detail modal: MUTUAL HOLD status section, per-party payment tracking, "Pay $X Hold" Stripe button. Propose modal: always-visible hold amount field with $10 min. Confirmation UI: "Yes, everything looks good" / "There's an issue". FAQ updated. 17/17 tests passed. (Mar 2026)

74. **Week in Wax Card Redesign** — Complete rewrite of share card to match Canva template. New layout: header, honey drip overlay, top album card, 3-column top artists bar, personality label, amber stat boxes, olive decade pills, amber closing line, footer. Generated honey drip asset. Verified via screenshot. (Mar 2026)

75. **Admin Hold Disputes Panel (Phase 4)** — New "Hold Disputes" tab in admin panel. Dispute cards show: HOLD FROZEN header with amount, both parties, traded records, dispute reason + evidence photos, resolution notes. 4 action buttons: Full Reversal, Penalize Proposer, Penalize Recipient, Partial Split. Verified with real dispute data. (Mar 2026)

76. **Admin Hold Disputes Redesign** — Full brand-aligned restyle: amber palette, cream backgrounds, Cormorant Garamond italic, amber-bordered HOLD FROZEN pill, 4 resolution buttons renamed (Refund Both, Proposer/Recipient Forfeits Hold, Custom Split) with specific confirmation dialogs. Admin tabs restyled to white pills with amber active state. (Mar 2026)

77. **Buyer Protection — Seller Transaction Count** — Completed transactions (trades + sales) displayed on: user profiles (stats row with ShoppingBag icon), listing cards ("X sales · Y ★" next to seller username), and listing detail modals. Backend: _build_user_response computes count from trades + listings collections. GET /api/seller/stats endpoint for current user. (Mar 2026)

78. **Buyer Protection — New Seller Listing Restrictions** — Sellers with < 3 completed transactions cannot list items priced above $150. Backend enforced on POST /api/listings. Frontend shows inline amber warning below price field in listing creation modal. Restriction lifts automatically at 3 completed transactions. (Mar 2026)

79. **Buyer Protection — Off-Platform Payment Detection** — Listing descriptions scanned for 7 keywords (Venmo, PayPal, CashApp, Zelle, wire transfer, Western Union, bank transfer). Case-insensitive. Flagged listings: offplatform_flagged=true stored on listing, yellow warning banner shown to buyers on listing detail. Admin: new "Off-Platform Alerts" tab showing username, flagged keywords, description snippet, dismiss action. Backend: offplatform_alerts collection, GET/PUT admin endpoints. (Mar 2026)

80. **Buyer Protection — Shipping Insurance Prompt** — Listings priced > $75 show insurance prompt before final submit: "Got it, I'll add insurance" / "Skip for now". Response stored as insured boolean on listing. Listing detail shows green "Seller added shipping insurance" or amber "No shipping insurance" indicator. (Mar 2026)

81. **Help & Support Integration** — Three access points: (1) Settings page "Help & Support" section with FAQ (external link), Contact Us (mailto), Report a Problem links. (2) Navbar dropdown "Help" link between Settings and Log out. (3) "How does this work?" explainer modal on Mutual Hold amount field in trade proposal modal with 4-step walkthrough. (Mar 2026)

82. **Terms of Service Page** — Public page at /terms with 10 sections covering acceptance, service description, user responsibilities, marketplace rules, fees, mutual hold, prohibited conduct, dispute resolution, liability, termination, and contact. Cream background, amber headings, footer links to Privacy and FAQ. (Mar 2026)

83. **Privacy Policy Page** — Public page at /privacy with 8 sections covering data collection, usage, sharing, storage, user rights, cookies, "never sell data" statement, and contact. Lists third-party services (Stripe, Discogs, Resend, Google Analytics). (Mar 2026)

84. **Rate Limiting** — In-memory sliding window rate limiter on login (5/15min), beta signup (3/hr), and invite registration (5/15min). Returns 429 with friendly error message. (Mar 2026)

85. **Invisible Honeypot on Beta Signup** — Hidden 'website' field invisible to humans, visible to bots. Filled submissions silently rejected (success returned, not saved). Blocked submissions logged to honeypot_blocks collection. (Mar 2026)

86. **Email Verification on Account Creation** — New users created via invite get email_verified=false. Verification email sent with 24hr expiry token. GET /api/auth/verify-email validates token. POST /api/auth/resend-verification resends. Login page shows verification banner with resend link for unverified users. Dedicated /verify-email page with loading/success/error states. (Mar 2026)

87. **Secured by Stripe Badge** — Small muted "Secured by Stripe" text badge with Stripe wordmark SVG shown below purchase buttons in ListingDetailModal and below Pay Hold button in TradesPage. (Mar 2026)

88. **P0 Auth Fix — Unverified User Blank Page** — Fixed register() in AuthContext.js to not set user state for unverified emails (same pattern as login). Prevents blank page on mobile for new users who haven't verified email. fetchUser() also clears state for unverified users on page refresh. (Mar 2026)

89. **Mobile Bottom Navigation** — Instagram/TikTok-style mobile nav. Desktop nav hidden on mobile (<768px). Replaced with: (1) 48px slim top bar with centered HoneyGroove wordmark, DM/notification/avatar icons on right. (2) 64px fixed bottom nav with 5 icon-only tabs: The Hive, Explore, Search, Collection, The Honeypot. Active icon: amber #C8861A, inactive: muted #8A6B4A at 50%. Safe area padding via env(safe-area-inset-bottom). Page padding updated to pt-16 md:pt-24. (Mar 2026)

90. **Brand Polish Phase 1 — Quick UI Fixes** — Login logo 200px, mobile wordmark 130px/56px bar, notification badge amber (not red), bottom nav inactive opacity 0.65, ISO card cream bg + amber border + outlined OPEN pill, Daily Prompt bee emoji replacing fire, Mutual Hold amber (not green) + copy fix, honey jar favicon at 16/32/180/192 sizes with PWA manifest. (Mar 2026)

91. **Brand Polish Phase 2 — Honey Jar Loading Screen** — SVG honey jar with CSS fill animation (1.5s ease), rotating loading phrases ('filling the hive...', 'warming up the wax...', etc.), replaces both index.html initial loader and React LoadingScreen component. (Mar 2026)

92. **Brand Polish Phase 3 — Custom Toasts** — Sonner unstyled mode with custom CSS: cream #FAF6EE bg, amber border, 16px radius, emoji icons (🍯 success, 🐝 error, 🎵 info), max-width 320px floating pill. All 85+ toast messages updated to lowercase conversational style. (Mar 2026)

93. **Brand Polish Phase 4 — Email Templates** — Sender name 'The Honey Groove', base template redesigned with logo image, honey drip, solid 2px amber divider, warm #FAF6EE bg, bee footer with amber link. Verification email migrated to use base template. (Mar 2026)

94. **Global Album Art Fallback** — Reusable AlbumArt component with shimmer loading skeleton and vinyl record SVG placeholder on error. Applied to 75+ img tags across all pages/components. Vinyl placeholder: cream bg with muted amber concentric circles. (Mar 2026)

95. **ISO Card & Toast Fixes** — Toast constrained to 320px max-width floating pill. ISO card: rounded-xl (12px), outlined amber OPEN badge (transparent bg, amber border/text). Beta page dropdown bg fixed to cream. (Mar 2026)

96. **Toast Position Fix** — Toast offset set to 96px so it appears below the desktop nav bar, not overlapping it. (Mar 2026)

97. **Notification Badge Global Fix** — Confirmed all notification badges use amber #C8861A. No remaining red badges outside of destructive/error actions. (Mar 2026)

98. **Buzz Emoji Fix** — All Flame icon imports removed. Every streak display and buzz-in count now uses literal 🐝 emoji. FAQ page text updated to reference bee icon. (Mar 2026)

99. **Placeholder Post Cleanup** — Deleted 148 placeholder posts with no type or record data from the posts collection. (Mar 2026)

100. **Content: 50 Daily Prompts** — Added 50 curated daily prompts to the daily_prompts collection. Total: 50 prompts. (Mar 2026)

101. **Content: 50 Bingo Squares** — Added 48 new bingo squares (2 were duplicates). Total: 76 active squares. (Mar 2026)

102. **Safari Blank Screen Fix** — Removed Safari-incompatible SVG CSS animation (jarFill). Simplified loading screen to static logo. Added -webkit-backdrop-filter prefix. 3-second hard timeout. (Mar 2026)

103. **Safari Blank Screen Fix v2 (Aggressive)** — Removed LoadingScreen component entirely from App.js. ProtectedRoute/AdminRoute/LandingWrapper return null during auth loading instead of blocking cream screen. AuthContext has 3s safety timeout to force loading=false. fetchUser timeout reduced to 5s. index.html loading screen force-removed at 2s. Safari fallback "tap to reload" button appears at 4s if React fails to mount. console.log('app mounted') diagnostic added. Full CSS Safari audit: no SVG animations, -webkit-backdrop-filter present, autoprefixer handles Tailwind utilities. (Mar 2026)

103. **Mobile Wordmark Fix** — Mobile top bar wordmark updated from w-[110px] to h-[36px] w-auto max-w-[130px] object-contain to prevent clipping. (Mar 2026)

104. **ISO Page Brand Color Audit** — Changed all off-brand colors: SEARCHING badge purple→amber, 'I have this' button green→amber, BUY_NOW badge green→amber, Make Offer button blue→amber, Mark Found button green→amber. All using #C8861A/#E8A820 palette. (Mar 2026)

105. **Added 50 Daily Prompts + 50 Bingo Squares** — Added to DB (total: 80 prompts, 124 bingo squares). Cleaned TEST entries from prompts, bingo squares, and records. Fixed 49 bingo squares missing emoji field. (Mar 2026)

106. **Redesigned Collector Bingo Teaser** — Replaced full 5x5 grid preview on Explore page with compact teaser card (~160px): countdown line + italic Cormorant Garamond teaser text + full-width amber "play now" CTA. Clicking opens full bingo modal with interactive 5x5 grid unchanged. Both active and locked states redesigned. (Mar 2026)

107. **Safari Route Navigation Fix** — ProtectedRoute/AdminRoute render visible bg-honey-cream div during loading instead of null. AuthContext uses loadingResolved ref to prevent loading from ever resetting to true. Safety timeout 3s. (Mar 2026)

108. **Mobile Wordmark Fix** — Top bar height increased to 52px, wordmark min-width 140px for legibility. (Mar 2026)

110. **Zero Loading Gate Architecture** — AuthContext.loading is now ALWAYS false. JWT decoded client-side for instant user hydration (decodeTokenPayload + initUserFromToken). fetchUser runs in background after page renders. ProtectedRoute has no loading check — only checks user existence. Fallback timeout increased to 15s. CORS expose_headers added. Login→Hive renders in <0.5s. (Mar 2026)

111. **Hide Demo Account from Public Views** — Added get_hidden_user_ids() helper in database.py. All public-facing endpoints now filter out posts/listings/ISOs from users with is_hidden=True: /explore feed, /feed, /search/posts, /listings, /iso/community, /buzzing. Demo account flagged with is_hidden=True in DB. (Mar 2026)

112. **"Unspun" → "no logged spins" Label Change** — Collection album tiles now show "no logged spins" (muted text) instead of "Unspun" when spin_count is 0. RecordDetailPage StatCard shows "no logged spins" for Your Spins when value is 0. Collection sort dropdown option renamed from "Never Spun" to "No Logged Spins". (Mar 2026)

113. **Fresh Pressings 24h Cache** — /api/explore/fresh-pressings uses MongoDB `cache` collection with 24-hour TTL. Fetches from Discogs API once per day, serves cached data otherwise. (Mar 2026)

114. **Compact Honeypot Listings** — Redesigned Shop and Trade tab listing cards from large cards with aspect-square images to compact ~80px rows. Each row: 64px album art thumbnail, album name (Playfair 14px bold), artist (muted 12px), condition pill + type badge inline, seller username + rating, price in amber on the right. Thin amber divider between rows. Both Shop and Trade tabs use divide-y layout. (Mar 2026)

115. **Delete Account** — Settings page: muted "Delete Account" button with trash icon at bottom. Confirmation modal: "Are you sure?" (Playfair), descriptive body (Cormorant Garamond), "Yes, delete my account" (outlined) + "Cancel" (amber). Backend DELETE /api/auth/account deletes all user data across 25+ collections, cancels Stripe holds, logs deletion to account_deletions collection, logs out and redirects to landing. (Mar 2026)

116. **Pop & Alternative Genres** — Added "Pop" (after R&B) and "Alternative" (after Indie) to the genre dropdown in profile settings. (Mar 2026)

117. **Admin User Management** — New "User Management" tab in admin panel. Table with username, email, joined date, role pill (Admin/User), and action button. Grant/revoke admin access with confirmation modals. Search by username/email. Filter: All Users, Admins, Standard. Cannot revoke own admin access. (Mar 2026)

118. **Trending in Collections (replaced Fresh Pressings)** — Replaced Fresh Pressings on Explore page with "Trending in Collections" section. Fetches most-collected vinyl records from Discogs API (sort=have, desc). Shows album art, title, artist, and "owned by X collectors" stat. 24h MongoDB cache. See All page at /explore/trending-in-collections. (Mar 2026)

119. **Share/Export Buttons Hidden** — All Instagram shareable export options temporarily removed from user-facing views: Hive post share button & dialog, Wax Report share button & modal, Collector Bingo "save & share card" button, Daily Prompt "share to instagram" + post-submit "save & share card", Mood Board export button, Collection Page "shareable card" label. Code preserved via comments for quick re-enable. (Mar 2026)

120. **Discogs Search Debounce (All Components)** — Added 350ms debounce to ComposerBar.js (haul search, ISO search) and OnboardingModal.js (record search) using useRef-based timers with cleanup. ISOPage.js already had debounce. Prevents excessive API calls on mobile. (Mar 2026)

121. **Weekly Wax Email — 12PM ET Schedule** — Changed wax report scheduler from Sunday midnight UTC to Sunday 12:00 PM ET using zoneinfo.ZoneInfo("America/New_York"). Handles DST transitions automatically. Starting March 8, 2026. (Mar 2026)

122. **Hold Auto-Reversal Fix** — Fixed import scope for auto_reverse_expired_holds in server.py. Import was inside startup function but referenced in _schedule_hold_auto_reversal — moved import into the scheduler function. (Mar 2026)

123. **Data Cleanup** — Deleted 3 orphan posts with no type. Purged all test accounts created during testing. Only real user (katieintheafterglow) and hidden admin remain. (Mar 2026)

124. **Global Search Overhaul** — Complete rewrite of search functionality. New unified backend endpoint GET /api/search/unified searches records (from collections), collectors, posts, AND Honeypot listings simultaneously using per-word regex matching. Relevancy scoring: exact match (100) > starts-with (60) > word boundary (40) > contains (20). Separate non-blocking GET /api/search/discogs for external Discogs catalog results. Frontend shows all content types in single scrollable view with section headers (Records, Collectors, Honeypot Listings, Posts) with counts. Fuzzy matching: "tay swift" finds Taylor Swift. Speed: avg 115ms (target was 300ms). Database indexes on records.artist, records.title, listings.artist+album, posts.caption+content. Empty state: "no results for [query]" with bee emoji. Batch queries for user data (no N+1). (Mar 2026)

125. **Search Input Lag Fix** — Added AbortController to GlobalSearch.js and AddRecordPage.js to cancel in-flight requests when user types again. Separated input state (instant) from search trigger (300ms debounce). Added amber loading spinner inside search bar. No keyboard blocking on mobile. (Mar 2026)

126. **Vinyl Variant Details in Search Cards** — Created reusable RecordSearchResult.js component showing two-line compact format: Line 1 = Year · Label · Catalog#, Line 2 = Format · Country. Color variants displayed in amber pill badges (e.g., "Blue Translucent", "Target Exclusive #3"). Enhanced backend search_discogs() to extract color/variant from Discogs formats.text field. Updated DiscogsSearchResult Pydantic model (format: str, added label/catno/country/color_variant/genre). Applied to all 6 search UIs: GlobalSearch, AddRecord, ISOPage DiscogsPicker, ComposerBar haul+ISO, OnboardingModal. (Mar 2026)

127. **Now Spinning Composer Search** — Replaced album Select dropdown in Now Spinning modal with a local collection search input. Features: "search your collection..." placeholder, 300ms debounce via setTimeout, fuzzy matching (words.every match), relevancy scoring, RecordSearchResult with variant details, selected record shows as compact card with album art + X to deselect, empty state "no results in your collection 🐝" with "add it first →" link to /add-record. No API calls (filters records prop locally). (Mar 2026)

## Upcoming Tasks
- **P2: Hauls Enhancement** — Dedicated hauls page with richer functionality
- **P2: Refactor ISOPage.js** — Break monolithic 3-tab component
- **P2: Monetization** — Pro membership, Verified Seller badge

## Data Model
```
users (bio, setup, location, favorite_genre, founding_member, onboarding_completed, completed_transactions),
posts, records, spins, hauls, iso_items,
listings (photo_urls[], condition, insured, offplatform_flagged),
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
reports (type, target_id, reason, status),
offplatform_alerts (listing_id, user_id, username, keywords, status),
email_verifications (user_id, token, created_at),
honeypot_blocks (ip, email, created_at)
```

## Test Credentials
- Admin: admin@thehoneygroove.com (is_admin: true, is_hidden: true)
- Real user: katieintheafterglow (kmklodnicki@gmail.com)
- demo@example.com has been DELETED
- To test: Generate invite code via admin, register via /join?code=XXXXXX
