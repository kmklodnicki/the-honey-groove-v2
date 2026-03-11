const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

const SERVE_PATH = '/api/files/serve/';

/**
 * Force any http:// URL to https:// for mobile browser compatibility.
 * Mobile Safari/Chrome silently block mixed-content http images.
 */
const enforceHttps = (url) => {
  if (!url || typeof url !== 'string') return url;
  if (url.startsWith('http://')) return url.replace('http://', 'https://');
  return url;
};

/**
 * Build a proxy URL for an image to bypass CORS/regional blocks.
 */
export function proxyImageUrl(src) {
  if (!src) return null;
  return `${API}/image-proxy?url=${encodeURIComponent(enforceHttps(src))}`;
}

/**
 * Resolve an image URL. Handles three cases:
 * 1. Raw storage path (no http prefix) → build proxy URL
 * 2. Old full URL from a different deployment that contains /api/files/serve/ → rewrite to current domain
 * 3. External URLs (discogs, dicebear, etc.) → return as-is, enforced to https
 */
export function resolveImageUrl(src) {
  if (!src) return null;

  // Case 2: Old URL containing our serve path but pointing to a different domain
  const serveIdx = src.indexOf(SERVE_PATH);
  if (serveIdx !== -1) {
    const storagePath = src.substring(serveIdx + SERVE_PATH.length);
    return enforceHttps(`${API}/files/serve/${storagePath}`);
  }

  // Case 3: External URLs (discogs images, dicebear, data URIs, etc.)
  if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('data:')) {
    return enforceHttps(src);
  }
  if (src.startsWith('/')) return src;

  // Case 1: Raw storage path
  return enforceHttps(`${API}/files/serve/${src}`);
}
