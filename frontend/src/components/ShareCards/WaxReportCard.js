import React from 'react';
import ShareCardBase, { BRAND } from './ShareCardBase';
import { resolveImageUrl } from '../../utils/imageUrl';

/* ── Personality → background gradient + text colors ── */
const PERSONALITY_THEMES = {
  'The Obsessive Digger': {
    bg: 'linear-gradient(160deg, #FFF3DC 0%, #FFDA8A 40%, #E8A820 100%)',
    accent: '#7A5008',
    sub: '#5A3A04',
  },
  'The Deep Listener': {
    bg: 'linear-gradient(160deg, #E8F0FF 0%, #C5D8FF 40%, #7BA7F7 100%)',
    accent: '#1E3A6E',
    sub: '#2A4A84',
  },
  'The Social Butterfly': {
    bg: 'linear-gradient(160deg, #FFE8F4 0%, #F8C8E8 40%, #E8A0D0 100%)',
    accent: '#8B2252',
    sub: '#6B1A3E',
  },
  'The Silent Spinner': {
    bg: 'linear-gradient(160deg, #2C2C3E 0%, #1A1A2C 50%, #0E0E1C 100%)',
    accent: '#D4A828',
    sub: '#A06A14',
    dark: true,
  },
  'The Buzz Machine': {
    bg: 'linear-gradient(160deg, #FFF8DC 0%, #FFE566 40%, #F0B429 100%)',
    accent: '#6B4A00',
    sub: '#4A3300',
  },
  'The Dream Chaser': {
    bg: 'linear-gradient(160deg, #FFE8D0 0%, #FFB870 40%, #B060C8 100%)',
    accent: '#4A1870',
    sub: '#3A1058',
  },
  'The Loyalist': {
    bg: 'linear-gradient(160deg, #FFF5E8 0%, #F5E0C0 50%, #E8C898 100%)',
    accent: '#7A4A18',
    sub: '#5A3410',
  },
  'The Newcomer': {
    bg: 'linear-gradient(160deg, #F0FFF4 0%, #C8F0D8 40%, #8ADCB0 100%)',
    accent: '#1A6B3E',
    sub: '#145830',
  },
};

const DEFAULT_THEME = {
  bg: 'linear-gradient(160deg, #FFF8EE 0%, #FFE8B8 60%, #FFDDA0 100%)',
  accent: BRAND.amberDark,
  sub: BRAND.warmBrown,
  dark: false,
};

function StatCircle({ value, label, accent, sub }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 10,
        width: 260,
      }}
    >
      <div
        style={{
          width: 200,
          height: 200,
          borderRadius: '50%',
          border: `5px solid ${accent}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(255,255,255,0.25)',
        }}
      >
        <span
          style={{
            fontFamily: "'DM Serif Display', Georgia, serif",
            fontSize: 64,
            fontWeight: 700,
            color: accent,
          }}
        >
          {value ?? '—'}
        </span>
      </div>
      <span
        style={{
          fontFamily: 'Georgia, serif',
          fontSize: 22,
          color: sub,
          textAlign: 'center',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
        }}
      >
        {label}
      </span>
    </div>
  );
}

/**
 * WaxReportCard — share card for the weekly Wax Report personality.
 *
 * Props:
 *   report       — full report object from API
 *   user         — user object
 *   isGold       — boolean, shows pro stats row if true
 */
const WaxReportCard = React.forwardRef(function WaxReportCard({ report, user, isGold }, ref) {
  if (!report) return null;

  const personalityLabel = report.personality?.label || 'The Record Collector';
  const tagline = report.personality?.tagline || report.personality?.description || '';
  const ls = report.listening_stats || {};
  const theme = PERSONALITY_THEMES[personalityLabel] || DEFAULT_THEME;

  // Week range display
  let weekRange = '';
  try {
    const ws = new Date(report.week_start);
    const we = new Date(report.week_end);
    we.setDate(we.getDate() - 1);
    weekRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { weekRange = ''; }

  // Most spun artist cover
  const topArtistCover = ls.top_records?.[0]?.cover_url
    ? resolveImageUrl(ls.top_records[0].cover_url)
    : null;
  const topArtistName = ls.top_artist || ls.top_records?.[0]?.artist || '';
  const topArtistSpins = ls.top_artist_spins || ls.top_records?.[0]?.spin_count || '';

  const footerTextColor = theme.dark ? '#D4A828' : BRAND.amber;
  const footerSubColor = theme.dark ? '#A06A14' : BRAND.warmBrown;
  const userTextColor = theme.dark ? '#E8D0B0' : BRAND.dark;

  return (
    <ShareCardBase
      ref={ref}
      bg={theme.bg}
      user={user}
      footerTextColor={footerTextColor}
      footerSubColor={footerSubColor}
      userTextColor={userTextColor}
    >
      {/* "YOUR WEEK IN WAX" */}
        <div style={{ textAlign: 'center' }}>
          <p
            style={{
              fontFamily: 'Georgia, serif',
              fontSize: 26,
              letterSpacing: '0.18em',
              textTransform: 'uppercase',
              color: theme.sub,
              margin: 0,
              fontWeight: 600,
            }}
          >
            Your Week in Wax
          </p>
          {weekRange && (
            <p style={{ fontFamily: 'Georgia, serif', fontSize: 22, color: theme.sub, opacity: 0.7, margin: '6px 0 0' }}>
              {weekRange}
            </p>
          )}
        </div>

        {/* Personality label */}
        <p
          style={{
            fontFamily: "'DM Serif Display', Georgia, serif",
            fontSize: 64,
            fontWeight: 700,
            color: theme.accent,
            textAlign: 'center',
            lineHeight: 1.1,
            margin: '28px 0 0',
          }}
        >
          {personalityLabel}
        </p>

        {/* Tagline */}
        {tagline && (
          <p
            style={{
              fontFamily: 'Georgia, serif',
              fontSize: 28,
              fontStyle: 'italic',
              color: theme.sub,
              textAlign: 'center',
              lineHeight: 1.4,
              maxWidth: 820,
              margin: '24px 0 0',
            }}
          >
            "{tagline}"
          </p>
        )}

        {/* Stats row — 3 circles */}
        <div style={{ display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'nowrap', marginTop: 32 }}>
          <StatCircle
            value={ls.records_added ?? ls.new_records ?? 0}
            label="Records Added"
            accent={theme.accent}
            sub={theme.sub}
          />
          <StatCircle
            value={ls.total_spins ?? ls.spins ?? 0}
            label="Total Spins"
            accent={theme.accent}
            sub={theme.sub}
          />
          <StatCircle
            value={ls.avg_value ? `$${ls.avg_value}` : (ls.records_value ? `$${ls.records_value}` : '—')}
            label="Avg. Value"
            accent={theme.accent}
            sub={theme.sub}
          />
        </div>

        {/* Most spun artist */}
        {topArtistName && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              background: 'rgba(255,255,255,0.2)',
              borderRadius: 20,
              padding: '16px 32px',
              marginTop: 28,
            }}
          >
            {topArtistCover && (
              <div
                style={{
                  width: 88,
                  height: 88,
                  borderRadius: 12,
                  overflow: 'hidden',
                  flexShrink: 0,
                  boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                }}
              >
                <img
                  src={topArtistCover}
                  alt=""
                  crossOrigin="anonymous"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
            )}
            <div>
              <p style={{ fontFamily: 'Georgia, serif', fontSize: 20, color: theme.sub, margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                Most Spun
              </p>
              <p style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 28, fontWeight: 700, color: theme.accent, margin: 0 }}>
                {topArtistName}
              </p>
              {topArtistSpins && (
                <p style={{ fontFamily: 'Georgia, serif', fontSize: 20, color: theme.sub, margin: '4px 0 0' }}>
                  {topArtistSpins} {topArtistSpins === 1 ? 'spin' : 'spins'}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Gold pro stats row */}
        {isGold && (report.collection_value?.change_pct || ls.value_change) && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 32,
              padding: '14px 40px',
              background: 'rgba(200,134,26,0.12)',
              borderRadius: 16,
              border: `1px solid rgba(200,134,26,0.25)`,
              marginTop: 24,
            }}
          >
            <span style={{ fontFamily: 'Georgia, serif', fontSize: 22, color: theme.accent, lineHeight: 1 }}>
              🍯 Gold
            </span>
            {report.collection_value?.change_pct && (
              <span style={{ fontFamily: 'Georgia, serif', fontSize: 22, color: theme.accent, lineHeight: 1 }}>
                Collection {report.collection_value.change_pct > 0 ? '+' : ''}{report.collection_value.change_pct}% this week
              </span>
            )}
          </div>
        )}
    </ShareCardBase>
  );
});

WaxReportCard.displayName = 'WaxReportCard';
export default WaxReportCard;
