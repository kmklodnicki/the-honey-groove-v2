import React from 'react';
import { ShareCardHeader, ShareCardFooter, ShareCardUser, BRAND, CARD_W, CARD_H } from './ShareCardBase';

const RoomCard = React.forwardRef(function RoomCard({ room, user }, ref) {
  if (!room) return null;

  const theme = room.theme || {};
  const bg = theme.bgGradient || 'linear-gradient(135deg, #FFF3E0, #FFE0B2)';
  const accentColor = theme.accentColor || BRAND.amber;
  const textColor = theme.textColor || BRAND.dark;

  const isDark = textColor?.includes('0A') || textColor === '#1A1A1A' || textColor?.includes('1A0A');
  const footerTextColor = isDark ? '#E8D0B0' : accentColor;
  const footerSubColor = isDark ? '#B8A090' : BRAND.warmBrown;

  const displayName = room.nickname || room.name;

  return (
    <div
      ref={ref}
      style={{
        display: 'none',
        width: CARD_W,
        height: CARD_H,
        background: bg,
        flexDirection: 'column',
        fontFamily: "'DM Serif Display', Georgia, serif",
        overflow: 'hidden',
        position: 'fixed',
        left: '-9999px',
        top: 0,
      }}
    >
      <ShareCardHeader />

      {/* Content */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '0 80px',
        }}
      >
        <div style={{ flex: 1, minHeight: 0 }} />
        {/* Hexagon room icon */}
        <div style={{ position: 'relative', width: 320, height: 360 }}>
          <svg width="320" height="360" viewBox="0 0 320 360">
            <polygon
              points="160,16 304,88 304,264 160,336 16,264 16,88"
              fill={accentColor}
              opacity="0.15"
              stroke={accentColor}
              strokeWidth="4"
            />
            <polygon
              points="160,48 280,115 280,253 160,320 40,253 40,115"
              fill={accentColor}
              opacity="0.08"
            />
          </svg>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 130,
            }}
          >
            {room.emoji}
          </div>
        </div>

        {/* "I'm in the" */}
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 48, color: textColor, opacity: 0.75, margin: '24px 0 0', textAlign: 'center', letterSpacing: '0.04em' }}>
          I'm in the
        </p>

        {/* Room name */}
        <p
          style={{
            fontFamily: "'DM Serif Display', Georgia, serif",
            fontSize: displayName && displayName.length > 12 ? 80 : 110,
            fontWeight: 700,
            color: textColor,
            textAlign: 'center',
            lineHeight: 1.1,
            margin: 0,
          }}
        >
          {displayName}
        </p>

        {/* "room" suffix */}
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 48, color: textColor, opacity: 0.75, margin: 0, letterSpacing: '0.04em' }}>
          room
        </p>

        {/* Member count */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '16px 40px',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: 100,
            border: `1.5px solid ${accentColor}40`,
            marginTop: 24,
          }}
        >
          <span style={{ fontFamily: 'Georgia, serif', fontSize: 36, color: accentColor, fontWeight: 700 }}>
            {(room.member_count || 0).toLocaleString()} {room.member_count === 1 ? 'member' : 'members'}
          </span>
        </div>
        <div style={{ flex: 1, minHeight: 0 }} />
      </div>

      <ShareCardUser user={user} textColor={textColor} />
      <ShareCardFooter textColor={footerTextColor} subColor={footerSubColor} />
    </div>
  );
});

RoomCard.displayName = 'RoomCard';
export default RoomCard;
