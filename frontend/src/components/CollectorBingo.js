import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from './ui/dialog';
import { Loader2, Download, Lock, PartyPopper, Maximize2 } from 'lucide-react';
import { toast } from 'sonner';

const CollectorBingo = () => {
  const { token, API } = useAuth();
  const [card, setCard] = useState(null);
  const [marks, setMarks] = useState([12]);
  const [hasBingo, setHasBingo] = useState(false);
  const [bingoCount, setBingoCount] = useState(0);
  const [isLocked, setIsLocked] = useState(false);
  const [communityStats, setCommunityStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [recentlyMarked, setRecentlyMarked] = useState(null);
  const [recentlyUnmarked, setRecentlyUnmarked] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const celebrationTimer = useRef(null);

  const fetchBingo = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/bingo/current`, { headers: { Authorization: `Bearer ${token}` } });
      setCard(r.data.card);
      setMarks(r.data.marks);
      setHasBingo(r.data.has_bingo);
      setBingoCount(r.data.bingo_count || 0);
      setIsLocked(r.data.is_locked);
      if (r.data.community_stats) setCommunityStats(r.data.community_stats);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchBingo(); }, [fetchBingo]);

  const toggleMark = async (index) => {
    if (isLocked || index === 12) return;
    const wasMarked = marks.includes(index);
    setToggling(index);
    if (wasMarked) { setRecentlyUnmarked(index); setRecentlyMarked(null); }
    else { setRecentlyMarked(index); setRecentlyUnmarked(null); }

    try {
      const r = await axios.post(`${API}/bingo/mark`, { index }, { headers: { Authorization: `Bearer ${token}` } });
      setMarks(r.data.marks);
      const newBingoCount = r.data.bingo_count || 0;
      if (newBingoCount > bingoCount) {
        if (celebrationTimer.current) clearTimeout(celebrationTimer.current);
        setShowCelebration(true);
        celebrationTimer.current = setTimeout(() => setShowCelebration(false), 3000);
      }
      setHasBingo(r.data.has_bingo);
      setBingoCount(newBingoCount);
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally {
      setToggling(null);
      setTimeout(() => { setRecentlyMarked(null); setRecentlyUnmarked(null); }, 250);
    }
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

  if (loading) return <Skeleton className="h-48 w-full rounded-xl" />;
  if (!card) return null;

  const markedSet = new Set(marks);
  const grid = card.grid || [];
  const pcts = communityStats?.percentages || {};
  const markedCount = marks.length;

  let dateRange = '';
  try {
    const ws = new Date(card.week_start);
    const we = new Date(card.week_end);
    dateRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} — ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { /* ignore */ }

  return (
    <div data-testid="collector-bingo">
      {/* ─── Compact Preview Card ─── */}
      <div className="flex justify-center">
        <Card className="p-4 border-amber-200/50 w-full" style={{ maxWidth: '500px' }} data-testid="bingo-preview">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-heading text-base">Collector Bingo</h3>
              <p className="text-[10px] text-muted-foreground">{dateRange}</p>
            </div>
            <div className="flex items-center gap-2">
              {hasBingo && <span className="px-2 py-0.5 rounded-full bg-amber-500 text-white text-[10px] font-bold" data-testid="bingo-badge">BINGO 🍯</span>}
              {isLocked && <Lock className="w-3.5 h-3.5 text-muted-foreground" />}
            </div>
          </div>

          {/* Mini 5x5 grid — read-only preview */}
          <div className="grid grid-cols-5 mx-auto mb-3" style={{ gap: '4px', maxWidth: '468px' }} data-testid="bingo-grid-preview">
            {grid.map((sq, i) => {
              const isMarked = markedSet.has(i);
              const isFree = sq.is_free;
              return (
                <div
                  key={i}
                  className={`aspect-square rounded-md flex flex-col items-center justify-center text-center overflow-hidden
                    ${isFree ? 'bg-amber-400/25 border border-amber-500/40'
                      : isMarked ? 'bg-amber-400/20 border border-amber-500/30'
                      : 'bg-white border border-amber-200/25'}
                  `}
                  data-testid={`bingo-sq-preview-${i}`}
                >
                  <span className="leading-none mb-0.5" style={{ fontSize: '16px' }}>{sq.emoji}</span>
                  <span
                    className={`leading-tight px-0.5 ${isMarked ? 'text-amber-900 font-medium' : 'text-muted-foreground'}`}
                    style={{ fontSize: '8px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}
                  >
                    {isFree ? 'sweet spot 🍯' : sq.text}
                  </span>
                </div>
              );
            })}
          </div>

          <Button
            onClick={() => setModalOpen(true)}
            className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white gap-2 text-sm h-9"
            data-testid="bingo-open-btn"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            {isLocked ? 'view full card' : 'play now'}
          </Button>
        </Card>
      </div>

      {/* ─── Full-Screen Interactive Modal ─── */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto" aria-describedby="bingo-modal-desc">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl">Collector Bingo</DialogTitle>
            <p id="bingo-modal-desc" className="text-xs text-muted-foreground">{dateRange}</p>
          </DialogHeader>

          <div className="relative" data-testid="bingo-modal">
            {/* Celebration overlay */}
            {showCelebration && (
              <div className="absolute inset-0 z-20 flex items-center justify-center rounded-xl pointer-events-none" style={{ animation: 'bingoCelebFadeIn 300ms ease-out' }}>
                <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl px-8 py-6 text-center border-2 border-amber-400" style={{ animation: 'bingoCelebPop 400ms cubic-bezier(0.34,1.56,0.64,1)' }}>
                  <PartyPopper className="w-10 h-10 text-amber-500 mx-auto mb-2" />
                  <p className="font-heading text-2xl text-amber-700">you got a bingo 🍯</p>
                  <p className="text-sm text-muted-foreground mt-1">share it with the hive!</p>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                {hasBingo && <span className="px-3 py-1 rounded-full bg-amber-500 text-white text-xs font-bold" data-testid="bingo-badge-modal">BINGO 🍯</span>}
                <span className="text-xs text-muted-foreground">{markedCount}/25 marked</span>
              </div>
              {isLocked && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Lock className="w-3.5 h-3.5" />
                  <span className="text-xs">locked</span>
                </div>
              )}
            </div>

            {/* Interactive 5x5 Grid */}
            <div className="grid grid-cols-5 gap-1 mb-4" data-testid="bingo-grid">
              {grid.map((sq, i) => {
                const isMarked = markedSet.has(i);
                const isFree = sq.is_free;
                const isAnimatingIn = recentlyMarked === i;
                const isAnimatingOut = recentlyUnmarked === i;
                const pct = pcts[String(i)];

                return (
                  <button key={i} onClick={() => toggleMark(i)}
                    disabled={isLocked || isFree || toggling !== null}
                    className={`aspect-square rounded-lg p-1.5 flex flex-col items-center justify-center text-center relative overflow-hidden
                      ${isFree ? 'bg-amber-400/25 border-2 border-amber-600 cursor-default'
                        : isMarked ? 'border-2 border-amber-600 shadow-inner cursor-pointer'
                        : 'bg-white border border-amber-200/30 hover:border-amber-300/60 cursor-pointer'}
                      ${isLocked && !isFree ? 'cursor-default' : ''}
                      ${!isLocked && !isFree ? 'active:scale-[0.96]' : ''}
                    `}
                    style={{ transition: 'transform 100ms ease-out, border-color 200ms ease' }}
                    data-testid={`bingo-sq-${i}`}
                  >
                    {/* Amber fill layer */}
                    {!isFree && (
                      <span
                        className="absolute inset-0 rounded-md pointer-events-none"
                        style={{
                          background: 'radial-gradient(circle at center, rgba(232,168,32,0.25) 0%, rgba(232,168,32,0.15) 60%, rgba(232,168,32,0.08) 100%)',
                          transform: isMarked ? 'scale(1)' : 'scale(0)',
                          opacity: isMarked ? 1 : 0,
                          transition: isAnimatingIn
                            ? 'transform 200ms cubic-bezier(0.34,1.56,0.64,1), opacity 150ms ease-out'
                            : isAnimatingOut
                            ? 'transform 200ms ease-in, opacity 200ms ease-in'
                            : 'transform 200ms ease, opacity 200ms ease',
                        }}
                      />
                    )}
                    {toggling === i && <Loader2 className="w-3 h-3 animate-spin absolute top-1 right-1 text-amber-400 z-10" />}
                    <span className="text-lg leading-none mb-0.5 relative z-10">{sq.emoji}</span>
                    <span className={`text-[10px] sm:text-[11px] leading-tight relative z-10 ${isMarked ? 'text-amber-900 font-medium' : 'text-muted-foreground'}`}>
                      {isFree ? 'sweet spot 🍯' : sq.text?.length > 45 ? sq.text.slice(0, 45) + '...' : sq.text}
                    </span>
                    {/* Community stat — only shown when locked */}
                    {isLocked && pct !== undefined && !isFree && (
                      <span
                        className="text-[8px] sm:text-[9px] leading-none mt-0.5 relative z-10 italic"
                        style={{ color: '#8A6B4A', opacity: 0.6, fontFamily: '"DM Serif Display", serif' }}
                        data-testid={`bingo-stat-${i}`}
                      >
                        {pct}% of the hive
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <Button onClick={handleExport} disabled={exporting} variant="outline"
              className="w-full rounded-full border-amber-300 text-amber-700 hover:bg-amber-50" data-testid="bingo-export-btn">
              {exporting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Download className="w-4 h-4 mr-2" />}
              save & share card
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CollectorBingo;
