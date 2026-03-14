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
4. **Performance (P0):** Twitter-level snappiness — optimistic UI, caching, lazy loading
5. **Instagram Story Export (P1):** Export Daily Prompt as 1080x1920 PNG
6. **Service Worker Caching (P1):** Pre-cache assets for faster loads

## What's Been Implemented

### Session 1 (Previous Fork)
- Auth overhaul, modal overflow fixes, text truncation, infinite scroll fix
- VinylShield error boundary, Discogs API resilience

### Session 2 (March 14, 2026)
- Centralized API URL, global 30s axios timeout
- ISO card data mapping fix, AlbumLink fix, collection button resilience
- MongoDB connection retry logic, JWT enrichment with isAdmin/avatar

### Session 3 (March 14, 2026 - Design Polish)
- Background: `#FFF6E6` warm cream with honeycomb pattern
- ISO VariantTag: unified gold-bordered pill with "Pressing:" colon format
- Backend ISO `color_variant` sync + backfill task (13/49 updated)

### Session 4 (March 14, 2026 - UI Polish + Performance)
- **Feed Filter Pills**: Fixed emoji overflow — `inline-flex items-center`, `px-4 py-1.5`, `whitespace-nowrap`, `flex-shrink-0` on emoji span. Text and emoji split into separate spans for proper alignment.
- **Honeycomb Pattern**: Decreased SVG size by 25% (56px→42px, 100px→75px), increased opacity to 0.12 for more defined texture.
- **ISO Budget Text**: Changed "? – $200" to "Up to $200" when only max price exists. Shows "$X – $Y" for both, "From $X" for min only.
- **Feed Caching**: Added `sessionStorage` cache (`hg_feed_cache`). On return visits, shows cached feed instantly while fetching fresh data in background.
- **Optimistic Comments**: Comments appear immediately in the thread before server confirmation. On failure, reverted with error toast.
- **Optimistic Comment Likes**: Like/unlike toggles instantly with revert on failure (matching existing post-like pattern).
- **Reply Auto-Focus + Scroll**: Clicking reply focuses input AND calls `scrollIntoView({ behavior: 'smooth', block: 'center' })` to keep input visible on mobile when keyboard opens.
- **View Replies Toggle**: Threads with 3+ replies collapse to show first 2, with "View X more replies" button. Includes "Hide replies" to collapse.
- All verified via testing agent (100% pass: 11 Playwright UI tests + 5 code review checks)

## Known Issues
- Production custom domain has ~21s proxy latency (mitigated by hardcoded preview URL)
- Some ISO items in DB have grade info in `pressing_notes` (data quality)
- Web scraper (`services/scraper.py`) fragile — needs rotating User-Agents
- 36/49 ISO items lack Discogs color_variant data

## Prioritized Backlog

### P0 - Complete
- [x] Production stability
- [x] Feed skeleton / VinylShield fix
- [x] ISO card data mapping + unified design
- [x] Background theme (#FFF6E6 + honeycomb)
- [x] Feed filter pill styling (emoji overflow fix)
- [x] ISO budget text fix ("Up to $X")
- [x] Twitter-level performance (optimistic UI, caching, lazy loading)
- [x] Threaded comment polish (View Replies, auto-focus+scroll)

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
- [ ] Split `PostCards.js` into type-specific card components

## Key Files
- `frontend/src/index.css` — Background theme + honeycomb pattern
- `frontend/src/pages/HivePage.js` — Feed, filter pills, caching, optimistic UI, comments
- `frontend/src/components/PostCards.js` — Feed card rendering, ISO budget text, VariantTag
- `frontend/src/components/CommentItem.js` — Comment thread with View Replies toggle
- `frontend/src/components/AlbumArt.js` — Lazy-loaded album art with CacheStorage
- `frontend/src/utils/apiBase.js` — API URL (hardcoded to preview for speed)
- `frontend/src/context/AuthContext.js` — Auth + session management
- `backend/routes/hive.py` — Feed/post/ISO endpoints
- `backend/server.py` — Startup tasks (backfill)
- `backend/models.py` — Data models

## Credentials
- Admin: `kmklodnicki@gmail.com` / `HoneyGroove2026!`
