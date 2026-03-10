import React, { useState, useEffect } from 'react';
import { Disc } from 'lucide-react';
import { resolveImageUrl } from '../utils/imageUrl';

const FALLBACK = '/vinyl-placeholder.svg';

const AlbumArt = ({ src, alt = '', className = '', style, artist, title, ...props }) => {
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

  const showGlassFallback = status === 'error' && (artist || title);

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {status === 'loading' && (
        <div className="absolute inset-0 bg-[#F0E8D8] animate-shimmer" />
      )}
      {showGlassFallback ? (
        <div
          className="w-full h-full flex flex-col items-center justify-center p-3 text-center"
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
        <img
          src={status === 'error' || !resolvedSrc ? FALLBACK : resolvedSrc}
          alt={alt}
          className="w-full h-full object-cover"
          onLoad={() => setStatus('loaded')}
          onError={() => setStatus('error')}
          draggable={false}
        />
      )}
    </div>
  );
};

export default AlbumArt;
