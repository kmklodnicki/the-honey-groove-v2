import React, { useRef, useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function ScrollRow({ children, className = '' }) {
  const ref = useRef(null);
  const [canLeft, setCanLeft] = useState(false);
  const [canRight, setCanRight] = useState(false);

  const check = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    setCanLeft(el.scrollLeft > 4);
    setCanRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
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

  return (
    <div className="relative group/scroll" data-testid="scroll-row">
      {/* Scrollable content */}
      <div
        ref={ref}
        className={`flex gap-3 overflow-x-auto pb-10 -mx-1 px-1 scrollbar-hide scroll-smooth ${className}`}
      >
        {children}
      </div>

      {/* Floating Glass Dock — bottom-center navigation */}
      {(canLeft || canRight) && (
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/80 backdrop-blur-md shadow-md border border-honey/20" data-testid="scroll-dock">
          <button
            onClick={() => scroll(-1)}
            disabled={!canLeft}
            className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${canLeft ? 'text-vinyl-black/70 hover:text-vinyl-black hover:bg-honey/10' : 'text-vinyl-black/20 cursor-default'}`}
            aria-label="Scroll left"
            data-testid="scroll-left"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="w-px h-4 bg-honey/30" />
          <button
            onClick={() => scroll(1)}
            disabled={!canRight}
            className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${canRight ? 'text-vinyl-black/70 hover:text-vinyl-black hover:bg-honey/10' : 'text-vinyl-black/20 cursor-default'}`}
            aria-label="Scroll right"
            data-testid="scroll-right"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
