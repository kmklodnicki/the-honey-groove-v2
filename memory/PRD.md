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
- **Polls** — 6th composition type with blind voting, Honey Gold branding, persistence, Creator View
- Admin panel with temp password, user management, beta invites, reports
- Threaded comment replies, follow/unfollow with optimistic UI
- Password reset (dynamic URL), record data hydration for ghost records
- Global price cache visible to all profile viewers

## Key Credentials
- Admin: `kmklodnicki@gmail.com` / `HoneyGroove2026!`

## Completed Work

### Session 4 (Mar 14, 2026) — P0 UI/UX Fixes & Deployment Readiness
- **Composer Bar Layout Fix:** Verified 3-column grid on desktop, 2-column on mobile. All 6 chips render without truncation.
- **Poll Creator View (Complete):** Backend `GET /api/polls/{post_id}/results` + frontend "See Results"/"Back to vote" buttons for poll creators who haven't voted. Tested end-to-end.
- **Feed Filter Dropdown:** Unified dropdown for all viewports with Honey Gold styling. Left-aligned on desktop (1024px+), centered on mobile.
- **Now Spinning Modal Mobile:** Responsive layout with sticky footer, scrollable content.
- **Hardcoded URL Fix:** Removed hardcoded preview URL from backend CORS origins. Dynamic CORS via `FRONTEND_URL` env var.
- **Haul Modal Restructure:** Records search moved to top (primary), location field below marked optional with 📍 emoji, prominent album art on selection.
- **Composer Chip Styling:** Added `white-space: nowrap` to labels, reduced horizontal padding, icon-text center alignment.
- **Now Spinning Emoji:** Updated to 🎵 across composer chip, modal title, feed filter, and PostTypeBadge.
- **Login Loading Text:** Changed "Warming up the hive..." to "Warming up the honey..."
- **Haul Post Display:** Store name now shows with 📍 prefix instead of "Found at".
- **Mini Groove Hidden:** "See what the Hive said yesterday" button and PromptArchiveDrawer hidden with `{false && ...}` — underlying logic and DB queries retained.
- **Composer Width Sync:** Removed hardcoded `maxWidth: 600px`. Composer now fills same `max-w-2xl` container as post cards (640px on desktop). Matched `shadow` class and `border-honey/30` for visual consistency.
- **Mobile Filter Dropdown:** Fixed width to 280px / max 80vw, centered text with `justify-center`, centered menu on screen, increased padding to `py-2.5` for thumb-friendly tapping.
- **Filter Dropdown Emoji-First:** Emoji moved to left of text labels (🍯 All, 🎵 Now Spinning, etc.), 8px gap, checkmark on far right. Subtle honey-gold dividers between items (not after last).
- **Now Spinning SVG Icon:** Replaced emoji with lucide-react `Music` SVG icon in dark honey (#78350F), matching stroke weight of other composer icons. Modal title also uses SVG.
- **Collection Buttons Mobile:** Changed from vertical stack to horizontal `flex-row` with condensed labels on mobile (Dupes, Fix), uniform h-9 height, no horizontal overflow.

### Session 3 (Mar 14, 2026) — Polls Feature
- **Full Poll Implementation:** Backend (PollCreate model, `POST /composer/poll`, `POST /polls/{post_id}/vote`, poll_votes collection, per-option results in build_post_response) + Frontend (PollCard with blind voting UX, Poll composer in ComposerBar with dynamic options min 2/max 6, 500 char limit)
- **Honey Gold Branding (#DAA520):** Gold progress bars with slide animation, gold circle checkmark for "My Vote" indicator
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
│   ├── server.py          # Main app, CORS, middleware
│   ├── routes/
│   │   ├── hive.py        # Feed, posts, ghost record hydration, POLL composer + vote + results
│   │   ├── daily_prompts.py
│   │   ├── valuation.py   # /record-values/{username} public endpoint
│   │   └── collection.py
│   ├── models.py
│   └── database.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── PostCards.js    # PollCard (blind voting, gold bars, creator view)
│       │   ├── ComposerBar.js  # 6 chips incl. Poll, grid layout
│       │   └── DailyPrompt.js
│       ├── pages/
│       │   ├── HivePage.js     # Feed filter dropdown
│       │   └── ProfilePage.js
│       └── utils/
│           └── apiBase.js      # Uses process.env.REACT_APP_BACKEND_URL
```

## Key API Endpoints
- `POST /api/composer/poll` — Create poll (question, options[2-6])
- `POST /api/polls/{post_id}/vote` — Cast vote (option_index), returns results
- `GET /api/polls/{post_id}/results` — Poll results without voting (creator view)
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
- Split PostCards.js into type-specific card components
- Break down remaining monolithic files

## Known Issues
- Discogs CDN returns 503 for some album images (external)
- Web scraper needs rotating User-Agents
- Feed filter `post_type` param not strictly filtering on backend (frontend handles it)
