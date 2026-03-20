import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Disc, TrendingUp, Users, Search, ShoppingCart, MessageCircle, ArrowUpRight, Calendar, DollarSign, BarChart3, Heart, Store, ExternalLink } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import AlbumArt from '../components/AlbumArt';
import UnofficialPill from '../components/UnofficialPill';
import UnofficialDisclaimer from '../components/UnofficialDisclaimer';
import SEOHead from '../components/SEOHead';
import { RarityCard } from '../components/RarityBadge';
import VariantCompletion from '../components/VariantCompletion';
import VariantActions from '../components/VariantActions';
import { useAuth } from '../context/AuthContext';
import { resolveImageUrl } from '../utils/imageUrl';
import axios from 'axios';

import { API_BASE } from '../utils/apiBase';
const BACKEND_URL = API_BASE;
const API = `${BACKEND_URL}/api`;

const StatCard = ({ icon: Icon, label, value, sub, onClick }) => (
  <Card
    className={`p-4 border-honey/20 bg-honey/5 transition-all duration-200 ${onClick ? 'cursor-pointer hover:-translate-y-0.5 hover:shadow-md hover:bg-honey/10 active:translate-y-0' : ''}`}
    data-testid={`stat-${label.toLowerCase().replace(/\s/g, '-')}`}
    onClick={onClick}
    role={onClick ? 'button' : undefined}
    tabIndex={onClick ? 0 : undefined}
  >
    <div className="flex items-center gap-2 mb-1">
      <Icon className="w-4 h-4 text-honey-amber" />
      <span className="text-xs text-muted-foreground uppercase tracking-wider">{label}</span>
    </div>
    <p className="text-2xl font-heading font-bold text-vinyl-black">{value ?? '—'}</p>
    {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
  </Card>
);

export default function VinylVariantPage() {
  const { artist, album, variant } = useParams();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [spotifyLink, setSpotifyLink] = useState(null);

  useEffect(() => {
    setData(null);  // Clear previous variant data to prevent "ghosting"
    setLoading(true);
    setError(null);
    setSpotifyLink(null);
    axios.get(`${API}/vinyl/${artist}/${album}/${variant}`)
      .then(res => {
        setData(res.data);
        // Fetch Spotify link if we have a discogs_id
        const discogsId = res.data?.variant_overview?.discogs_id;
        if (discogsId && token) {
          axios.get(`${API}/spotify/link/${discogsId}`, { headers: { Authorization: `Bearer ${token}` } })
            .then(sr => setSpotifyLink(sr.data))
            .catch(() => {});
        }
      })
      .catch(() => setError('Variant not found'))
      .finally(() => setLoading(false));
  }, [artist, album, variant, token]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 pt-3 md:pt-2 pb-28 flex items-center justify-center">
        <Disc className="w-8 h-8 animate-spin text-honey" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto px-4 pt-3 md:pt-2 pb-28 text-center">
        <Disc className="w-12 h-12 text-honey/40 mx-auto mb-4" />
        <h1 className="text-xl font-heading mb-2">Variant Not Found</h1>
        <p className="text-muted-foreground text-sm mb-6">We don't have data for this variant yet. As collectors add it, this page will come alive.</p>
        <Button onClick={() => navigate('/honeypot')} className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full">Browse Marketplace</Button>
      </div>
    );
  }

  const scrollTo = (testId) => {
    document.querySelector(`[data-testid="${testId}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const { variant_overview: ov, marketplace: mp, value: val, demand: dm, activity: act, seo, rarity } = data;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-28" data-testid="vinyl-variant-page">
      <SEOHead
        title={seo.title}
        description={seo.description}
        url={seo.canonical}
        image={seo.image}
        type="product"
        vinylMeta={{
          artist: ov.artist,
          album: ov.album,
          variant: ov.variant,
          year: ov.year,
          label: ov.label,
          catno: ov.catalog_number,
          format: ov.format,
        }}
        productMeta={mp.active_listings?.length ? {
          price: Math.min(...mp.active_listings.filter(l => l.price).map(l => l.price)),
          currency: 'USD',
          availability: 'in stock',
        } : undefined}
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'Product',
          name: `${ov.artist} — ${ov.album} (${ov.variant})`,
          image: ov.imageUrl || ov.imageSmall,
          category: 'Vinyl Record',
          url: `https://thehoneygroove.com${seo.canonical}`,
          brand: { '@type': 'MusicGroup', name: ov.artist },
          description: seo.description,
          additionalProperty: [
            { '@type': 'PropertyValue', name: 'Variant', value: ov.variant },
            { '@type': 'PropertyValue', name: 'Format', value: ov.format || 'Vinyl' },
            ...(ov.year ? [{ '@type': 'PropertyValue', name: 'Release Year', value: String(ov.year) }] : []),
          ],
          ...(val.average_value ? {
            offers: {
              '@type': 'AggregateOffer',
              lowPrice: String(val.lowest_sale || val.average_value),
              highPrice: String(val.highest_sale || val.average_value),
              priceCurrency: 'USD',
              offerCount: String(val.recent_sales_count),
            },
          } : {}),
        }}
      />

      {/* ===== HERO: Variant Overview ===== */}
      <section className="mb-10" data-testid="variant-overview">
        <div className="flex flex-col md:flex-row gap-6 items-start">
          {/* Album Art */}
          <div className="w-full md:w-64 shrink-0">
            <div
              className="relative aspect-square overflow-hidden bg-stone-200 transition-transform duration-150 ease-out hover:-translate-y-[3px]"
              style={{ borderRadius: '14px', boxShadow: '0 12px 28px rgba(0,0,0,0.12)' }}
            >
              <AlbumArt
                imageUrl={ov.imageUrl}
                imageSmall={ov.imageSmall}
                imageSource={ov.imageSource}
                needsCoverPhoto={ov.needsCoverPhoto}
                albumTitle={ov.album}
                artistName={ov.artist}
                size="large"
                alt={`${ov.artist} ${ov.album} ${ov.variant} vinyl record`}
                className="w-full h-full object-cover"
                isUnofficial={ov.is_unofficial}
                formatText={ov.format || ''}
              />
              {/* Variant pill — hidden on Spotify-sourced art (Spotify compliance §1.1); variant name shown in info section instead */}
              {ov.imageSource !== 'spotify' && (
                <div
                  className="absolute bottom-3 left-3 right-3 truncate uppercase text-[11px] font-bold px-3 py-1 rounded-full text-center"
                  style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                  data-testid="variant-pill"
                >
                  {ov.variant}
                </div>
              )}
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm text-honey-amber font-medium uppercase tracking-wider mb-1">{ov.variant} Variant</p>
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
              {ov.barcode && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-honey/10 text-xs text-vinyl-black/70 font-mono" data-testid="variant-upc">
                  UPC: {ov.barcode}
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
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              )}
            </div>

            {/* Discogs attribution — required per Discogs API TOS */}
            {ov.discogs_id && (
              <p className="text-[10px] text-muted-foreground/60 mt-1">
                <a
                  href={`https://www.discogs.com/release/${ov.discogs_id}`}
                  target="_blank"
                  rel="noopener"
                  className="hover:text-muted-foreground transition-colors"
                >
                  Data provided by Discogs
                </a>
              </p>
            )}

            {/* Quick stats row */}
            <div className="grid grid-cols-3 gap-3">
              <StatCard icon={Users} label="Collectors" value={dm.owners_count} sub="own this pressing" onClick={() => scrollTo('collectors-section')} />
              <StatCard icon={Search} label="Searching" value={dm.iso_count} sub="have it on ISO" onClick={() => scrollTo('marketplace-section')} />
              <StatCard icon={Heart} label="Posts" value={dm.post_count} sub="in the Hive" onClick={() => scrollTo('activity-section')} />
            </div>

            {/* Action buttons */}
            <VariantActions variant={ov} />
          </div>
        </div>
      </section>

      {/* BLOCK 591: Unofficial Release Disclaimer */}
      {ov.is_unofficial && (
        <section className="mb-10" data-testid="unofficial-section">
          <UnofficialDisclaimer />
        </section>
      )}

      {/* ===== RARITY SCORE ===== */}
      {rarity && (
        <section className="mb-10" data-testid="rarity-section">
          <RarityCard rarity={rarity} />
        </section>
      )}

      {/* ===== VARIANT COMPLETION ===== */}
      {ov.discogs_id && (
        <section className="mb-10" data-testid="completion-section">
          <VariantCompletion discogsId={ov.discogs_id} />
        </section>
      )}

      {/* ===== MARKET VALUE ===== */}
      <section className="mb-10" data-testid="value-section">
        <h2 className="text-xl font-heading font-bold mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-honey-amber" /> Market Value
        </h2>
        {val.recent_sales_count > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard icon={DollarSign} label="Avg. Value" value={val.average_value ? `$${val.average_value.toFixed(2)}` : '—'} />
            <StatCard icon={TrendingUp} label="Highest Sale" value={val.highest_sale ? `$${val.highest_sale.toFixed(2)}` : '—'} />
            <StatCard icon={ShoppingCart} label="Sales" value={val.recent_sales_count} sub="recorded" />
            {/* The Honeypot Price: internal listing price */}
            <div
              className="rounded-xl p-3 border cursor-pointer hover:shadow-md transition-all"
              style={{ borderColor: 'rgba(218,165,32,0.3)', background: 'rgba(255,215,0,0.06)' }}
              onClick={() => mp.listing_count > 0 ? document.querySelector('[data-testid="marketplace-section"]')?.scrollIntoView({ behavior: 'smooth' }) : navigate('/honeypot')}
              data-testid="honeypot-price-card"
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Store className="w-3.5 h-3.5" style={{ color: '#DAA520' }} />
                <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">The Honeypot Price</span>
              </div>
              {mp.honey_lowest ? (
                <>
                  <p className="text-xl font-heading font-bold" style={{ color: '#1A1A1A' }}>${mp.honey_lowest.toFixed(2)}</p>
                  <p className="text-[10px] text-muted-foreground">lowest in the Hive</p>
                </>
              ) : (
                <>
                  <p className="text-sm font-semibold text-muted-foreground">Not for sale</p>
                  <p className="text-[10px] font-medium" style={{ color: '#DAA520' }}>List yours &rarr;</p>
                </>
              )}
            </div>
          </div>
        ) : val.discogs_median ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <StatCard icon={DollarSign} label="Median Value" value={`$${val.discogs_median.toFixed(2)}`} sub="via Discogs" />
            <StatCard icon={TrendingUp} label="High" value={val.discogs_high ? `$${val.discogs_high.toFixed(2)}` : '—'} sub="via Discogs" />
            {/* The Honeypot Price fallback */}
            <div
              className="rounded-xl p-3 border cursor-pointer hover:shadow-md transition-all"
              style={{ borderColor: 'rgba(218,165,32,0.3)', background: 'rgba(255,215,0,0.06)' }}
              onClick={() => mp.listing_count > 0 ? document.querySelector('[data-testid="marketplace-section"]')?.scrollIntoView({ behavior: 'smooth' }) : navigate('/honeypot')}
              data-testid="honeypot-price-card"
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Store className="w-3.5 h-3.5" style={{ color: '#DAA520' }} />
                <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">The Honeypot Price</span>
              </div>
              {mp.honey_lowest ? (
                <>
                  <p className="text-xl font-heading font-bold" style={{ color: '#1A1A1A' }}>${mp.honey_lowest.toFixed(2)}</p>
                  <p className="text-[10px] text-muted-foreground">lowest in the Hive</p>
                </>
              ) : (
                <>
                  <p className="text-sm font-semibold text-muted-foreground">Not for sale</p>
                  <p className="text-[10px] font-medium" style={{ color: '#DAA520' }}>List yours &rarr;</p>
                </>
              )}
            </div>
          </div>
        ) : (
          <Card className="p-6 border-honey/20 text-center">
            <p className="text-muted-foreground text-sm">No recorded sales yet. Be the first to list this variant.</p>
            {user && (
              <Button onClick={() => navigate('/honeypot')} className="mt-3 bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs">
                List on The Honeypot
              </Button>
            )}
          </Card>
        )}
      </section>

      {/* ===== MARKETPLACE LISTINGS ===== */}
      <section className="mb-10" data-testid="marketplace-section">
        <h2 className="text-xl font-heading font-bold mb-4 flex items-center gap-2">
          <ShoppingCart className="w-5 h-5 text-honey-amber" /> Marketplace
        </h2>
        {mp.listing_count > 0 ? (
          <div className="space-y-3">
            {mp.active_listings.map((listing, i) => (
              <Card key={listing.id || i} className="p-4 border-honey/20 hover:shadow-honey transition-all cursor-pointer" data-testid={`listing-${listing.id}`}
                onClick={() => navigate(`/honeypot/listing/${listing.id}`)}>
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-lg overflow-hidden bg-stone-200 shrink-0">
                    <AlbumArt
                      src={listing.photo_urls?.[0] || listing.cover_url || ov.imageSmall || ov.imageUrl}
                      alt={`${listing.artist} ${listing.album}${listing.pressing_notes ? ` ${listing.pressing_notes}` : ''} vinyl record`}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-heading font-bold text-lg text-vinyl-black">
                        {listing.price ? `$${listing.price.toFixed(2)}` : 'Make Offer'}
                      </span>
                      {listing.listing_type === 'TRADE' && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-700">FOR TRADE</span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {listing.condition && `${listing.condition} · `}
                      Seller: @{listing.seller?.username || 'Unknown'}
                    </p>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground shrink-0" />
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-6 border-honey/20 text-center">
            <p className="text-muted-foreground text-sm">No active listings for this variant right now.</p>
            {user && (
              <Button onClick={() => navigate('/honeypot')} className="mt-3 bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs">
                Sell Yours
              </Button>
            )}
          </Card>
        )}
      </section>

      {/* ===== COLLECTORS ===== */}
      <section className="mb-10" data-testid="collectors-section">
        <h2 className="text-xl font-heading font-bold mb-4 flex items-center gap-2">
          <Users className="w-5 h-5 text-honey-amber" /> Collectors Who Own It
        </h2>
        {act.owners?.length > 0 ? (
          <div className="flex flex-wrap gap-3">
            {act.owners.map(owner => (
              <Link key={owner.id} to={`/profile/${owner.username}`} className="flex items-center gap-2 px-3 py-2 rounded-full bg-honey/5 hover:bg-honey/15 transition-colors border border-honey/20" data-testid={`owner-${owner.username}`}>
                {owner.avatar_url ? (
                  <img src={resolveImageUrl(owner.avatar_url)} alt={`${owner.username} avatar`} className="w-6 h-6 rounded-full object-cover" />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-honey/30 flex items-center justify-center text-[10px] font-bold">{owner.username?.charAt(0).toUpperCase()}</div>
                )}
                <span className="text-sm font-medium">@{owner.username}</span>
              </Link>
            ))}
            {dm.owners_count > 20 && (
              <span className="flex items-center px-3 py-2 text-xs text-muted-foreground">+{dm.owners_count - 20} more</span>
            )}
          </div>
        ) : (
          <Card className="p-6 border-honey/20 text-center">
            <p className="text-muted-foreground text-sm">No collectors have added this variant yet.</p>
          </Card>
        )}
      </section>

      {/* ===== HIVE ACTIVITY ===== */}
      <section className="mb-10" data-testid="activity-section">
        <h2 className="text-xl font-heading font-bold mb-4 flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-honey-amber" /> Hive Activity
        </h2>
        {act.recent_posts?.length > 0 ? (
          <div className="space-y-3">
            {act.recent_posts.map((post, i) => {
              const typeLabels = {
                NOW_SPINNING: 'Now Spinning',
                ADDED_TO_COLLECTION: 'Added to Collection',
                NEW_HAUL: 'New Haul',
                ISO: 'ISO',
                A_NOTE: 'A Note',
              };
              return (
                <Card key={post.id || i} className="p-4 border-honey/20" data-testid={`post-${post.id}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {post.user?.avatar_url ? (
                      <img src={resolveImageUrl(post.user.avatar_url)} alt={`${post.user?.username} avatar`} className="w-6 h-6 rounded-full object-cover" />
                    ) : (
                      <div className="w-6 h-6 rounded-full bg-honey/30 flex items-center justify-center text-[10px] font-bold">{post.user?.username?.charAt(0).toUpperCase() || '?'}</div>
                    )}
                    <span className="text-sm font-medium">@{post.user?.username || 'Unknown'}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-honey/10 text-honey-amber">{typeLabels[post.post_type] || post.post_type}</span>
                  </div>
                  {post.caption && <p className="text-sm text-vinyl-black/80">{post.caption.slice(0, 200)}</p>}
                </Card>
              );
            })}
          </div>
        ) : (
          <Card className="p-6 border-honey/20 text-center">
            <p className="text-muted-foreground text-sm">No Hive posts for this variant yet. Spin it and share!</p>
          </Card>
        )}
      </section>
    </div>
  );
}
