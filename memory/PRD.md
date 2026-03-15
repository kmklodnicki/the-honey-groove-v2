# The HoneyGroove - Product Requirements Document

## Original Problem Statement
The HoneyGroove is a vinyl record collector social platform. The admin has directed the project through multiple phases of UI/UX refinement, feature implementation (Polls, Threaded Comments), and bug fixing. The application was migrated to a Vercel production deployment with Cloudinary for image storage.

## Tech Stack
- **Frontend**: React (CRA + Craco), TailwindCSS, Shadcn/UI
- **Backend**: FastAPI (Python), MongoDB Atlas
- **Deployment**: Vercel (production), Emergent preview (staging)
- **Integrations**: Cloudinary (images), Stripe Connect (payments), Discogs API (record metadata), Resend (emails)

## Core Features (Implemented)
- User auth (register/login/invite codes)
- Collection management (add/remove records, Discogs import via OAuth)
- Social feed (Now Spinning, Hauls, ISOs, Notes, Polls) with server-side filtering
- Marketplace (The Honeypot - listings, trades, payments)
- Valuation system (Discogs market data, community valuations)
- Weekly Wax reports, Daily Prompts, Bingo cards
- DMs, notifications, follow system, blocking
- Profile page with tabs: Collection, Posts, For Sale, Dream List, ISO

## Recent Changes (March 2026)
- Moved UnofficialPill overlay from top-right to bottom-right of album art
- Feed filters now use server-side filtering (post_type param) with infinite scroll
- Profile page: removed 'In Common' tab, added 'Posts' tab with full interactivity
- Note Composer: changed record selector from dropdown to search input
- Image URL proxy: made dynamic (uses app's own API URL)
- Cloudinary upload: improved error diagnostics
- PostCard component extracted to shared HivePostCard.js

## P0 Issues (Vercel Production)
1. **Cloudinary uploads** - "Invalid Signature" on Vercel (credential config issue) - Code improvements done, needs Vercel env var verification by admin
2. **Old image display** - Code fixed to use dynamic API URL; needs EMERGENT_LLM_KEY on Vercel

## P1 Issues
- Notification email CTAs - needs user verification
- Instagram Story Export feature
- Re-enable "Mini Groove" feature

## P2 / Future
- Discogs API SSL resilience
- Login pre-fetching
- Service Worker caching
- Streaming Service integration
- Record Store Day Proxy Network
- Safari loading animation
- Pro memberships / Verified Seller badge
- Secret Search Feature
- Editable "New Music Friday" in Weekly Wax
- Update Crown Jewels logic

## Key Credentials
- Admin: kmklodnicki@gmail.com
- DB: MongoDB Atlas (cluster0.abcipnu.mongodb.net)
