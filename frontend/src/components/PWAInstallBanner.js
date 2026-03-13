import React, { useState, useEffect, useCallback } from 'react';
import { X, Share, PlusSquare } from 'lucide-react';

const isStandalone = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  window.navigator.standalone === true;

const isIOS = () =>
  /iPad|iPhone|iPod/.test(navigator.userAgent) ||
  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

const PWAInstallBanner = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showBanner, setShowBanner] = useState(false);
  const [showIOSGuide, setShowIOSGuide] = useState(false);

  useEffect(() => {
    if (isStandalone()) return;
    try { if (localStorage.getItem('pwa_installed') === 'true') return; } catch { /* noop */ }

    if (isIOS()) {
      setShowBanner(true);
      return;
    }

    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowBanner(true);
    };
    window.addEventListener('beforeinstallprompt', handler);

    // Fallback: show banner on mobile browsers after short delay even without the event
    const isMobile = /Android|webOS|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    let fallbackTimer;
    if (isMobile) {
      fallbackTimer = setTimeout(() => setShowBanner(true), 2000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      clearTimeout(fallbackTimer);
    };
  }, []);

  const handleInstall = useCallback(async () => {
    if (isIOS()) {
      setShowIOSGuide((prev) => !prev);
      return;
    }
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      try { localStorage.setItem('pwa_installed', 'true'); } catch { /* noop */ }
      setShowBanner(false);
    }
  }, [deferredPrompt]);

  const handleDismiss = useCallback(() => {
    setShowBanner(false);
    try { localStorage.setItem('pwa_installed', 'true'); } catch { /* noop */ }
  }, []);

  if (!showBanner) return null;

  return (
    <>
      {/* Spacer to push content below the fixed banner */}
      <div style={{ height: showIOSGuide ? '80px' : '40px' }} data-testid="pwa-banner-spacer" />

      <div
        className="fixed top-0 left-0 right-0 w-full"
        style={{ zIndex: 50, paddingTop: 'env(safe-area-inset-top, 0px)' }}
        data-testid="pwa-install-banner"
      >
        <div
          className="flex items-center justify-center gap-3 px-4 py-2.5"
          style={{ background: '#FDE68A', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
        >
          <span className="text-sm font-medium" style={{ color: '#915527' }}>
            Add The Honey Groove to your home screen!
          </span>
          <button
            onClick={handleInstall}
            className="px-3 py-1 rounded-full text-xs font-bold transition-transform hover:scale-105 active:scale-95"
            style={{ background: '#915527', color: '#FDE68A' }}
            data-testid="pwa-install-btn"
          >
            {isIOS() ? (showIOSGuide ? 'Got it' : 'How?') : 'Install'}
          </button>
          <button
            onClick={handleDismiss}
            className="ml-1 p-1.5 rounded-full transition-colors hover:bg-amber-200/50 active:bg-amber-200"
            style={{ color: '#915527' }}
            aria-label="Dismiss install banner"
            data-testid="pwa-dismiss-btn"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* iOS Add-to-Home-Screen guide */}
        {showIOSGuide && (
          <div
            className="px-5 py-3 flex items-start gap-3 text-xs leading-relaxed"
            style={{ background: '#FEF3C7', color: '#915527', borderTop: '1px solid rgba(145,85,39,0.15)' }}
            data-testid="pwa-ios-guide"
          >
            <div className="flex flex-col gap-1.5 flex-1">
              <p className="flex items-center gap-1.5">
                <span className="font-bold">1.</span> Tap the
                <Share className="w-3.5 h-3.5 inline" style={{ color: '#915527' }} />
                <span className="font-semibold">Share</span> button below
              </p>
              <p className="flex items-center gap-1.5">
                <span className="font-bold">2.</span> Scroll down and tap
                <PlusSquare className="w-3.5 h-3.5 inline" style={{ color: '#915527' }} />
                <span className="font-semibold">Add to Home Screen</span>
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default PWAInstallBanner;
