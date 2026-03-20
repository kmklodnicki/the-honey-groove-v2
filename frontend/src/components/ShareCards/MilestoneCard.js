import React from 'react';
import { ShareCardHeader, ShareCardFooter, ShareCardUser, CARD_W, CARD_H, HEADER_H } from './ShareCardBase';

const MilestoneCard = React.forwardRef(function MilestoneCard({ milestoneText, description, user }, ref) {
  const bg = 'linear-gradient(160deg, #FFFADC 0%, #FFE87A 35%, #F0B429 65%, #D4A828 100%)';

  const confetti = [
    { x: 60,  y: 200, color: '#FF6B6B', w: 22, h: 12, rot: 25 },
    { x: 180, y: 140, color: '#4ECDC4', w: 18, h: 10, rot: -15 },
    { x: 900, y: 180, color: '#FF8E53', w: 24, h: 12, rot: 40 },
    { x: 980, y: 300, color: '#A8E6CF', w: 16, h: 9,  rot: -30 },
    { x: 100, y: 400, color: '#FFD93D', w: 20, h: 11, rot: 10 },
    { x: 950, y: 450, color: '#6BCB77', w: 22, h: 12, rot: -20 },
    { x: 50,  y: 600, color: '#4D96FF', w: 18, h: 10, rot: 35 },
    { x: 1000,y: 550, color: '#FF6B6B', w: 16, h: 9,  rot: -45 },
    { x: 200, y: 500, color: '#A8E6CF', w: 24, h: 12, rot: 15 },
    { x: 850, y: 350, color: '#FFD93D', w: 20, h: 11, rot: -10 },
    { x: 700, y: 150, color: '#4ECDC4', w: 18, h: 10, rot: 55 },
    { x: 320, y: 160, color: '#FF8E53', w: 22, h: 12, rot: -25 },
    { x: 500, y: 700, color: '#FF6B6B', w: 16, h: 9,  rot: 20 },
    { x: 750, y: 800, color: '#4D96FF', w: 20, h: 11, rot: -35 },
    { x: 150, y: 750, color: '#6BCB77', w: 18, h: 10, rot: 45 },
  ];

  const milestoneSize = milestoneText && milestoneText.length > 10 ? 120 : 160;

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
      {confetti.map((c, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: c.x,
            top: c.y,
            width: c.w,
            height: c.h,
            background: c.color,
            borderRadius: 3,
            opacity: 0.8,
            transform: `rotate(${c.rot}deg)`,
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
        {/* Trophy */}
        <div style={{ fontSize: 160, lineHeight: 1 }}>🏆</div>

        {/* Milestone value */}
        <p
          style={{
            fontFamily: "'DM Serif Display', Georgia, serif",
            fontSize: milestoneSize,
            fontWeight: 700,
            color: '#5A2800',
            textAlign: 'center',
            lineHeight: 1.1,
            margin: '16px 0 0',
          }}
        >
          {milestoneText || 'Milestone!'}
        </p>

        {/* Divider */}
        <div style={{ width: 400, height: 4, background: 'rgba(90,40,0,0.3)', borderRadius: 2, marginTop: 32 }} />

        {/* Description */}
        <p
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: 44,
            fontStyle: 'italic',
            color: '#5A2800',
            textAlign: 'center',
            opacity: 0.85,
            margin: '32px 0 0',
            lineHeight: 1.45,
          }}
        >
          {description || 'A milestone reached on The Honey Groove'}
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
        <ShareCardFooter textColor="#5A2800" subColor="#7A4A18" />
      </div>
    </div>
  );
});

MilestoneCard.displayName = 'MilestoneCard';
export default MilestoneCard;
