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
import { Disc, Users, Search, TrendingUp, Lock, Play, UserPlus, MessageCircle, MapPin, Heart, Plus, Crown, Check, Sparkles, Star, PartyPopper, Info } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import BeeAvatar from '../components/BeeAvatar';
import { resolveImageUrl } from '../utils/imageUrl';
import { ListingTypeBadge } from '../components/PostCards';
import ScrollRow from '../components/ScrollRow';
import { useVariantModal } from '../context/VariantModalContext';
import { useAPI } from '../hooks/useAPI';
import GoldGate from '../components/GoldGate';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../components/ui/tooltip';

const ROOM_TYPE_TOOLTIPS = {
  genre:     "Rooms built around musical genres. Automatically created from the most-collected genres across all Vaults on THG.",
  artist:    "Dedicated rooms for artists with 10+ collectors on THG. Gold members can also create artist rooms manually.",
  era:       "Rooms organized by decade. Automatically generated based on release years across the THG catalog.",
  vibe:      "Mood-based rooms created by Gold members. Late night spins, rainy day records, road trip vinyl. The fun ones.",
  collector: "Rooms organized by collecting style, not genre. Colored vinyl, rare pressings, picture discs. Gold members only.",
};

const COUNTRY_NAMES = {US:'United States',GB:'United Kingdom',CA:'Canada',AU:'Australia',DE:'Germany',FR:'France',JP:'Japan',NL:'Netherlands',SE:'Sweden',IT:'Italy',ES:'Spain',BR:'Brazil',MX:'Mexico',NZ:'New Zealand',IE:'Ireland',NO:'Norway',DK:'Denmark',FI:'Finland',BE:'Belgium',AT:'Austria',CH:'Switzerland',PT:'Portugal',PL:'Poland',CZ:'Czech Republic',KR:'South Korea',TW:'Taiwan',SG:'Singapore',ZA:'South Africa',AR:'Argentina',CL:'Chile',CO:'Colombia',PH:'Philippines',IN:'India',IL:'Israel',GR:'Greece',HU:'Hungary',RO:'Romania',HR:'Croatia',SK:'Slovakia',BG:'Bulgaria',RS:'Serbia',UA:'Ukraine',TH:'Thailand',MY:'Malaysia',ID:'Indonesia',VN:'Vietnam',HK:'Hong Kong',AE:'UAE',SA:'Saudi Arabia'};

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
  const [suggestedRooms, setSuggestedRooms] = useState([]);
  const { openVariantModal } = useVariantModal();
  // Track optimistic follow state per username
  const [followedUsers, setFollowedUsers] = useState(new Set());

  const handleKindaFollow = async (username) => {
    // Optimistic: mark as followed instantly
    setFollowedUsers(prev => new Set(prev).add(username));
    try {
      await axios.post(`${API}/follow/${username}`, {}, { headers: { Authorization: `Bearer ${token}` } });
      toast.success(`now following @${username}`);
    } catch {
      // Revert on failure
      setFollowedUsers(prev => { const n = new Set(prev); n.delete(username); return n; });
      toast.error('could not follow.');
    }
  };

  const handleKindaUnfollow = async (username) => {
    // Optimistic: mark as unfollowed instantly
    setFollowedUsers(prev => { const n = new Set(prev); n.delete(username); return n; });
    try {
      await axios.delete(`${API}/follow/${username}`, { headers: { Authorization: `Bearer ${token}` } });
      toast.success(`unfollowed @${username}`);
    } catch {
      // Revert on failure
      setFollowedUsers(prev => new Set(prev).add(username));
      toast.error('could not unfollow.');
    }
  };

  // BLOCK 450: SWR cache for explore sections — instant back-nav
  const { data: swrTrending } = useAPI('/explore/trending?limit=10');
  const { data: swrSuggested } = useAPI('/explore/suggested-collectors?limit=8');
  const { data: swrTrendingCollections } = useAPI('/explore/trending-in-collections?limit=12');
  const { data: swrCrownJewels } = useAPI('/explore/crown-jewels?limit=12');
  const { data: swrMostWanted } = useAPI('/explore/most-wanted?limit=20');
  const { data: swrNearYou, isLoading: swrNearLoading } = useAPI('/explore/near-you');
  // Phase 2: Honey Drop, You Might Love, Milestones
  const { data: honeyDrop } = useAPI('/honey-drop/today');
  const { data: youMightLove } = useAPI('/explore/you-might-love?limit=8');
  const { data: milestonesFeed } = useAPI('/milestones/feed?limit=10');

  // Sync SWR data into local state
  useEffect(() => { if (swrTrending) setTrending(swrTrending); }, [swrTrending]);
  useEffect(() => { if (swrSuggested) setSuggested(swrSuggested); }, [swrSuggested]);
  useEffect(() => { if (swrTrendingCollections) setTrendingCollections(swrTrendingCollections); }, [swrTrendingCollections]);
  useEffect(() => { if (swrCrownJewels) setCrownJewels(swrCrownJewels); }, [swrCrownJewels]);
  useEffect(() => { if (swrMostWanted) setMostWanted(swrMostWanted); }, [swrMostWanted]);
  useEffect(() => { if (swrNearYou) setNearYou(swrNearYou); }, [swrNearYou]);
  useEffect(() => {
    if (swrTrending && !swrNearLoading) setLoading(false);
  }, [swrTrending, swrNearLoading]);

  // Location prompt
  const [showLocationPrompt, setShowLocationPrompt] = useState(false);
  const [regionInput, setRegionInput] = useState('');

  const headers = { Authorization: `Bearer ${token}` };

  // Fetch "My Kinda People" discovery (separate from SWR sections)
  useEffect(() => {
    if (!token) return;
    axios.get(`${API}/discover/my-kinda-people`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setMyKindaPeople(r.data)).catch(() => {});
  }, [API, token]);

  // Fetch suggested Honeycomb Rooms
  useEffect(() => {
    axios.get(`${API}/rooms/suggested`).then(r => setSuggestedRooms(r.data)).catch(() => {});
  }, [API]);

  useEffect(() => {}, []);

  // Re-fetch "Your Kinda People" on every page focus/navigation to ensure followed users are excluded
  useEffect(() => {
    const refetchKinda = () => {
      if (token) {
        axios.get(`${API}/discover/my-kinda-people`, { headers: { Authorization: `Bearer ${token}` } })
          .then(r => setMyKindaPeople(r.data)).catch(() => {});
      }
    };
    window.addEventListener('focus', refetchKinda);
    return () => window.removeEventListener('focus', refetchKinda);
  }, [API, token]);

  const openTrendingModal = (record) => {
    openVariantModal({
      artist: record.artist,
      album: record.title || record.album,
      variant: record.color_variant || record.variant || '',
      discogs_id: record.discogs_id,
      cover_url: record.cover_url,
    });
  };

  const isGold = user?.golden_hive || user?.golden_hive_verified;

  // Milestone reactions (optimistic)
  const [reactedMilestones, setReactedMilestones] = useState(new Set());
  const handleMilestoneReact = async (milestoneId) => {
    setReactedMilestones(prev => new Set(prev).add(milestoneId));
    try {
      await axios.post(`${API}/milestones/${milestoneId}/react`, {}, { headers });
    } catch { /* non-fatal */ }
  };

  // Create Room dialog
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  const [createRoomForm, setCreateRoomForm] = useState({ name: '', description: '', type: 'vibe', emoji: '🍯', theme_preset: 'honey' });
  const [creatingRoom, setCreatingRoom] = useState(false);
  const THEME_SWATCHES = [
    { key: 'honey',    label: 'Honey',    bg: 'linear-gradient(135deg, #FFF3E0, #FFE0B2)' },
    { key: 'midnight', label: 'Midnight', bg: 'linear-gradient(135deg, #1A1A2E, #16213E)' },
    { key: 'forest',   label: 'Forest',   bg: 'linear-gradient(135deg, #1B4332, #2D6A4F)' },
    { key: 'rose',     label: 'Rose',     bg: 'linear-gradient(135deg, #F8D7DA, #F1AEB5)' },
    { key: 'slate',    label: 'Slate',    bg: 'linear-gradient(135deg, #2C3E50, #3D5166)' },
    { key: 'plum',     label: 'Plum',     bg: 'linear-gradient(135deg, #4A235A, #6C3483)' },
  ];
  const handleCreateRoom = async () => {
    if (!createRoomForm.name.trim()) { toast.error('Room name is required.'); return; }
    setCreatingRoom(true);
    try {
      await axios.post(`${API}/rooms/create`, createRoomForm, { headers });
      toast.success('Room submitted for review! We\'ll notify you when it goes live.');
      setShowCreateRoom(false);
      setCreateRoomForm({ name: '', description: '', type: 'vibe', emoji: '🍯', theme_preset: 'honey' });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Could not create room.';
      if (err.response?.headers?.['x-gold-required']) {
        navigate('/gold');
      } else {
        toast.error(msg);
      }
    } finally {
      setCreatingRoom(false);
    }
  };

  // Dream Catcher — intent modal state
  const [dreamTarget, setDreamTarget] = useState(null); // { artist, album, discogs_id, cover_url, year }
  const [addedIds, setAddedIds] = useState(new Set());

  const openDreamCatcher = (artist, album, discogs_id, cover_url, year) => {
    setDreamTarget({ artist, album, discogs_id, cover_url, year });
  };

  const addToSeekingList = async (intent) => {
    if (!dreamTarget) return;
    const { artist, album, discogs_id, cover_url, year } = dreamTarget;
    try {
      await axios.post(`${API}/composer/iso`, {
        artist, album, discogs_id, cover_url, year,
        intent: intent || 'seeking',
      }, { headers });
      toast.success(intent === 'dreaming' ? 'Added to your Dream List.' : 'ISO posted to the Hive!');
      setAddedIds(prev => new Set(prev).add(discogs_id));
      setDreamTarget(null);
    } catch (err) {
      if (err.response?.status === 409) { toast.info('Already on your Dream List.'); setAddedIds(prev => new Set(prev).add(discogs_id)); }
      else toast.error('Could not add. Try again.');
      setDreamTarget(null);
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
      <div className="max-w-4xl mx-auto px-4 py-8 pt-3 md:pt-2">
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
      <div className="max-w-4xl mx-auto px-4 py-8 pt-3 md:pt-2">
        <Skeleton className="h-8 w-40 mb-6" />
        <Skeleton className="h-6 w-48 mb-3" />
        <div className="flex gap-3 overflow-hidden mb-8">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-48 w-36 rounded-xl shrink-0" />)}</div>
        <Skeleton className="h-6 w-32 mb-3" />
        <div className="grid grid-cols-2 gap-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-24 md:pb-8 honey-fade-in" data-testid="explore-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-1">Nectar</h1>
      <p className="text-sm text-muted-foreground mb-8">what the hive is into right now.</p>

      {/* 0. The Honey Drop — today's featured record */}
      {honeyDrop?.record && (
        <ExploreSection icon={<span className="text-base">🍯</span>} title="The Honey Drop" testId="honey-drop-section" seeAllTo={null}>
          <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">Today's featured record from the Hive.</p>
          <div
            className="relative rounded-2xl overflow-hidden cursor-pointer group"
            style={{ minHeight: 200 }}
            onClick={() => honeyDrop.record.discogs_id && navigate(`/variant/${honeyDrop.record.discogs_id}`)}
            data-testid="honey-drop-card"
          >
            {/* Banner art */}
            {honeyDrop.record.cover_url && (
              <div className="absolute inset-0">
                <AlbumArt
                  src={honeyDrop.record.cover_url}
                  alt={honeyDrop.record.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0" style={{ background: 'linear-gradient(to top, rgba(20,10,0,0.88) 40%, rgba(0,0,0,0.2) 100%)' }} />
              </div>
            )}
            {!honeyDrop.record.cover_url && (
              <div className="absolute inset-0 bg-honey/20" />
            )}
            {/* Overlay content */}
            <div className="relative z-10 p-5 flex flex-col justify-end" style={{ minHeight: 200 }}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-white font-heading text-xl font-bold leading-tight mb-0.5">{honeyDrop.record.title}</p>
                  <p className="text-white/80 text-sm">{honeyDrop.record.artist}</p>
                  {honeyDrop.blurb && <p className="text-white/70 text-xs mt-1 italic max-w-xs">{honeyDrop.blurb}</p>}
                </div>
                <Button
                  size="sm"
                  className="shrink-0 rounded-full text-[#2A1A06] font-bold"
                  style={{ background: '#E8A820' }}
                  onClick={(e) => { e.stopPropagation(); if (navigator.share) { navigator.share({ title: `${honeyDrop.record.title} on The Honey Groove`, url: window.location.origin }); } else { navigator.clipboard.writeText(window.location.origin); toast.success('Link copied!'); } }}
                >
                  Share
                </Button>
              </div>
              {/* Stats row */}
              <div className="flex gap-4 mt-3 text-xs text-white/60">
                {honeyDrop.ownership_count > 0 && <span>🎵 {honeyDrop.ownership_count} members own this</span>}
                {honeyDrop.estimated_value > 0 && <span>Est. ${honeyDrop.estimated_value >= 1000 ? (honeyDrop.estimated_value / 1000).toFixed(1) + 'k' : honeyDrop.estimated_value.toFixed(0)}</span>}
              </div>
              {/* Gold hint */}
              {!isGold && (
                <p className="text-[10px] text-[#E8A820] mt-2">
                  <Crown className="inline w-3 h-3 mr-0.5" />
                  Gold members get price alerts when this drops on Discogs
                </p>
              )}
            </div>
          </div>
        </ExploreSection>
      )}

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
            <p className="font-heading text-lg text-vinyl-black mb-1">You've reached the edge of the hive.</p>
            <p className="text-sm text-muted-foreground max-w-xs mx-auto">Check back soon for more fresh collectors.</p>
          </div>
        ) : (
          <ScrollRow>
            {myKindaPeople.map(p => {
              const isFollowed = followedUsers.has(p.username);
              return (
              <div key={p.username} className="flex-shrink-0 w-40 group" data-testid={`kinda-${p.username}`}>
                <Card className={`p-3 border-honey/30 hover:shadow-honey transition-all text-center ${p.follows_me ? 'ring-1 ring-honey/40' : ''}`}>
                  <Link to={`/profile/${p.username}?tab=in-common`}>
                    <div className="w-14 h-14 mx-auto mb-2">
                      <BeeAvatar user={p} className="h-14 w-14" />
                    </div>
                    <p className="text-sm font-medium truncate hover:underline" style={{ color: '#C8861A' }}>@{p.username}</p>
                    {p.follows_me && !isFollowed && (
                      <span className="inline-block text-[10px] font-medium mt-0.5 px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(218,165,32,0.12)', color: '#C8861A' }} data-testid={`follows-you-${p.username}`}>Follows you</span>
                    )}
                    <p className="text-sm font-semibold mt-0.5" style={{ color: '#C8861A' }}>{p.common_count || 0} {(p.common_count || 0) === 1 ? 'record' : 'records'} in common</p>
                    {p.shared_covers?.length > 0 && (
                      <div className="flex justify-center gap-1 mt-2">
                        {p.shared_covers.slice(0, 3).map((c, i) => (
                          <div key={i} className="w-10 h-10 rounded-md overflow-hidden bg-vinyl-black">
                            <AlbumArt src={c.cover_url} alt={c.title} className="w-full h-full object-cover" isUnofficial={c.is_unofficial} />
                          </div>
                        ))}
                      </div>
                    )}
                  </Link>
                  {isFollowed ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => { e.preventDefault(); handleKindaUnfollow(p.username); }}
                      className="mt-2 w-full text-xs rounded-full border-transparent text-white hover:opacity-90 transition-all"
                      style={{ background: '#C8861A' }}
                      data-testid={`following-btn-${p.username}`}
                    >
                      <Check className="w-3 h-3 mr-1" /> Following
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => { e.preventDefault(); handleKindaFollow(p.username); }}
                      className="mt-2 w-full text-xs rounded-full border-honey/40 text-[#C8861A] hover:bg-honey hover:text-vinyl-black transition-all"
                      data-testid={`follow-btn-${p.username}`}
                    >
                      <UserPlus className="w-3 h-3 mr-1" /> {p.follows_me ? 'Follow Back' : 'Follow'}
                    </Button>
                  )}
                </Card>
              </div>
              );
            })}
          </ScrollRow>
        )}
      </section>

      {/* Collector Bingo — hidden until feature is ready */}

      {/* 2. Honeycomb Rooms */}
      <ExploreSection icon={<span className="text-base">🍯</span>} title="Honeycomb Rooms" testId="rooms-section" seeAllTo={null}>
        <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">Join themed spaces for your era, genre, or favorite artist.</p>
        {suggestedRooms.length === 0 ? (
          <EmptyCard text="Rooms coming soon — check back shortly!" />
        ) : (
          <div className="flex flex-wrap justify-center gap-3" data-testid="rooms-grid">
            {suggestedRooms.map(room => (
              <HexRoomCard key={room.slug} room={room} onClick={() => navigate(`/nectar/rooms/${room.slug}`)} />
            ))}
          </div>
        )}
        {/* Create a Room CTA */}
        <div className="mt-4 flex justify-center">
          <GoldGate
            isGold={isGold}
            hint="Gold members can create Vibe and Collector rooms"
            compact
          >
            <Button
              variant="outline"
              size="sm"
              className="rounded-full border-honey/50 text-honey-amber hover:bg-honey/10"
              onClick={() => setShowCreateRoom(true)}
              data-testid="create-room-btn"
            >
              <Plus className="w-3 h-3 mr-1" /> Create a Room
            </Button>
          </GoldGate>
        </div>
      </ExploreSection>

      {/* 1. Hot Right Now */}
      <ExploreSection icon={<TrendingUp className="w-4 h-4 text-honey-amber" />} title="Hot Right Now" testId="trending-section" seeAllTo="/nectar/trending">
        <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">What Hive members have been spinning.</p>
        {trending.length === 0 ? (
          <EmptyCard text="No trending records yet. Start spinning!" />
        ) : (
          <ScrollRow>
            {trending.map((r, idx) => {
              const card = (
                <button key={r.id} onClick={() => openTrendingModal(r)}
                  className="flex-shrink-0 w-36 text-left group" data-testid={`trending-${r.id}`}>
                  <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm group-hover:shadow-md transition-shadow relative">
                    <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} artist={r.artist} title={r.title} className="w-full h-full object-cover" isUnofficial={r.is_unofficial} />
                    {idx === 0 && (
                      <span className="absolute top-2 left-2 w-6 h-6 flex items-center justify-center rounded-full text-[10px] font-bold text-white" style={{ background: '#DAA520' }} data-testid="rank-badge-1">#1</span>
                    )}
                    {(idx === 1 || idx === 2) && (
                      <span className="absolute top-2 left-2 w-6 h-6 flex items-center justify-center rounded-full text-[10px] font-bold bg-gray-200 text-gray-700" data-testid={`rank-badge-${idx + 1}`}>#{idx + 1}</span>
                    )}
                  </div>
                  <p className="text-sm font-medium truncate">{r.title}</p>
                  <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Play className="w-3 h-3 text-honey-amber" />
                    <span className="text-xs text-honey-amber font-medium">{r.trending_spins} {r.trending_spins === 1 ? 'spin' : 'spins'}</span>
                  </div>
                </button>
              );
              if (idx >= 5) {
                return (
                  <div key={r.id} className="flex-shrink-0 w-36">
                    <GoldGate isGold={isGold} compact hint="See the full Hot Right Now chart">
                      {card}
                    </GoldGate>
                  </div>
                );
              }
              return card;
            })}
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
              <div key={r.discogs_id || idx} className="flex-shrink-0 w-40">
              <GoldGate isGold={isGold || idx < 3} compact hint="Gold members see the full Crown Jewels vault">
              <button onClick={() => navigate(`/variant/${r.discogs_id}`)} className="w-full text-left group border-2 border-[#DAA520] rounded-xl p-1 shadow-[0_0_12px_rgba(218,165,32,0.2)]" data-testid={`crown-jewel-${r.discogs_id || idx}`}>
                <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm relative group-hover:shadow-md transition-shadow">
                  <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} artist={r.artist} title={r.title} className="w-full h-full object-cover" isUnofficial={r.is_unofficial} />
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
                    onClick={(e) => { e.stopPropagation(); openDreamCatcher(r.artist, r.title, r.discogs_id, r.cover_url, r.year); }}
                    className={`absolute bottom-2 right-2 rounded-full p-1.5 shadow transition-opacity cursor-pointer ${addedIds.has(r.discogs_id) ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
                    style={addedIds.has(r.discogs_id) ? { background: 'linear-gradient(135deg, #FFB300, #FFA000)' } : { background: 'rgba(255,255,255,0.9)' }}
                    data-testid={`add-wantlist-cj-${r.discogs_id || idx}`}>
                    {addedIds.has(r.discogs_id) ? <Check className="w-4 h-4 text-white" /> : <Plus className="w-4 h-4 text-honey-amber" />}
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
              </GoldGate>
              </div>
            ))}
          </ScrollRow>
        )}
      </ExploreSection>

      {/* 5. You Might Love */}
      <ExploreSection icon={<Sparkles className="w-4 h-4 text-honey-amber" />} title="You Might Love" testId="you-might-love-section" seeAllTo={null}>
        <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">Picked for you based on your collection.</p>
        {!youMightLove || youMightLove.length === 0 ? (
          <EmptyCard text="Add more records to your collection to get personalized picks!" />
        ) : (
          <ScrollRow>
            {youMightLove.map((r, idx) => (
              <div key={r.discogs_id || idx} className="flex-shrink-0 w-36">
                <GoldGate isGold={isGold || !r.gold_only} compact hint="Unlock all recommendations with Gold">
                  <button
                    onClick={() => r.discogs_id && openTrendingModal({ ...r, title: r.title || r.album })}
                    className="w-full text-left group"
                    data-testid={`you-might-love-${idx}`}
                  >
                    <div className="aspect-square rounded-xl overflow-hidden bg-honey/10 mb-2 shadow-sm group-hover:shadow-md transition-shadow">
                      <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title}`} className="w-full h-full object-cover" isUnofficial={r.is_unofficial} />
                    </div>
                    <p className="text-sm font-medium truncate">{r.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{r.artist}</p>
                    {r.reason && (
                      <p className="text-[10px] text-honey-amber mt-0.5 leading-tight">{r.reason}</p>
                    )}
                  </button>
                </GoldGate>
              </div>
            ))}
          </ScrollRow>
        )}
      </ExploreSection>

      {/* 4. The Buzz Board */}
      <ExploreSection icon={<Heart className="w-4 h-4 text-red-400" />} title="The Buzz Board" testId="most-wanted-section" seeAllTo="/nectar/most-wanted">
        <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">Hive members have their eyes on these records.</p>
        {mostWanted.length === 0 ? (
          <EmptyCard text="No Dream List data yet. Add records to your Dream List!" />
        ) : (
          <div className="space-y-2">
            {mostWanted.map((r, idx) => {
              const row = (
                <button key={`${r.artist}-${r.album}`} onClick={() => openTrendingModal({ ...r, title: r.album })}
                  className="flex items-center gap-3 py-2 px-1 rounded-lg hover:bg-honey/5 transition-colors w-full text-left" data-testid={`most-wanted-${idx}`}>
                  <span className="text-sm font-heading text-honey-amber w-6 text-right shrink-0">{idx + 1}</span>
                  <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} className="w-10 h-10 rounded-lg object-cover" isUnofficial={r.is_unofficial} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{r.album}</p>
                    <p className="text-xs text-muted-foreground truncate">{r.artist}{r.year ? ` (${r.year})` : ''}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-red-500 font-medium">{r.want_count} {r.want_count === 1 ? 'want' : 'wants'}</span>
                    <span onClick={(e) => { e.stopPropagation(); openDreamCatcher(r.artist, r.album, r.discogs_id, r.cover_url, r.year); }}
                      className="hover:bg-honey/10 rounded-full p-1 cursor-pointer" data-testid={`want-${idx}`}
                      style={addedIds.has(r.discogs_id) ? { background: 'linear-gradient(135deg, #FFB300, #FFA000)', borderRadius: '9999px' } : {}}>
                      {addedIds.has(r.discogs_id) ? <Check className="w-4 h-4 text-white" /> : <Plus className="w-4 h-4 text-honey-amber" />}
                    </span>
                  </div>
                </button>
              );
              if (idx >= 5) {
                return (
                  <GoldGate key={`${r.artist}-${r.album}`} isGold={isGold} compact hint="See the full Buzz Board with Gold">
                    {row}
                  </GoldGate>
                );
              }
              return row;
            })}
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
                      <p className="text-[10px] text-muted-foreground">{u.country === 'US' ? `${u.region || ''}, USA` : (COUNTRY_NAMES[u.country] || u.country || u.region || '')}</p>
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
                        {(l.photo_urls?.[0] || l.cover_url) ? <AlbumArt src={l.photo_urls?.[0] || l.cover_url} alt={`${l.artist} ${l.album} vinyl record`} className="w-full h-full object-cover" isUnofficial={l.is_unofficial} />
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

      {/* 8. Collector Milestones */}
      {milestonesFeed && milestonesFeed.length > 0 && (
        <ExploreSection icon={<Star className="w-4 h-4 text-honey-amber" />} title="Collector Milestones" testId="milestones-section" seeAllTo={null}>
          <p className="text-xs text-muted-foreground italic -mt-2 mb-3 pl-1">Celebrating the Hive's achievements.</p>
          <div className="space-y-2">
            {milestonesFeed.map(m => (
              <div
                key={m.id}
                className="flex items-center gap-3 p-3 rounded-xl border"
                style={{ background: '#FFF8E1', borderColor: 'rgba(218,165,32,0.3)' }}
                data-testid={`milestone-${m.id}`}
              >
                <span className="text-2xl shrink-0">{m.emoji}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">
                    <Link to={`/profile/${m.username}`} className="font-semibold" style={{ color: '#C8861A' }}>@{m.username}</Link>
                    {' '}reached <span className="font-semibold">{m.label}</span> 🎉
                  </p>
                </div>
                <button
                  onClick={() => handleMilestoneReact(m.id)}
                  className="shrink-0 text-xs rounded-full px-3 py-1 font-medium transition-all"
                  style={
                    reactedMilestones.has(m.id)
                      ? { background: 'linear-gradient(135deg, #FFB300, #FFA000)', color: '#fff' }
                      : { background: 'rgba(218,165,32,0.15)', color: '#C8861A' }
                  }
                  data-testid={`milestone-react-${m.id}`}
                >
                  {reactedMilestones.has(m.id) ? `🎉 ${(m.react_count || 0) + 1}` : `🎉 Congrats${m.react_count > 0 ? ` · ${m.react_count}` : ''}`}
                </button>
              </div>
            ))}
          </div>
        </ExploreSection>
      )}

      {/* Dream Catcher — Intent Selection Modal */}
      <Dialog open={!!dreamTarget} onOpenChange={(open) => !open && setDreamTarget(null)}>
        <DialogContent className="sm:max-w-xs" aria-describedby="dream-catcher-desc">
          <DialogHeader>
            <DialogTitle className="font-heading text-center" style={{ color: '#D98C2F' }}>
              Add to your list
            </DialogTitle>
            <p id="dream-catcher-desc" className="text-sm text-center text-muted-foreground mt-1">
              {dreamTarget?.title || dreamTarget?.album} by {dreamTarget?.artist}
            </p>
          </DialogHeader>
          <div className="flex flex-col gap-3 pt-3" data-testid="dream-catcher-modal">
            <Button
              onClick={() => addToSeekingList('dreaming')}
              className="w-full rounded-full py-3 text-sm font-semibold"
              style={{ background: '#FFF8E1', color: '#3E2723', border: '2px solid rgba(255,179,0,0.3)' }}
              data-testid="intent-dreaming"
            >
              Just Dreaming
            </Button>
            <Button
              onClick={() => addToSeekingList('seeking')}
              className="w-full rounded-full py-3 text-sm font-semibold text-white"
              style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)' }}
              data-testid="intent-seeking"
            >
              Actively Seeking
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Room Dialog */}
      <Dialog open={showCreateRoom} onOpenChange={setShowCreateRoom}>
        <DialogContent className="sm:max-w-sm" aria-describedby="create-room-desc">
          <DialogHeader>
            <DialogTitle className="font-heading" style={{ color: '#D98C2F' }}>Create a Room</DialogTitle>
            <p id="create-room-desc" className="text-xs text-muted-foreground mt-1">Vibe and Collector rooms are reviewed before going live.</p>
          </DialogHeader>
          <div className="space-y-3 pt-2">
            <Input
              placeholder="Room name *"
              value={createRoomForm.name}
              onChange={e => setCreateRoomForm(f => ({ ...f, name: e.target.value }))}
              className="border-honey/50"
              maxLength={60}
              data-testid="create-room-name"
            />
            <Input
              placeholder="Description (optional)"
              value={createRoomForm.description}
              onChange={e => setCreateRoomForm(f => ({ ...f, description: e.target.value }))}
              className="border-honey/50"
              maxLength={280}
              data-testid="create-room-desc-input"
            />
            <TooltipProvider delayDuration={300}>
              <div className="flex gap-2">
                {['vibe', 'collector'].map(t => (
                  <Tooltip key={t}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => setCreateRoomForm(f => ({ ...f, type: t }))}
                        className="flex-1 rounded-full py-1.5 text-xs font-semibold border transition-all capitalize"
                        style={createRoomForm.type === t
                          ? { background: '#E8A820', color: '#2A1A06', borderColor: '#E8A820' }
                          : { background: 'transparent', color: '#C8861A', borderColor: 'rgba(218,165,32,0.4)' }
                        }
                        data-testid={`room-type-${t}`}
                      >
                        {t}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="max-w-[180px] text-center text-xs leading-snug">
                      {ROOM_TYPE_TOOLTIPS[t]}
                    </TooltipContent>
                  </Tooltip>
                ))}
              </div>
            </TooltipProvider>
            {/* Emoji picker */}
            <div className="flex gap-2 flex-wrap">
              {['🍯','🎸','🎷','🎺','🥁','🎻','🎹','🎵','🎶','🌙'].map(em => (
                <button
                  key={em}
                  onClick={() => setCreateRoomForm(f => ({ ...f, emoji: em }))}
                  className="w-9 h-9 rounded-lg text-lg flex items-center justify-center transition-all"
                  style={createRoomForm.emoji === em
                    ? { background: 'rgba(218,165,32,0.25)', outline: '2px solid #E8A820' }
                    : { background: 'rgba(218,165,32,0.08)' }
                  }
                >
                  {em}
                </button>
              ))}
            </div>
            {/* Theme swatches */}
            <div>
              <p className="text-xs text-muted-foreground mb-2">Theme</p>
              <div className="flex gap-2 flex-wrap">
                {THEME_SWATCHES.map(sw => (
                  <button
                    key={sw.key}
                    onClick={() => setCreateRoomForm(f => ({ ...f, theme_preset: sw.key }))}
                    className="w-9 h-9 rounded-full transition-all"
                    style={{
                      background: sw.bg,
                      outline: createRoomForm.theme_preset === sw.key ? '3px solid #E8A820' : '2px solid rgba(0,0,0,0.1)',
                    }}
                    title={sw.label}
                    data-testid={`theme-swatch-${sw.key}`}
                  />
                ))}
              </div>
            </div>
            <Button
              onClick={handleCreateRoom}
              disabled={creatingRoom || !createRoomForm.name.trim()}
              className="w-full rounded-full font-bold text-[#2A1A06]"
              style={{ background: '#E8A820' }}
              data-testid="create-room-submit"
            >
              {creatingRoom ? 'Submitting…' : 'Submit for Review'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

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

const HexRoomCard = ({ room, onClick }) => {
  const tooltipText = ROOM_TYPE_TOOLTIPS[room.type] || null;
  return (
    <TooltipProvider delayDuration={400}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            onClick={onClick}
            style={{
              clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
              background: room.theme?.bgGradient || '#FFF3E0',
              width: 120,
              height: 138,
              cursor: 'pointer',
            }}
            className="flex flex-col items-center justify-center transition-transform hover:scale-105"
            data-testid={`room-hex-${room.slug}`}
          >
            <span className="text-3xl">{room.emoji}</span>
            <span className="text-xs font-semibold text-center mt-1 px-2" style={{ color: room.theme?.textColor || '#2A1A06' }}>
              {room.name}
            </span>
            {room.type && (
              <span className="text-[9px] font-medium capitalize mt-0.5 opacity-60" style={{ color: room.theme?.textColor || '#2A1A06' }}>
                {room.type}
              </span>
            )}
          </div>
        </TooltipTrigger>
        {tooltipText && (
          <TooltipContent side="bottom" className="max-w-[200px] text-center text-xs leading-snug">
            {tooltipText}
          </TooltipContent>
        )}
      </Tooltip>
    </TooltipProvider>
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
