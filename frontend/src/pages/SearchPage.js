import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, TrendingUp, Gem, Heart, Clock, ChevronRight, Loader2 } from 'lucide-react';
import { Card } from '../components/ui/card';
import { RarityPill } from '../components/RarityBadge';
import AlbumArt from '../components/AlbumArt';
import ScrollRow from '../components/ScrollRow';
import SEOHead from '../components/SEOHead';
import { useAuth } from '../context/AuthContext';
import { useVariantModal } from '../context/VariantModalContext';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

/* ─── Variant Quick Card ─── */
const VariantCard = ({ v, onOpen }) => (
  <button
    onClick={() => onOpen(v)}
    className="flex gap-3 p-3 rounded-xl hover:bg-honey/8 transition-all group text-left w-full"
    data-testid={`variant-card-${v.discogs_id || 'local'}`}
  >
    <div className="w-16 h-16 rounded-lg overflow-hidden shrink-0 bg-stone-100 shadow-sm">
      <AlbumArt
        src={v.cover_url}
        alt={`${v.artist} ${v.album} ${v.variant} vinyl record`}
        className="w-full h-full object-cover"
      />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-semibold text-vinyl-black truncate group-hover:text-honey-amber transition-colors">
        {v.album}
      </p>
      <p className="text-xs text-muted-foreground truncate">{v.artist}</p>
      <div className="flex items-center gap-2 mt-1">
        <span className="text-[11px] font-medium text-honey-amber bg-honey/10 px-2 py-0.5 rounded-full truncate max-w-[160px]">
          {v.variant}
        </span>
        {v.collectors > 0 && (
          <span className="text-[10px] text-muted-foreground">{v.collectors} collectors</span>
        )}
      </div>
    </div>
    {v.rarity_tier && <RarityPill tier={v.rarity_tier} size="sm" />}
  </button>
);

/* ─── Discovery Section ─── */
const DiscoverySection = ({ title, icon: Icon, items, onOpen }) => {
  if (!items?.length) return null;
  return (
    <section className="mb-8" data-testid={`discover-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4.5 h-4.5 text-honey-amber" />
        <h2 className="font-heading text-base font-bold text-vinyl-black">{title}</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
        {items.map((v, i) => (
          <VariantCard key={`${v.discogs_id}-${i}`} v={v} onOpen={onOpen} />
        ))}
      </div>
    </section>
  );
};

/* ─── Main SearchPage ─── */
export default function SearchPage() {
  const { token } = useAuth();
  const { openVariantModal } = useVariantModal();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQ = searchParams.get('q') || '';
  const [query, setQuery] = useState(initialQ);
  const [results, setResults] = useState(null);
  const [discover, setDiscover] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(0);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);
  const PAGE_SIZE = 20;

  const handleOpenVariant = (v) => {
    openVariantModal({
      artist: v.artist,
      album: v.album || v.title,
      variant: v.variant || '',
      discogs_id: v.discogs_id,
      cover_url: v.cover_url,
    });
  };

  // Focus input on mount
  useEffect(() => { inputRef.current?.focus(); }, []);

  // Load discovery data when no query
  useEffect(() => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    axios.get(`${API}/search/discover`, { headers })
      .then(r => setDiscover(r.data))
      .catch(() => {});
  }, [token]);

  // Debounced search
  const doSearch = useCallback((q, skip = 0) => {
    if (q.length < 2) { setResults(null); setLoading(false); return; }
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const isMore = skip > 0;
    if (isMore) setLoadingMore(true); else setLoading(true);

    axios.get(`${API}/search/variants`, { params: { q, skip, limit: PAGE_SIZE }, headers })
      .then(r => {
        if (isMore) {
          setResults(prev => prev ? {
            ...r.data,
            variants: [...prev.variants, ...r.data.variants],
          } : r.data);
        } else {
          setResults(r.data);
        }
        setPage(skip);
      })
      .catch(() => {})
      .finally(() => { setLoading(false); setLoadingMore(false); });
  }, [token]);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults(null);
      setSearchParams({}, { replace: true });
      return;
    }
    setSearchParams({ q: query }, { replace: true });
    debounceRef.current = setTimeout(() => doSearch(query, 0), 180);
    return () => clearTimeout(debounceRef.current);
  }, [query, doSearch, setSearchParams]);

  const loadMore = () => {
    if (results?.has_more && !loadingMore) {
      doSearch(query, page + PAGE_SIZE);
    }
  };

  const showDiscover = !query.trim() && discover;
  const hasResults = results && (results.variants?.length > 0 || results.albums?.length > 0);

  return (
    <div className="min-h-screen bg-white" data-testid="search-page">
      <SEOHead title="Search Vinyl Variants | The Honey Groove" description="Discover rare vinyl variants, albums, and artists." />

      {/* Search Bar — offset below fixed navbar */}
      <div className="sticky top-[52px] md:top-[88px] z-30 bg-white/95 backdrop-blur-md border-b border-honey/10 px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-honey-amber" />
            <input
              ref={inputRef}
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search artists, albums, or vinyl variants"
              className="w-full h-12 pl-11 pr-4 rounded-full border-2 border-honey/30 bg-honey/5 text-sm text-vinyl-black placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-honey/40 focus:border-honey/50 transition-all shadow-sm"
              data-testid="search-input"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-medium text-stone-400 hover:text-vinyl-black px-2 py-1 rounded-full hover:bg-stone-100 transition-colors"
                data-testid="search-clear"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">
        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-honey-amber" />
          </div>
        )}

        {/* Search Results */}
        {!loading && hasResults && (
          <>
            {/* Variant Results (Priority) */}
            {results.variants?.length > 0 && (
              <section className="mb-8" data-testid="search-variants">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="font-heading text-base font-bold text-vinyl-black">Variants</h2>
                  <span className="text-xs text-muted-foreground">{results.total} results</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
                  {results.variants.map((v, i) => (
                    <VariantCard key={`${v.discogs_id}-${i}`} v={v} onOpen={handleOpenVariant} />
                  ))}
                </div>
                {results.has_more && (
                  <button
                    onClick={loadMore}
                    disabled={loadingMore}
                    className="w-full mt-4 py-2.5 text-sm text-honey-amber hover:text-amber-600 font-medium flex items-center justify-center gap-1.5 transition-colors"
                    data-testid="load-more"
                  >
                    {loadingMore ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
                    {loadingMore ? 'Loading...' : 'Show More Variants'}
                  </button>
                )}
              </section>
            )}

            {/* Album Results */}
            {results.albums?.length > 0 && (
              <section className="mb-8" data-testid="search-albums">
                <h2 className="font-heading text-base font-bold text-vinyl-black mb-3">Albums</h2>
                <ScrollRow>
                  {results.albums.map((a, i) => (
                    <button
                      key={`${a.discogs_id}-${i}`}
                      onClick={() => handleOpenVariant(a)}
                      className="shrink-0 w-28 group text-left"
                      data-testid={`album-card-${a.discogs_id || i}`}
                    >
                      <div className="w-28 h-28 rounded-lg overflow-hidden bg-stone-100 shadow-sm mb-1.5">
                        <AlbumArt
                          src={a.cover_url}
                          alt={`${a.artist} ${a.title} vinyl record`}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <p className="text-xs font-semibold text-vinyl-black truncate group-hover:text-honey-amber transition-colors">{a.title}</p>
                      <p className="text-[10px] text-muted-foreground truncate">{a.artist}</p>
                      <p className="text-[10px] text-honey-amber">{a.variant_count} variant{a.variant_count !== 1 ? 's' : ''}</p>
                    </button>
                  ))}
                </ScrollRow>
              </section>
            )}

            {/* Artist Results */}
            {results.artists?.length > 0 && (
              <section className="mb-8" data-testid="search-artists">
                <h2 className="font-heading text-base font-bold text-vinyl-black mb-3">Artists</h2>
                <ScrollRow>
                  {results.artists.map(a => (
                    <button
                      key={a.name}
                      onClick={() => setQuery(a.name)}
                      className="shrink-0 w-24 flex flex-col items-center gap-1.5 group"
                      data-testid={`artist-card-${a.name}`}
                    >
                      <div className="w-20 h-20 rounded-full overflow-hidden bg-stone-100 shadow-sm ring-2 ring-transparent group-hover:ring-honey/40 transition-all">
                        {a.image_url ? (
                          <img src={a.image_url} alt={a.name} className="w-full h-full object-cover" loading="lazy" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-honey/20 to-stone-200 text-2xl font-heading font-bold text-honey-amber/60">
                            {a.name.charAt(0)}
                          </div>
                        )}
                      </div>
                      <p className="text-xs font-medium text-vinyl-black text-center truncate w-full group-hover:text-honey-amber transition-colors">
                        {a.name}
                      </p>
                    </button>
                  ))}
                </ScrollRow>
              </section>
            )}
          </>
        )}

        {/* No Results */}
        {!loading && query.length >= 2 && !hasResults && results !== null && (
          <div className="text-center py-16" data-testid="no-results">
            <Search className="w-10 h-10 text-stone-300 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No variants found for "{query}"</p>
            <p className="text-xs text-stone-400 mt-1">Try a different artist, album, or color</p>
          </div>
        )}

        {/* Discovery Sections (Empty State) */}
        {showDiscover && (
          <div data-testid="discover-sections">
            <DiscoverySection title="Trending Variants" icon={TrendingUp} items={discover.trending} onOpen={handleOpenVariant} />
            <DiscoverySection title="Rare Variants" icon={Gem} items={discover.rare} onOpen={handleOpenVariant} />
            <DiscoverySection title="Most Wanted" icon={Heart} items={discover.most_wanted} onOpen={handleOpenVariant} />
            <DiscoverySection title="Recently Added" icon={Clock} items={discover.recently_added} onOpen={handleOpenVariant} />
          </div>
        )}
      </div>
    </div>
  );
}
