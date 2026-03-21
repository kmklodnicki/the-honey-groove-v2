import React from 'react';
import { resolveImageUrl } from '../../utils/imageUrl';

/* ─── Card dimensions (px) ─── */
export const CARD_W = 1080;
export const CARD_H = 1920;
export const HEADER_H = 160; // logo zone height

/* ─── Design system color tokens ─── */
export const COLORS = {
  GOLD: '#D4A828',
  GOLD_LIGHT: '#E8CA5A',
  GOLD_PALE: '#F0E6C8',
  NAVY: '#1E2A3A',
  SLATE: '#3A4D63',
  CREAM: '#FFFBF2',
  CREAM_DARK: '#F3EBE0',
  PEWTER: '#7A8694',
  BORDER: '#E5DBC8',
};

/* ─── Legacy BRAND alias (kept for cards that import it) ─── */
export const BRAND = {
  amber: COLORS.GOLD,
  amberDark: '#8A5A0A',
  warmBrown: COLORS.SLATE,
  cream: COLORS.CREAM,
  dark: COLORS.NAVY,
  gold: COLORS.GOLD_LIGHT,
};

/**
 * HoneycombPattern — inline SVG honeycomb grid used as a subtle background texture.
 * Rendered as an inline SVG to avoid CSS data:image SecurityErrors on iOS Safari canvas.
 */
function HoneycombPattern() {
  const hexW = 120;
  const hexH = 104;
  const cols = 10;
  const rows = 20;
  const tiles = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const x = c * hexW + (r % 2 === 0 ? 0 : hexW / 2);
      const y = r * hexH * 0.75;
      tiles.push(
        <polygon
          key={`${r}-${c}`}
          points={`${x + 30},${y} ${x + 90},${y} ${x + 120},${y + 52} ${x + 90},${y + 104} ${x + 30},${y + 104} ${x},${y + 52}`}
          fill="none"
          stroke="rgba(212,168,40,0.18)"
          strokeWidth="1.5"
        />
      );
    }
  }
  return (
    <svg
      width={CARD_W}
      height={CARD_H}
      style={{ position: 'absolute', top: 0, left: 0, opacity: 0.08, pointerEvents: 'none', zIndex: 0 }}
    >
      {tiles}
    </svg>
  );
}

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
        zIndex: 1,
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: 1.1 }}>
        <span
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: 36,
            fontStyle: 'italic',
            fontWeight: 400,
            color: COLORS.GOLD,
            letterSpacing: '0.04em',
          }}
        >
          the
        </span>
        <span
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: 72,
            fontWeight: 700,
            color: COLORS.NAVY,
            letterSpacing: '0.02em',
          }}
        >
          HoneyGroove
        </span>
      </div>
    </div>
  );
}

/**
 * ShareCardUser — avatar + @username + Gold badge.
 * Used inside the navy footer zone.
 */
export function ShareCardUser({ user, textColor = '#FFFFFF' }) {
  if (!user) return null;

  const isGold = user.golden_hive || user.golden_hive_verified;
  const avatarUrl = user.avatar_url ? resolveImageUrl(user.avatar_url) : null;
  const initial = (user.username || '?')[0].toUpperCase();

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
      {/* Avatar — gold gradient circle */}
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          overflow: 'hidden',
          background: 'linear-gradient(135deg, #D4A828 0%, #E8CA5A 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          border: '2px solid rgba(232,202,90,0.4)',
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
          <span style={{ fontFamily: 'Georgia, serif', fontSize: 30, fontWeight: 700, color: COLORS.NAVY }}>
            {initial}
          </span>
        )}
      </div>

      {/* Username + badge */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <span
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: 28,
            fontWeight: 700,
            color: '#FFFFFF',
            letterSpacing: '0.01em',
          }}
        >
          @{user.username}
        </span>
        {isGold && (
          <span
            style={{
              fontFamily: 'Georgia, serif',
              fontSize: 20,
              color: COLORS.GOLD,
              background: 'rgba(212,168,40,0.2)',
              borderRadius: 20,
              padding: '3px 14px',
              fontWeight: 600,
              display: 'inline-block',
              lineHeight: '1.6',
              alignSelf: 'flex-start',
            }}
          >
            Gold Collector
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * ShareCardFooter — "the HoneyGroove" wordmark + handle.
 */
export function ShareCardFooter({ textColor = COLORS.GOLD, subColor = COLORS.SLATE }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 6,
      }}
    >
      {/* Wordmark: "the" gold italic + "Honey" white bold + "Groove" gold bold */}
      <p style={{ margin: 0, fontFamily: "'Playfair Display', Georgia, serif", fontSize: 34, letterSpacing: '0.03em' }}>
        <span style={{ fontStyle: 'italic', fontWeight: 400, color: COLORS.GOLD_LIGHT }}> the </span>
        <span style={{ fontWeight: 700, color: '#FFFFFF' }}>Honey</span>
        <span style={{ fontWeight: 700, color: COLORS.GOLD }}>Groove</span>
      </p>
      <p
        style={{
          fontFamily: 'Georgia, serif',
          fontSize: 22,
          color: COLORS.SLATE,
          margin: 0,
          opacity: 0.9,
          letterSpacing: '0.02em',
        }}
      >
        @thehoneygroove
      </p>
    </div>
  );
}

/**
 * ShareCardBase — outer wrapper. Every card using this component gets:
 *   - ZONE 1: Logo pinned to top (absolute, top 0, height HEADER_H)
 *   - ZONE 2: Content centered in the middle (absolute, top HEADER_H → bottom footerHeight)
 *   - ZONE 3: Navy footer pinned to bottom (absolute, height footerHeight)
 *
 * Props:
 *   bg               — CSS background value
 *   user             — user object for attribution
 *   isGold           — boolean, shows Gold Collector badge
 *   footerHeight     — bottom zone height in px (default 340)
 *   footerTextColor  — optional color override for footer branding (legacy compat)
 *   footerSubColor   — optional sub-color override for footer handle (legacy compat)
 *   userTextColor    — optional color override for @username text (legacy compat)
 *   children         — card-specific content
 */
const ShareCardBase = React.forwardRef(function ShareCardBase(
  { bg, user, isGold, children, footerHeight = 340, footerTextColor, footerSubColor, userTextColor },
  ref
) {
  return (
    <div
      ref={ref}
      style={{
        position: 'fixed',
        width: CARD_W,
        height: CARD_H,
        background: bg || COLORS.CREAM,
        left: '-9999px',
        top: 0,
        zIndex: -9999,
        fontFamily: "'Playfair Display', Georgia, serif",
        overflow: 'hidden',
      }}
    >
      {/* Honeycomb background pattern at 8% opacity */}
      <HoneycombPattern />

      {/* ZONE 1 — Logo: position absolute, top 0, centered */}
      <div
        style={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: HEADER_H,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1,
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: 1.1 }}>
          <span
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: 36,
              fontStyle: 'italic',
              fontWeight: 400,
              color: COLORS.GOLD,
              letterSpacing: '0.04em',
            }}
          >
            the
          </span>
          <span
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: 72,
              fontWeight: 700,
              color: COLORS.NAVY,
              letterSpacing: '0.02em',
            }}
          >
            HoneyGroove
          </span>
        </div>
      </div>

      {/* ZONE 2 — Content: absolute, top HEADER_H, bottom footerHeight */}
      <div
        style={{
          position: 'absolute',
          top: HEADER_H,
          bottom: footerHeight,
          left: 0,
          right: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 20px',
          zIndex: 1,
        }}
      >
        {children}
      </div>

      {/* ZONE 3 — Footer: navy bar pinned to bottom */}
      <div
        style={{
          position: 'absolute',
          bottom: 0, left: 0, right: 0,
          height: footerHeight,
          background: COLORS.NAVY,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 18,
          zIndex: 1,
        }}
      >
        {/* Row 1: avatar + username + gold badge */}
        {user && (
          <ShareCardUser user={user} textColor={userTextColor || '#FFFFFF'} />
        )}
        {/* Row 2+3: wordmark + handle */}
        <ShareCardFooter textColor={footerTextColor} subColor={footerSubColor} />
      </div>
    </div>
  );
});

ShareCardBase.displayName = 'ShareCardBase';
export default ShareCardBase;
