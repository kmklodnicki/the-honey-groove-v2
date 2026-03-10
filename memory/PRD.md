# The HoneyGroove - Product Requirements Document

## Original Problem Statement
A full-stack web application called **The HoneyGroove**, a social platform for vinyl collectors to track their collection, log spins, and interact socially.

## Core Architecture
- **Frontend:** React (port 3000)
- **Backend:** FastAPI (port 8001)
- **Database:** MongoDB
- **Payments:** Stripe Connect (LIVE MODE)
- **External APIs:** Discogs API
- **Email:** Resend (MOCKED)
- **Analytics:** Google Tag Manager / Google Analytics
- **Storage:** Emergent Storage

## What's Been Implemented

### User System & Auth
- Invite-only, email-verified accounts
- Country selection, custom title labels, social links
- Email change with verification, Golden Hive verification (BLOCK 3.3)

### Social Feed ("The Hive")
- Post types: Now Spinning, New Haul, ISO, A Note, Daily Prompt
- Full comment system with likes, nested replies, @mentions
- **Heart button fix:** Optimistic UI, stopPropagation, type=button

### Marketplace ("The Honeypot")
- Stripe Connect LIVE, sale/trade listings, auto-post to Hive
- **Dual Grading System** (NM/VG+/VG/G+/F with Honey labels + tooltips)
- **Payout Estimator** (BLOCK 3.1) - live fee/shipping/Take Home Honey
- **Honey Pulse** (BLOCK 4.1) - 90-day Discogs price analysis, hot zone, median/range
- **Shipping Cost** field on listings
- **Auto-Payout Cron** (BLOCK 3.2) - 72h standard / 24h for 4.5+ sellers
- **HONEY Order ID Branding** (BLOCK 4.3) - Sequential `HONEY-XXXXXXXXX` IDs starting at 134208789, new orders only. Legacy UUID orders retain `#XXXXXXXX` display
- **Ghost Order Protection** (BLOCK 8.1) - Atomic inventory lock via `find_one_and_update` prevents double-sales. Listing locked as PENDING before Stripe session. Rollback to ACTIVE on failure. 409 → toast + redirect to /nectar

### Report a Problem System (BLOCK 3.4)
- Listing reporting (6 reasons + Other)
- Seller reporting (5 reasons)
- Order issue reporting (4 reasons)
- Bug reporting with auto-captured URL + browser info
- **Screenshot upload** for bug reports (optional, JPG/PNG/WebP, 10MB max, preview + remove)
- **Required description** field for bug reports ("What happened?")
- Rate limiting: 5 reports per user per 24 hours
- **Admin Watchtower** - filterable queue with actions:
  - Review, Dismiss, Resolve, Remove Listing, Warn Seller, Suspend Seller
- Report buttons on: listing detail, seller profile, orders, settings page
- **Global Navbar Report Button** - AlertTriangle icon in desktop navbar + mobile top bar, opens ReportModal with type "bug" (March 2026)

### UI Consistency (March 2026)
- **Shared pill style system**: `PILL_STYLES` config in PostCards.js drives both Hive filter pills and card badges with matching colors (amber/pink/orange/teal/yellow/purple/violet)
- **Variant pills**: `VariantTag` uses `VARIANT_PILL_STYLES` color map (red/blue/pink/green/gold etc.) for pressing color display
- **Shared tag components**: `PostTypeBadge`, `ListingTypeBadge`, `TagPill` exported from PostCards.js
- All tag pills use single color mapping: OG Press=amber, Factory Sealed=emerald, Promo=violet, Any=stone
- Listing type badges: teal for Trade, green for Sale — consistent across Explore, Honeypot, Search
- Post type badges: distinct colors per type — used across Hive, Record Detail, Global Search

### Verification Queue — The Gate (BLOCK 3.3)
- User ID upload, server-side blur, admin approve/deny
- Golden Hive badge on approval

### Search, Collection, SEO
- Psychic search, infinite scroll, Discogs fallback
- EXIF fix, pressing variants, country flags
- JSON-LD schema, **alt tags: "Artist - Title Vinyl Record"** format
- **Welcome to the Hive Dashboard** (BLOCK 5.1) - One-time post-Discogs-import page showing collection value with count-up animation, witty message, stats (records/artists/top artist), 3 CTAs. Route: `/onboarding/welcome-to-the-hive`

## Key Files
- `/app/backend/routes/reports.py` - Report system endpoints
- `/app/backend/routes/payout_cron.py` - Auto-payout cron
- `/app/backend/routes/verification.py` - The Gate endpoints
- `/app/frontend/src/components/ReportModal.js` - Shared report modal
- `/app/frontend/src/components/GradeLabel.js` - Grade with tooltip
- `/app/frontend/src/components/GoldenHiveBadge.js` - Verified badge
- `/app/frontend/src/utils/grading.js` - Grade mapping utility

## Mocked Integrations
- **Email (Resend):** Logic in place but not live

## Pending / Upcoming Tasks

### Completed Recently (March 2026)
- **Full SEO & Metadata System** - DONE (2026-03-10). Comprehensive metadata implementation across all page types:
  - **Backend SSR endpoints** (`/api/ssr/*`): Pre-rendered HTML with full OG tags, Twitter Cards, JSON-LD, and vinyl-specific metadata for social preview bots. Covers: listings, records, profiles, collections, ISO lists, marketplace, Hive posts, and landing page.
  - **Bot detection middleware** (CRACO `onBeforeSetupMiddleware`): Intercepts requests from known bots (Twitterbot, facebookexternalhit, Discordbot, Slackbot, Googlebot, etc.) and proxies to backend SSR endpoints. Normal users get the React SPA.
  - **Client-side SEOHead component** (`react-helmet-async`): Dynamic meta tags on all page components — RecordDetailPage, ProfilePage, HivePage, ISOPage, CollectionPage, LandingPage, ListingDetailModal, AboutPage, FAQPage, TermsPage, PrivacyPage.
  - **Vinyl metadata**: vinyl:artist, vinyl:album, vinyl:variant, vinyl:color, vinyl:release_year, vinyl:label, vinyl:catalog_number, vinyl:format, vinyl:speed, vinyl:disc_count, vinyl:pressing_country, vinyl:media_condition, vinyl:sleeve_condition, vinyl:graded.
  - **Product metadata**: product:price:amount, product:price:currency, product:availability, product:condition.
  - **Trade metadata**: trade:available, trade:iso, trade:trade_type, trade:negotiable.
  - **Collector metadata**: collector:username, collector:collection_size, collector:iso_count.
  - **Post metadata**: post:type, post:artist, post:album, post:variant.
  - **Schema.org JSON-LD**: Product (listings), MusicRecording (records), ProfilePage (profiles), SocialMediaPosting (posts), CollectionPage (collections/marketplace), ItemList (ISOs), WebApplication (landing).
  - **Canonical URLs** on all pages. **Image alt attributes** fixed across all components.
  - Files: `backend/routes/seo.py`, `frontend/src/components/SEOHead.js`, `frontend/craco.config.js`, plus all page components.
- **Discogs Import 1,000 Record Limit Fix** - DONE (2026-03-10). Removed `$limit: 1000` from `get_my_records` aggregation pipeline, changed `.to_list(1000)` to `.to_list(None)` in both `get_my_records` and `get_user_records` endpoints. Collections of any size now fully supported. File: `backend/routes/collection.py`.

### P1
- Weekly Wax Email - configure scheduled email every Sunday 12:00 PM ET

### P2
- Hauls Enhancement - dedicated page
- Refactor ISOPage.jsx - technical debt
- Grading Guide page (optional)

### Completed Recently
- **BLOCK 61: "Following" Feed Mode Toggle** - DONE (2026-03-10). Moved "Following" from content filter chips to a top-level segmented toggle (All | Following) with a sliding honey gradient indicator. Content type filters (Now Spinning, New Haul, ISO, etc.) now apply *within* the selected feed mode. Example: Following + ISO = ISO posts from people you follow. Files: `HivePage.js`.
- **BLOCK 60: Comprehensive Micro-Interactions — Honey/Bee Theme** - DONE (2026-03-10). Complete overhaul of App.css with luxurious, professional micro-interactions: (1) Like button: honey-colored with `honeyLike` bounce + `honeyBurst` ring animation. (2) Desktop nav: honey gradient underline on active/hover tabs (`nav-honey-link`). (3) Mobile bottom nav: active honey dot indicator, icon glow, tap scale. (4) Feed posts: staggered `feedSlideIn` entrance animation (5 posts staggered, rest grouped). (5) Notification badges: `badgePulse` glow animation. (6) Avatar: `avatar-honey-ring` glow on hover. (7) Album art: `album-art-hover` tilt+shadow on hover. (8) Modal entrance: honey-themed `modalHoneyIn` with blur deblur. (9) Global button press: `scale(0.96)` on active. (10) Dropdown menus: smooth `dropdownIn`. (11) Page transitions: smooth `pageIn` fade+slide. (12) Honey selection color, focus rings, scrollbar refinement, skeleton loader, tab transitions, follow success animation, count bump. (13) Logo hover: honey drop shadow glow. Files: `App.css`, `Navbar.js`, `HivePage.js`, `PostCards.js`.
- **BLOCK 58: UI Polish — Button Hierarchy, Price Spacing, Variant Labels, Micro-Interactions** - DONE (2026-03-10). (1) Buy Now is now the primary solid CTA, Make Offer is secondary outlined — improves conversion clarity. (2) Price section gets +8px top / +12px bottom breathing room for clear visual hierarchy. (3) Variant label strengthened: larger text (11px→semibold), more padding, bigger disc icon — easily scannable for variant collectors. Pressing info styled as metadata (e.g. "Sunshine Yellow · 2023 pressing"). (4) Album art corners rounded to 10px across all card types for cohesive feel. (5) Global micro-interactions: button press scale(0.96), card lift on hover, modal entrance animation, photo thumbnail zoom, heartPop keyframe. Files: `App.css`, `ListingDetailModal.js`, `PostCards.js`, `ISOPage.js`.
- **BLOCK 57: Editable Listings** - DONE (2026-03-10). Sellers can now edit all details of their ACTIVE listings via an "Edit Listing" button in the ListingDetailModal. Editable fields: price, shipping cost, description, condition, pressing/variant notes, listing type, photos (add/remove), insurance, international shipping. Backend PUT `/api/listings/{listing_id}` validates ownership, ACTIVE status, min 1 photo, $150 new-seller limit, and re-runs off-platform keyword detection. Once sold, listings are locked. Files: `honeypot.py`, `models.py (ListingUpdate)`, `ListingDetailModal.js`.
- **BLOCK 56: Variant Display on Hive Feed Cards + Make Friends Rename** - DONE (2026-03-10). Two changes: (1) Variant/color info now visible directly on Hive feed cards without clicking — `VariantTag` placed in text area below artist name for NOW_SPINNING, ADDED_TO_COLLECTION, DAILY_PROMPT, and listing cards. Removed overlay-on-album-art approach. Format pill fallback when no variant but non-default format. Discogs import now extracts `color_variant` from `formats[].text` field. (2) "Make Friends" feature: backend `/explore/suggested-collectors` updated to sort by shared records count (discogs_id overlap) instead of shared artists, and now excludes blocked users in addition to followed/hidden. Frontend labels already said "Make Friends". Files: `PostCards.js`, `collection.py`, `explore.py`.
- **BLOCK 55: @Mention Tagging in Hive Posts** - DONE (2026-03-09). Full @mention system: `MentionTextarea` component with autocomplete dropdown (fetches `/api/mention-search`), `MentionText` renders @mentions as clickable profile links. All 5 composer endpoints parse mentions and create MENTION notifications (capped at 10). Posts store `mentions` array. PostCards renders MentionText for all post types. CommentItem already had renderMentions. Files: `MentionTextarea.js`, `MentionText.js`, `ComposerBar.js`, `PostCards.js`, `hive.py`.
- **BLOCK 54: Daily Prompt Founder Label Bug Fix** - DONE (2026-03-09). The "Founder" badge was showing for ALL users in Daily Prompt slides because `founding_member` is `true` for all users (first 500 get it for fee purposes). Fixed by restricting the "Founder" label display to only `katieintheafterglow` username. File: `frontend/src/components/DailyPrompt.js`.
- **BLOCK 53: Privacy Settings + Follow Requests + DM Gating** - DONE (2026-03-09). Full 3-phase implementation:
  - **Phase 1 (Privacy + Follow Requests):** `is_private` toggle in Settings. Private profiles show locked content (Instagram-style) with mutual signals. Follow requests with accept/decline. "Request to Follow" / "Requested" button states. FollowRequestsBadge on own profile. All profile data endpoints gated.
  - **Phase 2 (DM Gating):** `dm_setting` (everyone/following/requests) in Settings. DM creation enforces setting. Message requests with pending status. Accept/decline in thread view. Separate "Requests" tab in Messages inbox.
  - **Phase 3 (Notifications):** Follow request notifications, follow request accepted notifications, DM request notifications.
  - DB Collections: `follow_requests {id, from_id, to_id, status, created_at}`, `dm_conversations` now has `status` field.
  - Files: `models.py`, `auth.py`, `explore.py`, `dms.py`, `SettingsPage.js`, `ProfilePage.js`, `FollowRequests.js`, `MessagesPage.js`.
- **BLOCK 52: Clickable Followers/Following with Records in Common** - DONE (2026-03-09). Backend: `/users/{username}/followers` and `/users/{username}/following` now return `records_in_common` count for each user (compared against viewer's collection via discogs_id intersection). Frontend: `UserRow` in `FollowList.js` shows "X records in common" with amber Disc icon when > 0. Files: `backend/routes/explore.py`, `frontend/src/components/FollowList.js`.
- **BLOCK 51: iOS Safari Scroll Freeze Fix** - DONE (2026-03-09). Three-layer fix for scroll freezing on iPhone Safari caused by Radix UI's `data-scroll-locked` attribute persisting after dialogs close: (1) Route-change cleanup in `ScrollToTop` — removes stale scroll locks on every navigation. (2) CSS: `-webkit-overflow-scrolling: touch` and `overscroll-behavior-y: none` on html/body. (3) Safety-net: `visibilitychange` listener + 3s periodic check that removes `data-scroll-locked` if no dialog/overlay is actually visible. Files: `App.js`, `index.css`.
- **BLOCK 50: User Blocking Feature** - DONE (2026-03-09). Full user blocking system: POST/DELETE/GET `/api/block/{username}`. When User A blocks User B, both become invisible to each other (profile 403, posts/comments/collections/spins/ISOs all filtered). Blocking auto-removes mutual follows. Feed, comments, and "My Kinda People" all filter blocked users. Block button on ProfilePage with confirmation dialog. "Profile Unavailable" screen for blocked profiles. Account deletion cleans up blocks. Files: `database.py`, `explore.py`, `auth.py`, `hive.py`, `collection.py`, `ProfilePage.js`.
- **BLOCK 49: Discogs Import Skipped Records Log** - DONE (2026-03-09). Backend now tracks each skipped record with `{title, artist, discogs_id, reason}` during Discogs import. Three reasons: `duplicate` (already in collection), `missing_data` (no discogs_id), `error` (exception with detail). Stored in `discogs_imports` collection and returned in `/api/discogs/import/progress` and `/api/discogs/import/summary`. Frontend: new `SkippedRecordsLog` collapsible component in Import Summary modal groups skipped records by reason with color-coded labels, icons, and Discogs links. Files: `backend/routes/collection.py`, `frontend/src/components/DiscogsImport.js`.
- **BLOCK 48: Global Back Button** - DONE (2026-03-09). Added a subtle fixed back button (ArrowLeft icon) to the AppLayout that appears on all pages except `/` (landing) and `/hive` (home) for authenticated users. Positioned just below the navbar (56px mobile / 94px desktop), 32px hit target, muted stone-400 color with hover effect. Uses `navigate(-1)` for standard browser-back behavior. data-testid="global-back-btn".
- **BLOCK 47: Final Terminology Cleanup** - DONE (2026-03-09). Renamed ALL remaining user-facing "Reality" → "Collection" and "Dream Value" → "Value of ISOs" across the entire app. Changes: Tab label "Reality (N)" → "Collection (N)", toggle pill "Reality" → "Collection Value", toggle pill "Dream Value" → "Value of ISOs", "Add to Reality" → "Add to Collection", "Confirm to Reality" → "Confirm to Collection", "Upgrade to Reality" → "Upgrade to Collection", "Bring to Reality" → "Bring to Collection", toast messages updated, backend acquire response message updated, ProfilePage "Dream Value" → "Value of ISOs", DreamDebtHeader label updated. Files: CollectionPage.js, AddRecordPage.js, ISOPage.js, ProfilePage.js, backend/routes/honeypot.py.
- **Variant Identity Pill**: Frosted glass variant pill overlay on album art across all card types (RecordCard, WishlistCard, ProfilePage collection/dreaming cards). Semi-transparent with blur, gold border, uppercase gold text, mobile-safe truncation.
- **BLOCK 46.1-46.4: Wishlist Value Rebrand + Modal Resync** - DONE (2026-03-09). Renamed all "Dream Value"/"Dream Debt" → "Wishlist Value". Collection header: "If only I had $X... (Wishlist Value)". Profile: "Wishlist Value: $X". Taste match: "You share $X in Wishlist Value." Modal: "Moving to Wishlist?" with "Add to Wishlist Value" CTA in Sunset Gold.
- **BLOCK 44.1-44.3: Taste Match Refinements + Dreaming Tab + Dream Value** - DONE (2026-03-09). New Dreaming tab on public profiles (6 tabs total) with "In Your Collection" badges and "Tell them about this pressing" DM CTA. Honey glow (box-shadow: 0 0 15px #FFD700) on common records, 30% opacity dimming on non-matching. Dream Value sub-headline on profile. New endpoints: GET /api/users/{username}/dreaming, GET /api/valuation/wishlist/{username}. ISO endpoint now excludes WISHLIST items.
- **BLOCK 43.1-43.4: Dream Value Rebrand + Stats Fix + Shared Dream Value** - DONE (2026-03-09). Renamed "Dream Debt" → "Dream Value" everywhere. Headline now reads "If only I had $X... (The Dream Value)" with lighter font weight subtitle. Modal CTA updated to Sunset Gold (#FFB300) with white text and glow. Mobile stats use justify-around for perfect alignment. Taste-match API now returns shared_dream_value showing how much Dream Value two users share.
- **BLOCK 41.1-41.3: Modal CTA + Stats + Taste Match Color Refactor** - DONE (2026-03-09). "Move to Dreaming" button now honey-gold gradient with chocolate brown text and floating glow. "Keep it" button has soft amber border. Following/Followers inline with | separator, 12px spacing to second row. Taste Match pill upgraded to matching honey-gold gradient.
- **BLOCK 39.1-39.3 & 40.1-40.3: Taste Match Engine + Profile Refactor** - DONE (2026-03-09). New backend endpoint GET /api/users/{username}/taste-match calculates compatibility score (shared artists 50%, shared records 30%, shared wishlists 20%). Profile page: stats refactored (Following/Followers top row, Records/Value second row); Taste Match pill below Follow button opens "Common Ground" overlay with Shared Collection, Shared Dreams, Perfect Swap sections; "Show Common Records" toggle filters collection tab; "In Your Collection" badge + "Start a Chat" CTA on ISO items; Founder tooltip on taste match pill; Est. Value links to /collection.
- **BLOCK 37.1-37.3: Collection Cleanse (Reverse Flow + Multi-Select)** - DONE (2026-03-09). Moving items from Reality to Dreaming/Hunt now shows themed confirmation dialogs ("Releasing to the clouds?" / "Back on the hunt?"). Moving to Hunt adds "Seeking Upgrade" tag. Added multi-select mode with "Dreamify" and "Huntify" bulk action buttons. New backend endpoints: POST /records/bulk-move-to-wishlist, POST /records/bulk-move-to-iso. Immediate optimistic value updates for Reality/Dream Debt counters.
- **BLOCK 34.1-34.3: Dream Debt Header & Reality Comparison** - DONE (2026-03-09). Dreaming tab now shows "If only I had $X..." with serif italic amber price and counting animation (easeOutCubic, 1400ms) on tab open. Empty fallback: "Your dreams are currently free. Go find some grails." Reality header now shows "The Gold Standard: $X worth of wax on your shelf." with gold gradient. "Bring to Reality" shows subtraction text and updates counter immediately. New endpoint: GET /api/valuation/record-value/{discogs_id}. Nav item renamed from "Reality" to "Collection".
- **BLOCK 31: "Upgrade to Reality" Modal** - DONE (2026-03-09). When clicking "Found It" on a Wantlist/Hunt item, a confirmation modal now appears with Media Condition dropdown, Sleeve Condition dropdown, and optional Price Paid input. New backend endpoint POST /api/iso/{id}/acquire stores condition/price data on the collection record. Confetti + toast + redirect on success. Old /convert-to-collection endpoint retained for backwards compatibility.
- **BLOCK 30: Context-Sensitive Add Record** - DONE (2026-03-09). Dynamic "Add to Reality" / "Add to Dreaming" button based on active tab. AddRecordPage reads ?mode param — Reality mode: POST /api/records (collection), Dreaming mode: POST /api/iso with WISHLIST status. Context-aware confirm buttons ("Confirm to Reality" / "Save to Dreams"), toasts, and headings. Color Variant selector on all add forms. ?tab=wishlist URL param auto-switches Collection to Dreaming tab.
- **BLOCK 29: Refreshed Reality Branding** - DONE (2026-03-09). Reality header → "The Gold Standard." with gold gradient text. Dreaming header → "In the Clouds." Sparkles icon on Reality tab. RecordCards glassmorphism. Reality Check toggle. "Bring to Reality" button.
- **BLOCK 28: "Reality" Refactor** - DONE (2026-03-09). Collection tabs renamed to "Reality" (owned) + "Dreaming" (wishlist). Desktop/mobile nav renamed from "Collection" → "Reality". Record card dropdown: "Move to Dreaming", "Put on The Hunt", "Remove Completely".
- **BLOCK 27.1: Collection Tabs Refactor** - DONE (2026-03-09). Collection page split into "The Hive" (Owned) + "Wishlist" (Dreaming) tabs. Wishlist tab: Dream Debt banner with total value, "In your dreams..." copy, Certified Delusional badge (>$5K), WishlistCards with ghost variant pills and "Ready to Buy?" promote button.
- **BLOCK 27.2: Honeypot Wantlist Refactor** - DONE (2026-03-09). ISO tab renamed to "Wantlist" with "The Hunt is On." header tagline. WISHLIST items moved to Collection's Wishlist tab.
- **BLOCK 27.3: Variant Pill Sync** - DONE (2026-03-09). VariantTag now has 4 modes: solid (owned), glass (album art overlay), ghost (dreaming, outlined), gold (hunting, gradient). Supports prefix prop ("Dreaming of", "Hunting"). New PUT /api/iso/{id}/promote endpoint changes WISHLIST → OPEN status.
- **"Dream Debt" Wishlist Calculator** - DONE (2026-03-09). GET /api/valuation/wishlist returns total median value of WISHLIST ISO items. Frontend shows editorial "Dream Debt" card at top of Wishlist section ("Total Value of Your Dreams: $X" / "You've got expensive taste, babe. Start playing the lottery."). Gold "Certified Delusional" badge when value > $5,000. WISHLIST filter added to ISO tab.
- **BLOCK 18.1: ISO "I Found It!" Hunt Flow** - DONE (2026-03-09). POST /api/iso/{id}/convert-to-collection migrates ISO → collection record (notes='Found via ISO'). Frontend: confetti cannon (honey colors), toast celebration, auto-redirect to /collection after 1.5s.
- **BLOCK 18.2: Collection Quick Actions** - DONE (2026-03-09). RecordCard dropdown now has 4 options: Log Spin, Move to Wishlist (→ ISO WISHLIST status), Put back on ISO (→ ISO OPEN status), Remove Completely. Backend: POST /api/records/{id}/move-to-wishlist and /move-to-iso.
- **BLOCK 19.1: Optimistic Likes** - DONE (2026-03-09). Like button now has instant visual feedback with rollback on failure + "Sticky situation—try again" toast. Larger mobile touch target (p-2, 20px hitSlop), active:scale-125 tap animation, touchAction:manipulation.
- **BLOCK 19.2: Color Variant Pill** - DONE (2026-03-09). VariantTag now has Disc icon + glassmorphism mode (backdrop-filter blur, dark transparent bg, white text) for album art overlays. Added to NowSpinning, DailyPrompt, and Listing cards. PostResponse now includes color_variant and pressing_notes.
- **BLOCK 19.3: Collector Notes Overlay** - DONE (2026-03-09). NowSpinningCard shows record.notes, ListingPostCard shows pressing_notes. Italic serif font, truncated to 60 chars.
- **CRITICAL: Feed Visibility Fix** - DONE (2026-03-09). GET /api/feed now returns ALL posts from all non-hidden users instead of only followed users + self. New users can see all posts in The Hive. Frontend "Following" filter updated to use actual following list fetched from /api/users/{username}/following.
- **Admin Remove User** - DONE (2026-03-09). Trash icon on each user row in Admin Panel > User Management. Confirmation modal with permanent deletion warning. Backend DELETE /api/admin/users/{user_id} removes user + all associated data (posts, comments, likes, followers, records, spins, ISOs, notifications, reports). Self-deletion prevented.
- **"New Feature" Tag System** - DONE (2026-03-09). Admin-only tag for Hive posts with muted green pill badge, subtle card emphasis (#f3faf5 background + shadow-md), feed filter support, and admin dropdown toggle via POST /api/posts/{post_id}/new-feature.
- **Notes/Bio Paste Fix** - DONE (2026-03-09). Fixed silent paste rejection in ComposerBar Notes (280), Settings Bio (160), Settings Setup (100). Changed conditional `if (len <= max)` pattern to `.slice(0, max)` truncation so paste always works.
- Tag Color Inconsistency - DONE (shared TagPill, ListingTypeBadge, PostTypeBadge components)
- Report Bug Screenshot Upload - DONE
- **Essentials Upsell Modal** - One-time checkout upsell showing Core Three products before Stripe redirect. "Yes, Show Me" opens /essentials in new tab + continues checkout. "No Thanks" continues checkout. localStorage-based one-time display
- Honey Shop Essentials (BLOCK 5.3) - DONE (static affiliate page at /essentials)
- Welcome to the Hive Dashboard (BLOCK 5.1) - DONE
- HONEY Order ID Branding (BLOCK 4.3) - DONE
- Navbar Report Button - DONE

### Future / Backlog
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Buyer Protection features
- Re-enable Instagram sharing
- Golden Hive badge on user displays throughout app
- Break down GlobalSearch.js
- Replace star imports in backend
