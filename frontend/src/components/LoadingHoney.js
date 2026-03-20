import React from 'react';

/**
 * Global branded loading state — "Fetching the Honey"
 * Use this everywhere instead of generic spinners or blank states.
 */
const LoadingHoney = ({ text = 'Fetching the honey...', size = 'md', className = '' }) => {
  const iconSize = size === 'sm' ? 'w-10 h-10' : size === 'lg' ? 'w-16 h-16' : 'w-14 h-14';
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';
  const padding = size === 'sm' ? 'py-6' : 'py-12';

  return (
    <div className={`loading-honey-container ${padding} ${className}`} data-testid="loading-honey">
      <svg className={`loading-honey-icon ${iconSize}`} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Honeypot body */}
        <ellipse cx="32" cy="42" rx="18" ry="16" fill="#DAA520" />
        <ellipse cx="32" cy="42" rx="18" ry="16" fill="url(#honey-grad)" />
        {/* Pot rim */}
        <rect x="16" y="28" width="32" height="6" rx="3" fill="#D4A828" />
        {/* Honey drip */}
        <path d="M28 28c0-4 2-8 4-10 2 2 4 6 4 10" fill="#DAA520" />
        {/* Honey label */}
        <text x="32" y="46" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#78350F">H</text>
        <defs>
          <linearGradient id="honey-grad" x1="14" y1="26" x2="50" y2="58">
            <stop stopColor="#F5C842" />
            <stop offset="1" stopColor="#D4A828" />
          </linearGradient>
        </defs>
      </svg>
      <p className={`loading-honey-text ${textSize}`}>{text}</p>
    </div>
  );
};

export default LoadingHoney;
