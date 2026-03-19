import React from 'react';
import ShareCardBase from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

const NowSpinningCard = React.forwardRef(function NowSpinningCard({ post, user }, ref) {
  const coverUrl = post?.cover_url ? resolveImageUrl(post.cover_url) : null;
  const title = post?.title || post?.record_title || 'Unknown Album';
  const artist = post?.artist || post?.record_artist || '';

  const bg = 'linear-gradient(160deg, #FFF8EE 0%, #FFE8B8 55%, #FFDDA0 100%)';

  return (
    <ShareCardBase ref={ref} bg={bg} user={user}>
        {/* Vinyl + album art */}
        <div style={{ position: 'relative', width: 780, height: 780 }}>
          {/* Vinyl disc */}
          <div
            style={{
              position: 'absolute',
              right: -80,
              top: '50%',
              transform: 'translateY(-50%)',
              width: 640,
              height: 640,
              borderRadius: '50%',
              background: 'radial-gradient(circle at 50% 50%, #444 0%, #2a2a2a 40%, #1a1a1a 70%, #111 100%)',
              boxShadow: '0 12px 48px rgba(0,0,0,0.35)',
              zIndex: 1,
            }}
          >
            {[100, 165, 230, 280, 330].map(r => (
              <div
                key={r}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: r * 2,
                  height: r * 2,
                  borderRadius: '50%',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
              />
            ))}
            <div
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: 110,
                height: 110,
                borderRadius: '50%',
                background: '#C8861A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div style={{ width: 18, height: 18, borderRadius: '50%', background: '#1a1a1a' }} />
            </div>
          </div>

          {/* Album art */}
          <div
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: 700,
              height: 700,
              borderRadius: 28,
              overflow: 'hidden',
              boxShadow: '0 32px 80px rgba(0,0,0,0.28)',
              zIndex: 2,
              background: '#F0E6D0',
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
        </div>

        {/* "NOW SPINNING" label */}
        <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 44, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#C8861A', margin: '40px 0 0' }}>
          Now Spinning
        </p>

        {/* Album title */}
        <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 56, fontWeight: 700, color: '#2A1A06', textAlign: 'center', lineHeight: 1.15, margin: '24px 0 0', maxWidth: 880 }}>
          {title}
        </p>

        {/* Artist */}
        {artist && (
          <p style={{ fontFamily: 'Georgia, serif', fontSize: 38, fontStyle: 'italic', color: '#8A6B4A', margin: '20px 0 0', textAlign: 'center' }}>
            {artist}
          </p>
        )}
    </ShareCardBase>
  );
});

NowSpinningCard.displayName = 'NowSpinningCard';
export default NowSpinningCard;
