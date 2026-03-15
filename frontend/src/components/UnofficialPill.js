import React from 'react';

/**
 * BLOCK 592: "Unofficial" Pill Badge
 * Steel Gray/Charcoal pill that overlays on album art for unofficial releases.
 * Used in Collection grid, Feed, Marketplace listings, and Record detail.
 *
 * @param {'overlay' | 'inline'} variant - 'overlay' for top-right corner on art, 'inline' for text flow
 * @param {string} className - Additional classes
 */
const UnofficialPill = ({ variant = 'overlay', className = '' }) => {
  if (variant === 'inline') {
    return (
      <span
        className={`inline-flex items-center text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${className}`}
        style={{ background: '#4A4A4A', color: '#fff', letterSpacing: '0.5px' }}
        data-testid="unofficial-pill"
      >
        Unofficial
      </span>
    );
  }

  return (
    <div
      className={`absolute bottom-2 right-2 z-[6] text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full backdrop-blur-sm ${className}`}
      style={{
        background: 'rgba(74,74,74,0.85)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        color: '#fff',
        letterSpacing: '0.6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      }}
      data-testid="unofficial-pill"
    >
      Unofficial
    </div>
  );
};

export default UnofficialPill;
