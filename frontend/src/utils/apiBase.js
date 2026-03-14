// Single source of truth for API base URL.
// HARDCODED to the fast preview URL to bypass the slow production domain proxy.
// The production custom domain (thehoneygroove.com) adds ~20s latency per request.
const BASE = 'https://vinyl-shield-prod.preview.emergentagent.com';
export const API_BASE = BASE;
export const API = `${BASE}/api`;
