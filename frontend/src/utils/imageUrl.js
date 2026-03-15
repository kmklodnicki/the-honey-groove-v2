import { API as SHARED_API } from '../utils/apiBase';
const API = SHARED_API;

const SERVE_PATH = '/api/files/serve/';

// Emergent storage proxy — serves old images that predate Cloudinary migration
const EMERGENT_STORAGE_PROXY = 'https://migration-staging-4.preview.emergentagent.com/api/files/serve/';

const enforceHttps = (url) => {
  if (!url || typeof url !== 'string') return url;
  if (url.startsWith('http://')) return url.replace('http://', 'https://');
  return url;
};

export function isLegacyUploadUrl(src) {
  if (!src || typeof src !== 'string') return false;
  return src.includes('/uploads/') && !src.includes('res.cloudinary.com');
}

export function proxyImageUrl(src) {
  if (!src || typeof src !== 'string') return null;
  if (src.includes('image-proxy')) return src;
  return `${API}/image-proxy?url=${encodeURIComponent(enforceHttps(src))}`;
}

export function resolveImageUrl(src) {
  if (!src) return null;
  if (typeof src === 'object') return resolveImageUrl(src.url || src.src || null);
  if (typeof src !== 'string') return null;

  // Already proxied
  if (src.includes('image-proxy')) return src;

  // Cloudinary URLs — always work, return as-is
  if (src.includes('res.cloudinary.com')) return enforceHttps(src);

  // Emergent storage proxy — already pointing to working proxy
  if (src.includes('migration-staging-4.preview.emergentagent.com')) return enforceHttps(src);

  // Old URL containing /api/files/serve/ from ANY domain → rewrite to working Emergent proxy
  const serveIdx = src.indexOf(SERVE_PATH);
  if (serveIdx !== -1) {
    const storagePath = src.substring(serveIdx + SERVE_PATH.length);
    return `${EMERGENT_STORAGE_PROXY}${storagePath}`;
  }

  // External URLs (discogs, dicebear, data URIs)
  if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('data:')) {
    return enforceHttps(src);
  }
  if (src.startsWith('/')) return src;

  // Raw storage path → route through Emergent proxy
  return `${EMERGENT_STORAGE_PROXY}${src}`;
}
