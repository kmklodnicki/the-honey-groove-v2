import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { resolveImageUrl } from '../utils/imageUrl';

/**
 * Textarea with @mention autocomplete.
 * When user types @, fetches matching usernames and shows a dropdown.
 */
const MentionTextarea = ({ value, onChange, placeholder, rows = 2, maxLength, className = '', style = {}, autoFocus = false, 'data-testid': testId }) => {
  const { token, API } = useAuth();
  const [suggestions, setSuggestions] = useState([]);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionStart, setMentionStart] = useState(-1);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const textareaRef = useRef(null);
  const searchTimer = useRef(null);

  const searchUsers = useCallback(async (query) => {
    if (!query || query.length < 1) { setSuggestions([]); return; }
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(async () => {
      try {
        const resp = await axios.get(`${API}/mention-search?q=${encodeURIComponent(query)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSuggestions(resp.data);
        setSelectedIdx(0);
      } catch { setSuggestions([]); }
    }, 200);
  }, [API, token]);

  useEffect(() => {
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, []);

  const handleChange = (e) => {
    let text = e.target.value;
    if (maxLength && text.length > maxLength) text = text.slice(0, maxLength);
    onChange(text);

    const cursorPos = e.target.selectionStart;
    // Look backwards from cursor for an @ symbol
    const before = text.slice(0, cursorPos);
    const atMatch = before.match(/@(\w*)$/);

    if (atMatch) {
      setMentionStart(atMatch.index);
      setMentionQuery(atMatch[1]);
      setShowDropdown(true);
      searchUsers(atMatch[1]);
    } else {
      setShowDropdown(false);
      setMentionQuery('');
      setSuggestions([]);
    }
  };

  const insertMention = (username) => {
    const before = value.slice(0, mentionStart);
    const after = value.slice(mentionStart + mentionQuery.length + 1); // +1 for @
    const newValue = `${before}@${username} ${after}`;
    onChange(newValue);
    setShowDropdown(false);
    setSuggestions([]);
    // Focus back on textarea
    setTimeout(() => {
      if (textareaRef.current) {
        const pos = mentionStart + username.length + 2; // @username + space
        textareaRef.current.focus();
        textareaRef.current.setSelectionRange(pos, pos);
      }
    }, 0);
  };

  const handleKeyDown = (e) => {
    if (!showDropdown || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIdx(prev => (prev + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIdx(prev => (prev - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      if (suggestions[selectedIdx]) {
        e.preventDefault();
        insertMention(suggestions[selectedIdx].username);
      }
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  };

  return (
    <div className="relative">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={rows}
        autoFocus={autoFocus}
        className={`flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none ${className}`}
        style={style}
        data-testid={testId}
      />
      {showDropdown && suggestions.length > 0 && (
        <div
          className="absolute z-50 left-0 right-0 mt-1 bg-white border border-honey/30 rounded-lg shadow-lg max-h-48 overflow-y-auto"
          data-testid="mention-dropdown"
        >
          {suggestions.map((u, idx) => (
            <button
              key={u.id}
              onMouseDown={(e) => { e.preventDefault(); insertMention(u.username); }}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-left text-sm transition-colors ${
                idx === selectedIdx ? 'bg-honey/10' : 'hover:bg-[#FFFBF2]'
              }`}
              data-testid={`mention-option-${u.username}`}
            >
              <Avatar className="h-6 w-6 border border-honey/30">
                {u.avatar_url && <AvatarImage src={resolveImageUrl(u.avatar_url)} />}
                <AvatarFallback className="bg-honey-soft text-vinyl-black text-[10px] font-heading">
                  {u.username?.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="font-medium">@{u.username}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default MentionTextarea;
