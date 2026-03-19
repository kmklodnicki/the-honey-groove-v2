import React from 'react';
import ShareCardBase from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

const NowSpinningCard = React.forwardRef(function NowSpinningCard({ post, user }, ref) {
  const coverUrl = post?.cover_url ? resolveImageUrl(post.cover_url) : null;
  const title = post?.title || post?.record_title || 'Unknown Album';
  const artist = post?.artist || post?.record_artist || '';
  const variant = post?.variant || post?.color_variant || '';

  const bg = 'linear-gradient(160deg, #FFF8EE 0%, #FFE8B8 55%, #FFDDA0 100%)';

  return (
    <ShareCardBase ref={ref} bg={bg} user={user}>
        {/* Album art */}
        <div
          data-canvas-image="true"
          data-canvas-radius="28"
          style={{
            width: 700,
            height: 700,
            borderRadius: 28,
            overflow: 'hidden',
            boxShadow: '0 12px 40px rgba(0,0,0,0.35)',
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

        {/* Variant */}
        {variant && (
          <p style={{ fontFamily: 'Georgia, serif', fontSize: 28, fontStyle: 'italic', color: '#888888', margin: '12px 0 0', textAlign: 'center' }}>
            {variant}
          </p>
        )}
    </ShareCardBase>
  );
});

NowSpinningCard.displayName = 'NowSpinningCard';
export default NowSpinningCard;
