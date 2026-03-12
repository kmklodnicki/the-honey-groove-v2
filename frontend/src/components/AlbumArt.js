import React, { useState, useEffect, useRef } from 'react';
import { Disc } from 'lucide-react';
import { resolveImageUrl, proxyImageUrl } from '../utils/imageUrl';

const FALLBACK = '/vinyl-placeholder.svg';
const ART_CACHE_NAME = 'honeygroove-album-art-v1';

// BLOCK 567: Request WebP variant when possible
const toWebP = (url) => {
  if (!url) return url;
  // Discogs CDN supports format param
  if (url.includes('discogs') && !url.includes('.webp')) {
    return url.replace(/\.(jpe?g|png)$/i, '.webp');
  }
  return url;
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
  ...props
}) => {
  const resolvedSrc = resolveImageUrl(src);
  const webpSrc = toWebP(resolvedSrc);
  const [status, setStatus] = useState(resolvedSrc ? 'loading' : 'error');
  const [displaySrc, setDisplaySrc] = useState(null);
  const blurSrc = blurDataUrl || thumbSrc || null;
  const imgRef = useRef(null);

  useEffect(() => {
    const resolved = resolveImageUrl(src);
    if (!resolved) { setStatus('error'); return; }
    setStatus('loading');

    // BLOCK 567: Try CacheStorage first for 0ms render on back-navigation
    let cancelled = false;
    const webp = toWebP(resolved);
    getCachedArt(webp || resolved).then((cached) => {
      if (cancelled) return;
      if (cached) {
        setDisplaySrc(cached);
        setStatus('loaded');
      } else {
        setDisplaySrc(webp || resolved);
      }
    });
    return () => { cancelled = true; };
  }, [src]);

  useEffect(() => {
    if (status !== 'loading') return;
    const t = setTimeout(() => setStatus(s => s === 'loading' ? 'error' : s), 8000);
    return () => clearTimeout(t);
  }, [status]);

  return (
    // BLOCK 568: Zero-jitter — locked aspect-square is set by parent, overflow hidden
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {/* BLOCK 565: Glassy shimmer skeleton while loading */}
      {status === 'loading' && (
        blurSrc ? (
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
        )
      )}

      {/* BLOCK 565: Error state — charcoal vinyl icon */}
      {status === 'error' ? (
        <div
          className="w-full h-full flex items-center justify-center honey-fade-in"
          style={{ background: 'rgba(245, 243, 238, 1)' }}
        >
          <Disc className="w-10 h-10" style={{ color: '#4A4A4A', opacity: 0.35 }} />
        </div>
      ) : (
        /* BLOCK 565/567: Smooth 0.4s fade-in, priority loading for above-the-fold */
        <img
          ref={imgRef}
          src={displaySrc || (!resolvedSrc ? FALLBACK : webpSrc || resolvedSrc)}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity ease-in-out ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDuration: '0.4s' }}
          crossOrigin="anonymous"
          onLoad={async (e) => {
            setStatus('loaded');
            // BLOCK 567: Cache the loaded image for instant back-nav
            if (webpSrc && 'caches' in window) {
              try {
                const resp = await fetch(e.target.src, { mode: 'cors' });
                if (resp.ok) cacheArt(webpSrc, resp);
              } catch { /* skip caching */ }
            }
          }}
          onError={(e) => {
            if (!e.target.dataset.proxied && resolvedSrc) {
              e.target.dataset.proxied = '1';
              e.target.src = proxyImageUrl(src);
            } else if (!e.target.dataset.webpFailed && webpSrc !== resolvedSrc) {
              // Fall back from WebP to original format
              e.target.dataset.webpFailed = '1';
              e.target.src = resolvedSrc;
            } else {
              setStatus('error');
            }
          }}
          draggable={false}
          decoding={priority ? 'sync' : 'auto'}
          loading={priority ? 'eager' : 'lazy'}
          {...(priority ? { fetchPriority: 'high' } : {})}
        />
      )}
    </div>
  );
};

// BLOCK 567: Predictive prefetch — call from parent to preload URLs 2 rows ahead
export const prefetchArt = (urls) => {
  if (!urls?.length) return;
  urls.forEach((url) => {
    const resolved = resolveImageUrl(url);
    if (!resolved) return;
    const webp = toWebP(resolved);
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.as = 'image';
    link.href = webp || resolved;
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
    // Cleanup after 30s
    setTimeout(() => link.remove(), 30000);
  });
};

export default AlbumArt;
