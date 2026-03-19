import React from 'react';
import { resolveImageUrl } from '../../utils/imageUrl';

/* ─── Card dimensions (px) ─── */
export const CARD_W = 1080;
export const CARD_H = 1920;

/* ─── Brand tokens ─── */
export const BRAND = {
  amber: '#C8861A',
  amberDark: '#8A5A0A',
  warmBrown: '#8A6B4A',
  cream: '#FFF8EE',
  dark: '#2A1A06',
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
        height: 140,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        paddingTop: 60,
      }}
    >
      <img
        src="/logo-wordmark-clean.png"
        alt="The Honey Groove"
        crossOrigin="anonymous"
        style={{ height: 80, objectFit: 'contain', opacity: 0.92 }}
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
        alignItems: 'center',
        justifyContent: 'center',
        gap: 20,
        padding: '0 60px',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          overflow: 'hidden',
          border: '3px solid rgba(200,134,26,0.4)',
          flexShrink: 0,
          background: '#FAF0DC',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
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
          <span style={{ fontFamily: 'Georgia, serif', fontSize: 32, fontWeight: 700, color: BRAND.amber }}>
            {initial}
          </span>
        )}
      </div>

      {/* Username + badges */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
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
        <div style={{ display: 'flex', gap: 8 }}>
          {isGold && (
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
              }}
            >
              {/* opacity:0 — redrawn by Canvas 2D API via data-canvas-redraw */}
              <span
                style={{ opacity: 0 }}
                data-canvas-redraw="text"
                data-canvas-text="🍯 Gold Member"
                data-canvas-color={BRAND.amber}
                data-canvas-font="600 18px Georgia, serif"
              >
                🍯 Gold Member
              </span>
            </span>
          )}
          {isVerified && (
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
              }}
            >
              {/* opacity:0 — redrawn by Canvas 2D API via data-canvas-redraw */}
              <span
                style={{ opacity: 0 }}
                data-canvas-redraw="text"
                data-canvas-text="✓ Verified"
                data-canvas-color="#2563EB"
                data-canvas-font="600 18px Georgia, serif"
              >
                ✓ Verified
              </span>
            </span>
          )}
        </div>
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
  { bg, user, children, footerHeight = 260, footerTextColor, footerSubColor, userTextColor },
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
      {/* LOGO: pinned top (0–140px) */}
      <div
        style={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: 140,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          paddingTop: 60,
        }}
      >
        <img
          src="/logo-wordmark-clean.png"
          alt="The Honey Groove"
          crossOrigin="anonymous"
          style={{ height: 80, objectFit: 'contain', opacity: 0.92 }}
        />
      </div>

      {/* CONTENT: centered middle zone (140px → footerHeight from bottom) */}
      <div
        style={{
          position: 'absolute',
          top: 140,
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
