import React, { useState, useRef, useCallback, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';

const isStandalone = () =>
  typeof window !== 'undefined' &&
  (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true);

/**
 * Pull-to-refresh wrapper — only active in PWA standalone mode.
 * Uses touch events to detect downward swipe at top of page.
 */
const PullToRefresh = ({ children }) => {
  const [pulling, setPulling] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const startY = useRef(0);
  const standalone = useRef(isStandalone());

  const THRESHOLD = 80;

  const handleTouchStart = useCallback((e) => {
    if (!standalone.current) return;
    if (window.scrollY > 5) return;
    startY.current = e.touches[0].clientY;
    setPulling(true);
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (!pulling || refreshing) return;
    const dy = e.touches[0].clientY - startY.current;
    if (dy < 0) { setPullDistance(0); return; }
    setPullDistance(Math.min(dy * 0.5, 120));
  }, [pulling, refreshing]);

  const handleTouchEnd = useCallback(() => {
    if (!pulling) return;
    if (pullDistance >= THRESHOLD && !refreshing) {
      setRefreshing(true);
      setPullDistance(THRESHOLD);
      window.location.reload();
    } else {
      setPullDistance(0);
    }
    setPulling(false);
  }, [pulling, pullDistance, refreshing]);

  // Re-check standalone on mount (for hot reload)
  useEffect(() => { standalone.current = isStandalone(); }, []);

  if (!standalone.current) return children;

  const progress = Math.min(pullDistance / THRESHOLD, 1);

  return (
    <div
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      style={{ minHeight: '100vh' }}
    >
      {/* Pull indicator */}
      {pullDistance > 10 && (
        <div
          className="flex items-center justify-center transition-all"
          style={{
            height: `${pullDistance}px`,
            overflow: 'hidden',
          }}
          data-testid="pull-to-refresh-indicator"
        >
          <RefreshCw
            className="transition-transform"
            style={{
              width: 20,
              height: 20,
              color: '#915527',
              opacity: progress,
              transform: `rotate(${progress * 360}deg)`,
              animation: refreshing ? 'spin 0.8s linear infinite' : 'none',
            }}
          />
        </div>
      )}
      {children}
    </div>
  );
};

/**
 * Standalone-only refresh button for bottom nav or feed header.
 */
export const StandaloneRefreshButton = () => {
  const [show, setShow] = useState(false);

  useEffect(() => { setShow(isStandalone()); }, []);

  if (!show) return null;

  return (
    <button
      onClick={() => window.location.reload()}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all hover:scale-105 active:scale-95"
      style={{ background: '#FDE68A', color: '#915527', border: '1px solid rgba(145,85,39,0.15)' }}
      data-testid="standalone-refresh-btn"
    >
      <RefreshCw className="w-3 h-3" />
      Refresh
    </button>
  );
};

export default PullToRefresh;
