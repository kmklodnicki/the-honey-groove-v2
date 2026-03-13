// Single source of truth for API base URL.
// On custom domains (e.g. thehoneygroove.com), uses same-origin to avoid CORS.
// On preview/localhost, uses the env variable.
const BASE = (() => {
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  if (!envUrl) return window.location.origin;
  try {
    const envHost = new URL(envUrl).hostname;
    const currentHost = window.location.hostname;
    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1' && currentHost !== envHost) {
      return window.location.origin;
    }
  } catch {}
  return envUrl;
})();
export const API_BASE = BASE;
export const API = `${BASE}/api`;
