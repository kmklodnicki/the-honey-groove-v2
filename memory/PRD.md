# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Social platform for vinyl collectors and music lovers. Features include activity feed, user profiles with record collections, threaded comments, polls, marketplace (Honeypot), and daily engagement prompts ("Buzz In").

## Core Architecture
- **Frontend:** React + Tailwind CSS + shadcn/ui
- **Backend:** FastAPI + Socket.IO (real-time)
- **Database:** MongoDB Atlas
- **Image Storage:** Cloudinary (primary, production) with Emergent Object Storage fallback
- **Email:** Resend
- **Payments:** Stripe Connect
- **Music Data:** Discogs API

## What's Been Implemented

### P0 Sprint - Production Migration (March 2026)
- **Cloudinary Integration:** `backend/utils/cloudinary_upload.py` utility streams image buffers to Cloudinary. Upload endpoints in `routes/collection.py` and `routes/verification.py` try Cloudinary first, fallback to Emergent storage. Env vars: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
- **Global Mobile Modal Fix:** All Radix dialog components (`dialog.jsx`, `sheet.jsx`, `alert-dialog.jsx`) updated with `max-height: 85vh`, `overflow-y: auto`, responsive scaling via `modal-mobile-scale` CSS class, and `onCloseAutoFocus` scroll-lock fix.
- **Notification Deduplication:** SocketContext rewritten with proper cleanup, `processedIds` Set for dedup. Navbar `prevCountRef` starts at -1 (skips initial flood), `shownNotifIds` prevents duplicate browser notifications.
- **Broken Image Fallback:** `isLegacyUploadUrl()` in `imageUrl.js` detects old `/uploads` paths. AlbumArt and PostCards show "migration in progress" placeholder for failed legacy images.
- **Localhost Cleanup:** Removed `http://localhost:3000` from CORS origins in `server.py`. Dynamic CORS via `FRONTEND_URL` and `CORS_ORIGINS` env vars.

### Previously Completed
- Threaded comments with one-level-deep reply limit
- Comment deletion (soft-delete with placeholder)
- Global "Fetching the honey..." loading state (`LoadingHoney.jsx`)
- iOS zoom bug fix (viewport meta, 16px input fonts)
- Honey Essentials page overhaul
- Poll creator view
- Haul post composer restructure
- Filter dropdowns with emoji-first styling
- Now Spinning icon sync

## Prioritized Backlog

### P1 - Upcoming
- Instagram Story Export (Daily Prompt as 1080x1920 PNG)
- Re-enable "Mini Groove" feature
- Login pre-fetching during animation
- Crown Jewels sorting logic
- Service Worker Caching

### P2 - Future
- Streaming Service Integration (Spotify)
- Record Store Day Proxy Network
- Safari-compatible loading animation
- Pro memberships / Verified Seller badge
- Secret Search Feature
- Weekly Wax dynamic editing
- Fragile Web Scraper improvement (rotating User-Agents, backoff)

## Key Files
- `backend/server.py` - Main app entry, CORS, startup
- `backend/utils/cloudinary_upload.py` - Cloudinary upload utility
- `backend/routes/collection.py` - Upload endpoint, records, collection
- `backend/routes/verification.py` - Golden Hive verification uploads
- `frontend/src/components/ui/dialog.jsx` - Dialog with mobile fixes
- `frontend/src/context/SocketContext.js` - Socket with dedup
- `frontend/src/utils/imageUrl.js` - Image URL resolution + legacy detection
- `frontend/src/components/AlbumArt.js` - Album art with migration fallback

## Test Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!
