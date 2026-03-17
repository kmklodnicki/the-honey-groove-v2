/**
 * Image prefetch utility — BLOCK 444 & 448
 * Uses requestIdleCallback to prefetch images without stealing bandwidth.
 * Maintains an in-memory dedup set to prevent redundant requests.
 */

const _prefetched = new Set();

/**
 * Prefetch a single image URL during idle time.
 * Skips if already prefetched this session.
 */
export function prefetchImage(url) {
  if (!url || _prefetched.has(url)) return;
  _prefetched.add(url);

  const run = () => {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.as = 'image';
    link.href = url;
    // Only set crossOrigin for same-origin or CORS-enabled URLs
    // Discogs CDN doesn't support CORS, so skip it for those
    if (!url.includes('discogs.com')) {
      link.crossOrigin = 'anonymous';
    }
    document.head.appendChild(link);
  };

  if ('requestIdleCallback' in window) {
    requestIdleCallback(run, { timeout: 3000 });
  } else {
    setTimeout(run, 100);
  }
}

/**
 * Prefetch multiple image URLs. Deduplicates automatically.
 * Also sends URLs to the service worker for persistent caching.
 */
export function prefetchImages(urls) {
  const newUrls = urls.filter(u => u && !_prefetched.has(u));
  if (newUrls.length === 0) return;

  newUrls.forEach(u => prefetchImage(u));

  // Also send to service worker for persistent cache
  if (navigator.serviceWorker?.controller) {
    navigator.serviceWorker.controller.postMessage({
      type: 'PREFETCH_IMAGES',
      urls: newUrls,
    });
  }
}

/**
 * Check if an image URL has already been prefetched this session.
 */
export function isPrefetched(url) {
  return _prefetched.has(url);
}
