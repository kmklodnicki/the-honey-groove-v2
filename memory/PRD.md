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
- Country selection on signup
- Admin-assignable custom title labels (e.g., "Founder", "Moderator")
- Social media links (Instagram, TikTok) on profiles
- Email change with verification flow
- **Golden Hive verification** (BLOCK 3.3) - ID upload, admin review, badge

### Social Feed ("The Hive")
- Post types: Now Spinning, New Haul, ISO, A Note, Daily Prompt
- Full comment system with likes, nested replies, @mentions
- Admin pin post to top, pagination, "Back to Top" button

### Daily Prompt
- Daily prompt refresh at midnight ET, streak tracking
- Live album search in Buzz-In modal (debounced collection search)

### Marketplace ("The Honeypot")
- Stripe Connect LIVE peer-to-peer payments
- Sale/trade listings auto-post to Hive
- International shipping toggle, country-based restrictions
- Clickable "My Sales" rows with order details
- **Dual Grading System** (BLOCK 2.2+2.3) - NM/VG+/VG/G+/F with Honey labels + tooltips
- **Payout Estimator** (BLOCK 3.1) - Live fee/shipping/Take Home Honey calculation
- **Pulse Integration** (BLOCK 3.1) - 90-day Discogs price analysis, hot zone indicator
- **Shipping Cost** field on listings (default $6.00)
- **Auto-Payout Cron** (BLOCK 3.2) - 72h standard / 24h for 4.5+ rated sellers

### Verification Queue — The Gate (BLOCK 3.3)
- User ID photo upload in Settings page
- Server-side image blurring for admin preview
- Admin dashboard section "The Gate" with:
  - Blurred ID preview (unblur on demand)
  - Approve/Deny actions
  - Golden Hive badge on approval
- `golden_hive` boolean on user model, exposed in API

### Search & Discovery
- "Psychic" global search with weighted scoring
- Infinite scroll for records grouped by artist
- Discogs API fallback

### Collection Management
- Add records via Discogs search
- EXIF orientation fix, pressing variant display

### SEO & Accessibility
- JSON-LD schema, dynamic alt tags, country flags

## Key New Files (This Session)
- `/app/backend/routes/verification.py` - Verification Queue endpoints
- `/app/backend/routes/payout_cron.py` - Auto-payout cron logic
- `/app/frontend/src/components/GoldenHiveBadge.js` - Badge component

## Mocked Integrations
- **Email (Resend):** Logic in place but not using a live service

## Pending / Upcoming Tasks

### P1
- Weekly Wax Email - configure scheduled email every Sunday at 12:00 PM ET

### P2
- Hauls Enhancement - dedicated page and more functionality
- Refactor ISOPage.jsx - address technical debt
- "What do these grades mean?" Grading Guide page (optional)

### Future / Backlog
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Deferred Buyer Protection features
- Re-enable Instagram sharing
- Break down GlobalSearch.js into smaller components
- Replace star imports in backend routes
