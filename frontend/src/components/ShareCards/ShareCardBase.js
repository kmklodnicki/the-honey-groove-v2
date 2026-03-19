import React from 'react';
import { resolveImageUrl } from '../../utils/imageUrl';

/* ─── Universal zone heights (px, card is 1080×1920) ─── */
export const CARD_W = 1080;
export const CARD_H = 1920;
const HEADER_H = 120;
const USER_H = 180;
const FOOTER_H = 200;

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
 * ShareCardHeader — THG wordmark, top zone (~120px).
 */
export function ShareCardHeader({ tint = BRAND.amber }) {
  return (
    <div
      style={{
        height: HEADER_H,
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        padding: '0 60px 24px',
        flexShrink: 0,
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
 */
export function ShareCardUser({ user, textColor = BRAND.dark }) {
  if (!user) return <div style={{ height: USER_H, flexShrink: 0 }} />;

  const isGold = user.golden_hive || user.golden_hive_verified;
  const isVerified = user.is_verified || user.verified;
  const avatarUrl = user.avatar_url ? resolveImageUrl(user.avatar_url) : null;
  const initial = (user.username || '?')[0].toUpperCase();

  return (
    <div
      style={{
        height: USER_H,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 20,
        padding: '0 60px',
        flexShrink: 0,
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
                padding: '2px 12px',
                fontWeight: 600,
              }}
            >
              🍯 Gold Member
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
                padding: '2px 12px',
                fontWeight: 600,
              }}
            >
              ✓ Verified
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * ShareCardFooter — "The Honey Groove" wordmark + handle.
 */
export function ShareCardFooter({ textColor = BRAND.amber, subColor = BRAND.warmBrown }) {
  return (
    <div
      style={{
        height: FOOTER_H,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: 6,
        padding: '0 60px 48px',
        flexShrink: 0,
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
 * ShareCardBase — outer wrapper. Every card uses this.
 *
 * Props:
 *   cardRef     — React ref from useShareCard, attached to the outer div
 *   bg          — CSS background value (gradient string or color)
 *   user        — user object for the user attribution zone
 *   textColor   — optional override for user/footer text
 *   children    — the card-specific content area
 */
const ShareCardBase = React.forwardRef(function ShareCardBase(
  { bg, user, children, headerTint, footerTextColor, footerSubColor, userTextColor },
  ref
) {
  return (
    <div
      ref={ref}
      style={{
        display: 'none', // shown only during capture
        width: CARD_W,
        height: CARD_H,
        background: bg || BRAND.cream,
        flexDirection: 'column',
        fontFamily: "'DM Serif Display', Georgia, serif",
        overflow: 'hidden',
        position: 'fixed',
        left: '-9999px',
        top: 0,
      }}
    >
      <ShareCardHeader tint={headerTint} />

      {/* Content zone — explicit height so spacers inside children compute reliably */}
      <div
        style={{
          height: CARD_H - HEADER_H - USER_H - FOOTER_H,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'stretch',
          overflow: 'hidden',
        }}
      >
        {children}
      </div>

      <ShareCardUser user={user} textColor={userTextColor} />
      <ShareCardFooter textColor={footerTextColor} subColor={footerSubColor} />
    </div>
  );
});

ShareCardBase.displayName = 'ShareCardBase';
export default ShareCardBase;
