import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import { Loader2, Download, Lock, PartyPopper } from 'lucide-react';
import { toast } from 'sonner';

const CollectorBingo = () => {
  const { token, API } = useAuth();
  const [card, setCard] = useState(null);
  const [marks, setMarks] = useState([12]);
  const [hasBingo, setHasBingo] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  const fetchBingo = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/bingo/current`, { headers: { Authorization: `Bearer ${token}` } });
      setCard(r.data.card);
      setMarks(r.data.marks);
      setHasBingo(r.data.has_bingo);
      setIsLocked(r.data.is_locked);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchBingo(); }, [fetchBingo]);

  const toggleMark = async (index) => {
    if (isLocked || index === 12) return;
    setToggling(index);
    try {
      const r = await axios.post(`${API}/bingo/mark`, { index }, { headers: { Authorization: `Bearer ${token}` } });
      setMarks(r.data.marks);
      if (r.data.has_bingo && !hasBingo) {
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 3000);
      }
      setHasBingo(r.data.has_bingo);
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setToggling(null); }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const r = await axios.get(`${API}/bingo/export`, { headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' });
      const blob = new Blob([r.data], { type: 'image/png' });
      const file = new File([blob], `honeygroove-bingo-${Date.now()}.png`, { type: 'image/png' });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: 'the Honey Groove · Collector Bingo' });
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = file.name; a.click();
        URL.revokeObjectURL(url);
        toast.success('Downloaded!');
      }
    } catch { toast.error('Export failed'); }
    finally { setExporting(false); }
  };

  if (loading) return <Skeleton className="h-96 w-full rounded-xl" />;
  if (!card) return null;

  const markedSet = new Set(marks);
  const grid = card.grid || [];

  let dateRange = '';
  try {
    const ws = new Date(card.week_start);
    const we = new Date(card.week_end);
    dateRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} — ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { /* ignore */ }

  return (
    <div className="relative" data-testid="collector-bingo">
      {/* Celebration overlay */}
      {showCelebration && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-amber-500/10 rounded-xl animate-fade-in pointer-events-none">
          <div className="bg-white rounded-2xl shadow-xl px-8 py-6 text-center border-2 border-amber-400">
            <PartyPopper className="w-10 h-10 text-amber-500 mx-auto mb-2" />
            <p className="font-heading text-2xl text-amber-700">you got a bingo 🍯</p>
            <p className="text-sm text-muted-foreground mt-1">share it with the hive!</p>
          </div>
        </div>
      )}

      <Card className="p-4 border-amber-200/50 relative overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-heading text-lg">Collector Bingo</h3>
            <p className="text-xs text-muted-foreground">{dateRange}</p>
          </div>
          <div className="flex items-center gap-2">
            {hasBingo && <span className="px-3 py-1 rounded-full bg-amber-500 text-white text-xs font-bold" data-testid="bingo-badge">BINGO 🍯</span>}
            {isLocked && <Lock className="w-4 h-4 text-muted-foreground" />}
          </div>
        </div>

        {/* 5x5 Grid */}
        <div className="grid grid-cols-5 gap-1 mb-3" data-testid="bingo-grid">
          {grid.map((sq, i) => {
            const isMarked = markedSet.has(i);
            const isFree = sq.is_free;
            return (
              <button key={i} onClick={() => toggleMark(i)}
                disabled={isLocked || isFree || toggling !== null}
                className={`aspect-square rounded-lg p-1 flex flex-col items-center justify-center text-center transition-all relative
                  ${isMarked ? 'bg-amber-400/25 border-2 border-amber-600 shadow-inner' : 'bg-white border border-amber-200/30 hover:border-amber-300/60'}
                  ${isFree ? 'cursor-default' : isLocked ? 'cursor-default' : 'cursor-pointer active:scale-95'}
                `}
                data-testid={`bingo-sq-${i}`}
              >
                {toggling === i && <Loader2 className="w-3 h-3 animate-spin absolute top-1 right-1 text-amber-400" />}
                <span className="text-base leading-none mb-0.5">{sq.emoji}</span>
                <span className={`text-[9px] sm:text-[10px] leading-tight ${isMarked ? 'text-amber-900 font-medium' : 'text-muted-foreground'}`}>
                  {isFree ? 'sweet spot 🍯' : sq.text?.length > 40 ? sq.text.slice(0, 40) + '...' : sq.text}
                </span>
              </button>
            );
          })}
        </div>

        <Button onClick={handleExport} disabled={exporting} variant="outline"
          className="w-full rounded-full border-amber-300 text-amber-700 hover:bg-amber-50" data-testid="bingo-export-btn">
          {exporting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Download className="w-4 h-4 mr-2" />}
          save & share card
        </Button>
      </Card>
    </div>
  );
};

export default CollectorBingo;
