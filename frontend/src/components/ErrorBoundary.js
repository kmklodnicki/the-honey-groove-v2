import React from 'react';

// Shared turntable error screen used by both the React error boundary and maintenance mode
export const TurntableErrorScreen = ({ title, subtitle, actionLabel, onAction, showTimestamp = true }) => (
  <div className="fixed inset-0 z-[999999] flex items-center justify-center" style={{ background: 'linear-gradient(180deg, #FFF3D4 0%, #F5D76E 40%, #D4A017 100%)' }} data-testid="error-screen">
    <div className="flex flex-col items-center text-center px-6 max-w-md">
      {/* Turntable */}
      <div className="relative mb-8" style={{ width: 220, height: 220 }}>
        {/* Platter base */}
        <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, #E8E8E8 0%, #D0D0D0 60%, #B8B8B8 100%)', boxShadow: '0 8px 32px rgba(0,0,0,0.2), inset 0 2px 4px rgba(255,255,255,0.3)' }} />
        {/* Vinyl record */}
        <div className="absolute rounded-full" style={{ top: 10, left: 10, width: 200, height: 200, animation: 'vinylSpin 3s linear infinite' }}>
          <svg viewBox="0 0 200 200" width="200" height="200">
            <defs>
              <radialGradient id="errVinyl" cx="50%" cy="45%" r="50%">
                <stop offset="0%" stopColor="#2A2A2A" />
                <stop offset="100%" stopColor="#111" />
              </radialGradient>
            </defs>
            <circle cx="100" cy="100" r="98" fill="url(#errVinyl)" />
            <circle cx="100" cy="100" r="97" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
            {[88,82,76,70,64,58,52,46,40,34].map((r, i) => (
              <circle key={r} cx="100" cy="100" r={r} fill="none" stroke={i % 3 === 0 ? 'rgba(60,60,60,0.7)' : 'rgba(40,40,40,0.5)'} strokeWidth={i % 2 === 0 ? '0.8' : '0.4'} />
            ))}
            <circle cx="100" cy="100" r="28" fill="#1E1E1E" />
            <circle cx="100" cy="100" r="24" fill="#DAA520" />
            <text x="100" y="96" textAnchor="middle" fill="#1A1A1A" fontSize="5" fontWeight="bold" fontFamily="serif" letterSpacing="0.5">GROOVE STUCK</text>
            <text x="100" y="104" textAnchor="middle" fill="#1A1A1A" fontSize="4" fontFamily="serif">NEVER SKIP</text>
            <circle cx="100" cy="100" r="6" fill="#1A1A1A" />
            <circle cx="100" cy="100" r="3" fill="#333" />
          </svg>
        </div>
        {/* Tonearm */}
        <div className="absolute" style={{ top: -8, right: 20, transformOrigin: 'top right', transform: 'rotate(25deg)' }}>
          <div style={{ width: 3, height: 100, background: 'linear-gradient(180deg, #C0C0C0, #808080)', borderRadius: 2, boxShadow: '1px 1px 4px rgba(0,0,0,0.3)' }} />
          <div style={{ width: 8, height: 14, background: '#666', borderRadius: '0 0 2px 2px', marginLeft: -2.5, boxShadow: '0 2px 4px rgba(0,0,0,0.3)' }} />
        </div>
        {/* Tonearm pivot */}
        <div className="absolute" style={{ top: -12, right: 16, width: 14, height: 14, borderRadius: '50%', background: 'radial-gradient(circle, #D0D0D0, #909090)', boxShadow: '0 2px 6px rgba(0,0,0,0.3)' }} />
      </div>

      <h1 className="text-2xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif", color: '#3A2A0A' }} data-testid="error-title">
        {title}
      </h1>
      <p className="text-base mb-6" style={{ fontFamily: "'Cormorant Garamond', serif", color: '#6B5A3A', lineHeight: 1.5 }} data-testid="error-subtitle">
        {subtitle}
      </p>
      {onAction && (
        <button
          onClick={onAction}
          className="px-8 py-3 rounded-full text-base font-semibold transition-all hover:scale-105 active:scale-95"
          style={{ background: '#9A7520', color: '#FFF', boxShadow: '0 4px 16px rgba(154,117,32,0.4)' }}
          data-testid="error-action-btn"
        >
          {actionLabel || 'Try Again'}
        </button>
      )}
      {showTimestamp && (
        <p className="text-xs mt-6" style={{ color: '#9A8A6A' }}>
          {new Date().toLocaleTimeString()} — thehoneygroove.com
        </p>
      )}
    </div>
  </div>
);

// React Error Boundary class component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <TurntableErrorScreen
          title="Don't skip a beat!"
          subtitle="Our needle hit a little dust. We're auto-cleaning the grooves right now — try refreshing in a moment!"
          actionLabel="Try Again"
          onAction={() => window.location.reload()}
        />
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
