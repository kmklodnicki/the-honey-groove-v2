import React from 'react';
import ShareCardBase, { BRAND } from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

const VaultValueCard = React.forwardRef(function VaultValueCard({ vaultData, user, isGold }, ref) {
  if (!vaultData) return null;

  const totalValue = vaultData.total_value ?? vaultData.estimated_value ?? 0;
  const recordCount = vaultData.record_count ?? vaultData.total_records ?? 0;
  const topGenre = vaultData.top_genre || '';
  const topRecords = (vaultData.top_records || vaultData.crown_jewels || []).slice(0, 4);

  const formattedValue = totalValue >= 1000
    ? `$${(totalValue / 1000).toFixed(1)}K`
    : `$${Math.round(totalValue).toLocaleString()}`;

  const bg = 'linear-gradient(160deg, #FEFCF5 0%, #FDF5DC 40%, #F5E8B8 100%)';

  return (
    <ShareCardBase ref={ref} bg={bg} user={user}>
      {/* "MY COLLECTION" */}
        <p style={{ fontFamily: 'Georgia, serif', fontSize: 30, letterSpacing: '0.18em', textTransform: 'uppercase', color: BRAND.warmBrown, margin: 0, fontWeight: 600 }}>
          My Collection
        </p>

        {/* Gold foil line */}
        <div style={{ width: 480, height: 3, background: 'linear-gradient(90deg, transparent, #C8861A, #F0B429, #C8861A, transparent)', borderRadius: 2, marginTop: 20 }} />

        {/* Total value */}
        <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 130, fontWeight: 700, color: BRAND.amber, margin: '16px 0 0', lineHeight: 1, letterSpacing: '-0.02em' }}>
          {formattedValue}
        </p>

        {/* Record count + genre pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap', justifyContent: 'center', marginTop: 20 }}>
          <span style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 44, color: BRAND.dark, fontWeight: 600 }}>
            {recordCount.toLocaleString()} {recordCount === 1 ? 'Record' : 'Records'}
          </span>
          {topGenre && (
            <span style={{ fontFamily: 'Georgia, serif', fontSize: 28, color: BRAND.amber, background: 'rgba(200,134,26,0.12)', border: '1.5px solid rgba(200,134,26,0.3)', borderRadius: 100, padding: '8px 24px', fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1 }}>
              {topGenre}
            </span>
          )}
        </div>

        {/* Accent strip */}
        <div style={{ width: '100%', height: 2, background: 'linear-gradient(90deg, transparent, rgba(200,134,26,0.3), transparent)', marginTop: 24 }} />

        {/* 2×2 album grid */}
        {topRecords.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20, width: 600, marginTop: 24 }}>
            {topRecords.map((rec, i) => {
              const url = rec.cover_url ? resolveImageUrl(rec.cover_url) : null;
              return (
                <div
                  key={i}
                  style={{ width: 290, height: 290, borderRadius: 20, overflow: 'hidden', boxShadow: '0 8px 24px rgba(0,0,0,0.18)', background: '#F0E6D0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                  {url ? (
                    <img src={url} alt="" crossOrigin="anonymous" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    <span style={{ fontSize: 60 }}>🎵</span>
                  )}
                </div>
              );
            })}
          </div>
        ) : <div />}

        {/* Gold trend */}
        {isGold && vaultData.value_trend ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px 40px', background: 'rgba(200,134,26,0.1)', borderRadius: 20, border: '1px solid rgba(200,134,26,0.25)', marginTop: 24 }}>
            <span style={{ fontFamily: 'Georgia, serif', fontSize: 26, color: BRAND.amber }}>🍯</span>
            <span style={{ fontFamily: 'Georgia, serif', fontSize: 26, color: BRAND.amberDark, fontWeight: 600 }}>
              {vaultData.value_trend > 0 ? '+' : ''}{vaultData.value_trend < 0 ? '-' : ''}${Math.abs(vaultData.value_trend).toLocaleString()} this month
            </span>
          </div>
        ) : null}
    </ShareCardBase>
  );
});

VaultValueCard.displayName = 'VaultValueCard';
export default VaultValueCard;
