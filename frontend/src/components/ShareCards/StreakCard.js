import React from 'react';
import { ShareCardHeader, ShareCardFooter, ShareCardUser, CARD_W, CARD_H, HEADER_H } from './ShareCardBase';

const StreakCard = React.forwardRef(function StreakCard({ streakDays = 7, user }, ref) {
  const bg = 'linear-gradient(160deg, #FFF3DC 0%, #FFD080 35%, #FF9830 65%, #E86010 100%)';

  const embers = [
    { x: 80, y: 300, size: 20, opacity: 0.6 },
    { x: 200, y: 180, size: 14, opacity: 0.5 },
    { x: 900, y: 250, size: 18, opacity: 0.55 },
    { x: 950, y: 400, size: 12, opacity: 0.45 },
    { x: 140, y: 500, size: 16, opacity: 0.5 },
    { x: 880, y: 550, size: 22, opacity: 0.6 },
    { x: 60, y: 700, size: 14, opacity: 0.4 },
    { x: 1000, y: 350, size: 16, opacity: 0.5 },
    { x: 750, y: 200, size: 12, opacity: 0.4 },
    { x: 350, y: 150, size: 18, opacity: 0.55 },
    { x: 500, y: 280, size: 10, opacity: 0.35 },
    { x: 650, y: 420, size: 14, opacity: 0.45 },
  ];

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
      {embers.map((e, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: e.x,
            top: e.y,
            width: e.size,
            height: e.size,
            borderRadius: '50%',
            background: '#FFE566',
            opacity: e.opacity,
            boxShadow: `0 0 ${e.size * 2}px ${e.size}px rgba(255,200,50,0.4)`,
          }}
        />
      ))}

      {/* LOGO: pinned top */}
      <ShareCardHeader />

      {/* CONTENT: centered middle zone */}
      <div
        style={{
          position: 'absolute',
          top: HEADER_H,
          bottom: 260,
          left: 0, right: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 80px',
        }}
      >
        {/* Bee + flame */}
        <div style={{ fontSize: 160, lineHeight: 1 }}>🐝🔥</div>

        {/* Streak number */}
        <p
          style={{
            fontFamily: "'DM Serif Display', Georgia, serif",
            fontSize: 300,
            fontWeight: 700,
            margin: 0,
            lineHeight: 0.9,
            background: 'linear-gradient(180deg, #FFF8DC 0%, #FFD700 50%, #C8861A 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            filter: 'drop-shadow(0 4px 12px rgba(200,100,0,0.5))',
          }}
        >
          {streakDays}
        </p>

        {/* "DAY STREAK" label */}
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 72, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#7A3800', margin: 0 }}>
          Day Streak
        </p>

        {/* Flavor text */}
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 38, fontStyle: 'italic', color: '#5A2800', textAlign: 'center', margin: '20px 0 0', opacity: 0.85 }}>
          Buzz In streak on The Honey Groove
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
        }}
      >
        <ShareCardUser user={user} textColor="#5A2800" />
        <ShareCardFooter textColor="#7A3800" subColor="#5A2800" />
      </div>
    </div>
  );
});

StreakCard.displayName = 'StreakCard';
export default StreakCard;
