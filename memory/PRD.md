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
- Social feed with server-side filtering (Now Spinning, Hauls, ISOs, Notes, Polls)
- Collapsible pinned posts (localStorage persisted)
- Notification preferences (all/following/none) with sender_id filtering
- Marketplace (The Honeypot - listings, trades, payments)
- Valuation system (Discogs market data, community valuations)
- Weekly Wax reports, Daily Prompts, Bingo cards
- DMs, notifications, follow system, blocking
- Profile page with tabs: Collection, Posts, For Sale, Dream List, ISO
- Settings: password update modal, notification prefs, privacy controls

## Recent Changes (March 2026 - Session 2)
- Collapsible pinned post: X button, localStorage persistence, expand/collapse
- Notification preferences: User model field + backend filtering logic
- Settings: Notification card (All/Following/None radio buttons)
- Settings: Password update moved to modal, button next to email
- UnofficialPill moved to bottom-right
- Feed filters: server-side filtering with infinite scroll
- Profile Posts tab with cursor pagination

## P0 Issues (Vercel Production)
1. Cloudinary uploads - "Invalid Signature" on Vercel (credential config)
2. Old image display - needs EMERGENT_LLM_KEY on Vercel

## P1 Issues
- Notification email CTAs - needs user verification
- Instagram Story Export feature
- Re-enable "Mini Groove" feature

## P2 / Future
- Discogs API SSL resilience, Login pre-fetching
- Service Worker caching, Streaming Service integration
- Record Store Day Proxy Network, Safari loading animation
- Pro memberships / Verified Seller badge
- Secret Search Feature, Editable Weekly Wax, Crown Jewels logic
