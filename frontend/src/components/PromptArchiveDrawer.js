import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from './ui/sheet';
import { Loader2, Disc, Clock } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { resolveImageUrl } from '../utils/imageUrl';

const MiniCard = ({ prompt }) => {
  const feat = prompt.featured;
  const formatDate = (dateStr) => {
    try {
      const d = new Date(dateStr);
      const now = new Date();
      const diff = Math.floor((now - d) / 86400000);
      if (diff <= 1) return 'Yesterday';
      if (diff <= 6) return `${diff} days ago`;
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch { return ''; }
  };

  return (
    <div
      className="rounded-xl border border-amber-200/40 bg-white/60 overflow-hidden"
      style={{ cursor: 'default' }}
      data-testid={`prompt-mini-card-${prompt.id}`}
    >
      {/* DAILY PROMPT label */}
      <div className="px-3.5 pt-3">
        <span
          className="text-[9px] font-semibold tracking-[0.2em] uppercase"
          style={{ color: '#C8861A', fontVariant: 'small-caps' }}
          data-testid="mini-card-label"
        >
          Daily Prompt
        </span>
      </div>

      {/* Prompt text */}
      <div className="px-3.5 pt-1 pb-2">
        <p className="text-[13px] font-medium text-vinyl-black italic leading-snug">
          "{prompt.text}"
        </p>
        <span className="text-[9px] text-stone-400 uppercase tracking-wider mt-1 block">
          {formatDate(prompt.scheduled_date)}
          {prompt.response_count > 0 && (
            <span className="ml-2 text-amber-600">{prompt.response_count} buzzed in</span>
          )}
        </span>
      </div>

      {/* Featured response mini-card body */}
      {feat && (
        <div className="px-3.5 pb-3.5">
          <div className="rounded-lg bg-amber-50/60 p-2.5">
            {/* User identity row */}
            <div className="flex items-center gap-1.5 mb-2">
              <Avatar className="w-4 h-4" data-testid="mini-card-avatar">
                <AvatarImage src={feat.avatar_url} alt={feat.username || ''} />
                <AvatarFallback className="text-[6px] bg-amber-200 text-amber-800">
                  {(feat.username || '?')[0]?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="text-[10px] text-stone-500 font-medium" data-testid="mini-card-username">
                @{feat.username || 'anonymous'}
              </span>
            </div>

            {/* Album art + answer */}
            <div className="flex items-start gap-2.5">
              {/* 40px album cover */}
              <div
                className="shrink-0 w-10 h-10 rounded-md overflow-hidden"
                style={{ background: '#FFB800' }}
                data-testid="mini-card-artwork"
              >
                {feat.cover_url ? (
                  <img
                    src={resolveImageUrl(feat.cover_url)}
                    alt={feat.record_title || ''}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    draggable={false}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Disc className="w-5 h-5 text-amber-900/20" />
                  </div>
                )}
              </div>

              {/* Record info */}
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-semibold text-vinyl-black truncate leading-tight">
                  {feat.record_title || 'Unknown'}
                </p>
                <p className="text-[10px] text-stone-500 truncate">
                  {feat.record_artist || 'Unknown'}
                </p>
                {feat.caption && (
                  <p className="text-[10px] text-stone-600 italic line-clamp-2 mt-0.5 leading-snug">
                    {feat.caption}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const PromptArchiveDrawer = ({ open, onOpenChange }) => {
  const { token, API } = useAuth();
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!open || !token) return;
    setLoading(true);
    axios.get(`${API}/prompts/archive`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setPrompts(r.data))
      .catch(() => setPrompts([]))
      .finally(() => setLoading(false));
  }, [open, token, API]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="overflow-y-auto bg-[#FAF6EE]" data-testid="prompt-archive-drawer">
        <SheetHeader className="mb-5">
          <SheetTitle className="font-heading text-xl text-vinyl-black" data-testid="prompt-archive-title">
            The Mini-Groove
          </SheetTitle>
          <SheetDescription className="text-amber-700 text-xs tracking-wide">
            A look back at what the Hive has been buzzing about
          </SheetDescription>
        </SheetHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12" data-testid="prompt-archive-loading">
            <Loader2 className="w-6 h-6 animate-spin text-amber-500" />
          </div>
        ) : prompts.length === 0 ? (
          <div className="text-center py-12 text-stone-400" data-testid="prompt-archive-empty">
            <Clock className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No past prompts yet.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-6" data-testid="prompt-archive-list">
            {prompts.map((p) => (
              <MiniCard key={p.id} prompt={p} />
            ))}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
};

export default PromptArchiveDrawer;
