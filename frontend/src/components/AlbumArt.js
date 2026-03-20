import React, { useState, useEffect } from 'react';
import { Disc, Camera } from 'lucide-react';
import { resolveImageUrl, proxyImageUrl, isLegacyUploadUrl } from '../utils/imageUrl';
import UnofficialPill from './UnofficialPill';

// ─── Honeycomb placeholder (shown when imageSource === "placeholder") ─────────

function HoneycombPlaceholder({ albumTitle, artistName, size, onUploadClick, showUploadCta }) {
  const isLarge = size === 'large';
  return (
    <div
      className="relative w-full h-full flex flex-col items-center justify-center overflow-hidden select-none"
      style={{
        background: 'radial-gradient(circle at 60% 40%, #F6D6DE 0%, #E6C98B 60%, #D98FA1 100%)',
      }}
      data-testid="album-art-placeholder"
    >
      {/* Honeycomb SVG watermark */}
      <svg aria-hidden="true" className="absolute inset-0 w-full h-full opacity-10 pointer-events-none">
        <defs>
          <pattern id="hc-pat" width="28" height="32" patternUnits="userSpaceOnUse">
            <polygon points="14,2 26,9 26,23 14,30 2,23 2,9" fill="none" stroke="#1E2A3A" strokeWidth="1.2" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#hc-pat)" />
      </svg>

      {isLarge && (
        <div className="relative z-10 flex flex-col items-center gap-1 px-3 text-center">
          {albumTitle && (
            <p className="font-serif text-sm font-semibold leading-tight line-clamp-2 text-vinyl-black">
              {albumTitle}
            </p>
          )}
          {artistName && (
            <p className="text-xs leading-tight line-clamp-1 opacity-70 text-vinyl-black">{artistName}</p>
          )}
        </div>
      )}

      {isLarge && showUploadCta && onUploadClick && (
        <button
          onClick={onUploadClick}
          className="relative z-10 mt-2 flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium hover:opacity-80 transition-opacity"
          style={{ background: 'rgba(31,31,31,0.55)', color: '#FAF7F2' }}
          data-testid="album-art-upload-cta"
        >
          <Camera className="w-3.5 h-3.5 shrink-0" />
          Add Cover Photo
        </button>
      )}
    </div>
  );
}

// ─── Main AlbumArt component ──────────────────────────────────────────────────

const AlbumArt = ({
  // Legacy single-src API (backward compatible)
  src,
  // New resolved-image API (from backend image_resolver)
  imageUrl,
  imageSmall,
  imageSource,
  needsCoverPhoto,
  albumTitle,
  artistName,
  recordId,
  size = 'small',
  onUploadClick,
  showUploadCta = true,
  // Shared props
  alt = '',
  className = '',
  style,
  priority = false,
  isUnofficial = false,
  formatText = '',
  ...props
}) => {
  // Determine the effective src:
  //   - If new API fields are present, use imageUrl/imageSmall based on size
  //   - Otherwise fall back to legacy src
  const isNewApi = imageSource !== undefined || needsCoverPhoto !== undefined || imageUrl !== undefined;
  const effectiveSrc = isNewApi
    ? (size === 'large' ? (imageUrl || imageSmall) : (imageSmall || imageUrl))
    : src;

  const isPlaceholder = isNewApi && (needsCoverPhoto || imageSource === 'placeholder' || (!imageUrl && !imageSmall));

  const resolvedSrc = resolveImageUrl(effectiveSrc);
  const [imgSrc, setImgSrc] = useState(resolvedSrc);
  const [status, setStatus] = useState(resolvedSrc ? 'loading' : 'error');
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    if (isPlaceholder) { setStatus('error'); return; }
    const resolved = resolveImageUrl(effectiveSrc);
    if (!resolved) { setStatus('error'); return; }
    setImgSrc(resolved);
    setStatus('loading');
    setRetryCount(0);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveSrc, isPlaceholder]);

  const handleError = () => {
    if (retryCount === 0 && effectiveSrc) {
      setRetryCount(1);
      setImgSrc(proxyImageUrl(effectiveSrc));
    } else {
      setStatus('error');
    }
  };

  const displayAlt = alt || (albumTitle ? `${albumTitle}${artistName ? ` by ${artistName}` : ''}` : 'Album cover');

  return (
    <div className={`relative overflow-hidden ${className}`} style={style} {...props}>
      {status === 'error' ? (
        isPlaceholder ? (
          <HoneycombPlaceholder
            albumTitle={albumTitle}
            artistName={artistName}
            size={size}
            onUploadClick={onUploadClick}
            showUploadCta={showUploadCta}
          />
        ) : isLegacyUploadUrl(effectiveSrc) ? (
          <div className="migration-placeholder w-full h-full">
            <Disc className="w-8 h-8 text-[#D4A828] opacity-60" />
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
          alt={displayAlt}
          className={`w-full h-full object-cover transition-opacity duration-300 ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setStatus('loaded')}
          onError={handleError}
          draggable={false}
          decoding={priority ? 'sync' : 'async'}
          loading={priority ? 'eager' : 'lazy'}
          referrerPolicy="no-referrer"
          data-source={imageSource}
          {...(priority ? { fetchPriority: 'high' } : {})}
        />
      )}
      {status === 'loading' && !isPlaceholder && (
        <div className="absolute inset-0 silk-shimmer" />
      )}
      {/* "Change cover" affordance for user-uploaded art in large view */}
      {size === 'large' && imageSource === 'user_upload' && onUploadClick && status !== 'error' && (
        <button
          onClick={onUploadClick}
          className="absolute bottom-2 right-2 flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
          style={{ background: 'rgba(31,31,31,0.6)', color: '#FAF7F2' }}
          data-testid="album-art-change-cover"
        >
          <Camera className="w-3 h-3" />
          Change
        </button>
      )}
      {isUnofficial && imageSource !== 'spotify' && <UnofficialPill variant="overlay" />}
      {!isUnofficial && formatText && /unofficial/i.test(formatText) && imageSource !== 'spotify' && <UnofficialPill variant="overlay" />}
    </div>
  );
};

export default AlbumArt;

// No-op — browser's native cache handles this now
export const prefetchArt = () => {};
