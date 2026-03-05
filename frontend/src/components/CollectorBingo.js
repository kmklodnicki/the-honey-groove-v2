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

/* ── Helpers ── */

function getNextFridayDrop() {
  const now = new Date();
  const day = now.getUTCDay(); // 0=Sun..6=Sat
  let daysUntil = (5 - day + 7) % 7;
  if (daysUntil === 0 && now.getUTCHours() >= 9) daysUntil = 7;
  if (daysUntil === 0 && now.getUTCHours() < 9) daysUntil = 0;
  const next = new Date(now);
  next.setUTCDate(next.getUTCDate() + daysUntil);
  next.setUTCHours(9, 0, 0, 0);
  return next;
}

function formatCountdown(target) {
  const diff = target.getTime() - Date.now();
  if (diff <= 0) return null;
  const d = Math.floor(diff / 86400000);
  const h = Math.floor((diff % 86400000) / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const parts = [];
  if (d > 0) parts.push(`${d}d`);
  parts.push(`${h}h`);
  parts.push(`${m}m`);
  return parts.join(' ');
}

function formatDropDate(target) {
  return target.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', timeZone: 'UTC' }) + ' at 9am';
}

/* ── Component ── */

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
  const [countdown, setCountdown] = useState('');
  const [activeCountdown, setActiveCountdown] = useState('');
  const [activeUrgency, setActiveUrgency] = useState('normal'); // normal | urgent | critical
  const [showLockBanner, setShowLockBanner] = useState(false);
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

  // Live countdown timer — works for both locked and active states
  useEffect(() => {
    const tick = () => {
      if (isLocked) {
        const target = getNextFridayDrop();
        const cd = formatCountdown(target);
        if (!cd) {
          setCountdown('');
          setShowLockBanner(false);
          fetchBingo();
          return true;
        }
        setCountdown(cd);
        setActiveCountdown('');
      } else if (card?.week_end) {
        // Active state: count down to card lock (Sunday midnight)
        const lockTime = new Date(card.week_end);
        const diff = lockTime.getTime() - Date.now();
        if (diff <= 0) {
          // Card just locked!
          setIsLocked(true);
          setActiveCountdown('');
          setShowLockBanner(true);
          setTimeout(() => setShowLockBanner(false), 3000);
          fetchBingo();
          return true;
        }
        const d = Math.floor(diff / 86400000);
        const h = Math.floor((diff % 86400000) / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);
        // Under 1 hour: show minutes + seconds
        if (diff < 3600000) {
          setActiveCountdown(`${m}m ${s}s`);
        } else {
          const parts = [];
          if (d > 0) parts.push(`${d}d`);
          parts.push(`${h}h`);
          parts.push(`${m}m`);
          setActiveCountdown(parts.join(' '));
        }
        setActiveUrgency(diff < 3600000 ? 'critical' : diff < 86400000 ? 'urgent' : 'normal');
        setCountdown('');
      }
      return false;
    };
    tick();
    // Under 1 hour: update every second; otherwise every 30s
    const getInterval = () => {
      if (!isLocked && card?.week_end) {
        const diff = new Date(card.week_end).getTime() - Date.now();
        if (diff < 3600000 && diff > 0) return 1000;
      }
      return 30000;
    };
    let id = setInterval(() => { if (tick()) clearInterval(id); }, getInterval());
    // Re-check interval when urgency changes
    const recheckId = setInterval(() => {
      if (!isLocked && card?.week_end) {
        const diff = new Date(card.week_end).getTime() - Date.now();
        if (diff < 3600000 && diff > 0) {
          clearInterval(id);
          id = setInterval(() => { if (tick()) clearInterval(id); }, 1000);
          clearInterval(recheckId);
        }
      }
    }, 10000);
    return () => { clearInterval(id); clearInterval(recheckId); };
  }, [isLocked, card?.week_end, fetchBingo]);

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
  const userPlayed = marks.length > 1; // more than just free space [12]
  const nextDrop = getNextFridayDrop();
  const dropDateStr = formatDropDate(nextDrop);

  let dateRange = '';
  try {
    const ws = new Date(card.week_start);
    const we = new Date(card.week_end);
    dateRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} — ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { /* ignore */ }

  /* ── Locked state: countdown + greyed card ── */
  if (isLocked) {
    return (
      <div data-testid="collector-bingo">
        <div className="flex justify-center">
          <div className="w-full" style={{ maxWidth: '500px' }}>
            {/* Card title */}
            <div className="flex items-center justify-between mb-2 px-1">
              <h3 className="font-heading text-base">Collector Bingo</h3>
              <Lock className="w-3.5 h-3.5 text-muted-foreground" />
            </div>

            {/* Previous card at 60% opacity — only if user played */}
            {userPlayed && (
              <Card
                className="p-3 border-amber-200/50 mb-3 relative cursor-pointer"
                style={{ opacity: 0.6 }}
                onClick={() => setModalOpen(true)}
                data-testid="bingo-locked-card"
              >
                <p className="text-[10px] text-muted-foreground mb-2">{dateRange}</p>
                <div className="grid grid-cols-5 mx-auto" style={{ gap: '3px', maxWidth: '468px' }} data-testid="bingo-grid-preview">
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
                        <span className="leading-none mb-0.5" style={{ fontSize: '14px' }}>{sq.emoji}</span>
                        <span
                          className={`leading-tight px-0.5 ${isMarked ? 'text-amber-900 font-medium' : 'text-muted-foreground'}`}
                          style={{ fontSize: '7px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}
                        >
                          {isFree ? 'sweet spot 🍯' : sq.text}
                        </span>
                      </div>
                    );
                  })}
                </div>
                {hasBingo && (
                  <div className="mt-2 text-center">
                    <span className="px-2 py-0.5 rounded-full bg-amber-500 text-white text-[10px] font-bold" data-testid="bingo-badge">BINGO 🍯</span>
                  </div>
                )}
              </Card>
            )}

            {/* "You missed last week" message */}
            {!userPlayed && (
              <p
                className="text-center mb-3 italic"
                style={{ color: '#8A6B4A', opacity: 0.7, fontFamily: '"DM Serif Display", serif', fontSize: '13px' }}
                data-testid="bingo-missed-msg"
              >
                you missed last week. don't miss this one.
              </p>
            )}

            {/* Countdown strip */}
            {countdown && (
              <div
                className="flex items-center px-4 w-full"
                style={{
                  background: '#FAF6EE',
                  border: '1px solid rgba(200,134,26,0.15)',
                  borderRadius: '12px',
                  height: '48px',
                }}
                data-testid="bingo-countdown"
              >
                <span className="shrink-0" style={{ fontSize: '16px' }}>🐝</span>
                <span
                  className="flex-1 text-center"
                  style={{ fontFamily: '"DM Serif Display", serif', fontSize: '13px', color: '#8A6B4A' }}
                >
                  new card drops in{' '}
                  <span style={{ fontWeight: 700, color: '#996012' }} data-testid="bingo-countdown-time">{countdown}</span>
                </span>
                <span
                  className="shrink-0 text-right"
                  style={{ fontFamily: '"DM Serif Display", serif', fontSize: '11px', color: '#8A6B4A', opacity: 0.7 }}
                >
                  {dropDateStr}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Modal for viewing locked card details */}
        <BingoModal
          open={modalOpen} onOpenChange={setModalOpen}
          grid={grid} markedSet={markedSet} isLocked={isLocked}
          hasBingo={hasBingo} markedCount={markedCount} pcts={pcts}
          dateRange={dateRange}
          toggleMark={toggleMark} toggling={toggling}
          recentlyMarked={recentlyMarked} recentlyUnmarked={recentlyUnmarked}
          showCelebration={showCelebration}
          handleExport={handleExport} exporting={exporting}
        />
      </div>
    );
  }

  /* ── Active state: compact preview + play now ── */
  const urgentBorder = activeUrgency === 'normal' ? 'rgba(200,134,26,0.15)' : '#C8861A';
  const urgentBg = activeUrgency === 'normal' ? '#FAF6EE' : 'rgba(232,168,32,0.08)';
  const urgentTimeColor = activeUrgency === 'normal' ? '#996012' : '#C8861A';

  return (
    <div data-testid="collector-bingo">
      <div className="flex justify-center">
        <div className="w-full" style={{ maxWidth: '500px' }}>
          {/* Lock banner — shows briefly when card just locked */}
          {showLockBanner && (
            <div className="flex items-center justify-center gap-2 mb-2 px-4 rounded-xl bg-amber-50 border border-amber-300/40 text-amber-700 text-sm font-medium"
              style={{ height: '44px', animation: 'bingoCelebFadeIn 300ms ease-out' }}
              data-testid="bingo-lock-banner"
            >
              <Lock className="w-4 h-4" /> your card has been saved 🍯
            </div>
          )}

          {/* Active countdown strip */}
          {activeCountdown && (
            <div
              className="flex items-center px-4 w-full mb-3"
              style={{
                background: urgentBg,
                border: `1px solid ${urgentBorder}`,
                borderRadius: '12px',
                height: '48px',
                transition: 'background 400ms ease, border-color 400ms ease',
              }}
              data-testid="bingo-active-countdown"
            >
              <span className="shrink-0" style={{ fontSize: '16px' }}>🐝</span>
              <span
                className="flex-1 text-center"
                style={{ fontFamily: '"DM Serif Display", serif', fontSize: '13px', color: '#8A6B4A' }}
              >
                card locks in{' '}
                <span style={{ fontWeight: 700, color: urgentTimeColor, transition: 'color 400ms ease' }} data-testid="bingo-active-countdown-time">{activeCountdown}</span>
              </span>
              <span
                className="shrink-0 text-right"
                style={{ fontFamily: '"DM Serif Display", serif', fontSize: '11px', color: '#8A6B4A', opacity: 0.7 }}
              >
                locks Sunday at midnight
              </span>
            </div>
          )}

          <Card className="p-4 border-amber-200/50 w-full" data-testid="bingo-preview">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-heading text-base">Collector Bingo</h3>
              <p className="text-[10px] text-muted-foreground">{dateRange}</p>
            </div>
            <div className="flex items-center gap-2">
              {hasBingo && <span className="px-2 py-0.5 rounded-full bg-amber-500 text-white text-[10px] font-bold" data-testid="bingo-badge">BINGO 🍯</span>}
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
            play now
          </Button>
        </Card>
        </div>
      </div>

      {/* Interactive modal */}
      <BingoModal
        open={modalOpen} onOpenChange={setModalOpen}
        grid={grid} markedSet={markedSet} isLocked={isLocked}
        hasBingo={hasBingo} markedCount={markedCount} pcts={pcts}
        dateRange={dateRange}
        toggleMark={toggleMark} toggling={toggling}
        recentlyMarked={recentlyMarked} recentlyUnmarked={recentlyUnmarked}
        showCelebration={showCelebration}
        handleExport={handleExport} exporting={exporting}
      />
    </div>
  );
};

/* ── Full-screen modal (shared by locked + active states) ── */
const BingoModal = ({
  open, onOpenChange, grid, markedSet, isLocked, hasBingo,
  markedCount, pcts, dateRange, toggleMark, toggling,
  recentlyMarked, recentlyUnmarked, showCelebration,
  handleExport, exporting,
}) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto" aria-describedby="bingo-modal-desc">
      <DialogHeader>
        <DialogTitle className="font-heading text-xl">Collector Bingo</DialogTitle>
        <p id="bingo-modal-desc" className="text-xs text-muted-foreground">{dateRange}</p>
      </DialogHeader>

      <div className="relative" data-testid="bingo-modal">
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

        <div className="grid grid-cols-5 gap-1 mb-4" data-testid="bingo-grid">
          {grid.map((sq, i) => {
            const isMarked = markedSet.has(i);
            const isFree = sq.is_free;
            const isAnimIn = recentlyMarked === i;
            const isAnimOut = recentlyUnmarked === i;
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
                {!isFree && (
                  <span className="absolute inset-0 rounded-md pointer-events-none"
                    style={{
                      background: 'radial-gradient(circle at center, rgba(232,168,32,0.25) 0%, rgba(232,168,32,0.15) 60%, rgba(232,168,32,0.08) 100%)',
                      transform: isMarked ? 'scale(1)' : 'scale(0)',
                      opacity: isMarked ? 1 : 0,
                      transition: isAnimIn
                        ? 'transform 200ms cubic-bezier(0.34,1.56,0.64,1), opacity 150ms ease-out'
                        : isAnimOut ? 'transform 200ms ease-in, opacity 200ms ease-in'
                        : 'transform 200ms ease, opacity 200ms ease',
                    }}
                  />
                )}
                {toggling === i && <Loader2 className="w-3 h-3 animate-spin absolute top-1 right-1 text-amber-400 z-10" />}
                <span className="text-lg leading-none mb-0.5 relative z-10">{sq.emoji}</span>
                <span className={`text-[10px] sm:text-[11px] leading-tight relative z-10 ${isMarked ? 'text-amber-900 font-medium' : 'text-muted-foreground'}`}>
                  {isFree ? 'sweet spot 🍯' : sq.text?.length > 45 ? sq.text.slice(0, 45) + '...' : sq.text}
                </span>
                {isLocked && pct !== undefined && !isFree && (
                  <span className="text-[8px] sm:text-[9px] leading-none mt-0.5 relative z-10 italic"
                    style={{ color: '#8A6B4A', opacity: 0.6, fontFamily: '"DM Serif Display", serif' }}
                    data-testid={`bingo-stat-${i}`}
                  >{pct}% of the hive</span>
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
);

export default CollectorBingo;
