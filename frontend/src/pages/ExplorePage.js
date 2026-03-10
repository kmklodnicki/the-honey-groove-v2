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
import { Disc, Users, Search, TrendingUp, Lock, ShoppingBag, Play, UserPlus, MessageCircle, MapPin, Heart, Plus, X, Loader2, ArrowRightLeft, Calendar, Music2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import CollectorBingo from '../components/CollectorBingo';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';
import { ListingTypeBadge } from '../components/PostCards';

const ExplorePage = () => {
  usePageTitle('Nectar');
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [trending, setTrending] = useState([]);
  const [suggested, setSuggested] = useState([]);
  const [trendingCollections, setTrendingCollections] = useState([]);
  const [mostWanted, setMostWanted] = useState([]);
  const [nearYou, setNearYou] = useState({ collectors: [], listings: [], needs_location: true });
  const [loading, setLoading] = useState(true);
  const [myKindaPeople, setMyKindaPeople] = useState([]);

  // Trending modal
  const [trendingModal, setTrendingModal] = useState(null); // { record, posts }
  const [modalLoading, setModalLoading] = useState(false);
  const [modalInCollection, setModalInCollection] = useState(null); // null | { in_collection, record_id }
  const [modalRelease, setModalRelease] = useState(null); // Discogs release details
  const [spinningModal, setSpinningModal] = useState(false);
  const [addingToCollection, setAddingToCollection] = useState(false);

  // Location prompt
  const [showLocationPrompt, setShowLocationPrompt] = useState(false);
  const [cityInput, setCityInput] = useState('');
  const [regionInput, setRegionInput] = useState('');

  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = useCallback(async () => {
    if (!token) { setLoading(false); return; }
    try {
      const [trendRes, sugRes, tcRes, mwRes, nyRes] = await Promise.all([
        axios.get(`${API}/explore/trending?limit=10`, { headers }),
        axios.get(`${API}/explore/suggested-collectors?limit=8`, { headers }),
        axios.get(`${API}/explore/trending-in-collections?limit=12`, { headers }),
        axios.get(`${API}/explore/most-wanted?limit=20`, { headers }),
        axios.get(`${API}/explore/near-you`, { headers }),
      ]);
      setTrending(trendRes.data);
      setSuggested(sugRes.data);
      setTrendingCollections(tcRes.data);
      setMostWanted(mwRes.data);
      setNearYou(nyRes.data);
      // Fetch discovery carousel
      axios.get(`${API}/discover/my-kinda-people`, { headers }).then(r => setMyKindaPeople(r.data)).catch(() => {});
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const openTrendingModal = async (record) => {
    setModalLoading(true);
    setModalInCollection(null);
    setModalRelease(null);
    setTrendingModal({ record, posts: [] });

    const discogsId = record.discogs_id;

    // Fire all requests in parallel
    const postsPromise = record.id
      ? axios.get(`${API}/explore/trending/${record.id}/posts`, { headers }).catch(() => null)
      : Promise.resolve(null);
    const ownershipPromise = discogsId
      ? axios.get(`${API}/records/check-ownership?discogs_id=${discogsId}`, { headers }).catch(() => null)
      : (record.artist && record.title)
        ? axios.get(`${API}/records/check-ownership?artist=${encodeURIComponent(record.artist)}&title=${encodeURIComponent(record.title)}`, { headers }).catch(() => null)
        : Promise.resolve(null);
    const releasePromise = discogsId
      ? axios.get(`${API}/discogs/release/${discogsId}`, { headers }).catch(() => null)
      : Promise.resolve(null);

    const [postsResp, ownershipResp, releaseResp] = await Promise.all([postsPromise, ownershipPromise, releasePromise]);

    if (postsResp?.data) {
      setTrendingModal({ record: postsResp.data.record || record, posts: postsResp.data.posts || [] });
    }
    if (ownershipResp?.data) {
      setModalInCollection(ownershipResp.data);
    } else {
      setModalInCollection({ in_collection: false, record_id: null });
    }
    if (releaseResp?.data) {
      setModalRelease(releaseResp.data);
    }
    setModalLoading(false);
  };

  const handleAddToCollection = async () => {
    if (!trendingModal?.record) return;
    setAddingToCollection(true);
    const r = trendingModal.record;
    try {
      const res = await axios.post(`${API}/records`, {
        discogs_id: r.discogs_id,
        title: r.title || r.album,
        artist: r.artist,
        cover_url: r.cover_url,
        year: r.year,
        format: modalRelease?.format?.[0] || 'Vinyl',
      }, { headers });
      toast.success('added to your collection!');
      setModalInCollection({ in_collection: true, record_id: res.data.id });
    } catch (err) {
      if (err.response?.status === 409) toast.info('already in your collection.');
      else toast.error('could not add. try again.');
    }
    setAddingToCollection(false);
  };

  const handleLogSpin = async () => {
    if (!modalInCollection?.record_id) return;
    setSpinningModal(true);
    try {
      await axios.post(`${API}/spins`, { record_id: modalInCollection.record_id }, { headers });
      toast.success('spin logged!');
    } catch { toast.error('could not log spin. try again.'); }
    setSpinningModal(false);
  };

  const addToWantlist = async (artist, album, discogs_id, cover_url, year) => {
    try {
      await axios.post(`${API}/composer/iso`, {
        artist, album, discogs_id, cover_url, year,
      }, { headers });
      toast.success(`Added to your Wantlist!`);
    } catch (err) {
      if (err.response?.status === 409) toast.info('already on your wantlist.');
      else toast.error('could not add. try again.');
    }
  };

  const saveLocation = async () => {
    if (!cityInput.trim()) { toast.error('city is required.'); return; }
    try {
      await axios.put(`${API}/auth/me`, { city: cityInput.trim(), region: regionInput.trim() }, { headers });
      toast.success('location saved.');
      setShowLocationPrompt(false);
      fetchData();
    } catch { toast.error('could not save location. try again.'); }
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

      {/* Make Friends Discovery Carousel */}
      {myKindaPeople.length > 0 && (
        <section className="mb-8" data-testid="make-friends-carousel">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-4 h-4 text-honey-amber" />
            <h2 className="font-heading text-lg text-vinyl-black">Make Friends</h2>
          </div>
          <p className="text-xs text-muted-foreground mb-3">Collectors who share your vibe.</p>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
            {myKindaPeople.map(p => (
              <Link key={p.username} to={`/profile/${p.username}?tab=in-common`} className="flex-shrink-0 w-40 group" data-testid={`kinda-${p.username}`}>
                <Card className="p-3 border-honey/30 hover:shadow-honey transition-all text-center">
                  <div className="w-14 h-14 mx-auto rounded-full overflow-hidden bg-honey/10 mb-2">
                    {p.avatar_url ? <img src={p.avatar_url} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Users className="w-6 h-6 text-honey" /></div>}
                  </div>
                  <p className="text-sm font-medium truncate">@{p.username}</p>
                  <p className="text-xs font-bold mt-0.5" style={{ color: '#C8861A' }}>{p.shared_records || p.score || 0} records in common</p>
                  {/* Shared covers stack */}
                  {p.shared_covers?.length > 0 && (
                    <div className="flex justify-center gap-1 mt-2">
                      {p.shared_covers.slice(0, 3).map((c, i) => (
                        <div key={i} className="w-10 h-10 rounded-md overflow-hidden bg-vinyl-black">
                          <AlbumArt src={c.cover_url} alt={c.title} className="w-full h-full object-cover" />
                        </div>
                      ))}
                    </div>
                  )}
                  <p className="text-[10px] text-muted-foreground mt-1">{p.common_count} in common</p>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Collector Bingo — hidden until feature is ready */}

      {/* 1. Trending in the Hive */}
      <ExploreSection icon={<TrendingUp className="w-4 h-4 text-honey-amber" />} title="Trending in the Hive" testId="trending-section" seeAllTo="/nectar/trending">
        {trending.length === 0 ? (
          <EmptyCard text="No trending records yet. Start spinning!" />
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
            {trending.map(r => (
              <button key={r.id} onClick={() => openTrendingModal(r)}
                className="flex-shrink-0 w-36 text-left group" data-testid={`trending-${r.id}`}>
                <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm group-hover:shadow-md transition-shadow">
                  <AlbumArt src={r.cover_url} alt="" className="w-full h-full object-cover" />
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

      {/* 2. Make Friends */}
      <ExploreSection icon={<Users className="w-4 h-4 text-honey-amber" />} title="Make Friends" testId="make-friends-section" seeAllTo="/nectar/make-friends">
        {suggested.length === 0 ? (
          <EmptyCard text="Add more records to your collection to discover new friends." />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {suggested.map(u => (
              <Card key={u.id} className="p-4 border-honey/30 hover:shadow-sm transition-all" data-testid={`make-friends-${u.id}`}>
                <div className="flex items-center gap-3">
                  <Link to={`/profile/${u.username}`}>
                    {u.avatar_url ? <img src={resolveImageUrl(u.avatar_url)} alt="" className="w-11 h-11 rounded-full object-cover" />
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

      {/* 3. Trending in Collections */}
      <ExploreSection icon={<TrendingUp className="w-4 h-4 text-honey-amber" />} title="Trending in Collections" testId="trending-collections-section" seeAllTo="/nectar/trending-in-collections">
        {trendingCollections.length === 0 ? (
          <EmptyCard text="No trending collection data right now." />
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
            {trendingCollections.map((r, idx) => (
              <button key={r.discogs_id || idx} onClick={() => openTrendingModal(r)} className="flex-shrink-0 w-40 text-left group" data-testid={`trending-collection-${r.discogs_id || idx}`}>
                <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm relative group-hover:shadow-md transition-shadow">
                  <AlbumArt src={r.cover_url} alt="" className="w-full h-full object-cover" />
                  <span
                    role="button"
                    onClick={(e) => { e.stopPropagation(); addToWantlist(r.artist, r.title, r.discogs_id, r.cover_url, r.year); }}
                    className="absolute bottom-2 right-2 bg-white/90 hover:bg-white rounded-full p-1.5 shadow opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                    data-testid={`add-wantlist-tc-${r.discogs_id || idx}`}>
                    <Plus className="w-4 h-4 text-honey-amber" />
                  </span>
                </div>
                <p className="text-sm font-medium truncate">{r.title}</p>
                <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
                {r.have > 0 && <p className="text-[10px] text-muted-foreground">owned by {r.have.toLocaleString()} collectors</p>}
              </button>
            ))}
          </div>
        )}
      </ExploreSection>

      {/* 4. Most Wanted */}
      <ExploreSection icon={<Heart className="w-4 h-4 text-red-400" />} title="Most Wanted" testId="most-wanted-section" seeAllTo="/nectar/most-wanted">
        {mostWanted.length === 0 ? (
          <EmptyCard text="No wantlist data yet. Add records to your Wantlist!" />
        ) : (
          <div className="space-y-2">
            {mostWanted.map((r, idx) => (
              <button key={`${r.artist}-${r.album}`} onClick={() => openTrendingModal({ ...r, title: r.album })}
                className="flex items-center gap-3 py-2 px-1 rounded-lg hover:bg-honey/5 transition-colors w-full text-left" data-testid={`most-wanted-${idx}`}>
                <span className="text-sm font-heading text-honey-amber w-6 text-right shrink-0">{idx + 1}</span>
                <AlbumArt src={r.cover_url} alt="" className="w-10 h-10 rounded-lg object-cover" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{r.album}</p>
                  <p className="text-xs text-muted-foreground truncate">{r.artist}{r.year ? ` (${r.year})` : ''}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-red-500 font-medium">{r.want_count} {r.want_count === 1 ? 'want' : 'wants'}</span>
                  <span onClick={(e) => { e.stopPropagation(); addToWantlist(r.artist, r.album, r.discogs_id, r.cover_url, r.year); }}
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
                      {u.avatar_url ? <img src={resolveImageUrl(u.avatar_url)} alt="" className="w-10 h-10 rounded-full object-cover" />
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
                        {(l.photo_urls?.[0] || l.cover_url) ? <AlbumArt src={l.photo_urls?.[0] || l.cover_url} alt="" className="w-full h-full object-cover" />
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
                </div>
              </>
            )}
          </div>
        )}
      </ExploreSection>

      {/* Trending Record Modal */}
      <Dialog open={!!trendingModal} onOpenChange={(open) => { if (!open) { setTrendingModal(null); setModalInCollection(null); setModalRelease(null); } }}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto" aria-describedby="trending-modal-desc">
          <DialogHeader>
            <DialogTitle className="font-heading text-lg">Album Details</DialogTitle>
            <p id="trending-modal-desc" className="sr-only">Details and actions for this record</p>
          </DialogHeader>
          {trendingModal && (
            <div>
              {/* Record card */}
              <div className="flex items-center gap-4 mb-3 bg-honey/10 rounded-xl p-3">
                {trendingModal.record?.cover_url ? (
                  <AlbumArt src={trendingModal.record.cover_url} alt="" className="w-20 h-20 rounded-lg object-cover shadow" />
                ) : (
                  <div className="w-20 h-20 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-heading text-base leading-tight" data-testid="modal-album-title">{trendingModal.record?.title || trendingModal.record?.album}</p>
                  <p className="text-sm text-honey-amber italic" data-testid="modal-album-artist">{trendingModal.record?.artist}{trendingModal.record?.year ? ` (${trendingModal.record.year})` : ''}</p>
                </div>
              </div>

              {/* Variant / Pressing Details */}
              {(modalRelease || trendingModal.record?.format) && (
                <div className="flex flex-wrap gap-1.5 mb-4" data-testid="modal-variant-details">
                  {(modalRelease?.year || trendingModal.record?.year) && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                      <Calendar className="w-3 h-3" /> {modalRelease?.year || trendingModal.record?.year}
                    </span>
                  )}
                  {modalRelease?.label?.[0] && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70" data-testid="modal-label">
                      {modalRelease.label[0]}
                    </span>
                  )}
                  {modalRelease?.catno && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70" data-testid="modal-catno">
                      {modalRelease.catno}
                    </span>
                  )}
                  {modalRelease?.format?.[0] && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70" data-testid="modal-format">
                      <Disc className="w-3 h-3" /> {modalRelease.format.join(', ')}
                    </span>
                  )}
                  {modalRelease?.country && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70" data-testid="modal-country">
                      {modalRelease.country}
                    </span>
                  )}
                  {modalRelease?.color_variant && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-xs text-amber-800 font-medium" data-testid="modal-color-variant">
                      {modalRelease.color_variant}
                    </span>
                  )}
                  {!modalRelease && trendingModal.record?.format && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                      <Disc className="w-3 h-3" /> {Array.isArray(trendingModal.record.format) ? trendingModal.record.format.join(', ') : trendingModal.record.format}
                    </span>
                  )}
                </div>
              )}

              {/* Contextual Action Buttons */}
              {modalLoading ? (
                <div className="flex justify-center py-3"><Loader2 className="w-5 h-5 animate-spin text-honey-amber" /></div>
              ) : modalInCollection?.in_collection ? (
                <div className="flex flex-wrap gap-2 mb-4" data-testid="modal-owner-actions">
                  <Button size="sm" className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs"
                    onClick={handleLogSpin} disabled={spinningModal} data-testid="modal-log-spin">
                    {spinningModal ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Play className="w-3 h-3 mr-1" />} Log a Spin
                  </Button>
                  <Button size="sm" variant="outline" className="rounded-full text-xs border-honey/50 text-honey-amber hover:bg-honey/10"
                    onClick={() => {
                      const r = trendingModal.record;
                      setTrendingModal(null);
                      navigate(`/honeypot?create=sale&artist=${encodeURIComponent(r.artist)}&album=${encodeURIComponent(r.title || r.album)}&discogs_id=${r.discogs_id || ''}&cover_url=${encodeURIComponent(r.cover_url || '')}&year=${r.year || ''}`);
                    }} data-testid="modal-list-for-sale">
                    <ShoppingBag className="w-3 h-3 mr-1" /> List for Sale
                  </Button>
                  <Button size="sm" variant="outline" className="rounded-full text-xs border-honey/50 text-honey-amber hover:bg-honey/10"
                    onClick={() => {
                      const r = trendingModal.record;
                      setTrendingModal(null);
                      navigate(`/honeypot?create=trade&artist=${encodeURIComponent(r.artist)}&album=${encodeURIComponent(r.title || r.album)}&discogs_id=${r.discogs_id || ''}&cover_url=${encodeURIComponent(r.cover_url || '')}&year=${r.year || ''}`);
                    }} data-testid="modal-offer-trade">
                    <ArrowRightLeft className="w-3 h-3 mr-1" /> Offer to Trade
                  </Button>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2 mb-4" data-testid="modal-nonowner-actions">
                  <Button size="sm" className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs"
                    onClick={handleAddToCollection} disabled={addingToCollection} data-testid="modal-add-collection">
                    {addingToCollection ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Plus className="w-3 h-3 mr-1" />} Add to Collection
                  </Button>
                  <Button size="sm" variant="outline" className="rounded-full text-xs border-honey/50 text-honey-amber hover:bg-honey/10"
                    onClick={() => addToWantlist(trendingModal.record.artist, trendingModal.record.title || trendingModal.record.album, trendingModal.record.discogs_id, trendingModal.record.cover_url, trendingModal.record.year)}
                    data-testid="modal-add-wantlist">
                    <Heart className="w-3 h-3 mr-1" /> Add to Wantlist
                  </Button>
                </div>
              )}

              {/* Discogs link */}
              {trendingModal.record?.discogs_id && (
                <a href={`https://www.discogs.com/release/${trendingModal.record.discogs_id}`} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-vinyl-black/5 text-xs text-vinyl-black/60 hover:bg-vinyl-black/10 transition-colors mb-4" data-testid="modal-discogs-link">
                  <Music2 className="w-3 h-3" /> View on Discogs
                </a>
              )}

              {/* Divider */}
              <div className="border-t border-honey/20 pt-3 mt-1" />

              {/* Posts feed */}
              <p className="text-xs font-medium text-muted-foreground mb-2">Recent Spins</p>
              {modalLoading ? (
                <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-16 w-full" />)}</div>
              ) : trendingModal.posts.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground py-6">no recent spins for this record.</p>
              ) : (
                <div className="space-y-3">
                  {trendingModal.posts.map(post => (
                    <div key={post.id} className="flex items-start gap-3 py-2" data-testid={`trending-post-${post.id}`}>
                      <Link to={`/profile/${post.user?.username}`}>
                        {post.user?.avatar_url ? <img src={resolveImageUrl(post.user.avatar_url)} alt="" className="w-8 h-8 rounded-full object-cover" />
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
