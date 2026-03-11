import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from './ui/sheet';
import { Loader2, MessageCircle, CheckCircle2, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';

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
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="overflow-y-auto bg-[#FAF6EE]" data-testid="prompt-archive-drawer">
        <SheetHeader className="mb-4">
          <SheetTitle className="font-heading text-xl text-vinyl-black" data-testid="prompt-archive-title">
            Prompt Archive
          </SheetTitle>
          <SheetDescription className="text-amber-700 text-xs tracking-wide">
            See what the Hive has been buzzing about
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
          <div className="space-y-2" data-testid="prompt-archive-list">
            {prompts.map((p) => (
              <Link
                key={p.id}
                to={`/hive?prompt_id=${p.id}`}
                onClick={() => onOpenChange(false)}
                className="block rounded-xl p-3.5 transition-all duration-200 hover:bg-amber-100/60 border border-transparent hover:border-amber-200/60"
                data-testid={`prompt-archive-item-${p.id}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-vinyl-black italic leading-snug flex-1">
                    "{p.text}"
                  </p>
                  {p.user_responded && (
                    <CheckCircle2 className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                  )}
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-[10px] text-stone-400 uppercase tracking-wider">
                    {formatDate(p.scheduled_date)}
                  </span>
                  {p.response_count > 0 && (
                    <span className="flex items-center gap-1 text-[10px] text-amber-600 font-medium">
                      <MessageCircle className="w-3 h-3" />
                      {p.response_count} buzzed in
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
};

export default PromptArchiveDrawer;
