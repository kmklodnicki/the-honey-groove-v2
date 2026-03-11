import React, { useRef, useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function ScrollRow({ children, className = '' }) {
  const ref = useRef(null);
  const [canLeft, setCanLeft] = useState(false);
  const [canRight, setCanRight] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isMobile, setIsMobile] = useState(false);
  const touchStartRef = useRef(null);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)');
    setIsMobile(mq.matches);
    const handler = (e) => setIsMobile(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const check = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    setCanLeft(el.scrollLeft > 4);
    setCanRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
    const pageW = el.clientWidth;
    const total = Math.max(1, Math.ceil(el.scrollWidth / pageW));
    const active = Math.round(el.scrollLeft / pageW);
    setTotalPages(total);
    setActiveIdx(Math.min(active, total - 1));
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    check();
    el.addEventListener('scroll', check, { passive: true });
    const ro = new ResizeObserver(check);
    ro.observe(el);
    return () => { el.removeEventListener('scroll', check); ro.disconnect(); };
  }, [check, children]);

  const scroll = (dir) => {
    const el = ref.current;
    if (!el) return;
    const amount = el.clientWidth * 0.75;
    el.scrollBy({ left: dir * amount, behavior: 'smooth' });
  };

  const onTouchStart = (e) => {
    touchStartRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  };

  const onTouchEnd = (e) => {
    if (!touchStartRef.current) return;
    const dx = e.changedTouches[0].clientX - touchStartRef.current.x;
    const dy = e.changedTouches[0].clientY - touchStartRef.current.y;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
      scroll(dx < 0 ? 1 : -1);
    }
    touchStartRef.current = null;
  };

  const arrowBtnStyle = {
    background: 'rgba(255,255,255,0.7)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
    border: '1px solid rgba(218,165,32,0.15)',
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
  };

  return (
    <div className="relative group/scroll" data-testid="scroll-row">
      {/* Scrollable content */}
      <div
        ref={ref}
        onTouchStart={isMobile ? onTouchStart : undefined}
        onTouchEnd={isMobile ? onTouchEnd : undefined}
        className={`flex gap-3 overflow-x-auto pb-4 -mx-1 px-1 scrollbar-hide scroll-smooth ${className}`}
      >
        {children}
      </div>

      {/* Desktop: Left/Right edge Diamond Glass arrows — visible on hover */}
      {!isMobile && canLeft && (
        <button
          onClick={() => scroll(-1)}
          className="absolute top-1/2 -translate-y-1/2 -left-5 z-20 w-10 h-10 rounded-full flex items-center justify-center opacity-0 group-hover/scroll:opacity-100 transition-opacity duration-200 hover:scale-110 text-[#996012]"
          style={arrowBtnStyle}
          aria-label="Scroll left"
          data-testid="scroll-left"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      )}
      {!isMobile && canRight && (
        <button
          onClick={() => scroll(1)}
          className="absolute top-1/2 -translate-y-1/2 -right-5 z-20 w-10 h-10 rounded-full flex items-center justify-center opacity-0 group-hover/scroll:opacity-100 transition-opacity duration-200 hover:scale-110 text-[#996012]"
          style={arrowBtnStyle}
          aria-label="Scroll right"
          data-testid="scroll-right"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      )}

      {/* Mobile: Minimalist dot indicators */}
      {isMobile && totalPages > 1 && (
        <div className="flex items-center justify-center gap-1.5 mt-1" data-testid="scroll-dots">
          {Array.from({ length: totalPages }).map((_, i) => (
            <div
              key={i}
              className={`rounded-full transition-all duration-300 ${
                i === activeIdx
                  ? 'w-4 h-1.5 bg-[#C8861A]/70'
                  : 'w-1.5 h-1.5 bg-stone-300/60'
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
