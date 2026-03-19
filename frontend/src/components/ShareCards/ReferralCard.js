import React from 'react';
import { ShareCardHeader, ShareCardFooter, ShareCardUser, CARD_W, CARD_H } from './ShareCardBase';

const ReferralCard = React.forwardRef(function ReferralCard({ referralCode, user }, ref) {
  const bg = 'linear-gradient(160deg, #FFF8DC 0%, #FFE87A 35%, #F0B429 65%, #C8861A 100%)';

  const hexTiles = [];
  for (let r = 0; r < 20; r++) {
    for (let c = 0; c < 10; c++) {
      hexTiles.push(
        <g key={`${r}-${c}`} transform={`translate(${c * 120},${r * 104})`}>
          <polygon points='30,2 90,2 120,52 90,102 30,102 0,52' fill='none' stroke='rgba(255,255,255,0.12)' strokeWidth='2' />
          <polygon points='90,2 150,2 180,52 150,102 90,102 60,52' fill='none' stroke='rgba(255,255,255,0.12)' strokeWidth='2' />
          <polygon points='30,54 90,54 120,104 90,154 30,154 0,104' fill='none' stroke='rgba(255,255,255,0.12)' strokeWidth='2' />
        </g>
      );
    }
  }

  return (
    <div
      ref={ref}
      style={{
        display: 'flex',
        width: CARD_W,
        height: CARD_H,
        background: bg,
        position: 'fixed',
        zIndex: -9999,
        left: '-9999px',
        top: 0,
        fontFamily: "'DM Serif Display', Georgia, serif",
        overflow: 'hidden',
      }}
    >
      {/* Hex pattern — inline SVG to avoid iOS canvas SecurityError with data: URL backgrounds */}
      <svg
        width='1080'
        height='1920'
        style={{ position: 'absolute', top: 0, left: 0, opacity: 0.7, pointerEvents: 'none' }}
      >
        {hexTiles}
      </svg>

      {/* LOGO: pinned top */}
      <ShareCardHeader />

      {/* CONTENT: centered middle zone */}
      <div
        style={{
          position: 'absolute',
          top: 140,
          bottom: 260,
          left: 0, right: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 80px',
          position: 'relative',
          zIndex: 1,
        }}
      >
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
                lineHeight: 1,
                textAlign: 'center',
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
      </div>

      {/* FOOTER: pinned bottom */}
      <div
        style={{
          position: 'absolute',
          bottom: 0, left: 0, right: 0,
          height: 260,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          zIndex: 1,
        }}
      >
        <ShareCardUser user={user} textColor="#5A2800" />
        <ShareCardFooter textColor="#5A2800" subColor="#7A4A18" />
      </div>
    </div>
  );
});

ReferralCard.displayName = 'ReferralCard';
export default ReferralCard;
