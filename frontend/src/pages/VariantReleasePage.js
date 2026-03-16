import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Disc, Users, TrendingUp, DollarSign, BarChart3,
  Calendar, ArrowLeft, Loader2, Heart, RefreshCw, Store
} from 'lucide-react';
import { Card } from '../components/ui/card';
import AlbumArt from '../components/AlbumArt';
import UnofficialPill from '../components/UnofficialPill';
import UnofficialDisclaimer from '../components/UnofficialDisclaimer';
import SEOHead from '../components/SEOHead';
import { RarityCard } from '../components/RarityBadge';
import { useAuth } from '../context/AuthContext';
import { resolveImageUrl } from '../utils/imageUrl';
import axios from 'axios';

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

  useEffect(() => {
    setData(null);  // Clear previous variant data to prevent "ghosting"
    setLoading(true);
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    axios.get(`${API}/vinyl/release/${releaseId}`, { headers })
      .then(r => setData(r.data))
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

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-28" data-testid="variant-release-page">
      <SEOHead
        title={`${ov.artist} — ${ov.album} (${ov.variant || 'Standard'})`}
        description={`${ov.variant || 'Standard'} pressing of ${ov.album} by ${ov.artist}. ${scarcity.discogs_have} global owners.`}
        url={`/variant/${releaseId}`}
        image={ov.cover_url}
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
            {ov.cover_url ? (
              <AlbumArt src={ov.cover_url} alt={`${ov.artist} ${ov.album} ${ov.variant} vinyl`} className="w-full h-full object-cover" isUnofficial={ov.is_unofficial} formatText={ov.format || ''} />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Disc className="w-16 h-16 text-honey/30" />
              </div>
            )}
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
          <p className="text-sm text-honey-amber font-medium uppercase tracking-wider mb-1">{ov.variant || 'Standard'} Pressing</p>
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
          </div>

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
                  cover_url: ov.cover_url || '',
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
    </div>
  );
}
