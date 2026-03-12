import React, { useState, useEffect } from 'react';
import { Disc } from 'lucide-react';
import { resolveImageUrl, proxyImageUrl } from '../utils/imageUrl';

const FALLBACK = '/vinyl-placeholder.svg';

const AlbumArt = ({
  src,
  alt = '',
  className = '',
  style,
  blurDataUrl,
  thumbSrc,
  priority = false,
  ...props
}) => {
  const resolvedSrc = resolveImageUrl(src);
  const [status, setStatus] = useState(resolvedSrc ? 'loading' : 'error');
  const blurSrc = blurDataUrl || thumbSrc || null;

  useEffect(() => {
    setStatus(resolveImageUrl(src) ? 'loading' : 'error');
  }, [src]);

  useEffect(() => {
    if (status !== 'loading') return;
    const t = setTimeout(() => setStatus(s => s === 'loading' ? 'error' : s), 8000);
    return () => clearTimeout(t);
  }, [status]);

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {/* BLOCK 565: Glassy shimmer skeleton while loading — no text overlay */}
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
            <div className="absolute inset-0 silk-shimmer" />
          </div>
        ) : (
          <div className="absolute inset-0 silk-shimmer" />
        )
      )}

      {/* BLOCK 565: Error state — clean charcoal vinyl icon, no text, no broken image */}
      {status === 'error' ? (
        <div
          className="w-full h-full flex items-center justify-center honey-fade-in"
          style={{ background: 'rgba(245, 243, 238, 1)' }}
        >
          <Disc className="w-10 h-10" style={{ color: '#4A4A4A', opacity: 0.35 }} />
        </div>
      ) : (
        /* BLOCK 565: Smooth 0.4s fade-in over shimmer */
        <img
          src={!resolvedSrc ? FALLBACK : resolvedSrc}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity ease-in-out ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDuration: '0.4s' }}
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
