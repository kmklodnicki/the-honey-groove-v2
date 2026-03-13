import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const PWAInstallBanner = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem('honey_groove_installed') === 'true'; } catch { return false; }
  });

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      window.__pwaPrompt = e;
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      try { localStorage.setItem('honey_groove_installed', 'true'); } catch {}
      setDeferredPrompt(null);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    try { localStorage.setItem('honey_groove_installed', 'true'); } catch {}
  };

  if (!deferredPrompt || dismissed) return null;

  return (
    <div
      className="sticky top-0 z-[999999] w-full flex items-center justify-center gap-3 px-4 py-2.5"
      style={{ background: '#FDE68A' }}
      data-testid="pwa-install-banner"
    >
      <span className="text-sm font-medium" style={{ color: '#915527' }}>
        Download The Honey Groove App!
      </span>
      <button
        onClick={handleInstall}
        className="px-3 py-1 rounded-full text-xs font-bold transition-transform hover:scale-105"
        style={{ background: '#915527', color: '#FDE68A' }}
        data-testid="pwa-install-btn"
      >
        Install
      </button>
      <button
        onClick={handleDismiss}
        className="ml-1 transition-colors"
        style={{ color: 'rgba(145,85,39,0.5)' }}
        data-testid="pwa-dismiss-btn"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export default PWAInstallBanner;
