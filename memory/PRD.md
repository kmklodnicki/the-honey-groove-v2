# HoneyGroove PRD

## Problem Statement
A social platform for vinyl collectors called **The HoneyGroove** — the vinyl social club. Users track their collection, log spins, share activity, import from Discogs, hunt for records (ISO), follow friends, trade vinyl, and interact through a rich social feed.

## Branding
- Colors: Honey #F4B942, Honey Soft #F9D776, Cream #FFF6E6, Amber #D98C2F, Vinyl Black #1F1F1F
- Fonts: DM Serif Display (headings), Inter (body)

## Core Pages
1. **Landing Page** — Hero ("the vinyl social club, finally."), Features ("built for the obsessed."), CTA, Footer
2. **The Hive** — Social feed with composer bar (Now Spinning, New Haul, ISO, Vinyl Mood)
3. **Explore** — Discovery page with Feed/People tabs
4. **Collection** — Personal vinyl library with sorting + Discogs import + Add Record
5. **ISO & Market** — Vinyl wish list, peer-to-peer marketplace with required photos, Stripe payments
6. **My Trades** — Full trade management (Active/History tabs, detail modal)
7. **Profile** — 4 tabs: Collection, ISO, Spinning, Trades + Stripe Connect status
8. **Admin Disputes** — Admin-only dispute review dashboard with resolve modal

## Implemented Features
1-14: Auth, Collection, Discogs Import, Feed, Composer, Post Cards, Comments/Likes, Shareable Graphics, Sorting, Profile Photos, ISO Page, Profile Tabs, Following System, Explore
15. **Vinyl Mood Overhaul** — 12 moods with emojis, dynamic backgrounds, animated selection
16. **Marketplace Photo Upload** — 1-10 required photos with gallery carousel
17. **Trade System (Complete)** — Propose/Counter/Accept/Decline, shipping, confirmation, disputes, ratings
18. **Stripe Connect Onboarding** — Seller onboarding via Stripe Connect Express
19. **In-App Notifications** — Notification bell with dropdown, unread count, mark-all-read
20. **Landing Page Redesign** — Updated hero, features (6 cards), CTA, footer (© 2026)
21. **Stripe Payment Execution** — Buy Now & Make Offer checkout flow with return handling
22. **Admin Dispute Dashboard** — Full UI with Open/Resolved tabs, dispute cards, resolve modal
23. **Browser Push Notifications** — Desktop notifications via Notification API for real-time alerts

## Trade Status Machine
```
PROPOSED → (Counter) → COUNTERED → (Accept/Decline)
PROPOSED/COUNTERED → ACCEPTED → SHIPPING (5-day deadline)
SHIPPING → CONFIRMING (both ship, 48h deadline) → COMPLETED (both confirm, records transfer)
SHIPPING/CONFIRMING → DISPUTED → Admin resolves (COMPLETED/CANCELLED/PARTIAL)
COMPLETED → Mandatory rating before next trade
```

## Upcoming (User's Roadmap)
- **P2: Explore Enhancements** — Trending records, active ISO listings
- **P2: Hauls Feature** — Dedicated hauls page
- **P2: HoneyGroove Weekly** — Weekly summary aggregation + display
- **P2: Monetization** — Pro membership, 4% transaction fee, Verified Seller badge
- **P2: Backend Refactor** — Split monolithic server.py into /routes, /models, /services

## Data Model
```
users, posts, records, spins, hauls, iso_items,
listings (photo_urls[]),
likes, comments, followers,
trades, trade_messages, trade_shippings, trade_disputes, trade_ratings,
notifications, payment_transactions
```

## Test Credentials
- Admin: demo@example.com / password123 (is_admin: true)
