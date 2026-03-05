import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Disc, Users, Search, TrendingUp, Lock, ShoppingBag, Play, UserPlus, MessageCircle } from 'lucide-react';
import { UserRow } from '../components/FollowList';
import { formatDistanceToNow } from 'date-fns';

const ExplorePage = () => {
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [trending, setTrending] = useState([]);
  const [isoMatches, setIsoMatches] = useState([]);
  const [recentHauls, setRecentHauls] = useState([]);
  const [suggested, setSuggested] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    if (!token) { setLoading(false); return; }
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [trendRes, isoRes, haulRes, sugRes] = await Promise.all([
        axios.get(`${API}/explore/trending?limit=12`, { headers }),
        axios.get(`${API}/explore/active-isos`, { headers }),
        axios.get(`${API}/explore/recent-hauls?limit=8`, { headers }),
        axios.get(`${API}/explore/suggested-collectors?limit=8`, { headers }),
      ]);
      setTrending(trendRes.data);
      setIsoMatches(isoRes.data);
      setRecentHauls(haulRes.data);
      setSuggested(sugRes.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (!query.trim() || query.length < 2) { setSearchResults([]); return; }
    if (!token) return;
    setSearching(true);
    try {
      const resp = await axios.get(`${API}/users/search?query=${encodeURIComponent(query)}`, { headers: { Authorization: `Bearer ${token}` } });
      setSearchResults(resp.data);
    } catch { setSearchResults([]); }
    finally { setSearching(false); }
  };

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-24">
        <h1 className="font-heading text-3xl text-vinyl-black mb-6">Explore</h1>
        <div className="relative">
          <div className="blur-md pointer-events-none">
            {[1, 2, 3].map(i => (
              <Card key={i} className="mb-4 p-6 border-honey/30">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-full bg-honey/30" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-32 bg-honey/20 rounded" />
                    <div className="h-20 w-full bg-honey/10 rounded-lg" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Card className="p-8 text-center shadow-lg border-honey/30 bg-white/95">
              <Lock className="w-10 h-10 text-honey mx-auto mb-3" />
              <h3 className="font-heading text-xl mb-2">Join The Hive</h3>
              <p className="text-muted-foreground text-sm mb-4">Sign in to explore the vinyl community</p>
              <div className="flex gap-3 justify-center">
                <Link to="/login"><Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full">Log In</Button></Link>
                <Link to="/signup"><Button variant="outline" className="rounded-full">Sign Up</Button></Link>
              </div>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-24">
        <Skeleton className="h-8 w-40 mb-6" />
        <Skeleton className="h-6 w-32 mb-3" />
        <div className="flex gap-3 overflow-hidden mb-8">{[1,2,3,4].map(i => <Skeleton key={i} className="h-48 w-36 rounded-xl shrink-0" />)}</div>
        <Skeleton className="h-6 w-32 mb-3" />
        <div className="grid grid-cols-2 gap-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8" data-testid="explore-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-1">Explore</h1>
      <p className="text-sm text-muted-foreground mb-6">discover what the community is into.</p>

      {/* Search */}
      <div className="relative mb-8">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search collectors..." value={searchQuery} onChange={e => handleSearch(e.target.value)} className="pl-9 border-honey/50 rounded-full" data-testid="explore-search" />
      </div>

      {searchQuery.trim().length >= 2 && (
        <div className="mb-8">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">Search Results</h3>
          {searching ? <Skeleton className="h-16 w-full" /> : searchResults.length === 0 ? (
            <p className="text-sm text-muted-foreground">No collectors found for "{searchQuery}"</p>
          ) : (
            <Card className="border-honey/30 divide-y divide-honey/10 px-4">
              {searchResults.map(u => <UserRow key={u.id} u={u} currentUserId={user?.id} token={token} API={API} onFollowChange={fetchData} />)}
            </Card>
          )}
        </div>
      )}

      {!searchQuery && (
        <>
          {/* Trending Records */}
          {trending.length > 0 && (
            <section className="mb-8" data-testid="trending-section">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-honey-amber" />
                <h2 className="font-heading text-lg text-vinyl-black">Trending Records</h2>
              </div>
              <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
                {trending.map(r => (
                  <div key={r.id} className="flex-shrink-0 w-36" data-testid={`trending-${r.id}`}>
                    <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm">
                      {r.cover_url ? <img src={r.cover_url} alt="" className="w-full h-full object-cover" />
                        : <div className="w-full h-full flex items-center justify-center"><Disc className="w-10 h-10 text-honey" /></div>}
                    </div>
                    <p className="text-sm font-medium truncate">{r.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
                    <div className="flex items-center gap-1 mt-0.5">
                      <Play className="w-3 h-3 text-honey-amber" />
                      <span className="text-xs text-honey-amber font-medium">{r.trending_spins} {r.trending_spins === 1 ? 'spin' : 'spins'} this week</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ISO Matches */}
          {isoMatches.length > 0 && (
            <section className="mb-8" data-testid="iso-matches-section">
              <div className="flex items-center gap-2 mb-3">
                <Search className="w-4 h-4 text-purple-600" />
                <h2 className="font-heading text-lg text-vinyl-black">Wantlist Matches</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {isoMatches.map((m, idx) => (
                  <Card key={`${m.id}-${idx}`} className="p-3 border-purple-200 bg-purple-50/50 hover:shadow-md transition-all" data-testid={`iso-match-${m.id}`}>
                    <div className="flex items-center gap-3">
                      {m.cover_url ? <img src={m.cover_url} alt="" className="w-12 h-12 rounded-lg object-cover" />
                        : <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center"><Disc className="w-5 h-5 text-purple-400" /></div>}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{m.album}</p>
                        <p className="text-xs text-muted-foreground truncate">{m.artist}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${m.listing_type === 'TRADE' ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'}`}>
                            {m.listing_type === 'TRADE' ? 'Trade' : `$${m.price}`}
                          </span>
                          {m.user && <Link to={`/profile/${m.user.username}`} className="text-[10px] text-purple-600 hover:underline">@{m.user.username}</Link>}
                        </div>
                      </div>
                      <Button size="sm" className="bg-purple-100 text-purple-700 hover:bg-purple-200 rounded-full text-xs shrink-0"
                        onClick={() => navigate('/honeypot')} data-testid={`view-match-${m.id}`}>View</Button>
                    </div>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Recent Hauls */}
          {recentHauls.length > 0 && (
            <section className="mb-8" data-testid="recent-hauls-section">
              <div className="flex items-center gap-2 mb-3">
                <ShoppingBag className="w-4 h-4 text-honey-amber" />
                <h2 className="font-heading text-lg text-vinyl-black">Recent Hauls</h2>
              </div>
              <div className="space-y-3">
                {recentHauls.map(post => (
                  <Card key={post.id} className="p-4 border-honey/30 hover:shadow-sm transition-all" data-testid={`haul-${post.id}`}>
                    <div className="flex items-start gap-3">
                      <Link to={`/profile/${post.user?.username}`}>
                        {post.user?.avatar_url ? (
                          <img src={post.user.avatar_url} alt="" className="w-9 h-9 rounded-full object-cover" />
                        ) : (
                          <div className="w-9 h-9 rounded-full bg-honey/30 flex items-center justify-center text-sm font-bold text-honey-amber">
                            {(post.user?.username || '?')[0].toUpperCase()}
                          </div>
                        )}
                      </Link>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Link to={`/profile/${post.user?.username}`} className="text-sm font-medium hover:underline">@{post.user?.username}</Link>
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-700">New Haul</span>
                          <span className="text-[10px] text-muted-foreground ml-auto">{formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}</span>
                        </div>
                        {post.caption && <p className="text-sm text-vinyl-black/80 mb-1">{post.caption}</p>}
                        {post.haul?.items && (
                          <div className="flex gap-2 overflow-x-auto">
                            {post.haul.items.slice(0, 4).map((item, i) => (
                              <div key={i} className="flex items-center gap-1.5 bg-honey/10 rounded-lg px-2 py-1 shrink-0">
                                {item.cover_url ? <img src={item.cover_url} alt="" className="w-6 h-6 rounded object-cover" />
                                  : <Disc className="w-4 h-4 text-honey" />}
                                <span className="text-xs font-medium truncate max-w-[100px]">{item.title}</span>
                              </div>
                            ))}
                            {post.haul.items.length > 4 && <span className="text-xs text-muted-foreground self-center">+{post.haul.items.length - 4} more</span>}
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Suggested Collectors */}
          {suggested.length > 0 && (
            <section className="mb-8" data-testid="suggested-section">
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-4 h-4 text-honey-amber" />
                <h2 className="font-heading text-lg text-vinyl-black">Collectors You Might Like</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {suggested.map(u => (
                  <Card key={u.id} className="p-4 border-honey/30 hover:shadow-sm transition-all" data-testid={`suggested-${u.id}`}>
                    <div className="flex items-center gap-3">
                      <Link to={`/profile/${u.username}`}>
                        {u.avatar_url ? (
                          <img src={u.avatar_url} alt="" className="w-11 h-11 rounded-full object-cover" />
                        ) : (
                          <div className="w-11 h-11 rounded-full bg-honey/30 flex items-center justify-center text-base font-bold text-honey-amber">
                            {(u.username || '?')[0].toUpperCase()}
                          </div>
                        )}
                      </Link>
                      <div className="flex-1 min-w-0">
                        <Link to={`/profile/${u.username}`} className="text-sm font-medium hover:underline">@{u.username}</Link>
                        {u.shared_artists > 0 && (
                          <p className="text-xs text-muted-foreground">{u.shared_artists} artists in common</p>
                        )}
                        <p className="text-xs text-muted-foreground">{u.collection_count || 0} records</p>
                      </div>
                      <div className="flex gap-1.5 shrink-0">
                        <Button size="sm" variant="ghost" className="h-8 w-8 p-0 rounded-full" onClick={() => navigate(`/messages?to=${u.id}`)} data-testid={`dm-${u.id}`}>
                          <MessageCircle className="w-4 h-4" />
                        </Button>
                        <Button size="sm" className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs h-8 px-3" onClick={() => navigate(`/profile/${u.username}`)} data-testid={`view-profile-${u.id}`}>
                          <UserPlus className="w-3 h-3 mr-1" /> Follow
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Empty state */}
          {trending.length === 0 && isoMatches.length === 0 && recentHauls.length === 0 && suggested.length === 0 && (
            <Card className="p-8 text-center border-honey/30">
              <Disc className="w-12 h-12 text-honey mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">The community is just getting started</h3>
              <p className="text-muted-foreground text-sm">Add records, spin vinyl, and post hauls to populate Explore.</p>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default ExplorePage;
