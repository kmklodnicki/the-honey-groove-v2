import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';

/**
 * UserBadges — renders the badge stack for any user object.
 * Order: [Verified ✓] [Gold ⬡] [FOUNDER]
 *
 * Reads:
 *   user.is_verified        — green checkmark (Verified badge)
 *   user.golden_hive_verified — legacy fallback for Verified badge
 *   user.is_gold_member     — gold hexagon (Gold badge)
 *   user.is_founder / user.is_admin — orange Founder badge
 *
 * Props:
 *   user   — user object (from API response)
 *   size   — "small" (16px) | "large" (24px), default "small"
 */
function BadgeTooltip({ open, anchor, children }) {
  const [pos, setPos] = useState({ top: 0, left: 0, above: true });
  const tipRef = useRef(null);

  useEffect(() => {
    if (!open || !anchor.current) return;
    const rect = anchor.current.getBoundingClientRect();
    const tipW = 200;
    let left = rect.left + rect.width / 2 - tipW / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tipW - 8));
    const above = rect.top > 70;
    const top = above ? rect.top - 8 : rect.bottom + 8;
    setPos({ top, left, above });
  }, [open, anchor]);

  if (!open) return null;
  return ReactDOM.createPortal(
    <div
      ref={tipRef}
      className="fixed px-3 py-2 rounded-lg max-w-[200px] whitespace-normal pointer-events-none animate-in fade-in-0 zoom-in-95 duration-150"
      style={{
        ...(pos.above ? { bottom: `${window.innerHeight - pos.top}px` } : { top: pos.top }),
        left: pos.left,
        zIndex: 9999,
        background: '#1A1A1A',
        color: '#fff',
        boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
        borderRadius: '10px',
        fontSize: '11px',
        lineHeight: 1.5,
      }}
    >
      {children}
    </div>,
    document.body
  );
}

function BadgeWrapper({ tooltip, children }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const isTouchDevice = typeof window !== 'undefined' && 'ontouchstart' in window;

  return (
    <>
      <span
        ref={ref}
        className="inline-flex items-center shrink-0 cursor-default"
        onMouseEnter={() => !isTouchDevice && setOpen(true)}
        onMouseLeave={() => !isTouchDevice && setOpen(false)}
        onClick={(e) => { if (isTouchDevice) { e.preventDefault(); setOpen(o => !o); } }}
      >
        {children}
      </span>
      <BadgeTooltip open={open} anchor={ref}>{tooltip}</BadgeTooltip>
    </>
  );
}

export function VerifiedBadge({ size = 16 }) {
  return (
    <BadgeWrapper tooltip={<><strong style={{ display: 'block', marginBottom: 2 }}>Verified</strong>This user's identity has been verified. They are a trusted member of The Honey Groove community.</>}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        data-testid="verified-badge"
        style={{ filter: 'drop-shadow(0 0 3px rgba(34,197,94,0.4))' }}
      >
        <circle cx="12" cy="12" r="11" fill="#22C55E" />
        <path d="M7.5 12l3 3 6-6" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </BadgeWrapper>
  );
}

export function GoldBadge({ size = 16 }) {
  const gradId = `goldHex_${size}`;
  return (
    <BadgeWrapper tooltip={<><strong style={{ display: 'block', marginBottom: 2 }}>THG Gold</strong>This user is a THG Gold subscriber. Lower fees, early Honeypot access, and premium community membership.</>}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        data-testid="gold-badge"
        style={{ filter: 'drop-shadow(0 0 3px rgba(218,165,32,0.5))' }}
      >
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFD700" />
            <stop offset="50%" stopColor="#E8A820" />
            <stop offset="100%" stopColor="#B8860B" />
          </linearGradient>
        </defs>
        {/* Hexagon path */}
        <path
          d="M12 2l8.66 5v10L12 22l-8.66-5V7z"
          fill={`url(#${gradId})`}
          stroke="#8B6914"
          strokeWidth="0.5"
        />
        <text x="12" y="16" textAnchor="middle" fontSize="9" fontWeight="bold" fill="#1A1A1A">G</text>
      </svg>
    </BadgeWrapper>
  );
}

export function FounderBadge() {
  return (
    <BadgeWrapper tooltip={<><strong style={{ display: 'block', marginBottom: 2 }}>Founder</strong>Founder of The Honey Groove. Trusted community leader.</>}>
      <span
        className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide shrink-0"
        style={{ background: 'linear-gradient(135deg, #FFD700, #DAA520)', color: '#1A1A1A' }}
        data-testid="founder-badge"
      >
        FOUNDER
      </span>
    </BadgeWrapper>
  );
}

/**
 * UserBadges — drop-in badge stack for any user object.
 * @param {{ user: object, size?: "small"|"large" }} props
 */
const UserBadges = ({ user, size = 'small' }) => {
  if (!user) return null;
  const px = size === 'large' ? 24 : 16;
  const isVerified = user.is_verified || user.golden_hive_verified || user.golden_hive;
  const isGold = user.is_gold_member;
  const isFounder = user.is_founder || user.is_admin;

  if (!isVerified && !isGold && !isFounder) return null;

  return (
    <span className="inline-flex items-center gap-0.5" data-testid="user-badges">
      {isVerified && <VerifiedBadge size={px} />}
      {isGold && <GoldBadge size={px} />}
      {isFounder && <FounderBadge />}
    </span>
  );
};

export default UserBadges;
