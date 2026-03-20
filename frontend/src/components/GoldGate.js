import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Crown } from 'lucide-react';
import { Button } from './ui/button';

/**
 * GoldGate — wraps children in a blur+upsell overlay for non-Gold users.
 * If isGold is true, renders children directly (no overhead).
 */
const GoldGate = ({
  isGold,
  children,
  label = 'Get Gold',
  hint,
  compact = false,
}) => {
  const navigate = useNavigate();

  if (isGold) return children;

  return (
    <div className="relative rounded-xl overflow-hidden" data-testid="gold-gate">
      <div className="blur-sm pointer-events-none select-none">{children}</div>
      <div
        className="absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-xl"
        style={{ background: 'rgba(255,248,225,0.88)', backdropFilter: 'blur(2px)' }}
      >
        <Crown className={`text-[#DAA520] ${compact ? 'w-4 h-4' : 'w-5 h-5'}`} />
        {hint && (
          <p className={`text-center text-[#3A4D63] px-3 ${compact ? 'text-[10px]' : 'text-xs'}`}>
            {hint}
          </p>
        )}
        <Button
          size="sm"
          className="rounded-full font-bold text-[#1E2A3A] shadow-sm"
          style={{ background: '#E8A820', fontSize: compact ? '10px' : '12px' }}
          onClick={() => navigate('/gold')}
          data-testid="gold-gate-cta"
        >
          {label}
        </Button>
      </div>
    </div>
  );
};

export default GoldGate;
