import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { resolveImageUrl } from '../utils/imageUrl';

const PhotoLightbox = ({ photos = [], initialIndex = 0, open, onClose }) => {
  const [idx, setIdx] = useState(initialIndex);
  const [animating, setAnimating] = useState(false);
  const [visible, setVisible] = useState(false);
  const touchRef = useRef({ startX: 0, startY: 0, swiping: false });
  const containerRef = useRef(null);

  useEffect(() => { if (open) { setIdx(initialIndex); requestAnimationFrame(() => setVisible(true)); } else { setVisible(false); } }, [open, initialIndex]);

  const close = useCallback(() => { setVisible(false); setTimeout(onClose, 200); }, [onClose]);

  const go = useCallback((dir) => {
    if (animating || photos.length <= 1) return;
    setAnimating(true);
    setIdx(prev => (prev + dir + photos.length) % photos.length);
    setTimeout(() => setAnimating(false), 250);
  }, [animating, photos.length]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') go(-1);
      if (e.key === 'ArrowRight') go(1);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [open, close, go]);

  const onTouchStart = (e) => {
    touchRef.current = { startX: e.touches[0].clientX, startY: e.touches[0].clientY, swiping: true };
  };

  const onTouchEnd = (e) => {
    if (!touchRef.current.swiping) return;
    const dx = e.changedTouches[0].clientX - touchRef.current.startX;
    const dy = e.changedTouches[0].clientY - touchRef.current.startY;
    touchRef.current.swiping = false;
    if (Math.abs(dy) > 80 && Math.abs(dy) > Math.abs(dx)) { close(); return; }
    if (Math.abs(dx) > 50) { go(dx < 0 ? 1 : -1); }
  };

  if (!open || !photos.length) return null;

  const resolved = photos.map(p => resolveImageUrl(p));

  const lightboxContent = (
    <div
      ref={containerRef}
      className="fixed inset-0 flex flex-col items-center justify-center transition-opacity duration-200"
      style={{ zIndex: 9999, background: 'rgba(0,0,0,0.92)', opacity: visible ? 1 : 0 }}
      onClick={(e) => { if (e.target === containerRef.current || e.target.dataset.overlay) close(); }}
      data-testid="photo-lightbox"
    >
      {/* Counter */}
      {photos.length > 1 && (
        <div className="absolute top-4 left-4 text-white/70 text-sm font-medium z-10 select-none" data-testid="lightbox-counter">
          {idx + 1} / {photos.length}
        </div>
      )}

      {/* Close */}
      <button onClick={close} className="absolute top-4 right-4 text-white/70 hover:text-white z-10 transition-colors" data-testid="lightbox-close">
        <X className="w-7 h-7" />
      </button>

      {/* Arrows (desktop) */}
      {photos.length > 1 && (
        <>
          <button onClick={(e) => { e.stopPropagation(); go(-1); }}
            className="hidden md:flex absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition z-10"
            data-testid="lightbox-prev">
            <ChevronLeft className="w-6 h-6" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); go(1); }}
            className="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition z-10"
            data-testid="lightbox-next">
            <ChevronRight className="w-6 h-6" />
          </button>
        </>
      )}

      {/* Main photo */}
      <div
        className="flex-1 flex items-center justify-center w-full px-4 md:px-16"
        data-overlay="true"
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        <img
          src={resolved[idx]}
          alt=""
          className="max-w-full max-h-[75vh] object-contain rounded-lg select-none transition-transform duration-250 ease-out"
          style={{ transform: visible ? 'scale(1)' : 'scale(0.92)' }}
          draggable={false}
          data-testid="lightbox-photo"
        />
      </div>

      {/* Thumbnail strip */}
      {photos.length > 1 && (
        <div className="flex gap-2 px-4 pb-6 pt-3 overflow-x-auto max-w-full" data-testid="lightbox-thumbnails">
          {resolved.map((url, i) => (
            <button key={i} onClick={(e) => { e.stopPropagation(); setIdx(i); }}
              className={`flex-shrink-0 w-14 h-14 rounded-lg overflow-hidden transition-all duration-200 ${i === idx ? 'ring-2 ring-[#C8861A] ring-offset-2 ring-offset-black opacity-100' : 'opacity-50 hover:opacity-80'}`}
              data-testid={`lightbox-thumb-${i}`}>
              <img src={url} alt="" className="w-full h-full object-cover" draggable={false} />
            </button>
          ))}
        </div>
      )}
    </div>
  );

  return ReactDOM.createPortal(lightboxContent, document.body);
};

export default PhotoLightbox;
