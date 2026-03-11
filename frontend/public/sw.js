/* Service Worker — HoneyGroove Asset Cache */
/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'honeygroove-img-v1';
const IMG_CACHE_MAX = 80;

// Force activation: skip waiting + claim clients immediately
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME)
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Cache image responses on the fly
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only cache image requests (proxy, discogs, files/serve)
  const isImage =
    url.pathname.includes('/api/image-proxy') ||
    url.pathname.includes('/api/files/serve/') ||
    url.hostname.includes('discogs.com') ||
    /\.(jpe?g|png|webp|gif|svg)(\?|$)/i.test(url.pathname);

  if (!isImage || request.method !== 'GET') return;

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(request);
      if (cached) return cached;

      try {
        const response = await fetch(request);
        if (response.ok) {
          // Trim cache if over limit
          const keys = await cache.keys();
          if (keys.length >= IMG_CACHE_MAX) {
            await cache.delete(keys[0]);
          }
          cache.put(request, response.clone());
        }
        return response;
      } catch {
        return new Response('', { status: 503 });
      }
    })
  );
});
