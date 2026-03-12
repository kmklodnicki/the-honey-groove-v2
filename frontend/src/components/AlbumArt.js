import React, { useState, useEffect, useRef } from 'react';
import { Disc } from 'lucide-react';
import { resolveImageUrl, proxyImageUrl } from '../utils/imageUrl';
import UnofficialPill from './UnofficialPill';

const FALLBACK = '/vinyl-placeholder.svg';
const ART_CACHE_NAME = 'honeygroove-album-art-v1';
// BLOCK 571: Cache-bust version — forces fresh asset downloads
const ASSET_VERSION = '2.3.9';

// BLOCK 567: Request WebP variant when possible
const toWebP = (url) => {
  if (!url) return url;
  if (url.includes('discogs') && !url.includes('.webp')) {
    return url.replace(/\.(jpe?g|png)$/i, '.webp');
  }
  return url;
};

// BLOCK 571: Append cache-bust version to image URLs
const bustCache = (url) => {
  if (!url) return url;
  const sep = url.includes('?') ? '&' : '?';
  return `${url}${sep}v=${ASSET_VERSION}`;
};

// BLOCK 567: Blob caching via CacheStorage API
const cacheArt = async (url, response) => {
  try {
    if ('caches' in window) {
      const cache = await caches.open(ART_CACHE_NAME);
      await cache.put(url, response.clone());
    }
  } catch { /* silently fail */ }
};

const getCachedArt = async (url) => {
  try {
    if ('caches' in window) {
      const cache = await caches.open(ART_CACHE_NAME);
      const cached = await cache.match(url);
      if (cached) return URL.createObjectURL(await cached.blob());
    }
  } catch { /* silently fail */ }
  return null;
};

const AlbumArt = ({
  src,
  alt = '',
  className = '',
  style,
  blurDataUrl,
  thumbSrc,
  priority = false,
  isUnofficial = false,
  ...props
}) => {
  const resolvedSrc = resolveImageUrl(src);
  const webpSrc = toWebP(resolvedSrc);
  const [status, setStatus] = useState(resolvedSrc ? 'loading' : 'error');
  const [displaySrc, setDisplaySrc] = useState(null);
  // BLOCK 572: Track whether thumb has been shown as instant preview
  const [showThumb, setShowThumb] = useState(false);
  const blurSrc = blurDataUrl || thumbSrc || null;
  const imgRef = useRef(null);

  useEffect(() => {
    const resolved = resolveImageUrl(src);
    if (!resolved) { setStatus('error'); return; }
    setStatus('loading');
    setShowThumb(false);

    let cancelled = false;
    const webp = toWebP(resolved);
    getCachedArt(webp || resolved).then((cached) => {
      if (cancelled) return;
      if (cached) {
        setDisplaySrc(cached);
        setStatus('loaded');
      } else {
        setDisplaySrc(bustCache(webp || resolved));
      }
    });

    // BLOCK 572: If hi-res hasn't loaded in 50ms, show the thumb instantly
    const thumbTimer = setTimeout(() => {
      if (!cancelled) setShowThumb(true);
    }, 50);

    return () => { cancelled = true; clearTimeout(thumbTimer); };
  }, [src]);

  // BLOCK 572: 8s timeout → show shimmer indefinitely (not broken icon)
  useEffect(() => {
    if (status !== 'loading') return;
    const t = setTimeout(() => setStatus(s => s === 'loading' ? 'shimmer' : s), 8000);
    return () => clearTimeout(t);
  }, [status]);

  // BLOCK 572: "shimmer" state = image failed but we show glass shimmer, not broken icon
  const isLoading = status === 'loading' || status === 'shimmer';

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {/* Loading state: shimmer + optional thumb preview */}
      {isLoading && (
        <>
          {/* BLOCK 572: Show thumb instantly after 50ms for immediate visibility */}
          {showThumb && blurSrc ? (
            <div className="absolute inset-0">
              <img
                src={blurSrc}
                alt=""
                aria-hidden="true"
                className="absolute inset-0 w-full h-full object-cover"
                style={{ filter: 'blur(20px)', transform: 'scale(1.2)' }}
                draggable={false}
              />
              <div className="absolute inset-0 silk-shimmer" />
            </div>
          ) : (
            <div className="absolute inset-0 silk-shimmer" />
          )}
        </>
      )}

      {/* Error state: charcoal vinyl icon — BLOCK 572: never show browser broken icon */}
      {status === 'error' ? (
        <div
          className="w-full h-full flex items-center justify-center honey-fade-in"
          style={{ background: 'rgba(245, 243, 238, 1)' }}
        >
          <Disc className="w-10 h-10" style={{ color: '#4A4A4A', opacity: 0.35 }} />
        </div>
      ) : status !== 'shimmer' ? (
        <img
          ref={imgRef}
          src={displaySrc || (!resolvedSrc ? FALLBACK : bustCache(webpSrc || resolvedSrc))}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity ease-in-out ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDuration: '0.4s' }}
          crossOrigin="anonymous"
          onLoad={async (e) => {
            setStatus('loaded');
            if (webpSrc && 'caches' in window) {
              try {
                const resp = await fetch(e.target.src, { mode: 'cors' });
                if (resp.ok) cacheArt(webpSrc, resp);
              } catch { /* skip caching */ }
            }
          }}
          onError={(e) => {
            // BLOCK 574: Cascade fallback — internal proxy (fast) → WebP fallback → original → error
            if (!e.target.dataset.proxied && resolvedSrc) {
              e.target.dataset.proxied = '1';
              e.target.src = bustCache(proxyImageUrl(src));
            } else if (!e.target.dataset.webpFailed && webpSrc !== resolvedSrc) {
              e.target.dataset.webpFailed = '1';
              e.target.src = bustCache(resolvedSrc);
            } else {
              setStatus('error');
            }
          }}
          draggable={false}
          decoding={priority ? 'sync' : 'auto'}
          loading="eager"
          {...(priority ? { fetchPriority: 'high' } : {})}
        />
      ) : null}
      {isUnofficial && <UnofficialPill variant="overlay" className="!top-auto !bottom-1.5 !left-1.5 !right-auto" />}
    </div>
  );
};

// BLOCK 567: Predictive prefetch
export const prefetchArt = (urls) => {
  if (!urls?.length) return;
  urls.forEach((url) => {
    const resolved = resolveImageUrl(url);
    if (!resolved) return;
    const webp = toWebP(resolved);
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.as = 'image';
    link.href = bustCache(webp || resolved);
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
    setTimeout(() => link.remove(), 30000);
  });
};

export default AlbumArt;
