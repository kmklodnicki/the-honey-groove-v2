import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Renders text with:
 *   @mentions  → clickable profile links
 *   URLs       → clickable hyperlinks
 *   *bold*     → <strong>
 *   /italics/  → <em>
 * Set noLinks=true to suppress URL hyperlinking (e.g. sale/trade posts).
 */
const URL_REGEX = /(https?:\/\/[^\s<]+)/g;
const COMBINED_REGEX = /(https?:\/\/[^\s<]+|@\w+)/g;

// Matches *bold* and /italic/ in plain text (not inside URLs — those are pre-split)
const FORMAT_REGEX = /(\*[^*]+\*|\/[^/]+\/)/g;

/**
 * Parse a plain-text fragment for *bold* and /italic/ markers.
 * Returns an array of React elements.
 */
function formatPlainText(text, keyPrefix) {
  const parts = text.split(FORMAT_REGEX);
  return parts.map((seg, j) => {
    if (!seg) return null;
    if (seg.startsWith('*') && seg.endsWith('*') && seg.length > 2) {
      return <strong key={`${keyPrefix}-b${j}`}>{seg.slice(1, -1)}</strong>;
    }
    if (seg.startsWith('/') && seg.endsWith('/') && seg.length > 2) {
      return <em key={`${keyPrefix}-i${j}`}>{seg.slice(1, -1)}</em>;
    }
    return <React.Fragment key={`${keyPrefix}-t${j}`}>{seg}</React.Fragment>;
  });
}

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
              className="text-[#D4A828] font-medium hover:underline"
              data-testid={`mention-link-${username}`}
            >
              {part}
            </Link>
          );
        }
        // URL — render as-is, no bold/italic parsing inside URLs
        if (part.match(URL_REGEX)) {
          if (noLinks) return <React.Fragment key={i}>{part}</React.Fragment>;
          return (
            <a
              key={i}
              href={part}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#D4A828] hover:underline break-all"
              data-testid="auto-link"
            >
              {part.length > 50 ? part.slice(0, 47) + '...' : part}
            </a>
          );
        }
        // Plain text — apply *bold* and /italic/ formatting
        return <React.Fragment key={i}>{formatPlainText(part, i)}</React.Fragment>;
      })}
    </span>
  );
};

export default MentionText;
