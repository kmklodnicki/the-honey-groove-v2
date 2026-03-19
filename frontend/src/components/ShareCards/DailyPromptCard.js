import React from 'react';
import ShareCardBase, { BRAND } from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

const DailyPromptCard = React.forwardRef(function DailyPromptCard({ promptQuestion, record, user }, ref) {
  const coverUrl = record?.cover_url ? resolveImageUrl(record.cover_url) : null;
  const title = record?.title || record?.record_title || '';
  const artist = record?.artist || record?.record_artist || '';

  const bg = 'linear-gradient(160deg, #FFFDF5 0%, #FFF8E0 45%, #FAF0C0 100%)';

  // Inline SVG tiled pattern — avoids data:image/svg+xml CSS backgrounds which
  // cause SecurityError on iOS Safari when html2canvas tries to draw them to canvas.
  const hexCols = 10;
  const hexRows = 20;
  const hexW = 120;
  const hexH = 104;
  const hexTiles = [];
  for (let r = 0; r < hexRows; r++) {
    for (let c = 0; c < hexCols; c++) {
      const x = c * hexW;
      const y = r * hexH;
      hexTiles.push(
        <g key={`${r}-${c}`} transform={`translate(${x},${y})`}>
          <polygon points='30,2 90,2 120,52 90,102 30,102 0,52' fill='none' stroke='rgba(200,134,26,0.08)' strokeWidth='2' />
          <polygon points='90,2 150,2 180,52 150,102 90,102 60,52' fill='none' stroke='rgba(200,134,26,0.08)' strokeWidth='2' />
          <polygon points='30,54 90,54 120,104 90,154 30,154 0,104' fill='none' stroke='rgba(200,134,26,0.08)' strokeWidth='2' />
        </g>
      );
    }
  }

  return (
    <ShareCardBase ref={ref} bg={bg} user={user}>
      {/* Hex pattern overlay — inline SVG so html2canvas can render it without canvas security errors */}
      <svg
        width='1080'
        height='1920'
        style={{ position: 'absolute', top: 0, left: 0, opacity: 0.5, pointerEvents: 'none', zIndex: 0 }}
      >
        {hexTiles}
      </svg>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', position: 'relative', zIndex: 1 }}>
        {/* "Daily Prompt" tag */}
        <div style={{ background: 'rgba(200,134,26,0.12)', border: '1.5px solid rgba(200,134,26,0.3)', borderRadius: 100, padding: '10px 32px', display: 'inline-block', textAlign: 'center' }}>
          {/* Text is opacity:0 so html2canvas preserves layout but doesn't draw it wrong.
              Canvas 2D API redraws it pixel-perfectly via the data-canvas-redraw mechanism. */}
          <p
            style={{ fontFamily: 'Georgia, serif', fontSize: 26, color: BRAND.amber, fontWeight: 700, letterSpacing: '0.08em', margin: 0, textTransform: 'uppercase', lineHeight: '1.6', opacity: 0 }}
            data-canvas-redraw="text"
            data-canvas-text="🐝 DAILY PROMPT"
            data-canvas-color={BRAND.amber}
            data-canvas-font="bold 26px Georgia, serif"
          >
            🐝 Daily Prompt
          </p>
        </div>

        {/* Prompt question */}
        {promptQuestion && (
          <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 42, fontStyle: 'italic', color: BRAND.dark, textAlign: 'center', lineHeight: 1.4, margin: '28px 0 0', maxWidth: 860 }}>
            "{promptQuestion}"
          </p>
        )}

        {/* Album art */}
        <div
          style={{
            width: 660,
            height: 660,
            borderRadius: 28,
            overflow: 'hidden',
            boxShadow: '0 24px 64px rgba(0,0,0,0.22)',
            background: '#F0E6D0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginTop: 28,
          }}
        >
          {coverUrl ? (
            <img src={coverUrl} alt="" crossOrigin="anonymous" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <span style={{ fontSize: 100 }}>🎵</span>
          )}
        </div>

        {/* Album info */}
        {title && (
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 46, fontWeight: 700, color: BRAND.dark, margin: 0, lineHeight: 1.2 }}>
              {title}
            </p>
            {artist && (
              <p style={{ fontFamily: 'Georgia, serif', fontSize: 32, fontStyle: 'italic', color: BRAND.warmBrown, margin: '10px 0 0' }}>
                {artist}
              </p>
            )}
          </div>
        )}

        {/* Tag */}
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 26, color: BRAND.warmBrown, margin: '16px 0 0', opacity: 0.75 }}>
          Daily Prompt on The Honey Groove
        </p>
      </div>
    </ShareCardBase>
  );
});

DailyPromptCard.displayName = 'DailyPromptCard';
export default DailyPromptCard;
