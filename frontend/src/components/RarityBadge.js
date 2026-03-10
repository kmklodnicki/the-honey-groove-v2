import React from 'react';
import { Gem } from 'lucide-react';

const TIER_CONFIG = {
  'Ultra Rare': { bg: 'bg-gradient-to-r from-purple-600 to-fuchsia-500', text: 'text-white', glow: 'shadow-purple-400/40', ring: 'ring-purple-300' },
  'Very Rare':  { bg: 'bg-gradient-to-r from-amber-500 to-orange-500', text: 'text-white', glow: 'shadow-amber-400/40', ring: 'ring-amber-300' },
  'Rare':       { bg: 'bg-gradient-to-r from-sky-500 to-cyan-400', text: 'text-white', glow: 'shadow-sky-400/30', ring: 'ring-sky-300' },
  'Uncommon':   { bg: 'bg-emerald-100', text: 'text-emerald-700', glow: '', ring: 'ring-emerald-200' },
  'Common':     { bg: 'bg-stone-100', text: 'text-stone-600', glow: '', ring: 'ring-stone-200' },
};

export const RarityPill = ({ tier, size = 'md' }) => {
  const cfg = TIER_CONFIG[tier] || TIER_CONFIG['Common'];
  const isGlowing = ['Ultra Rare', 'Very Rare', 'Rare'].includes(tier);
  const sizes = {
    sm: 'text-[10px] px-2 py-0.5 gap-1',
    md: 'text-xs px-3 py-1 gap-1.5',
    lg: 'text-sm px-4 py-1.5 gap-2',
  };

  return (
    <span
      className={`inline-flex items-center font-bold uppercase tracking-wider rounded-full ${cfg.bg} ${cfg.text} ${sizes[size]} ${isGlowing ? `shadow-lg ${cfg.glow}` : ''}`}
      data-testid="rarity-pill"
    >
      <Gem className={size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4.5 h-4.5' : 'w-3.5 h-3.5'} />
      {tier}
    </span>
  );
};

export const RarityCard = ({ rarity }) => {
  if (!rarity?.tier) return null;
  const cfg = TIER_CONFIG[rarity.tier] || TIER_CONFIG['Common'];
  const isGlowing = ['Ultra Rare', 'Very Rare', 'Rare'].includes(rarity.tier);

  return (
    <div
      className={`rounded-2xl border p-5 ${isGlowing ? `ring-1 ${cfg.ring} shadow-lg ${cfg.glow}` : 'border-honey/20'}`}
      style={isGlowing ? { background: 'linear-gradient(135deg, rgba(255,248,230,0.8), rgba(255,240,210,0.6))' } : {}}
      data-testid="rarity-card"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Gem className="w-5 h-5 text-honey-amber" />
          <span className="font-heading text-lg font-bold text-vinyl-black">Rarity Score</span>
        </div>
        <RarityPill tier={rarity.tier} size="md" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center" data-testid="rarity-owners">
          <p className="text-2xl font-heading font-bold text-vinyl-black">{(rarity.discogs_owners ?? 0).toLocaleString()}</p>
          <p className="text-[11px] text-muted-foreground uppercase tracking-wider mt-0.5">Discogs Owners</p>
        </div>
        <div className="text-center" data-testid="rarity-wantlist">
          <p className="text-2xl font-heading font-bold text-vinyl-black">{(rarity.discogs_wantlist ?? 0).toLocaleString()}</p>
          <p className="text-[11px] text-muted-foreground uppercase tracking-wider mt-0.5">Discogs Wantlist</p>
        </div>
        <div className="text-center" data-testid="rarity-listings">
          <p className="text-2xl font-heading font-bold text-vinyl-black">{(rarity.listings_available ?? 0).toLocaleString()}</p>
          <p className="text-[11px] text-muted-foreground uppercase tracking-wider mt-0.5">Listings Available</p>
        </div>
      </div>
    </div>
  );
};

export default RarityPill;
