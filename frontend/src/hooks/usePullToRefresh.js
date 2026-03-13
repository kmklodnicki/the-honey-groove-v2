import { useState, useRef, useCallback, useEffect } from 'react';

const THRESHOLD = 80;

export function usePullToRefresh(onRefresh) {
  const [pulling, setPulling] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const startY = useRef(0);
  const active = useRef(false);

  const handleTouchStart = useCallback((e) => {
    if (window.scrollY > 5) return;
    startY.current = e.touches[0].clientY;
    active.current = true;
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (!active.current || refreshing) return;
    const dy = e.touches[0].clientY - startY.current;
    if (dy > 0) {
      setPulling(true);
      setPullDistance(Math.min(dy * 0.5, 120));
    }
  }, [refreshing]);

  const handleTouchEnd = useCallback(async () => {
    if (!active.current) return;
    active.current = false;
    if (pullDistance >= THRESHOLD && !refreshing) {
      setRefreshing(true);
      setPullDistance(THRESHOLD);
      try { await onRefresh(); } catch {}
      setRefreshing(false);
    }
    setPulling(false);
    setPullDistance(0);
  }, [pullDistance, refreshing, onRefresh]);

  useEffect(() => {
    const opts = { passive: true };
    document.addEventListener('touchstart', handleTouchStart, opts);
    document.addEventListener('touchmove', handleTouchMove, opts);
    document.addEventListener('touchend', handleTouchEnd);
    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  const PullIndicator = () => {
    if (!pulling && !refreshing) return null;
    return (
      <div
        className="flex items-center justify-center overflow-hidden transition-all"
        style={{ height: pullDistance, opacity: Math.min(pullDistance / THRESHOLD, 1) }}
        data-testid="pull-to-refresh-indicator"
      >
        <div
          className={`w-8 h-8 rounded-full border-3 border-t-transparent ${refreshing ? 'animate-spin' : ''}`}
          style={{
            borderColor: '#C8861A',
            borderTopColor: 'transparent',
            transform: refreshing ? undefined : `rotate(${pullDistance * 3}deg)`,
          }}
        />
      </div>
    );
  };

  return { PullIndicator, refreshing };
}
