/**
 * useAPI — SWR-powered data fetching hook for The HoneyGroove
 * BLOCK 450: Instant Nav Overhaul
 *
 * Provides automatic caching, deduplication, and stale-while-revalidate
 * behavior for all API calls. Navigating back to a page shows cached data
 * instantly while revalidating in the background.
 */
import useSWR from 'swr';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

/**
 * Authenticated fetcher — used by SWR internally.
 * Accepts [url, token] as key.
 */
const authedFetcher = async ([url, token]) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const resp = await axios.get(url, { headers });
  return resp.data;
};

/**
 * useAPI — SWR wrapper with auth.
 *
 * @param {string|null} path - API path (e.g. "/users/katie") or null to skip
 * @param {object} options - SWR options override
 * @returns {{ data, error, isLoading, isValidating, mutate }}
 *
 * Usage:
 *   const { data: profile, isLoading } = useAPI(`/users/${username}`);
 *   const { data: records } = useAPI(username ? `/users/${username}/records` : null);
 */
export function useAPI(path, options = {}) {
  const { token, API } = useAuth();
  const url = path ? `${API}${path}` : null;
  const key = url ? [url, token] : null;

  return useSWR(key, authedFetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 10000, // 10s dedup — prevents duplicate requests on fast nav
    ...options,
  });
}

/**
 * useAPIMultiple — Fetch multiple endpoints in parallel, all cached.
 * Returns an array of SWR results.
 *
 * @param {Array<string|null>} paths - Array of API paths
 * @returns {Array<{ data, error, isLoading, mutate }>}
 */
export function useAPIMultiple(paths) {
  // SWR hooks must be called unconditionally, so we use a fixed-length approach
  // For variable-length, callers should use individual useAPI calls instead
  return paths.map(p => useAPI(p)); // eslint-disable-line react-hooks/rules-of-hooks
}

/**
 * Prefetch — warm the SWR cache for a path before the user navigates.
 * Call this on hover/focus of navigation links.
 */
export function prefetchAPI(API, token, path) {
  if (!path || !API) return;
  const url = `${API}${path}`;
  const key = [url, token];
  // SWR mutate with no data just triggers revalidation
  import('swr').then(({ mutate }) => {
    mutate(key, authedFetcher(key), { revalidate: false });
  });
}
