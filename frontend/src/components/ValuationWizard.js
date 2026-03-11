import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Dialog, DialogContent } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { DollarSign, Check, Loader2, SkipForward, X, PartyPopper, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import AlbumArt from './AlbumArt';

const ValuationWizard = ({ open, onClose, onComplete }) => {
  const { token, API } = useAuth();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [slideDirection, setSlideDirection] = useState('');
  const [totalInitial, setTotalInitial] = useState(0);
  const [savedCount, setSavedCount] = useState(0);
  const [finished, setFinished] = useState(false);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/valuation/unvalued-queue`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setQueue(r.data);
      setTotalInitial(r.data.length);
      setCurrentIdx(0);
      setValue('');
      setSavedCount(0);
      setFinished(r.data.length === 0);
    } catch {
      toast.error('Could not load records');
    }
    setLoading(false);
  }, [API, token]);

  useEffect(() => {
    if (open) fetchQueue();
  }, [open, fetchQueue]);

  const current = queue[currentIdx];
  const remaining = queue.length - currentIdx;

  const advanceToNext = () => {
    setSlideDirection('slide-out');
    setTimeout(() => {
      if (currentIdx + 1 >= queue.length) {
        setFinished(true);
      } else {
        setCurrentIdx(i => i + 1);
        setValue('');
      }
      setSlideDirection('slide-in');
      setTimeout(() => setSlideDirection(''), 300);
    }, 200);
  };

  const handleSave = async () => {
    const num = parseFloat(value);
    if (!num || num <= 0) {
      toast.error('Enter a valid amount');
      return;
    }
    if (!current?.discogs_id) return;
    setSaving(true);
    try {
      await axios.post(
        `${API}/valuation/wizard-save/${current.discogs_id}`,
        { value: num },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSavedCount(c => c + 1);
      advanceToNext();
    } catch {
      toast.error('Could not save value');
    }
    setSaving(false);
  };

  const handleSkip = () => {
    advanceToNext();
  };

  const handleDone = () => {
    onComplete?.(savedCount);
    onClose();
  };

  const progressPct = totalInitial > 0
    ? Math.round(((totalInitial - remaining) / totalInitial) * 100)
    : 0;

  return (
    <Dialog open={open} onOpenChange={v => { if (!v) handleDone(); }}>
      <DialogContent
        className="max-w-lg w-full p-0 gap-0 overflow-hidden"
        style={{ maxHeight: '90vh' }}
        data-testid="valuation-wizard-modal"
      >
        {/* Progress bar */}
        <div className="h-1 w-full bg-stone-100" data-testid="wizard-progress-bar">
          <div
            className="h-full transition-all duration-500 ease-out"
            style={{ width: `${progressPct}%`, background: 'linear-gradient(90deg, #C8861A, #FFD700)' }}
          />
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#C8861A' }} />
          </div>
        ) : finished ? (
          /* ===== CELEBRATION STATE ===== */
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center" data-testid="wizard-celebration">
            <div
              className="w-20 h-20 rounded-full flex items-center justify-center mb-5"
              style={{ background: 'linear-gradient(135deg, #FFD700, #C8861A)' }}
            >
              <PartyPopper className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-xl font-bold tracking-tight">Collection Fully Valued!</h2>
            <p className="text-sm text-muted-foreground mt-2 max-w-xs leading-relaxed">
              The Hive thanks you. Your benchmarks help every collector
              understand the true value of their wax.
            </p>
            {savedCount > 0 && (
              <p className="text-sm font-medium mt-4" style={{ color: '#C8861A' }}>
                You valued {savedCount} record{savedCount !== 1 ? 's' : ''} this session.
              </p>
            )}
            <Button
              onClick={handleDone}
              className="mt-6 rounded-full px-6 font-semibold border-0"
              style={{ background: '#FFD700', color: '#1A1A1A' }}
              data-testid="wizard-done-btn"
            >
              Done
            </Button>
          </div>
        ) : current ? (
          /* ===== CARD UI ===== */
          <div className={`wizard-card ${slideDirection}`}>
            {/* Header */}
            <div className="flex items-center justify-between px-5 pt-4 pb-2">
              <p className="text-xs font-medium text-muted-foreground" data-testid="wizard-counter">
                Record {totalInitial - remaining + 1} of {totalInitial} remaining
              </p>
              <button
                onClick={handleDone}
                className="text-xs text-stone-400 hover:text-stone-600 transition-colors flex items-center gap-1"
                data-testid="wizard-done-for-now"
              >
                <X className="w-3.5 h-3.5" /> Done for now
              </button>
            </div>

            {/* Album Art */}
            <div className="px-5">
              <div className="w-full aspect-square rounded-xl overflow-hidden bg-stone-200 shadow-lg" data-testid="wizard-album-art">
                {current.cover_url ? (
                  <AlbumArt
                    src={current.cover_url}
                    alt={`${current.artist} - ${current.title}`}
                    className="w-full h-full object-cover"
                    artist={current.artist}
                    title={current.title}
                  />
                ) : (
                  <AlbumArt
                    src={null}
                    alt=""
                    className="w-full h-full"
                    artist={current.artist}
                    title={current.title}
                  />
                )}
              </div>
            </div>

            {/* Record Info */}
            <div className="px-5 pt-4 pb-2">
              <h3 className="text-lg font-bold leading-tight truncate" data-testid="wizard-record-title">
                {current.title}
              </h3>
              <p className="text-sm text-muted-foreground truncate">{current.artist}</p>
              {current.year && <p className="text-xs text-stone-400 mt-0.5">{current.year}</p>}
            </div>

            {/* Hive Benchmark */}
            <div className="px-5 py-2">
              {current.hive_average > 0 ? (
                <div
                  className="flex items-center gap-2 px-3 py-2 rounded-lg"
                  style={{ background: 'rgba(255,215,0,0.08)', border: '1px solid rgba(200,134,26,0.2)' }}
                  data-testid="wizard-hive-benchmark"
                >
                  <span className="text-xs font-semibold" style={{ color: '#7A5A1A' }}>
                    Hive Benchmark: ${current.hive_average.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-stone-400">
                    ({current.hive_count} {current.hive_count === 1 ? 'submission' : 'submissions'})
                  </span>
                </div>
              ) : (
                <p className="text-xs text-stone-400 italic">No community data yet — be the first to set the benchmark.</p>
              )}
            </div>

            {/* Value Input */}
            <div className="px-5 pb-3">
              <label className="text-xs font-medium text-stone-500 block mb-1.5">Your Estimate</label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-stone-400" />
                <Input
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  value={value}
                  onChange={e => setValue(e.target.value)}
                  className="h-12 pl-9 text-lg font-semibold"
                  data-testid="wizard-value-input"
                  autoFocus
                  onKeyDown={e => { if (e.key === 'Enter' && value) handleSave(); }}
                />
              </div>
              {current.hive_average > 0 && (
                <button
                  onClick={() => setValue(current.hive_average.toFixed(2))}
                  className="text-[11px] mt-1.5 font-medium hover:underline transition-colors"
                  style={{ color: '#C8861A' }}
                  data-testid="wizard-accept-hive"
                >
                  Use Hive Benchmark (${current.hive_average.toFixed(2)})
                </button>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 px-5 pb-5">
              <Button
                variant="outline"
                onClick={handleSkip}
                className="flex-1 h-11 rounded-full font-semibold text-sm"
                data-testid="wizard-skip-btn"
              >
                <SkipForward className="w-4 h-4 mr-1.5" /> Skip
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving || !value}
                className="flex-1 h-11 rounded-full font-semibold text-sm border-0"
                style={{ background: '#FFD700', color: '#1A1A1A' }}
                data-testid="wizard-save-next-btn"
              >
                {saving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>Save & Next <ChevronRight className="w-4 h-4 ml-1" /></>
                )}
              </Button>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
};

export default ValuationWizard;
