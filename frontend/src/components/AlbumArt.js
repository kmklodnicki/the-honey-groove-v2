import React, { useState, useEffect } from 'react';
import { Disc } from 'lucide-react';
import { resolveImageUrl, proxyImageUrl } from '../utils/imageUrl';

const FALLBACK = '/vinyl-placeholder.svg';

const AlbumArt = ({
  src,
  alt = '',
  className = '',
  style,
  artist,
  title,
  blurDataUrl,
  thumbSrc,
  priority = false,
  ...props
}) => {
  const resolvedSrc = resolveImageUrl(src);
  const [status, setStatus] = useState(resolvedSrc ? 'loading' : 'error');
  // The blur source: prefer inline base64, fall back to small thumb URL
  const blurSrc = blurDataUrl || thumbSrc || null;

  useEffect(() => {
    setStatus(resolveImageUrl(src) ? 'loading' : 'error');
  }, [src]);

  useEffect(() => {
    if (status !== 'loading') return;
    const t = setTimeout(() => setStatus(s => s === 'loading' ? 'error' : s), 8000);
    return () => clearTimeout(t);
  }, [status]);

  const showGlassFallback = status === 'error' && (artist || title);

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {/* Layer 1: Blur placeholder OR grey shimmer */}
      {status === 'loading' && (
        blurSrc ? (
          <div className="absolute inset-0">
            <img
              src={blurSrc}
              alt=""
              aria-hidden="true"
              className="absolute inset-0 w-full h-full object-cover"
              style={{ filter: 'blur(20px)', transform: 'scale(1.2)' }}
              draggable={false}
            />
            <div className="absolute inset-0 honey-shimmer-overlay" />
          </div>
        ) : (
          <div className="absolute inset-0 honey-shimmer" />
        )
      )}

      {/* Layer 2: Glass fallback (no cover art at all) */}
      {showGlassFallback ? (
        <div
          className="w-full h-full flex flex-col items-center justify-center p-3 text-center honey-fade-in"
          style={{
            background: 'linear-gradient(135deg, rgba(255,246,230,0.9), rgba(218,165,32,0.15))',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
          }}
        >
          <Disc className="w-8 h-8 text-[#DAA520] opacity-30 mb-2" />
          {title && <p className="text-xs font-bold text-vinyl-black/80 leading-tight line-clamp-2">{title}</p>}
          {artist && <p className="text-[10px] text-vinyl-black/50 mt-0.5 truncate max-w-full">{artist}</p>}
        </div>
      ) : (
        /* Layer 3: High-res image — fades in over blur */
        <img
          src={status === 'error' || !resolvedSrc ? FALLBACK : resolvedSrc}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity duration-300 ease-in ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
          crossOrigin="anonymous"
          onLoad={() => setStatus('loaded')}
          onError={(e) => {
            if (!e.target.dataset.proxied && resolvedSrc) {
              e.target.dataset.proxied = '1';
              e.target.src = proxyImageUrl(src);
            } else {
              setStatus('error');
            }
          }}
          draggable={false}
          decoding={priority ? 'sync' : 'auto'}
          {...(priority ? { fetchPriority: 'high', loading: 'eager' } : {})}
        />
      )}
    </div>
  );
};

export default AlbumArt;
