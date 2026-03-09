import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Search, Clock, Trash2, UserPlus, Disc, Feather, ShoppingBag, Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import RecordSearchResult from './RecordSearchResult';
import { formatGradeDisplay } from '../utils/grading';
import safeStorage from '../utils/safeStorage';
import { resolveImageUrl } from '../utils/imageUrl';

const POST_ICONS = {
  NOW_SPINNING: Disc, ISO: Search, NEW_HAUL: Plus, NOTE: Feather,
};

const RECENT_KEY = 'hg_recent_searches';
const MAX_RECENT = 8;

function getRecent() {
  try { return JSON.parse(safeStorage.getItem(RECENT_KEY) || '[]').slice(0, MAX_RECENT); }
  catch { return []; }
}
function addRecent(q) {
  const list = getRecent().filter(s => s !== q);
  list.unshift(q);
  safeStorage.setItem(RECENT_KEY, JSON.stringify(list.slice(0, MAX_RECENT)));
}
function clearRecent() { safeStorage.removeItem(RECENT_KEY); }

const GlobalSearch = ({ onClose }) => {
  const { token, API } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({ records: [], collectors: [], posts: [], listings: [] });
  const [discogsResults, setDiscogsResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [discogsLoading, setDiscogsLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState(getRecent());
  const inputRef = useRef(null);
  const debounceRef = useRef(null);
  const abortRef = useRef(null);
  const discogsAbortRef = useRef(null);

  // Infinite scroll state for records
  const [paginatedRecords, setPaginatedRecords] = useState([]);
  const [recordsSkip, setRecordsSkip] = useState(0);
  const [recordsHasMore, setRecordsHasMore] = useState(false);
  const [recordsLoadingMore, setRecordsLoadingMore] = useState(false);
  const scrollRef = useRef(null);
  const recordsSentinelRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (abortRef.current) abortRef.current.abort();
      if (discogsAbortRef.current) discogsAbortRef.current.abort();
    };
  }, []);

  const doSearch = useCallback(async (q) => {
    if (!q || q.length < 2) {
      setResults({ records: [], collectors: [], posts: [], listings: [] });
      setDiscogsResults([]);
      setPaginatedRecords([]);
      setRecordsSkip(0);
      setRecordsHasMore(false);
      setLoading(false);
      setDiscogsLoading(false);
      return;
    }

    // Cancel any in-flight requests
    if (abortRef.current) abortRef.current.abort();
    if (discogsAbortRef.current) discogsAbortRef.current.abort();

    const localController = new AbortController();
    const discogsController = new AbortController();
    abortRef.current = localController;
    discogsAbortRef.current = discogsController;

    const headers = { Authorization: `Bearer ${token}` };

    // Fast local search (collectors, posts, listings) + paginated records
    setLoading(true);
    setPaginatedRecords([]);
    setRecordsSkip(0);
    try {
      const [unifiedResp, recordsResp] = await Promise.all([
        axios.get(`${API}/search/unified?q=${encodeURIComponent(q)}`, {
          headers, timeout: 5000, signal: localController.signal,
        }),
        axios.get(`${API}/search/records?q=${encodeURIComponent(q)}&skip=0&limit=20`, {
          headers, timeout: 5000, signal: localController.signal,
        }),
      ]);
      setResults(unifiedResp.data);
      // Use discogs_fallback from unified search if local results were few
      const fallback = unifiedResp.data.discogs_fallback || [];
      if (fallback.length > 0) {
        setDiscogsResults(fallback);
      }
      setPaginatedRecords(recordsResp.data.records || []);
      setRecordsHasMore(recordsResp.data.has_more || false);
      setRecordsSkip(20);
      addRecent(q);
      setRecentSearches(getRecent());
    } catch (e) {
      if (!axios.isCancel(e)) {
        setResults({ records: [], collectors: [], posts: [], listings: [] });
        setPaginatedRecords([]);
      }
    } finally {
      if (!localController.signal.aborted) setLoading(false);
    }

    // Slower Discogs external search (non-blocking)
    setDiscogsLoading(true);
    try {
      const resp = await axios.get(`${API}/search/discogs?q=${encodeURIComponent(q)}`, {
        headers, timeout: 8000, signal: discogsController.signal,
      });
      setDiscogsResults(resp.data?.slice(0, 8) || []);
    } catch (e) {
      if (!axios.isCancel(e)) setDiscogsResults([]);
    } finally {
      if (!discogsController.signal.aborted) setDiscogsLoading(false);
    }
  }, [API, token]);

  const loadMoreRecords = useCallback(async () => {
    if (recordsLoadingMore || !recordsHasMore || query.length < 2) return;
    setRecordsLoadingMore(true);
    try {
      const resp = await axios.get(`${API}/search/records?q=${encodeURIComponent(query)}&skip=${recordsSkip}&limit=20`, {
        headers: { Authorization: `Bearer ${token}` }, timeout: 5000,
      });
      const newRecords = resp.data.records || [];
      setPaginatedRecords(prev => [...prev, ...newRecords]);
      setRecordsHasMore(resp.data.has_more || false);
      setRecordsSkip(prev => prev + 20);
    } catch { /* silent */ }
    finally { setRecordsLoadingMore(false); }
  }, [API, token, query, recordsSkip, recordsHasMore, recordsLoadingMore]);

  // Debounced search trigger — input state updates instantly, search fires after 300ms pause
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.length >= 2) {
      setLoading(true); // show spinner immediately
      debounceRef.current = setTimeout(() => doSearch(query), 300);
    } else {
      setResults({ records: [], collectors: [], posts: [], listings: [] });
      setDiscogsResults([]);
      setLoading(false);
      setDiscogsLoading(false);
    }
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, doSearch]);

  const goToRecord = (r) => { if (r.discogs_id) navigate(`/record/${r.discogs_id}`); onClose?.(); };
  const goToCollector = (u) => { navigate(`/profile/${u.username}`); onClose?.(); };
  const goToPost = () => { navigate('/hive'); onClose?.(); };
  const goToListing = (l) => { navigate(`/honeypot?listing=${l.id}`); onClose?.(); };

  const addToCollection = async (r) => {
    try {
      await axios.post(`${API}/records`, {
        title: r.title, artist: r.artist, cover_url: r.cover_url,
        discogs_id: r.discogs_id, year: r.year, format: r.format,
      }, { headers: { Authorization: `Bearer ${token}` }, timeout: 15000 });
      toast.success('added to collection.');
    } catch (e) { toast.error(e.response?.data?.detail || "couldn't add that record. please try again."); }
  };

  const followUser = async (u) => {
    try {
      await axios.post(`${API}/follow/${u.username}`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setResults(prev => ({
        ...prev,
        collectors: prev.collectors.map(c => c.id === u.id ? { ...c, is_following: true } : c),
      }));
      toast.success(`following @${u.username}.`);
    } catch { toast.error('something went wrong.'); }
  };

  const hasQuery = query.length >= 2;
  const { collectors, posts, listings } = results;

  // Merge paginated records + discogs (deduped by discogs_id)
  const seenIds = new Set(paginatedRecords.map(r => r.discogs_id).filter(Boolean));
  const extraDiscogs = discogsResults.filter(r => r.discogs_id && !seenIds.has(r.discogs_id));
  const allRecords = [...paginatedRecords, ...extraDiscogs.map(r => ({ ...r, source: 'discogs' }))];

  // Group records by artist with sticky headers
  const groupedByArtist = React.useMemo(() => {
    const groups = [];
    const artistMap = new Map();
    for (const r of allRecords) {
      const artist = r.artist || 'Unknown Artist';
      if (!artistMap.has(artist)) {
        const group = { artist, records: [] };
        artistMap.set(artist, group);
        groups.push(group);
      }
      artistMap.get(artist).records.push(r);
    }
    return groups;
  }, [allRecords]);

  const totalResults = allRecords.length + collectors.length + posts.length + listings.length;
  const noResults = hasQuery && !loading && !discogsLoading && totalResults === 0;

  // IntersectionObserver for infinite scroll
  useEffect(() => {
    const sentinel = recordsSentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) loadMoreRecords(); },
      { root: scrollRef.current, rootMargin: '200px' }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMoreRecords]);

  return (
    <div className="flex flex-col h-full" data-testid="global-search">
      {/* Search input */}
      <div className="flex items-center gap-2 p-4 border-b border-honey/20">
        <Search className="w-5 h-5 text-muted-foreground shrink-0" />
        <Input
          ref={inputRef}
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="search records, collectors, posts..."
          className="border-0 shadow-none focus-visible:ring-0 text-base"
          data-testid="global-search-input"
        />
        {loading && <Loader2 className="w-4 h-4 animate-spin text-amber-400 shrink-0" data-testid="search-spinner" />}
        <Button variant="ghost" size="sm" onClick={onClose} className="text-muted-foreground shrink-0" data-testid="search-close-btn">
          Cancel
        </Button>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-4" ref={scrollRef}>
        {/* Recent searches (before typing) */}
        {!hasQuery && !loading && (
          <div>
            {recentSearches.length > 0 && (
              <>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Recent</span>
                  <button onClick={() => { clearRecent(); setRecentSearches([]); }} className="text-xs text-muted-foreground hover:text-amber-600 flex items-center gap-1" data-testid="clear-recent-btn">
                    <Trash2 className="w-3 h-3" /> clear all
                  </button>
                </div>
                <div className="space-y-1">
                  {recentSearches.map((s, i) => (
                    <button key={i} onClick={() => setQuery(s)}
                      className="flex items-center gap-2.5 w-full text-left px-3 py-2 rounded-lg hover:bg-honey/10 transition-colors"
                      data-testid={`recent-search-${i}`}
                    >
                      <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                      <span className="text-sm">{s}</span>
                    </button>
                  ))}
                </div>
              </>
            )}
            {recentSearches.length === 0 && (
              <p className="text-center text-sm text-muted-foreground italic py-8" style={{ fontFamily: '"DM Serif Display", serif' }}>
                search by artist, album, username, or keyword
              </p>
            )}
          </div>
        )}

        {/* No results */}
        {noResults && (
          <div className="text-center py-12" data-testid="search-empty-state">
            <p className="text-sm text-muted-foreground" style={{ color: '#8A6B4A' }}>
              no results for "{query}" 🐝
            </p>
          </div>
        )}

        {/* Unified results grouped by section */}
        {hasQuery && !noResults && (totalResults > 0 || loading || discogsLoading) && (
          <div className="space-y-6">
            {/* Records Section - grouped by artist, infinite scroll */}
            {allRecords.length > 0 && (
              <section data-testid="search-records-section">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Disc className="w-3.5 h-3.5" /> Records
                  <span className="text-[10px] opacity-60">({allRecords.length}{recordsHasMore ? '+' : ''})</span>
                  {discogsLoading && <Loader2 className="w-3 h-3 animate-spin ml-1" />}
                </h3>
                <div className="space-y-0.5">
                  {groupedByArtist.map(group => (
                    <div key={group.artist}>
                      <div className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm px-2 py-1 -mx-1 border-b border-honey/10">
                        <span className="text-[11px] font-semibold text-honey-amber tracking-wide">{group.artist}</span>
                      </div>
                      {group.records.map((r, i) => (
                        <RecordSearchResult
                          key={r.discogs_id || `${r.title}-${i}`}
                          record={r}
                          onClick={() => goToRecord(r)}
                          testId={`search-record-${r.discogs_id || i}`}
                          actions={
                            <button onClick={(e) => { e.stopPropagation(); addToCollection(r); }}
                              className="text-xs text-amber-600 hover:text-amber-800 px-2 py-1 rounded-full border border-amber-300 hover:bg-amber-50 opacity-0 group-hover:opacity-100 transition-opacity"
                              data-testid={`search-add-collection-${r.discogs_id || i}`}
                            >+ collection</button>
                          }
                        />
                      ))}
                    </div>
                  ))}
                  {/* Infinite scroll sentinel */}
                  <div ref={recordsSentinelRef} className="py-2 text-center">
                    {recordsLoadingMore && <Loader2 className="w-4 h-4 animate-spin mx-auto text-honey" />}
                    {!recordsHasMore && allRecords.length > 20 && (
                      <p className="text-[10px] text-muted-foreground italic">end of results</p>
                    )}
                  </div>
                </div>
              </section>
            )}

            {/* Collectors Section */}
            {collectors.length > 0 && (
              <section data-testid="search-collectors-section">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <UserPlus className="w-3.5 h-3.5" /> Collectors
                  <span className="text-[10px] opacity-60">({collectors.length})</span>
                </h3>
                <div className="space-y-0.5">
                  {collectors.map((u, i) => (
                    <div key={u.id || i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-honey/10 cursor-pointer" onClick={() => goToCollector(u)} data-testid={`search-collector-${i}`}>
                      <Avatar className="h-10 w-10 border border-honey/30">
                        <AvatarImage src={resolveImageUrl(u.avatar_url)} />
                        <AvatarFallback className="bg-honey-soft text-sm font-medium">{u.username?.[0]?.toUpperCase()}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">@{u.username}</p>
                        <p className="text-xs text-muted-foreground">{u.record_count || 0} records</p>
                      </div>
                      {u.is_following ? (
                        <span className="text-xs text-muted-foreground px-3 py-1.5 rounded-full border border-stone-200 bg-stone-50" data-testid={`search-following-${i}`}>
                          Following
                        </span>
                      ) : (
                        <button onClick={(e) => { e.stopPropagation(); followUser(u); }}
                          className="text-xs text-amber-600 hover:text-amber-800 px-3 py-1.5 rounded-full border border-amber-300 hover:bg-amber-50 flex items-center gap-1"
                          data-testid={`search-follow-${i}`}
                        >
                          <UserPlus className="w-3 h-3" /> Follow
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Listings Section */}
            {listings.length > 0 && (
              <section data-testid="search-listings-section">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <ShoppingBag className="w-3.5 h-3.5" /> Honeypot Listings
                  <span className="text-[10px] opacity-60">({listings.length})</span>
                </h3>
                <div className="space-y-0.5">
                  {listings.map((l, i) => (
                    <div key={l.id || i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-honey/10 cursor-pointer" onClick={() => goToListing(l)} data-testid={`search-listing-${i}`}>
                      <div className="shrink-0">
                        {l.cover_url ? (
                          <img src={resolveImageUrl(l.cover_url)} alt="" className="w-11 h-11 rounded-md object-cover shadow-sm" />
                        ) : (
                          <div className="w-11 h-11 rounded-md bg-stone-100 flex items-center justify-center"><ShoppingBag className="w-5 h-5 text-stone-400" /></div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{l.album}</p>
                        <p className="text-xs text-muted-foreground truncate">{l.artist}</p>
                      </div>
                      <div className="text-right shrink-0">
                        {l.price && <p className="text-sm font-semibold" style={{ color: '#C8861A' }}>${l.price}</p>}
                        {l.condition && <p className="text-[10px] text-muted-foreground">{formatGradeDisplay(l.condition)}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Posts Section */}
            {posts.length > 0 && (
              <section data-testid="search-posts-section">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Feather className="w-3.5 h-3.5" /> Posts
                  <span className="text-[10px] opacity-60">({posts.length})</span>
                </h3>
                <div className="space-y-0.5">
                  {posts.map((p, i) => {
                    const Icon = POST_ICONS[p.post_type] || Disc;
                    return (
                      <div key={p.id || i} className="flex items-start gap-3 p-2 rounded-lg hover:bg-honey/10 cursor-pointer" onClick={goToPost} data-testid={`search-post-${i}`}>
                        <div className="mt-0.5 shrink-0">
                          <Icon className="w-4 h-4 text-amber-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            {p.post_type !== 'NOTE' && p.post_type && (
                              <span className="text-[10px] font-medium text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">{p.post_type?.replace('_', ' ')}</span>
                            )}
                            <span className="text-xs text-muted-foreground">@{p.user?.username}</span>
                          </div>
                          <p className="text-sm truncate">{p.caption}</p>
                          <p className="text-[10px] text-muted-foreground mt-0.5">
                            {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GlobalSearch;
