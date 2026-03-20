import React from 'react';
import { resolveImageUrl } from '../utils/imageUrl';

/**
 * RoomShareCard — hidden 1080×1920 export target for html2canvas.
 * Render off-screen via ref in RoomPage. Toggle display before capture.
 *
 * Props:
 *   room         — room doc (name, emoji, member_count, theme)
 *   post         — optional post being shared (cover_url, caption)
 *   shareRef     — forwarded ref attached to the outer div
 */
const RoomShareCard = React.forwardRef(({ room, post }, ref) => {
  if (!room) return null;

  const theme = room.theme || {};
  const bgGradient = theme.bgGradient || 'linear-gradient(135deg, #FFF3E0, #FFE0B2)';
  const accentColor = theme.accentColor || '#D4A828';
  const textColor = theme.textColor || '#1E2A3A';

  return (
    <div
      ref={ref}
      style={{
        display: 'none',
        width: 1080,
        height: 1920,
        background: bgGradient,
        position: 'fixed',
        left: '-9999px',
        top: 0,
        fontFamily: 'DM Serif Display, serif',
        overflow: 'hidden',
      }}
    >
      {/* Top wordmark */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 0,
          right: 0,
          textAlign: 'center',
        }}
      >
        <p
          style={{
            fontFamily: 'DM Serif Display, serif',
            fontSize: 36,
            fontWeight: 700,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: accentColor,
          }}
        >
          THE HONEY GROOVE
        </p>
      </div>

      {/* Center content */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: 0,
          right: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 32,
          padding: '0 100px',
        }}
      >
        {/* Room emoji */}
        <div style={{ fontSize: 120, lineHeight: 1 }}>{room.emoji}</div>

        {/* Room name */}
        <p
          style={{
            fontFamily: 'DM Serif Display, serif',
            fontSize: 72,
            fontWeight: 700,
            color: textColor,
            textAlign: 'center',
            lineHeight: 1.1,
          }}
        >
          {room.nickname || room.name}
        </p>

        {/* Member count */}
        <p
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 36,
            color: accentColor,
            fontWeight: 600,
          }}
        >
          {(room.member_count || 0).toLocaleString()} members
        </p>

        {/* Optional post album art + caption */}
        {post?.cover_url && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20 }}>
            <div
              style={{
                width: 400,
                height: 400,
                borderRadius: 24,
                overflow: 'hidden',
                boxShadow: '0 24px 60px rgba(0,0,0,0.25)',
              }}
            >
              <img
                src={resolveImageUrl(post.cover_url)}
                alt=""
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                crossOrigin="anonymous"
              />
            </div>
            {post.caption && (
              <p
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: 32,
                  color: textColor,
                  textAlign: 'center',
                  opacity: 0.85,
                  maxWidth: 800,
                  lineHeight: 1.4,
                }}
              >
                "{post.caption.slice(0, 120)}{post.caption.length > 120 ? '…' : ''}"
              </p>
            )}
          </div>
        )}
      </div>

      {/* Bottom branding */}
      <div
        style={{
          position: 'absolute',
          bottom: 100,
          left: 0,
          right: 0,
          textAlign: 'center',
        }}
      >
        <p
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 30,
            color: accentColor,
            opacity: 0.8,
          }}
        >
          @thehoneygroove · thehoneygroove.com
        </p>
      </div>
    </div>
  );
});

RoomShareCard.displayName = 'RoomShareCard';
export default RoomShareCard;
