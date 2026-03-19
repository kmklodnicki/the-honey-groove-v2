import React from 'react';
import ShareCardBase from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

const NewHaulCard = React.forwardRef(function NewHaulCard({ post, user }, ref) {
  // Hauls can be a single record or a bundle — show first record's art
  const coverUrl = post?.cover_url
    ? resolveImageUrl(post.cover_url)
    : post?.bundle_records?.[0]?.cover_url
      ? resolveImageUrl(post.bundle_records[0].cover_url)
      : null;
  const title = post?.title || post?.record_title || post?.bundle_records?.[0]?.title || 'New Haul';
  const artist = post?.artist || post?.record_artist || post?.bundle_records?.[0]?.artist || '';
  const variant = post?.variant || post?.color_variant || '';
  const bundleCount = post?.bundle_records?.length;

  // Slightly deeper warm gradient to distinguish from Now Spinning
  const bg = 'linear-gradient(160deg, #FFF5E8 0%, #FFD9A0 55%, #FFBF6A 100%)';

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
          <span style={{ fontSize: 100 }}>🎶</span>
        )}
      </div>

      {/* "NEW HAUL" label */}
      <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 44, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#C8861A', margin: '40px 0 0' }}>
        New Haul
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

      {/* Bundle indicator */}
      {bundleCount > 1 && (
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 28, color: '#C8861A', margin: '16px 0 0', opacity: 0.8 }}>
          +{bundleCount - 1} more record{bundleCount - 1 !== 1 ? 's' : ''}
        </p>
      )}
    </ShareCardBase>
  );
});

NewHaulCard.displayName = 'NewHaulCard';
export default NewHaulCard;
