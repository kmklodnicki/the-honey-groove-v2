import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import { ArrowLeft, TrendingUp, Users, Disc, Heart, MapPin, Play, Plus, MessageCircle, UserPlus } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';
import { ListingTypeBadge } from '../components/PostCards';

const SECTIONS = {
  trending: { title: 'Trending in the Hive', icon: TrendingUp, iconColor: 'text-honey-amber' },
  'make-friends': { title: 'Make Friends', icon: Users, iconColor: 'text-honey-amber' },
  'trending-in-collections': { title: 'Trending in Collections', icon: TrendingUp, iconColor: 'text-honey-amber' },
  'most-wanted': { title: 'Most Wanted', icon: Heart, iconColor: 'text-red-400' },
  'near-you': { title: 'Near You', icon: MapPin, iconColor: 'text-honey-amber' },
};

const ExploreSeeAllPage = () => {
  usePageTitle('Nectar');
  const { section } = useParams();
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const meta = SECTIONS[section];
  const headers = { Authorization: `Bearer ${token}` };

  // Trending modal state
  const [trendingModal, setTrendingModal] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);

  // Location prompt
  const [showLocationPrompt, setShowLocationPrompt] = useState(false);
  const [cityInput, setCityInput] = useState('');
  const [regionInput, setRegionInput] = useState('');

  const fetchData = useCallback(async () => {
    if (!token) { setLoading(false); return; }
    try {
      let resp;
      switch (section) {
        case 'trending':
          resp = await axios.get(`${API}/explore/trending?limit=50`, { headers });
          break;
        case 'make-friends':
          resp = await axios.get(`${API}/explore/suggested-collectors?limit=50`, { headers });
          break;
        case 'trending-in-collections':
          resp = await axios.get(`${API}/explore/trending-in-collections?limit=50`, { headers });
          break;
        case 'most-wanted':
          resp = await axios.get(`${API}/explore/most-wanted?limit=100`, { headers });
          break;
        case 'near-you':
          resp = await axios.get(`${API}/explore/near-you?collector_limit=50&listing_limit=30`, { headers });
          break;
        default:
          break;
      }
      setData(resp?.data ?? []);
    } catch { toast.error('something went wrong. please try again.'); }
    finally { setLoading(false); }
  }, [API, token, section]);

  useEffect(() => { setLoading(true); setData(null); fetchData(); }, [fetchData]);

  const openTrendingModal = async (record) => {
    setModalLoading(true);
    setTrendingModal({ record, posts: [] });
    try {
      const resp = await axios.get(`${API}/explore/trending/${record.id}/posts`, { headers });
      setTrendingModal({ record: resp.data.record, posts: resp.data.posts });
    } catch { toast.error('could not load posts.'); }
    finally { setModalLoading(false); }
  };

  const addToWantlist = async (artist, album, discogs_id, cover_url, year) => {
    try {
      await axios.post(`${API}/composer/iso`, { artist, album, discogs_id, cover_url, year }, { headers });
      toast.success('added to your wantlist.');
      trackEvent('wantlist_added');
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

  if (!meta) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-16 md:pt-24 text-center">
        <p className="text-muted-foreground">Section not found.</p>
        <Link to="/nectar" className="text-honey-amber hover:underline text-sm mt-2 inline-block">Back to Nectar</Link>
      </div>
    );
  }

  const Icon = meta.icon;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8" data-testid={`see-all-${section}`}>
      {/* Header */}
      <Link to="/nectar" className="inline-flex items-center gap-1.5 text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors mb-6" data-testid="see-all-back">
        <ArrowLeft className="w-4 h-4" /> back to nectar
      </Link>
      <div className="flex items-center gap-2 mb-8">
        <Icon className={`w-5 h-5 ${meta.iconColor}`} />
        <h1 className="font-heading text-3xl text-vinyl-black">{meta.title}</h1>
      </div>

      {loading ? <LoadingSkeleton section={section} /> : (
        <>
          {section === 'trending' && <TrendingAll data={data} onOpen={openTrendingModal} />}
          {section === 'make-friends' && <TasteMatchAll data={data} navigate={navigate} />}
          {section === 'trending-in-collections' && <TrendingCollectionsAll data={data} addToWantlist={addToWantlist} />}
          {section === 'most-wanted' && <MostWantedAll data={data} addToWantlist={addToWantlist} />}
          {section === 'near-you' && (
            <NearYouAll
              data={data}
              navigate={navigate}
              onSetLocation={() => setShowLocationPrompt(true)}
            />
          )}
        </>
      )}

      {/* Trending Modal */}
      <Dialog open={!!trendingModal} onOpenChange={(open) => { if (!open) setTrendingModal(null); }}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto" aria-describedby="sa-trending-desc">
          <DialogHeader>
            <DialogTitle className="font-heading text-lg">Now Spinning</DialogTitle>
            <p id="sa-trending-desc" className="sr-only">Recent spins for this record</p>
          </DialogHeader>
          {trendingModal && (
            <div>
              <div className="flex items-center gap-4 mb-4 bg-honey/10 rounded-xl p-3">
                {trendingModal.record?.cover_url ? (
                  <AlbumArt src={trendingModal.record.cover_url} alt={`${trendingModal.record.artist} ${trendingModal.record.title} vinyl record`} className="w-16 h-16 rounded-lg object-cover shadow" />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-heading text-base">{trendingModal.record?.title}</p>
                  <p className="text-sm text-muted-foreground">{trendingModal.record?.artist}</p>
                </div>
                <Button size="sm" className="bg-purple-100 text-purple-700 hover:bg-purple-200 rounded-full text-xs shrink-0"
                  onClick={() => addToWantlist(trendingModal.record.artist, trendingModal.record.title, trendingModal.record.discogs_id, trendingModal.record.cover_url, trendingModal.record.year)}
                  data-testid="sa-modal-add-wantlist">
                  <Plus className="w-3 h-3 mr-1" /> Wantlist
                </Button>
              </div>
              {modalLoading ? (
                <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-16 w-full" />)}</div>
              ) : trendingModal.posts.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground py-6">No recent spins for this record.</p>
              ) : (
                <div className="space-y-3">
                  {trendingModal.posts.map(post => (
                    <div key={post.id} className="flex items-start gap-3 py-2">
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
        <DialogContent className="sm:max-w-sm" aria-describedby="sa-location-desc">
          <DialogHeader>
            <DialogTitle className="font-heading">Set Your Location</DialogTitle>
            <p id="sa-location-desc" className="sr-only">Add your city to find nearby collectors</p>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <Input placeholder="City *" value={cityInput} onChange={e => setCityInput(e.target.value)} className="border-honey/50" data-testid="sa-location-city" autoFocus />
            <Input placeholder="State / Region (optional)" value={regionInput} onChange={e => setRegionInput(e.target.value)} className="border-honey/50" data-testid="sa-location-region" />
            <p className="text-xs text-muted-foreground">This helps us show collectors and listings near you.</p>
            <Button onClick={saveLocation} disabled={!cityInput.trim()} className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="sa-save-location-btn">
              <MapPin className="w-4 h-4 mr-1" /> Save Location
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

/* ========================== Section Renderers ========================== */

const TrendingAll = ({ data, onOpen }) => {
  if (!data || data.length === 0) return <EmptyState text="No trending records yet. Start spinning!" />;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4" data-testid="trending-grid">
      {data.map(r => (
        <button key={r.id} onClick={() => onOpen(r)} className="text-left group" data-testid={`sa-trending-${r.id}`}>
          <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm group-hover:shadow-md transition-shadow">
            <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} className="w-full h-full object-cover" />
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
  );
};

const TasteMatchAll = ({ data, navigate }) => {
  if (!data || data.length === 0) return <EmptyState text="Add more records to your collection to discover new friends." />;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="make-friends-grid">
      {data.map(u => (
        <Card key={u.id} className="p-4 border-honey/30 hover:shadow-sm transition-all" data-testid={`sa-taste-${u.id}`}>
          <div className="flex items-center gap-3">
            <Link to={`/profile/${u.username}`}>
              {u.avatar_url ? <img src={resolveImageUrl(u.avatar_url)} alt="" className="w-11 h-11 rounded-full object-cover" />
                : <div className="w-11 h-11 rounded-full bg-honey/30 flex items-center justify-center text-base font-bold text-honey-amber">{(u.username || '?')[0].toUpperCase()}</div>}
            </Link>
            <div className="flex-1 min-w-0">
              <Link to={`/profile/${u.username}`} className="text-sm font-medium hover:underline">@{u.username}</Link>
              <p className="text-xs text-honey-amber font-medium">{u.shared_records || u.shared_artists || 0} records in common</p>
            </div>
            <div className="flex gap-1.5 shrink-0">
              <Button size="sm" variant="ghost" className="h-8 w-8 p-0 rounded-full" onClick={() => navigate(`/messages?to=${u.id}`)}>
                <MessageCircle className="w-4 h-4" />
              </Button>
              <Button size="sm" className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs h-8 px-3" onClick={() => navigate(`/profile/${u.username}`)}>
                <UserPlus className="w-3 h-3 mr-1" /> Follow
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};

const TrendingCollectionsAll = ({ data, addToWantlist }) => {
  if (!data || data.length === 0) return <EmptyState text="No trending collection data right now." />;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4" data-testid="trending-collections-grid">
      {data.map((r, idx) => (
        <div key={r.discogs_id || idx} data-testid={`sa-tc-${r.discogs_id || idx}`}>
          <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm relative group">
            <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} className="w-full h-full object-cover" />
            <button
              onClick={() => addToWantlist(r.artist, r.title, r.discogs_id, r.cover_url, r.year)}
              className="absolute bottom-2 right-2 bg-white/90 hover:bg-white rounded-full p-1.5 shadow opacity-0 group-hover:opacity-100 transition-opacity"
              data-testid={`sa-add-wantlist-tc-${r.discogs_id || idx}`}>
              <Plus className="w-4 h-4 text-honey-amber" />
            </button>
          </div>
          <p className="text-sm font-medium truncate">{r.title}</p>
          <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
          {r.have > 0 && <p className="text-[10px] text-muted-foreground">owned by {r.have.toLocaleString()} collectors</p>}
        </div>
      ))}
    </div>
  );
};

const MostWantedAll = ({ data, addToWantlist }) => {
  if (!data || data.length === 0) return <EmptyState text="No wantlist data yet. Add records to your Wantlist!" />;
  return (
    <div className="space-y-1" data-testid="most-wanted-list">
      {data.map((r, idx) => (
        <div key={`${r.artist}-${r.album}-${idx}`} className="flex items-center gap-3 py-3 px-2 rounded-lg hover:bg-honey/5 transition-colors" data-testid={`sa-mw-${idx}`}>
          <span className="text-sm font-heading text-honey-amber w-8 text-right shrink-0">{idx + 1}</span>
          <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} className="w-12 h-12 rounded-lg object-cover" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{r.album}</p>
            <p className="text-xs text-muted-foreground truncate">{r.artist}{r.year ? ` (${r.year})` : ''}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs text-red-500 font-medium">{r.want_count} {r.want_count === 1 ? 'want' : 'wants'}</span>
            <button onClick={() => addToWantlist(r.artist, r.album, r.discogs_id, r.cover_url, r.year)}
              className="text-purple-600 hover:bg-purple-50 rounded-full p-1" data-testid={`sa-want-${idx}`}>
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

const NearYouAll = ({ data, navigate, onSetLocation }) => {
  if (!data) return <EmptyState text="Loading..." />;
  if (data.needs_location) {
    return (
      <Card className="p-8 text-center border-honey/30 max-w-md mx-auto" data-testid="sa-near-you-prompt">
        <MapPin className="w-12 h-12 text-honey/40 mx-auto mb-4" />
        <h3 className="font-heading text-lg mb-2">Set your location</h3>
        <p className="text-muted-foreground text-sm mb-5">Add your city to discover collectors and listings near you.</p>
        <Button onClick={onSetLocation} className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="sa-set-location-btn">
          <MapPin className="w-4 h-4 mr-1" /> Set Location
        </Button>
      </Card>
    );
  }
  const { collectors = [], listings = [] } = data;
  if (collectors.length === 0 && listings.length === 0) return <EmptyState text="No collectors found in your area yet. Spread the word!" />;
  return (
    <div data-testid="near-you-content">
      {collectors.length > 0 && (
        <>
          <h3 className="font-heading text-base text-vinyl-black mb-3">Collectors</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8" data-testid="near-you-collectors-grid">
            {collectors.map(u => (
              <Card key={u.id} className="p-4 border-honey/30 hover:shadow-sm transition-all" data-testid={`sa-nearby-${u.id}`}>
                <div className="flex items-center gap-3">
                  <Link to={`/profile/${u.username}`}>
                    {u.avatar_url ? <img src={resolveImageUrl(u.avatar_url)} alt="" className="w-10 h-10 rounded-full object-cover" />
                      : <div className="w-10 h-10 rounded-full bg-honey/30 flex items-center justify-center text-sm font-bold text-honey-amber">{(u.username || '?')[0].toUpperCase()}</div>}
                  </Link>
                  <div className="flex-1 min-w-0">
                    <Link to={`/profile/${u.username}`} className="text-sm font-medium hover:underline">@{u.username}</Link>
                    <p className="text-[11px] text-muted-foreground">{u.city}{u.region ? `, ${u.region}` : ''}</p>
                    <p className="text-[11px] text-muted-foreground">{u.collection_count} records{u.active_listings > 0 ? ` · ${u.active_listings} listings` : ''}</p>
                  </div>
                  <Button size="sm" variant="ghost" className="h-8 w-8 p-0 rounded-full shrink-0" onClick={() => navigate(`/messages?to=${u.id}`)}>
                    <MessageCircle className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
      {listings.length > 0 && (
        <>
          <h3 className="font-heading text-base text-vinyl-black mb-3">Listings near you</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4" data-testid="near-you-listings-grid">
            {listings.map(l => (
              <Card key={l.id} className="p-2 border-honey/30" data-testid={`sa-nearby-listing-${l.id}`}>
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
          </div>
        </>
      )}
    </div>
  );
};

/* ========================== Shared Components ========================== */

const EmptyState = ({ text }) => (
  <Card className="p-8 text-center border-honey/30" data-testid="see-all-empty">
    <p className="text-sm text-muted-foreground">{text}</p>
  </Card>
);

const LoadingSkeleton = ({ section }) => {
  if (section === 'most-wanted') {
    return <div className="space-y-2">{Array.from({ length: 10 }, (_, i) => <Skeleton key={i} className="h-14 w-full rounded-lg" />)}</div>;
  }
  if (section === 'make-friends' || section === 'near-you') {
    return <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{Array.from({ length: 8 }, (_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>;
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {Array.from({ length: 15 }, (_, i) => <Skeleton key={i} className="aspect-square rounded-xl" />)}
    </div>
  );
};

export default ExploreSeeAllPage;
