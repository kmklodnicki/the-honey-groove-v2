import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';

/**
 * BLOCK 581: Universal Gold Shield — drop-in verified badge for Feed, Profile, Search, Listings.
 * Renders the metallic gold shield SVG with portal tooltip on hover/tap.
 *
 * @param {number} size - Shield dimensions in px (default 20 for feed, 34 for profile)
 * @param {boolean} isFounder - Shows "Founder" in tooltip instead of generic verified text
 * @param {string} className - Additional classes
 */
const VerifiedShield = ({ size = 20, isFounder = false, className = '' }) => {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0, above: true });
  const ref = useRef(null);
  const tipRef = useRef(null);
  const isTouchDevice = typeof window !== 'undefined' && 'ontouchstart' in window;

  useEffect(() => {
    if (!open || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const tipW = 220;
    let left = rect.left + rect.width / 2 - tipW / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tipW - 8));
    const above = rect.top > 70;
    const top = above ? rect.top - 8 : rect.bottom + 8;
    setPos({ top, left, above });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const dismiss = (e) => {
      if (ref.current?.contains(e.target)) return;
      if (tipRef.current?.contains(e.target)) return;
      setOpen(false);
    };
    document.addEventListener('mousedown', dismiss);
    document.addEventListener('touchstart', dismiss);
    return () => {
      document.removeEventListener('mousedown', dismiss);
      document.removeEventListener('touchstart', dismiss);
    };
  }, [open]);

  const gradientId = `goldShield_${size}`;

  return (
    <>
      <span
        ref={ref}
        className={`inline-flex items-center shrink-0 cursor-default ${className}`}
        onMouseEnter={() => !isTouchDevice && setOpen(true)}
        onMouseLeave={() => !isTouchDevice && setOpen(false)}
        onClick={(e) => { if (isTouchDevice) { e.preventDefault(); setOpen(o => !o); } }}
        data-testid="verified-shield"
      >
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
          style={{ filter: `drop-shadow(0px 1px 2px rgba(0,0,0,0.15)) drop-shadow(0 0 ${size > 24 ? 8 : 4}px rgba(253,185,49,0.4))` }}>
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFD700"/>
              <stop offset="50%" stopColor="#FDB931"/>
              <stop offset="100%" stopColor="#B8860B"/>
            </linearGradient>
          </defs>
          <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" fill={`url(#${gradientId})`} stroke="#8B6914" strokeWidth="0.5"/>
          <path d="M9.5 12l2 2 3.5-4" stroke="#1A1A1A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        </svg>
      </span>
      {open && ReactDOM.createPortal(
        <div
          ref={tipRef}
          className="fixed px-3 py-2 rounded-lg max-w-[220px] whitespace-normal pointer-events-auto animate-in fade-in-0 zoom-in-95 duration-150"
          style={{
            ...(pos.above ? { bottom: `${window.innerHeight - pos.top}px` } : { top: pos.top }),
            left: pos.left,
            zIndex: 9999,
            background: '#1A1A1A',
            color: '#fff',
            boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
            borderRadius: '10px',
          }}
          data-testid="verified-shield-tooltip"
        >
          <p className="font-bold text-xs mb-0.5">{isFounder ? 'Founder' : 'Golden Hive ID'}</p>
          <p className="text-[11px] leading-relaxed opacity-90">
            {isFounder
              ? 'Founder of The Honey Groove. ID verified and trusted community leader.'
              : 'This user has been officially ID verified. They are a trusted member of The Honey Groove community.'}
          </p>
        </div>,
        document.body
      )}
    </>
  );
};

export default VerifiedShield;
