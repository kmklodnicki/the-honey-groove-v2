import React, { useState, useEffect, useCallback } from 'react';
import { Award, Diamond, ArrowLeft, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { usePageTitle } from '../hooks/usePageTitle';
import { usePullToRefresh } from '../hooks/usePullToRefresh';

const VINYL_CHARMS = [
  {
    id: 'mirrorball-charm',
    honeyLabel: 'The Mirrorball',
    name: 'Mirrorball / Disco Ball Charm',
    descriptor: 'A tiny disco ball that sits on top of your spinning record, catching the light and setting the mood.',
    url: 'https://vinylcharms.com/products/mirrorball-disco-ball-charm-for-record-collectors-or-accessorizing-your-vinyl-collection?ref=KATIE',
    partner: 'vinylcharms',
    partnerLabel: 'VinylCharms',
    image: 'https://customer-assets.emergentagent.com/job_9fb17d67-a974-4652-b57c-8e9a0febaeaf/artifacts/rbk1l11x_mirrorball.webp',
  },
  {
    id: 'ts-charms',
    honeyLabel: 'The Eras',
    name: 'TS Charms',
    descriptor: 'There\'s a perfect charm for every era.',
    url: 'https://vinylcharms.com/products/ts-charms?ref=KATIE',
    partner: 'vinylcharms',
    partnerLabel: 'VinylCharms',
    image: 'https://customer-assets.emergentagent.com/job_9fb17d67-a974-4652-b57c-8e9a0febaeaf/artifacts/gzlfqygu_opalite.webp',
  },
  {
    id: 'sabrina-charms',
    honeyLabel: 'The Espresso',
    name: 'Sabrina Charms',
    descriptor: 'From espresso cups to pretty girl avenue, Vinyl Charms has you covered.',
    url: 'https://vinylcharms.com/products/sabrina-charms-for-record-collectors-or-accessorizing-sabrina-carpenter-fans-espresso-and-short-n-sweet?ref=KATIE',
    partner: 'vinylcharms',
    partnerLabel: 'VinylCharms',
    image: 'https://customer-assets.emergentagent.com/job_9fb17d67-a974-4652-b57c-8e9a0febaeaf/artifacts/p4rrq9a0_sabrina.webp',
  },
];

const VINYL_PROTECTION = [
  {
    id: 'cleaning-kit',
    honeyLabel: 'The Polish',
    name: 'Vinyl Record Cleaning Kit',
    descriptor: 'A complete care kit for records that deserve a little extra love. Keep your audio sounding crisp.',
    url: 'https://amzn.to/4setivM',
    partner: 'amazon',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/obo7sks1_image3.jpg',
  },
  {
    id: 'shield',
    honeyLabel: 'The Shield',
    name: 'Premium Outer Sleeves',
    descriptor: 'Crystal-clear outer protection for the records worth showing off.',
    url: 'https://amzn.to/40ERkEd',
    partner: 'amazon',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/j6e6td19_714yHNMQsLL._AC_SL1500_%20%281%29.jpg',
  },
  {
    id: 'vault',
    honeyLabel: 'The Vault',
    name: 'Anti-Static Inner Sleeves',
    descriptor: 'Antistatic inner sleeves that keep your vinyl clean and properly tucked away.',
    url: 'https://amzn.to/4bfoyP4',
    partner: 'amazon',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/6g7drwvn_product2.jpg',
  },
  {
    id: 'cracked-ice',
    honeyLabel: 'The Prism',
    name: 'Holographic Outer Sleeves - Cracked Ice',
    descriptor: 'Iridescent protection that makes your shelf shimmer like a disco ball.',
    url: 'https://vinylsupplyco.com/products/holographic-outer-sleeves?ref=KATHRYNKLODNICKI',
    partner: 'vinylsupplyco',
    partnerLabel: 'VinylSupplyCo',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/1rzzzzu9_1.webp',
  },
  {
    id: 'lovely',
    honeyLabel: 'The Sweetheart',
    name: 'Holographic Outer Sleeves - Lovely',
    descriptor: 'Heart-patterned holographic sleeves for the records you love most.',
    url: 'https://vinylsupplyco.com/collections/holographic-sleeves/products/holographic-outer-sleeves-lovely?ref=KATHRYNKLODNICKI',
    partner: 'vinylsupplyco',
    partnerLabel: 'VinylSupplyCo',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/5vhwif93_2.webp',
  },
  {
    id: 'pearl-shimmer',
    honeyLabel: 'The Glow',
    name: 'Holographic Outer Sleeves - Pearl Shimmer',
    descriptor: 'Soft pearl iridescence that gives your vault an ethereal glow.',
    url: 'https://vinylsupplyco.com/collections/holographic-sleeves/products/holographic-outer-sleeves-pearl-shimmer?ref=KATHRYNKLODNICKI',
    partner: 'vinylsupplyco',
    partnerLabel: 'VinylSupplyCo',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/tvavxlin_3.webp',
  },
];

const LIGHT_UP = [
  {
    id: 'led-turntable',
    honeyLabel: 'The Stage',
    name: 'LED Platter Light Kit',
    descriptor: 'Transform your setup with a neon glow ring that turns every spin into a light show. Remote control included.',
    url: 'https://vinylsupplyco.com/products/led-turntable-kit?ref=KATHRYNKLODNICKI',
    partner: 'vinylsupplyco',
    partnerLabel: 'VinylSupplyCo',
    image: 'https://images.unsplash.com/photo-1746127609033-78c30b79038e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2OTV8MHwxfHNlYXJjaHwzfHx0dXJudGFibGUlMjBMRUQlMjBsaWdodCUyMGtpdCUyMHZpbnlsJTIwZ2xvdyUyMG5lb258ZW58MHx8fHwxNzczMTc2Mjg0fDA&ixlib=rb-4.1.0&q=85',
  },
];

const ApprovedSeal = () => (
  <div className="inline-flex items-center gap-1.5 bg-gradient-to-r from-amber-100/80 to-yellow-50/80 border border-amber-300/40 rounded-full px-3 py-1" data-testid="approved-seal">
    <Award className="w-3.5 h-3.5 text-amber-600" />
    <span className="text-[11px] font-semibold tracking-wide text-amber-700 uppercase">Honey Groove Approved</span>
  </div>
);

/* ─── Escape key handler hook ─── */
const useEscapeKey = (open, onClose) => {
  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);
};

/* ─── BLOCK 115.1: The Groove Gateway (Amazon) ─── */
const GrooveGatewayModal = ({ item, open, onClose }) => {
  const [phase, setPhase] = useState('loading');
  useEscapeKey(open, onClose);

  useEffect(() => {
    if (!open) { setPhase('loading'); return; }
    const t = setTimeout(() => {
      setPhase('handoff');
      window.open(item?.url, '_blank', 'noopener,noreferrer');
    }, 1500);
    return () => clearTimeout(t);
  }, [open, item]);

  if (!open || !item) return null;

  return (
    <div className="fixed inset-0 z-[200000] flex items-end sm:items-center justify-center" data-testid="groove-gateway-modal">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div
        className="relative w-full sm:max-w-lg mx-auto rounded-t-3xl sm:rounded-3xl overflow-hidden"
        style={{
          background: 'linear-gradient(180deg, rgba(255,246,230,0.97) 0%, rgba(255,255,255,0.98) 100%)',
          border: '1px solid rgba(218,165,32,0.3)',
          boxShadow: '0 -8px 40px rgba(0,0,0,0.2)',
          maxHeight: '90vh',
        }}
      >
        <div
          className="flex items-center justify-between px-5 py-4 border-b"
          style={{ background: 'rgba(255,215,0,0.08)', borderColor: 'rgba(218,165,32,0.15)' }}
        >
          <button onClick={onClose} className="flex items-center gap-1.5 text-sm text-vinyl-black/70 hover:text-vinyl-black transition-colors" data-testid="gateway-back-btn">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <span className="text-xs font-bold uppercase tracking-widest text-[#C8861A]">The Groove Gateway</span>
          <button onClick={onClose} className="text-vinyl-black/40 hover:text-vinyl-black/70 transition-colors" data-testid="gateway-close-btn">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 sm:p-8">
          {phase === 'loading' ? (
            <div className="flex flex-col items-center justify-center py-12" data-testid="groove-gateway-loading">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1.5s linear infinite' }}>
                <circle cx="12" cy="12" r="11" fill="#1A1A1A" />
                <circle cx="12" cy="12" r="9.5" fill="none" stroke="#333" strokeWidth="0.4" />
                <circle cx="12" cy="12" r="8" fill="none" stroke="#333" strokeWidth="0.3" />
                <circle cx="12" cy="12" r="6.5" fill="none" stroke="#333" strokeWidth="0.3" />
                <circle cx="12" cy="12" r="5" fill="none" stroke="#333" strokeWidth="0.3" />
                <circle cx="12" cy="12" r="3.5" fill="#DAA520" />
                <circle cx="12" cy="12" r="1.5" fill="#1A1A1A" />
              </svg>
              <p className="text-sm text-[#C8861A] font-medium mt-5 tracking-wide">Securing your request...</p>
            </div>
          ) : (
            <div className="text-center" data-testid="groove-gateway-handoff">
              <div className="w-24 h-24 mx-auto rounded-xl overflow-hidden shadow-md mb-5">
                <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
              </div>

              <p className="text-xs font-bold uppercase tracking-widest text-[#C8861A] mb-2">{item.honeyLabel}</p>
              <h3 className="font-heading text-xl text-vinyl-black mb-4">{item.name}</h3>

              <div
                className="rounded-xl p-4 mb-6 text-sm text-vinyl-black/70 leading-relaxed"
                style={{ background: 'rgba(255,215,0,0.06)', border: '1px solid rgba(218,165,32,0.2)' }}
              >
                You are being directed to our Amazon fulfillment partner. Your Groove status remains active.
              </div>

              <button
                onClick={() => { window.open(item.url, '_blank', 'noopener,noreferrer'); onClose(); }}
                className="w-full py-4 rounded-2xl text-base font-bold uppercase tracking-wider transition-all duration-200 active:scale-[0.98]"
                style={{
                  background: 'linear-gradient(135deg, #FFD700, #DAA520, #C8861A)',
                  color: '#2A1A06',
                  border: '2px solid rgba(218,165,32,0.6)',
                  boxShadow: '0 4px 20px rgba(218,165,32,0.3), inset 0 1px 0 rgba(255,255,255,0.3)',
                }}
                data-testid="groove-gateway-acquire-btn"
              >
                <Diamond className="w-4 h-4 inline-block mr-2 -mt-0.5" />
                Get via Partner
              </button>

              <p className="text-[10px] text-muted-foreground mt-3">Secured by The Honey Groove</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ─── BLOCK 119.1: The Groove Terminal — Branded Gateway (VinylSupplyCo) ─── */
const GrooveTerminalModal = ({ item, open, onClose }) => {
  const [phase, setPhase] = useState('pulse');
  useEscapeKey(open, onClose);

  useEffect(() => {
    if (!open) { setPhase('pulse'); return; }
    const t = setTimeout(() => setPhase('ready'), 1500);
    return () => clearTimeout(t);
  }, [open]);

  if (!open || !item) return null;

  return (
    <div className="fixed inset-0 z-[200000] flex items-end sm:items-center justify-center" data-testid="groove-terminal-modal">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-md" onClick={onClose} />

      <div
        className="relative w-full sm:max-w-lg mx-auto rounded-t-3xl sm:rounded-3xl overflow-hidden"
        style={{
          background: 'linear-gradient(180deg, rgba(255,248,230,0.97) 0%, rgba(255,255,255,0.98) 100%)',
          border: '1px solid rgba(218,165,32,0.3)',
          boxShadow: '0 -8px 40px rgba(0,0,0,0.2)',
          maxHeight: '90vh',
        }}
      >
        {/* Diamond Glass Header */}
        <div
          className="flex items-center justify-between px-5 py-4 border-b"
          style={{ background: 'rgba(255,215,0,0.08)', borderColor: 'rgba(218,165,32,0.15)' }}
          data-testid="groove-terminal-header"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-heading text-vinyl-black tracking-tight">The Honey Groove</span>
            <span className="text-[#DAA520] text-sm font-light mx-0.5">&times;</span>
            <span className="text-sm font-heading text-[#C8861A] tracking-tight">{item?.partnerLabel || 'Partner'}</span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full transition-colors hover:bg-[#DAA520]/10"
            data-testid="groove-terminal-close-btn"
          >
            <X className="w-5 h-5" style={{ color: '#C8861A' }} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 sm:p-8">
          {phase === 'pulse' ? (
            <div className="flex flex-col items-center justify-center py-12" data-testid="groove-terminal-pulse">
              {/* Nectar Pulse — glowing gold ring around spinning vinyl */}
              <div className="relative flex items-center justify-center" style={{ width: 88, height: 88 }}>
                <div
                  className="absolute rounded-full"
                  style={{
                    inset: 0,
                    border: '2px solid rgba(218,165,32,0.5)',
                    animation: 'nectarPulse 1.5s ease-in-out infinite',
                  }}
                />
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1.5s linear infinite' }}>
                  <circle cx="12" cy="12" r="11" fill="#1A1A1A" />
                  <circle cx="12" cy="12" r="9.5" fill="none" stroke="#333" strokeWidth="0.4" />
                  <circle cx="12" cy="12" r="8" fill="none" stroke="#333" strokeWidth="0.3" />
                  <circle cx="12" cy="12" r="6.5" fill="none" stroke="#333" strokeWidth="0.3" />
                  <circle cx="12" cy="12" r="5" fill="none" stroke="#333" strokeWidth="0.3" />
                  <circle cx="12" cy="12" r="3.5" fill="#DAA520" />
                  <circle cx="12" cy="12" r="1.5" fill="#1A1A1A" />
                </svg>
              </div>
              <p className="text-sm text-[#C8861A] font-medium mt-6 tracking-wide">Securing your request...</p>
            </div>
          ) : (
            <div className="text-center" data-testid="groove-terminal-ready">
              <div className="w-24 h-24 mx-auto rounded-xl overflow-hidden shadow-md mb-5">
                <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
              </div>

              <p className="text-xs font-bold uppercase tracking-widest text-[#C8861A] mb-2">{item.honeyLabel}</p>
              <h3 className="font-heading text-xl text-vinyl-black mb-4">{item.name}</h3>

              <div
                className="rounded-xl p-4 mb-6 text-sm text-vinyl-black/70 leading-relaxed"
                style={{ background: 'rgba(255,215,0,0.06)', border: '1px solid rgba(218,165,32,0.2)' }}
              >
                You are being directed to our fulfillment partner to complete your acquisition. Your Groove status remains active.
              </div>

              <button
                onClick={() => { window.open(item.url, '_blank', 'noopener,noreferrer'); onClose(); }}
                className="w-full py-4 rounded-2xl text-base font-bold uppercase tracking-wider transition-all duration-200 active:scale-[0.98]"
                style={{
                  background: 'linear-gradient(135deg, #FFD700, #DAA520, #C8861A)',
                  color: '#2A1A06',
                  border: '2px solid rgba(218,165,32,0.6)',
                  boxShadow: '0 4px 20px rgba(218,165,32,0.3), inset 0 1px 0 rgba(255,255,255,0.3)',
                }}
                data-testid="groove-terminal-purchase-btn"
              >
                <Diamond className="w-4 h-4 inline-block mr-2 -mt-0.5" />
                Complete Purchase on {item?.partnerLabel || 'Partner'}
              </button>

              <p className="text-[10px] text-muted-foreground mt-3">Secured by The Honey Groove</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ─── Product Card ─── */
const ProductCard = ({ item, onAcquire }) => {
  return (
    <div
      className="group bg-white rounded-2xl border border-stone-200/60 shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden flex flex-col"
      data-testid={`product-card-${item.id}`}
    >
      <div className="relative aspect-square bg-stone-50 overflow-hidden">
        <img
          src={item.image}
          alt={`${item.name} - Vinyl Record Accessory`}
          className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
          loading="lazy"
        />
      </div>

      <div className="flex flex-col flex-1 p-5 sm:p-6 gap-3">
        <ApprovedSeal />

        <div className="space-y-1">
          <p className="text-xs font-semibold tracking-widest uppercase text-amber-600" data-testid="honey-label">
            {item.honeyLabel}
          </p>
          <h3 className="font-heading text-lg text-stone-900 leading-snug" data-testid="product-name">
            {item.name}
          </h3>
        </div>

        <p className="text-sm text-stone-500 leading-relaxed flex-1" data-testid="product-descriptor">
          {item.descriptor}
        </p>

        <Button
          onClick={() => onAcquire(item)}
          className="mt-auto bg-stone-900 text-white hover:bg-stone-800 rounded-full gap-2 w-full text-center py-2.5 px-2"
          style={{ fontSize: 'clamp(0.75rem, 2vw, 1rem)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
          data-testid={`cta-${item.id}`}
        >
          <Diamond className="w-3.5 h-3.5 shrink-0" />
          Get via Partner
        </Button>
      </div>
    </div>
  );
};

/* ─── Section Header ─── */
const SectionHeader = ({ title, subtext, testId, showDivider }) => (
  <>
    {showDivider && (
      <div className="mt-10 sm:mt-14 mb-10 sm:mb-14 mx-auto" style={{ maxWidth: '120px', borderTop: '1px solid rgba(218, 165, 32, 0.2)' }} />
    )}
    <div className="text-center mb-6 sm:mb-8 space-y-2" data-testid={testId}>
      <h2 className="font-heading text-2xl sm:text-3xl text-stone-900 tracking-tight">{title}</h2>
      <p className="text-sm text-stone-500 max-w-lg mx-auto leading-relaxed">{subtext}</p>
    </div>
  </>
);

const EssentialsPage = () => {
  usePageTitle('Honey Essentials');
  const [gatewayItem, setGatewayItem] = useState(null);
  const [terminalItem, setTerminalItem] = useState(null);

  const { PullIndicator } = usePullToRefresh(useCallback(async () => {
    window.location.reload();
  }, []));

  const handleAcquire = useCallback((item) => {
    if (item.partner === 'amazon') {
      setGatewayItem(item);
    } else {
      setTerminalItem(item);
    }
  }, []);

  return (
    <div className="min-h-[calc(100vh-80px)]">
      <PullIndicator />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 pt-3 md:pt-2 pb-24 md:pb-8">
        <div className="text-center mb-10 sm:mb-14 space-y-3" data-testid="essentials-header">
          <h1 className="font-heading text-4xl sm:text-5xl text-stone-900 tracking-tight">
            Honey Essentials
          </h1>
          <p className="text-base text-stone-500 max-w-md mx-auto">
            The curated essentials that keep your vault sweet.
          </p>
        </div>

        {/* Section 1: Vinyl Charms */}
        <SectionHeader
          title="Vinyl Charms"
          subtext="Enhance your spin experience by putting a vinyl charm on top of your record while it's spinning to match the vibe."
          testId="section-vinyl-charms"
        />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-6" data-testid="charms-grid">
          {VINYL_CHARMS.map(item => (
            <ProductCard key={item.id} item={item} onAcquire={handleAcquire} />
          ))}
        </div>

        {/* Section 2: Vinyl Protection */}
        <SectionHeader
          title="Vinyl Protection"
          subtext="Protect your investments. Sleeves prevent scratches, dust, and provide anti-static protection. Regular cleaning helps keep your audio sounding crisp."
          testId="section-vinyl-protection"
          showDivider
        />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-6" data-testid="protection-grid">
          {VINYL_PROTECTION.map(item => (
            <ProductCard key={item.id} item={item} onAcquire={handleAcquire} />
          ))}
        </div>

        {/* Section 3: Light Up Your Records */}
        <SectionHeader
          title="Light Up Your Records"
          subtext="This LED light kit goes underneath your record player platter and comes with a remote control to adjust the light color from neutral white, solid colors, and moving rainbow colors."
          testId="section-light-up"
          showDivider
        />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-6 mb-8" data-testid="lightup-grid">
          {LIGHT_UP.map(item => (
            <ProductCard key={item.id} item={item} onAcquire={handleAcquire} />
          ))}
        </div>
      </div>

      <GrooveGatewayModal item={gatewayItem} open={!!gatewayItem} onClose={() => setGatewayItem(null)} />
      <GrooveTerminalModal item={terminalItem} open={!!terminalItem} onClose={() => setTerminalItem(null)} />
    </div>
  );
};

export default EssentialsPage;
