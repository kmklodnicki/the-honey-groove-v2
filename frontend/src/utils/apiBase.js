// Single source of truth for API base URL.
// Falls back to window.location.origin so production deployments
// always talk to their own backend, regardless of build-time env.
const BASE = process.env.REACT_APP_BACKEND_URL || window.location.origin;
export const API_BASE = BASE;           // e.g. https://thehoneygroove.com
export const API = `${BASE}/api`;       // e.g. https://thehoneygroove.com/api
