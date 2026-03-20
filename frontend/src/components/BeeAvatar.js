import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { resolveImageUrl } from '../utils/imageUrl';

// Bee Avatar component with first letter and bee icon
const BeeAvatar = ({ user, className = "h-10 w-10", showBorder = true }) => {
  const firstLetter = user?.username?.charAt(0).toUpperCase() || '?';
  const hasCustomAvatar = user?.avatar_url && !user.avatar_url.includes('dicebear');

  return (
    <Avatar className={`${className} ${showBorder ? 'border-2 border-honey/50' : ''}`}>
      {hasCustomAvatar && <AvatarImage src={resolveImageUrl(user.avatar_url)} alt={user?.username} />}
      <AvatarFallback className="bg-honey-soft text-vinyl-black relative">
        <span className="font-heading text-lg">{firstLetter}</span>
        <svg 
          viewBox="0 0 24 24" 
          className="absolute -bottom-0.5 -right-0.5 w-4 h-4"
          fill="none"
        >
          {/* Bee body */}
          <ellipse cx="12" cy="14" rx="5" ry="4" fill="#1E2A3A"/>
          {/* Yellow stripes */}
          <ellipse cx="12" cy="13" rx="3.5" ry="2" fill="#D4A828"/>
          <ellipse cx="12" cy="15" rx="3" ry="1.5" fill="#D4A828"/>
          {/* Head */}
          <circle cx="12" cy="9" r="2.5" fill="#1E2A3A"/>
          {/* Wings */}
          <ellipse cx="8" cy="11" rx="2" ry="3" fill="#1E2A3A" opacity="0.3"/>
          <ellipse cx="16" cy="11" rx="2" ry="3" fill="#1E2A3A" opacity="0.3"/>
        </svg>
      </AvatarFallback>
    </Avatar>
  );
};

export default BeeAvatar;
