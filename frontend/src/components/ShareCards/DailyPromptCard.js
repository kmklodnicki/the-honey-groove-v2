import React from 'react';
import ShareCardBase, { BRAND } from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

const DailyPromptCard = React.forwardRef(function DailyPromptCard({ promptQuestion, record, user }, ref) {
  const coverUrl = record?.cover_url ? resolveImageUrl(record.cover_url) : null;
  const title = record?.title || record?.record_title || '';
  const artist = record?.artist || record?.record_artist || '';

  const bg = 'linear-gradient(160deg, #FFFDF5 0%, #FFF8E0 45%, #FAF0C0 100%)';

  const hexPattern = `
    <svg xmlns='http://www.w3.org/2000/svg' width='120' height='104' viewBox='0 0 120 104'>
      <polygon points='30,2 90,2 120,52 90,102 30,102 0,52' fill='none' stroke='rgba(200,134,26,0.08)' stroke-width='2'/>
      <polygon points='90,2 150,2 180,52 150,102 90,102 60,52' fill='none' stroke='rgba(200,134,26,0.08)' stroke-width='2'/>
      <polygon points='30,54 90,54 120,104 90,154 30,154 0,104' fill='none' stroke='rgba(200,134,26,0.08)' stroke-width='2'/>
    </svg>
  `;
  const hexDataUrl = `data:image/svg+xml;base64,${btoa(hexPattern)}`;

  return (
    <ShareCardBase ref={ref} bg={bg} user={user}>
      {/* Hex pattern overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url("${hexDataUrl}")`,
          backgroundSize: '120px 104px',
          backgroundRepeat: 'repeat',
          opacity: 0.5,
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', padding: '0 80px', position: 'relative', zIndex: 1 }}>
        <div style={{ flex: 1, minHeight: 0 }} />

        {/* "Daily Prompt" tag */}
        <div style={{ background: 'rgba(200,134,26,0.12)', border: '1.5px solid rgba(200,134,26,0.3)', borderRadius: 100, padding: '10px 32px' }}>
          <p style={{ fontFamily: 'Georgia, serif', fontSize: 26, color: BRAND.amber, fontWeight: 700, letterSpacing: '0.08em', margin: 0, textTransform: 'uppercase' }}>
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
        <div style={{ flex: 1, minHeight: 0 }} />
      </div>
    </ShareCardBase>
  );
});

DailyPromptCard.displayName = 'DailyPromptCard';
export default DailyPromptCard;
