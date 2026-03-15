import { API as SHARED_API } from '../utils/apiBase';
const API = SHARED_API;

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
 * Check if an image URL points to the old /uploads path (pre-Cloudinary migration).
 */
export function isLegacyUploadUrl(src) {
  if (!src || typeof src !== 'string') return false;
  return src.includes('/uploads/') || src.includes('/api/files/serve/');
}

/**
 * Build a proxy URL for an image to bypass CORS/regional blocks.
 */
export function proxyImageUrl(src) {
  if (!src || typeof src !== 'string') return null;
  if (src.includes('image-proxy')) return src;
  return `${API}/image-proxy?url=${encodeURIComponent(enforceHttps(src))}`;
}

/**
 * Resolve an image URL. Handles four cases:
 * 1. Cloudinary URLs → return as-is (already absolute https)
 * 2. Raw storage path (no http prefix) → build proxy URL
 * 3. Old full URL from a different deployment that contains /api/files/serve/ → rewrite to current domain
 * 4. External URLs (discogs, dicebear, etc.) → return as-is, enforced to https
 */
export function resolveImageUrl(src) {
  if (!src) return null;
  if (typeof src === 'object') return resolveImageUrl(src.url || src.src || null);
  if (typeof src !== 'string') return null;

  // Already proxied — return as-is
  if (src.includes('image-proxy')) return src;

  // Cloudinary URLs — return as-is
  if (src.includes('res.cloudinary.com')) return enforceHttps(src);

  // Case 3: Old URL containing our serve path but pointing to a different domain
  const serveIdx = src.indexOf(SERVE_PATH);
  if (serveIdx !== -1) {
    const storagePath = src.substring(serveIdx + SERVE_PATH.length);
    return enforceHttps(`${API}/files/serve/${storagePath}`);
  }

  // Case 4: External URLs (discogs images, dicebear, data URIs, etc.)
  if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('data:')) {
    return enforceHttps(src);
  }
  if (src.startsWith('/')) return src;

  // Case 2: Raw storage path
  return enforceHttps(`${API}/files/serve/${src}`);
}
