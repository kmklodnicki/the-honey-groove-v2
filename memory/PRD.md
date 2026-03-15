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
- Social feed (Now Spinning, Hauls, ISOs, Notes, Polls)
- Marketplace (The Honeypot - listings, trades, payments)
- Valuation system (Discogs market data, community valuations)
- Weekly Wax reports, Daily Prompts, Bingo cards
- DMs, notifications, follow system, blocking

## Current Status
- **Production**: Live on thehoneygroove.com via Vercel
- **Staging**: Emergent preview environment

## P0 Issues (Critical)
1. **Cloudinary uploads** - "Invalid Signature" on Vercel (credential config issue) - Code improvements done, needs Vercel env var verification by admin
2. **Old image display** - Images from before migration may not show on Vercel if storage init fails - Code fixed to use dynamic API URL

## P1 Issues
- Notification email CTAs - needs user verification that links point to thehoneygroove.com
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
