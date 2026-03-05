import React from 'react';
import { Link } from 'react-router-dom';
import { Disc, Package, Search, Moon, Plus, Music } from 'lucide-react';

const MOOD_EMOJI_MAP = {
  'Late Night': '\u{1F56F}\uFE0F', 'Good Morning': '\u2600\uFE0F', 'Sunday Morning': '\u2600\uFE0F',
  'Rainy Day': '\u{1F327}\uFE0F', 'Road Trip': '\u{1F697}', 'Golden Hour': '\u{1F305}',
  'Deep Focus': '\u{1F3A7}', 'Party Mode': '\u{1F942}', 'Lazy Afternoon': '\u{1F6CB}\uFE0F',
  'Melancholy': '\u{1F494}', 'Upbeat Vibes': '\u2728', 'Cozy Evening': '\u{1F9F8}', 'Workout': '\u{1F525}',
};
const MOOD_COLOR_MAP = {
  'Late Night': '#6a3a9a', 'Good Morning': '#e8a820', 'Sunday Morning': '#e8a820',
  'Rainy Day': '#4a7aaa', 'Road Trip': '#4a8a4a', 'Golden Hour': '#c8861a',
  'Deep Focus': '#2a6a2a', 'Party Mode': '#aa3a8a', 'Lazy Afternoon': '#aa7a3a',
  'Melancholy': '#5a5a8a', 'Upbeat Vibes': '#3a9a5a', 'Cozy Evening': '#aa5a2a', 'Workout': '#cc3a2a',
};

// Badge showing post type
const PostTypeBadge = ({ type, mood }) => {
  const config = {
    NOW_SPINNING: { label: 'Now Spinning', icon: Disc, bg: 'bg-honey/20 text-honey-amber' },
    NEW_HAUL: { label: 'New Haul', icon: Package, bg: 'bg-amber-100/60 text-amber-700' },
    ISO: { label: 'ISO', icon: Search, bg: 'bg-blue-100/60 text-blue-700' },
    ADDED_TO_COLLECTION: { label: 'Added', icon: Plus, bg: 'bg-green-100/60 text-green-700' },
    WEEKLY_WRAP: { label: 'Weekly Wrap', icon: Music, bg: 'bg-purple-100/60 text-purple-700' },
    VINYL_MOOD: { label: 'Vinyl Mood', icon: Moon, bg: 'bg-purple-100/60 text-purple-700' },
    DAILY_PROMPT: { label: 'Daily Prompt', icon: Disc, bg: 'bg-amber-100/60 text-amber-700' },
  };
  const c = config[type] || config.NOW_SPINNING;
  const Icon = c.icon;
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${c.bg}`}>
        <Icon className="w-3 h-3" />
        {c.label}
      </span>
      {/* Mood pill badge for Now Spinning posts */}
      {type === 'NOW_SPINNING' && mood && (
        <MoodPill mood={mood} />
      )}
    </span>
  );
};

// Small mood pill badge
const MoodPill = ({ mood }) => {
  const emoji = MOOD_EMOJI_MAP[mood] || '';
  const color = MOOD_COLOR_MAP[mood] || '#7e22ce';
  if (!mood) return null;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
      style={{ backgroundColor: color + '20', color }}
      data-testid="mood-pill-badge">
      {emoji} {mood}
    </span>
  );
};

// NOW_SPINNING card body
const NowSpinningCard = ({ post }) => {
  const record = post.record;
  if (!record) return null;
  return (
    <div className="flex gap-4 items-start" data-testid="now-spinning-card">
      {record.cover_url ? (
        <img src={record.cover_url} alt={record.title} className="w-24 h-24 rounded-lg object-cover shadow-md" />
      ) : (
        <div className="w-24 h-24 rounded-lg bg-vinyl-black flex items-center justify-center">
          <Disc className="w-10 h-10 text-honey animate-spin" style={{ animationDuration: '3s' }} />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="font-heading text-lg leading-tight">{record.title}</p>
        <p className="text-sm text-muted-foreground">{record.artist}</p>
        {post.track && <p className="text-xs text-honey-amber mt-1">Track: {post.track}</p>}
        {post.caption && <p className="text-sm mt-2">{post.caption}</p>}
      </div>
    </div>
  );
};

// NEW_HAUL card body
const NewHaulCard = ({ post }) => {
  const haul = post.haul;
  if (!haul) return <p className="text-sm">{post.caption}</p>;
  const items = haul.items || [];
  return (
    <div data-testid="new-haul-card">
      {haul.store_name && <p className="text-sm text-amber-700 font-medium mb-2">Found at {haul.store_name}</p>}
      {post.caption && <p className="text-sm mb-3">{post.caption}</p>}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {items.slice(0, 6).map((item, idx) => (
          <div key={idx} className="flex items-center gap-2 bg-amber-50 rounded-lg p-2">
            {item.cover_url ? <img src={item.cover_url} alt="" className="w-10 h-10 rounded object-cover" />
              : <div className="w-10 h-10 rounded bg-amber-200 flex items-center justify-center"><Disc className="w-5 h-5 text-amber-700" /></div>}
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium truncate">{item.title}</p>
              <p className="text-xs text-muted-foreground truncate">{item.artist}</p>
            </div>
          </div>
        ))}
      </div>
      {items.length > 6 && <p className="text-xs text-muted-foreground mt-2">+ {items.length - 6} more records</p>}
    </div>
  );
};

// ISO card body
const ISOCard = ({ post }) => {
  const iso = post.iso;
  if (!iso) return <p className="text-sm">{post.caption}</p>;
  return (
    <div className="bg-blue-50 rounded-lg p-4" data-testid="iso-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-heading text-lg">{iso.album}</p>
          <p className="text-sm text-muted-foreground">{iso.artist}</p>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${iso.status === 'FOUND' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>{iso.status}</span>
      </div>
      {iso.pressing_notes && <p className="text-xs mt-2 text-blue-700">Pressing: {iso.pressing_notes}</p>}
      {iso.condition_pref && <p className="text-xs text-blue-600">Condition: {iso.condition_pref}</p>}
      {(iso.target_price_min || iso.target_price_max) && (
        <p className="text-xs text-blue-600 mt-1">Budget: {iso.target_price_min ? `$${iso.target_price_min}` : '?'} – {iso.target_price_max ? `$${iso.target_price_max}` : '?'}</p>
      )}
      {post.caption && <p className="text-sm mt-3">{post.caption}</p>}
    </div>
  );
};

// ADDED_TO_COLLECTION card body
const AddedToCollectionCard = ({ post }) => {
  const record = post.record;
  if (!record) return <p className="text-sm">{post.caption}</p>;
  return (
    <div className="flex gap-3 items-center" data-testid="added-card">
      {record.cover_url ? <img src={record.cover_url} alt="" className="w-16 h-16 rounded-lg object-cover shadow" />
        : <div className="w-16 h-16 rounded-lg bg-green-100 flex items-center justify-center"><Plus className="w-6 h-6 text-green-600" /></div>}
      <div>
        <p className="font-medium">{record.title}</p>
        <p className="text-sm text-muted-foreground">{record.artist}</p>
      </div>
    </div>
  );
};

// WEEKLY_WRAP card body
const WeeklyWrapCard = ({ post }) => {
  const content = post.caption || post.content || '';
  return (
    <div className="bg-gradient-to-br from-purple-50 to-honey/10 rounded-lg p-4" data-testid="weekly-wrap-card">
      <p className="text-sm font-medium text-purple-700">{content}</p>
    </div>
  );
};

// VINYL_MOOD card body (legacy — kept for old posts)
const VinylMoodCard = ({ post }) => {
  const record = post.record;
  const mood = post.mood || '';
  const emoji = MOOD_EMOJI_MAP[mood] || '';
  const color = MOOD_COLOR_MAP[mood] || '#7e22ce';
  return (
    <div data-testid="vinyl-mood-card">
      <div className="inline-block px-4 py-2 rounded-full text-lg font-heading mb-2" style={{ backgroundColor: color + '26', color }}>
        {emoji} {mood}
      </div>
      {record && (
        <div className="flex gap-3 items-center mt-2 rounded-lg p-2" style={{ backgroundColor: color + '15' }}>
          {record.cover_url && <img src={record.cover_url} alt="" className="w-10 h-10 rounded object-cover" />}
          <div>
            <p className="text-sm font-medium">{record.title}</p>
            <p className="text-xs text-muted-foreground">{record.artist}</p>
          </div>
        </div>
      )}
      {post.caption && <p className="text-sm mt-2">{post.caption}</p>}
    </div>
  );
};

// DAILY_PROMPT card body
const DailyPromptPostCard = ({ post }) => (
  <div data-testid="daily-prompt-post-card">
    <p className="text-sm italic text-amber-700 mb-3">{post.prompt_text}</p>
    <div className="flex gap-4 items-start bg-amber-50/60 rounded-lg p-3">
      {post.cover_url ? (
        <img src={post.cover_url} alt="" className="w-20 h-20 rounded-lg object-cover shadow-md" />
      ) : (
        <div className="w-20 h-20 rounded-lg bg-amber-100 flex items-center justify-center"><Disc className="w-8 h-8 text-amber-300" /></div>
      )}
      <div className="flex-1 min-w-0">
        <p className="font-heading text-lg leading-tight">{post.record_title}</p>
        <p className="text-sm text-muted-foreground">{post.record_artist}</p>
      </div>
    </div>
    {post.caption && <p className="text-sm mt-3">{post.caption}</p>}
  </div>
);

// Main renderer
const PostCardBody = ({ post }) => {
  switch (post.post_type) {
    case 'NOW_SPINNING': return <NowSpinningCard post={post} />;
    case 'NEW_HAUL': return <NewHaulCard post={post} />;
    case 'ISO': return <ISOCard post={post} />;
    case 'ADDED_TO_COLLECTION': return <AddedToCollectionCard post={post} />;
    case 'WEEKLY_WRAP': return <WeeklyWrapCard post={post} />;
    case 'VINYL_MOOD': return <VinylMoodCard post={post} />;
    case 'DAILY_PROMPT': return <DailyPromptPostCard post={post} />;
    default:
      return (
        <div>
          {post.record && (
            <div className="flex gap-3 items-center mb-2">
              {post.record.cover_url && <img src={post.record.cover_url} alt="" className="w-14 h-14 rounded object-cover" />}
              <div>
                <p className="font-medium">{post.record.title}</p>
                <p className="text-sm text-muted-foreground">{post.record.artist}</p>
              </div>
            </div>
          )}
          <p className="text-sm">{post.caption || post.content}</p>
        </div>
      );
  }
};

export { PostTypeBadge, PostCardBody };
