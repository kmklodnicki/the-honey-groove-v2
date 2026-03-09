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

### P1
- Weekly Wax Email - configure scheduled email every Sunday 12:00 PM ET

### P2
- Hauls Enhancement - dedicated page
- Refactor ISOPage.jsx - technical debt
- Grading Guide page (optional)

### Completed Recently
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
