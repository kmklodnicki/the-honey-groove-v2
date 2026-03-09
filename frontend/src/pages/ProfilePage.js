import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '../components/ui/dialog';
import { Disc, Edit, UserPlus, UserMinus, Loader2, Search, Play, CheckCircle2, ArrowRightLeft, CreditCard, Star, MessageCircle, MapPin, ShoppingBag, Flag, Sparkles, Eye, X, Cloud } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { FollowListModal } from '../components/FollowList';
import { usePageTitle } from '../hooks/usePageTitle';
import { MoodBoardTab } from '../components/MoodBoardTab';
import ReportModal from '../components/ReportModal';
import { resolveImageUrl } from '../utils/imageUrl';
import AlbumArt from '../components/AlbumArt';
import { countryFlag } from '../utils/countryFlag';
import { TitleBadge } from '../components/TitleBadge';
import { TagPill } from '../components/PostCards';

const ProfilePage = () => {
  usePageTitle('Profile');
  const { username } = useParams();
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [records, setRecords] = useState([]);
  const [spins, setSpins] = useState([]);
  const [isos, setIsos] = useState([]);
  const [trades, setTrades] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [followLoading, setFollowLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('collection');
  const [followListType, setFollowListType] = useState(null);
  const [stripeStatus, setStripeStatus] = useState(null);
  const [stripeLoading, setStripeLoading] = useState(false);
  const [ratings, setRatings] = useState(null);
  const [collectionValue, setCollectionValue] = useState(null);
  const [promptStreak, setPromptStreak] = useState(null);
  const [reportSellerOpen, setReportSellerOpen] = useState(false);
  const [tasteMatch, setTasteMatch] = useState(null);
  const [tasteLoading, setTasteLoading] = useState(false);
  const [commonGroundOpen, setCommonGroundOpen] = useState(false);
  const [showCommonOnly, setShowCommonOnly] = useState(false);
  const [myRecordDiscogs, setMyRecordDiscogs] = useState(new Set());
  const [dreamingItems, setDreamingItems] = useState([]);
  const [dreamValue, setDreamValue] = useState(null);

  const isOwnProfile = user?.username === username;

  const fetchProfile = useCallback(async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const [profileRes, recordsRes] = await Promise.all([
        axios.get(`${API}/users/${username}`, { headers }),
        axios.get(`${API}/users/${username}/records`, { headers }),
      ]);
      setProfile(profileRes.data);
      setRecords(recordsRes.data);

      if (token && !isOwnProfile) {
        const followRes = await axios.get(`${API}/follow/check/${username}`, { headers: { Authorization: `Bearer ${token}` }});
        setIsFollowing(followRes.data.is_following);
      }
      if (token && isOwnProfile) {
        axios.get(`${API}/stripe/status`, { headers: { Authorization: `Bearer ${token}` }}).then(r => setStripeStatus(r.data)).catch(() => {});
      }
      axios.get(`${API}/users/${username}/ratings`).then(r => setRatings(r.data)).catch(() => {});
      axios.get(`${API}/valuation/collection/${username}`).then(r => setCollectionValue(r.data)).catch(() => {});
      axios.get(`${API}/prompts/streak/${username}`).then(r => setPromptStreak(r.data)).catch(() => {});
      axios.get(`${API}/valuation/wishlist/${username}`).then(r => setDreamValue(r.data)).catch(() => {});

      // Fetch taste match for other users
      if (token && !isOwnProfile) {
        setTasteLoading(true);
        axios.get(`${API}/users/${username}/taste-match`, { headers: { Authorization: `Bearer ${token}` }})
          .then(r => setTasteMatch(r.data))
          .catch(() => {})
          .finally(() => setTasteLoading(false));
        // Fetch own collection discogs IDs for "In Your Collection" badges
        axios.get(`${API}/records`, { headers: { Authorization: `Bearer ${token}` }})
          .then(r => setMyRecordDiscogs(new Set(r.data.filter(rec => rec.discogs_id).map(rec => rec.discogs_id))))
          .catch(() => {});
      }
    } catch {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  }, [API, token, username, isOwnProfile]);

  useEffect(() => {
    setLoading(true);
    setActiveTab('collection');
    setTasteMatch(null);
    setShowCommonOnly(false);
    setCommonGroundOpen(false);
    setDreamingItems([]);
    setDreamValue(null);
    fetchProfile();
  }, [fetchProfile]);

  // Lazy-load tab data
  useEffect(() => {
    if (activeTab === 'spinning' && spins.length === 0) {
      axios.get(`${API}/users/${username}/spins`)
        .then(r => setSpins(r.data))
        .catch(() => {});
    }
    if (activeTab === 'iso' && isos.length === 0) {
      axios.get(`${API}/users/${username}/iso`)
        .then(r => setIsos(r.data))
        .catch(() => {});
    }
    if (activeTab === 'trades' && trades.length === 0) {
      axios.get(`${API}/users/${username}/trades`)
        .then(r => setTrades(r.data))
        .catch(() => {});
    }
    if (activeTab === 'dreaming' && dreamingItems.length === 0) {
      axios.get(`${API}/users/${username}/dreaming`)
        .then(r => setDreamingItems(r.data))
        .catch(() => {});
    }
  }, [activeTab, API, username, spins.length, isos.length, trades.length, dreamingItems.length]);

  const handleFollow = async () => {
    setFollowLoading(true);
    try {
      if (isFollowing) {
        await axios.delete(`${API}/follow/${username}`, { headers: { Authorization: `Bearer ${token}` }});
        setIsFollowing(false);
        setProfile(p => p ? { ...p, followers_count: p.followers_count - 1 } : p);
      } else {
        await axios.post(`${API}/follow/${username}`, {}, { headers: { Authorization: `Bearer ${token}` }});
        setIsFollowing(true);
        setProfile(p => p ? { ...p, followers_count: p.followers_count + 1 } : p);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    } finally {
      setFollowLoading(false);
    }
  };

  const handleMarkFound = async (isoId) => {
    try {
      await axios.put(`${API}/iso/${isoId}/found`, {}, { headers: { Authorization: `Bearer ${token}` }});
      setIsos(prev => prev.map(i => i.id === isoId ? { ...i, status: 'FOUND' } : i));
      toast.success('marked as found.');
    } catch { toast.error('something went wrong.'); }
  };

  const handleDeleteIso = async (isoId) => {
    try {
      await axios.delete(`${API}/iso/${isoId}`, { headers: { Authorization: `Bearer ${token}` }});
      setIsos(prev => prev.filter(i => i.id !== isoId));
      toast.success('iso removed.');
    } catch { toast.error('something went wrong.'); }
  };

  const handleStripeConnect = async () => {
    setStripeLoading(true);
    try {
      const resp = await axios.post(`${API}/stripe/connect`, {}, { headers: { Authorization: `Bearer ${token}` }});
      if (resp.data.url) window.location.href = resp.data.url;
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setStripeLoading(false); }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24">
        <Skeleton className="h-48 w-full rounded-xl mb-6" />
        <Skeleton className="h-12 w-64 mb-4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24 text-center">
        <h2 className="font-heading text-2xl mb-2">User not found</h2>
        <p className="text-muted-foreground">@{username} doesn't exist.</p>
      </div>
    );
  }

  const firstLetter = profile.username?.charAt(0).toUpperCase() || '?';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8" data-testid="profile-page">
      {/* Profile Header */}
      <Card className="p-6 border-honey/30 mb-6" style={{ backgroundColor: '#FAF6EE' }}>
        <div className="flex flex-col sm:flex-row items-start gap-6">
          <Avatar className="h-24 w-24 border-4 border-honey/30">
            {profile.avatar_url && <AvatarImage src={resolveImageUrl(profile.avatar_url)} />}
            <AvatarFallback className="bg-honey-soft text-vinyl-black text-3xl font-heading">
              {firstLetter}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1" style={{ minWidth: 0 }}>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="font-heading text-2xl break-words" style={{ flexShrink: 1, minWidth: 0 }} data-testid="profile-username">@{profile.username}{profile.country && <span className="ml-1.5" data-testid="profile-country-flag">{countryFlag(profile.country)}</span>}</h1>
              {profile.title_label && <TitleBadge label={profile.title_label} />}
              {promptStreak && promptStreak.streak > 0 && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-700 text-xs font-bold" data-testid="profile-streak-pill">
                  {promptStreak.streak} day streak
                </span>
              )}
              {!isOwnProfile && token && (
                <>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleFollow}
                    disabled={followLoading}
                    className={`rounded-full ${isFollowing ? 'bg-white border border-vinyl-black/30 text-vinyl-black hover:bg-red-50 hover:text-red-600' : 'bg-honey text-vinyl-black hover:bg-honey-amber'}`}
                    data-testid="follow-btn"
                  >
                    {followLoading ? <Loader2 className="w-4 h-4 animate-spin" /> :
                      isFollowing ? <><UserMinus className="w-4 h-4 mr-1" />Following</> :
                      <><UserPlus className="w-4 h-4 mr-1" />Follow</>
                    }
                  </Button>
                  <Button
                    size="sm" variant="outline"
                    onClick={() => navigate(`/messages?to=${profile.id}`)}
                    className="rounded-full border-vinyl-black/30"
                    data-testid="profile-message-btn"
                  >
                    <MessageCircle className="w-4 h-4 mr-1" /> Message
                  </Button>
                  <Button
                    size="sm" variant="ghost"
                    onClick={() => setReportSellerOpen(true)}
                    className="rounded-full text-muted-foreground/60 hover:text-red-500"
                    data-testid="report-seller-btn"
                  >
                    <Flag className="w-3 h-3" />
                  </Button>
                </div>
                {/* Taste Match Pill (BLOCK 40.2) */}
                {tasteMatch && !tasteLoading && (
                  <button
                    onClick={() => setCommonGroundOpen(true)}
                    className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold transition-all hover:scale-105 group relative"
                    style={{ background: 'linear-gradient(135deg, #FFD700 0%, #FDB931 100%)', color: '#3E2723', border: '1px solid rgba(253,185,49,0.3)', boxShadow: '0 2px 10px rgba(253,185,49,0.25)' }}
                    data-testid="taste-match-pill"
                  >
                    <Sparkles className="w-3.5 h-3.5" style={{ color: '#C8861A' }} />
                    {tasteMatch.score}% Taste Match
                    {tasteMatch.label && <span className="ml-1">· {tasteMatch.label}</span>}
                    {profile.founding_member && (
                      <span className="absolute -bottom-8 left-0 right-0 text-center text-[10px] font-normal italic text-amber-600 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none" data-testid="founder-taste-tooltip">
                        Founder Taste: Compare your collection to the creator of the Groove.
                      </span>
                    )}
                  </button>
                )}
                </>
              )}
              {isOwnProfile && (
                <Link to="/settings">
                  <Button variant="outline" size="sm" className="rounded-full gap-1">
                    <Edit className="w-3 h-3" /> Edit
                  </Button>
                </Link>
              )}
            </div>
            {profile.bio && <p className="text-sm text-muted-foreground mt-1">{profile.bio}</p>}
            {profile.setup && (
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1" data-testid="profile-setup">
                <Disc className="w-3 h-3" /> {profile.setup}
              </p>
            )}
            {(profile.location || profile.city || profile.region) && (
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <MapPin className="w-3 h-3" /> {profile.location || `${profile.city || ''}${profile.region ? `, ${profile.region}` : ''}`}
              </p>
            )}
            {profile.favorite_genre && (
              <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 text-xs font-medium" data-testid="profile-genre">
                {profile.favorite_genre}
              </span>
            )}
            {profile.founding_member && (
              <div className="mt-1.5 inline-block" data-testid="founding-badge">
                <span className="italic text-xs" style={{ color: '#C8861A', fontFamily: '"DM Serif Display", serif' }}>
                  founding member
                </span>
              </div>
            )}

            {/* Social links */}
            {(profile.instagram_username || profile.tiktok_username) && (
              <div className="flex items-center gap-3 mt-2" data-testid="profile-social-links">
                {profile.instagram_username && (
                  <a href={`https://instagram.com/${profile.instagram_username}`} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-pink-500 transition-colors"
                    data-testid="profile-instagram-link">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
                    @{profile.instagram_username}
                  </a>
                )}
                {profile.tiktok_username && (
                  <a href={`https://tiktok.com/@${profile.tiktok_username}`} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-vinyl-black transition-colors"
                    data-testid="profile-tiktok-link">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 00-.79-.05A6.34 6.34 0 003.15 15.2a6.34 6.34 0 0010.86 4.46V13.2a8.27 8.27 0 005.58 2.17V11.9a4.83 4.83 0 01-3.77-1.44V6.69h3.77z"/></svg>
                    @{profile.tiktok_username}
                  </a>
                )}
              </div>
            )}

            {/* Stats - Social first, then collection */}
            <div className="mt-4 space-y-3" data-testid="profile-stats">
              {/* Row 1: Following / Followers — same horizontal line */}
              <div className="flex flex-row items-center justify-around sm:justify-start sm:gap-8">
                <button onClick={() => setFollowListType('following')} className="hover:opacity-70 transition text-center" data-testid="following-stat">
                  <span className="font-heading text-2xl text-vinyl-black">{profile.following_count}</span>
                  <span className="text-[11px] text-muted-foreground ml-1.5">Following</span>
                </button>
                <span className="text-stone-300 hidden sm:inline">|</span>
                <button onClick={() => setFollowListType('followers')} className="hover:opacity-70 transition text-center" data-testid="followers-stat">
                  <span className="font-heading text-2xl text-vinyl-black">{profile.followers_count}</span>
                  <span className="text-[11px] text-muted-foreground ml-1.5">Followers</span>
                </button>
              </div>
              {/* Row 2: Records / Est. Value / Sales */}
              <div className="flex flex-row items-center justify-around sm:justify-start sm:gap-8">
                <div className="text-center sm:text-left">
                  <div className="font-heading text-2xl text-vinyl-black">{profile.collection_count}</div>
                  <div className="text-[11px] text-muted-foreground">Records</div>
                </div>
                {collectionValue && collectionValue.total_value > 0 && (
                  <Link to={isOwnProfile ? '/collection' : '#'} className={isOwnProfile ? 'hover:opacity-70 transition' : ''} data-testid="profile-collection-value">
                    <div className="text-center sm:text-left">
                      <div className="font-heading text-2xl text-honey-amber">
                        ${collectionValue.total_value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </div>
                      <div className="text-[11px] text-muted-foreground">Est. Value</div>
                    </div>
                  </Link>
                )}
                {profile.completed_transactions > 0 && (
                  <div className="text-center sm:text-left" data-testid="profile-transactions">
                    <div className="font-heading text-2xl text-vinyl-black flex items-center justify-center sm:justify-start gap-1">
                      <ShoppingBag className="w-4 h-4 text-honey-amber" /> {profile.completed_transactions}
                    </div>
                    <div className="text-[11px] text-muted-foreground">Sales</div>
                  </div>
                )}
              </div>
            </div>

            {/* Trade rating */}
            {ratings && ratings.count > 0 && (
              <div className="flex items-center gap-1 mt-2" data-testid="profile-trade-rating">
                <div className="flex gap-0.5">{[1,2,3,4,5].map(v => <Star key={v} className={`w-3.5 h-3.5 ${v <= Math.round(ratings.average) ? 'fill-honey text-honey' : 'text-gray-300'}`} />)}</div>
                <span className="text-xs text-muted-foreground ml-1">{ratings.average} ({ratings.count} trade{ratings.count !== 1 ? 's' : ''})</span>
              </div>
            )}

            {/* Wishlist Value sub-headline */}
            {dreamValue && dreamValue.total_value > 0 && (
              <p className="mt-2 font-serif italic text-sm" style={{ color: '#C8861A' }} data-testid="profile-dream-value">
                Wishlist Value: ${dreamValue.total_value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </p>
            )}

            {/* Stripe Connect - owner only */}
            {isOwnProfile && stripeStatus && (
              <div className="mt-3">
                {stripeStatus.stripe_connected ? (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700" data-testid="stripe-connected-badge">
                    <CreditCard className="w-3 h-3" /> Stripe Connected
                  </span>
                ) : (
                  <Button size="sm" onClick={handleStripeConnect} disabled={stripeLoading}
                    className="rounded-full bg-[#635bff] text-white hover:bg-[#5146e0] gap-1" data-testid="stripe-connect-btn">
                    {stripeLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <CreditCard className="w-3 h-3" />}
                    Connect with Stripe
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Pinned Wax Report */}
      <WaxReportPin username={username} API={API} token={token} />

      {/* 4 Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-6">
          <TabsTrigger value="collection" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-collection">
            Collection
          </TabsTrigger>
          <TabsTrigger value="dreaming" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-dreaming">
            Dreaming
          </TabsTrigger>
          <TabsTrigger value="iso" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-iso">
            ISO
          </TabsTrigger>
          <TabsTrigger value="spinning" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-spinning">
            Spinning
          </TabsTrigger>
          <TabsTrigger value="trades" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-trades">
            Trades
          </TabsTrigger>
          <TabsTrigger value="mood" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-mood">
            Mood
          </TabsTrigger>
        </TabsList>

        {/* Collection Tab */}
        <TabsContent value="collection">
          {/* Show Common Records toggle (BLOCK 39.1) */}
          {!isOwnProfile && tasteMatch && records.length > 0 && (
            <div className="flex items-center gap-2 mb-4">
              <Button
                variant={showCommonOnly ? "default" : "outline"}
                size="sm"
                onClick={() => setShowCommonOnly(!showCommonOnly)}
                className={`rounded-full gap-1.5 text-xs ${showCommonOnly ? 'bg-honey text-vinyl-black hover:bg-honey-amber' : 'border-honey/50'}`}
                data-testid="show-common-btn"
              >
                <Eye className="w-3.5 h-3.5" />
                {showCommonOnly ? 'Showing Common Records' : 'Show Common Records'}
              </Button>
              {showCommonOnly && (
                <span className="text-xs text-muted-foreground">{tasteMatch.shared_reality.length} shared</span>
              )}
            </div>
          )}
          {records.length === 0 ? (
            <EmptyState icon={Disc} title="No records yet" sub={isOwnProfile ? 'Start building your collection!' : `@${username} hasn't added any records yet`} />
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {records
                .filter(record => !showCommonOnly || (tasteMatch?.shared_reality || []).some(s => s.discogs_id && s.discogs_id === record.discogs_id))
                .map(record => {
                  const isCommon = !isOwnProfile && tasteMatch && (tasteMatch.shared_reality || []).some(s => s.discogs_id && s.discogs_id === record.discogs_id);
                  return (
                <Link to={`/record/${record.id}`} key={record.id}>
                  <Card
                    className={`border-honey/30 overflow-hidden hover:shadow-honey transition-all hover:-translate-y-1`}
                    style={isCommon
                      ? { boxShadow: '0 0 15px #FFD700' }
                      : (showCommonOnly ? { opacity: 0.3 } : {})}
                  >
                    <div className="aspect-square bg-vinyl-black">
                      {record.cover_url ? (
                        <AlbumArt src={record.cover_url} alt={record.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Disc className="w-12 h-12 text-honey" />
                        </div>
                      )}
                    </div>
                    <div className="p-3">
                      <h4 className="font-medium text-sm truncate">{record.title}</h4>
                      <p className="text-xs text-muted-foreground truncate">{record.artist}</p>
                      {isCommon && <span className="inline-block mt-1 text-[10px] font-medium text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded-full" data-testid="common-badge">In Your Collection</span>}
                    </div>
                  </Card>
                </Link>
                  );
                })}
            </div>
          )}
        </TabsContent>

        {/* Dreaming Tab */}
        <TabsContent value="dreaming">
          {dreamingItems.length === 0 ? (
            <EmptyState icon={Cloud} title="No dreams yet" sub={isOwnProfile ? 'Add records to your Dreaming tab to start building your Wishlist Value.' : `@${username} isn't dreaming of anything right now`} />
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {dreamingItems.map(item => {
                const ownerHasIt = !isOwnProfile && item.discogs_id && myRecordDiscogs.has(item.discogs_id);
                return (
                  <Card key={item.id} className="border-honey/30 overflow-hidden transition-all hover:-translate-y-1" style={ownerHasIt ? { boxShadow: '0 0 15px #FFD700' } : {}} data-testid={`dreaming-item-${item.id}`}>
                    <div className="aspect-square bg-vinyl-black">
                      {item.cover_url ? (
                        <AlbumArt src={item.cover_url} alt={item.album} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Disc className="w-12 h-12 text-honey" />
                        </div>
                      )}
                    </div>
                    <div className="p-3">
                      <h4 className="font-medium text-sm truncate">{item.album}</h4>
                      <p className="text-xs text-muted-foreground truncate">{item.artist}</p>
                      {ownerHasIt && (
                        <>
                          <span className="inline-block mt-1 text-[10px] font-medium text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded-full" data-testid={`in-collection-dream-${item.id}`}>
                            In Your Collection
                          </span>
                          <button
                            onClick={() => navigate(`/messages?to=${profile.id}&text=${encodeURIComponent(`Hey! I saw you're dreaming of ${item.album}. It's one of my favorites — tell me about your ideal pressing!`)}`)}
                            className="block mt-1.5 text-[10px] font-medium text-honey-amber hover:underline"
                            data-testid={`tell-them-${item.id}`}
                          >
                            Tell them about this pressing.
                          </button>
                        </>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* ISO Tab */}
        <TabsContent value="iso">
          {isos.length === 0 ? (
            <EmptyState icon={Search} title="No ISOs yet" sub={isOwnProfile ? 'Post an ISO from The Hive to start searching!' : `@${username} isn't searching for anything right now`} />
          ) : (
            <div className="space-y-3">
              {isos.map(iso => (
                <Card key={iso.id} className={`p-4 border-honey/30 ${iso.status === 'FOUND' ? 'opacity-60' : ''}`} data-testid={`iso-item-${iso.id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-heading text-lg">{iso.album}</h4>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                          iso.status === 'FOUND' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'
                        }`}>{iso.status}</span>
                        {/* "In Your Collection" badge (BLOCK 39.2) */}
                        {!isOwnProfile && iso.discogs_id && myRecordDiscogs.has(iso.discogs_id) && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-honey/20 text-amber-700" data-testid={`in-your-collection-${iso.id}`}>
                            In Your Collection
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{iso.artist}</p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {(iso.tags || []).map(tag => (
                          <TagPill key={tag} tag={tag} />
                        ))}
                        {iso.pressing_notes && <span className="text-xs text-muted-foreground">Press: {iso.pressing_notes}</span>}
                        {iso.condition_pref && <span className="text-xs text-muted-foreground">Cond: {iso.condition_pref}</span>}
                      </div>
                      {(iso.target_price_min || iso.target_price_max) && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Budget: {iso.target_price_min ? `$${iso.target_price_min}` : '?'} – {iso.target_price_max ? `$${iso.target_price_max}` : '?'}
                        </p>
                      )}
                      {/* Pre-filled chat CTA (BLOCK 39.2) */}
                      {!isOwnProfile && iso.discogs_id && myRecordDiscogs.has(iso.discogs_id) && iso.status !== 'FOUND' && (
                        <Button
                          size="sm" variant="outline"
                          className="mt-2 rounded-full text-xs border-honey/50 text-honey-amber hover:bg-honey/10 gap-1"
                          onClick={() => navigate(`/messages?to=${profile.id}&text=${encodeURIComponent(`Hey! I saw you're dreaming of ${iso.album}. It's one of my favorites in my collection. Are you looking for a specific variant?`)}`)}
                          data-testid={`chat-about-${iso.id}`}
                        >
                          <MessageCircle className="w-3 h-3" /> Start a Chat
                        </Button>
                      )}
                    </div>
                    {isOwnProfile && iso.status === 'OPEN' && (
                      <div className="flex gap-1 shrink-0">
                        <Button size="sm" variant="ghost" className="text-green-600 hover:bg-green-50 h-8 px-2" onClick={() => handleMarkFound(iso.id)} data-testid={`mark-found-${iso.id}`}>
                          <CheckCircle2 className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" className="text-red-400 hover:bg-red-50 h-8 px-2" onClick={() => handleDeleteIso(iso.id)}>✕</Button>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Spinning Tab */}
        <TabsContent value="spinning">
          {spins.length === 0 ? (
            <EmptyState icon={Play} title="No spins yet" sub={isOwnProfile ? 'Spin a record to see your history here!' : `@${username} hasn't spun anything yet`} />
          ) : (
            <div className="space-y-3">
              {spins.map(spin => (
                <Card key={spin.id} className="p-4 border-honey/30 flex items-center gap-4" data-testid={`spin-${spin.id}`}>
                  {spin.record?.cover_url ? (
                    <AlbumArt src={spin.record.cover_url} alt="" className="w-14 h-14 rounded-lg object-cover shadow" />
                  ) : (
                    <div className="w-14 h-14 rounded-lg bg-vinyl-black flex items-center justify-center">
                      <Disc className="w-6 h-6 text-honey" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{spin.record?.title || 'Unknown'}</p>
                    <p className="text-xs text-muted-foreground truncate">{spin.record?.artist || 'Unknown'}</p>
                    {spin.notes && <p className="text-xs text-honey-amber mt-0.5">Track: {spin.notes}</p>}
                  </div>
                  <p className="text-xs text-muted-foreground shrink-0">
                    {formatDistanceToNow(new Date(spin.created_at), { addSuffix: true })}
                  </p>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Trades Tab */}
        <TabsContent value="trades">
          {trades.length === 0 ? (
            <EmptyState icon={ArrowRightLeft} title="No trades yet" sub={isOwnProfile ? 'Propose a trade from The Honeypot!' : `@${username} hasn't completed any trades yet`} />
          ) : (
            <div className="space-y-3">
              {trades.map(trade => {
                const isInit = trade.initiator_id === profile.id;
                const otherUser = isInit ? trade.responder : trade.initiator;
                const statusColors = {
                  ACCEPTED: 'bg-green-100 text-green-700',
                  COMPLETED: 'bg-green-100 text-green-700',
                  SHIPPING: 'bg-purple-100 text-purple-700',
                  CONFIRMING: 'bg-cyan-100 text-cyan-700',
                };
                return (
                  <Card key={trade.id} className="p-4 border-honey/30" data-testid={`profile-trade-${trade.id}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${statusColors[trade.status] || 'bg-gray-100 text-gray-600'}`}>
                        {trade.status}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(trade.updated_at), { addSuffix: true })}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {trade.offered_record?.cover_url ? (
                          <AlbumArt src={trade.offered_record.cover_url} alt="" className="w-10 h-10 rounded object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>
                        )}
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{trade.offered_record?.title || 'Unknown'}</p>
                          <p className="text-xs text-muted-foreground truncate">{trade.offered_record?.artist}</p>
                        </div>
                      </div>
                      <ArrowRightLeft className="w-4 h-4 text-honey shrink-0" />
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {trade.listing_record?.cover_url ? (
                          <AlbumArt src={trade.listing_record.cover_url} alt="" className="w-10 h-10 rounded object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>
                        )}
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{trade.listing_record?.album || 'Unknown'}</p>
                          <p className="text-xs text-muted-foreground truncate">{trade.listing_record?.artist}</p>
                        </div>
                      </div>
                    </div>
                    {otherUser && (
                      <p className="text-xs text-muted-foreground mt-2">
                        Trade with <Link to={`/profile/${otherUser.username}`} className="text-honey-amber hover:underline">@{otherUser.username}</Link>
                      </p>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
          {isOwnProfile && (
            <Link to="/trades" className="block mt-4">
              <Button variant="outline" className="w-full rounded-full border-honey/30 text-honey-amber hover:bg-honey/10" data-testid="view-all-trades-btn">
                View All Trades
              </Button>
            </Link>
          )}
        </TabsContent>

        {/* Mood Board Tab */}
        <TabsContent value="mood">
          <MoodBoardTab username={username} />
        </TabsContent>
      </Tabs>

      {/* Common Ground Overlay (BLOCK 40.2) */}
      <Dialog open={commonGroundOpen} onOpenChange={setCommonGroundOpen}>
        <DialogContent className="sm:max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2">
              <Sparkles className="w-5 h-5" style={{ color: '#C8861A' }} /> Common Ground with @{username}
            </DialogTitle>
            <DialogDescription>
              {tasteMatch?.score}% Taste Match {tasteMatch?.label && `· ${tasteMatch.label}`}
              {tasteMatch?.shared_dream_value > 0 && (
                <span className="block mt-1 font-medium" style={{ color: '#C8861A' }} data-testid="shared-dream-value">
                  You share ${tasteMatch.shared_dream_value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} in Wishlist Value.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          {tasteMatch && (
            <div className="space-y-5 pt-2">
              {/* Shared Reality */}
              <div>
                <h4 className="text-sm font-semibold text-vinyl-black mb-2">Shared Collection</h4>
                <p className="text-xs text-muted-foreground mb-2">You both own these.</p>
                {tasteMatch.shared_reality.length === 0 ? (
                  <p className="text-xs text-stone-400 italic">No shared records yet.</p>
                ) : (
                  <div className="flex gap-2 overflow-x-auto pb-2" data-testid="shared-reality-list">
                    {tasteMatch.shared_reality.map((r, i) => (
                      <div key={i} className="shrink-0 w-20">
                        <div className="w-20 h-20 rounded-lg overflow-hidden bg-vinyl-black">
                          {r.cover_url ? <AlbumArt src={r.cover_url} alt={r.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
                        </div>
                        <p className="text-[10px] font-medium truncate mt-1">{r.title}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{r.artist}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {/* Shared Dreams */}
              <div>
                <h4 className="text-sm font-semibold text-vinyl-black mb-2">Shared Dreams</h4>
                <p className="text-xs text-muted-foreground mb-2">You're both dreaming of these.</p>
                {tasteMatch.shared_dreams.length === 0 ? (
                  <p className="text-xs text-stone-400 italic">No shared dreams yet.</p>
                ) : (
                  <div className="flex gap-2 overflow-x-auto pb-2" data-testid="shared-dreams-list">
                    {tasteMatch.shared_dreams.map((r, i) => (
                      <div key={i} className="shrink-0 w-20">
                        <div className="w-20 h-20 rounded-lg overflow-hidden bg-vinyl-black">
                          {r.cover_url ? <AlbumArt src={r.cover_url} alt={r.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
                        </div>
                        <p className="text-[10px] font-medium truncate mt-1">{r.title}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{r.artist}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {/* Swap Potential */}
              <div>
                <h4 className="text-sm font-semibold text-vinyl-black mb-2">Perfect Swap</h4>
                <p className="text-xs text-muted-foreground mb-2">They own what you're hunting for.</p>
                {tasteMatch.swap_potential.length === 0 ? (
                  <p className="text-xs text-stone-400 italic">No swap matches right now.</p>
                ) : (
                  <div className="flex gap-2 overflow-x-auto pb-2" data-testid="swap-potential-list">
                    {tasteMatch.swap_potential.map((r, i) => (
                      <div key={i} className="shrink-0 w-20">
                        <div className="w-20 h-20 rounded-lg overflow-hidden bg-vinyl-black ring-2 ring-honey/40">
                          {r.cover_url ? <AlbumArt src={r.cover_url} alt={r.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
                        </div>
                        <p className="text-[10px] font-medium truncate mt-1">{r.title}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{r.artist}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Follow List Modal */}
      <FollowListModal
        open={!!followListType}
        onOpenChange={(open) => !open && setFollowListType(null)}
        username={username}
        listType={followListType || 'followers'}
        onFollowChange={fetchProfile}
      />
      <ReportModal open={reportSellerOpen} onOpenChange={setReportSellerOpen} targetType="seller" targetId={profile?.id} />
    </div>
  );
};

const EmptyState = ({ icon: Icon, title, sub }) => (
  <Card className="p-8 text-center border-honey/30">
    <Icon className="w-12 h-12 text-honey mx-auto mb-4" />
    <h3 className="font-heading text-xl mb-2">{title}</h3>
    <p className="text-muted-foreground text-sm">{sub}</p>
  </Card>
);

const WaxReportPin = ({ username, API, token }) => {
  const [report, setReport] = useState(null);
  useEffect(() => {
    axios.get(`${API}/wax-reports/latest/${username}`)
      .then(r => setReport(r.data))
      .catch(() => {});
  }, [API, username]);

  if (!report) return null;

  let weekRange = '';
  try {
    const ws = new Date(report.week_start);
    const we = new Date(report.week_end);
    we.setDate(we.getDate() - 1);
    weekRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} · ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { weekRange = ''; }

  return (
    <Link to={`/wax-reports/${report.id}`} className="block mb-4" data-testid="profile-wax-pin">
      <Card className="p-4 rounded-2xl shadow-sm hover:shadow-md transition-all" style={{ background: '#FAEDC7', border: '1px solid rgba(200,134,26,0.15)' }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0" style={{ background: 'rgba(200,134,26,0.08)' }}>
            <Disc className="w-4 h-4" style={{ color: '#C8861A' }} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-heading" style={{ color: '#2A1A06' }}>your week in wax</p>
            <p className="text-[11px] truncate" style={{ color: '#8A6B4A' }}>
              {weekRange} · {report.total_spins} spins · {report.personality?.label?.slice(0, 40)}...
            </p>
          </div>
          <span className="text-[11px] shrink-0" style={{ color: '#C8861A' }}>View &rarr;</span>
        </div>
      </Card>
    </Link>
  );
};

export default ProfilePage;
