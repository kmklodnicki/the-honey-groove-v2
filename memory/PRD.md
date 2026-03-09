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
- Post type label colors standardized

### Daily Prompt
- Daily prompt refresh at midnight ET
- Streak tracking
- Live album search in Buzz-In modal (searches user's collection with debounced input) - **COMPLETED Feb 2026**
- Export card feature
- Post to Hive option

### Marketplace ("The Honeypot")
- Stripe Connect LIVE peer-to-peer payments
- Sale/trade listings auto-post to Hive
- International shipping toggle
- Country-based purchase restrictions
- Clickable "My Sales" rows with order details

### Search & Discovery
- "Psychic" global search with weighted scoring
- Infinite scroll for records grouped by artist
- Discogs API fallback for sparse results

### Collection Management
- Add records via Discogs search
- EXIF orientation fix for uploaded images
- Pressing variant display on cards

### SEO & Accessibility
- JSON-LD schema
- Dynamic alt tags for all album art
- Country flags on profiles and listings

## Mocked Integrations
- **Email (Resend):** Logic in place but not using a live service

## Pending / Upcoming Tasks

### P1
- Weekly Wax Email - configure scheduled email every Sunday at 12:00 PM ET

### P2
- Hauls Enhancement - dedicated page and more functionality
- Refactor ISOPage.jsx - address technical debt

### Future / Backlog
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Deferred Buyer Protection features
- Re-enable Instagram sharing
- Break down GlobalSearch.js into smaller components
- Replace star imports in backend routes

## Key Files
- `frontend/src/components/DailyPrompt.js` - Daily Prompt card + Buzz-In modal with live search
- `frontend/src/components/ComposerBar.js` - Post composer (Now Spinning, Haul, ISO, Note)
- `frontend/src/components/layout/GlobalSearch.js` - Psychic search with infinite scroll
- `frontend/src/pages/HivePage.js` - Main social feed
- `backend/routes/buzz.py` - Daily prompt backend
- `backend/routes/search.py` - Search endpoints
- `backend/routes/honeypot.py` - Marketplace
