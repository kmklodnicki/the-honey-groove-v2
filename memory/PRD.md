# The HoneyGroove - Product Requirements Document

## Original Problem Statement
The HoneyGroove is a social platform for vinyl record collectors built with React/FastAPI/MongoDB. The admin has been guiding development through bug reports and feature requests, focusing on production stability, UI/UX polish, performance optimization, and admin capabilities.

## Tech Stack
- **Frontend:** React (CRA), Shadcn/UI, Tailwind CSS
- **Backend:** FastAPI (Python), Motor (async MongoDB)
- **Database:** MongoDB Atlas
- **3rd Party:** Resend (email), Stripe Connect (payments), Discogs API (album metadata)

## Core Features (Completed)
- Feed with SWR-like caching, optimistic UI for likes/comments/follows
- Daily Prompt with SWR caching, buzz-in with retry logic, streak tracking
- **Polls** — 6th composition type with blind voting, Honey Gold branding, persistence
- Admin panel with temp password, user management, beta invites, reports
- Threaded comment replies, follow/unfollow with optimistic UI
- Password reset (dynamic URL), record data hydration for ghost records
- Global price cache visible to all profile viewers

## Key Credentials
- Admin: `kmklodnicki@gmail.com` / `HoneyGroove2026!`

## Completed Work

### Session 3 (Mar 14, 2026) — Polls Feature
- **Full Poll Implementation:** Backend (PollCreate model, `POST /composer/poll`, `POST /polls/{post_id}/vote`, poll_votes collection, per-option results in build_post_response) + Frontend (PollCard with blind voting UX, Poll composer in ComposerBar with dynamic options min 2/max 6, 500 char limit)
- **Honey Gold Branding (#DAA520):** Gold progress bars with slide animation, gold circle checkmark for "My Vote" indicator, 📊 emoji in filter pills/badge/composer, amber PILL_STYLES
- **Responsive Layout:** Feed filter bar wraps into clean rows (flex-wrap, max-width 580px desktop). ComposerBar supports 6 chips with wrap on mobile. 📊 Poll filter visible in both layouts
- **Blind Voting:** Pre-vote shows clickable buttons without percentages. Post-vote reveals gold percentage bars and "X people responded" count. Persistence: refresh shows results for users who already voted

### Session 2 (Mar 14, 2026)
- Daily Prompt submission retry on stale prompt_id
- Discogs pricing fix: public `GET /valuation/record-values/{username}` endpoint
- Ghost records hydration, DailyPrompt SWR caching, Admin layout flex-wrap

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
│   │   ├── hive.py           # Feed, posts, ghost record hydration, POLL composer + vote
│   │   ├── daily_prompts.py  # Prompt CRUD, buzz-in, streak
│   │   ├── valuation.py      # /record-values/{username} public endpoint
│   │   └── collection.py     # Record CRUD
│   ├── models.py             # PollCreate, PostResponse with poll_* fields
│   └── database.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── PostCards.js    # PollCard (blind voting, gold bars), PostTypeBadge with 📊
│       │   ├── ComposerBar.js  # 6 chips incl. Poll, Poll modal with gold theme
│       │   └── DailyPrompt.js  # SWR cached + retry on stale prompt_id
│       └── pages/
│           ├── HivePage.js     # 7 filter pills incl. "Polls 📊"
│           └── ProfilePage.js  # Fetches values for any user
```

## Key API Endpoints
- `POST /api/composer/poll` — Create poll (question, options[2-6])
- `POST /api/polls/{post_id}/vote` — Cast vote (option_index), returns results
- `GET /api/feed` — Includes POLL posts with poll_question/options/results/user_vote
- `GET /api/valuation/record-values/{username}` — Public median values
- `POST /api/prompts/buzz-in` — Daily prompt answer

## DB Collections
- `poll_votes` — {id, post_id, user_id, option_index, created_at}
- `posts` — POLL type: {poll_question, poll_options: string[]}

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
- New Music Friday dynamic editing

### Refactoring
- Break down monolithic server.py into route modules
- Split PostCards.js into type-specific card components

## Known Issues
- Discogs CDN returns 503 for some album images (external)
- Web scraper needs rotating User-Agents
