// Single source of truth for API base URL.
// Always uses the build-time env URL (fast preview endpoint) for API calls.
// The production custom domain adds significant proxy latency, so we bypass it.
const BASE = process.env.REACT_APP_BACKEND_URL || window.location.origin;
export const API_BASE = BASE;
export const API = `${BASE}/api`;
