import React from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * VinylShield — Global Error Boundary + API health-check gate.
 * Shows a friendly "needle hit dust" screen when:
 *   - React component tree throws (classic Error Boundary)
 *   - /api/health or /api/auth/me returns 500 / timeout / ECONNREFUSED
 * Stays hidden when the app is working normally.
 */

const SHIELD_STYLE = {
  wrapper: {
    position: 'fixed', inset: 0, zIndex: 9999,
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    background: 'linear-gradient(135deg, #FFF8E7 0%, #FFE8A3 50%, #F5C542 100%)',
    fontFamily: "'DM Sans', 'Inter', system-ui, sans-serif",
    padding: '24px', textAlign: 'center',
  },
  vinyl: {
    width: 120, height: 120, borderRadius: '50%',
    background: 'radial-gradient(circle at 50% 50%, #222 30%, #111 31%, #111 48%, #333 49%, #333 50%, #111 51%, #111 100%)',
    boxShadow: '0 0 0 4px #C8861A, 0 8px 32px rgba(0,0,0,0.25)',
    animation: 'vinyl-spin 2s linear infinite',
  },
  heading: {
    fontSize: 22, fontWeight: 700, color: '#5C3D10', marginTop: 28, marginBottom: 8,
    lineHeight: 1.3, maxWidth: 400,
  },
  body: {
    fontSize: 15, color: '#7A5A20', maxWidth: 360, lineHeight: 1.6, marginBottom: 28,
  },
  btn: {
    background: '#C8861A', color: '#fff', border: 'none', borderRadius: 999,
    padding: '12px 32px', fontSize: 15, fontWeight: 600, cursor: 'pointer',
    boxShadow: '0 2px 12px rgba(200,134,26,0.35)',
    transition: 'transform 0.15s, box-shadow 0.15s',
  },
};

/* Inject the spin keyframes once */
if (typeof document !== 'undefined' && !document.getElementById('vinyl-spin-kf')) {
  const style = document.createElement('style');
  style.id = 'vinyl-spin-kf';
  style.textContent = `@keyframes vinyl-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`;
  document.head.appendChild(style);
}

function ShieldUI({ onRetry }) {
  return (
    <div style={SHIELD_STYLE.wrapper} data-testid="vinyl-shield">
      <div style={SHIELD_STYLE.vinyl} data-testid="vinyl-shield-spinner" />
      <h1 style={SHIELD_STYLE.heading}>Don't skip a beat!</h1>
      <p style={SHIELD_STYLE.body}>
        Our needle hit a little dust. We're auto-cleaning the grooves right now — try refreshing in a moment!
      </p>
      <button
        style={SHIELD_STYLE.btn}
        data-testid="vinyl-shield-retry"
        onClick={onRetry}
        onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.04)'; }}
        onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
      >
        Try Again
      </button>
    </div>
  );
}

class VinylShield extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, apiDown: false, checking: true };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('[VinylShield] React error caught:', error, info);
  }

  componentDidMount() {
    this.checkHealth();
  }

  checkHealth = async () => {
    try {
      const res = await axios.get(`${API}/health`, { timeout: 8000 });
      if (res.status >= 500) throw new Error('Server error');
      this.setState({ apiDown: false, checking: false });
    } catch (err) {
      console.warn('[VinylShield] Health check failed:', err.message);
      this.setState({ apiDown: true, checking: false });
    }
  };

  handleRetry = () => {
    // Clear local storage cache that could be stale
    try {
      localStorage.removeItem('honeygroove_token');
      localStorage.removeItem('swr-cache');
      // Clear any stale session cookies
      document.cookie.split(';').forEach(c => {
        const name = c.split('=')[0].trim();
        if (name.startsWith('honeygroove') || name.startsWith('next-auth')) {
          document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
        }
      });
    } catch (_) { /* storage access can throw in some browsers */ }
    window.location.reload();
  };

  render() {
    // React crash → show shield
    if (this.state.hasError) {
      return <ShieldUI onRetry={this.handleRetry} />;
    }
    // API health check failed → show shield
    if (this.state.apiDown && !this.state.checking) {
      return <ShieldUI onRetry={this.handleRetry} />;
    }
    // Still checking → show nothing (children will show their own loading states)
    if (this.state.checking) {
      return this.props.children;
    }
    return this.props.children;
  }
}

export default VinylShield;
