const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

const SERVE_PATH = '/api/files/serve/';

/**
 * Resolve an image URL. Handles three cases:
 * 1. Raw storage path (no http prefix) → build proxy URL
 * 2. Old full URL from a different deployment that contains /api/files/serve/ → rewrite to current domain
 * 3. External URLs (discogs, dicebear, etc.) → return as-is
 */
export function resolveImageUrl(src) {
  if (!src) return null;

  // Case 2: Old URL containing our serve path but pointing to a different domain
  const serveIdx = src.indexOf(SERVE_PATH);
  if (serveIdx !== -1) {
    const storagePath = src.substring(serveIdx + SERVE_PATH.length);
    return `${API}/files/serve/${storagePath}`;
  }

  // Case 3: External URLs (discogs images, dicebear, data URIs, etc.)
  if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('/') || src.startsWith('data:')) return src;

  // Case 1: Raw storage path
  return `${API}/files/serve/${src}`;
}
