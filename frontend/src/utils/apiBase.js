// Single source of truth for API base URL.
const BASE = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = BASE;
export const API = `${BASE}/api`;
