import React, { useState } from 'react';

const FALLBACK = '/vinyl-placeholder.svg';

const AlbumArt = ({ src, alt = '', className = '', style, ...props }) => {
  const [status, setStatus] = useState(src ? 'loading' : 'error');

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {status === 'loading' && (
        <div className="absolute inset-0 bg-[#F0E8D8] animate-shimmer" />
      )}
      <img
        src={status === 'error' || !src ? FALLBACK : src}
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
