/* Service Worker — HoneyGroove Performance Cache */
/* eslint-disable no-restricted-globals */

const STATIC_CACHE = 'honeygroove-static-v3';
const IMG_CACHE = 'honeygroove-img-v3';
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
      cache.addAll(PRECACHE_ASSETS).catch(() => {
        // Non-critical: continue even if some assets fail
      })
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

  // ─── Image requests: Cache-first with LRU eviction ───
  const isImage =
    url.pathname.includes('/api/image-proxy') ||
    url.pathname.includes('/api/files/serve/') ||
    url.hostname.includes('discogs.com') ||
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
              // Evict oldest 10 entries at once to reduce overhead
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
        cache.match(url).then((cached) => {
          if (!cached) {
            fetch(url, { mode: 'cors', credentials: 'omit' })
              .then((resp) => { if (resp.ok) cache.put(url, resp); })
              .catch(() => {}); // Non-critical
          }
        });
      });
    });
  }

  // BLOCK 321: Daily Prompt image pre-cache
  // Main thread sends the prompt image URL after fetching /prompts/today
  // We cache it eagerly with high priority so it's instant on next visit
  if (event.data?.type === 'PREFETCH_DAILY_PROMPT') {
    const urls = event.data.urls || [];
    if (urls.length === 0) return;
    caches.open(IMG_CACHE).then((cache) => {
      // Pre-cache all prompt-related images (prompt artwork + first few responses)
      urls.forEach((url) => {
        cache.match(url).then((cached) => {
          if (!cached) {
            fetch(url, { mode: 'cors', credentials: 'omit' })
              .then((resp) => {
                if (resp.ok) {
                  // Put in cache with high priority — evict old entries if needed
                  cache.put(url, resp);
                }
              })
              .catch(() => {});
          }
        });
      });
    });
  }
});
