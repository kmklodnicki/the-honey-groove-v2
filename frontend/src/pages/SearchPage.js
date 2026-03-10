import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, TrendingUp, Gem, Heart, Clock, ChevronRight, Loader2, SlidersHorizontal, X, ChevronDown, Users } from 'lucide-react';
import { Card } from '../components/ui/card';
import AlbumArt from '../components/AlbumArt';
import ScrollRow from '../components/ScrollRow';
import SEOHead from '../components/SEOHead';
import { useAuth } from '../context/AuthContext';
import { useVariantModal } from '../context/VariantModalContext';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

/* ─── Tag color map for collector metadata pills ─── */
const TAG_STYLES = {
  RSD:            { bg: '#FCEED6', color: '#B97A00' },
  Limited:        { bg: '#F4EFFF', color: '#6C54E8' },
  Exclusive:      { bg: '#EAF7F2', color: '#2F8F6B' },
  Numbered:       { bg: '#FFF3F0', color: '#C15A3A' },
  Signed:         { bg: '#F7EAF3', color: '#A14578' },
  'Test Pressing':{ bg: '#F0F4FF', color: '#4A6FA5' },
  Tour:           { bg: '#FFF8E6', color: '#9A7B2D' },
};

/* ─── Variant Quick Card ─── */
const VariantCard = ({ v, onOpen }) => (
  <button
    onClick={() => onOpen(v)}
    className="flex gap-3 p-2.5 rounded-xl hover:bg-honey/8 transition-all group text-left w-full"
    data-testid={`variant-card-${v.discogs_id || 'local'}`}
  >
    <div className="w-14 h-14 rounded-lg overflow-hidden shrink-0 bg-stone-100 shadow-sm">
      <AlbumArt
        src={v.cover_url}
        alt={`${v.artist} ${v.album} ${v.variant} vinyl record`}
        className="w-full h-full object-cover"
      />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-semibold text-vinyl-black truncate group-hover:text-honey-amber transition-colors">
        {v.album} {v.year ? <span className="text-muted-foreground font-normal">({v.year})</span> : null}
      </p>
      <p className="text-xs text-muted-foreground truncate">{v.artist}</p>
      <div className="flex items-center gap-1.5 mt-1 flex-wrap">
        <span className="text-[11px] font-medium text-honey-amber bg-honey/10 px-2.5 py-0.5 rounded-full truncate max-w-[160px]">
          {v.variant}
        </span>
        {v.tags?.map(tag => {
          const style = TAG_STYLES[tag] || { bg: '#F5F5F5', color: '#666' };
          return (
            <span
              key={tag}
              className="text-[11px] font-medium px-2.5 leading-none rounded-full"
              style={{ background: style.bg, color: style.color, padding: '4px 10px' }}
              data-testid={`tag-${tag.toLowerCase().replace(/\s+/g, '-')}`}
            >
              {tag}
            </span>
          );
        })}
        {v.collectors > 0 && (
          <span className="text-[10px] text-muted-foreground">{v.collectors} have</span>
        )}
      </div>
    </div>
  </button>
);

/* ─── Discovery Section ─── */
const DiscoverySection = ({ title, icon: Icon, items, onOpen }) => {
  if (!items?.length) return null;
  return (
    <section className="mb-5" data-testid={`discover-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-honey-amber" />
        <h2 className="font-heading text-sm font-bold text-vinyl-black">{title}</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-0.5">
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
  const [userResults, setUserResults] = useState(null);
  const [page, setPage] = useState(0);
  const [activeFilters, setActiveFilters] = useState(new Set());
  const [yearFrom, setYearFrom] = useState(null);
  const [yearTo, setYearTo] = useState(null);
  const [filterOpen, setFilterOpen] = useState(false);
  const filterRef = useRef(null);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);
  const PAGE_SIZE = 20;

  const ATTRIBUTE_CHIPS = [
    { key: 'RSD',       label: 'RSD' },
    { key: 'Limited',   label: 'Limited' },
    { key: 'Exclusive', label: 'Exclusive' },
    { key: 'Signed',    label: 'Signed' },
    { key: 'Numbered',  label: 'Numbered' },
    { key: 'Tour',      label: 'Tour' },
  ];

  const toggleFilter = (key) => {
    setActiveFilters(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const clearAllFilters = () => {
    setActiveFilters(new Set());
    setYearFrom(null);
    setYearTo(null);
  };

  const hasYearFilter = yearFrom !== null || yearTo !== null;
  const hasAnyFilter = activeFilters.size > 0 || hasYearFilter;
  const totalFilterCount = activeFilters.size + (hasYearFilter ? 1 : 0);

  // Close filter drawer on outside click
  useEffect(() => {
    const handler = (e) => {
      if (filterRef.current && !filterRef.current.contains(e.target)) setFilterOpen(false);
    };
    if (filterOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [filterOpen]);

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

    // Fetch matching users in parallel (only on first page)
    if (!isMore) {
      axios.get(`${API}/search/users`, { params: { q, limit: 6 }, headers })
        .then(r => setUserResults(r.data.users || []))
        .catch(() => setUserResults([]));
    }
  }, [token]);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults(null);
      setUserResults(null);
      clearAllFilters();
      setSearchParams({}, { replace: true });
      return;
    }
    setSearchParams({ q: query }, { replace: true });
    clearAllFilters();
    debounceRef.current = setTimeout(() => doSearch(query, 0), 180);
    return () => clearTimeout(debounceRef.current);
  }, [query, doSearch, setSearchParams]);

  const loadMore = () => {
    if (results?.has_more && !loadingMore) {
      doSearch(query, page + PAGE_SIZE);
    }
  };

  const showDiscover = !query.trim() && discover;
  const hasResults = (results && (results.variants?.length > 0 || results.albums?.length > 0)) || (userResults && userResults.length > 0);

  // Client-side filtering (tags + years)
  const allVariants = results?.variants || [];

  // Extract available years (full sorted list for dropdown)
  const availableYears = {};
  allVariants.forEach(v => {
    if (v.year) availableYears[v.year] = (availableYears[v.year] || 0) + 1;
  });
  const yearList = Object.keys(availableYears)
    .map(Number)
    .filter(y => y > 1900)
    .sort((a, b) => b - a);

  // Collect available tags from current results
  const availableTags = new Set();
  allVariants.forEach(v => (v.tags || []).forEach(t => availableTags.add(t)));

  // Apply all filters
  const filteredVariants = allVariants.filter(v => {
    // Tag filter
    if (activeFilters.size > 0) {
      const tags = v.tags || [];
      if (![...activeFilters].every(f => tags.includes(f))) return false;
    }
    // Year range filter
    if (hasYearFilter) {
      const yr = v.year;
      if (!yr) return false;
      if (yearFrom !== null && yr < yearFrom) return false;
      if (yearTo !== null && yr > yearTo) return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-white pt-[52px] md:pt-[88px]" data-testid="search-page">
      <SEOHead title="Search Vinyl Variants | The Honey Groove" description="Discover rare vinyl variants, albums, and artists." />

      {/* Search Bar — compact sticky bar */}
      <div className="sticky top-[52px] md:top-[88px] z-30 bg-white/95 backdrop-blur-md border-b border-honey/10 px-4 py-2 overflow-visible">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-honey-amber" />
            <input
              ref={inputRef}
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search artists, albums, or vinyl variants"
              className="w-full h-11 pl-10 pr-4 rounded-full border border-honey/25 bg-honey/5 text-sm text-vinyl-black placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-honey/40 focus:border-honey/50 transition-all"
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

        {/* Filter bar — toggle + scrollable active chips */}
        {hasResults && (
          <div className="max-w-2xl mx-auto mt-2" data-testid="filter-bar">
            <div className="flex items-center gap-1.5">
              {/* Filter toggle + dropdown — outside overflow container */}
              <div className="relative shrink-0" ref={filterRef}>
                <button
                  onClick={() => setFilterOpen(prev => !prev)}
                  className="flex items-center gap-1 text-[11px] font-medium px-3 py-1.5 rounded-full border transition-all"
                  style={{
                    background: filterOpen || hasAnyFilter ? '#FFF8EE' : '#FAFAFA',
                    borderColor: filterOpen || hasAnyFilter ? '#E8C675' : '#E5E5E5',
                    color: filterOpen || hasAnyFilter ? '#B97A00' : '#666',
                  }}
                  data-testid="filter-toggle"
                >
                  <SlidersHorizontal className="w-3 h-3" />
                  Filters
                  {totalFilterCount > 0 && (
                    <span className="ml-0.5 w-4 h-4 rounded-full bg-honey-amber text-white text-[9px] flex items-center justify-center font-bold">{totalFilterCount}</span>
                  )}
                  <ChevronDown className={`w-3 h-3 transition-transform ${filterOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Filter Drawer */}
                {filterOpen && (
                  <div
                    className="absolute left-0 top-full mt-1.5 w-72 bg-white rounded-xl shadow-lg border border-stone-200/80 p-4 z-50"
                    data-testid="filter-drawer"
                  >
                    {availableTags.size > 0 && (
                      <div className="mb-4">
                        <p className="text-[10px] uppercase tracking-wider text-stone-400 font-semibold mb-2">Attributes</p>
                        <div className="flex flex-wrap gap-1.5">
                          {ATTRIBUTE_CHIPS.filter(c => availableTags.has(c.key)).map(chip => {
                            const active = activeFilters.has(chip.key);
                            return (
                              <button
                                key={chip.key}
                                onClick={() => toggleFilter(chip.key)}
                                className={`text-[11px] font-medium px-2.5 py-1 rounded-full border transition-all ${
                                  active
                                    ? 'bg-vinyl-black text-white border-vinyl-black'
                                    : 'bg-stone-50 text-stone-600 border-stone-200 hover:border-stone-300'
                                }`}
                                data-testid={`filter-${chip.key.toLowerCase()}`}
                              >
                                {chip.label}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Year range */}
                    {yearList.length > 0 && (
                      <div className="mb-3">
                        <p className="text-[10px] uppercase tracking-wider text-stone-400 font-semibold mb-2">Year</p>
                        <div className="flex items-center gap-2">
                          <select
                            value={yearFrom ?? ''}
                            onChange={e => setYearFrom(e.target.value ? Number(e.target.value) : null)}
                            className="flex-1 text-[11px] font-medium px-2.5 py-1.5 rounded-lg border border-stone-200 bg-stone-50 text-stone-600 focus:outline-none focus:ring-1 focus:ring-honey/40 focus:border-honey/50 appearance-none cursor-pointer"
                            data-testid="filter-year-from"
                          >
                            <option value="">From</option>
                            {yearList.map(y => (
                              <option key={y} value={y} disabled={yearTo !== null && y > yearTo}>{y}</option>
                            ))}
                          </select>
                          <span className="text-[10px] text-stone-400">to</span>
                          <select
                            value={yearTo ?? ''}
                            onChange={e => setYearTo(e.target.value ? Number(e.target.value) : null)}
                            className="flex-1 text-[11px] font-medium px-2.5 py-1.5 rounded-lg border border-stone-200 bg-stone-50 text-stone-600 focus:outline-none focus:ring-1 focus:ring-honey/40 focus:border-honey/50 appearance-none cursor-pointer"
                            data-testid="filter-year-to"
                          >
                            <option value="">To</option>
                            {yearList.map(y => (
                              <option key={y} value={y} disabled={yearFrom !== null && y < yearFrom}>{y}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t border-stone-100">
                      {hasAnyFilter && (
                        <button
                          onClick={() => { clearAllFilters(); }}
                          className="text-[11px] text-stone-400 hover:text-stone-600 transition-colors"
                          data-testid="filter-clear-drawer"
                        >
                          Clear all
                        </button>
                      )}
                      <button
                        onClick={() => setFilterOpen(false)}
                        className="ml-auto text-[11px] font-semibold text-honey-amber hover:text-amber-600 px-3 py-1.5 rounded-full bg-honey/10 transition-colors"
                        data-testid="filter-apply"
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Scrollable active filter chips */}
              <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide min-w-0 flex-1 pr-2">
                {[...activeFilters].map(f => (
                  <button
                    key={`af-${f}`}
                    onClick={() => toggleFilter(f)}
                    className="shrink-0 flex items-center gap-1 text-[11px] font-medium pl-2.5 pr-1.5 py-1 rounded-full bg-stone-100 text-stone-600 border border-stone-200 hover:bg-stone-200 transition-all"
                    data-testid={`active-filter-${f.toLowerCase()}`}
                  >
                    {f}<X className="w-3 h-3 text-stone-400" />
                  </button>
                ))}
                {hasYearFilter && (
                  <button
                    onClick={() => { setYearFrom(null); setYearTo(null); }}
                    className="shrink-0 flex items-center gap-1 text-[11px] font-medium pl-2.5 pr-1.5 py-1 rounded-full bg-stone-100 text-stone-600 border border-stone-200 hover:bg-stone-200 transition-all"
                    data-testid="active-year-range"
                  >
                    {yearFrom && yearTo ? `${yearFrom}–${yearTo}` : yearFrom ? `${yearFrom}+` : `≤${yearTo}`}
                    <X className="w-3 h-3 text-stone-400" />
                  </button>
                )}
                {hasAnyFilter && (
                  <button
                    onClick={clearAllFilters}
                    className="shrink-0 text-[11px] text-stone-400 hover:text-stone-600 px-1.5 py-1 transition-colors"
                    data-testid="filter-clear-all"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="max-w-2xl mx-auto px-4 pt-3 pb-6">
        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-6">
            <Loader2 className="w-5 h-5 animate-spin text-honey-amber" />
          </div>
        )}

        {/* Search Results */}
        {!loading && hasResults && (
          <>
            {/* Variant Results (Priority) */}
            {filteredVariants.length > 0 && (
              <section className="mb-5" data-testid="search-variants">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="font-heading text-sm font-bold text-vinyl-black">Variants</h2>
                  <span className="text-xs text-muted-foreground">
                    {hasAnyFilter ? `${filteredVariants.length} of ${results.total}` : `${results.total} results`}
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-0.5">
                  {filteredVariants.map((v, i) => (
                    <VariantCard key={`${v.discogs_id}-${i}`} v={v} onOpen={handleOpenVariant} />
                  ))}
                </div>
                {results.has_more && !hasAnyFilter && (
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

            {/* No matches after filter */}
            {filteredVariants.length === 0 && hasAnyFilter && (
              <div className="text-center py-8" data-testid="no-filter-results">
                <SlidersHorizontal className="w-8 h-8 text-stone-300 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No variants match these filters</p>
                <button onClick={clearAllFilters} className="text-xs text-honey-amber hover:underline mt-1" data-testid="filter-clear-inline">Clear filters</button>
              </div>
            )}

            {/* Album Results */}
            {results.albums?.length > 0 && (
              <section className="mb-5" data-testid="search-albums">
                <h2 className="font-heading text-sm font-bold text-vinyl-black mb-2">Albums</h2>
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
              <section className="mb-5" data-testid="search-artists">
                <h2 className="font-heading text-sm font-bold text-vinyl-black mb-2">Artists</h2>
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

        {/* Collectors Section */}
        {!loading && userResults && userResults.length > 0 && (
          <section className="mb-8" data-testid="collector-results">
            <h3 className="text-xs uppercase tracking-wider text-stone-400 font-semibold mb-3 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5" /> Collectors
            </h3>
            <div className="space-y-2">
              {userResults.map(u => (
                <Link
                  key={u.id}
                  to={`/profile/${u.username}`}
                  className="flex items-center gap-3 p-3 rounded-xl bg-white/60 border border-stone-200/60 hover:border-honey/30 hover:bg-honey/5 transition-all group"
                  data-testid={`collector-${u.username}`}
                >
                  <div className="w-10 h-10 rounded-full bg-stone-200 overflow-hidden shrink-0">
                    {u.avatar_url ? (
                      <img src={u.avatar_url} alt={u.username} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-stone-400 text-sm font-medium">
                        {(u.username || '?')[0].toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-vinyl-black group-hover:text-honey-amber transition-colors truncate">
                      @{u.username}
                    </p>
                    <p className="text-xs text-stone-400">
                      {u.record_count.toLocaleString()} record{u.record_count !== 1 ? 's' : ''}
                      {u.records_in_common > 0 && (
                        <span className="ml-1.5 text-honey-amber font-medium">
                          · {u.records_in_common} in common
                        </span>
                      )}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-stone-300 group-hover:text-honey-amber transition-colors shrink-0" />
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* No Results */}
        {!loading && query.length >= 2 && !hasResults && results !== null && (
          <div className="text-center py-10" data-testid="no-results">
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
