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

### Social Feed ("The Hive")
- Post types: Now Spinning, New Haul, ISO, A Note, Daily Prompt
- Full comment system with likes, nested replies, @mentions
- Admin pin post to top of feed
- Pagination ("View Older Posts") and "Back to Top" button
- Mood-themed Now Spinning posts

### Daily Prompt
- Daily prompt refresh at midnight ET
- Streak tracking
- Live album search in Buzz-In modal (debounced collection search) - **Feb 2026**
- Export card feature, Post to Hive option

### Marketplace ("The Honeypot")
- Stripe Connect LIVE peer-to-peer payments
- Sale/trade listings auto-post to Hive
- International shipping toggle, country-based restrictions
- Clickable "My Sales" rows with order details

### Dual Grading System (BLOCK 2.2 + 2.3) - **Feb 2026**
- Standard vinyl grades (NM, VG+, VG, G+, F) stored in DB
- Honey-branded labels derived from mapping layer:
  - NM -> Queen's Choice
  - VG+ -> The Sweet Spot
  - VG -> Hive Classic
  - G+/G -> Well-Worn Honeycomb
  - F/P -> Sticky Situation
- GradeLabel component with 3 variants: pill, compact, inline
- Tooltips with full descriptions on hover (Radix UI)
- Listing form dropdown shows dual format (code + honey label)
- Legacy long-form values (Near Mint, Very Good Plus, etc.) backward-compatible via normalizeGrade()
- Applied across: marketplace cards, listing detail modal, trade proposals, orders, global search

### Search & Discovery
- "Psychic" global search with weighted scoring
- Infinite scroll for records grouped by artist
- Discogs API fallback for sparse results

### Collection Management
- Add records via Discogs search
- EXIF orientation fix for uploaded images
- Pressing variant display on cards

### SEO & Accessibility
- JSON-LD schema, dynamic alt tags for all album art
- Country flags on profiles and listings

## Mocked Integrations
- **Email (Resend):** Logic in place but not using a live service

## Key New Files (Grading System)
- `/app/frontend/src/utils/grading.js` - GRADE_MAP, GRADE_OPTIONS, normalizeGrade, formatGradeDisplay, gradeCode, gradeColorClass
- `/app/frontend/src/components/GradeLabel.js` - Reusable component with tooltip support

## Pending / Upcoming Tasks

### P1
- Weekly Wax Email - configure scheduled email every Sunday at 12:00 PM ET

### P2
- Hauls Enhancement - dedicated page and more functionality
- Refactor ISOPage.jsx - address technical debt
- Optional: "What do these grades mean?" link to Honey Groove Grading Guide page

### Future / Backlog
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Deferred Buyer Protection features
- Re-enable Instagram sharing
- Break down GlobalSearch.js into smaller components
- Replace star imports in backend routes
