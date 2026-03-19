import React from 'react';
import ShareCardBase, { BRAND } from './ShareCardBase';

/**
 * ReferralCard — share card for referral invites.
 *
 * Props:
 *   referralCode  — e.g. "KATIE-HIVE"
 *   user          — user object
 */
const ReferralCard = React.forwardRef(function ReferralCard({ referralCode, user }, ref) {
  const bg = 'linear-gradient(160deg, #FFF8DC 0%, #FFE87A 35%, #F0B429 65%, #C8861A 100%)';

  // Honeycomb hex pattern
  const hexPattern = `
    <svg xmlns='http://www.w3.org/2000/svg' width='120' height='104' viewBox='0 0 120 104'>
      <polygon points='30,2 90,2 120,52 90,102 30,102 0,52' fill='none' stroke='rgba(255,255,255,0.12)' stroke-width='2'/>
      <polygon points='90,2 150,2 180,52 150,102 90,102 60,52' fill='none' stroke='rgba(255,255,255,0.12)' stroke-width='2'/>
      <polygon points='30,54 90,54 120,104 90,154 30,154 0,104' fill='none' stroke='rgba(255,255,255,0.12)' stroke-width='2'/>
    </svg>
  `;
  const hexDataUrl = `data:image/svg+xml;base64,${btoa(hexPattern)}`;

  return (
    <div
      ref={ref}
      style={{
        display: 'none',
        width: 1080,
        height: 1920,
        background: bg,
        flexDirection: 'column',
        fontFamily: "'DM Serif Display', Georgia, serif",
        overflow: 'hidden',
        position: 'fixed',
        left: '-9999px',
        top: 0,
      }}
    >
      {/* Hex pattern */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url("${hexDataUrl}")`,
          backgroundSize: '120px 104px',
          opacity: 0.7,
          pointerEvents: 'none',
        }}
      />

      {/* Header */}
      <div style={{ height: 120, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', padding: '0 60px 24px', flexShrink: 0, position: 'relative', zIndex: 1 }}>
        <img src="/logo-wordmark-clean.png" alt="The Honey Groove" crossOrigin="anonymous" style={{ height: 80, objectFit: 'contain', opacity: 0.95 }} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 80px', position: 'relative', zIndex: 1 }}>
        <div style={{ flex: 1, minHeight: 0 }} />

        {/* Bee icon */}
        <div style={{ fontSize: 120, lineHeight: 1 }}>🐝</div>

        {/* Headline */}
        <p
          style={{
            fontFamily: "'DM Serif Display', Georgia, serif",
            fontSize: 76,
            fontWeight: 700,
            color: '#5A2800',
            textAlign: 'center',
            lineHeight: 1.15,
            margin: '24px 0 0',
          }}
        >
          Join me on The Honey Groove
        </p>

        {/* Sub-tagline */}
        <p
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: 30,
            fontStyle: 'italic',
            color: '#7A4A18',
            textAlign: 'center',
            margin: '20px 0 0',
            opacity: 0.9,
          }}
        >
          The social marketplace for vinyl collectors
        </p>

        {/* Referral code pill */}
        {referralCode && (
          <div
            style={{
              background: 'rgba(255,255,255,0.45)',
              border: '2.5px solid rgba(90,40,0,0.25)',
              borderRadius: 20,
              padding: '28px 56px',
              textAlign: 'center',
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
              marginTop: 28,
            }}
          >
            <p
              style={{
                fontFamily: 'Georgia, serif',
                fontSize: 22,
                color: '#7A4A18',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                margin: '0 0 12px',
              }}
            >
              Use my code
            </p>
            <p
              style={{
                fontFamily: "'DM Serif Display', Georgia, serif",
                fontSize: 72,
                fontWeight: 700,
                color: '#5A2800',
                margin: 0,
                letterSpacing: '0.06em',
              }}
            >
              {referralCode}
            </p>
          </div>
        )}

        {/* URL */}
        <p
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: 28,
            color: '#5A2800',
            fontWeight: 600,
            margin: '24px 0 0',
          }}
        >
          thehoneygroove.com
        </p>
        <div style={{ flex: 1, minHeight: 0 }} />
      </div>

      {/* User zone */}
      {user && (
        <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20, padding: '0 60px', flexShrink: 0, position: 'relative', zIndex: 1 }}>
          <div style={{ width: 80, height: 80, borderRadius: '50%', overflow: 'hidden', border: '3px solid rgba(90,40,0,0.3)', background: '#FAF0DC', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            {user.avatar_url ? (
              <img src={user.avatar_url} alt="" crossOrigin="anonymous" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <span style={{ fontFamily: 'Georgia, serif', fontSize: 32, fontWeight: 700, color: '#C8861A' }}>{(user.username || '?')[0].toUpperCase()}</span>
            )}
          </div>
          <span style={{ fontFamily: 'Georgia, serif', fontSize: 28, fontWeight: 700, color: '#5A2800' }}>@{user.username}</span>
        </div>
      )}

      {/* Footer */}
      <div style={{ height: 200, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', gap: 6, padding: '0 60px 48px', flexShrink: 0, position: 'relative', zIndex: 1 }}>
        <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 30, fontWeight: 700, color: '#5A2800', margin: 0 }}>The Honey Groove</p>
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 22, color: '#7A4A18', margin: 0, opacity: 0.8 }}>@thehoneygroove · thehoneygroove.com</p>
      </div>
    </div>
  );
});

ReferralCard.displayName = 'ReferralCard';
export default ReferralCard;
