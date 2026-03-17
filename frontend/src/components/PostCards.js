import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Disc, Package, Search, Moon, Plus, Music, Feather, ShoppingBag, ArrowRightLeft, Shuffle, Gem, MessageCircle, BookOpen, Sparkles, BarChart3, Check, Circle, FileText } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import AlbumArt from './AlbumArt';
import { resolveImageUrl, isLegacyUploadUrl } from '../utils/imageUrl';
import PhotoLightbox from './PhotoLightbox';
import MentionText from './MentionText';
import UnofficialPill from './UnofficialPill';

// Streaming deep links — Spotify & Apple Music
// Uses resolved Spotify link from API when discogs_id is available, falls back to generic search
const StreamingLinks = ({ artist, album, discogsId, showEqualizer }) => {
  const { token, API } = useAuth();
  const [resolvedSpotify, setResolvedSpotify] = React.useState(null);

  React.useEffect(() => {
    if (!discogsId || !token) return;
    let cancelled = false;
    axios.get(`${API}/spotify/link/${discogsId}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { if (!cancelled) setResolvedSpotify(r.data); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [discogsId, token, API]);

  if (!artist || !album) return null;

  const q = encodeURIComponent(`${artist} ${album}`);
  const spotifyUrl = resolvedSpotify?.spotify_url || `https://open.spotify.com/search/${q}`;
  const spotifyMatched = resolvedSpotify?.matched || false;
  const appleUrl = `https://music.apple.com/us/search?term=${q}`;
  return (
    <div className="flex items-center gap-2 mt-4 mb-3" data-testid="streaming-links">
      <a href={spotifyUrl} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
        className="transition-all hover:scale-110" data-testid="spotify-link"
        title={spotifyMatched ? 'Listen on Spotify' : 'Search on Spotify'}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill={spotifyMatched ? "#1DB954" : "#9CA3AF"}>
          <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
        </svg>
      </a>
      <a href={appleUrl} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
        className="transition-all hover:scale-110" data-testid="apple-music-link">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#FA243C">
          <path d="M23.994 6.124a9.23 9.23 0 00-.24-2.19c-.317-1.31-1.062-2.31-2.18-3.043a5.022 5.022 0 00-1.877-.726 10.496 10.496 0 00-1.564-.15c-.04-.003-.083-.01-.124-.013H5.986c-.152.01-.303.017-.455.026-.747.043-1.49.123-2.193.4-1.336.53-2.3 1.452-2.865 2.78-.192.448-.292.925-.363 1.408-.056.392-.088.785-.1 1.18 0 .032-.007.062-.01.093v12.223c.01.14.017.283.027.424.05.815.154 1.624.497 2.373.65 1.42 1.738 2.353 3.234 2.802.42.127.856.187 1.293.228.555.053 1.11.06 1.667.06h11.03a12.5 12.5 0 001.57-.1c.822-.106 1.596-.35 2.295-.81a5.046 5.046 0 001.88-2.207c.186-.42.293-.87.37-1.324.113-.675.138-1.358.137-2.04-.002-3.8 0-7.595-.003-11.393zm-6.423 3.99v5.712c0 .417-.058.827-.244 1.206-.29.59-.76.962-1.388 1.14-.35.1-.706.157-1.07.173-.95.042-1.8-.6-1.965-1.48-.18-.965.407-1.867 1.35-2.076.39-.086.784-.14 1.176-.208.254-.046.464-.175.56-.433.05-.14.073-.29.073-.443V10.12a.507.507 0 00-.4-.497c-.09-.02-.183-.03-.273-.042-.578-.074-1.156-.14-1.734-.218-.378-.05-.756-.104-1.132-.162a.475.475 0 00-.076-.003c-.318.008-.512.2-.512.52-.003 2.563-.002 5.124-.005 7.687 0 .373-.047.74-.2 1.084-.307.69-.827 1.1-1.566 1.27-.325.074-.655.117-.99.128a1.79 1.79 0 01-1.723-1.13 1.756 1.756 0 011.028-2.386c.395-.137.81-.2 1.22-.27.274-.047.5-.182.598-.463.045-.128.063-.266.063-.403V7.272c0-.37.148-.634.49-.803.126-.062.263-.1.4-.125l4.148-.753c.308-.056.617-.108.927-.153.088-.013.178-.01.265.004.282.05.435.233.454.52.003.058.004.117.004.176 0 1.262 0 2.524-.003 3.786z"/>
        </svg>
      </a>
      {showEqualizer && <LiveEqualizer />}
    </div>
  );
};

const MOOD_EMOJI_MAP = {
  // Current 12 moods
  'New Arrival': '\u{1F4E6}', 'Deep Listening': '\u{1F9D8}', 'In The Zone': '\u{1F3AF}',
  'Me Time': '\u{1F9CD}', 'Cleaning Session': '\u{1F9FC}', 'Spin Party': '\u{1FA69}',
  'Limited Edition': '\u{1F48E}', 'Vibe Check': '\u2728', 'Late Night': '\u{1F319}',
  'Background': '\u2615', 'In My Feels': '\u{1F972}', 'Daydreaming': '\u2601\uFE0F',
  // Legacy (backward compat)
  'High Fidelity': '\u{1F50A}', 'Solo Session': '\u{1F56F}\uFE0F', 'Background Wax': '\u2615',
  'Good Morning': '\u2600\uFE0F', 'Sunday Morning': '\u2600\uFE0F',
  'Rainy Day': '\u{1F327}\uFE0F', 'Road Trip': '\u{1F697}', 'Golden Hour': '\u{1F305}',
  'Deep Focus': '\u{1F3A7}', 'Party Mode': '\u{1F942}', 'Lazy Afternoon': '\u{1F6CB}\uFE0F',
  'Melancholy': '\u{1F494}', 'Upbeat Vibes': '\u2728', 'Cozy Evening': '\u{1F9F8}', 'Workout': '\u{1F525}',
};
const MOOD_COLOR_MAP = {
  // Current 12 moods
  'New Arrival': '#c8861a', 'Deep Listening': '#4a7aaa', 'In The Zone': '#2a6a2a',
  'Me Time': '#6a3a9a', 'Cleaning Session': '#3a9a5a', 'Spin Party': '#aa3a8a',
  'Limited Edition': '#5a5aaa', 'Vibe Check': '#aa7a3a', 'Late Night': '#4a4a8a',
  'Background': '#8a6a3a', 'In My Feels': '#5a5a8a', 'Daydreaming': '#6a8aaa',
  // Legacy
  'High Fidelity': '#cc3a2a', 'Solo Session': '#6a3a9a', 'Background Wax': '#8a6a3a',
  'Good Morning': '#e8a820', 'Sunday Morning': '#e8a820',
  'Rainy Day': '#4a7aaa', 'Road Trip': '#4a8a4a', 'Golden Hour': '#c8861a',
  'Deep Focus': '#2a6a2a', 'Party Mode': '#aa3a8a', 'Lazy Afternoon': '#aa7a3a',
  'Melancholy': '#5a5a8a', 'Upbeat Vibes': '#3a9a5a', 'Cozy Evening': '#aa5a2a', 'Workout': '#cc3a2a',
};

// Clickable album card wrapper — calls onAlbumClick if provided, otherwise navigates to record detail
const AlbumLink = ({ record, children, className = '', onAlbumClick }) => {
  const rid = record?.id || record?.record_id;
  if (rid || record?.discogs_id) {
    if (onAlbumClick) {
      return (
        <div
          role="button"
          tabIndex={0}
          onClick={(e) => { e.stopPropagation(); onAlbumClick(record); }}
          onKeyDown={(e) => e.key === 'Enter' && onAlbumClick(record)}
          className={`block hover:opacity-80 active:scale-[0.98] transition-all cursor-pointer ${className}`}
          data-testid={`album-link-${rid || record.discogs_id}`}
        >
          {children}
        </div>
      );
    }
    if (rid) {
      return (
        <Link to={`/record/${rid}`} className={`block hover:opacity-80 transition-opacity cursor-pointer ${className}`} data-testid={`album-link-${rid}`}>
          {children}
        </Link>
      );
    }
  }
  return <div className={className}>{children}</div>;
};

// Badge showing post type
// ── Shared Pill Style System ──
// Used by both filter pills (HivePage) and card badges (PostCards)
const PILL_STYLES = {
  NOW_SPINNING:         { bg: 'bg-amber-100',   text: 'text-amber-700',   border: 'border-amber-200' },
  NEW_HAUL:             { bg: 'bg-pink-100',     text: 'text-pink-600',    border: 'border-pink-200' },
  ISO:                  { bg: 'bg-rose-100',     text: 'text-rose-600',    border: 'border-rose-200' },
  ADDED_TO_COLLECTION:  { bg: 'bg-green-100',    text: 'text-green-700',   border: 'border-green-200' },
  listing_sale:         { bg: 'bg-teal-100',     text: 'text-teal-700',    border: 'border-teal-200' },
  listing_trade:        { bg: 'bg-teal-100',     text: 'text-teal-700',    border: 'border-teal-200' },
  listing:              { bg: 'bg-teal-100',     text: 'text-teal-700',    border: 'border-teal-200' },
  WEEKLY_WRAP:          { bg: 'bg-purple-100',   text: 'text-purple-700',  border: 'border-purple-200' },
  VINYL_MOOD:           { bg: 'bg-purple-100',   text: 'text-purple-700',  border: 'border-purple-200' },
  DAILY_PROMPT:         { bg: 'bg-sky-100',      text: 'text-sky-700',     border: 'border-sky-200' },
  RANDOMIZER:           { bg: 'bg-amber-200',    text: 'text-black',       border: 'border-amber-400' },
  NOTE:                 { bg: 'bg-yellow-100',   text: 'text-yellow-700',  border: 'border-yellow-200' },
  RELEASE_NOTE:         { bg: 'bg-amber-500',    text: 'text-white',       border: 'border-amber-600' },
  POLL:                 { bg: 'bg-amber-100',    text: 'text-amber-800',   border: 'border-amber-200' },
  NEW_FEATURE:          { bg: 'bg-green-100',    text: 'text-green-700',   border: 'border-green-200' },
  following:            { bg: 'bg-violet-100',   text: 'text-violet-700',  border: 'border-violet-200' },
  all:                  { bg: 'bg-stone-100',    text: 'text-stone-600',   border: 'border-stone-200' },
};

const VARIANT_PILL_STYLES = {
  red:     'bg-red-100 text-red-700 border-red-200',
  blue:    'bg-blue-100 text-blue-700 border-blue-200',
  pink:    'bg-pink-100 text-pink-700 border-pink-200',
  green:   'bg-green-100 text-green-700 border-green-200',
  yellow:  'bg-yellow-100 text-yellow-700 border-yellow-200',
  orange:  'bg-orange-100 text-orange-700 border-orange-200',
  purple:  'bg-purple-100 text-purple-700 border-purple-200',
  white:   'bg-gray-50 text-gray-600 border-gray-200',
  black:   'bg-gray-900/10 text-gray-800 border-gray-300',
  clear:   'bg-gray-100 text-gray-600 border-gray-200',
  gold:    'bg-amber-100 text-amber-700 border-amber-200',
  silver:  'bg-slate-100 text-slate-600 border-slate-200',
};
const VARIANT_DEFAULT = 'bg-stone-100 text-stone-600 border-stone-200';

// Build link path for a variant pill from a record's discogs_id
const variantLink = (record) => record?.discogs_id ? `/variant/${record.discogs_id}` : undefined;

const PostTypeBadge = ({ type, mood, isReleaseNote }) => {
  // Release Note badge overrides the default post type pill
  if (isReleaseNote) {
    const s = PILL_STYLES.RELEASE_NOTE;
    return (
      <span className="inline-flex items-center gap-1.5">
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border whitespace-nowrap shadow-sm ${s.bg} ${s.text} ${s.border}`} data-testid="release-note-badge">
          <FileText className="w-3 h-3 shrink-0" />
          Release Note
        </span>
      </span>
    );
  }
  if (type === 'NOTE') {
    const s = PILL_STYLES.NOTE;
    return (
      <span className="inline-flex items-center gap-1.5">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border whitespace-nowrap ${s.bg} ${s.text} ${s.border}`}>
          <BookOpen className="w-3 h-3 shrink-0" />
          Note
        </span>
      </span>
    );
  }
  const config = {
    NOW_SPINNING: { label: 'Now Spinning', icon: Disc, emoji: '🎵' },
    NEW_HAUL: { label: 'New Haul', icon: Package },
    ISO: { label: 'ISO', icon: Gem },
    ADDED_TO_COLLECTION: { label: 'Added', icon: Plus },
    WEEKLY_WRAP: { label: 'Weekly Wrap', icon: Music },
    VINYL_MOOD: { label: 'Vinyl Mood', icon: Moon },
    DAILY_PROMPT: { label: 'Daily Prompt', icon: MessageCircle },
    POLL: { label: 'Poll', icon: BarChart3, emoji: '📊' },
    RANDOMIZER: { label: 'Now Spinning: Randomized', icon: Shuffle },
    listing_sale: { label: 'For Sale', icon: ShoppingBag },
    listing_trade: { label: 'For Trade', icon: ArrowRightLeft },
  };
  const c = config[type] || config.NOW_SPINNING;
  const s = PILL_STYLES[type] || PILL_STYLES.NOW_SPINNING;
  const Icon = c.icon;
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border whitespace-nowrap ${s.bg} ${s.text} ${s.border}`}>
        {c.emoji ? <span className="text-xs leading-none">{c.emoji}</span> : <Icon className="w-3 h-3 shrink-0" />}
        {c.label}
      </span>
      {type === 'NOW_SPINNING' && mood && <MoodPill mood={mood} />}
    </span>
  );
};

const MoodPill = ({ mood }) => {
  const emoji = MOOD_EMOJI_MAP[mood] || '';
  const color = MOOD_COLOR_MAP[mood] || '#7e22ce';
  if (!mood) return null;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap"
      style={{ backgroundColor: color + '20', color }}
      data-testid="mood-pill-badge">
      {emoji} {mood}
    </span>
  );
};

const VariantTag = ({ variant, glass, ghost, gold, prefix, linkTo }) => {
  if (!variant) return null;
  const key = variant.toLowerCase().trim();
  const match = Object.keys(VARIANT_PILL_STYLES).find(k => key.includes(k));
  const style = match ? VARIANT_PILL_STYLES[match] : VARIANT_DEFAULT;
  const label = prefix ? `${prefix}: ${variant}` : variant;

  const linkClass = linkTo ? 'cursor-pointer transition-transform duration-150 hover:scale-105 active:scale-100' : '';
  // Mobile-only truncation: expand full on desktop (>1024px), truncate on mobile (<480px)
  const truncClass = 'variant-pill-responsive';

  const wrap = (content, testId) => {
    if (!linkTo) return content;
    return (
      <Link to={linkTo} className={`inline-flex ${linkClass}`} onClick={e => e.stopPropagation()} data-testid={`${testId}-link`}>
        {content}
      </Link>
    );
  };

  if (glass) {
    return wrap(
      <span className={`inline-flex items-center gap-1 text-[10px] sm:text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${truncClass}`}
        style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
        data-testid="variant-pill-glass">
        <span className="truncate">{label}</span>
      </span>,
      'variant-pill-glass'
    );
  }
  if (ghost) {
    return wrap(
      <span className={`inline-flex items-center gap-1 text-[10px] sm:text-[10px] font-medium px-2 py-0.5 rounded-full border border-stone-300 text-stone-400 bg-transparent ${truncClass}`}
        data-testid="variant-pill-ghost">
        <Disc className="w-2.5 h-2.5 shrink-0" />
        <span className="truncate">{label}</span>
      </span>,
      'variant-pill-ghost'
    );
  }
  if (gold) {
    return wrap(
      <span className={`inline-flex items-center gap-1 text-[10px] sm:text-[10px] font-bold px-2 py-0.5 rounded-full border border-amber-400 bg-gradient-to-r from-yellow-400/80 via-amber-400/80 to-yellow-500/80 text-amber-950 ${truncClass}`}
        data-testid="variant-pill-gold">
        <Disc className="w-2.5 h-2.5 shrink-0" />
        <span className="truncate">{label}</span>
      </span>,
      'variant-pill-gold'
    );
  }
  return wrap(
    <span className={`inline-flex items-center gap-1 text-[11px] sm:text-[11px] font-bold tracking-wide px-2.5 py-1 rounded-full ${truncClass}`}
      style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
      data-testid="variant-pill">
      <Disc className="w-3 h-3 shrink-0" />
      <span className="truncate">{label}</span>
    </span>,
    'variant-pill'
  );
};

const EditionTag = ({ number }) => {
  if (!number) return null;
  return (
    <span className="inline-flex items-center gap-1 mt-0.5 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
      style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
      data-testid="edition-pill">
      No. {number}
    </span>
  );
};

// Spinning vinyl disc — slides out from behind right side of album art sleeve
// High-fidelity grooved vinyl record — peeking behind album art
// Size presets: 'feed' (92px, 20px peek), 'prompt' (72px, 10px peek), 'small' (56px, 8px peek)
const VINYL_PRESETS = {
  feed:   { size: 92, peek: 20, offset: '-2px' },
  prompt: { size: 72, peek: 10, offset: '-2px' },
  small:  { size: 56, peek: 8,  offset: '-2px' },
};

const SpinningVinyl = ({ preset = 'feed' }) => {
  const { size, offset } = VINYL_PRESETS[preset] || VINYL_PRESETS.feed;
  const uid = `v${size}`;
  return (
    <div className="absolute top-1/2 -translate-y-1/2 z-[5] pointer-events-none" style={{ right: offset }} data-testid="spinning-vinyl-icon">
      <svg width={size} height={size} viewBox="0 0 92 92" fill="none" style={{ animation: 'vinylSpin 1.8s linear infinite', filter: 'drop-shadow(1px 1px 3px rgba(0,0,0,0.3))' }}>
        <defs>
          <radialGradient id={`vg${uid}`} cx="50%" cy="45%" r="50%">
            <stop offset="0%" stopColor="#2A2A2A" />
            <stop offset="100%" stopColor="#111" />
          </radialGradient>
          <radialGradient id={`sp${uid}`} cx="35%" cy="30%" r="45%">
            <stop offset="0%" stopColor="rgba(255,255,255,0.08)" />
            <stop offset="100%" stopColor="rgba(255,255,255,0)" />
          </radialGradient>
        </defs>
        <circle cx="46" cy="46" r="44" fill={`url(#vg${uid})`} />
        <circle cx="46" cy="46" r="43" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
        {[40,38,36,34,32,30,28,26,24,22,20,18,16].map((r, i) => (
          <circle key={r} cx="46" cy="46" r={r} fill="none"
            stroke={i % 3 === 0 ? 'rgba(60,60,60,0.7)' : 'rgba(40,40,40,0.5)'}
            strokeWidth={i % 2 === 0 ? '0.6' : '0.35'} />
        ))}
        <circle cx="46" cy="46" r="14" fill="#1E1E1E" />
        <circle cx="46" cy="46" r="12" fill="#DAA520" />
        <circle cx="46" cy="46" r="11.2" fill="none" stroke="rgba(0,0,0,0.15)" strokeWidth="0.5" />
        <circle cx="46" cy="46" r="3" fill="#1A1A1A" />
        <circle cx="46" cy="46" r="1.5" fill="#333" />
        <circle cx="46" cy="46" r="43" fill={`url(#sp${uid})`} />
      </svg>
    </div>
  );
};

// Wrapper: album art with peeking vinyl behind — proportional peek per card type
const AlbumWithVinyl = ({ children, showVinyl = true, preset = 'feed' }) => {
  const { peek } = VINYL_PRESETS[preset] || VINYL_PRESETS.feed;
  return (
    <div className="relative" style={{ paddingRight: showVinyl ? `${peek + 4}px` : 0 }}>
      {showVinyl && <SpinningVinyl preset={preset} />}
      {children}
    </div>
  );
};

// Live 4-bar equalizer with staggered bounce + honey glow — inline in streaming row
const LiveEqualizer = () => (
  <div className="flex items-end gap-[2px] shrink-0" style={{ height: '24px', width: '18px' }} data-testid="live-equalizer">
    <span className="w-[3px] rounded-full" style={{ background: '#FFB800', boxShadow: '0 0 4px rgba(255,184,0,0.5)', animation: 'eqBar1 0.8s ease-in-out infinite alternate', height: '40%' }} />
    <span className="w-[3px] rounded-full" style={{ background: '#FFB800', boxShadow: '0 0 4px rgba(255,184,0,0.5)', animation: 'eqBar2 0.6s ease-in-out infinite alternate', height: '70%' }} />
    <span className="w-[3px] rounded-full" style={{ background: '#FFB800', boxShadow: '0 0 4px rgba(255,184,0,0.5)', animation: 'eqBar3 0.9s ease-in-out infinite alternate', height: '50%' }} />
    <span className="w-[3px] rounded-full" style={{ background: '#FFB800', boxShadow: '0 0 4px rgba(255,184,0,0.5)', animation: 'eqBar4 0.7s ease-in-out infinite alternate', height: '60%' }} />
  </div>
);

// NOW_SPINNING card body
const NowSpinningCard = ({ post, onAlbumClick, imgPriority }) => {
  const record = post.record || {};
  const [lightboxOpen, setLightboxOpen] = React.useState(false);
  // Fallback: use post-level fields when record object is missing
  const coverUrl = record.cover_url || post.cover_url;
  const title = record.title || post.record_title || '';
  const artist = record.artist || post.record_artist || '';
  if (!coverUrl && !title && !post.caption) return null;
  const variantText = post.color_variant || record.color_variant || post.pressing_variant;
  const linkRecord = record.id ? record : { title, artist, cover_url: coverUrl };
  return (
    <AlbumLink record={linkRecord} onAlbumClick={onAlbumClick}>
      <div data-testid="now-spinning-card">
        <div className="flex justify-between items-start gap-3">
          {/* Left: album art + metadata */}
          <div className={`${post.photo_url ? 'flex-1 mr-2' : 'w-full'} min-w-0`}>
            <div className="flex gap-4 items-start">
              {coverUrl ? (
                <div className="shrink-0" style={{ overflow: 'visible' }}>
                  <AlbumWithVinyl>
                    <AlbumArt src={coverUrl} alt={`${artist} ${title}${variantText ? ` ${variantText}` : ''} vinyl record`} className="w-24 h-24 rounded-[10px] object-cover shadow-md album-art-hover relative z-[6]" priority={imgPriority} isUnofficial={record.is_unofficial} />
                    {post.honeypot_rating && (
                      <div className="absolute top-1 right-4 z-[7] px-1.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide"
                        style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(4px)', border: '1px solid #FFD700', color: '#FFD700' }}
                        data-testid="feed-rating-pill">
                        {post.honeypot_rating}
                      </div>
                    )}
                  </AlbumWithVinyl>
                  <StreamingLinks artist={artist} album={title} discogsId={record.discogs_id || post.discogs_id} showEqualizer />
                </div>
              ) : (
                <div className="w-24 h-24 rounded-lg bg-vinyl-black flex items-center justify-center shrink-0">
                  <Disc className="w-10 h-10 text-honey animate-spin" style={{ animationDuration: '3s' }} />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-heading text-lg leading-tight truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{title}</p>
                <p className="text-sm text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{artist}</p>
                <div className="flex flex-wrap gap-1 mt-1" data-testid="card-meta-pills">
                  {variantText && <VariantTag variant={variantText} linkTo={variantLink(record)} />}
                  {(record.edition_number || post.edition_number) && <EditionTag number={record.edition_number || post.edition_number} />}
                  {!variantText && record.format && record.format !== 'Vinyl' && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full border border-stone-200 text-stone-500 bg-stone-50" data-testid="format-pill">
                      <Disc className="w-2.5 h-2.5" /> {record.format}
                    </span>
                  )}
                  {record.is_unofficial && <UnofficialPill variant="inline" />}
                </div>
                {post.track && <p className="text-xs text-honey-amber mt-1" data-testid="track-name">Track: {post.track}</p>}
              </div>
            </div>
          </div>

          {/* Right: user-uploaded photo */}
          {post.photo_url && (
            <div className="shrink-0">
              <img
                src={resolveImageUrl(post.photo_url)}
                alt="User photo"
                className="w-20 h-20 sm:w-24 sm:h-24 rounded-lg object-cover cursor-pointer hover:opacity-90 transition-opacity border border-stone-200/60 shadow-sm"
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setLightboxOpen(true); }}
                loading="lazy"
                data-testid="user-photo-thumb"
                onError={(e) => {
                  if (isLegacyUploadUrl(post.photo_url)) {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<div class="migration-placeholder w-20 h-20 sm:w-24 sm:h-24 rounded-lg"><span class="migration-placeholder-text">migration in progress</span></div>';
                  } else {
                    e.target.style.display = 'none';
                  }
                }}
              />
            </div>
          )}
        </div>
        {post.caption && <p className="text-sm mt-2"><MentionText text={post.caption} /></p>}
        {post.photo_url && (
          <PhotoLightbox
            photos={[post.photo_url]}
            initialIndex={0}
            open={lightboxOpen}
            onClose={() => setLightboxOpen(false)}
          />
        )}
      </div>
    </AlbumLink>
  );
};

// NEW_HAUL card body — handles both manual hauls and auto-bundled collection adds
const NewHaulCard = ({ post, onAlbumClick, imgPriority }) => {
  const [expanded, setExpanded] = React.useState(false);
  const [lightboxOpen, setLightboxOpen] = React.useState(false);
  const bundle = post.bundle_records;
  const photoUrl = post.image_url || (post.haul && post.haul.image_url);
  
  // Auto-bundle flow: stacked album art grid
  if (bundle && bundle.length > 0) {
    const shown = expanded ? bundle : bundle.slice(0, 4);
    const extra = bundle.length - 4;
    return (
      <div data-testid="haul-bundle-card">
        <div className="flex justify-between items-start gap-3">
          <div className={`${photoUrl ? 'flex-1 mr-2' : 'w-full'} min-w-0`}>
            {post.caption && <p className="text-sm mb-3"><MentionText text={post.caption} /></p>}
            <div className="grid grid-cols-4 gap-1.5">
              {shown.map((item, idx) => (
                <AlbumLink key={idx} record={item} onAlbumClick={onAlbumClick}>
                  <div className="relative group/cover">
                    <AlbumArt src={item.cover_url} alt={`${item.artist} - ${item.title}`} 
                      className="w-full aspect-square rounded-lg object-cover border border-stone-200/60" isUnofficial={item.is_unofficial} />
                    {item.color_variant && (
                      <div className="absolute bottom-1 left-1 right-1 z-[6]">
                        <span className="inline-block max-w-full truncate text-[8px] font-bold uppercase tracking-wide px-1.5 py-px rounded-full"
                          style={{ background: 'rgba(255,215,0,0.25)', backdropFilter: 'blur(10px)', WebkitBackdropFilter: 'blur(10px)', color: '#fff', textShadow: '0 1px 2px rgba(0,0,0,0.5)', border: '1.5px solid rgba(218,165,32,0.6)', boxShadow: '0 2px 8px rgba(0,0,0,0.2)' }}
                          data-testid={`haul-variant-pill-${idx}`}>
                          {item.color_variant}
                        </span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent rounded-lg opacity-0 group-hover/cover:opacity-100 transition-opacity flex items-end p-1.5">
                      <div className="min-w-0">
                        <p className="text-[10px] font-medium text-white truncate">{item.title}</p>
                        <p className="text-[9px] text-white/70 truncate">{item.artist}</p>
                      </div>
                    </div>
                  </div>
                </AlbumLink>
              ))}
              {!expanded && extra > 0 && (
                <button
                  onClick={(e) => { e.stopPropagation(); setExpanded(true); }}
                  className="aspect-square rounded-lg flex items-center justify-center text-sm font-bold"
                  style={{ background: 'rgba(232,168,32,0.12)', color: '#996012', border: '1px dashed rgba(200,134,26,0.3)' }}
                  data-testid="haul-bundle-expand"
                >
                  +{extra} more
                </button>
              )}
            </div>
            {expanded && bundle.length > 4 && (
              <button onClick={() => setExpanded(false)} className="text-xs text-muted-foreground mt-2 hover:underline" data-testid="haul-bundle-collapse">
                Show less
              </button>
            )}
          </div>
          {photoUrl && (
            <div className="shrink-0">
              <img
                src={resolveImageUrl(photoUrl)}
                alt="Haul photo"
                className="w-20 h-20 sm:w-24 sm:h-24 rounded-lg object-cover cursor-pointer hover:opacity-90 transition-opacity border border-stone-200/60 shadow-sm"
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setLightboxOpen(true); }}
                loading="lazy"
                data-testid="user-photo-thumb"
                onError={(e) => {
                  if (isLegacyUploadUrl(photoUrl)) {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<div class="migration-placeholder w-20 h-20 sm:w-24 sm:h-24 rounded-lg"><span class="migration-placeholder-text">migration in progress</span></div>';
                  } else { e.target.style.display = 'none'; }
                }}
              />
            </div>
          )}
        </div>
        {photoUrl && (
          <PhotoLightbox photos={[photoUrl]} initialIndex={0} open={lightboxOpen} onClose={() => setLightboxOpen(false)} />
        )}
      </div>
    );
  }
  
  // Manual haul flow (from composer)
  const haul = post.haul;

  // Fallback: no haul object but post has flat fields (seeded posts)
  if (!haul) {
    const coverUrl = post.cover_url;
    const title = post.record_title || '';
    const artist = post.record_artist || '';
    if (!coverUrl && !title && !post.caption) return null;
    // Render as a single-item haul card using flat fields
    if (coverUrl || title) {
      const fallbackRecord = { title, artist, cover_url: coverUrl };
      return (
        <AlbumLink record={fallbackRecord} onAlbumClick={onAlbumClick}>
          <div data-testid="new-haul-card">
            <div className="flex gap-4 items-start">
              {coverUrl ? (
                <div className="shrink-0">
                  <AlbumArt src={coverUrl} alt={`${artist} ${title} vinyl record`} className="w-24 h-24 rounded-[10px] object-cover shadow-md" priority={imgPriority} />
                </div>
              ) : (
                <div className="w-24 h-24 rounded-lg bg-pink-50 flex items-center justify-center shrink-0">
                  <Package className="w-10 h-10 text-pink-300" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-heading text-lg leading-tight truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{title}</p>
                <p className="text-sm text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{artist}</p>
                {post.caption && <p className="text-sm mt-2"><MentionText text={post.caption} /></p>}
              </div>
            </div>
          </div>
        </AlbumLink>
      );
    }
    return <p className="text-sm"><MentionText text={post.caption} /></p>;
  }

  const items = haul.items || [];
  return (
    <div data-testid="new-haul-card">
      <div className="flex justify-between items-start gap-3">
        <div className={`${photoUrl ? 'flex-1 mr-2' : 'w-full'} min-w-0`}>
          {haul.store_name && <p className="text-sm text-amber-700 font-medium mb-2">📍 {haul.store_name}</p>}
          {post.caption && <p className="text-sm mb-3"><MentionText text={post.caption} /></p>}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {items.slice(0, 6).map((item, idx) => (
              <AlbumLink key={idx} record={item} onAlbumClick={onAlbumClick}>
                <div className="flex items-center gap-2 bg-amber-50 rounded-lg p-2">
                  <AlbumArt src={item.cover_url} alt={`${item.artist} ${item.title}${item.color_variant ? ` ${item.color_variant}` : ''} vinyl record`} className="w-10 h-10 rounded object-cover" isUnofficial={item.is_unofficial} />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium truncate">{item.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{item.artist}</p>
                    <VariantTag variant={item.color_variant} linkTo={item.discogs_id ? `/variant/${item.discogs_id}` : undefined} />
                  </div>
                </div>
              </AlbumLink>
            ))}
          </div>
          {items.length > 6 && <p className="text-xs text-muted-foreground mt-2">+ {items.length - 6} more records</p>}
        </div>
        {photoUrl && (
          <div className="shrink-0">
            <img
              src={resolveImageUrl(photoUrl)}
              alt="Haul photo"
              className="w-20 h-20 sm:w-24 sm:h-24 rounded-lg object-cover cursor-pointer hover:opacity-90 transition-opacity border border-stone-200/60 shadow-sm"
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); setLightboxOpen(true); }}
              loading="lazy"
              data-testid="user-photo-thumb"
              onError={(e) => {
                if (isLegacyUploadUrl(photoUrl)) {
                  e.target.style.display = 'none';
                  e.target.parentElement.innerHTML = '<div class="migration-placeholder w-20 h-20 sm:w-24 sm:h-24 rounded-lg"><span class="migration-placeholder-text">migration in progress</span></div>';
                } else { e.target.style.display = 'none'; }
              }}
            />
          </div>
        )}
      </div>
      {photoUrl && (
        <PhotoLightbox photos={[photoUrl]} initialIndex={0} open={lightboxOpen} onClose={() => setLightboxOpen(false)} />
      )}
    </div>
  );
};

// ISO card body
const ISOCard = ({ post, onAlbumClick }) => {
  const iso = post.iso;
  const intent = post.intent;

  // Fallback: build iso-like data from flat post fields when iso object is missing
  const rawIso = iso || {
    album: post.record_title || '',
    artist: post.record_artist || '',
    cover_url: post.cover_url,
    color_variant: post.color_variant,
    pressing_notes: post.pressing_notes,
  };
  // Merge: prefer iso.color_variant, fall back to post.color_variant
  const isoData = {
    ...rawIso,
    color_variant: rawIso.color_variant || post.color_variant || '',
  };

  if (!iso && !post.cover_url && !post.record_title && !post.caption) {
    return <p className="text-sm"><MentionText text={post.caption} /></p>;
  }

  const isoRecord = { title: isoData.album, artist: isoData.artist, discogs_id: isoData.discogs_id, cover_url: isoData.cover_url, year: isoData.year };
  return (
    <AlbumLink record={isoRecord} onAlbumClick={onAlbumClick}>
      <div className="relative bg-[#FAF6EE] border border-[#C8861A]/15 rounded-xl p-4 hover:border-[#C8861A]/40 transition-colors" data-testid="iso-card">
        {/* Intent Badge */}
        {intent && (
          <span
            className="absolute top-3 right-3 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold z-10"
            style={intent === 'dreaming'
              ? { background: 'rgba(240,240,248,0.8)', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)', border: '1px solid rgba(200,200,220,0.35)', color: '#6B7280' }
              : { background: 'rgba(255,215,0,0.15)', border: '1px solid rgba(218,165,32,0.3)', color: '#92702A', boxShadow: '0 0 8px rgba(218,165,32,0.15)' }
            }
            data-testid={`iso-intent-${intent}`}
          >
            {intent === 'dreaming' ? '☁️ Just Dreaming' : '🔥 Actively Seeking'}
          </span>
        )}
        <div className="flex items-start gap-3">
          <div className="relative shrink-0">
            {isoData.cover_url ? (
              <AlbumArt src={isoData.cover_url} alt={`${isoData.artist} ${isoData.album}${isoData.color_variant ? ` ${isoData.color_variant}` : ''} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow-sm" isUnofficial={isoData.is_unofficial} />
            ) : (
              <div className="w-14 h-14 rounded-lg bg-[#C8861A]/10 flex items-center justify-center"><Search className="w-5 h-5 text-[#C8861A]/50" /></div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="min-w-0 pr-24">
              <p className="font-heading text-lg truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{isoData.album}</p>
              <p className="text-sm text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{isoData.artist}</p>
            </div>
            {isoData.color_variant && (
              <div className="mt-1.5" data-testid="iso-pressing">
                <VariantTag variant={isoData.color_variant} linkTo={isoData.discogs_id ? `/variant/${isoData.discogs_id}` : undefined} />
              </div>
            )}
            {isoData.pressing_notes && !(/^(mint|near mint|nm|m|vg|vg\+|g\+|g|f|p|nm\/m|near mint \/ mint)/i.test(isoData.pressing_notes.trim())) && (
              <p className="text-xs text-[#8A6B4A]" data-testid="iso-notes">Notes: {isoData.pressing_notes}</p>
            )}
            {isoData.condition_pref && <p className="text-xs text-[#8A6B4A]" data-testid="iso-condition">Condition: {isoData.condition_pref}</p>}
            {(isoData.target_price_min || isoData.target_price_max) && (
              <p className="text-xs text-[#8A6B4A] mt-0.5">Budget: {isoData.target_price_min && isoData.target_price_max ? `$${isoData.target_price_min} – $${isoData.target_price_max}` : isoData.target_price_max ? `Up to $${isoData.target_price_max}` : isoData.target_price_min ? `From $${isoData.target_price_min}` : ''}</p>
            )}
            {isoData.is_unofficial && <UnofficialPill variant="inline" className="mt-1.5" />}
          </div>
        </div>
        {post.caption && <p className="text-sm mt-3"><MentionText text={post.caption} /></p>}
        {isoData.is_unofficial && (
          <div className="mt-3 px-3 py-2 rounded-lg text-[11px] leading-relaxed" style={{ background: 'rgba(74,74,74,0.05)', border: '1px solid rgba(74,74,74,0.1)', color: '#6B6B6B' }} data-testid="unofficial-disclaimer">
            <span className="font-semibold text-stone-500">NOTICE:</span> This release is identified as &lsquo;Unofficial.&rsquo; The Hive facilitates the secondary market trade of these items for archival and collection purposes.
          </div>
        )}
      </div>
    </AlbumLink>
  );
};

// ADDED_TO_COLLECTION card body
const AddedToCollectionCard = ({ post, onAlbumClick, imgPriority }) => {
  const record = post.record || {};
  // Fallback: use post-level fields when record object is missing
  const coverUrl = record.cover_url || post.cover_url;
  const title = record.title || post.record_title || '';
  const artist = record.artist || post.record_artist || '';
  if (!coverUrl && !title && !post.caption) return null;
  const variantText = post.color_variant || record.color_variant;
  const linkRecord = record.id ? record : { title, artist, cover_url: coverUrl };
  return (
    <AlbumLink record={linkRecord} onAlbumClick={onAlbumClick}>
      <div className="flex gap-3 items-center" data-testid="added-card">
        <div className="shrink-0 pr-2">
          <AlbumWithVinyl preset="small">
            {coverUrl ? (
              <AlbumArt src={coverUrl} alt={`${artist} ${title}${variantText ? ` ${variantText}` : ''} vinyl record`} className="w-16 h-16 rounded-[10px] object-cover shadow relative z-[6]" priority={imgPriority} isUnofficial={record.is_unofficial} />
            ) : (
              <div className="w-16 h-16 rounded-[10px] bg-green-50 flex items-center justify-center relative z-[6]">
                <Plus className="w-6 h-6 text-green-300" />
              </div>
            )}
          </AlbumWithVinyl>
        </div>
        <div className="min-w-0">
          <p className="font-medium truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{title}</p>
          <p className="text-sm text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{artist}</p>
          <div className="flex flex-wrap gap-1 mt-1" data-testid="card-meta-pills">
            {variantText && <VariantTag variant={variantText} linkTo={variantLink(record)} />}
            {(record.edition_number || post.edition_number) && <EditionTag number={record.edition_number || post.edition_number} />}
            {record.is_unofficial && <UnofficialPill variant="inline" />}
          </div>
        </div>
      </div>
    </AlbumLink>
  );
};

// WEEKLY_WRAP card body
const WeeklyWrapCard = ({ post }) => {
  const content = post.caption || post.content || '';
  return (
    <div className="bg-gradient-to-br from-purple-50 to-honey/10 rounded-lg p-4" data-testid="weekly-wrap-card">
      <p className="text-sm font-medium text-purple-700"><MentionText text={content} /></p>
    </div>
  );
};

// VINYL_MOOD card body
const VinylMoodCard = ({ post, onAlbumClick, imgPriority }) => {
  const record = post.record || {};
  // Fallback: use post-level fields when record object is missing
  const coverUrl = record.cover_url || post.cover_url;
  const title = record.title || post.record_title || '';
  const artist = record.artist || post.record_artist || '';
  const mood = post.mood || '';
  const emoji = MOOD_EMOJI_MAP[mood] || '';
  const color = MOOD_COLOR_MAP[mood] || '#7e22ce';
  const linkRecord = record.id ? record : { title, artist, cover_url: coverUrl };
  const hasAlbum = coverUrl || title;
  return (
    <div data-testid="vinyl-mood-card">
      <div className="inline-block px-4 py-2 rounded-full text-lg font-heading mb-2" style={{ backgroundColor: color + '26', color }}>
        {emoji} {mood}
      </div>
      {hasAlbum && (
        <AlbumLink record={linkRecord} onAlbumClick={onAlbumClick}>
          <div className="flex gap-3 items-center mt-2 rounded-lg p-2" style={{ backgroundColor: color + '15' }}>
            {coverUrl ? (
              <AlbumArt src={coverUrl} alt={`${artist} ${title}${record.color_variant ? ` ${record.color_variant}` : ''} vinyl record`} className="w-10 h-10 rounded object-cover" priority={imgPriority} isUnofficial={record.is_unofficial} />
            ) : (
              <div className="w-10 h-10 rounded flex items-center justify-center" style={{ backgroundColor: color + '20' }}>
                <Moon className="w-5 h-5" style={{ color }} />
              </div>
            )}
            <div className="min-w-0">
              <p className="text-sm font-medium truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{title}</p>
              <p className="text-xs text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{artist}</p>
            </div>
          </div>
        </AlbumLink>
      )}
      {post.caption && <p className="text-sm mt-2"><MentionText text={post.caption} /></p>}
    </div>
  );
};

// DAILY_PROMPT card body
const DailyPromptPostCard = ({ post, imgPriority, onAlbumClick }) => {
  const promptRecord = post.record || {
    discogs_id: post.discogs_id,
    title: post.record_title,
    artist: post.record_artist,
    cover_url: post.cover_url,
    color_variant: post.color_variant,
  };
  return (
  <div data-testid="daily-prompt-post-card">
    <p className="text-sm italic text-amber-700 mb-3">{post.prompt_text}</p>
    <AlbumLink record={promptRecord} onAlbumClick={onAlbumClick}>
    <div className="flex gap-4 items-start bg-amber-50/60 rounded-lg p-3">
      {post.cover_url ? (
        <div className="shrink-0 pr-2">
          <AlbumWithVinyl preset="prompt">
            <AlbumArt src={post.cover_url} alt={`${post.record_artist} ${post.record_title}${post.color_variant ? ` ${post.color_variant}` : ''} vinyl record`} className="w-20 h-20 rounded-[10px] object-cover shadow-md relative z-[6]" priority={imgPriority} isUnofficial={post.is_unofficial} />
            {post.honeypot_rating && (
              <div className="absolute top-1 right-1 z-[7] px-1.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide"
              style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(4px)', border: '1px solid #FFD700', color: '#FFD700' }}
              data-testid="feed-rating-pill">
              🍯 {post.honeypot_rating}
            </div>
          )}
          </AlbumWithVinyl>
        </div>
      ) : (
        <div className="w-20 h-20 rounded-lg bg-amber-100 flex items-center justify-center"><Disc className="w-8 h-8 text-amber-300" /></div>
      )}
      <div className="flex-1 min-w-0">
        <p className="font-heading text-lg leading-tight truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{post.record_title}</p>
        <p className="text-sm text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{post.record_artist}</p>
        <div className="flex flex-wrap gap-1 mt-1" data-testid="card-meta-pills">
          {(post.color_variant || post.pressing_variant) && <VariantTag variant={post.color_variant || post.pressing_variant} linkTo={variantLink(post.record)} />}
        </div>
      </div>
    </div>
    </AlbumLink>
    {post.caption && <p className="text-sm mt-3"><MentionText text={post.caption} /></p>}
  </div>
  );
};

// NOTE card body
const NoteCard = ({ post, onAlbumClick }) => {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  return (
    <div data-testid="note-card">
      <p className="text-sm whitespace-pre-wrap"><MentionText text={post.caption || post.content} /></p>
      {post.record && (
        <AlbumLink record={post.record} onAlbumClick={onAlbumClick}>
          <div className="flex items-center gap-2.5 bg-stone-50 rounded-lg px-3 py-2 mt-3" data-testid="note-record-tag">
            {post.record.cover_url ? (
              <AlbumArt src={post.record.cover_url} alt={`${post.record.artist} ${post.record.title}${post.record.color_variant ? ` ${post.record.color_variant}` : ''} vinyl record`} className="w-10 h-10 rounded object-cover shadow-sm" isUnofficial={post.record.is_unofficial} />
            ) : (
              <div className="w-10 h-10 rounded bg-stone-200 flex items-center justify-center"><Disc className="w-5 h-5 text-stone-400" /></div>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium truncate">{post.record.title}</p>
              <p className="text-xs text-muted-foreground truncate">{post.record.artist}</p>
            </div>
          </div>
        </AlbumLink>
      )}
      {post.image_url && (
        <>
          <img
            src={resolveImageUrl(post.image_url)} alt={`${post.record_artist || 'User'} ${post.record_title || 'post'} vinyl record`}
            className="w-full rounded-lg mt-3 object-cover max-h-80 cursor-pointer"
            onClick={() => setLightboxOpen(true)}
            onError={(e) => {
              if (isLegacyUploadUrl(post.image_url)) {
                e.target.outerHTML = '<div class="migration-placeholder w-full rounded-lg mt-3"><span class="migration-placeholder-text">migration in progress</span></div>';
              } else {
                e.target.style.display = 'none';
              }
            }}
          />
          <PhotoLightbox
            photos={[post.image_url]}
            initialIndex={0}
            open={lightboxOpen}
            onClose={() => setLightboxOpen(false)}
          />
        </>
      )}
    </div>
  );
};

// POLL card body — "Blind" voting UX with Honey Gold branding
const PollCard = ({ post }) => {
  const { user, token, API } = useAuth();
  const [userVote, setUserVote] = useState(post.poll_user_vote);
  const [results, setResults] = useState(post.poll_results || null);
  const [totalVotes, setTotalVotes] = useState(post.poll_total_votes || 0);
  const [voting, setVoting] = useState(false);
  const [justVoted, setJustVoted] = useState(false);
  const [peeking, setPeeking] = useState(false); // creator peek at results without voting
  const hasVoted = userVote !== null && userVote !== undefined;
  const isCreator = user?.id === post.user_id;
  const showResults = hasVoted || results || peeking;
  const options = post.poll_options || [];

  const handleVote = async (idx) => {
    if (hasVoted || voting || peeking) return;
    setVoting(true);
    try {
      const r = await axios.post(`${API}/polls/${post.id}/vote`, { option_index: idx }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUserVote(r.data.user_vote);
      setResults(r.data.results);
      setTotalVotes(r.data.total_votes);
      setJustVoted(true);
      setPeeking(false);
    } catch (e) {
      if (e.response?.status === 409) setUserVote(idx);
    }
    setVoting(false);
  };

  const handlePeek = async () => {
    setPeeking(true);
    try {
      const r = await axios.get(`${API}/polls/${post.id}/results`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setResults(r.data.results);
      setTotalVotes(r.data.total_votes);
    } catch { /* silent */ }
  };

  const handleBackToVote = () => {
    setPeeking(false);
    setResults(null);
  };

  return (
    <div data-testid="poll-card" className="space-y-2.5">
      <p className="font-heading text-base leading-snug" style={{ color: '#3A2A0A' }}>{post.poll_question}</p>
      <div className="space-y-1.5 pt-0.5">
        {options.map((opt, i) => {
          const voted = showResults;
          const r = results?.[i];
          const pct = r?.percentage ?? (voted ? 0 : null);
          const isMyChoice = userVote === i;
          return (
            <button
              key={i}
              data-testid={`poll-option-${i}`}
              disabled={voted || voting}
              onClick={() => handleVote(i)}
              className={`w-full text-left relative rounded-lg px-3.5 py-2.5 text-sm transition-all overflow-hidden ${
                voted ? 'cursor-default' : 'cursor-pointer active:scale-[0.99]'
              }`}
              style={
                voted
                  ? { border: isMyChoice ? '2px solid #DAA520' : '1px solid #E7E5E4', background: isMyChoice ? 'rgba(218,165,32,0.06)' : '#FAFAF9' }
                  : { border: '1px solid #E7E5E4', background: '#FAFAF9' }
              }
              onMouseEnter={e => { if (!voted) { e.currentTarget.style.borderColor = '#DAA520'; e.currentTarget.style.background = 'rgba(218,165,32,0.06)'; } }}
              onMouseLeave={e => { if (!voted) { e.currentTarget.style.borderColor = '#E7E5E4'; e.currentTarget.style.background = '#FAFAF9'; } }}
            >
              {/* Honey Gold progress bar */}
              {voted && (
                <div
                  className="absolute inset-y-0 left-0 rounded-l-lg"
                  style={{
                    width: `${pct || 0}%`,
                    background: isMyChoice
                      ? 'linear-gradient(90deg, rgba(218,165,32,0.25), rgba(218,165,32,0.15))'
                      : 'linear-gradient(90deg, rgba(218,165,32,0.12), rgba(218,165,32,0.06))',
                    transition: 'width 0.7s cubic-bezier(0.22, 1, 0.36, 1)',
                  }}
                />
              )}
              <div className="relative flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 font-medium truncate" style={{ color: '#3A2A0A' }}>
                  {voted && isMyChoice && (
                    <span className="inline-flex items-center justify-center w-4 h-4 rounded-full shrink-0" style={{ background: '#DAA520' }}>
                      <Check className="w-2.5 h-2.5 text-white" />
                    </span>
                  )}
                  {opt}
                </span>
                {voted && <span className="text-xs font-semibold shrink-0 tabular-nums" style={{ color: '#8B6914' }}>{pct ?? 0}%</span>}
              </div>
            </button>
          );
        })}
      </div>
      <div className="flex items-center justify-between pt-0.5">
        {showResults ? (
          <p className="text-xs" style={{ color: '#A8A29E' }} data-testid="poll-total-votes">
            {totalVotes} {totalVotes === 1 ? 'person' : 'people'} responded
          </p>
        ) : (
          <span />
        )}
        {/* Creator-only: See Results / Back to Vote */}
        {isCreator && !hasVoted && (
          peeking ? (
            <button
              onClick={handleBackToVote}
              className="text-xs font-medium transition-opacity hover:opacity-80"
              style={{ color: '#DAA520' }}
              data-testid="poll-back-to-vote"
            >
              Back to vote
            </button>
          ) : (
            <button
              onClick={handlePeek}
              className="text-xs font-medium transition-opacity hover:opacity-80"
              style={{ color: '#DAA520' }}
              data-testid="poll-see-results"
            >
              See results
            </button>
          )
        )}
      </div>
    </div>
  );
};


// Main renderer
// Listing post card (auto-created when a listing is made)
const ListingPostCard = ({ post }) => {
  const isSale = post.post_type === 'listing_sale';
  const variantText = post.color_variant || post.pressing_variant;
  return (
    <Link to={post.listing_id ? `/honeypot/listing/${post.listing_id}` : '/honeypot'} className="block" data-testid={`listing-post-${post.id}`}>
      <div className="flex gap-3 items-center bg-stone-50 rounded-xl p-3 hover:bg-stone-100 transition-colors">
        {post.cover_url ? (
          <div className="shrink-0">
            <AlbumArt src={post.cover_url} alt={`${post.record_artist || 'Artist'} ${post.record_title || 'Album'}${variantText ? ` ${variantText}` : ''} vinyl record`} className="w-16 h-16 rounded-[10px] object-cover shadow-sm" isUnofficial={post.is_unofficial} />
          </div>
        ) : (
          <div className="w-16 h-16 rounded-lg bg-amber-100 flex items-center justify-center"><Disc className="w-6 h-6 text-amber-400" /></div>
        )}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{post.record_title}</p>
          <p className="text-xs text-muted-foreground truncate">{post.record_artist}</p>
          <div className="flex flex-wrap gap-1 mt-1" data-testid="card-meta-pills">
            {variantText && <VariantTag variant={variantText} linkTo={variantLink(post.record)} />}
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-teal-100/60 text-teal-700`}>
              {isSale ? <ShoppingBag className="w-3 h-3" /> : <ArrowRightLeft className="w-3 h-3" />}
              {isSale ? 'For Sale' : 'For Trade'}
            </span>
          </div>
          {post.pressing_notes && <p className="text-xs italic text-stone-500 font-serif mt-1 truncate">{post.pressing_notes.length > 60 ? post.pressing_notes.slice(0, 60) + '...' : post.pressing_notes}</p>}
        </div>
      </div>
    </Link>
  );
};

const PostCardBody = ({ post, onAlbumClick, imgPriority }) => {
  switch (post.post_type) {
    case 'NOW_SPINNING': return <NowSpinningCard post={post} onAlbumClick={onAlbumClick} imgPriority={imgPriority} />;
    case 'NEW_HAUL': return <NewHaulCard post={post} onAlbumClick={onAlbumClick} imgPriority={imgPriority} />;
    case 'ISO': return <ISOCard post={post} onAlbumClick={onAlbumClick} />;
    case 'NOTE': return <NoteCard post={post} onAlbumClick={onAlbumClick} />;
    case 'ADDED_TO_COLLECTION': return <AddedToCollectionCard post={post} onAlbumClick={onAlbumClick} imgPriority={imgPriority} />;
    case 'WEEKLY_WRAP': return <WeeklyWrapCard post={post} />;
    case 'VINYL_MOOD': return <VinylMoodCard post={post} onAlbumClick={onAlbumClick} imgPriority={imgPriority} />;
    case 'DAILY_PROMPT': return <DailyPromptPostCard post={post} onAlbumClick={onAlbumClick} imgPriority={imgPriority} />;
    case 'POLL': return <PollCard post={post} />;
    case 'RANDOMIZER': return <NowSpinningCard post={post} onAlbumClick={onAlbumClick} imgPriority={imgPriority} />;
    case 'listing_sale': return <ListingPostCard post={post} />;
    case 'listing_trade': return <ListingPostCard post={post} />;
    default:
      {
        const defRecord = post.record || {};
        const defCover = defRecord.cover_url || post.cover_url;
        const defTitle = defRecord.title || post.record_title || '';
        const defArtist = defRecord.artist || post.record_artist || '';
        const defLink = defRecord.id ? defRecord : { title: defTitle, artist: defArtist, cover_url: defCover };
        return (
          <div>
            {(defCover || defTitle) && (
              <AlbumLink record={defLink} onAlbumClick={onAlbumClick}>
                <div className="flex gap-3 items-center mb-2">
                  {defCover ? (
                    <AlbumArt src={defCover} alt={`${defArtist} ${defTitle} vinyl record`} className="w-14 h-14 rounded object-cover" isUnofficial={defRecord.is_unofficial} />
                  ) : (
                    <div className="w-14 h-14 rounded bg-stone-100 flex items-center justify-center"><Disc className="w-6 h-6 text-stone-400" /></div>
                  )}
                  <div className="min-w-0">
                    <p className="font-medium truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{defTitle}</p>
                    <p className="text-sm text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{defArtist}</p>
                  </div>
                </div>
              </AlbumLink>
            )}
            <p className="text-sm"><MentionText text={post.caption || post.content} /></p>
          </div>
        );
      }
  }
};

// Listing type badge (For Sale / For Trade) — shared across Explore, Honeypot, Search
const ListingTypeBadge = ({ type, price, size = 'sm' }) => {
  const isTrade = type === 'TRADE';
  const cls = size === 'xs'
    ? 'px-1.5 py-0.5 rounded text-[10px] font-bold'
    : 'px-2 py-0.5 rounded-full text-xs font-medium border';
  return (
    <span
      className={`${cls} ${isTrade ? 'bg-teal-100/60 text-teal-700 border-teal-200/50' : 'bg-green-100/60 text-green-700 border-green-200/50'}`}
      data-testid="listing-type-badge"
    >
      {isTrade ? 'Trade' : `$${price}`}
    </span>
  );
};

// Tag pill — shared across ISO cards, Hive feed, Profile, listing detail
const TAG_COLOR_MAP = {
  'OG Press':        'bg-amber-100/70 text-amber-800',
  'Factory Sealed':  'bg-emerald-100/70 text-emerald-800',
  'Any':             'bg-stone-100 text-stone-600',
  'Promo':           'bg-violet-100/70 text-violet-800',
};
const TAG_DEFAULT = 'bg-honey/15 text-honey-amber';

const TagPill = ({ tag }) => (
  <span
    className={`px-2 py-0.5 rounded-full text-xs font-medium ${TAG_COLOR_MAP[tag] || TAG_DEFAULT}`}
    data-testid={`tag-pill-${tag}`}
  >
    {tag}
  </span>
);

const NewFeatureBadge = () => {
  const s = PILL_STYLES.NEW_FEATURE;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${s.bg} ${s.text} ${s.border}`} data-testid="new-feature-badge">
      <span className="text-[10px]">&#10024;</span> New Feature
    </span>
  );
};

const FORMAT_ICONS = {
  Vinyl: Disc,
  CD: Circle,
  Cassette: null,
};

const FORMAT_STYLES = {
  Vinyl: 'bg-stone-100 text-stone-600 border-stone-200',
  CD: 'bg-blue-50 text-blue-600 border-blue-200',
  Cassette: 'bg-orange-50 text-orange-600 border-orange-200',
};

const FormatPill = ({ format }) => {
  if (!format) return null;
  const normalized = format.charAt(0).toUpperCase() + format.slice(1).toLowerCase();
  const key = Object.keys(FORMAT_STYLES).find(k => normalized.toLowerCase().includes(k.toLowerCase())) || 'Vinyl';
  const style = FORMAT_STYLES[key] || FORMAT_STYLES.Vinyl;
  const Icon = FORMAT_ICONS[key];
  const label = key;
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium border whitespace-nowrap ${style}`} data-testid="format-type-pill">
      {Icon && <Icon className="w-2.5 h-2.5" />}
      {!Icon && <span className="text-[9px]">&#x1F4FC;</span>}
      {label}
    </span>
  );
};

export { PostTypeBadge, PostCardBody, ListingTypeBadge, TagPill, NewFeatureBadge, VariantTag, PILL_STYLES, FormatPill };
