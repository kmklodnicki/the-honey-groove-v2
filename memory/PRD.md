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

### Report a Problem System (BLOCK 3.4)
- Listing reporting (6 reasons + Other)
- Seller reporting (5 reasons)
- Order issue reporting (4 reasons)
- Bug reporting with auto-captured URL + browser info
- Rate limiting: 5 reports per user per 24 hours
- **Admin Watchtower** - filterable queue with actions:
  - Review, Dismiss, Resolve, Remove Listing, Warn Seller, Suspend Seller
- Report buttons on: listing detail, seller profile, orders, settings page
- **Global Navbar Report Button** - AlertTriangle icon in desktop navbar + mobile top bar, opens ReportModal with type "bug" (March 2026)

### Verification Queue — The Gate (BLOCK 3.3)
- User ID upload, server-side blur, admin approve/deny
- Golden Hive badge on approval

### Search, Collection, SEO
- Psychic search, infinite scroll, Discogs fallback
- EXIF fix, pressing variants, country flags
- JSON-LD schema, **alt tags: "Artist - Title Vinyl Record"** format

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
- Tag Color Inconsistency - unify PostTypeBadge colors between Hive feed and marketplace listing cards
- Weekly Wax Email - configure scheduled email every Sunday 12:00 PM ET

### P2
- Hauls Enhancement - dedicated page
- Refactor ISOPage.jsx - technical debt
- Grading Guide page (optional)

### Future / Backlog
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Buyer Protection features
- Re-enable Instagram sharing
- Golden Hive badge on user displays throughout app
- Break down GlobalSearch.js
- Replace star imports in backend
