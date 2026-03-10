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
      {/* Left Arrow */}
      {canLeft && (
        <button
          onClick={() => scroll(-1)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white/90 shadow-md border border-honey/20 flex items-center justify-center text-vinyl-black/60 hover:text-vinyl-black hover:shadow-lg transition-all opacity-0 group-hover/scroll:opacity-100 md:opacity-100"
          aria-label="Scroll left"
          data-testid="scroll-left"
        >
          <ChevronLeft className="w-4.5 h-4.5" />
        </button>
      )}

      {/* Scrollable content */}
      <div
        ref={ref}
        className={`flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide scroll-smooth ${className}`}
      >
        {children}
      </div>

      {/* Right Arrow */}
      {canRight && (
        <button
          onClick={() => scroll(1)}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white/90 shadow-md border border-honey/20 flex items-center justify-center text-vinyl-black/60 hover:text-vinyl-black hover:shadow-lg transition-all opacity-0 group-hover/scroll:opacity-100 md:opacity-100"
          aria-label="Scroll right"
          data-testid="scroll-right"
        >
          <ChevronRight className="w-4.5 h-4.5" />
        </button>
      )}
    </div>
  );
}
