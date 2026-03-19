import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Disc, Users, TrendingUp, DollarSign, BarChart3,
  Calendar, ArrowLeft, Loader2, Heart, RefreshCw, Store,
  Plus, Search, Trash2, X, Send
} from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import AlbumArt from '../components/AlbumArt';
import UnofficialPill from '../components/UnofficialPill';
import UnofficialDisclaimer from '../components/UnofficialDisclaimer';
import SEOHead from '../components/SEOHead';
import { RarityCard } from '../components/RarityBadge';
import MentionTextarea from '../components/MentionTextarea';
import { useAuth } from '../context/AuthContext';
import { resolveImageUrl } from '../utils/imageUrl';
import axios from 'axios';
import { toast } from 'sonner';

import { API_BASE } from '../utils/apiBase';
const BACKEND_URL = API_BASE;
const API = `${BACKEND_URL}/api`;

const Stat = ({ icon: Icon, label, value, sub }) => (
  <Card className="p-4 border-honey/20 bg-honey/5" data-testid={`stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center gap-2 mb-1">
      <Icon className="w-4 h-4 text-honey-amber" />
      <span className="text-xs text-muted-foreground uppercase tracking-wider">{label}</span>
    </div>
    <p className="text-2xl font-heading font-bold text-vinyl-black">{value ?? '—'}</p>
    {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
  </Card>
);

export default function VariantReleasePage() {
  const { releaseId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resyncing, setResyncing] = useState(false);
  const [spotifyLink, setSpotifyLink] = useState(null);
  const [ownership, setOwnership] = useState({ in_collection: false, record_id: null });
  const [actionModal, setActionModal] = useState(null); // 'add' | 'dream' | 'seeking' | null
  const [postToHive, setPostToHive] = useState(true);
  const [caption, setCaption] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [removing, setRemoving] = useState(false);
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    setData(null);
    setLoading(true);
    setSpotifyLink(null);
    setOwnership({ in_collection: false, record_id: null });
    const hdrs = token ? { Authorization: `Bearer ${token}` } : {};
    axios.get(`${API}/vinyl/release/${releaseId}`, { headers: hdrs })
      .then(r => {
        setData(r.data);
        if (token) {
          axios.get(`${API}/spotify/link/${releaseId}`, { headers: { Authorization: `Bearer ${token}` } })
            .then(sr => setSpotifyLink(sr.data))
            .catch(() => {});
          axios.get(`${API}/records/check-ownership?discogs_id=${releaseId}`, { headers: { Authorization: `Bearer ${token}` } })
            .then(or => setOwnership(or.data))
            .catch(() => {});
        }
      })
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [releaseId, token]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 pt-3 md:pt-2 pb-28 flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-honey-amber" />
      </div>
    );
  }

  if (!data || data.error) {
    return (
      <div className="max-w-4xl mx-auto px-4 pt-3 md:pt-2 pb-28 text-center">
        <Disc className="w-12 h-12 text-honey/40 mx-auto mb-4" />
        <h1 className="text-xl font-heading mb-2" data-testid="variant-not-found">Variant Not Found</h1>
        <p className="text-muted-foreground text-sm mb-6">
          {data?.error || "We couldn't load data for this pressing. It may be a temporary issue with Discogs."}
        </p>
        <div className="flex gap-3 justify-center">
          <button onClick={() => {
            setLoading(true);
            setData(null);
            const headers = token ? { Authorization: `Bearer ${token}` } : {};
            axios.get(`${API}/vinyl/release/${releaseId}`, { headers })
              .then(r => setData(r.data))
              .catch(() => setData(null))
              .finally(() => setLoading(false));
          }} className="text-sm text-white bg-honey-amber hover:bg-honey-amber/80 px-4 py-2 rounded-full transition-colors" data-testid="variant-retry-btn">
            <RefreshCw className="w-3.5 h-3.5 inline mr-1.5" />Try Again
          </button>
          <button onClick={() => navigate(-1)} className="text-sm text-honey-amber hover:underline px-4 py-2" data-testid="variant-go-back">Go Back</button>
        </div>
      </div>
    );
  }

  const { variant_overview: ov, scarcity, value: val, community, honeypot } = data;

  const handleResync = () => {
    setResyncing(true);
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    axios.get(`${API}/vinyl/release/${releaseId}?force_refresh=true`, { headers })
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setResyncing(false));
  };

  const openAction = (type) => {
    setActionModal(type);
    setPostToHive(true);
    setCaption('');
  };

  const handleAddToCollection = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API}/records`, {
        discogs_id: parseInt(releaseId),
        title: ov.album, artist: ov.artist,
        cover_url: ov.imageUrl || ov.imageSmall || '', year: ov.year,
        pressing_notes: ov.variant || '',
      }, { headers: { Authorization: `Bearer ${token}` } });
      setOwnership({ in_collection: true, record_id: null });
      toast.success('added to your vault.');
      setActionModal(null);
    } catch (err) { toast.error(err.response?.data?.detail || 'failed to add'); }
    finally { setActionLoading(false); }
  };

  const handleDreamOrSeeking = async () => {
    const intent = actionModal; // 'dream' or 'seeking'
    if (postToHive && !caption.trim()) { toast.error('a caption is required to share with the hive.'); return; }
    setActionLoading(true);
    try {
      await axios.post(`${API}/composer/iso`, {
        artist: ov.artist, album: ov.album,
        discogs_id: parseInt(releaseId),
        cover_url: ov.imageUrl || ov.imageSmall || null,
        year: ov.year || null,
        pressing_notes: ov.variant || null,
        caption: caption || null,
        intent: intent === 'dream' ? 'dreaming' : 'seeking',
        post_to_hive: postToHive,
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success(postToHive
        ? (intent === 'dream' ? 'dream added & shared.' : 'iso posted to the hive.')
        : (intent === 'dream' ? 'added to dream list.' : 'iso saved.'));
      setActionModal(null);
    } catch (err) { toast.error(err.response?.data?.detail || 'failed'); }
    finally { setActionLoading(false); }
  };

  const handleRemove = async () => {
    if (!ownership.record_id) { toast.error('record not found in your vault.'); return; }
    setRemoving(true);
    try {
      await axios.delete(`${API}/records/${ownership.record_id}`, { headers: { Authorization: `Bearer ${token}` } });
      setOwnership({ in_collection: false, record_id: null });
      toast.success('removed from your vault.');
    } catch (err) { toast.error(err.response?.data?.detail || 'failed to remove'); }
    finally { setRemoving(false); }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-28" data-testid="variant-release-page">
      <SEOHead
        title={`${ov.artist} — ${ov.album} (${ov.variant || 'Standard'})`}
        description={`${ov.variant || 'Standard'} pressing of ${ov.album} by ${ov.artist}. ${scarcity.discogs_have} global owners.`}
        url={`/variant/${releaseId}`}
        image={ov.imageUrl || ov.imageSmall}
      />

      {/* Back */}
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-sm text-stone-500 hover:text-vinyl-black mb-8 transition-colors group"
        data-testid="back-btn"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" /> Back
      </button>

      {/* Hero */}
      <section className="flex flex-col md:flex-row gap-8 mb-10" data-testid="variant-hero">
        <div className="w-full md:w-72 shrink-0">
          <div className="relative aspect-square overflow-hidden bg-stone-200 rounded-2xl shadow-lg shadow-black/5">
            <AlbumArt
              imageUrl={ov.imageUrl}
              imageSmall={ov.imageSmall}
              imageSource={ov.imageSource}
              needsCoverPhoto={ov.needsCoverPhoto}
              albumTitle={ov.album}
              artistName={ov.artist}
              size="large"
              alt={`${ov.artist} ${ov.album} ${ov.variant} vinyl`}
              className="w-full h-full object-cover"
              isUnofficial={ov.is_unofficial}
              formatText={ov.format || ''}
            />
            {/* Variant pill */}
            <div
              className="absolute bottom-3 left-3 right-3 truncate uppercase text-[11px] font-bold px-3 py-1 rounded-full text-center"
              style={{
                background: 'rgba(255,215,0,0.2)',
                backdropFilter: 'blur(14px)',
                WebkitBackdropFilter: 'blur(14px)',
                color: '#000',
                letterSpacing: '0.5px',
                border: '2px solid #DAA520',
                boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)',
              }}
              data-testid="variant-pill"
            >
              {ov.variant || 'Standard'}
            </div>
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm text-honey-amber font-medium uppercase tracking-wider mb-1">{ov.variant || 'Standard Pressing'}{ov.variant && !ov.variant.toLowerCase().includes('pressing') ? ' Pressing' : ''}</p>
          <div className="flex items-center gap-3 flex-wrap mb-1">
            <h1 className="text-3xl sm:text-4xl font-heading font-bold leading-tight" data-testid="variant-title">{ov.album}</h1>
            {ov.is_unofficial && <UnofficialPill variant="inline" className="!text-[11px] !px-2.5 !py-1" />}
          </div>
          <p className="text-lg text-muted-foreground mb-4" data-testid="variant-artist">{ov.artist}</p>

          {/* Meta tags */}
          <div className="flex flex-wrap gap-2 mb-6">
            {ov.year && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                <Calendar className="w-3 h-3" /> {ov.year}
              </span>
            )}
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
              <Disc className="w-3 h-3" /> {ov.format || 'Vinyl'}
            </span>
            {ov.label && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                {ov.label}
              </span>
            )}
            {ov.catalog_number && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                Cat# {ov.catalog_number}
              </span>
            )}
            {spotifyLink && spotifyLink.spotify_url && (
              <a
                href={spotifyLink.spotify_url}
                target="_blank"
                rel="noopener noreferrer"
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  spotifyLink.matched
                    ? 'bg-[#1DB954]/15 text-[#1DB954] hover:bg-[#1DB954]/25 border border-[#1DB954]/30'
                    : 'bg-stone-100 text-stone-500 hover:bg-stone-200 border border-stone-200'
                }`}
                data-testid="spotify-link"
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
                {spotifyLink.matched ? 'Listen on Spotify' : 'Search Spotify'}
              </a>
            )}
          </div>

          {/* Discogs attribution — required per Discogs API TOS */}
          {releaseId && (
            <p className="text-[10px] text-muted-foreground/60 mt-1 mb-4">
              <a
                href={`https://www.discogs.com/release/${releaseId}`}
                target="_blank"
                rel="noopener"
                className="hover:text-muted-foreground transition-colors"
              >
                Data provided by Discogs
              </a>
            </p>
          )}

          {/* Action buttons */}
          {token && (
            <div className="flex flex-wrap gap-2 mb-6" data-testid="variant-actions">
              {ownership.in_collection ? (
                <Button variant="outline" size="sm" onClick={handleRemove} disabled={removing}
                  className="rounded-full border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 h-8 px-3 text-xs"
                  data-testid="variant-remove-btn">
                  {removing ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Trash2 className="w-3 h-3 mr-1" />}
                  Remove from Vault
                </Button>
              ) : (
                <Button size="sm" onClick={() => openAction('add')}
                  className="rounded-full bg-honey text-vinyl-black hover:bg-honey-amber h-8 px-3 text-xs"
                  data-testid="variant-add-btn">
                  <Plus className="w-3 h-3 mr-1" /> Add to Vault
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={() => openAction('dream')}
                className="rounded-full border-stone-300 hover:bg-stone-50 h-8 px-3 text-xs"
                data-testid="variant-dream-btn">
                <Heart className="w-3 h-3 mr-1" /> Dream List
              </Button>
              <Button variant="outline" size="sm" onClick={() => openAction('seeking')}
                className="rounded-full border-amber-300 text-amber-700 hover:bg-amber-50 h-8 px-3 text-xs"
                data-testid="variant-seeking-btn">
                <Search className="w-3 h-3 mr-1" /> Seeking (ISO)
              </Button>
            </div>
          )}

          {/* Variant-specific quick stats */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">
              {scarcity.stats_source === 'master' ? 'Stats from master release' : 'Variant-specific stats'}
            </span>
            <button
              onClick={handleResync}
              disabled={resyncing}
              className="inline-flex items-center gap-1 text-[11px] text-honey-amber hover:underline transition-colors disabled:opacity-50"
              data-testid="resync-btn"
            >
              <RefreshCw className={`w-3 h-3 ${resyncing ? 'animate-spin' : ''}`} />
              Re-sync
            </button>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Stat icon={Users} label="Owners" value={scarcity.discogs_have != null ? scarcity.discogs_have.toLocaleString() : '—'} sub={scarcity.stats_source === 'master' ? 'via master release' : 'global (this pressing)'} />
            <Stat icon={Heart} label="Wantlist" value={scarcity.discogs_want != null ? scarcity.discogs_want.toLocaleString() : '—'} sub={scarcity.stats_source === 'master' ? 'via master release' : 'global (this pressing)'} />
            {/* The Honeypot Price: internal listing price */}
            <div
              className="flex flex-col items-center text-center p-2 rounded-xl cursor-pointer hover:shadow-md transition-all"
              style={{ background: 'rgba(255,215,0,0.06)', border: '1px solid rgba(218,165,32,0.2)' }}
              onClick={() => honeypot?.active_listings > 0 ? navigate(`/honeypot?q=${encodeURIComponent(ov.artist + ' ' + ov.album)}`) : navigate('/honeypot')}
              data-testid="honey-market-stat"
            >
              <Store className="w-4 h-4 mb-0.5" style={{ color: '#DAA520' }} />
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">The Honeypot Price</span>
              {honeypot?.honey_lowest ? (
                <>
                  <span className="text-xl font-heading font-bold" style={{ color: '#1A1A1A' }}>${honeypot.honey_lowest.toFixed(2)}</span>
                  <span className="text-[10px] text-muted-foreground">in the Hive</span>
                </>
              ) : (
                <>
                  <span className="text-sm font-semibold text-muted-foreground mt-0.5">Not listed</span>
                  <span className="text-[10px] font-medium" style={{ color: '#DAA520' }}>List yours</span>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Unofficial Release Disclaimer */}
      {ov.is_unofficial && (
        <section className="mb-10" data-testid="unofficial-section">
          <UnofficialDisclaimer />
        </section>
      )}

      {/* Global Variant Scarcity */}
      {scarcity?.tier && (
        <section className="mb-10" data-testid="scarcity-section">
          <RarityCard
            rarity={scarcity}
            label="Global Variant Scarcity"
            honeypotListings={honeypot?.active_listings ?? 0}
            onForSaleClick={() => navigate(`/honeypot?q=${encodeURIComponent(ov.artist + ' ' + ov.album)}`)}
            albumName={ov.album}
            variantName={ov.variant}
            onNotifySubscribe={() => {
              if (token) {
                axios.post(`${API}/listing-alerts`, {
                  discogs_id: parseInt(releaseId),
                  album_name: ov.album || '',
                  variant_name: ov.variant || null,
                  artist: ov.artist || '',
                  cover_url: ov.imageUrl || ov.imageSmall || '',
                }, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
              }
            }}
          />
        </section>
      )}

      {/* Market Value */}
      {(val.discogs_median || val.discogs_high || honeypot?.honey_lowest) && (
        <section className="mb-10" data-testid="value-section">
          <h2 className="text-xl font-heading font-bold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-honey-amber" /> Market Value
          </h2>
          <div className="grid grid-cols-3 gap-3">
            {/* The Honeypot Price replaces Discogs Low */}
            <div
              className="rounded-xl p-4 border cursor-pointer hover:shadow-md transition-all"
              style={{ borderColor: 'rgba(218,165,32,0.3)', background: 'rgba(255,215,0,0.06)' }}
              onClick={() => honeypot?.active_listings > 0 ? navigate(`/honeypot?q=${encodeURIComponent(ov.artist + ' ' + ov.album)}`) : navigate('/honeypot')}
              data-testid="honeypot-price-card"
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Store className="w-3.5 h-3.5" style={{ color: '#DAA520' }} />
                <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">The Honeypot Price</span>
              </div>
              {honeypot?.honey_lowest ? (
                <>
                  <p className="text-xl font-heading font-bold" style={{ color: '#1A1A1A' }}>${honeypot.honey_lowest.toFixed(2)}</p>
                  <p className="text-[10px] text-muted-foreground">lowest in the Hive</p>
                </>
              ) : (
                <>
                  <p className="text-sm font-semibold text-muted-foreground">Not listed</p>
                  <p className="text-[10px] font-medium" style={{ color: '#DAA520' }}>List yours &rarr;</p>
                </>
              )}
            </div>
            <Stat icon={DollarSign} label="Median" value={val.discogs_median ? `$${val.discogs_median.toFixed(2)}` : '—'} sub="via Discogs" />
            <Stat icon={TrendingUp} label="High" value={val.discogs_high ? `$${val.discogs_high.toFixed(2)}` : '—'} sub="via Discogs" />
          </div>
        </section>
      )}

      {/* Collectors */}
      {community.owners?.length > 0 && (
        <section className="mb-10" data-testid="collectors-section">
          <h2 className="text-xl font-heading font-bold mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-honey-amber" /> Collectors Who Own This Pressing
          </h2>
          <div className="flex flex-wrap gap-3">
            {community.owners.map(owner => (
              <Link
                key={owner.id}
                to={`/profile/${owner.username}`}
                className="flex items-center gap-2 px-3 py-2 rounded-full bg-honey/5 hover:bg-honey/15 transition-colors border border-honey/20"
                data-testid={`owner-${owner.username}`}
              >
                {owner.avatar_url ? (
                  <img src={resolveImageUrl(owner.avatar_url)} alt={`${owner.username}`} className="w-6 h-6 rounded-full object-cover" />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-honey/30 flex items-center justify-center text-[10px] font-bold">
                    {owner.username?.charAt(0).toUpperCase()}
                  </div>
                )}
                <span className="text-sm font-medium">@{owner.username}</span>
              </Link>
            ))}
            {community.internal_owners_count > 20 && (
              <span className="flex items-center px-3 py-2 text-xs text-muted-foreground">
                +{community.internal_owners_count - 20} more
              </span>
            )}
          </div>
        </section>
      )}

      {/* Action Dialog — Add / Dream List / Seeking */}
      <Dialog open={!!actionModal} onOpenChange={(open) => !open && setActionModal(null)}>
        <DialogContent className="sm:max-w-md p-0 overflow-hidden" data-testid="variant-action-dialog">
          <DialogHeader className="px-6 pt-6 pb-2">
            <DialogTitle className="font-heading flex items-center gap-2">
              {actionModal === 'add' && <><Plus className="w-5 h-5 text-honey-amber" /> Add to Vault</>}
              {actionModal === 'dream' && <><Heart className="w-5 h-5 text-stone-500" /> Dream List</>}
              {actionModal === 'seeking' && <><Search className="w-5 h-5 text-amber-600" /> Seeking (ISO)</>}
            </DialogTitle>
            <DialogDescription>
              {actionModal === 'add' ? `Add ${ov.album} to your vault` : `${ov.artist} — ${ov.album}`}
            </DialogDescription>
          </DialogHeader>

          {actionModal === 'add' ? (
            <div className="px-6 pb-6 pt-2 space-y-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-honey/10">
                {(ov.imageUrl || ov.imageSmall) && <img src={ov.imageSmall || ov.imageUrl} alt="" className="w-12 h-12 rounded-md object-cover" />}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{ov.album}</p>
                  <p className="text-xs text-muted-foreground truncate">{ov.artist} · {ov.variant || 'Standard'}</p>
                </div>
              </div>
              <Button onClick={handleAddToCollection} disabled={actionLoading} className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="variant-add-confirm">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                Add to Vault
              </Button>
            </div>
          ) : (
            <div className="px-6 pb-2 pt-2 space-y-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-honey/10">
                {(ov.imageUrl || ov.imageSmall) && <img src={ov.imageSmall || ov.imageUrl} alt="" className="w-12 h-12 rounded-md object-cover" />}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{ov.album}</p>
                  <p className="text-xs text-muted-foreground truncate">{ov.artist} · {ov.variant || 'Standard'}</p>
                </div>
              </div>
              {postToHive && (
                <MentionTextarea
                  placeholder={actionModal === 'dream' ? "Why is this a grail for you..." : "I'm looking for this because..."}
                  value={caption} onChange={setCaption}
                  className="resize-none" rows={2}
                  style={{ borderColor: 'rgba(200,134,26,0.5)' }}
                  data-testid="variant-action-caption"
                />
              )}
            </div>
          )}

          {actionModal && actionModal !== 'add' && (
            <div className="px-6 pb-6 pt-2 border-t border-honey/15">
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium text-stone-600">Post to Hive</label>
                <button type="button" role="switch" aria-checked={postToHive} onClick={() => setPostToHive(!postToHive)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${postToHive ? 'bg-amber-500' : 'bg-stone-300'}`}
                  data-testid="variant-action-toggle">
                  <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${postToHive ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </button>
              </div>
              {!postToHive && <p className="text-xs text-stone-400 mb-3">{actionModal === 'dream' ? 'Added to your Dream List only.' : 'Saved privately.'}</p>}
              <Button onClick={handleDreamOrSeeking} disabled={actionLoading}
                className="w-full rounded-full"
                style={actionModal === 'dream' ? { background: '#f3f4f6', color: '#374151' } : { background: 'linear-gradient(135deg, #FFD700, #DAA520)', color: '#2A1A06' }}
                data-testid="variant-action-submit">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : actionModal === 'dream' ? <Heart className="w-4 h-4 mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                {postToHive
                  ? (actionModal === 'dream' ? 'Add to Dream List & Share' : 'Post ISO to the Hive')
                  : (actionModal === 'dream' ? 'Add to Dream List' : 'Save ISO Privately')
                }
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
