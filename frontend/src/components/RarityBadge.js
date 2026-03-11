import React from 'react';
import { Disc } from 'lucide-react';
import { toast } from 'sonner';

const TIER_CONFIG = {
  'Grail':      { label: 'Grail',      color: '#FFF', bg: 'linear-gradient(135deg, #7B2FF2, #C8861A)', border: '#7B2FF2', glow: '0 0 12px rgba(123,47,242,0.4)' },
  'Ultra Rare': { label: 'Ultra Rare', color: '#FFF', bg: 'linear-gradient(135deg, #FF6B00, #FF9500)', border: '#FF6B00', glow: '0 0 10px rgba(255,107,0,0.3)' },
  'Rare':       { label: 'Rare',       color: '#FFF', bg: '#DC2626', border: '#DC2626', glow: 'none' },
  'Uncommon':   { label: 'Uncommon',   color: '#FFF', bg: '#2563EB', border: '#2563EB', glow: 'none' },
  'Common':     { label: 'Common',     color: '#FFF', bg: '#9CA3AF', border: '#9CA3AF', glow: 'none' },
  'Obscure':    { label: 'Obscure',    color: '#CBD5E1', bg: 'rgba(0,0,0,0.6)', border: '#475569', glow: 'none' },
};

// Pill-style tier display used on detail pages
const PILL_COLOR = {
  'Ultra Rare': '#8B0000',
  'Rare':       '#B8860B',
  'Uncommon':   '#556B2F',
  'Common':     '#555',
  'Grail':      '#7B2FF2',
  'Obscure':    '#475569',
};

export const RarityPill = ({ tier, size = 'md' }) => {
  const label = TIER_CONFIG[tier]?.label || tier || 'Common';
  const pillColor = PILL_COLOR[tier] || '#555';
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
        color: pillColor,
        letterSpacing: '0.5px',
        border: '2px solid #DAA520',
        boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)',
      }}
      data-testid="rarity-pill"
    >
      <Disc className={size === 'sm' ? 'w-2.5 h-2.5 opacity-40' : 'w-3 h-3 opacity-40'} />
      {label}
    </span>
  );
};


// Compact badge for collection cards — uses vivid color-coded backgrounds
export const RarityBadge = ({ label, size = 'sm' }) => {
  if (!label) return null;
  const cfg = TIER_CONFIG[label] || TIER_CONFIG['Common'];
  const isSmall = size === 'sm';
  return (
    <span
      className={`inline-flex items-center font-bold uppercase tracking-wider rounded-full whitespace-nowrap ${isSmall ? 'text-[9px] px-2 py-0.5' : 'text-[10px] px-2.5 py-0.5'}`}
      style={{
        background: cfg.bg,
        color: cfg.color,
        border: `1.5px solid ${cfg.border}`,
        boxShadow: cfg.glow,
        letterSpacing: '0.5px',
      }}
      data-testid={`rarity-badge-${label.toLowerCase().replace(/\s/g, '-')}`}
    >
      {cfg.label}
    </span>
  );
};

export const RarityCard = ({ rarity, label, honeypotListings, onForSaleClick, albumName, variantName, onNotifySubscribe }) => {
  if (!rarity?.tier) return null;
  const cardLabel = label || 'Global Variant Rarity';
  const useHoneypot = honeypotListings != null;
  const forSaleCount = useHoneypot ? honeypotListings : (rarity.listings_available ?? 0);
  const isEmptyHoneypot = useHoneypot && forSaleCount === 0;
  const forSaleLabel = useHoneypot
    ? (isEmptyHoneypot ? 'Notify me when listed' : `${forSaleCount} in Honeypot`)
    : 'For Sale';

  const handleNotifyClick = () => {
    const cleanVariant = variantName && variantName !== 'Standard' && variantName.trim() ? variantName.trim() : '';
    const displayName = cleanVariant ? `${albumName || 'this record'} (${cleanVariant})` : (albumName || 'this record');
    toast.success(`We'll notify you when ${displayName} is for sale!`, {
      duration: 3000,
      style: { border: '2px solid #DAA520', background: '#FFFDF5' },
    });
    if (onNotifySubscribe) onNotifySubscribe();
    if (onForSaleClick) onForSaleClick();
  };

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
        <div
          className={`text-center ${(onForSaleClick || isEmptyHoneypot) ? 'cursor-pointer hover:bg-honey/10 rounded-lg -m-1 p-1 transition-colors' : ''}`}
          onClick={isEmptyHoneypot ? handleNotifyClick : onForSaleClick}
          role={onForSaleClick || isEmptyHoneypot ? 'button' : undefined}
          data-testid="rarity-listings"
        >
          {isEmptyHoneypot ? (
            <>
              <p
                className="text-[11px] font-bold uppercase tracking-wider rounded-full px-3 py-1.5 inline-block mt-1"
                style={{ color: '#DAA520', border: '1.5px solid rgba(218,165,32,0.5)', background: 'rgba(255,215,0,0.06)' }}
              >
                {forSaleLabel}
              </p>
            </>
          ) : (
            <>
              <p
                className="text-2xl font-heading font-bold"
                style={{ color: useHoneypot ? '#FFD700' : undefined }}
              >
                {forSaleCount.toLocaleString()}
              </p>
              <p
                className="text-[11px] uppercase tracking-wider mt-0.5"
                style={{ color: useHoneypot ? '#DAA520' : undefined }}
              >
                {forSaleLabel}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
