import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

/**
 * Hook that fetches blur placeholder data for a batch of cover URLs.
 * Returns a map: { [coverUrl]: { blur_data_url, thumb_url } }
 */
export function useBlurPlaceholders(coverUrls) {
  const [blurMap, setBlurMap] = useState({});
  const fetchedRef = useRef(new Set());

  useEffect(() => {
    if (!coverUrls || coverUrls.length === 0) return;
    // Filter to only Discogs URLs we haven't fetched yet
    const newUrls = coverUrls.filter(
      u => u && u.includes('discogs.com') && !fetchedRef.current.has(u) && !blurMap[u]
    );
    if (newUrls.length === 0) return;

    // Mark as fetching to avoid re-fetches
    newUrls.forEach(u => fetchedRef.current.add(u));

    // Batch fetch (max 50 per request)
    const batch = newUrls.slice(0, 50);
    axios.post(`${API}/image/blur-batch`, { urls: batch })
      .then(res => {
        if (res.data?.results) {
          setBlurMap(prev => ({ ...prev, ...res.data.results }));
        }
      })
      .catch(() => { /* silent fail */ });
  }, [coverUrls, blurMap]);

  return blurMap;
}
