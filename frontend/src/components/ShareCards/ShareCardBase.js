import React from 'react';
import { resolveImageUrl } from '../../utils/imageUrl';

/* ─── Card dimensions (px) ─── */
export const CARD_W = 1080;
export const CARD_H = 1920;
export const HEADER_H = 280; // logo zone height — must clear Instagram Stories UI bar

/* ─── Brand tokens ─── */
export const BRAND = {
  amber: '#D4A828',
  amberDark: '#8A5A0A',
  warmBrown: '#3A4D63',
  cream: '#FFF8EE',
  dark: '#1E2A3A',
  gold: '#F0B429',
};

/**
 * ShareCardHeader — exported for standalone cards that manage their own layout.
 */
export function ShareCardHeader() {
  return (
    <div
      style={{
        position: 'absolute',
        top: 0, left: 0, right: 0,
        height: HEADER_H,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        paddingTop: 160,
      }}
    >
      <img
        src="/logo-wordmark-clean.png"
        alt="The Honey Groove"
        crossOrigin="anonymous"
        style={{ height: 92, objectFit: 'contain', opacity: 0.92 }}
      />
    </div>
  );
}

/**
 * ShareCardUser — avatar + @username + Gold/Verified badges.
 * Natural height (no fixed height) so it fits inside the 260px footer zone.
 */
export function ShareCardUser({ user, textColor = BRAND.dark }) {
  if (!user) return null;

  const isGold = user.golden_hive || user.golden_hive_verified;
  const isVerified = user.is_verified || user.verified;
  const avatarUrl = user.avatar_url ? resolveImageUrl(user.avatar_url) : null;
  const initial = (user.username || '?')[0].toUpperCase();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 10,
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 96,
          height: 96,
          borderRadius: '50%',
          overflow: 'hidden',
          border: '3px solid rgba(200,134,26,0.4)',
          background: '#FAF0DC',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt=""
            crossOrigin="anonymous"
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <span style={{ fontFamily: 'Georgia, serif', fontSize: 36, fontWeight: 700, color: BRAND.amber }}>
            {initial}
          </span>
        )}
      </div>

      {/* Username */}
      <span
        style={{
          fontFamily: 'Georgia, serif',
          fontSize: 28,
          fontWeight: 700,
          color: textColor,
          letterSpacing: '0.01em',
        }}
      >
        @{user.username}
      </span>

      {/* Badges row — always rendered so DOM coords are stable regardless of hydration timing.
          opacity:0 hides from html2canvas; data-canvas-active tells the canvas overdraw
          whether to actually draw the badge. */}
      <div style={{ display: 'flex', gap: 10 }}>
        <span
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: 18,
            color: BRAND.amber,
            background: 'rgba(200,134,26,0.12)',
            borderRadius: 20,
            padding: '4px 12px',
            fontWeight: 600,
            display: 'inline-block',
            lineHeight: '1.6',
            opacity: 0,
          }}
          data-canvas-pill="gold-member"
          data-canvas-active={isGold ? 'true' : 'false'}
        >
          🏅 Gold Member
        </span>
        <span
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: 18,
            color: '#2563EB',
            background: 'rgba(37,99,235,0.08)',
            borderRadius: 20,
            padding: '4px 12px',
            fontWeight: 600,
            display: 'inline-block',
            lineHeight: '1.6',
            opacity: 0,
          }}
          data-canvas-pill="verified"
          data-canvas-active={isVerified ? 'true' : 'false'}
        >
          ✓ Verified
        </span>
      </div>
    </div>
  );
}

/**
 * ShareCardFooter — "The Honey Groove" wordmark + handle.
 * Natural height (no fixed height).
 */
export function ShareCardFooter({ textColor = BRAND.amber, subColor = BRAND.warmBrown }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 6,
        padding: '0 60px',
      }}
    >
      <p
        style={{
          fontFamily: "'DM Serif Display', Georgia, serif",
          fontSize: 30,
          fontWeight: 700,
          color: textColor,
          margin: 0,
          letterSpacing: '0.04em',
        }}
      >
        The Honey Groove
      </p>
      <p
        style={{
          fontFamily: 'Georgia, serif',
          fontSize: 22,
          color: subColor,
          margin: 0,
          opacity: 0.85,
        }}
      >
        @thehoneygroove · thehoneygroove.com
      </p>
    </div>
  );
}

/**
 * ShareCardBase — outer wrapper. Every card using this component gets:
 *   - Logo pinned to top (140px)
 *   - Content centered in the middle zone (top 140 → bottom footerHeight)
 *   - User attribution + THG branding pinned to bottom (footerHeight, default 260px)
 *
 * Props:
 *   cardRef          — React ref (via React.forwardRef)
 *   bg               — CSS background value
 *   user             — user object for attribution
 *   footerHeight     — bottom zone height in px (default 260; use 200 for content-heavy cards)
 *   footerTextColor  — optional color override for footer branding
 *   footerSubColor   — optional sub-color override for footer handle
 *   userTextColor    — optional color override for @username text
 *   children         — card-specific content (no spacers needed)
 */
const ShareCardBase = React.forwardRef(function ShareCardBase(
  { bg, user, children, footerHeight = 340, footerTextColor, footerSubColor, userTextColor },
  ref
) {
  return (
    <div
      ref={ref}
      style={{
        display: 'flex',
        width: CARD_W,
        height: CARD_H,
        background: bg || BRAND.cream,
        position: 'fixed',
        left: '-9999px',
        top: 0,
        zIndex: -9999,
        fontFamily: "'DM Serif Display', Georgia, serif",
        overflow: 'hidden',
      }}
    >
      {/* LOGO: pinned top (0–280px) — must clear Instagram Stories UI bar */}
      <div
        style={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: HEADER_H,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          paddingTop: 160,
        }}
      >
        <img
          src="/logo-wordmark-clean.png"
          alt="The Honey Groove"
          crossOrigin="anonymous"
          style={{ height: 92, objectFit: 'contain', opacity: 0.92 }}
        />
      </div>

      {/* CONTENT: centered middle zone (280px → footerHeight from bottom) */}
      <div
        style={{
          position: 'absolute',
          top: HEADER_H,
          bottom: footerHeight,
          left: 0, right: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 80px',
        }}
      >
        {children}
      </div>

      {/* FOOTER: pinned bottom — user attribution + THG branding */}
      <div
        style={{
          position: 'absolute',
          bottom: 0, left: 0, right: 0,
          height: footerHeight,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
        }}
      >
        <ShareCardUser user={user} textColor={userTextColor} />
        <ShareCardFooter textColor={footerTextColor} subColor={footerSubColor} />
      </div>
    </div>
  );
});

ShareCardBase.displayName = 'ShareCardBase';
export default ShareCardBase;
