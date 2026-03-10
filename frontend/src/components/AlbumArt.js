import React, { useState, useEffect } from 'react';
import { resolveImageUrl } from '../utils/imageUrl';

const FALLBACK = '/vinyl-placeholder.svg';

const AlbumArt = ({ src, alt = '', className = '', style, ...props }) => {
  const resolvedSrc = resolveImageUrl(src);
  const [status, setStatus] = useState(resolvedSrc ? 'loading' : 'error');

  // Reset status when src changes
  useEffect(() => {
    setStatus(resolveImageUrl(src) ? 'loading' : 'error');
  }, [src]);

  // Timeout: if still loading after 8s, show fallback
  useEffect(() => {
    if (status !== 'loading') return;
    const t = setTimeout(() => setStatus(s => s === 'loading' ? 'error' : s), 8000);
    return () => clearTimeout(t);
  }, [status]);

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {status === 'loading' && (
        <div className="absolute inset-0 bg-[#F0E8D8] animate-shimmer" />
      )}
      <img
        src={status === 'error' || !resolvedSrc ? FALLBACK : resolvedSrc}
        alt={alt}
        className="w-full h-full object-cover"
        onLoad={() => setStatus('loaded')}
        onError={() => setStatus('error')}
        draggable={false}
      />
    </div>
  );
};

export default AlbumArt;
