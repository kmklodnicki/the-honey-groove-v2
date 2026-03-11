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
import { Disc, Edit, UserPlus, UserMinus, Loader2, Search, Play, ArrowRightLeft, CreditCard, Star, MessageCircle, MapPin, ShoppingBag, Flag, Sparkles, Eye, X, Cloud, ShieldOff, ShieldCheck, Lock, Clock, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { FollowListModal } from '../components/FollowList';
import { FollowRequestsBadge, FollowRequestsModal } from '../components/FollowRequests';
import { usePageTitle } from '../hooks/usePageTitle';
import { MoodBoardTab } from '../components/MoodBoardTab';
import ReportModal from '../components/ReportModal';
import MentionText from '../components/MentionText';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { resolveImageUrl } from '../utils/imageUrl';
import AlbumArt from '../components/AlbumArt';
import { countryFlag } from '../utils/countryFlag';
import { TitleBadge } from '../components/TitleBadge';
import SEOHead from '../components/SEOHead';
import { useVariantModal } from '../context/VariantModalContext';
import { EmptyState } from '../components/EmptyState';
import WaxReportPin from '../components/WaxReportPin';
import BackToTop from '../components/BackToTop';

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
  const [isBlocked, setIsBlocked] = useState(false);
  const [followsMe, setFollowsMe] = useState(false);
  const [blockLoading, setBlockLoading] = useState(false);
  const [showBlockConfirm, setShowBlockConfirm] = useState(false);
  const [profileUnavailable, setProfileUnavailable] = useState(false);
  const [followRequestPending, setFollowRequestPending] = useState(false);
  const [followRequestCount, setFollowRequestCount] = useState(0);
  const [followRequestsOpen, setFollowRequestsOpen] = useState(false);
  const [goldenHiveModalOpen, setGoldenHiveModalOpen] = useState(false);
  const [goldenHiveCheckoutLoading, setGoldenHiveCheckoutLoading] = useState(false);
  const [deleteSpinTarget, setDeleteSpinTarget] = useState(null);

  const handleDeleteSpin = async () => {
    if (!deleteSpinTarget) return;
    try {
      await axios.delete(`${API}/spins/${deleteSpinTarget.id}`, { 
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Spin and linked post deleted.');
      setSpins(prev => prev.filter(s => s.id !== deleteSpinTarget.id));
      setDeleteSpinTarget(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete spin.');
    }
  };

  const { openVariantModal } = useVariantModal();

  const isOwnProfile = user?.username === username;

  const openRecordVariant = (record) => {
    openVariantModal({
      artist: record.artist,
      album: record.title || record.album,
      variant: record.color_variant || record.pressing_notes || record.variant || '',
      discogs_id: record.discogs_id,
      cover_url: record.cover_url,
    });
  };

  const fetchProfile = useCallback(async () => {
    try {
      setProfileUnavailable(false);
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      // Fetch profile first
      const profileRes = await axios.get(`${API}/users/${username}`, { headers });
      setProfile(profileRes.data);
      
      const profileLocked = profileRes.data.profile_locked;
      
      // Only fetch records/content if profile is not locked
      if (!profileLocked) {
        const recordsRes = await axios.get(`${API}/users/${username}/records`, { headers });
        setRecords(recordsRes.data);
      } else {
        setRecords([]);
      }

      if (token && !isOwnProfile) {
        const [followRes, blockRes] = await Promise.all([
          axios.get(`${API}/follow/check/${username}`, { headers: { Authorization: `Bearer ${token}` }}),
          axios.get(`${API}/block/check/${username}`, { headers: { Authorization: `Bearer ${token}` }}),
        ]);
        setIsFollowing(followRes.data.is_following);
        setFollowsMe(followRes.data.follows_me || false);
        setIsBlocked(blockRes.data.is_blocked);
        setFollowRequestPending(followRes.data.follow_request_pending || profileRes.data.follow_request_status === 'pending');
      }
      if (token && isOwnProfile) {
        axios.get(`${API}/stripe/status`, { headers: { Authorization: `Bearer ${token}` }}).then(r => setStripeStatus(r.data)).catch(() => {});
        axios.get(`${API}/follow-requests`, { headers: { Authorization: `Bearer ${token}` }}).then(r => setFollowRequestCount(r.data.length)).catch(() => {});
      }
      
      if (!profileLocked) {
        axios.get(`${API}/users/${username}/ratings`).then(r => setRatings(r.data)).catch(() => {});
        axios.get(`${API}/valuation/collection/${username}`).then(r => setCollectionValue(r.data)).catch(() => {});
        axios.get(`${API}/prompts/streak/${username}`).then(r => setPromptStreak(r.data)).catch(() => {});
        axios.get(`${API}/valuation/dreamlist/${username}`).then(r => setDreamValue(r.data)).catch(() => {});

        // Fetch taste match for other users
        if (token && !isOwnProfile) {
          setTasteLoading(true);
          axios.get(`${API}/users/${username}/taste-match`, { headers: { Authorization: `Bearer ${token}` }})
            .then(r => {
              setTasteMatch(r.data);
              if (r.data.score >= 90 && !new URLSearchParams(window.location.search).get('tab')) {
                setActiveTab('in-common');
              }
            })
            .catch(() => {})
            .finally(() => setTasteLoading(false));
          axios.get(`${API}/records`, { headers: { Authorization: `Bearer ${token}` }})
            .then(r => setMyRecordDiscogs(new Set(r.data.filter(rec => rec.discogs_id).map(rec => rec.discogs_id))))
            .catch(() => {});
        }
      }
    } catch (err) {
      if (err.response?.status === 403) {
        setProfileUnavailable(true);
      } else {
        toast.error('Failed to load profile');
      }
    } finally {
      setLoading(false);
    }
  }, [API, token, username, isOwnProfile]);

  useEffect(() => {
    setLoading(true);
    setActiveTab(new URLSearchParams(window.location.search).get('tab') || 'collection');
    setTasteMatch(null);
    setShowCommonOnly(false);
    setCommonGroundOpen(false);
    setDreamingItems([]);
    setDreamValue(null);
    fetchProfile();

    // Handle Golden Hive redirect
    const params = new URLSearchParams(window.location.search);
    const ghSessionId = params.get('session_id');
    const ghStatus = params.get('golden_hive');
    if (ghStatus === 'success' && ghSessionId && token) {
      axios.get(`${API}/golden-hive/verify-payment?session_id=${ghSessionId}`, { headers: { Authorization: `Bearer ${token}` } })
        .then(() => { toast.success('Payment confirmed! Your Golden Hive ID is pending admin review.'); window.history.replaceState({}, '', window.location.pathname); fetchProfile(); })
        .catch(() => {});
    }
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
      if (isFollowing || followRequestPending) {
        await axios.delete(`${API}/follow/${username}`, { headers: { Authorization: `Bearer ${token}` }});
        if (isFollowing) {
          setIsFollowing(false);
          setProfile(p => p ? { ...p, followers_count: p.followers_count - 1 } : p);
        }
        setFollowRequestPending(false);
      } else {
        const res = await axios.post(`${API}/follow/${username}`, {}, { headers: { Authorization: `Bearer ${token}` }});
        if (res.data.status === 'requested') {
          setFollowRequestPending(true);
          toast.success('Follow request sent');
        } else {
          setIsFollowing(true);
          setProfile(p => p ? { ...p, followers_count: p.followers_count + 1 } : p);
        }
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    } finally {
      setFollowLoading(false);
    }
  };

  const handleBlock = async () => {
    setBlockLoading(true);
    try {
      await axios.post(`${API}/block/${username}`, {}, { headers: { Authorization: `Bearer ${token}` }});
      setIsBlocked(true);
      setIsFollowing(false);
      toast.success(`@${username} has been blocked.`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to block user');
    } finally {
      setBlockLoading(false);
      setShowBlockConfirm(false);
    }
  };

  const handleUnblock = async () => {
    setBlockLoading(true);
    try {
      await axios.delete(`${API}/block/${username}`, { headers: { Authorization: `Bearer ${token}` }});
      setIsBlocked(false);
      toast.success(`@${username} has been unblocked.`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to unblock user');
    } finally {
      setBlockLoading(false);
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
    if (stripeLoading) return;
    setStripeLoading(true);
    try {
      const resp = await axios.post(`${API}/stripe/connect`, {}, { headers: { Authorization: `Bearer ${token}` }});
      if (resp.status !== 200 || !resp.data?.url) {
        toast.error('Could not create Stripe session. Please try again.');
        setStripeLoading(false);
        return;
      }
      window.location.href = resp.data.url;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to connect Stripe');
      setStripeLoading(false);
    }
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

  if (!profile && !profileUnavailable) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24 text-center">
        <h2 className="font-heading text-2xl mb-2">User not found</h2>
        <p className="text-muted-foreground">@{username} doesn't exist.</p>
      </div>
    );
  }

  if (profileUnavailable) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24 text-center" data-testid="profile-unavailable">
        <div className="flex flex-col items-center gap-4 py-16">
          <div className="w-16 h-16 rounded-full bg-stone-100 flex items-center justify-center">
            <ShieldOff className="w-7 h-7 text-stone-400" />
          </div>
          <h2 className="font-heading text-2xl text-stone-700">Profile Unavailable</h2>
          <p className="text-sm text-stone-500 max-w-xs">This profile is not available to you.</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(-1)}
            className="mt-2 rounded-full border-stone-300 text-stone-600"
            data-testid="go-back-btn"
          >
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  const firstLetter = profile.username?.charAt(0).toUpperCase() || '?';

  const profileTitle = `@${profile.username}${profile.title_label ? ` — ${profile.title_label}` : ''} — ${records.length} Records`;
  const profileDesc = `@${profile.username}'s vinyl collection on The Honey Groove. ${records.length} records collected.${profile.bio ? ` ${profile.bio.slice(0, 160)}` : ''}${profile.city ? ` Based in ${profile.city}.` : ''}`;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8" data-testid="profile-page">
      <SEOHead
        title={profileTitle}
        description={profileDesc}
        url={`/profile/${profile.username}`}
        image={profile.avatar_url}
        type="profile"
        collectorMeta={{
          username: profile.username,
          collectionSize: records.length,
          isoCount: isos.length,
        }}
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'ProfilePage',
          name: `@${profile.username}`,
          url: `https://thehoneygroove.com/profile/${profile.username}`,
          image: profile.avatar_url,
          description: profileDesc,
          mainEntity: {
            '@type': 'Person',
            name: profile.username,
            url: `https://thehoneygroove.com/profile/${profile.username}`,
            image: profile.avatar_url,
            interactionStatistic: [{
              '@type': 'InteractionCounter',
              interactionType: 'https://schema.org/FollowAction',
              userInteractionCount: profile.followers_count || 0,
            }],
          },
        }}
      />
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
                    className={`rounded-full ${
                      isFollowing ? 'bg-white border border-vinyl-black/30 text-vinyl-black hover:bg-red-50 hover:text-red-600' :
                      followRequestPending ? 'bg-white border border-amber-400 text-amber-700 hover:bg-red-50 hover:text-red-600' :
                      followsMe && !isFollowing ? 'bg-honey text-vinyl-black hover:bg-honey-amber shadow-[0_0_12px_rgba(244,185,66,0.4)] animate-[honeyPulse_2s_ease-in-out_infinite]' :
                      'bg-honey text-vinyl-black hover:bg-honey-amber'
                    }`}
                    data-testid="follow-btn"
                  >
                    {followLoading ? <Loader2 className="w-4 h-4 animate-spin" /> :
                      isFollowing ? <><UserMinus className="w-4 h-4 mr-1" />Following</> :
                      followRequestPending ? <><Loader2 className="w-4 h-4 mr-1" />Requested</> :
                      profile?.is_private ? <><Lock className="w-4 h-4 mr-1" />Request to Follow</> :
                      followsMe ? <><UserPlus className="w-4 h-4 mr-1" />Follow Back</> :
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
                  <Button
                    size="sm" variant="ghost"
                    onClick={() => isBlocked ? handleUnblock() : setShowBlockConfirm(true)}
                    disabled={blockLoading}
                    className={`rounded-full ${isBlocked ? 'text-red-500 hover:text-stone-600' : 'text-muted-foreground/60 hover:text-red-500'}`}
                    data-testid="block-btn"
                  >
                    {blockLoading ? <Loader2 className="w-3 h-3 animate-spin" /> :
                      isBlocked ? <ShieldCheck className="w-3 h-3" /> : <ShieldOff className="w-3 h-3" />
                    }
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
            {profile.bio && <p className="text-sm text-muted-foreground mt-1"><MentionText text={profile.bio} /></p>}
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

            {/* Golden Hive ID Badge */}
            {profile.golden_hive_verified && (
              <div className="mt-1.5 inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-gradient-to-r from-amber-100 to-yellow-50 border border-amber-300/50" data-testid="golden-hive-badge">
                <svg className="w-3.5 h-3.5 text-amber-600" viewBox="0 0 24 24" fill="currentColor"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span className="text-xs font-medium text-amber-700">Golden Hive ID</span>
              </div>
            )}
            {profile.golden_hive_status === 'pending' && isOwnProfile && (
              <div className="mt-1.5 inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-stone-100 border border-stone-200" data-testid="golden-hive-pending">
                <Clock className="w-3 h-3 text-stone-500" />
                <span className="text-xs text-stone-500">Golden Hive ID — Pending Verification</span>
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

            {/* Value of Dream Records sub-headline */}
            {dreamValue && dreamValue.total_value > 0 && dreamValue.total_count > 0 && (
              <p className="mt-2 font-serif italic text-sm" style={{ color: '#C8861A' }} data-testid="profile-dream-value">
                Value of Dream Records: ${dreamValue.total_value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
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
            {/* Golden Hive ID — own profile only */}
            {isOwnProfile && !profile.golden_hive_verified && profile.golden_hive_status !== 'pending' && (
              <div className="mt-3" data-testid="golden-hive-cta">
                <Button size="sm" onClick={() => setGoldenHiveModalOpen(true)} className="rounded-full bg-gradient-to-r from-amber-400 to-yellow-400 text-vinyl-black hover:from-amber-500 hover:to-yellow-500 gap-1.5 font-medium" data-testid="golden-hive-open-modal-btn">
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  Get Golden Hive ID
                </Button>
                <p className="text-[10px] text-muted-foreground mt-1 max-w-[200px]">Verified identity badge for trusted trading and selling</p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Pinned Wax Report */}
      <WaxReportPin username={username} API={API} token={token} />

      {/* Follow Requests Badge — own profile only */}
      {isOwnProfile && followRequestCount > 0 && (
        <div className="mb-4">
          <FollowRequestsBadge count={followRequestCount} onClick={() => setFollowRequestsOpen(true)} />
        </div>
      )}

      {/* Profile Content — Locked or Tabs */}
      {profile?.profile_locked ? (
        <div className="text-center py-12 px-4" data-testid="profile-locked">
          <div className="flex flex-col items-center gap-4 max-w-sm mx-auto">
            <div className="w-16 h-16 rounded-full bg-stone-100 flex items-center justify-center">
              <Lock className="w-7 h-7 text-stone-400" />
            </div>
            <h3 className="font-heading text-xl text-stone-700">This Account is Private</h3>
            <p className="text-sm text-stone-500">Follow this user to see their posts, collection, ISOs, and Dream Items.</p>
            
            {/* Mutual signals */}
            {profile.mutual_followers?.length > 0 && (
              <p className="text-xs text-stone-500" data-testid="mutual-followers-hint">
                Followed by <span className="font-medium text-stone-700">{profile.mutual_followers.join(', ')}</span>
              </p>
            )}
            {profile.records_in_common > 0 && (
              <p className="text-xs text-amber-700 flex items-center gap-1" data-testid="records-common-hint">
                <Disc className="w-3 h-3" /> {profile.records_in_common} record{profile.records_in_common !== 1 ? 's' : ''} in common
              </p>
            )}
            
            <Button
              size="sm"
              onClick={handleFollow}
              disabled={followLoading || followRequestPending}
              className={`rounded-full mt-2 ${
                followRequestPending ? 'bg-white border border-amber-400 text-amber-700' :
                followsMe ? 'bg-honey text-vinyl-black hover:bg-honey-amber shadow-[0_0_12px_rgba(244,185,66,0.4)] animate-[honeyPulse_2s_ease-in-out_infinite]' :
                'bg-honey text-vinyl-black hover:bg-honey-amber'
              }`}
              data-testid="locked-follow-btn"
            >
              {followLoading ? <Loader2 className="w-4 h-4 animate-spin" /> :
                followRequestPending ? 'Requested' :
                followsMe ? <><UserPlus className="w-4 h-4 mr-1" /> Follow Back</> :
                <><Lock className="w-4 h-4 mr-1" /> Request to Follow</>
              }
            </Button>
          </div>
        </div>
      ) : (
      /* 4 Tabs */
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6 w-full flex overflow-x-auto no-scrollbar gap-1 p-1" style={{ WebkitOverflowScrolling: 'touch' }}>
          <TabsTrigger value="collection" className="data-[state=active]:bg-honey text-xs sm:text-sm shrink-0 px-3" data-testid="tab-collection">
            Collection
          </TabsTrigger>
          <TabsTrigger value="dreaming" className="data-[state=active]:bg-honey text-xs sm:text-sm shrink-0 px-3" data-testid="tab-dreaming">
            Dream List
          </TabsTrigger>
          {!isOwnProfile && tasteMatch && (
            <TabsTrigger value="in-common" className="data-[state=active]:bg-honey text-xs sm:text-sm shrink-0 px-3" data-testid="tab-in-common">
              In Common
            </TabsTrigger>
          )}
          <TabsTrigger value="iso" className="data-[state=active]:bg-honey text-xs sm:text-sm shrink-0 px-3" data-testid="tab-iso">
            ISO
          </TabsTrigger>
          <TabsTrigger value="spinning" className="data-[state=active]:bg-honey text-xs sm:text-sm shrink-0 px-3" data-testid="tab-spinning">
            Spin History
          </TabsTrigger>
          <TabsTrigger value="trades" className="data-[state=active]:bg-honey text-xs sm:text-sm shrink-0 px-3" data-testid="tab-trades">
            Trades
          </TabsTrigger>
          <TabsTrigger value="mood" className="data-[state=active]:bg-honey text-xs sm:text-sm shrink-0 px-3" data-testid="tab-mood">
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
                <button onClick={() => openRecordVariant(record)} key={record.id} className="text-left w-full">
                  <Card
                    className={`border-honey/30 overflow-hidden hover:shadow-honey transition-all hover:-translate-y-1`}
                    style={isCommon
                      ? { boxShadow: '0 0 15px #FFD700' }
                      : (showCommonOnly ? { opacity: 0.3 } : {})}
                  >
                    <div className="relative aspect-square bg-vinyl-black">
                      {record.cover_url ? (
                        <AlbumArt src={record.cover_url} alt={`${record.artist} ${record.title}${record.color_variant ? ` ${record.color_variant}` : ''} vinyl record`} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Disc className="w-12 h-12 text-honey" />
                        </div>
                      )}
                      {record.color_variant && (
                        <>
                          <div className="absolute top-0 left-0 w-1/2 h-1/2 z-[4] pointer-events-none rounded-tl-2xl" style={{ background: 'linear-gradient(135deg, rgba(0,0,0,0.25) 0%, transparent 60%)' }} />
                          <div
                            className="absolute top-2 left-2 max-w-[70%] truncate uppercase text-[10px] font-bold px-2 py-0.5 rounded-full"
                            style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                            data-testid={`variant-pill-${record.id}`}
                          >
                            {record.color_variant}
                          </div>
                        </>
                      )}
                      {record.edition_number && (
                        <div
                          className={`absolute ${record.color_variant ? 'top-8' : 'top-2'} left-2 uppercase text-[9px] font-bold px-2 py-0.5 rounded-full z-[5]`}
                          style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                          data-testid={`edition-pill-${record.id}`}
                        >
                          No. {record.edition_number}
                        </div>
                      )}
                    </div>
                    <div className="p-3">
                      <h4 className="font-medium text-sm truncate">{record.title}</h4>
                      <p className="text-xs text-muted-foreground truncate">{record.artist}</p>
                      {isCommon && <span className="inline-block mt-1 text-[10px] font-medium text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded-full" data-testid="common-badge">In Your Collection</span>}
                    </div>
                  </Card>
                </button>
                  );
                })}
            </div>
          )}
        </TabsContent>

        {/* Dreaming Tab */}
        <TabsContent value="dreaming">
          {dreamingItems.length === 0 ? (
            <EmptyState icon={Cloud} title="No dreams yet" sub={isOwnProfile ? 'Add records to your Dream List to start building your Value of Dream Records.' : `@${username} isn't dreaming of anything right now`} />
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {dreamingItems.map(item => {
                const ownerHasIt = !isOwnProfile && item.discogs_id && myRecordDiscogs.has(item.discogs_id);
                return (
                  <Card
                    key={item.id}
                    className="border-honey/30 overflow-hidden transition-all hover:-translate-y-1 cursor-pointer"
                    style={ownerHasIt ? { boxShadow: '0 0 15px #FFD700' } : {}}
                    onClick={() => openRecordVariant(item)}
                    data-testid={`dreaming-item-${item.id}`}
                  >
                    <div className="relative aspect-square bg-vinyl-black">
                      {item.cover_url ? (
                        <AlbumArt src={item.cover_url} alt={`${item.artist} ${item.album}${item.color_variant ? ` ${item.color_variant}` : ''} vinyl record`} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Disc className="w-12 h-12 text-honey" />
                        </div>
                      )}
                      {item.color_variant && (
                        <>
                          <div className="absolute top-0 left-0 w-1/2 h-1/2 z-[4] pointer-events-none rounded-tl-2xl" style={{ background: 'linear-gradient(135deg, rgba(0,0,0,0.25) 0%, transparent 60%)' }} />
                          <div
                            className="absolute top-2 left-2 max-w-[70%] truncate uppercase text-[10px] font-bold px-2 py-0.5 rounded-full"
                            style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                          >
                            {item.color_variant}
                          </div>
                        </>
                      )}
                      {item.preferred_number && (
                        <div
                          className={`absolute ${item.color_variant ? 'top-8' : 'top-2'} left-2 uppercase text-[9px] font-bold px-2 py-0.5 rounded-full z-[5]`}
                          style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                          data-testid={`preferred-number-${item.id}`}
                        >
                          Seeking No. {item.preferred_number}
                        </div>
                      )}
                      {/* Price badge — always visible */}
                      {!ownerHasIt && (
                        item.median_value > 0 ? (
                          <div className="absolute top-2 right-2 px-2.5 py-1 rounded-full font-black z-[5]"
                            style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', fontSize: '18px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                            data-testid={`dream-value-${item.id}`}>
                            ${Math.round(item.median_value)}
                          </div>
                        ) : (
                          <div className="absolute top-2 right-2 px-2.5 py-1 rounded-full font-black z-[5]"
                            style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: 'rgba(0,0,0,0.5)', fontSize: '14px', letterSpacing: '1px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                            data-testid={`dream-value-placeholder-${item.id}`}>
                            ---
                          </div>
                        )
                      )}
                      <div className="absolute bottom-2 right-2">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-pink-500/90 text-white">DREAMING</span>
                      </div>
                      {ownerHasIt && (
                        <div className="absolute top-2 right-2">
                          <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-honey/90 text-vinyl-black">In Yours</span>
                        </div>
                      )}
                    </div>
                    <div className="p-3">
                      <h4 className="font-medium text-sm truncate">{item.album}</h4>
                      <p className="text-xs text-muted-foreground truncate">{item.artist}</p>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* In Common Tab (only when viewing another user with taste match) */}
        {!isOwnProfile && tasteMatch && (
          <TabsContent value="in-common">
            <div className="space-y-8" data-testid="in-common-tab">
              {/* Shared Realities */}
              <div>
                <h3 className="font-heading text-lg mb-1">Shared Realities</h3>
                <p className="text-xs text-muted-foreground mb-3">You both own these specific records.</p>
                {tasteMatch.shared_reality.length === 0 ? (
                  <p className="text-sm text-stone-400 italic py-4" data-testid="no-shared-reality">No matching records yet. Maybe you're the first with this specific taste!</p>
                ) : (
                  <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3" data-testid="shared-realities-grid">
                    {tasteMatch.shared_reality.map((r, i) => (
                      <button key={i} className="group text-left" style={{ boxShadow: '0 0 12px rgba(255,215,0,0.3)' }} onClick={() => openRecordVariant(r)}>
                        <div className="aspect-square rounded-lg overflow-hidden bg-vinyl-black">
                          {r.cover_url ? <AlbumArt src={r.cover_url} alt={r.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>}
                        </div>
                        <p className="text-xs font-medium truncate mt-1">{r.title}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{r.artist}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {/* Shared Visions */}
              <div>
                <h3 className="font-heading text-lg mb-1">Shared Visions</h3>
                <p className="text-xs text-muted-foreground mb-3">You both have these on your Dream List.</p>
                {tasteMatch.shared_dreams.length === 0 ? (
                  <p className="text-sm text-stone-400 italic py-4" data-testid="no-shared-dreams">No shared dreams yet.</p>
                ) : (
                  <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3" data-testid="shared-visions-grid">
                    {tasteMatch.shared_dreams.map((r, i) => (
                      <button key={i} className="text-left" onClick={() => openRecordVariant(r)}>
                        <div className="aspect-square rounded-lg overflow-hidden bg-vinyl-black">
                          {r.cover_url ? <AlbumArt src={r.cover_url} alt={r.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>}
                        </div>
                        <p className="text-xs font-medium truncate mt-1">{r.title}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{r.artist}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {/* The Cross-Over */}
              <div>
                <h3 className="font-heading text-lg mb-1">The Cross-Over</h3>
                <p className="text-xs text-muted-foreground mb-3">Records they own that you want, and vice-versa.</p>
                {tasteMatch.swap_potential.length === 0 ? (
                  <p className="text-sm text-stone-400 italic py-4" data-testid="no-crossover">No cross-over matches right now.</p>
                ) : (
                  <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3" data-testid="crossover-grid">
                    {tasteMatch.swap_potential.map((r, i) => (
                      <button key={i} className="text-left" style={{ boxShadow: '0 0 12px rgba(200,134,26,0.3)' }} onClick={() => openRecordVariant(r)}>
                        <div className="aspect-square rounded-lg overflow-hidden bg-vinyl-black ring-1 ring-honey/40">
                          {r.cover_url ? <AlbumArt src={r.cover_url} alt={r.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>}
                        </div>
                        <p className="text-xs font-medium truncate mt-1">{r.title}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{r.artist}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
        )}

        {/* ISO Tab */}
        <TabsContent value="iso">
          {isos.length === 0 ? (
            <EmptyState icon={Search} title="No ISOs yet" sub={isOwnProfile ? 'Post an ISO from The Hive to start searching!' : `@${username} isn't searching for anything right now`} />
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {isos.map(iso => (
                <Card
                  key={iso.id}
                  className={`border-honey/30 overflow-hidden hover:shadow-honey transition-all hover:-translate-y-1 cursor-pointer ${iso.status === 'FOUND' ? 'opacity-60' : ''}`}
                  onClick={() => openRecordVariant(iso)}
                  data-testid={`iso-item-${iso.id}`}
                >
                  <div className="relative aspect-square bg-vinyl-black">
                    {iso.cover_url ? (
                      <AlbumArt src={iso.cover_url} alt={`${iso.artist} ${iso.album}${iso.pressing_notes ? ` ${iso.pressing_notes}` : ''} vinyl record`} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Disc className="w-12 h-12 text-honey" />
                      </div>
                    )}
                    {iso.pressing_notes && (
                      <>
                        <div className="absolute top-0 left-0 w-1/2 h-1/2 z-[4] pointer-events-none rounded-tl-2xl" style={{ background: 'linear-gradient(135deg, rgba(0,0,0,0.25) 0%, transparent 60%)' }} />
                        <div
                          className="absolute top-2 left-2 max-w-[70%] truncate uppercase text-[10px] font-bold px-2 py-0.5 rounded-full"
                          style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                        >
                          {iso.pressing_notes}
                        </div>
                      </>
                    )}
                    {iso.preferred_number && (
                      <div
                        className={`absolute ${iso.pressing_notes ? 'top-8' : 'top-2'} left-2 uppercase text-[9px] font-bold px-2 py-0.5 rounded-full z-[5]`}
                        style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                        data-testid={`preferred-number-iso-${iso.id}`}
                      >
                        Seeking No. {iso.preferred_number}
                      </div>
                    )}
                    <div className="absolute bottom-2 right-2">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        iso.status === 'FOUND' ? 'bg-green-500/90 text-white' : 'bg-purple-500/90 text-white'
                      }`}>{iso.status}</span>
                    </div>
                    {!isOwnProfile && iso.discogs_id && myRecordDiscogs.has(iso.discogs_id) && (
                      <div className="absolute top-2 right-2">
                        <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-honey/90 text-vinyl-black">
                          In Yours
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="p-3">
                    <h4 className="font-medium text-sm truncate">{iso.album}</h4>
                    <p className="text-xs text-muted-foreground truncate">{iso.artist}</p>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Spin History Tab */}
        <TabsContent value="spinning">
          {spins.length === 0 ? (
            <EmptyState icon={Play} title="No spins yet" sub={isOwnProfile ? 'Spin a record to see your history here!' : `@${username} hasn't spun anything yet`} />
          ) : (
            <div className="space-y-3" data-testid="spin-history-list">
              {spins.map(spin => (
                <Card key={spin.id} className="p-4 border-honey/30" data-testid={`spin-${spin.id}`}>
                  <div className="flex items-start gap-4">
                    {spin.record?.cover_url ? (
                      <AlbumArt src={spin.record.cover_url} alt={`${spin.record.artist} ${spin.record.title} vinyl record`} className="w-16 h-16 rounded-lg object-cover shadow" />
                    ) : (
                      <div className="w-16 h-16 rounded-lg bg-vinyl-black flex items-center justify-center shrink-0">
                        <Disc className="w-6 h-6 text-honey" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="font-medium text-sm truncate">{spin.record?.title || 'Unknown'}</p>
                          <p className="text-xs text-muted-foreground truncate">{spin.record?.artist || 'Unknown'}</p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {spin.mood && (
                            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: '#FFF8E1', color: '#3E2723' }}>
                              {spin.mood}
                            </span>
                          )}
                          <p className="text-[10px] text-muted-foreground">
                            {formatDistanceToNow(new Date(spin.created_at), { addSuffix: true })}
                          </p>
                        </div>
                      </div>
                      {spin.notes && <p className="text-xs text-honey-amber mt-1">Track: {spin.notes}</p>}
                      {spin.caption && (
                        <p className="text-sm text-vinyl-black/80 mt-2 leading-relaxed">{spin.caption}</p>
                      )}
                    </div>
                    {isOwnProfile && (
                      <button
                        onClick={() => setDeleteSpinTarget(spin)}
                        className="shrink-0 p-1.5 rounded-full hover:bg-red-50 text-muted-foreground hover:text-red-500 transition-colors"
                        data-testid={`delete-spin-${spin.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
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
                          <AlbumArt src={trade.offered_record.cover_url} alt={`${trade.offered_record.artist} ${trade.offered_record.title} vinyl record`} className="w-10 h-10 rounded object-cover" />
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
                          <AlbumArt src={trade.listing_record.cover_url} alt={`${trade.listing_record.artist} ${trade.listing_record.title} vinyl record`} className="w-10 h-10 rounded object-cover" />
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
      )}

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
                  You share ${tasteMatch.shared_dream_value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} in Value of Dream Records.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          {tasteMatch && (
            <div className="space-y-5 pt-2">
              {/* Shared Collection */}
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
                <p className="text-xs text-muted-foreground mb-2">You both have these on your Dream List.</p>
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

      {/* Follow Requests Modal */}
      <FollowRequestsModal open={followRequestsOpen} onOpenChange={setFollowRequestsOpen} />

      {/* Block confirmation dialog */}
      <AlertDialog open={showBlockConfirm} onOpenChange={setShowBlockConfirm}>
        <AlertDialogContent data-testid="block-confirm-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Block @{username}?</AlertDialogTitle>
            <AlertDialogDescription>
              They won't be able to see your profile, posts, collection, or interact with you. You'll also stop seeing their content. This will remove any existing follows between you.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="block-cancel-btn">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBlock}
              className="bg-red-600 hover:bg-red-700 text-white"
              data-testid="block-confirm-btn"
            >
              {blockLoading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
              Block
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Golden Hive ID Detail Modal */}
      <Dialog open={goldenHiveModalOpen} onOpenChange={setGoldenHiveModalOpen}>
        <DialogContent className="sm:max-w-md" data-testid="golden-hive-modal">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2 text-lg">
              <svg className="w-5 h-5 text-amber-500" viewBox="0 0 24 24" fill="currentColor"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              Golden Hive ID
            </DialogTitle>
            <DialogDescription>Stand out as a trusted member of the community.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <ul className="space-y-2.5 text-sm">
              <li className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                <span><strong>Verified badge</strong> on your profile, posts, and listings</span>
              </li>
              <li className="flex items-start gap-2">
                <Star className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                <span><strong>Priority visibility</strong> in search results and the marketplace</span>
              </li>
              <li className="flex items-start gap-2">
                <ArrowRightLeft className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                <span><strong>Increased trust</strong> for trades and sales with other collectors</span>
              </li>
              <li className="flex items-start gap-2">
                <Lock className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                <span><strong>Admin-verified identity</strong> — manually reviewed for authenticity</span>
              </li>
            </ul>
            <div className="border-t pt-3">
              <p className="text-center text-xs text-muted-foreground mb-3">One-time verification — <span className="font-semibold text-amber-700">$9.99</span></p>
              <Button
                className="w-full rounded-full bg-gradient-to-r from-amber-400 to-yellow-400 text-vinyl-black hover:from-amber-500 hover:to-yellow-500 font-medium h-11"
                disabled={goldenHiveCheckoutLoading}
                data-testid="golden-hive-checkout-btn"
                onClick={async () => {
                  if (goldenHiveCheckoutLoading) return;
                  setGoldenHiveCheckoutLoading(true);
                  try {
                    const resp = await axios.post(`${API}/golden-hive/checkout`, {}, { headers: { Authorization: `Bearer ${token}` } });
                    if (resp.status !== 200 || !resp.data?.url || !resp.data?.session_id) {
                      toast.error('Checkout session could not be created. Please try again.');
                      setGoldenHiveCheckoutLoading(false);
                      return;
                    }
                    const checkoutUrl = resp.data.url;
                    if (!checkoutUrl.startsWith('https://')) {
                      toast.error('Invalid checkout URL received. Please contact support.');
                      setGoldenHiveCheckoutLoading(false);
                      return;
                    }
                    await new Promise(r => setTimeout(r, 300));
                    window.location.href = checkoutUrl;
                  } catch (err) {
                    toast.error(err.response?.data?.detail || 'Could not start checkout. Please try again.');
                    setGoldenHiveCheckoutLoading(false);
                  }
                }}
              >
                {goldenHiveCheckoutLoading ? (
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10" strokeOpacity="0.25" /><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" /></svg>
                    Taking you to checkout...
                  </span>
                ) : 'Get Verified Now'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Spin Confirmation Dialog */}
      <Dialog open={!!deleteSpinTarget} onOpenChange={(open) => !open && setDeleteSpinTarget(null)}>
        <DialogContent className="sm:max-w-xs" aria-describedby="delete-spin-desc">
          <DialogHeader>
            <DialogTitle className="font-heading text-center" style={{ color: '#D98C2F' }}>
              Delete this spin?
            </DialogTitle>
            <DialogDescription id="delete-spin-desc" className="text-center text-sm text-muted-foreground mt-1">
              This will also remove the linked post from The Hive feed. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex gap-2 pt-3" data-testid="delete-spin-confirm">
            <Button onClick={() => setDeleteSpinTarget(null)} variant="outline" className="flex-1 rounded-full">
              Cancel
            </Button>
            <Button onClick={handleDeleteSpin} className="flex-1 rounded-full text-white" style={{ background: 'linear-gradient(135deg, #EF4444, #DC2626)' }} data-testid="confirm-delete-spin">
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <BackToTop />
    </div>
  );
};

export default ProfilePage;
