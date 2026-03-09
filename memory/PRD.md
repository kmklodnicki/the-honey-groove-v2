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
