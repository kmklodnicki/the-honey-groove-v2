# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Social platform for vinyl record collectors. The admin reported production stability issues, UI bugs, and data mapping errors on the live site (`thehoneygroove.com`).

## Tech Stack
- Frontend: React (CRA) + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB Atlas
- Deployment: Emergent Platform -> custom domain `thehoneygroove.com`

## Core Requirements
1. **Production Stability (P0):** Live app must be stable with working auth, feed, and collection
2. **UI/UX Integrity (P0):** Fix critical UI bugs (modals, layouts, data display)
3. **Aesthetic Polish (P0):** Unified card design across all feed types
4. **Instagram Story Export (P1):** Export Daily Prompt as 1080x1920 PNG
5. **Service Worker Caching (P1):** Pre-cache assets for faster loads

## What's Been Implemented

### Session 1 (Previous Fork)
- Auth overhaul (GET /api/auth/me, password reset, JWT enrichment)
- Modal overflow fixes for mobile
- Text truncation fixes on feed/honeypot cards
- Infinite scroll fix on HivePage
- VinylShield error boundary
- Discogs API resilience (retry + cache fallback)

### Session 2 (March 14, 2026)
- Centralized API URL resolution (`apiBase.js`)
- VinylShield fix — removed overly aggressive health check
- Global 30s axios timeout
- ISO card data mapping fix — "Pressing" shows `color_variant`
- Backend variant fallback removed
- AlbumLink fix — handles `record_id` from bundle records
- "Recover Values" button resilience
- Service worker cache bump (v2 -> v3)
- MongoDB password update for Atlas user `katie`
- Manual password reset for user `usahoyt@aol.com`

### Session 3 (March 14, 2026 - Design Polish)
- **Background Update**: Changed from `#F8E9E4` to `#FFF6E6` (warm cream)
- **Honeycomb Pattern**: Increased opacity from 0.04 to 0.08 for clear visibility
- **CSS Variable Sync**: Updated `--background` to `hsl(40, 100%, 95%)` to match
- **ISO VariantTag Mirroring**: ISO cards now use exact same gold-bordered VariantTag as Daily Prompt cards (disc icon, backdrop-blur, `#DAA520` border)
- **Colon Label Format**: Changed from "Pressing Pink Nebula" to "Pressing: Pink Nebula" across all card types
- **Backend ISO `color_variant` Sync**: 
  - Added `color_variant` field to `ISOPostCreate` model
  - ISO composer endpoint now extracts `color_variant` from Discogs release data
  - Created background ISO backfill task (runs on startup, updated 13/49 existing items)
- **Testing**: All verified via testing agent (100% pass rate, 6 backend + 8 frontend tests)

## Known Issues
- Production custom domain has ~21s proxy latency (vs 0.24s on preview URL)
- Some ISO items in DB have grade info in `pressing_notes` field (data quality issue)
- Web scraper (`services/scraper.py`) is fragile — needs rotating User-Agents
- 36/49 ISO items don't have `color_variant` because Discogs doesn't list a specific pressing variant for those releases

## Prioritized Backlog

### P0 - Complete
- [x] Production stability
- [x] VinylShield blocking fix
- [x] Feed skeleton loader fix
- [x] ISO card data mapping
- [x] Record linking fix
- [x] Unified ISO/Daily Prompt card design
- [x] Background theme update (#FFF6E6 + honeycomb)
- [x] Backend/frontend color_variant sync for ISOs

### P1 - Upcoming
- [ ] Instagram Story Export (Daily Prompt as 1080x1920 PNG)
- [ ] Service Worker Caching improvements
- [ ] Streaming Service Integration (needs Spotify callback URL)

### P2 - Future
- [ ] Record Store Day Proxy Network
- [ ] Safari-compatible loading animation
- [ ] Pro memberships / Verified Seller badge
- [ ] Secret Search Feature
- [ ] New Music Friday dynamic editing
- [ ] Web scraper hardening

### Refactoring
- [ ] Break down monolithic `server.py` into route modules
- [ ] Split complex `PostCards.js` into smaller type-specific components

## Credentials
- Admin: `kmklodnicki@gmail.com` / `HoneyGroove2026!`
- Atlas: `katie` / `HoneyGroove2026`

## Key Files
- `frontend/src/index.css` — Background theme + honeycomb pattern
- `frontend/src/utils/apiBase.js` — Single source of truth for API URL
- `frontend/src/context/AuthContext.js` — Auth + session management
- `frontend/src/components/PostCards.js` — Feed card rendering (VariantTag, all card types)
- `frontend/src/pages/LoginPage.js` — Login page with honeycomb bg
- `frontend/src/pages/CollectionPage.js` — Collection/Vault page
- `frontend/src/components/VinylShield.js` — Error boundary
- `backend/routes/hive.py` — Feed/post endpoints + ISO composer
- `backend/routes/collection.py` — Collection/record endpoints
- `backend/routes/auth.py` — Authentication endpoints
- `backend/models.py` — Pydantic models (ISOPostCreate has color_variant)
- `backend/server.py` — Startup tasks including ISO backfill
