# The HoneyGroove — Product Requirements Document

## Overview
A premium social platform for vinyl collectors. React frontend + FastAPI backend + MongoDB.

## Production URLs
- **Live site**: thehoneygroove.com
- **Production API**: wax-collector-app.emergent.host
- **Production DB**: `groove-social-beta-test_database` (MongoDB Atlas)

## Completed — March 13, 2026
- **P0 FIXED**: Admin prompts sorted descending (newest first)
- **P0 FIXED**: Honeypot page bottom padding pb-32 for bottom nav clearance
- **P0 FIXED**: FRONTEND_URL hard-coded to `https://www.thehoneygroove.com`
- **P0 FIXED**: Sticky top banner hierarchy — PWA banner (z:101) above nav (z:100) via CSS var
- **P0 FIXED**: Invite redemption — case-insensitive token lookup, read-only validation, `POST /api/auth/resend-invite`, "Send me a fresh invite link" fallback on BOTH error pages (ClaimInvitePage + JoinPage)
- **P0 FIXED**: Email CTA updated to "Join Now" for new users
- **P0 FIXED**: Detailed backend logging for invite token errors (`INVITE TOKEN ERROR [reason]`)
- **P0 FIXED**: Frontend console.error logging for invite token errors

## P0 — Next Priority
1. **Instagram Story Export** — Export Daily Prompt as 1080x1920 PNG
2. **CRITICAL: User must redeploy production** for all fixes to take effect

## P1 — Upcoming
- Service Worker Caching (BLOCK 321)
- Streaming Service Integration (BLOCK 254) — needs Spotify callback URL

## P2 — Future/Backlog
- Record Store Day Proxy Network
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Secret Search Feature
- Dynamic "New Music Friday" for Weekly Wax email

## Key API Endpoints (Invite Flow)
- `GET /api/auth/validate-invite?token=` — Read-only, case-insensitive, detailed logging
- `POST /api/auth/resend-invite` — `{email}` → fresh token + branded email
- `POST /api/auth/claim-invite` — `{token, password}` → burns token only on success

## Key Files
- `backend/routes/auth.py` — Auth + invite flow endpoints
- `frontend/src/pages/ClaimInvitePage.js` — UUID token claim page with error fallback
- `frontend/src/pages/JoinPage.js` — Short invite code page with error fallback
- `frontend/src/components/PWAInstallBanner.js` — PWA banner
- `frontend/src/components/Navbar.js` — Nav with banner coordination
- `backend/database.py` — FRONTEND_URL hard-coded
- `backend/scripts/send_invite_campaign.py` — Email campaign templates

## Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!
