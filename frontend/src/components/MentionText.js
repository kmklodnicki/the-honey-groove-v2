import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Renders text with @mentions as clickable profile links.
 * @mentions are matched by @username pattern and rendered as Links.
 */
const MentionText = ({ text, className = '' }) => {
  if (!text) return null;

  // Split on @username patterns (word characters only)
  const parts = text.split(/(@\w+)/g);

  return (
    <span className={className}>
      {parts.map((part, i) => {
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
        return <React.Fragment key={i}>{part}</React.Fragment>;
      })}
    </span>
  );
};

export default MentionText;
