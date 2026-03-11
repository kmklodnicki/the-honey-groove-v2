import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ChevronDown, ChevronUp, ChevronRight, Loader2 } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import DuplicateConfirmationModal from './DuplicateConfirmationModal';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const ProgressBar = ({ pct }) => (
  <div className="w-full h-3 bg-stone-200/60 rounded-full overflow-hidden" data-testid="completion-progress-bar">
    <div
      className="h-full rounded-full transition-all duration-700 ease-out"
      style={{
        width: `${pct}%`,
        background: pct === 100
          ? 'linear-gradient(90deg, #10b981, #059669)'
          : 'linear-gradient(90deg, #FFD700, #E8A820)',
      }}
    />
  </div>
);

const VariantRow = ({ variant, onAdd, adding }) => {
  const navigate = useNavigate();
  const releaseId = variant.release_ids?.[0];
  const handleNavigate = (e) => {
    // Don't navigate if clicking the add checkbox
    if (e.target.closest('[data-variant-add]')) return;
    if (releaseId) navigate(`/variant/${releaseId}`);
  };

  return (
    <div
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 cursor-pointer ${
        variant.owned
          ? 'bg-emerald-50/80 hover:bg-emerald-50'
          : 'bg-stone-50/60 hover:bg-amber-50/60'
      }`}
      style={{ '--hover-border': 'rgba(218,165,32,0.2)' }}
      onClick={handleNavigate}
      role="link"
      data-testid={`variant-row-${variant.name.toLowerCase().replace(/\s+/g, '-')}`}
    >
      {variant.owned ? (
        <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
          <Check className="w-3 h-3 text-white" strokeWidth={3} />
        </div>
      ) : (
        <button
          data-variant-add="true"
          onClick={(e) => { e.stopPropagation(); onAdd(variant); }}
          disabled={adding}
          className="w-5 h-5 rounded border-2 border-stone-300 shrink-0 hover:border-honey hover:bg-honey/10 transition-colors cursor-pointer"
          data-testid={`variant-add-btn-${variant.name.toLowerCase().replace(/\s+/g, '-')}`}
          aria-label={`Add ${variant.name} to collection`}
        />
      )}
      <span className={`text-sm flex-1 ${variant.owned ? 'font-medium text-emerald-800' : 'text-stone-500'}`}>
        {variant.name}
      </span>
      {variant.release_ids?.length > 1 && (
        <span className="text-[10px] text-muted-foreground">
          {variant.release_ids.length} pressings
        </span>
      )}
      {releaseId && (
        <ChevronRight className="w-3.5 h-3.5 text-stone-300 shrink-0" />
      )}
    </div>
  );
};

const TrackerSkeleton = () => (
  <Card className="p-5 border-honey/20 animate-pulse" data-testid="variant-tracker-skeleton">
    <div className="flex items-center justify-between mb-3">
      <div className="h-5 w-32 bg-stone-200 rounded" />
      <div className="h-4 w-20 bg-stone-200 rounded" />
    </div>
    <div className="w-full h-3 bg-stone-200 rounded-full mb-1.5" />
    <div className="h-3 w-16 bg-stone-100 rounded ml-auto mb-4" />
    <div className="space-y-2">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="flex items-center gap-3 px-3 py-2.5">
          <div className="w-5 h-5 rounded-full bg-stone-200 shrink-0" />
          <div className="h-4 bg-stone-200 rounded" style={{ width: `${50 + i * 12}%` }} />
        </div>
      ))}
    </div>
  </Card>
);

export default function VariantCompletion({ discogsId }) {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [confirmVariant, setConfirmVariant] = useState(null);
  const [adding, setAdding] = useState(false);
  const [dupModal, setDupModal] = useState({ open: false, copyCount: 0, title: '' });
  const pendingAddRef = useRef(null);

  useEffect(() => {
    if (!discogsId) return;
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    axios.get(`${API}/vinyl/completion/${discogsId}`, { headers })
      .then(res => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [discogsId, token]);

  const executeVariantAdd = useCallback(async (recordData, variant) => {
    await axios.post(`${API}/records`, recordData, { headers: { Authorization: `Bearer ${token}` } });

    // Update local state
    setData(prev => {
      if (!prev) return prev;
      const updatedVariants = prev.variants.map(v =>
        v.name === variant.name ? { ...v, owned: true } : v
      );
      updatedVariants.sort((a, b) => (a.owned === b.owned ? a.name.localeCompare(b.name) : a.owned ? -1 : 1));
      const newOwned = updatedVariants.filter(v => v.owned).length;
      const total = updatedVariants.length;
      const newPct = total ? Math.round((newOwned / total) * 100) : 0;
      return { ...prev, variants: updatedVariants, owned_count: newOwned, completion_pct: newPct };
    });

    toast.success(`${variant.name} added to your collection!`);

    const updatedOwned = data.owned_count + 1;
    if (updatedOwned === data.total_variants) {
      try {
        const confetti = (await import('canvas-confetti')).default;
        confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 } });
      } catch {}
      toast.success('You completed the full variant set!', { duration: 5000 });
    }
  }, [data, token]);

  const handleDupConfirm = useCallback(async () => {
    setDupModal({ open: false, copyCount: 0, title: '' });
    if (!pendingAddRef.current) return;
    setAdding(true);
    try {
      const { recordData, variant } = pendingAddRef.current;
      await executeVariantAdd({ ...recordData, instance_id: Date.now() }, variant);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not add to collection.');
    } finally {
      setAdding(false);
      setConfirmVariant(null);
      pendingAddRef.current = null;
    }
  }, [executeVariantAdd]);

  const handleDupCancel = useCallback(() => {
    setDupModal({ open: false, copyCount: 0, title: '' });
    pendingAddRef.current = null;
    setAdding(false);
    setConfirmVariant(null);
  }, []);

  const handleAddToCollection = useCallback(async () => {
    if (!confirmVariant || !data || !token) return;
    setAdding(true);

    const releaseId = confirmVariant.release_ids?.[0];
    if (!releaseId) {
      toast.error('No release ID found for this variant.');
      setAdding(false);
      setConfirmVariant(null);
      return;
    }

    try {
      let title = data.album || '';
      let artist = data.artist || '';
      let coverUrl = '';
      let year = null;

      try {
        const releaseRes = await axios.get(`${API}/discogs/release/${releaseId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const rel = releaseRes.data;
        title = rel.title || title;
        artist = rel.artist || artist;
        coverUrl = rel.cover_url || '';
        year = rel.year || null;
      } catch {}

      const recordData = {
        discogs_id: releaseId, title, artist, cover_url: coverUrl,
        year, format: 'Vinyl', color_variant: confirmVariant.name,
      };

      // Check for duplicates
      const ownerCheck = await axios.get(`${API}/records/check-ownership`, {
        params: { discogs_id: releaseId },
        headers: { Authorization: `Bearer ${token}` },
      });

      if (ownerCheck.data.in_collection) {
        pendingAddRef.current = { recordData, variant: confirmVariant };
        setDupModal({ open: true, copyCount: ownerCheck.data.copy_count || 1, title });
        return;
      }

      await executeVariantAdd(recordData, confirmVariant);
    } catch (err) {
      if (err.response?.status === 409) {
        toast.info('Already in your collection.');
        setData(prev => {
          if (!prev) return prev;
          const updatedVariants = prev.variants.map(v =>
            v.name === confirmVariant.name ? { ...v, owned: true } : v
          );
          updatedVariants.sort((a, b) => (a.owned === b.owned ? a.name.localeCompare(b.name) : a.owned ? -1 : 1));
          const newOwned = updatedVariants.filter(v => v.owned).length;
          const total = updatedVariants.length;
          return { ...prev, variants: updatedVariants, owned_count: newOwned, completion_pct: total ? Math.round((newOwned / total) * 100) : 0 };
        });
      } else {
        toast.error('Could not add to collection. Try again.');
      }
    } finally {
      setAdding(false);
      setConfirmVariant(null);
    }
  }, [confirmVariant, data, token, executeVariantAdd]);

  if (loading) return <TrackerSkeleton />;
  if (!data || data.error || data.total_variants <= 1) return null;

  const { total_variants, owned_count, completion_pct, variants } = data;
  const owned = variants.filter(v => v.owned);
  const missing = variants.filter(v => !v.owned);
  const previewCount = 6;
  const needsExpand = variants.length > previewCount;

  return (
    <>
      <Card className="p-5 border-honey/20" data-testid="variant-completion-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-heading text-lg font-bold text-vinyl-black">Variant Tracker</h3>
          <span className="text-sm font-medium text-honey-amber" data-testid="completion-count">
            {owned_count} / {total_variants} variants
          </span>
        </div>

        <ProgressBar pct={completion_pct} />

        <p className="text-right text-xs text-muted-foreground mt-1.5 mb-4" data-testid="completion-pct">
          {completion_pct}% complete
        </p>

        {/* Owned Section */}
        {owned.length > 0 && (
          <div className="mb-3">
            <p className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider mb-1.5">Owned</p>
            <div className="space-y-1">
              {owned.map(v => <VariantRow key={v.name} variant={v} onAdd={setConfirmVariant} adding={adding} />)}
            </div>
          </div>
        )}

        {/* Missing Section */}
        {missing.length > 0 && (
          <div>
            <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1.5">
              Missing {!token && <span className="text-[10px] font-normal">(sign in to add)</span>}
            </p>
            <div className="space-y-1">
              {(expanded ? missing : missing.slice(0, Math.max(0, previewCount - owned.length))).map(v => (
                <VariantRow key={v.name} variant={v} onAdd={token ? setConfirmVariant : () => {}} adding={adding} />
              ))}
            </div>
          </div>
        )}

        {/* Expand/Collapse */}
        {needsExpand && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full mt-3 flex items-center justify-center gap-1 text-xs text-honey-amber hover:text-amber-600 transition-colors py-1.5"
            data-testid="completion-toggle"
          >
            {expanded ? (
              <>Show Less <ChevronUp className="w-3.5 h-3.5" /></>
            ) : (
              <>Show All {total_variants} Variants <ChevronDown className="w-3.5 h-3.5" /></>
            )}
          </button>
        )}
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={!!confirmVariant} onOpenChange={(open) => { if (!open) setConfirmVariant(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Add to Collection?</AlertDialogTitle>
            <AlertDialogDescription>
              Add <strong>{confirmVariant?.name}</strong> to your collection?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={adding} data-testid="variant-add-cancel">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleAddToCollection}
              disabled={adding}
              className="bg-honey text-vinyl-black hover:bg-honey-amber"
              data-testid="variant-add-confirm"
            >
              {adding ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
              Add to Collection
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <DuplicateConfirmationModal
        open={dupModal.open}
        copyCount={dupModal.copyCount}
        recordTitle={dupModal.title}
        onConfirm={handleDupConfirm}
        onCancel={handleDupCancel}
      />
    </>
  );
}
