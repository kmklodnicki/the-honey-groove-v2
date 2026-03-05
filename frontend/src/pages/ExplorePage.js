import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import { Disc, Users, Search, TrendingUp, Lock, ShoppingBag, Play, UserPlus, MessageCircle, MapPin, Heart, Plus, X } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';

const ExplorePage = () => {
  usePageTitle('Explore');
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [trending, setTrending] = useState([]);
  const [suggested, setSuggested] = useState([]);
  const [freshPressings, setFreshPressings] = useState([]);
  const [mostWanted, setMostWanted] = useState([]);
  const [nearYou, setNearYou] = useState({ collectors: [], listings: [], needs_location: true });
  const [loading, setLoading] = useState(true);

  // Trending modal
  const [trendingModal, setTrendingModal] = useState(null); // { record, posts }
  const [modalLoading, setModalLoading] = useState(false);

  // Location prompt
  const [showLocationPrompt, setShowLocationPrompt] = useState(false);
  const [cityInput, setCityInput] = useState('');
  const [regionInput, setRegionInput] = useState('');

  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = useCallback(async () => {
    if (!token) { setLoading(false); return; }
    try {
      const [trendRes, sugRes, fpRes, mwRes, nyRes] = await Promise.all([
        axios.get(`${API}/explore/trending?limit=10`, { headers }),
        axios.get(`${API}/explore/suggested-collectors?limit=8`, { headers }),
        axios.get(`${API}/explore/fresh-pressings?limit=12`, { headers }),
        axios.get(`${API}/explore/most-wanted?limit=20`, { headers }),
        axios.get(`${API}/explore/near-you`, { headers }),
      ]);
      setTrending(trendRes.data);
      setSuggested(sugRes.data);
      setFreshPressings(fpRes.data);
      setMostWanted(mwRes.data);
      setNearYou(nyRes.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const openTrendingModal = async (record) => {
    setModalLoading(true);
    setTrendingModal({ record, posts: [] });
    try {
      const resp = await axios.get(`${API}/explore/trending/${record.id}/posts`, { headers });
      setTrendingModal({ record: resp.data.record, posts: resp.data.posts });
    } catch { toast.error('Failed to load posts'); }
    finally { setModalLoading(false); }
  };

  const addToWantlist = async (artist, album, discogs_id, cover_url, year) => {
    try {
      await axios.post(`${API}/composer/iso`, {
        artist, album, discogs_id, cover_url, year,
      }, { headers });
      toast.success(`Added to your Wantlist!`);
    } catch (err) {
      if (err.response?.status === 409) toast.info('Already on your Wantlist');
      else toast.error('Failed to add');
    }
  };

  const saveLocation = async () => {
    if (!cityInput.trim()) { toast.error('City is required'); return; }
    try {
      await axios.put(`${API}/auth/me`, { city: cityInput.trim(), region: regionInput.trim() }, { headers });
      toast.success('Location saved!');
      setShowLocationPrompt(false);
      fetchData();
    } catch { toast.error('Failed to save location'); }
  };

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-24">
        <h1 className="font-heading text-3xl text-vinyl-black mb-6">Explore</h1>
        <div className="relative">
          <div className="blur-md pointer-events-none">
            {[1, 2, 3].map(i => <Card key={i} className="mb-4 p-6 border-honey/30"><div className="flex gap-4"><div className="w-12 h-12 rounded-full bg-honey/30" /><div className="flex-1 space-y-2"><div className="h-4 w-32 bg-honey/20 rounded" /><div className="h-20 w-full bg-honey/10 rounded-lg" /></div></div></Card>)}
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
        <Skeleton className="h-6 w-48 mb-3" />
        <div className="flex gap-3 overflow-hidden mb-8">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-48 w-36 rounded-xl shrink-0" />)}</div>
        <Skeleton className="h-6 w-32 mb-3" />
        <div className="grid grid-cols-2 gap-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8" data-testid="explore-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-1">Explore</h1>
      <p className="text-sm text-muted-foreground mb-8">discover what the community is into.</p>

      {/* 1. Trending in the Hive */}
      <ExploreSection icon={<TrendingUp className="w-4 h-4 text-honey-amber" />} title="Trending in the Hive" testId="trending-section" seeAllTo="/explore/trending">
        {trending.length === 0 ? (
          <EmptyCard text="No trending records yet. Start spinning!" />
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
            {trending.map(r => (
              <button key={r.id} onClick={() => openTrendingModal(r)}
                className="flex-shrink-0 w-36 text-left group" data-testid={`trending-${r.id}`}>
                <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm group-hover:shadow-md transition-shadow">
                  {r.cover_url ? <img src={r.cover_url} alt="" className="w-full h-full object-cover" />
                    : <div className="w-full h-full flex items-center justify-center"><Disc className="w-10 h-10 text-honey" /></div>}
                </div>
                <p className="text-sm font-medium truncate">{r.title}</p>
                <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <Play className="w-3 h-3 text-honey-amber" />
                  <span className="text-xs text-honey-amber font-medium">{r.trending_spins} {r.trending_spins === 1 ? 'spin' : 'spins'}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </ExploreSection>

      {/* 2. Taste Match */}
      <ExploreSection icon={<Users className="w-4 h-4 text-honey-amber" />} title="Taste Match" testId="taste-match-section" seeAllTo="/explore/taste-match">
        {suggested.length === 0 ? (
          <EmptyCard text="Add more records to your collection to find taste matches." />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {suggested.map(u => (
              <Card key={u.id} className="p-4 border-honey/30 hover:shadow-sm transition-all" data-testid={`taste-match-${u.id}`}>
                <div className="flex items-center gap-3">
                  <Link to={`/profile/${u.username}`}>
                    {u.avatar_url ? <img src={u.avatar_url} alt="" className="w-11 h-11 rounded-full object-cover" />
                      : <div className="w-11 h-11 rounded-full bg-honey/30 flex items-center justify-center text-base font-bold text-honey-amber">{(u.username || '?')[0].toUpperCase()}</div>}
                  </Link>
                  <div className="flex-1 min-w-0">
                    <Link to={`/profile/${u.username}`} className="text-sm font-medium hover:underline">@{u.username}</Link>
                    <p className="text-xs text-honey-amber font-medium">{u.shared_artists} records in common</p>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    <Button size="sm" variant="ghost" className="h-8 w-8 p-0 rounded-full" onClick={() => navigate(`/messages?to=${u.id}`)}><MessageCircle className="w-4 h-4" /></Button>
                    <Button size="sm" className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs h-8 px-3" onClick={() => navigate(`/profile/${u.username}`)}>
                      <UserPlus className="w-3 h-3 mr-1" /> Follow
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </ExploreSection>

      {/* 3. Fresh Pressings */}
      <ExploreSection icon={<Disc className="w-4 h-4 text-honey-amber" />} title="Fresh Pressings" testId="fresh-pressings-section" seeAllTo="/explore/fresh-pressings">
        {freshPressings.length === 0 ? (
          <EmptyCard text="No fresh pressings found right now." />
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
            {freshPressings.map((r, idx) => (
              <div key={r.discogs_id || idx} className="flex-shrink-0 w-40" data-testid={`fresh-pressing-${r.discogs_id || idx}`}>
                <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm relative group">
                  {r.cover_url ? <img src={r.cover_url} alt="" className="w-full h-full object-cover" />
                    : <div className="w-full h-full flex items-center justify-center"><Disc className="w-10 h-10 text-honey" /></div>}
                  <button
                    onClick={() => addToWantlist(r.artist, r.title, r.discogs_id, r.cover_url, r.year)}
                    className="absolute bottom-2 right-2 bg-white/90 hover:bg-white rounded-full p-1.5 shadow opacity-0 group-hover:opacity-100 transition-opacity"
                    data-testid={`add-wantlist-${r.discogs_id || idx}`}>
                    <Plus className="w-4 h-4 text-purple-600" />
                  </button>
                </div>
                <p className="text-sm font-medium truncate">{r.title}</p>
                <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
                {r.label && r.label.length > 0 && <p className="text-[10px] text-muted-foreground truncate">{r.label[0]}</p>}
              </div>
            ))}
          </div>
        )}
      </ExploreSection>

      {/* 4. Most Wanted */}
      <ExploreSection icon={<Heart className="w-4 h-4 text-red-400" />} title="Most Wanted" testId="most-wanted-section" seeAllTo="/explore/most-wanted">
        {mostWanted.length === 0 ? (
          <EmptyCard text="No wantlist data yet. Add records to your Wantlist!" />
        ) : (
          <div className="space-y-2">
            {mostWanted.map((r, idx) => (
              <div key={`${r.artist}-${r.album}`} className="flex items-center gap-3 py-2 px-1 rounded-lg hover:bg-honey/5 transition-colors" data-testid={`most-wanted-${idx}`}>
                <span className="text-sm font-heading text-honey-amber w-6 text-right shrink-0">{idx + 1}</span>
                {r.cover_url ? <img src={r.cover_url} alt="" className="w-10 h-10 rounded-lg object-cover" />
                  : <div className="w-10 h-10 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-5 h-5 text-honey" /></div>}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{r.album}</p>
                  <p className="text-xs text-muted-foreground truncate">{r.artist}{r.year ? ` (${r.year})` : ''}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-red-500 font-medium">{r.want_count} {r.want_count === 1 ? 'want' : 'wants'}</span>
                  <button onClick={() => addToWantlist(r.artist, r.album, r.discogs_id, r.cover_url, r.year)}
                    className="text-purple-600 hover:bg-purple-50 rounded-full p-1" data-testid={`want-${idx}`}>
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </ExploreSection>

      {/* 5. Near You */}
      <ExploreSection icon={<MapPin className="w-4 h-4 text-honey-amber" />} title="Near You" testId="near-you-section" seeAllTo="/explore/near-you">
        {nearYou.needs_location ? (
          <Card className="p-6 text-center border-honey/30">
            <MapPin className="w-10 h-10 text-honey/40 mx-auto mb-3" />
            <h3 className="font-heading text-lg mb-1">Set your location</h3>
            <p className="text-muted-foreground text-sm mb-4">Add your city to discover collectors and listings near you.</p>
            <Button onClick={() => setShowLocationPrompt(true)} className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="set-location-btn">
              <MapPin className="w-4 h-4 mr-1" /> Set Location
            </Button>
          </Card>
        ) : nearYou.collectors.length === 0 ? (
          <EmptyCard text="No collectors found in your area yet. Spread the word!" />
        ) : (
          <div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              {nearYou.collectors.map(u => (
                <Card key={u.id} className="p-3 border-honey/30 hover:shadow-sm transition-all" data-testid={`nearby-${u.id}`}>
                  <div className="flex items-center gap-3">
                    <Link to={`/profile/${u.username}`}>
                      {u.avatar_url ? <img src={u.avatar_url} alt="" className="w-10 h-10 rounded-full object-cover" />
                        : <div className="w-10 h-10 rounded-full bg-honey/30 flex items-center justify-center text-sm font-bold text-honey-amber">{(u.username || '?')[0].toUpperCase()}</div>}
                    </Link>
                    <div className="flex-1 min-w-0">
                      <Link to={`/profile/${u.username}`} className="text-sm font-medium hover:underline">@{u.username}</Link>
                      <p className="text-[10px] text-muted-foreground">{u.city}{u.region ? `, ${u.region}` : ''}</p>
                      <p className="text-[10px] text-muted-foreground">{u.collection_count} records{u.active_listings > 0 ? ` · ${u.active_listings} listings` : ''}</p>
                    </div>
                    <Button size="sm" variant="ghost" className="h-8 w-8 p-0 rounded-full shrink-0" onClick={() => navigate(`/messages?to=${u.id}`)}>
                      <MessageCircle className="w-4 h-4" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
            {nearYou.listings.length > 0 && (
              <>
                <p className="text-xs font-medium text-muted-foreground mb-2">Listings near you</p>
                <div className="flex gap-3 overflow-x-auto pb-2">
                  {nearYou.listings.map(l => (
                    <Card key={l.id} className="flex-shrink-0 w-40 p-2 border-honey/30" data-testid={`nearby-listing-${l.id}`}>
                      <div className="aspect-square rounded-lg overflow-hidden bg-honey/10 mb-1.5">
                        {(l.photo_urls?.[0] || l.cover_url) ? <img src={l.photo_urls?.[0] || l.cover_url} alt="" className="w-full h-full object-cover" />
                          : <div className="w-full h-full flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>}
                      </div>
                      <p className="text-xs font-medium truncate">{l.album}</p>
                      <p className="text-[10px] text-muted-foreground truncate">{l.artist}</p>
                      <div className="flex items-center justify-between mt-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${l.listing_type === 'TRADE' ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'}`}>
                          {l.listing_type === 'TRADE' ? 'Trade' : `$${l.price}`}
                        </span>
                        {l.user && <span className="text-[10px] text-muted-foreground">@{l.user.username}</span>}
                      </div>
                    </Card>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </ExploreSection>

      {/* Trending Record Modal */}
      <Dialog open={!!trendingModal} onOpenChange={(open) => { if (!open) setTrendingModal(null); }}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto" aria-describedby="trending-modal-desc">
          <DialogHeader>
            <DialogTitle className="font-heading text-lg">Now Spinning</DialogTitle>
            <p id="trending-modal-desc" className="sr-only">Recent spins for this record</p>
          </DialogHeader>
          {trendingModal && (
            <div>
              {/* Record card */}
              <div className="flex items-center gap-4 mb-4 bg-honey/10 rounded-xl p-3">
                {trendingModal.record?.cover_url ? (
                  <img src={trendingModal.record.cover_url} alt="" className="w-16 h-16 rounded-lg object-cover shadow" />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-heading text-base">{trendingModal.record?.title}</p>
                  <p className="text-sm text-muted-foreground">{trendingModal.record?.artist}{trendingModal.record?.year ? ` (${trendingModal.record.year})` : ''}</p>
                </div>
                <Button size="sm" className="bg-purple-100 text-purple-700 hover:bg-purple-200 rounded-full text-xs shrink-0"
                  onClick={() => addToWantlist(trendingModal.record.artist, trendingModal.record.title, trendingModal.record.discogs_id, trendingModal.record.cover_url, trendingModal.record.year)}
                  data-testid="modal-add-wantlist">
                  <Plus className="w-3 h-3 mr-1" /> Wantlist
                </Button>
              </div>
              {/* Posts feed */}
              {modalLoading ? (
                <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-16 w-full" />)}</div>
              ) : trendingModal.posts.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground py-6">No recent spins for this record.</p>
              ) : (
                <div className="space-y-3">
                  {trendingModal.posts.map(post => (
                    <div key={post.id} className="flex items-start gap-3 py-2" data-testid={`trending-post-${post.id}`}>
                      <Link to={`/profile/${post.user?.username}`}>
                        {post.user?.avatar_url ? <img src={post.user.avatar_url} alt="" className="w-8 h-8 rounded-full object-cover" />
                          : <div className="w-8 h-8 rounded-full bg-honey/30 flex items-center justify-center text-xs font-bold text-honey-amber">{(post.user?.username || '?')[0].toUpperCase()}</div>}
                      </Link>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Link to={`/profile/${post.user?.username}`} className="text-sm font-medium hover:underline">@{post.user?.username}</Link>
                          <span className="text-[10px] text-muted-foreground">{formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}</span>
                        </div>
                        {post.caption && <p className="text-sm text-vinyl-black/80 mt-0.5">{post.caption}</p>}
                        {post.track && <p className="text-xs text-honey-amber mt-0.5">Track: {post.track}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Location Prompt Modal */}
      <Dialog open={showLocationPrompt} onOpenChange={setShowLocationPrompt}>
        <DialogContent className="sm:max-w-sm" aria-describedby="location-modal-desc">
          <DialogHeader>
            <DialogTitle className="font-heading">Set Your Location</DialogTitle>
            <p id="location-modal-desc" className="sr-only">Add your city to find nearby collectors</p>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <Input placeholder="City *" value={cityInput} onChange={e => setCityInput(e.target.value)} className="border-honey/50" data-testid="location-city" autoFocus />
            <Input placeholder="State / Region (optional)" value={regionInput} onChange={e => setRegionInput(e.target.value)} className="border-honey/50" data-testid="location-region" />
            <p className="text-xs text-muted-foreground">This helps us show collectors and listings near you.</p>
            <Button onClick={saveLocation} disabled={!cityInput.trim()} className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="save-location-btn">
              <MapPin className="w-4 h-4 mr-1" /> Save Location
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const ExploreSection = ({ icon, title, testId, seeAllTo, children }) => (
  <section className="mb-10" data-testid={testId}>
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        {icon}
        <h2 className="font-heading text-lg text-vinyl-black">{title}</h2>
      </div>
      {seeAllTo && (
        <Link to={seeAllTo} className="text-xs text-honey-amber hover:text-amber-600 font-medium transition-colors" data-testid={`${testId}-see-all`}>
          See All &rarr;
        </Link>
      )}
    </div>
    {children}
  </section>
);

const EmptyCard = ({ text }) => (
  <Card className="p-6 text-center border-honey/30">
    <p className="text-sm text-muted-foreground">{text}</p>
  </Card>
);

export default ExplorePage;
