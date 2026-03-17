import React, { useState, useEffect } from 'react';
import { Disc } from 'lucide-react';
import { resolveImageUrl, proxyImageUrl, isLegacyUploadUrl } from '../utils/imageUrl';
import UnofficialPill from './UnofficialPill';

const AlbumArt = ({
  src,
  alt = '',
  className = '',
  style,
  priority = false,
  isUnofficial = false,
  formatText = '',
  ...props
}) => {
  const resolvedSrc = resolveImageUrl(src);
  const [imgSrc, setImgSrc] = useState(resolvedSrc);
  const [status, setStatus] = useState(resolvedSrc ? 'loading' : 'error');
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const resolved = resolveImageUrl(src);
    if (!resolved) { setStatus('error'); return; }
    setImgSrc(resolved);
    setStatus('loading');
    setRetryCount(0);
  }, [src]);

  const handleError = () => {
    if (retryCount === 0 && src) {
      // First failure: try through image proxy
      setRetryCount(1);
      setImgSrc(proxyImageUrl(src));
    } else {
      setStatus('error');
    }
  };

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {status === 'error' ? (
        isLegacyUploadUrl(src) ? (
          <div className="migration-placeholder w-full h-full">
            <Disc className="w-8 h-8 text-amber-700 opacity-60" />
            <span className="migration-placeholder-text">migration in progress</span>
          </div>
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{ background: 'rgba(245, 243, 238, 1)' }}
          >
            <Disc className="w-10 h-10" style={{ color: '#4A4A4A', opacity: 0.35 }} />
          </div>
        )
      ) : (
        <img
          src={imgSrc}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity duration-300 ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setStatus('loaded')}
          onError={handleError}
          draggable={false}
          decoding={priority ? 'sync' : 'async'}
          loading={priority ? 'eager' : 'lazy'}
          referrerPolicy="no-referrer"
          {...(priority ? { fetchPriority: 'high' } : {})}
        />
      )}
      {status === 'loading' && (
        <div className="absolute inset-0 silk-shimmer" />
      )}
      {isUnofficial && <UnofficialPill variant="overlay" />}
      {!isUnofficial && formatText && /unofficial/i.test(formatText) && <UnofficialPill variant="overlay" />}
    </div>
  );
};

export default AlbumArt;

// No-op — browser's native cache handles this now
export const prefetchArt = () => {};
