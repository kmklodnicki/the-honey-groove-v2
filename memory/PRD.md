# The HoneyGroove - Product Requirements Document

## Original Problem Statement
The HoneyGroove is a vinyl record collector social platform with collection management, social feed, marketplace, and valuation features. Deployed on Vercel with Cloudinary for images.

## Tech Stack
- **Frontend**: React (CRA + Craco), TailwindCSS, Shadcn/UI
- **Backend**: FastAPI (Python), MongoDB Atlas
- **Deployment**: Vercel (production), Emergent preview (staging)
- **Integrations**: Cloudinary (images), Stripe Connect (payments), Discogs API (record metadata), Resend (emails)

## Core Features (Implemented)
- User auth, collection management, Discogs import via OAuth
- **Smart Match**: Auto-links manual album entries to Discogs (cover art, tracklist, community data)
- **Rarity System**: Grail/Ultra Rare/Very Rare/Rare/Uncommon/Common/Obscure/Unknown tiers from Discogs community have/want data. "Unknown" for records without Discogs link.
- Social feed with server-side filtering, collapsible pinned posts
- Notification preferences (all/following/none)
- Marketplace, valuation system, weekly reports, daily prompts
- Profile page: Collection, Posts, For Sale, Dream List, ISO tabs
- Collection sort: Artist, Title, Newest, Spins, Value, **Rarest First**, **Most Common**

## Recent Changes (March 2026)
- Smart Match on manual add (high-confidence Discogs auto-linking)
- Rarity badge logic: "Unknown" for no discogs_id, "Very Rare" tier added
- Collection sort by rarity (most common / rarest first)
- ISO auto-populate from Discogs (backfilled 59 of 63 ISOs)
- Collapsible pinned posts, notification preferences, password modal
- Feed server-side filtering, Profile Posts tab

## P0 Issues (Vercel Production)
1. Cloudinary uploads - "Invalid Signature" (credential config on Vercel)
2. Old image display - needs EMERGENT_LLM_KEY on Vercel

## Upcoming
- Instagram Story Export (P1), Re-enable Mini Groove (P1)
- Login pre-fetching, Service Worker caching

## Future/Backlog
- Pro memberships, Secret Search, Crown Jewels logic
- Streaming integration, Record Store Day Proxy
- Editable Weekly Wax, Safari animation
