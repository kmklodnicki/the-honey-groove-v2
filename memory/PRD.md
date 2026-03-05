# HoneyGroove PRD

## Original Problem Statement
Build HoneyGroove - a social platform for vinyl collectors where users track their records, log spins, share hauls, and follow friends. The branding should feel warm, cozy, and music-focused with honey-inspired aesthetics.

## User Personas
1. **Casual Collector** - Wants to track their vinyl collection and share with friends
2. **Serious Collector** - Needs detailed tracking, notes, and weekly listening stats
3. **Social Collector** - Focused on following others and discovering new music through the community

## Core Requirements (Static)
- User authentication (email/password with username)
- Vinyl collection tracking with Discogs API integration
- Spin logging for listening history
- Hauls for batch record additions
- Friends/Following system
- Activity feed ("The Hive")
- Trending records ("Buzzing Now")
- Weekly summary ("HoneyGroove Weekly")
- Shareable PNG graphics for social media

## What's Been Implemented ✅
**Date: Jan 2026**

### Backend (FastAPI + MongoDB)
- User auth (register, login, profile update)
- Discogs API integration for record search and cover art
- Records CRUD with spin count tracking
- Spins logging system
- Hauls creation (batch record additions)
- Following/followers system
- Activity feed (posts, likes, comments)
- Weekly summary generation
- PNG share image generation (Now Spinning, Hauls, Weekly Summary)
- File upload support

### Frontend (React + shadcn/ui + Tailwind)
- Landing page with HoneyGroove branding
- Auth pages (Login, Signup)
- The Hive (activity feed)
- Explore page with Latest and Buzzing Now tabs
- Collection page with search and Spin Now
- Add Record page with Discogs search
- Profile page with stats and weekly summary
- Record detail page with share option
- Create Haul page
- Settings page
- Responsive navigation with mobile bottom nav

### Design System
- Honey color palette (#F4B942, #F9D776, #FFF6E6, #D98C2F, #1F1F1F)
- DM Serif Display for headings, Inter for UI
- Honeycomb patterns and bee motifs
- Warm, cozy aesthetic

## Prioritized Backlog

### P0 (Critical) - Done ✅
- User registration/login
- Add records from Discogs
- View collection
- Log spins
- Activity feed

### P1 (Important)
- Story format (1080x1920) share graphics
- Improved image generation with actual cover art
- Comments UI in feed
- Search users feature
- Profile followers/following list

### P2 (Nice to Have)
- Push notifications
- Record price tracking
- Wishlist feature
- Collection value estimation
- Advanced search filters (by year, format, genre)
- Record condition tracking
- Dark mode

## Next Tasks
1. Add story format (1080x1920) share graphics
2. Implement comments UI in feed posts
3. Add user search in navbar
4. Improve share graphics with actual album art
5. Add haul creation link to navigation
