import React from 'react';
import ShareCardBase, { BRAND } from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

/**
 * TradeCard — vertical layout (sent above, received below) to fill 9:16 canvas.
 */
const TradeCard = React.forwardRef(function TradeCard(
  { sentRecord, receivedRecord, partnerUsername, user },
  ref
) {
  const sentUrl = sentRecord?.cover_url ? resolveImageUrl(sentRecord.cover_url) : null;
  const receivedUrl = receivedRecord?.cover_url ? resolveImageUrl(receivedRecord.cover_url) : null;

  const bg = 'linear-gradient(160deg, #FFF8EE 0%, #FFE8B8 50%, #FFCF78 100%)';

  const coverStyle = {
    width: 440,
    height: 440,
    borderRadius: 24,
    overflow: 'hidden',
    boxShadow: '0 20px 60px rgba(0,0,0,0.22)',
    background: '#F0E6D0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  };

  return (
    <ShareCardBase ref={ref} bg={bg} user={user} footerHeight={200}>
        {/* "JUST TRADED" */}
        <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 72, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: BRAND.amberDark, margin: 0, textAlign: 'center' }}>
          Just Traded
        </p>

        {/* Sent record */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, marginTop: 20 }}>
          <p style={{ fontFamily: 'Georgia, serif', fontSize: 26, color: BRAND.warmBrown, textTransform: 'uppercase', letterSpacing: '0.12em', margin: 0 }}>Sent</p>
          <div style={coverStyle}>
            {sentUrl ? (
              <img src={sentUrl} alt="" crossOrigin="anonymous" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <span style={{ fontSize: 80 }}>🎵</span>
            )}
          </div>
          {sentRecord?.title && (
            <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 28, fontWeight: 700, color: BRAND.dark, textAlign: 'center', margin: 0, lineHeight: 1.25, maxWidth: 440 }}>
              {sentRecord.title}
            </p>
          )}
        </div>

        {/* Swap icon */}
        <div style={{ fontSize: 64, lineHeight: 1, color: BRAND.amber, marginTop: 12 }}>⇅</div>

        {/* Received record */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, marginTop: 12 }}>
          <p style={{ fontFamily: 'Georgia, serif', fontSize: 26, color: BRAND.warmBrown, textTransform: 'uppercase', letterSpacing: '0.12em', margin: 0 }}>Received</p>
          <div style={coverStyle}>
            {receivedUrl ? (
              <img src={receivedUrl} alt="" crossOrigin="anonymous" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <span style={{ fontSize: 80 }}>🎵</span>
            )}
          </div>
          {receivedRecord?.title && (
            <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 28, fontWeight: 700, color: BRAND.dark, textAlign: 'center', margin: 0, lineHeight: 1.25, maxWidth: 440 }}>
              {receivedRecord.title}
            </p>
          )}
        </div>

        {/* Trade partner */}
        {partnerUsername && user?.username && (
          <p style={{ fontFamily: 'Georgia, serif', fontSize: 28, color: BRAND.warmBrown, margin: '20px 0 0', textAlign: 'center' }}>
            @{user.username} × @{partnerUsername}
          </p>
        )}
    </ShareCardBase>
  );
});

TradeCard.displayName = 'TradeCard';
export default TradeCard;
