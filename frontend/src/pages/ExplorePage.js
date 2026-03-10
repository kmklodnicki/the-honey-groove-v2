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
import { Disc, Users, Search, TrendingUp, Lock, Play, UserPlus, MessageCircle, MapPin, Heart, Plus, Crown } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';
import { ListingTypeBadge } from '../components/PostCards';
import ScrollRow from '../components/ScrollRow';
import { useVariantModal } from '../context/VariantModalContext';

const ExplorePage = () => {
  usePageTitle('Nectar');
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [trending, setTrending] = useState([]);
  const [suggested, setSuggested] = useState([]);
  const [trendingCollections, setTrendingCollections] = useState([]);
  const [crownJewels, setCrownJewels] = useState([]);
  const [mostWanted, setMostWanted] = useState([]);
  const [nearYou, setNearYou] = useState({ collectors: [], listings: [], needs_location: true });
  const [loading, setLoading] = useState(true);
  const [myKindaPeople, setMyKindaPeople] = useState([]);
  const { openVariantModal } = useVariantModal();

  // Location prompt
  const [showLocationPrompt, setShowLocationPrompt] = useState(false);
  const [regionInput, setRegionInput] = useState('');

  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = useCallback(async () => {
    if (!token) { setLoading(false); return; }
    try {
      const [trendRes, sugRes, tcRes, mwRes, nyRes, cjRes] = await Promise.all([
        axios.get(`${API}/explore/trending?limit=10`, { headers }),
        axios.get(`${API}/explore/suggested-collectors?limit=8`, { headers }),
        axios.get(`${API}/explore/trending-in-collections?limit=12`, { headers }),
        axios.get(`${API}/explore/most-wanted?limit=20`, { headers }),
        axios.get(`${API}/explore/near-you`, { headers }),
        axios.get(`${API}/explore/crown-jewels?limit=12`, { headers }),
      ]);
      setTrending(trendRes.data);
      setSuggested(sugRes.data);
      setTrendingCollections(tcRes.data);
      setMostWanted(mwRes.data);
      setNearYou(nyRes.data);
      setCrownJewels(cjRes.data);
      // Fetch discovery carousel
      axios.get(`${API}/discover/my-kinda-people`, { headers }).then(r => setMyKindaPeople(r.data)).catch(() => {});
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const openTrendingModal = (record) => {
    openVariantModal({
      artist: record.artist,
      album: record.title || record.album,
      variant: record.color_variant || record.variant || '',
      discogs_id: record.discogs_id,
      cover_url: record.cover_url,
    });
  };

  const addToSeekingList = async (artist, album, discogs_id, cover_url, year) => {
    try {
      await axios.post(`${API}/composer/iso`, {
        artist, album, discogs_id, cover_url, year,
        intent: 'seeking',
      }, { headers });
      toast.success(`Added to your Dream List!`);
    } catch (err) {
      if (err.response?.status === 409) toast.info('already on your Dream List.');
      else toast.error('could not add. try again.');
    }
  };

  const saveLocation = async () => {
    if (!regionInput.trim()) { toast.error('state is required.'); return; }
    try {
      await axios.put(`${API}/auth/me`, { region: regionInput.trim() }, { headers });
      toast.success('state saved.');
      setShowLocationPrompt(false);
      fetchData();
    } catch { toast.error('could not save state. try again.'); }
  };

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-16 md:pt-24">
        <h1 className="font-heading text-3xl text-vinyl-black mb-6">Nectar</h1>
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
      <div className="max-w-4xl mx-auto px-4 py-8 pt-16 md:pt-24">
        <Skeleton className="h-8 w-40 mb-6" />
        <Skeleton className="h-6 w-48 mb-3" />
        <div className="flex gap-3 overflow-hidden mb-8">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-48 w-36 rounded-xl shrink-0" />)}</div>
        <Skeleton className="h-6 w-32 mb-3" />
        <div className="grid grid-cols-2 gap-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8" data-testid="explore-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-1">Nectar</h1>
      <p className="text-sm text-muted-foreground mb-8">what the hive is into right now.</p>

      {/* Your Kinda People Discovery Carousel */}
      <section className="mb-8" data-testid="make-friends-carousel">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-honey-amber" />
          <h2 className="font-heading text-lg text-vinyl-black font-bold">Your Kinda People</h2>
        </div>
        <p className="text-xs text-muted-foreground mb-3">Collectors who share your vibe.</p>
        {myKindaPeople.length === 0 ? (
          <div
            className="rounded-2xl p-8 text-center"
            style={{
              background: 'rgba(255,255,255,0.6)',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
              border: '1px solid rgba(218,165,32,0.2)',
            }}
            data-testid="kinda-people-empty"
          >
            <Search className="w-8 h-8 mx-auto mb-3" style={{ color: '#DAA520', animation: 'nectarPulse 2s ease-in-out infinite' }} />
            <p className="font-heading text-lg text-vinyl-black mb-1">You've Found Your Tribe.</p>
            <p className="text-sm text-muted-foreground max-w-xs mx-auto">You are already following all the top collectors in this groove. Check back soon for new arrivals.</p>
          </div>
        ) : (
          <ScrollRow>
            {myKindaPeople.map(p => (
              <Link key={p.username} to={`/profile/${p.username}?tab=in-common`} className="flex-shrink-0 w-40 group" data-testid={`kinda-${p.username}`}>
                <Card className="p-3 border-honey/30 hover:shadow-honey transition-all text-center">
                  <div className="w-14 h-14 mx-auto rounded-full overflow-hidden bg-honey/10 mb-2">
                    {p.avatar_url ? <img src={p.avatar_url} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Users className="w-6 h-6 text-honey" /></div>}
                  </div>
                  <p className="text-sm font-medium truncate">@{p.username}</p>
                  <p className="text-xs font-bold mt-0.5" style={{ color: '#C8861A' }}>{p.common_count || 0} {(p.common_count || 0) === 1 ? 'record' : 'records'} in common</p>
                  {p.shared_covers?.length > 0 && (
                    <div className="flex justify-center gap-1 mt-2">
                      {p.shared_covers.slice(0, 3).map((c, i) => (
                        <div key={i} className="w-10 h-10 rounded-md overflow-hidden bg-vinyl-black">
                          <AlbumArt src={c.cover_url} alt={c.title} className="w-full h-full object-cover" />
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              </Link>
            ))}
          </ScrollRow>
        )}
      </section>

      {/* Collector Bingo — hidden until feature is ready */}

      {/* 1. Trending in the Hive */}
      <ExploreSection icon={<TrendingUp className="w-4 h-4 text-honey-amber" />} title="Trending in the Hive" testId="trending-section" seeAllTo="/nectar/trending">
        <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">What Hive members have been spinning.</p>
        {trending.length === 0 ? (
          <EmptyCard text="No trending records yet. Start spinning!" />
        ) : (
          <ScrollRow>
            {trending.map(r => (
              <button key={r.id} onClick={() => openTrendingModal(r)}
                className="flex-shrink-0 w-36 text-left group" data-testid={`trending-${r.id}`}>
                <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm group-hover:shadow-md transition-shadow">
                  <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} artist={r.artist} title={r.title} className="w-full h-full object-cover" />
                </div>
                <p className="text-sm font-medium truncate">{r.title}</p>
                <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <Play className="w-3 h-3 text-honey-amber" />
                  <span className="text-xs text-honey-amber font-medium">{r.trending_spins} {r.trending_spins === 1 ? 'spin' : 'spins'}</span>
                </div>
              </button>
            ))}
          </ScrollRow>
        )}
      </ExploreSection>

      {/* 3. Crown Jewels — rarest & most valuable records */}
      <ExploreSection icon={<Crown className="w-4 h-4 text-[#FFD700]" />} title="Crown Jewels" testId="crown-jewels-section" seeAllTo="/nectar/crown-jewels">
        <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">The rarest and most valuable records owned by Hive members.</p>
        {crownJewels.length === 0 ? (
          <EmptyCard text="Scanning the vaults for grails..." />
        ) : (
          <ScrollRow>
            {crownJewels.map((r, idx) => (
              <button key={r.discogs_id || idx} onClick={() => navigate(`/variant/${r.discogs_id}`)} className="flex-shrink-0 w-40 text-left group" data-testid={`crown-jewel-${r.discogs_id || idx}`}>
                <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm relative group-hover:shadow-md transition-shadow">
                  <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} artist={r.artist} title={r.title} className="w-full h-full object-cover" />
                  {r.estimated_value > 0 && (
                    <span
                      className="absolute top-2 left-2 text-[10px] font-bold px-2 py-0.5 rounded-full"
                      style={{ background: 'rgba(255,215,0,0.85)', color: '#2A1A06', backdropFilter: 'blur(6px)', border: '1px solid rgba(218,165,32,0.6)' }}
                      data-testid={`cj-value-${r.discogs_id || idx}`}
                    >
                      ${r.estimated_value >= 1000 ? (r.estimated_value / 1000).toFixed(1) + 'k' : r.estimated_value.toFixed(0)}
                    </span>
                  )}
                  <span
                    role="button"
                    onClick={(e) => { e.stopPropagation(); addToSeekingList(r.artist, r.title, r.discogs_id, r.cover_url, r.year); }}
                    className="absolute bottom-2 right-2 bg-white/90 hover:bg-white rounded-full p-1.5 shadow opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                    data-testid={`add-wantlist-cj-${r.discogs_id || idx}`}>
                    <Plus className="w-4 h-4 text-honey-amber" />
                  </span>
                </div>
                <p className="text-sm font-medium truncate">{r.title}</p>
                <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
                {r.variant && (
                  <p className="text-[10px] text-muted-foreground flex items-center gap-1 truncate">
                    <Crown className="w-2.5 h-2.5 text-[#FFD700] shrink-0" /> {r.variant}
                  </p>
                )}
                {r.have > 0 && <p className="text-[10px] text-muted-foreground">{r.have.toLocaleString()} global owners</p>}
              </button>
            ))}
          </ScrollRow>
        )}
      </ExploreSection>

      {/* 4. Most Wanted */}
      <ExploreSection icon={<Heart className="w-4 h-4 text-red-400" />} title="Most Wanted" testId="most-wanted-section" seeAllTo="/nectar/most-wanted">
        <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">Hive members have their eyes on these records.</p>
        {mostWanted.length === 0 ? (
          <EmptyCard text="No Dream List data yet. Add records to your Dream List!" />
        ) : (
          <div className="space-y-2">
            {mostWanted.map((r, idx) => (
              <button key={`${r.artist}-${r.album}`} onClick={() => openTrendingModal({ ...r, title: r.album })}
                className="flex items-center gap-3 py-2 px-1 rounded-lg hover:bg-honey/5 transition-colors w-full text-left" data-testid={`most-wanted-${idx}`}>
                <span className="text-sm font-heading text-honey-amber w-6 text-right shrink-0">{idx + 1}</span>
                <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} className="w-10 h-10 rounded-lg object-cover" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{r.album}</p>
                  <p className="text-xs text-muted-foreground truncate">{r.artist}{r.year ? ` (${r.year})` : ''}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-red-500 font-medium">{r.want_count} {r.want_count === 1 ? 'want' : 'wants'}</span>
                  <span onClick={(e) => { e.stopPropagation(); addToSeekingList(r.artist, r.album, r.discogs_id, r.cover_url, r.year); }}
                    className="text-honey-amber hover:bg-honey/10 rounded-full p-1 cursor-pointer" data-testid={`want-${idx}`}>
                    <Plus className="w-4 h-4" />
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </ExploreSection>

      {/* 5. Near You */}
      <ExploreSection icon={<MapPin className="w-4 h-4 text-honey-amber" />} title="Near You" testId="near-you-section" seeAllTo="/nectar/near-you">
        {nearYou.needs_location ? (
          <Card className="p-6 text-center border-honey/30">
            <MapPin className="w-10 h-10 text-honey/40 mx-auto mb-3" />
            <h3 className="font-heading text-lg mb-1">Set your state</h3>
            <p className="text-muted-foreground text-sm mb-4">Add your state to discover collectors near you.</p>
            <Button onClick={() => setShowLocationPrompt(true)} className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="set-location-btn">
              <MapPin className="w-4 h-4 mr-1" /> Set State
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
                      {u.avatar_url ? <img src={resolveImageUrl(u.avatar_url)} alt="" className="w-10 h-10 rounded-full object-cover" />
                        : <div className="w-10 h-10 rounded-full bg-honey/30 flex items-center justify-center text-sm font-bold text-honey-amber">{(u.username || '?')[0].toUpperCase()}</div>}
                    </Link>
                    <div className="flex-1 min-w-0">
                      <Link to={`/profile/${u.username}`} className="text-sm font-medium hover:underline">@{u.username}</Link>
                      <p className="text-[10px] text-muted-foreground">{u.region}</p>
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
                <ScrollRow>
                  {nearYou.listings.map(l => (
                    <Card key={l.id} className="flex-shrink-0 w-40 p-2 border-honey/30" data-testid={`nearby-listing-${l.id}`}>
                      <div className="aspect-square rounded-lg overflow-hidden bg-honey/10 mb-1.5">
                        {(l.photo_urls?.[0] || l.cover_url) ? <AlbumArt src={l.photo_urls?.[0] || l.cover_url} alt={`${l.artist} ${l.album} vinyl record`} className="w-full h-full object-cover" />
                          : <div className="w-full h-full flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>}
                      </div>
                      <p className="text-xs font-medium truncate">{l.album}</p>
                      <p className="text-[10px] text-muted-foreground truncate">{l.artist}</p>
                      <div className="flex items-center justify-between mt-1">
                        <ListingTypeBadge type={l.listing_type} price={l.price} size="xs" />
                        {l.user && <span className="text-[10px] text-muted-foreground">@{l.user.username}</span>}
                      </div>
                    </Card>
                  ))}
                </ScrollRow>
              </>
            )}
          </div>
        )}
      </ExploreSection>

      {/* Location Prompt Modal */}
      <Dialog open={showLocationPrompt} onOpenChange={setShowLocationPrompt}>
        <DialogContent className="sm:max-w-sm" aria-describedby="location-modal-desc">
          <DialogHeader>
            <DialogTitle className="font-heading">Set Your State</DialogTitle>
            <p id="location-modal-desc" className="sr-only">Add your state to find nearby collectors</p>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <Input placeholder="State *" value={regionInput} onChange={e => setRegionInput(e.target.value)} className="border-honey/50" data-testid="location-region" autoFocus />
            <p className="text-xs text-muted-foreground">This helps us show collectors in your state.</p>
            <Button onClick={saveLocation} disabled={!regionInput.trim()} className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="save-location-btn">
              <MapPin className="w-4 h-4 mr-1" /> Save State
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
