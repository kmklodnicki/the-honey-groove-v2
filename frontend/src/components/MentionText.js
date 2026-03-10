import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Renders text with @mentions as clickable profile links
 * and URLs as clickable hyperlinks.
 * Set noLinks=true to suppress URL hyperlinking (e.g. sale/trade posts).
 */
const URL_REGEX = /(https?:\/\/[^\s<]+)/g;
const MENTION_REGEX = /(@\w+)/g;
const COMBINED_REGEX = /(https?:\/\/[^\s<]+|@\w+)/g;

const MentionText = ({ text, className = '', noLinks = false }) => {
  if (!text) return null;

  const parts = text.split(COMBINED_REGEX);

  return (
    <span className={className}>
      {parts.map((part, i) => {
        if (!part) return null;
        // @mention
        if (part.match(/^@(\w+)$/)) {
          const username = part.slice(1);
          return (
            <Link
              key={i}
              to={`/profile/${username}`}
              className="text-amber-700 font-medium hover:underline"
              data-testid={`mention-link-${username}`}
            >
              {part}
            </Link>
          );
        }
        // URL
        if (!noLinks && part.match(URL_REGEX)) {
          return (
            <a
              key={i}
              href={part}
              target="_blank"
              rel="noopener noreferrer"
              className="text-amber-700 hover:underline break-all"
              data-testid="auto-link"
            >
              {part.length > 50 ? part.slice(0, 47) + '...' : part}
            </a>
          );
        }
        return <React.Fragment key={i}>{part}</React.Fragment>;
      })}
    </span>
  );
};

export default MentionText;
