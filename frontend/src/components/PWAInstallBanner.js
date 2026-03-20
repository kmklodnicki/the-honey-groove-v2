import React, { useState, useEffect, useCallback, useRef } from 'react';
import { X, Share, PlusSquare } from 'lucide-react';

const isStandalone = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  window.matchMedia('(display-mode: fullscreen)').matches ||
  window.matchMedia('(display-mode: minimal-ui)').matches ||
  window.navigator.standalone === true ||
  document.referrer.includes('android-app://');

const isIOS = () =>
  /iPad|iPhone|iPod/.test(navigator.userAgent) ||
  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

const setBannerHeight = (px) => {
  document.documentElement.style.setProperty('--pwa-banner-h', `${px}px`);
};

const PWAInstallBanner = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showBanner, setShowBanner] = useState(false);
  const [showIOSGuide, setShowIOSGuide] = useState(false);
  const bannerRef = useRef(null);

  // Sync CSS variable with actual rendered banner height
  useEffect(() => {
    if (!showBanner) {
      setBannerHeight(0);
      return;
    }
    const measure = () => {
      if (bannerRef.current) setBannerHeight(bannerRef.current.offsetHeight);
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (bannerRef.current) ro.observe(bannerRef.current);
    return () => ro.disconnect();
  }, [showBanner, showIOSGuide]);

  useEffect(() => {
    // Already running as installed app — never show
    if (isStandalone()) return;
    // User previously installed or dismissed — check multiple storage mechanisms
    try { if (localStorage.getItem('pwa_installed') === 'true') return; } catch { /* noop */ }
    try { if (localStorage.getItem('pwa_banner_dismissed') === 'true') return; } catch { /* noop */ }
    if (document.cookie.includes('pwa_dismissed=1')) return;

    // Listen for standalone mode changes (user installs while page is open)
    const mq = window.matchMedia('(display-mode: standalone)');
    const onStandaloneChange = (e) => {
      if (e.matches) {
        setShowBanner(false);
        setBannerHeight(0);
        try { localStorage.setItem('pwa_installed', 'true'); } catch { /* noop */ }
      }
    };
    mq.addEventListener('change', onStandaloneChange);

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

    const isMobile = /Android|webOS|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    let fallbackTimer;
    if (isMobile) {
      fallbackTimer = setTimeout(() => setShowBanner(true), 2000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      mq.removeEventListener('change', onStandaloneChange);
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
    setBannerHeight(0);
    try { localStorage.setItem('pwa_installed', 'true'); } catch { /* noop */ }
    try { localStorage.setItem('pwa_banner_dismissed', 'true'); } catch { /* noop */ }
    // Cookie fallback for when localStorage is cleared (e.g., Safari ITP)
    try { document.cookie = 'pwa_dismissed=1;max-age=31536000;path=/;SameSite=Lax'; } catch { /* noop */ }
  }, []);

  if (!showBanner) return null;

  return (
    <>
      {/* Spacer — height matches the fixed banner via CSS variable */}
      <div style={{ height: 'var(--pwa-banner-h, 0px)' }} data-testid="pwa-banner-spacer" />

      <div
        ref={bannerRef}
        className="fixed top-0 left-0 w-full"
        style={{
          zIndex: 101,
          paddingTop: 'env(safe-area-inset-top, 0px)',
        }}
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
            className="ml-1 p-1.5 rounded-full transition-colors hover:bg-[#E8CA5A]/50 active:bg-[#F0E6C8]"
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
