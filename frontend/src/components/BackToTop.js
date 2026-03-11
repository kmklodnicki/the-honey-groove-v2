import React, { useState, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

const BackToTop = ({ threshold = 400 }) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > threshold);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, [threshold]);

  if (!visible) return null;

  return (
    <button
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      data-testid="back-to-top-btn"
      className="fixed right-6 bottom-6 md:bottom-6 z-[100003] w-12 h-12 rounded-full flex items-center justify-center cursor-pointer transition-all duration-200 hover:scale-110 active:scale-95 shadow-lg"
      style={{
        background: 'rgba(255,255,255,0.85)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        border: '1px solid rgba(200,134,26,0.25)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1), 0 0 0 1px rgba(200,134,26,0.1)',
        bottom: 'var(--btt-bottom, 24px)',
      }}
      aria-label="Back to top"
    >
      <ArrowUp className="w-5 h-5" style={{ color: '#C8861A' }} />
      <style>{`
        @media (max-width: 767px) {
          [data-testid="back-to-top-btn"] { --btt-bottom: 80px !important; }
        }
        @media (min-width: 768px) {
          [data-testid="back-to-top-btn"] { --btt-bottom: 24px !important; }
        }
      `}</style>
    </button>
  );
};

export default BackToTop;
