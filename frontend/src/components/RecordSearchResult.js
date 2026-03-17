import React, { useState } from 'react';
import { Disc } from 'lucide-react';
import { API as SHARED_API } from '../utils/apiBase';

const proxyDiscogsUrl = (src) => {
  if (!src || typeof src !== 'string') return src;
  if (src.includes('discogs') || src.includes('discogs.com')) {
    return `${SHARED_API}/image-proxy?url=${encodeURIComponent(src)}`;
  }
  return src;
};

// Simple image component for search results — proxies Discogs CDN images
// to avoid hotlink blocking on production domains.
const SearchResultImage = ({ src, alt, className }) => {
  const [failed, setFailed] = useState(false);
  const proxiedSrc = proxyDiscogsUrl(src);
  if (failed || !proxiedSrc) {
    return (
      <div className={`${className} rounded-md bg-stone-100 flex items-center justify-center`}>
        <Disc className="w-5 h-5 text-stone-400" />
      </div>
    );
  }
  return (
    <img
      src={proxiedSrc}
      alt={alt}
      className={`${className} rounded-md object-cover shadow-sm`}
      loading="eager"
      referrerPolicy="no-referrer"
      crossOrigin="anonymous"
      onError={() => setFailed(true)}
      data-testid="search-result-img"
    />
  );
};

const RecordSearchResult = ({ record, onClick, actions, size = 'md', testId }) => {
  const r = record;
  const imgSize = size === 'sm' ? 'w-10 h-10' : 'w-12 h-12';
  const titleSize = size === 'sm' ? 'text-sm' : 'text-sm';

  // Build detail lines
  const line1Parts = [r.year, r.label, r.catno].filter(Boolean);
  const line2Parts = [r.format].filter(Boolean);
  if (r.country) line2Parts.push(r.country);

  return (
    <div
      className="flex items-center gap-3 p-2 rounded-lg hover:bg-honey/10 cursor-pointer group"
      onClick={onClick}
      data-testid={testId}
    >
      <div className="shrink-0">
        {r.cover_url ? (
          <SearchResultImage src={r.cover_url} alt={`${r.artist} ${r.title}`} className={imgSize} />
        ) : (
          <div className={`${imgSize} rounded-md bg-stone-100 flex items-center justify-center`}>
            <Disc className="w-5 h-5 text-stone-400" />
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`${titleSize} font-medium truncate`}>{r.title}</p>
        <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
        {line1Parts.length > 0 && (
          <p className="text-[11px] text-muted-foreground truncate mt-0.5">
            {line1Parts.join(' \u00B7 ')}
          </p>
        )}
        {(line2Parts.length > 0 || r.color_variant) && (
          <p className="text-[11px] text-muted-foreground truncate flex items-center gap-1 mt-0.5">
            <span>{line2Parts.join(' \u00B7 ')}</span>
            {r.color_variant && (
              <span className="inline-flex items-center px-1.5 py-0 rounded-full text-[10px] font-medium bg-amber-100 text-amber-700 border border-amber-200/60 whitespace-nowrap">
                {r.color_variant}
              </span>
            )}
          </p>
        )}
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </div>
  );
};

export default RecordSearchResult;
