# The HoneyGroove - Product Requirements Document

## Original Problem Statement
The HoneyGroove is a social platform for vinyl record collectors built with React/FastAPI/MongoDB. The admin has been guiding development through bug reports and feature requests, focusing on production stability, UI/UX polish, performance optimization, and admin capabilities.

## Tech Stack
- **Frontend:** React (CRA), Shadcn/UI, Tailwind CSS
- **Backend:** FastAPI (Python), Motor (async MongoDB)
- **Database:** MongoDB Atlas
- **3rd Party:** Resend (email), Stripe Connect (payments), Discogs API (album metadata)

## Core Features (Completed)
- Feed with SWR-like caching (useFeed.js), optimistic UI for likes/comments/follows
- Daily Prompt with SWR caching, buzz-in with retry logic, streak tracking
- Admin panel with temp password, user management, beta invites, reports
- Threaded comment replies, follow/unfollow with optimistic UI
- Password reset (dynamic URL from Origin header)
- Record data hydration for ghost records in feed
- Custom "Honeypot" branded login animation
- Global price cache visible to all profile viewers

## Key Credentials
- Admin: `kmklodnicki@gmail.com` / `HoneyGroove2026!`

## Completed Work

### Session 2 (Mar 14, 2026)
- **Daily Prompt Submission Fix:** Added retry logic in `handleSubmit` — if buzz-in returns 404 "not found" (stale/deleted prompt_id), the component re-fetches `/prompts/today` and retries with the fresh prompt_id.
- **Discogs Pricing Bug Fix:** Created new public endpoint `GET /valuation/record-values/{username}` that returns median values for ANY user's collection. Updated `ProfilePage.js` to fetch values for any profile (not just own). Verified 147 priced records for katie, 86 for travis.
- **Ghost Records Fix:** Backend `build_post_response()` hydrates missing record_title/cover_url from records collection; skips posts where record was deleted.
- **DailyPrompt Skeleton Fix:** Added SWR-like localStorage caching for instant render; AbortController for StrictMode cleanup.
- **Admin Panel Layout Fix:** Changed nav button container from `overflow-x-auto` to `flex-wrap`.

### Session 1 (Previous)
- Performance: SWR-like feed caching, optimistic UI, lazy loading
- Password reset URL fix, Daily Prompt sync fix, threaded comments
- Admin temp password feature, change password in settings

## Architecture
```
/app/
├── backend/
│   ├── server.py
│   ├── routes/
│   │   ├── hive.py           # Feed, ghost record hydration
│   │   ├── daily_prompts.py  # Prompt CRUD, buzz-in, streak
│   │   ├── valuation.py      # NEW: /record-values/{username} public endpoint
│   │   └── collection.py     # Record CRUD, user collections
│   ├── database.py
│   └── models.py
├── frontend/
│   └── src/
│       ├── api/apiBase.js
│       ├── components/
│       │   ├── DailyPrompt.js  # SWR cached + retry on stale prompt_id
│       │   └── ...
│       ├── context/AuthContext.js
│       ├── hooks/useFeed.js, useAPI.js
│       └── pages/
│           ├── HivePage.js
│           ├── ProfilePage.js  # Fixed: fetches values for any user
│           ├── CollectionPage.js
│           └── AdminPage.js    # Fixed: flex-wrap nav
```

## Key API Endpoints
- `POST /api/auth/login` → returns `access_token`
- `GET /api/prompts/today` → today's prompt with buzz_count, streak
- `POST /api/prompts/buzz-in` → submit daily prompt answer
- `GET /api/feed` → hydrated feed with record data
- `GET /api/valuation/record-values/{username}` → (NEW) public median values for any user
- `GET /api/valuation/record-values` → median values for authenticated user
- `GET /api/users/{username}/records` → user's collection list

## Prioritized Backlog

### P1 - Upcoming
- Instagram Story Export (1080x1920 PNG from Daily Prompt)
- Login Pre-fetching (pre-fetch feed/profile during login animation)
- Service Worker Caching (pre-cache key assets)

### P2 - Future
- Spotify Integration (needs callback URL from user)
- Record Store Day Proxy Network
- Safari-compatible loading animation
- Pro memberships / Verified Seller badge
- Secret Search Feature
- New Music Friday dynamic editing in Weekly Wax email

### Refactoring
- Break down monolithic server.py into route modules
- Split PostCards.js into type-specific card components

## Known Issues
- Discogs CDN returns 503 for some album images (external, not our bug)
- Web scraper needs rotating User-Agents (backend/services/scraper.py)
