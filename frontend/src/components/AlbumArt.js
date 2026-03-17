import React, { useState, useEffect, useRef } from 'react';
import { Disc } from 'lucide-react';
import { resolveImageUrl, proxyImageUrl, isLegacyUploadUrl } from '../utils/imageUrl';
import UnofficialPill from './UnofficialPill';

const FALLBACK = '/vinyl-placeholder.svg';
const ART_CACHE_NAME = 'honeygroove-album-art-v1';

// Discogs CDN does NOT support WebP extension swapping (returns 403).
// Since we now proxy through image-proxy, skip WebP conversion entirely.
const toWebP = (url) => url;

// Skip cache-busting for proxied URLs (already have query params)
const bustCache = (url) => {
  if (!url || url.includes('image-proxy') || url.includes('discogs.com') || url.includes('res.cloudinary.com')) return url;
  const sep = url.includes('?') ? '&' : '?';
  return `${url}${sep}v=2.4.0`;
};

// In-memory LRU for blob URLs — avoids CacheStorage async overhead on repeat renders
const memCache = new Map();
const MEM_MAX = 200;
const memSet = (key, val) => {
  if (memCache.size >= MEM_MAX) {
    const first = memCache.keys().next().value;
    memCache.delete(first);
  }
  memCache.set(key, val);
};

// CacheStorage write (fire-and-forget)
const cacheArt = async (url, response) => {
  try {
    if ('caches' in window) {
      const cache = await caches.open(ART_CACHE_NAME);
      await cache.put(url, response.clone());
    }
  } catch { /* silently fail */ }
};

// CacheStorage read — only called as background enhancement
const getCachedArt = async (url) => {
  try {
    if ('caches' in window) {
      const cache = await caches.open(ART_CACHE_NAME);
      const cached = await cache.match(url);
      if (cached) {
        const blobUrl = URL.createObjectURL(await cached.blob());
        memSet(url, blobUrl);
        return blobUrl;
      }
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
  formatText = '',
  ...props
}) => {
  const resolvedSrc = resolveImageUrl(src);
  const webpSrc = toWebP(resolvedSrc);
  const cacheKey = webpSrc || resolvedSrc;

  // Check in-memory cache synchronously for instant display
  const memHit = cacheKey ? memCache.get(cacheKey) : null;

  const [status, setStatus] = useState(resolvedSrc ? (memHit ? 'loaded' : 'loading') : 'error');
  const [displaySrc, setDisplaySrc] = useState(memHit || (resolvedSrc ? bustCache(webpSrc || resolvedSrc) : null));
  const [showThumb, setShowThumb] = useState(false);
  const blurSrc = blurDataUrl || thumbSrc || null;
  const imgRef = useRef(null);

  useEffect(() => {
    const resolved = resolveImageUrl(src);
    if (!resolved) { setStatus('error'); return; }

    const webp = toWebP(resolved);
    const key = webp || resolved;

    // Instant hit from memory
    const mem = memCache.get(key);
    if (mem) {
      setDisplaySrc(mem);
      setStatus('loaded');
      setShowThumb(false);
      return;
    }

    // Start loading immediately with the direct URL — don't wait for CacheStorage
    setStatus('loading');
    setShowThumb(false);
    setDisplaySrc(bustCache(key));

    // Background: check CacheStorage for a local blob (faster on repeat visits)
    let cancelled = false;
    getCachedArt(key).then((cached) => {
      if (cancelled || !cached) return;
      setDisplaySrc(cached);
      setStatus('loaded');
    });

    // Show thumb preview after 50ms if still loading
    const thumbTimer = setTimeout(() => {
      if (!cancelled) setShowThumb(true);
    }, 50);

    return () => { cancelled = true; clearTimeout(thumbTimer); };
  }, [src]);

  // 8s timeout → show shimmer indefinitely
  useEffect(() => {
    if (status !== 'loading') return;
    const t = setTimeout(() => setStatus(s => s === 'loading' ? 'shimmer' : s), 8000);
    return () => clearTimeout(t);
  }, [status]);

  const isLoading = status === 'loading' || status === 'shimmer';

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {/* Loading state: shimmer + optional thumb preview */}
      {isLoading && (
        <>
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

      {/* Error state */}
      {status === 'error' ? (
        isLegacyUploadUrl(src) ? (
          <div className="migration-placeholder w-full h-full">
            <Disc className="w-8 h-8 text-amber-700 opacity-60" />
            <span className="migration-placeholder-text">migration in progress</span>
          </div>
        ) : (
        <div
          className="w-full h-full flex items-center justify-center honey-fade-in"
          style={{ background: 'rgba(245, 243, 238, 1)' }}
        >
          <Disc className="w-10 h-10" style={{ color: '#4A4A4A', opacity: 0.35 }} />
        </div>
        )
      ) : (
        <img
          ref={imgRef}
          src={displaySrc || FALLBACK}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity ease-in-out ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDuration: '0.3s' }}
          onLoad={async (e) => {
            setStatus('loaded');
            if (cacheKey) memSet(cacheKey, e.target.src);
          }}
          onError={(e) => {
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
          decoding={priority ? 'sync' : 'async'}
          loading={priority ? 'eager' : 'lazy'}
          {...(priority ? { fetchPriority: 'high' } : {})}
        />
      )}
      {isUnofficial && <UnofficialPill variant="overlay" />}
      {!isUnofficial && formatText && /unofficial/i.test(formatText) && <UnofficialPill variant="overlay" />}
    </div>
  );
};

// Predictive prefetch — fire link preloads for upcoming images
export const prefetchArt = (urls) => {
  if (!urls?.length) return;
  urls.forEach((url) => {
    const resolved = resolveImageUrl(url);
    if (!resolved || memCache.has(toWebP(resolved) || resolved)) return;
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = bustCache(toWebP(resolved) || resolved);
    link.type = 'image/webp';
    document.head.appendChild(link);
    setTimeout(() => link.remove(), 30000);
  });
};

export default AlbumArt;
