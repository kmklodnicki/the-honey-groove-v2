# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Social platform for vinyl record collectors. The admin reported production stability issues, UI bugs, and data mapping errors on the live site (`thehoneygroove.com`).

## Tech Stack
- Frontend: React (CRA) + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB Atlas
- Deployment: Emergent Platform → custom domain `thehoneygroove.com`

## Core Requirements
1. **Production Stability (P0):** Live app must be stable with working auth, feed, and collection
2. **UI/UX Integrity (P0):** Fix critical UI bugs (modals, layouts, data display)
3. **Instagram Story Export (P1):** Export Daily Prompt as 1080x1920 PNG
4. **Service Worker Caching (P1):** Pre-cache assets for faster loads

## What's Been Implemented

### Session 1 (Previous Fork)
- Auth overhaul (GET /api/auth/me, password reset, JWT enrichment)
- Modal overflow fixes for mobile
- Text truncation fixes on feed/honeypot cards
- Infinite scroll fix on HivePage
- VinylShield error boundary
- Discogs API resilience (retry + cache fallback)

### Session 2 (Current - March 14, 2026)
- **Centralized API URL resolution** (`apiBase.js`) — all 17+ files now use single source
- **VinylShield fix** — removed overly aggressive health check that blocked app (8s timeout vs 21s prod latency)
- **Global 30s axios timeout** — prevents production proxy latency from killing requests
- **ISO card data mapping fix** — "Pressing" now shows `color_variant`, not `pressing_notes`/grade
- **Backend variant fallback removed** — `build_post_response` no longer falls back to `pressing_notes`
- **AlbumLink fix** — now handles `record_id` from bundle records for correct linking
- **"Recover Values" button resilience** — shows even when valuation API is slow
- **Service worker cache bump** (v2 → v3)
- **MongoDB password update** for Atlas user `katie`
- **Manual password reset** for user `usahoyt@aol.com`

## Known Issues
- Production custom domain has ~21s proxy latency (vs 0.24s on preview URL)
- Some ISO items in DB have grade info in `pressing_notes` field (data quality issue)
- Web scraper (`services/scraper.py`) is fragile — needs rotating User-Agents

## Prioritized Backlog

### P0 - Complete
- [x] Production stability
- [x] VinylShield blocking fix
- [x] Feed skeleton loader fix
- [x] ISO card data mapping
- [x] Record linking fix

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
- [ ] Deployment configuration hardening

## Credentials
- Admin: `kmklodnicki@gmail.com` / `HoneyGroove2026!`
- Atlas: `katie` / `HoneyGroove2026`

## Key Files
- `frontend/src/utils/apiBase.js` — Single source of truth for API URL
- `frontend/src/context/AuthContext.js` — Auth + session management
- `frontend/src/components/PostCards.js` — Feed card rendering
- `frontend/src/pages/CollectionPage.js` — Collection/Vault page
- `frontend/src/components/VinylShield.js` — Error boundary
- `backend/routes/hive.py` — Feed/post endpoints
- `backend/routes/collection.py` — Collection/record endpoints
- `backend/routes/auth.py` — Authentication endpoints
