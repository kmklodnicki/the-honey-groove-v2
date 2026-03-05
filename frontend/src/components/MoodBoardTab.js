import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import { Loader2, Download, Grid3X3 } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';

const TIME_PILLS = [
  { key: 'week', label: 'This Week' },
  { key: 'month', label: 'This Month' },
  { key: 'all_time', label: 'All Time' },
];

export const MoodBoardTab = ({ username }) => {
  const { token, API } = useAuth();
  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedRange, setSelectedRange] = useState('week');

  const fetchBoards = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/mood-boards/history/${username}`, { headers: { Authorization: `Bearer ${token}` } });
      setBoards(r.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token, username]);

  useEffect(() => { fetchBoards(); }, [fetchBoards]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await axios.post(`${API}/mood-boards/generate`, { time_range: selectedRange }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Mood board created!');
      fetchBoards();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to generate'); }
    finally { setGenerating(false); }
  };

  const handleExport = async (boardId) => {
    try {
      const r = await axios.get(`${API}/mood-boards/${boardId}/image`, { headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' });
      const blob = new Blob([r.data], { type: 'image/png' });
      trackEvent('export_card_generated', { card_type: 'mood_board' });
      const file = new File([blob], `honeygroove-moodboard-${Date.now()}.png`, { type: 'image/png' });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: 'the Honey Groove · Mood Board' });
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = file.name; a.click();
        URL.revokeObjectURL(url);
        toast.success('Downloaded!');
      }
    } catch { toast.error('Export failed'); }
  };

  return (
    <div className="space-y-4" data-testid="mood-board-tab">
      {/* Manual generation */}
      <Card className="p-4 border-amber-200/50">
        <p className="text-xs font-medium text-muted-foreground mb-3 uppercase tracking-wide">Generate a Mood Board</p>
        <div className="flex gap-2 mb-3">
          {TIME_PILLS.map(p => (
            <button key={p.key} onClick={() => setSelectedRange(p.key)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${selectedRange === p.key ? 'bg-amber-500 text-white shadow-sm' : 'bg-amber-100/60 text-amber-700 hover:bg-amber-200/60'}`}
              data-testid={`mood-pill-${p.key}`}>{p.label}</button>
          ))}
        </div>
        <Button onClick={handleGenerate} disabled={generating} className="bg-amber-500 hover:bg-amber-600 text-white rounded-full" data-testid="mood-generate-btn">
          {generating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Grid3X3 className="w-4 h-4 mr-2" />}
          generate mood board
        </Button>
      </Card>

      {/* History */}
      {loading ? (
        <div className="grid grid-cols-2 gap-3">{[0,1].map(i => <Skeleton key={i} className="aspect-square rounded-xl" />)}</div>
      ) : boards.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">No mood boards yet. Generate one above!</p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {boards.map((b, i) => (
            <MoodBoardCard key={b.id} board={b} isPinned={i === 0} onExport={() => handleExport(b.id)} />
          ))}
        </div>
      )}
    </div>
  );
};

const MoodBoardCard = ({ board, isPinned, onExport }) => {
  const records = board.records || [];
  const covers = records.map(r => r.cover_url).filter(Boolean);
  const dateStr = new Date(board.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  const rangeLabel = board.time_range === 'week' ? 'Weekly' : board.time_range === 'month' ? 'Monthly' : 'All Time';

  return (
    <Card className={`overflow-hidden border-amber-200/40 group cursor-pointer hover:shadow-md transition-shadow ${isPinned ? 'col-span-2' : ''}`} data-testid="mood-board-card">
      {/* 3x3 mini grid */}
      <div className={`grid grid-cols-3 ${isPinned ? 'max-w-sm mx-auto' : ''}`}>
        {[...Array(9)].map((_, i) => (
          <div key={i} className="aspect-square bg-amber-50">
            {covers[i] ? <img src={covers[i]} alt="" className="w-full h-full object-cover" loading="lazy" />
              : <div className="w-full h-full bg-amber-100/50" />}
          </div>
        ))}
      </div>
      <div className="p-3 flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">{rangeLabel} · {dateStr}</p>
          {isPinned && <p className="text-[10px] text-amber-600 font-medium">Latest</p>}
        </div>
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onExport(); }}
          className="text-amber-600 hover:text-amber-800 h-8 px-2" data-testid="mood-export-btn">
          <Download className="w-3.5 h-3.5" />
        </Button>
      </div>
    </Card>
  );
};

export default MoodBoardTab;
