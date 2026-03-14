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
- Daily Prompt with caching, buzz-in, streak tracking, carousel responses
- Admin panel with temp password, user management, beta invites, reports
- Threaded comment replies, follow/unfollow with optimistic UI
- Password reset (dynamic URL from Origin header)
- Record data hydration for ghost records
- Custom "Honeypot" branded login animation

## Key Credentials
- Admin: `kmklodnicki@gmail.com` / `HoneyGroove2026!`

## Completed Work (Mar 14, 2026)
- **Ghost Records Fix:** Backend `build_post_response()` now hydrates missing record_title/cover_url from records collection; skips posts where record was deleted (35 orphaned records filtered out)
- **DailyPrompt Skeleton Fix:** Added SWR-like localStorage caching for instant render on subsequent visits; AbortController cleanup for React StrictMode
- **Admin Layout Fix:** Changed button container from `overflow-x-auto` to `flex-wrap` for two-row layout on desktop

## Architecture
```
/app/
├── backend/
│   ├── server.py           # Main FastAPI app
│   ├── routes/
│   │   ├── hive.py         # Feed, posts, ghost record hydration
│   │   ├── daily_prompts.py # Prompt CRUD, buzz-in, streak, export
│   │   └── ...
│   ├── database.py         # DB connection, auth helpers
│   └── services/
├── frontend/
│   └── src/
│       ├── api/apiBase.js   # Uses REACT_APP_BACKEND_URL
│       ├── components/
│       │   ├── DailyPrompt.js  # SWR cached prompt card
│       │   └── ...
│       ├── context/AuthContext.js
│       ├── hooks/useFeed.js
│       └── pages/
│           ├── HivePage.js
│           ├── AdminPage.js (flex-wrap nav)
│           └── ...
```

## Key API Endpoints
- `POST /api/auth/login` → returns `access_token` (not `token`)
- `GET /api/prompts/today` → today's prompt with buzz_count, streak
- `POST /api/prompts/buzz-in` → submit daily prompt answer
- `GET /api/feed` → hydrated feed with record data
- `POST /api/admin/users/{user_id}/temp-password` → admin temp password

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
- Web scraper (backend/services/scraper.py) needs rotating User-Agents
