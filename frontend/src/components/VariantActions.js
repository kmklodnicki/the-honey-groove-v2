import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, Search, Plus, ArrowRightLeft, DollarSign, Loader2, Check } from 'lucide-react';
import { Button } from './ui/button';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function VariantActions({ variant }) {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [ownership, setOwnership] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

  const { artist, album, variant: variantName, discogs_id, cover_url, year, label, catalog_number } = variant;

  useEffect(() => {
    if (!discogs_id) { setLoading(false); return; }
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    axios.get(`${API}/vinyl/ownership/${discogs_id}`, { headers })
      .then(r => setOwnership(r.data))
      .catch(() => setOwnership({ owned: false, iso_status: null }))
      .finally(() => setLoading(false));
  }, [discogs_id, token]);

  if (!user) return (
    <div className="flex items-center gap-3 mt-5 p-4 rounded-2xl border border-honey/20 bg-white/60" data-testid="variant-actions-login">
      <p className="text-sm text-muted-foreground">Sign in to add this variant to your collection</p>
      <Button onClick={() => navigate('/login')} className="h-[42px] rounded-full bg-honey text-vinyl-black hover:bg-honey-amber text-sm px-6 font-semibold shadow-sm shrink-0">
        Sign In
      </Button>
    </div>
  );

  if (loading) return (
    <div className="flex justify-center p-4">
      <Loader2 className="w-5 h-5 animate-spin text-honey-amber" />
    </div>
  );

  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const addToCollection = async () => {
    setActionLoading('collection');
    try {
      await axios.post(`${API}/records`, {
        discogs_id, title: album, artist, cover_url, year,
        color_variant: variantName, format: 'Vinyl',
        notes: [label, catalog_number].filter(Boolean).join(' / '),
      }, { headers });
      toast.success(`${album} added to your collection!`);
      setOwnership(prev => ({ ...prev, owned: true }));
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to add to collection');
    } finally { setActionLoading(null); }
  };

  const addToISO = async (status) => {
    const key = status === 'WISHLIST' ? 'wishlist' : 'iso';
    setActionLoading(key);
    try {
      await axios.post(`${API}/iso`, {
        artist, album, discogs_id, cover_url, year, color_variant: variantName,
        status, priority: status === 'OPEN' ? 'HIGH' : 'LOW',
      }, { headers });
      const label_ = status === 'WISHLIST' ? 'wishlist' : 'ISO list';
      toast.success(`${album} added to your ${label_}!`);
      setOwnership(prev => ({ ...prev, iso_status: status }));
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to add');
    } finally { setActionLoading(null); }
  };

  const goToSell = () => {
    const params = new URLSearchParams({
      create: 'sale', artist, album, discogs_id: String(discogs_id),
      cover_url: cover_url || '', year: String(year || ''),
    });
    navigate(`/honeypot?${params.toString()}`);
  };

  const goToTrade = () => {
    const params = new URLSearchParams({
      create: 'trade', artist, album, discogs_id: String(discogs_id),
      cover_url: cover_url || '', year: String(year || ''),
    });
    navigate(`/honeypot?${params.toString()}`);
  };

  const owned = ownership?.owned;
  const isoStatus = ownership?.iso_status;

  const btnBase = 'h-[42px] rounded-full text-sm gap-1.5 px-[18px]';
  const btnSecondary = `${btnBase} border-honey/30 hover:bg-honey/10`;
  const btnPrimary = `${btnBase} bg-honey text-vinyl-black hover:bg-honey-amber px-6 font-semibold shadow-sm`;

  return (
    <div className="flex flex-wrap items-center gap-2.5 mt-5" data-testid="variant-actions">
      {!owned ? (
        <>
          <Button
            onClick={() => addToISO('WISHLIST')}
            disabled={!!actionLoading || isoStatus === 'WISHLIST'}
            variant="outline"
            className={btnSecondary}
            data-testid="action-wishlist"
          >
            {actionLoading === 'wishlist' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
              isoStatus === 'WISHLIST' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> :
              <Heart className="w-3.5 h-3.5" />}
            {isoStatus === 'WISHLIST' ? 'On Wishlist' : 'Add to Wishlist'}
          </Button>
          <Button
            onClick={() => addToISO('OPEN')}
            disabled={!!actionLoading || isoStatus === 'OPEN'}
            variant="outline"
            className={btnSecondary}
            data-testid="action-iso"
          >
            {actionLoading === 'iso' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
              isoStatus === 'OPEN' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> :
              <Search className="w-3.5 h-3.5" />}
            {isoStatus === 'OPEN' ? 'Actively Seeking' : 'Add to Actively Seeking'}
          </Button>
          <Button
            onClick={addToCollection}
            disabled={!!actionLoading}
            className={btnPrimary}
            data-testid="action-add-collection"
          >
            {actionLoading === 'collection' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
              <Plus className="w-3.5 h-3.5" />}
            Add to Collection
          </Button>
        </>
      ) : (
        <>
          <Button
            onClick={goToTrade}
            variant="outline"
            className={btnSecondary}
            data-testid="action-trade"
          >
            <ArrowRightLeft className="w-3.5 h-3.5" /> Trade
          </Button>
          <Button
            onClick={goToSell}
            className={btnPrimary}
            data-testid="action-sell"
          >
            <DollarSign className="w-3.5 h-3.5" /> Sell
          </Button>
        </>
      )}
    </div>
  );
}
