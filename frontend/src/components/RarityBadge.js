import React from 'react';
import { Disc } from 'lucide-react';

const TIER_CONFIG = {
  'Ultra Rare': { label: 'Ultra Rare', color: '#8B0000' },
  'Rare':       { label: 'Rare',       color: '#B8860B' },
  'Uncommon':   { label: 'Uncommon',   color: '#556B2F' },
  'Common':     { label: 'Common',     color: '#555' },
};

export const RarityPill = ({ tier, size = 'md' }) => {
  const cfg = TIER_CONFIG[tier] || TIER_CONFIG['Common'];
  const sizes = {
    sm: 'text-[9px] px-2 py-0.5 gap-1',
    md: 'text-[10px] px-2.5 py-1 gap-1.5',
    lg: 'text-xs px-3 py-1.5 gap-2',
  };

  return (
    <span
      className={`inline-flex items-center font-bold uppercase tracking-wider rounded-full ${sizes[size]}`}
      style={{
        background: 'rgba(255,215,0,0.2)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        color: cfg.color,
        letterSpacing: '0.5px',
        border: '2px solid #DAA520',
        boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)',
      }}
      data-testid="rarity-pill"
    >
      <Disc className={size === 'sm' ? 'w-2.5 h-2.5 opacity-40' : 'w-3 h-3 opacity-40'} />
      Global Variant Rarity: {cfg.label}
    </span>
  );
};

export const RarityCard = ({ rarity, label }) => {
  if (!rarity?.tier) return null;
  const cardLabel = label || 'Global Variant Rarity';

  return (
    <div
      className="rounded-2xl p-5"
      style={{
        background: 'rgba(255,215,0,0.08)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        border: '2px solid #DAA520',
        boxShadow: '0 8px 32px 0 rgba(0,0,0,0.05), inset 0 0 0 0.5px rgba(255,215,0,0.3)',
      }}
      data-testid="rarity-card"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Disc className="w-4 h-4 text-[#DAA520] opacity-50" />
          <span className="font-heading text-base font-bold text-vinyl-black">{cardLabel}</span>
        </div>
        <RarityPill tier={rarity.tier} size="md" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center" data-testid="rarity-owners">
          <p className="text-2xl font-heading font-bold text-vinyl-black">{(rarity.discogs_owners ?? 0).toLocaleString()}</p>
          <p className="text-[11px] text-muted-foreground uppercase tracking-wider mt-0.5">Owners</p>
        </div>
        <div className="text-center" data-testid="rarity-wantlist">
          <p className="text-2xl font-heading font-bold text-vinyl-black">{(rarity.discogs_wantlist ?? 0).toLocaleString()}</p>
          <p className="text-[11px] text-muted-foreground uppercase tracking-wider mt-0.5">Wantlist</p>
        </div>
        <div className="text-center" data-testid="rarity-listings">
          <p className="text-2xl font-heading font-bold text-vinyl-black">{(rarity.listings_available ?? 0).toLocaleString()}</p>
          <p className="text-[11px] text-muted-foreground uppercase tracking-wider mt-0.5">For Sale</p>
        </div>
      </div>
    </div>
  );
};
