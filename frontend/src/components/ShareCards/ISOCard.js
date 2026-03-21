import React from 'react';
import ShareCardBase from './ShareCardBase';
import { COLORS } from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

/**
 * ISOCard — share card for "In Search Of" posts.
 *
 * Props:
 *   record   — record object with cover_url, title, artist
 *   user     — user object for footer attribution
 */
const ISOCard = React.forwardRef(function ISOCard({ record, user }, ref) {
  const coverUrl = record?.cover_url ? resolveImageUrl(record.cover_url) : null;
  const title = record?.title || record?.record_title || 'Unknown Album';
  const artist = record?.artist || record?.record_artist || '';

  const bg = `linear-gradient(160deg, ${COLORS.CREAM} 0%, ${COLORS.CREAM_DARK} 55%, #EDE0CC 100%)`;

  return (
    <ShareCardBase ref={ref} bg={bg} user={user}>
      {/* "SEEKING" badge */}
      <div
        style={{
          display: 'inline-block',
          background: 'rgba(30,42,58,0.10)',
          border: '1.5px solid rgba(30,42,58,0.18)',
          borderRadius: 9999,
          padding: '10px 36px',
          textAlign: 'center',
        }}
      >
        <span
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: 34,
            fontWeight: 700,
            color: COLORS.NAVY,
            textTransform: 'uppercase',
            letterSpacing: '0.14em',
          }}
        >
          Seeking
        </span>
      </div>

      {/* "ISO: Looking for this record" */}
      <p
        style={{
          fontFamily: "'Playfair Display', Georgia, serif",
          fontSize: 52,
          fontWeight: 700,
          color: COLORS.NAVY,
          textAlign: 'center',
          margin: '40px 0 0',
          lineHeight: 1.3,
          maxWidth: 860,
        }}
      >
        ISO: Looking for this record
      </p>

      {/* Album art */}
      <div
        data-canvas-image="true"
        data-canvas-radius="50"
        style={{
          width: 600,
          height: 600,
          borderRadius: 50,
          overflow: 'hidden',
          background: COLORS.GOLD_PALE,
          margin: '60px auto 0',
          border: '2px dashed rgba(212,168,40,0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 16px 48px rgba(0,0,0,0.18)',
        }}
      >
        {coverUrl ? (
          <img
            src={coverUrl}
            alt=""
            crossOrigin="anonymous"
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <span style={{ fontSize: 120 }}>🎵</span>
        )}
      </div>

      {/* Album title */}
      <p
        style={{
          fontFamily: "'Playfair Display', Georgia, serif",
          fontSize: 64,
          fontWeight: 700,
          color: COLORS.NAVY,
          textAlign: 'center',
          margin: '50px 0 0',
          lineHeight: 1.2,
          maxWidth: 880,
        }}
      >
        {title}
      </p>

      {/* Artist */}
      {artist && (
        <p
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: 42,
            fontStyle: 'italic',
            color: COLORS.SLATE,
            textAlign: 'center',
            margin: '20px 0 0',
          }}
        >
          {artist}
        </p>
      )}

      {/* CTA bar */}
      <div
        style={{
          marginTop: 48,
          padding: '22px 64px',
          borderRadius: 24,
          background: 'rgba(212,168,40,0.10)',
          border: '1.5px solid rgba(212,168,40,0.20)',
          textAlign: 'center',
        }}
      >
        <span
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: 34,
            fontWeight: 700,
            color: COLORS.GOLD,
            letterSpacing: '0.02em',
          }}
        >
          Have this? DM me on The Honey Groove
        </span>
      </div>
    </ShareCardBase>
  );
});

ISOCard.displayName = 'ISOCard';
export default ISOCard;
