/* Service Worker — HoneyGroove Performance Cache */
/* eslint-disable no-restricted-globals */

const STATIC_CACHE = 'honeygroove-static-v4';
const IMG_CACHE = 'honeygroove-img-v4';
const IMG_CACHE_MAX = 150;

// Static assets to pre-cache on install for instant second-visit loads
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/vinyl-placeholder.svg',
  '/manifest.json',
];

// Force activation: skip waiting + claim clients immediately
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) =>
      cache.addAll(PRECACHE_ASSETS).catch(() => {})
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== STATIC_CACHE && k !== IMG_CACHE)
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Cache strategy: images use cache-first, static assets use stale-while-revalidate
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') return;

  // NEVER intercept Discogs CDN — let the browser handle these natively.
  // Service worker fetch for cross-origin images can cause opaque response issues.
  if (url.hostname.includes('discogs.com')) return;

  // ─── Image requests: Cache-first with LRU eviction ───
  // Only cache our own proxied images and local files
  const isImage =
    url.pathname.includes('/api/image-proxy') ||
    url.pathname.includes('/api/files/serve/') ||
    /\.(jpe?g|png|webp|gif|svg)(\?|$)/i.test(url.pathname);

  if (isImage) {
    event.respondWith(
      caches.open(IMG_CACHE).then(async (cache) => {
        const cached = await cache.match(request);
        if (cached) return cached;

        try {
          const response = await fetch(request);
          if (response.ok) {
            const keys = await cache.keys();
            if (keys.length >= IMG_CACHE_MAX) {
              const toEvict = keys.slice(0, 10);
              await Promise.all(toEvict.map((k) => cache.delete(k)));
            }
            cache.put(request, response.clone());
          }
          return response;
        } catch {
          return new Response('', { status: 503 });
        }
      })
    );
    return;
  }

  // ─── Static assets (CSS, JS, fonts): Stale-while-revalidate ───
  const isStatic =
    /\.(css|js|woff2?|ttf|eot)(\?|$)/i.test(url.pathname) ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com') ||
    url.hostname.includes('cdnjs.cloudflare.com');

  if (isStatic) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(async (cache) => {
        const cached = await cache.match(request);
        const fetchPromise = fetch(request).then((response) => {
          if (response.ok) {
            cache.put(request, response.clone());
          }
          return response;
        }).catch(() => cached || new Response('', { status: 503 }));

        return cached || fetchPromise;
      })
    );
    return;
  }
});

// ─── Message handler for prefetch requests from the main thread ───
self.addEventListener('message', (event) => {
  if (event.data?.type === 'PREFETCH_IMAGES') {
    const urls = event.data.urls || [];
    caches.open(IMG_CACHE).then((cache) => {
      urls.forEach((url) => {
        // Skip Discogs CDN URLs — can't prefetch cross-origin without CORS
        if (url.includes('discogs.com')) return;
        cache.match(url).then((cached) => {
          if (!cached) {
            fetch(url, { mode: 'cors', credentials: 'omit' })
              .then((resp) => { if (resp.ok) cache.put(url, resp); })
              .catch(() => {});
          }
        });
      });
    });
  }

  if (event.data?.type === 'PREFETCH_DAILY_PROMPT') {
    const urls = event.data.urls || [];
    if (urls.length === 0) return;
    caches.open(IMG_CACHE).then((cache) => {
      urls.forEach((url) => {
        if (url.includes('discogs.com')) return;
        cache.match(url).then((cached) => {
          if (!cached) {
            fetch(url, { mode: 'cors', credentials: 'omit' })
              .then((resp) => { if (resp.ok) cache.put(url, resp); })
              .catch(() => {});
          }
        });
      });
    });
  }
});
