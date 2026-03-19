import React from 'react';
import ShareCardBase, { BRAND } from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

const SaleCard = React.forwardRef(function SaleCard({ record, price, user }, ref) {
  const coverUrl = record?.cover_url ? resolveImageUrl(record.cover_url) : null;
  const title = record?.title || record?.record_title || 'Unknown Album';
  const artist = record?.artist || record?.record_artist || '';
  const priceStr = price != null ? `$${Number(price).toFixed(2)}` : '';

  const bg = 'linear-gradient(160deg, #F0FFF4 0%, #C8F0D8 40%, #88D8A8 100%)';

  return (
    <ShareCardBase ref={ref} bg={bg} user={user} footerTextColor="#1A6B3E" footerSubColor="#145830">
      {/* Album art with SOLD overlay */}
        <div style={{ position: 'relative', width: 700, height: 700 }}>
          <div
            style={{
              width: 700,
              height: 700,
              borderRadius: 28,
              overflow: 'hidden',
              boxShadow: '0 24px 64px rgba(0,0,0,0.22)',
              background: '#E0F0E8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {coverUrl ? (
              <img src={coverUrl} alt="" crossOrigin="anonymous" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <span style={{ fontSize: 100 }}>🎵</span>
            )}
          </div>

          {/* SOLD banner */}
          <div
            style={{
              position: 'absolute',
              top: 50,
              right: -30,
              width: 240,
              background: 'linear-gradient(135deg, #C8861A, #E8A820)',
              color: '#FFF',
              fontFamily: "'DM Serif Display', Georgia, serif",
              fontSize: 36,
              fontWeight: 700,
              letterSpacing: '0.12em',
              textAlign: 'center',
              padding: '14px 0',
              transform: 'rotate(30deg)',
              transformOrigin: 'center',
              boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
            }}
          >
            SOLD
          </div>
        </div>

        {/* Record info */}
        <div style={{ textAlign: 'center', marginTop: 28 }}>
          <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 52, fontWeight: 700, color: '#1A3D28', margin: 0, lineHeight: 1.15, maxWidth: 860 }}>
            {title}
          </p>
          {artist && (
            <p style={{ fontFamily: 'Georgia, serif', fontSize: 34, fontStyle: 'italic', color: '#2D6B4A', margin: '12px 0 0' }}>
              {artist}
            </p>
          )}
        </div>

        {/* Price */}
        {priceStr && (
          <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 96, fontWeight: 700, color: '#1A6B3E', margin: '20px 0 0', lineHeight: 1 }}>
            {priceStr}
          </p>
        )}

        {/* Tagline */}
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 34, color: '#2D6B4A', fontStyle: 'italic', margin: '16px 0 0', opacity: 0.85 }}>
          Sold on The Honeypot
        </p>
    </ShareCardBase>
  );
});

SaleCard.displayName = 'SaleCard';
export default SaleCard;
