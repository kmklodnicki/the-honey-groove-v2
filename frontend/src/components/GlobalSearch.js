import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Search, Plus, Clock, Trash2, UserPlus, Disc, Feather } from 'lucide-react';
import { toast } from 'sonner';
import AlbumArt from './AlbumArt';
import safeStorage from '../utils/safeStorage';

const TABS = [
  { key: 'records', label: 'Records' },
  { key: 'collectors', label: 'Collectors' },
  { key: 'posts', label: 'Posts' },
];

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

const GlobalSearch = ({ onClose, initialTab }) => {
  const { token, API } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState(initialTab || 'records');
  const [records, setRecords] = useState([]);
  const [collectors, setCollectors] = useState([]);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState(getRecent());
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const doSearch = useCallback(async (q) => {
    if (!q || q.length < 2) { setRecords([]); setCollectors([]); setPosts([]); return; }
    setLoading(true);
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [recResp, colResp, postResp] = await Promise.all([
        axios.get(`${API}/discogs/search?q=${encodeURIComponent(q)}`, { headers }).catch(() => ({ data: [] })),
        axios.get(`${API}/users/search?query=${encodeURIComponent(q)}`, { headers }).catch(() => ({ data: [] })),
        axios.get(`${API}/search/posts?q=${encodeURIComponent(q)}`, { headers }).catch(() => ({ data: [] })),
      ]);
      setRecords(recResp.data?.slice(0, 12) || []);
      setCollectors(colResp.data?.slice(0, 12) || []);
      setPosts(postResp.data?.slice(0, 12) || []);
      addRecent(q);
      setRecentSearches(getRecent());
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.length >= 2) {
      debounceRef.current = setTimeout(() => doSearch(query), 300);
    } else {
      setRecords([]); setCollectors([]); setPosts([]);
    }
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, doSearch]);

  const goToRecord = (r) => {
    if (r.discogs_id) navigate(`/record/${r.discogs_id}`);
    onClose?.();
  };
  const goToCollector = (u) => { navigate(`/profile/${u.username}`); onClose?.(); };
  const goToPost = (p) => { navigate('/hive'); onClose?.(); };

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
      await axios.post(`${API}/users/${u.id}/follow`, {}, { headers: { Authorization: `Bearer ${token}` } });
      toast.success(`following @${u.username}.`);
    } catch { toast.error('something went wrong.'); }
  };

  const currentResults = tab === 'records' ? records : tab === 'collectors' ? collectors : posts;
  const hasQuery = query.length >= 2;
  const noResults = hasQuery && !loading && currentResults.length === 0;

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
        <Button variant="ghost" size="sm" onClick={onClose} className="text-muted-foreground shrink-0" data-testid="search-close-btn">
          Cancel
        </Button>
      </div>

      {/* Tabs */}
      {hasQuery && (
        <div className="flex border-b border-honey/20 px-4" data-testid="search-tabs">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${tab === t.key ? 'border-amber-500 text-amber-700' : 'border-transparent text-muted-foreground hover:text-vinyl-black'}`}
              data-testid={`search-tab-${t.key}`}
            >
              {t.label}
              {t.key === 'records' && records.length > 0 && <span className="ml-1 text-xs opacity-60">({records.length})</span>}
              {t.key === 'collectors' && collectors.length > 0 && <span className="ml-1 text-xs opacity-60">({collectors.length})</span>}
              {t.key === 'posts' && posts.length > 0 && <span className="ml-1 text-xs opacity-60">({posts.length})</span>}
            </button>
          ))}
        </div>
      )}

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

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
            <span className="text-3xl block mb-3">🎵</span>
            <p className="italic text-muted-foreground" style={{ fontFamily: '"DM Serif Display", serif', color: '#8A6B4A' }}>
              nothing in the hive for that yet.
            </p>
          </div>
        )}

        {/* Records results */}
        {hasQuery && !loading && tab === 'records' && records.length > 0 && (
          <div className="space-y-1" data-testid="search-records-list">
            {records.map((r, i) => (
              <div key={r.discogs_id || i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-honey/10 cursor-pointer group" data-testid={`search-record-${i}`}>
                <div className="shrink-0 cursor-pointer" onClick={() => goToRecord(r)}>
                  {r.cover_url ? (
                    <AlbumArt src={r.cover_url} alt="" className="w-12 h-12 rounded-md object-cover shadow-sm" />
                  ) : (
                    <div className="w-12 h-12 rounded-md bg-stone-100 flex items-center justify-center"><Disc className="w-5 h-5 text-stone-400" /></div>
                  )}
                </div>
                <div className="flex-1 min-w-0 cursor-pointer" onClick={() => goToRecord(r)}>
                  <p className="text-sm font-medium truncate">{r.title}</p>
                  <p className="text-xs text-muted-foreground truncate">{r.artist} {r.year ? `(${r.year})` : ''} {r.format ? `· ${r.format}` : ''}</p>
                </div>
                <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button onClick={(e) => { e.stopPropagation(); addToCollection(r); }}
                    className="text-xs text-amber-600 hover:text-amber-800 px-2 py-1 rounded-full border border-amber-300 hover:bg-amber-50"
                    data-testid={`search-add-collection-${i}`}
                  >+ collection</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Collectors results */}
        {hasQuery && !loading && tab === 'collectors' && collectors.length > 0 && (
          <div className="space-y-1" data-testid="search-collectors-list">
            {collectors.map((u, i) => (
              <div key={u.id || i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-honey/10 cursor-pointer" onClick={() => goToCollector(u)} data-testid={`search-collector-${i}`}>
                <Avatar className="h-10 w-10 border border-honey/30">
                  <AvatarImage src={u.avatar_url} />
                  <AvatarFallback className="bg-honey-soft text-sm font-medium">{u.username?.[0]?.toUpperCase()}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">@{u.username}</p>
                  <p className="text-xs text-muted-foreground">{u.record_count || 0} records</p>
                </div>
                <button onClick={(e) => { e.stopPropagation(); followUser(u); }}
                  className="text-xs text-amber-600 hover:text-amber-800 px-3 py-1.5 rounded-full border border-amber-300 hover:bg-amber-50 flex items-center gap-1"
                  data-testid={`search-follow-${i}`}
                >
                  <UserPlus className="w-3 h-3" /> Follow
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Posts results */}
        {hasQuery && !loading && tab === 'posts' && posts.length > 0 && (
          <div className="space-y-1" data-testid="search-posts-list">
            {posts.map((p, i) => {
              const Icon = POST_ICONS[p.post_type] || Disc;
              return (
                <div key={p.id || i} className="flex items-start gap-3 p-2 rounded-lg hover:bg-honey/10 cursor-pointer" onClick={() => goToPost(p)} data-testid={`search-post-${i}`}>
                  <div className="mt-0.5 shrink-0">
                    <Icon className="w-4 h-4 text-amber-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      {p.post_type !== 'NOTE' && (
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
        )}
      </div>
    </div>
  );
};

export default GlobalSearch;
