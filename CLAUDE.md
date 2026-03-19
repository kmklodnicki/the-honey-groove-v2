# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**The Honey Groove** is a social platform for vinyl record collectors. Users track collections, share listening sessions ("spins") and purchases ("hauls"), hunt rare pressings (ISOs — "In Search Of"), and buy/sell/trade records via a marketplace ("Honeypot").

---

## Development Commands

### Frontend (`/frontend`)
```bash
cd frontend
yarn install          # install deps
yarn start            # dev server (uses REACT_APP_BACKEND_URL env var)
yarn build            # production build → frontend/build/
yarn test             # run tests (craco/jest)
```
The frontend uses **craco** (not plain CRA) — always use `yarn start/build/test`, not `react-scripts` directly.

### Backend (`/backend`)
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001   # dev server
```
Env vars required: `MONGO_URL`, `DB_NAME`, `JWT_SECRET_KEY` (plus external service keys for Discogs, Stripe, S3, Cloudinary, Resend, Spotify, Gemini).

### Running Tests
```bash
# API integration tests (hit a live server)
python backend_test.py

# Backend unit tests
cd backend && pytest tests/

# Frontend tests
cd frontend && yarn test --watchAll=false
```

### Linting & Formatting
```bash
# Backend
cd backend && flake8 .
cd backend && black .
cd backend && isort .

# Frontend
cd frontend && npx eslint src/
```

---

## Architecture

### Request Flow

```
Browser → React (Vite/CRA via craco)
           │
           ├─ REST: REACT_APP_BACKEND_URL/api/...  → FastAPI (backend/server.py)
           │                                            ├─ routes/*.py  (25 modules)
           │                                            ├─ database.py  (MongoDB/Motor + JWT/bcrypt)
           │                                            └─ models.py    (all Pydantic schemas)
           │
           └─ WebSocket: Socket.IO  →  live_hive.py  (real-time posts/notifications)
```

All frontend API calls go through `src/utils/apiBase.js` which reads `REACT_APP_BACKEND_URL`. The `API` export (from apiBase) is the base for all fetch/axios calls; `AuthContext` attaches the JWT Bearer token.

### Backend Structure

- **`server.py`** — FastAPI app entry point; registers all 25+ routers under `/api` prefix; mounts Socket.IO via ASGI
- **`database.py`** — MongoDB connection (Motor async), JWT encode/decode, bcrypt helpers, `require_auth` FastAPI dependency, Discogs HTTP session with retry
- **`models.py`** — All Pydantic request/response schemas in one file
- **`live_hive.py`** — Socket.IO server; `emit_new_post()` broadcasts `NEW_POST` events to all clients
- **`routes/`** — One file per feature domain (hive, collection, honeypot, trades, search, dms, auth, admin, etc.)
- **`services/`** — `email_service.py` (Resend), `price_scraper.py` (Discogs market prices), `rate_limiter.py`, `content_filter.py`
- **`utils/`** — `cloudinary_upload.py`, `image_helpers.py`, `rarity.py`

### Frontend Structure

- **`src/App.js`** — Route definitions (React Router 7), lazy-loaded pages, error boundary, auth gate, `MaintenanceGate`
- **`src/context/AuthContext.js`** — JWT storage, user hydration (token-first, then API), all auth actions
- **`src/context/SocketContext.js`** — Socket.IO client initialization
- **`src/pages/`** — One file per page/route (~40 pages)
- **`src/components/`** — Shared UI components (~60+)
- **`src/utils/imageUrl.js`** — `resolveImageUrl()` — canonical function for all image src resolution (see below)
- **`src/utils/apiBase.js`** — Single source of truth for backend URL

### MongoDB Collections

`users`, `records`, `posts`, `spins`, `followers`, `listings`, `trades`, `notifications`, `conversations`, `messages`, `discogs_releases`, `spotify_links`

---

## Critical Patterns to Know

### Image URL Resolution (`resolveImageUrl`)
Always use `resolveImageUrl(src)` from `src/utils/imageUrl.js` — never use image URLs directly. The routing logic:
- **Cloudinary** (`res.cloudinary.com`) → direct (no proxy needed)
- **Discogs CDN** (`discogs.com`) → must proxy through `/api/image-proxy` (Discogs blocks hotlinking from production domain)
- **Emergent file host** / legacy `/api/files/serve/` paths → proxy through backend
- **S3** URLs → served via CloudFront CDN, used directly

### Authentication
`require_auth` is a FastAPI dependency (in `database.py`) injected into protected routes. On the frontend, the JWT is stored in localStorage via `safeStorage` and decoded client-side — no network call needed to restore session. The `_hydrated` flag on the user object indicates whether full profile data has been fetched from `/api/auth/me`.

### MongoDB Connection Pool
Pool is tuned for Atlas M0 (500 connection cap): `maxPoolSize=10, minPoolSize=1, maxIdleTimeMS=45000`. Do not increase `maxPoolSize` without checking the deployment's Atlas tier.

### Search (AND-logic)
`routes/search.py` uses `_build_and_filter()` — every query word must match at least one field. This was intentionally rewritten from OR-logic. Discogs API is used as a fallback when local DB returns no results.

### Real-time Feed Deduplication
`HivePage.js` maintains a `postsRef` to deduplicate posts arriving via both HTTP poll and Socket.IO `NEW_POST` events. Any changes to how posts are added to the feed must account for both paths.

### Post Types
Feed posts have a `post_type` field: `spin` | `haul` | `iso` | `note` | `release_note`. Each type has different display logic in `PostCards.js` and `HivePostCard.js`.

### Error Resilience
- `ErrorBoundary` (React) — wraps the whole app
- `ApiErrorGate` — intercepts 500/503 after 2 consecutive failures
- `MaintenanceGate` — polls `/api/status/maintenance` every 60s
- Discogs API calls use a retry wrapper (3 retries, exponential backoff) defined in `database.py`

---

## Design System

Defined in `design_guidelines.json`. Key tokens:
- **Fonts:** DM Serif Display (headings), Inter (body)
- **Colors:** `#FAF7F2` (cream bg), `#F6D6DE` (primary pink), `#D98FA1` (dusty rose), `#E6C98B` (champagne accent), `#1F1F1F` (black text)
- **Radius:** `0.75rem` default, `1rem` cards, `9999px` buttons
- **Icons:** `lucide-react`

All interactive elements should have `data-testid` attributes.

### HEIC/HEIF Uploads
Mobile photo uploads convert HEIC → JPEG client-side using `heic2any` with a Canvas fallback before sending to the backend.

---

## Deployment

- **Frontend:** Vercel — builds `frontend/` with `npm run build`, serves from `frontend/build/`
- **Backend:** Vercel serverless via `/api/index.py` (see `vercel.json`) — all `/api/*` requests route there
- **Database:** MongoDB Atlas M0 cluster
- **Assets:** S3 + CloudFront (images), Cloudinary (processed images)
