import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSocket } from '../context/SocketContext';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Heart, MessageCircle, Share2, Disc, Send, ChevronUp, MoreVertical, Trash2, Play, Plus, Loader2, Pin, Reply, ArrowUp, Sparkles } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import ComposerBar from '../components/ComposerBar';
import { resolveImageUrl } from '../utils/imageUrl';
import { PostTypeBadge, PostCardBody, NewFeatureBadge, PILL_STYLES } from '../components/PostCards';
import { PostCard, BeeAvatar, InfiniteScrollSentinel } from '../components/HivePostCard';
import { TitleBadge } from '../components/TitleBadge';
import { usePageTitle } from '../hooks/usePageTitle';
import { usePullToRefresh } from '../hooks/usePullToRefresh';
import { DailyPromptCard } from '../components/DailyPrompt';
import OnboardingModal from '../components/OnboardingModal';
import AlbumArt, { prefetchArt } from '../components/AlbumArt';
import SEOHead from '../components/SEOHead';
import { useVariantModal } from '../context/VariantModalContext';
import LoadingHoney from '../components/LoadingHoney';

const HivePage = () => {
  usePageTitle('The Hive');
  const { user, token, API } = useAuth();
  const { socket, connected } = useSocket();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [posts, setPosts] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [feedError, setFeedError] = useState(false);
  // Following filter works by fetching the user's following list
  const [followingIds, setFollowingIds] = useState([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false);

  // Live feed: queued new posts from WebSocket
  const [newPostsQueue, setNewPostsQueue] = useState([]);
  const postsRef = useRef(posts);
  useEffect(() => { postsRef.current = posts; }, [posts]);

  // Daily prompt buzz state — controls streak banner vs. prompt card visibility
  const promptRef = useRef(null);
  const [promptBuzzedIn, setPromptBuzzedIn] = useState(false);
  const [promptStreak, setPromptStreak] = useState(0);
  const handleBuzzStatusChange = useCallback((buzzed, streak) => {
    setPromptBuzzedIn(buzzed);
    setPromptStreak(streak);
  }, []);

  const targetPostId = searchParams.get('post');
  const targetCommentId = searchParams.get('comment');

  const { openVariantModal } = useVariantModal();

  const [activeFilter, setActiveFilter] = useState('all');
  const [feedMode, setFeedMode] = useState('all'); // 'all' or 'following'
  const promptFilter = searchParams.get('prompt_id');
  const [promptFilterText, setPromptFilterText] = useState(null);

  // Fetch prompt text for the filter banner
  useEffect(() => {
    if (!promptFilter) { setPromptFilterText(null); return; }
    axios.get(`${API}/prompts/today`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { if (r.data.prompt?.id === promptFilter) setPromptFilterText(r.data.prompt.text); else setPromptFilterText('a daily prompt'); })
      .catch(() => setPromptFilterText('a daily prompt'));
  }, [promptFilter, API, token]);

  const FEED_FILTERS = [
    { key: 'all', emoji: '\u{1F36F}', text: 'All' },
    { key: 'NOW_SPINNING', emoji: '\u{1F3B5}', text: 'Spinning' },
    { key: 'NEW_HAUL', emoji: '\u{1F4E6}', text: 'Hauls' },
    { key: 'ISO', emoji: '\u{1F50D}', text: 'ISOs' },
    { key: 'DAILY_PROMPT', emoji: '\u{1F41D}', text: 'Prompts' },
    { key: 'POLL', emoji: '\u{1F4CA}', text: 'Polls' },
  ];

  const headers = { Authorization: `Bearer ${token}` };

  const FEED_LIMIT = 20;

  // Feed cache key for sessionStorage
  const FEED_CACHE_KEY = 'hg_feed_cache';

  const fetchFeed = useCallback(async (filterOverride) => {
    try {
      setFeedError(false);
      const params = { limit: FEED_LIMIT };
      const filter = filterOverride !== undefined ? filterOverride : activeFilter;
      if (filter && filter !== 'all') params.post_type = filter;
      const response = await axios.get(`${API}/feed`, {
        params,
        headers: { Authorization: `Bearer ${token}` },
        timeout: 30000,
      });
      let feedPosts = response.data;
      setHasMore(feedPosts.length >= FEED_LIMIT);
      // If a specific post is targeted from notification but not in feed, fetch and inject it
      if (targetPostId && !feedPosts.find(p => p.id === targetPostId)) {
        try {
          const single = await axios.get(`${API}/posts/${targetPostId}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          feedPosts = [single.data, ...feedPosts];
        } catch { /* post might be deleted */ }
      }
      setPosts(feedPosts);
      // Prefetch album art for first 15 posts
      const artUrls = feedPosts.slice(0, 15).flatMap(p => [
        p.cover_url, p.iso?.cover_url,
        ...(p.bundle_records || []).map(r => r.cover_url),
        ...(p.haul?.items || []).map(i => i.cover_url),
      ]).filter(Boolean);
      if (artUrls.length) prefetchArt(artUrls);
      // Cache feed for instant return visits
      try { sessionStorage.setItem(FEED_CACHE_KEY, JSON.stringify(feedPosts)); } catch { /* quota */ }
    } catch (error) {
      console.error('Feed fetch failed:', error?.message, error?.response?.status);
      setFeedError(true);
      toast.error('something went wrong loading the hive.');
    } finally {
      setLoading(false);
    }
  }, [API, token, targetPostId]);

  const loadMore = useCallback(async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const lastPost = posts[posts.length - 1];
      const before = lastPost?.created_at || null;
      const params = { limit: FEED_LIMIT };
      if (before) params.before = before;
      if (activeFilter && activeFilter !== 'all') params.post_type = activeFilter;
      const response = await axios.get(`${API}/feed`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });
      const newPosts = response.data;
      setHasMore(newPosts.length >= FEED_LIMIT);
      setPosts(prev => [...prev, ...newPosts]);
    } catch {
      toast.error('could not load more posts.');
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, hasMore, posts, API, token, FEED_LIMIT, activeFilter]);

  const fetchRecords = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/records`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecords(response.data);
    } catch { /* ignore */ }
  }, [API, token]);

  // Pull-to-refresh
  const { PullIndicator } = usePullToRefresh(useCallback(async () => {
    await Promise.all([fetchFeed(), fetchRecords()]);
  }, [fetchFeed, fetchRecords]));

  useEffect(() => {
    // Hydrate from cache for instant display, then fetch fresh in background
    try {
      const cached = sessionStorage.getItem(FEED_CACHE_KEY);
      if (cached) {
        const cachedPosts = JSON.parse(cached);
        if (cachedPosts?.length) {
          setPosts(cachedPosts);
          setLoading(false);
        }
      }
    } catch { /* corrupt cache */ }
    fetchFeed();
    fetchRecords();
    // Fetch following list for the "Following" filter
    if (user?.username) {
      axios.get(`${API}/users/${user.username}/following`, { headers: { Authorization: `Bearer ${token}` } })
        .then(res => setFollowingIds((res.data || []).map(u => u.id)))
        .catch(() => {});
    }
    // Check if onboarding needed (only after full user data loads, not JWT-decoded partial data)
    if (user && !user._fromToken && user.onboarding_completed === false) {
      setShowOnboarding(true);
    }
  }, [fetchFeed, fetchRecords, user]);

  // Re-fetch when filter changes (server-side filtering)
  const filterInitRef = useRef(true);
  useEffect(() => {
    if (filterInitRef.current) { filterInitRef.current = false; return; }
    setLoading(true);
    setPosts([]);
    setHasMore(true);
    fetchFeed(activeFilter);
  }, [activeFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  // WebSocket: listen for NEW_POST events
  useEffect(() => {
    if (!socket) return;
    const handleNewPost = (data) => {
      const { post, author_id } = data;
      if (author_id === user?.id) return;
      setNewPostsQueue(prev => {
        if (prev.some(p => p.id === post.id)) return prev;
        if (postsRef.current.some(p => p.id === post.id)) return prev;
        return [post, ...prev];
      });
    };
    socket.on('NEW_POST', handleNewPost);
    return () => socket.off('NEW_POST', handleNewPost);
  }, [socket, user?.id]);

  // Polling fallback: check for new posts every 20s when WS is not connected
  const latestPostTs = useRef(null);
  useEffect(() => {
    if (posts.length > 0 && posts[0]?.created_at) {
      latestPostTs.current = posts[0].created_at;
    }
  }, [posts]);

  useEffect(() => {
    if (connected) return; // WS is live, no need to poll
    const interval = setInterval(async () => {
      if (!latestPostTs.current || !token) return;
      try {
        const params = { limit: 10, after: latestPostTs.current };
        if (activeFilter && activeFilter !== 'all') params.post_type = activeFilter;
        const res = await axios.get(`${API}/feed`, { params, headers: { Authorization: `Bearer ${token}` } });
        const fresh = (res.data || []).filter(p => p.author_id !== user?.id);
        if (fresh.length > 0) {
          setNewPostsQueue(prev => {
            const queueIds = new Set(prev.map(p => p.id));
            const feedIds = new Set(postsRef.current.map(p => p.id));
            const unique = fresh.filter(p => !queueIds.has(p.id) && !feedIds.has(p.id));
            return unique.length ? [...unique, ...prev] : prev;
          });
        }
      } catch { /* silent */ }
    }, 20000);
    return () => clearInterval(interval);
  }, [connected, API, token, activeFilter, user?.id]);

  // Flush queued posts into the feed
  const showNewPosts = () => {
    setPosts(prev => {
      const existingIds = new Set(prev.map(p => p.id));
      const unique = newPostsQueue.filter(p => !existingIds.has(p.id));
      return [...unique, ...prev];
    });
    setNewPostsQueue([]);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };


  // Back to top — handled globally via App.js BackToTop component

  const filteredPosts = React.useMemo(() => {
    let result = posts;
    // Apply prompt filter first if active
    if (promptFilter) {
      result = result.filter(p => p.prompt_id === promptFilter);
    }
    // Apply feed mode (All vs Following)
    if (feedMode === 'following') {
      result = result.filter(p => followingIds.includes(p.user_id));
    }
    // Post type filtering is now server-side, no client-side filter needed
    return result;
  }, [posts, feedMode, followingIds, promptFilter]);

  const handleLike = async (postId, isLiked) => {
    // Optimistic update — instant visual feedback
    setPosts(prev => prev.map(post => {
      if (post.id === postId) {
        return { ...post, is_liked: !isLiked, likes_count: isLiked ? Math.max(0, post.likes_count - 1) : post.likes_count + 1 };
      }
      return post;
    }));
    try {
      if (isLiked) {
        await axios.delete(`${API}/posts/${postId}/like`, { headers: { Authorization: `Bearer ${token}` }});
      } else {
        await axios.post(`${API}/posts/${postId}/like`, {}, { headers: { Authorization: `Bearer ${token}` }});
      }
    } catch {
      // Revert on failure
      setPosts(prev => prev.map(post => {
        if (post.id === postId) {
          return { ...post, is_liked: isLiked, likes_count: isLiked ? post.likes_count + 1 : Math.max(0, post.likes_count - 1) };
        }
        return post;
      }));
      toast.error('Sticky situation—try again');
    }
  };

  const updatePostCommentCount = (postId, delta) => {
    setPosts(prev => prev.map(post => {
      if (post.id === postId) return { ...post, comments_count: post.comments_count + delta };
      return post;
    }));
  };

  const handlePostCreated = () => {
    fetchFeed();
    fetchRecords();
  };

  const handleDeletePost = async (postId) => {
    try {
      await axios.delete(`${API}/posts/${postId}`, { headers });
      setPosts(prev => prev.filter(p => p.id !== postId));
      toast.success('post deleted.');
    } catch {
      toast.error('could not delete post. try again.');
    }
  };

  const handlePinPost = async (postId, isPinned) => {
    try {
      if (isPinned) {
        await axios.delete(`${API}/posts/${postId}/pin`, { headers });
        setPosts(prev => prev.map(p => p.id === postId ? { ...p, is_pinned: false } : p));
        toast.success('post unpinned.');
      } else {
        await axios.post(`${API}/posts/${postId}/pin`, {}, { headers });
        setPosts(prev => prev.map(p => ({ ...p, is_pinned: p.id === postId })));
        toast.success('post pinned to top.');
      }
    } catch {
      toast.error('could not update pin status.');
    }
  };

  const handleToggleFeature = async (postId, isNewFeature) => {
    try {
      const resp = await axios.post(`${API}/posts/${postId}/new-feature`, {}, { headers });
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, is_new_feature: resp.data.is_new_feature } : p));
      toast.success(resp.data.is_new_feature ? 'tagged as New Feature.' : 'New Feature tag removed.');
    } catch {
      toast.error('could not update feature tag.');
    }
  };

  const handleToggleReleaseNote = async (postId, isReleaseNote) => {
    try {
      const resp = await axios.post(`${API}/posts/${postId}/release-note`, {}, { headers });
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, is_release_note: resp.data.is_release_note } : p));
      toast.success(resp.data.is_release_note ? 'Promoted to Release Note.' : 'Release Note demoted.');
    } catch {
      toast.error('could not update release note status.');
    }
  };


  // Album detail — open unified variant modal
  const handleAlbumClick = (record) => {
    openVariantModal({
      artist: record.artist,
      album: record.title || record.album,
      variant: record.color_variant || record.variant || '',
      discogs_id: record.discogs_id,
      cover_url: record.cover_url,
      record_id: record.id || record.record_id,
    });
  };

  const handleOnboardingComplete = () => {
    setShowOnboarding(false);
    setShowWelcome(true);
    fetchFeed();
    fetchRecords();
    setTimeout(() => setShowWelcome(false), 4000);
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 pt-3 md:pt-2">
        <h1 className="font-heading text-3xl mb-6">The Hive</h1>
        {feedError ? (
          <Card className="p-8 text-center border-honey/30" data-testid="hive-error-state">
            <p className="italic text-muted-foreground mb-4" style={{ fontFamily: '"DM Serif Display", serif', color: '#3A4D63' }}>
              couldn't reach the hive. tap below to try again.
            </p>
            <Button onClick={() => { setLoading(true); setFeedError(false); fetchFeed(); }} className="bg-[#D4A828] text-white hover:bg-[#E8CA5A] rounded-full" data-testid="hive-retry-btn">
              Try Again
            </Button>
          </Card>
        ) : (
          <LoadingHoney />
        )}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-24 md:pb-8 honey-fade-in">
      <PullIndicator />
      <SEOHead
        title="The Hive — Vinyl Social Feed"
        description="See what collectors are spinning, buying, and trading. The Hive is the social feed for vinyl lovers on The Honey Groove."
        url="/hive"
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'CollectionPage',
          name: 'The Hive — Vinyl Social Feed',
          url: 'https://thehoneygroove.com/hive',
          description: 'Social feed for vinyl collectors. See what records people are spinning, collecting, and trading.',
        }}
      />
      {/* Onboarding Modal */}
      <OnboardingModal open={showOnboarding} onComplete={handleOnboardingComplete} />

      {/* Welcome Banner */}
      {showWelcome && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-[#F0E6C8] border border-[#E5DBC8]/50 text-center"
          style={{ animation: 'bingoCelebFadeIn 300ms ease-out' }}
          data-testid="welcome-banner"
        >
          <p className="text-[#D4A828] font-medium italic" style={{ fontFamily: '"DM Serif Display", serif' }}>
            welcome to the hive. 🐝 you're in.
          </p>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <h1 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: '24px', fontWeight: 700, color: '#1E2A3A', margin: 0 }}>The Hive</h1>
        <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: '#2D6A4F' }}>
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#2D6A4F' }} />
          Live Feed
        </div>
      </div>

      {/* Feed Mode Toggle: All | Following */}
      <div className="flex items-center justify-between mb-4" data-testid="feed-mode-toggle">
        <div className="flex" style={{ borderRadius: '8px', overflow: 'hidden' }}>
          <button
            onClick={() => setFeedMode('all')}
            className="transition-all duration-200"
            style={{
              padding: '8px 24px', fontSize: '12px', fontWeight: 700, cursor: 'pointer',
              background: feedMode === 'all' ? '#1E2A3A' : 'rgba(255,255,255,0.5)',
              color: feedMode === 'all' ? '#E8CA5A' : '#7A8694',
              border: feedMode === 'all' ? 'none' : '1px solid #E5DBC8',
              borderRadius: '8px 0 0 8px',
              boxShadow: feedMode === 'all' ? '0 2px 4px rgba(30,42,58,0.2), 0 4px 12px rgba(30,42,58,0.12)' : 'none',
            }}
            data-testid="feed-mode-all"
          >All</button>
          <button
            onClick={() => setFeedMode('following')}
            className="transition-all duration-200"
            style={{
              padding: '8px 24px', fontSize: '12px', fontWeight: 700, cursor: 'pointer',
              background: feedMode === 'following' ? '#1E2A3A' : 'rgba(255,255,255,0.5)',
              color: feedMode === 'following' ? '#E8CA5A' : '#7A8694',
              border: feedMode === 'following' ? 'none' : '1px solid #E5DBC8',
              borderLeft: 'none',
              borderRadius: '0 8px 8px 0',
              boxShadow: feedMode === 'following' ? '0 2px 4px rgba(30,42,58,0.2), 0 4px 12px rgba(30,42,58,0.12)' : 'none',
            }}
            data-testid="feed-mode-following"
          >Following</button>
        </div>
      </div>

      {/* Composer Bar */}
      <ComposerBar onPostCreated={handlePostCreated} records={records} />

      {/* Streak Banner — shown when user hasn't buzzed in yet */}
      {!promptBuzzedIn && (
        <div
          style={{
            background: '#354B66', borderRadius: '10px', padding: '12px 16px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px',
            boxShadow: '0 2px 4px rgba(53,75,102,0.2), 0 4px 12px rgba(53,75,102,0.12)',
            marginBottom: '14px',
          }}
          data-testid="streak-banner"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
            <span style={{ fontSize: '20px', lineHeight: 1, flexShrink: 0 }}>🐝{promptStreak > 0 ? '🔥' : ''}</span>
            <div style={{ minWidth: 0 }}>
              <p style={{ fontSize: '12px', fontWeight: 700, color: '#FFFFFF', margin: 0, lineHeight: 1.2 }}>
                {promptStreak > 0 ? `${promptStreak}-day Buzz In streak!` : 'Daily Buzz In'}
              </p>
              <p style={{ fontSize: '10px', color: '#F0E6C8', margin: '2px 0 0', opacity: 0.85 }}>Answer today's prompt to keep it going</p>
            </div>
          </div>
          <button
            onClick={() => promptRef.current?.openBuzzModal()}
            style={{
              flexShrink: 0, padding: '7px 16px', borderRadius: '7px', fontSize: '10px', fontWeight: 700,
              background: '#D4A828', color: '#FFFFFF', border: 'none', cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(212,168,40,0.28), 0 4px 12px rgba(212,168,40,0.20)',
              transition: 'opacity 0.15s',
            }}
            data-testid="streak-buzz-in-btn"
          >
            Buzz In
          </button>
        </div>
      )}

      {/* Daily Prompt — shown after buzzing in (no buzz-in button, just carousel) */}
      <DailyPromptCard
        ref={promptRef}
        records={records}
        onPostCreated={handlePostCreated}
        onBuzzStatusChange={handleBuzzStatusChange}
      />

      {/* Feed Filter — centered pill row */}
      <div className="mb-4 flex flex-wrap gap-1.5 justify-center" data-testid="feed-filter-bar">
        {FEED_FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setActiveFilter(f.key)}
            style={{
              padding: '6px 14px', borderRadius: '9999px', fontSize: '10px', fontWeight: 600,
              whiteSpace: 'nowrap', cursor: 'pointer', transition: 'all 0.15s ease',
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              background: activeFilter === f.key ? '#1E2A3A' : 'rgba(255,255,255,0.6)',
              color: activeFilter === f.key ? '#E8CA5A' : '#3A4D63',
              border: activeFilter === f.key ? 'none' : '1px solid #E5DBC8',
              boxShadow: activeFilter === f.key ? '0 2px 4px rgba(30,42,58,0.2), 0 4px 12px rgba(30,42,58,0.12)' : 'none',
            }}
            data-testid={`filter-${f.key}`}
          >
            <span>{f.emoji}</span>
            <span>{f.text}</span>
          </button>
        ))}
      </div>

      {/* Prompt Filter Banner */}
      {promptFilter && promptFilterText && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-[#F0E6C8] border border-[#E5DBC8]/60 flex items-center justify-between gap-3" data-testid="prompt-filter-banner">
          <p className="text-sm text-[#1E2A3A] font-medium italic truncate">
            Viewing responses to: {promptFilterText}
          </p>
          <Button
            size="sm" variant="ghost"
            onClick={() => setSearchParams({})}
            className="shrink-0 text-xs text-[#D4A828] hover:text-[#1E2A3A]"
            data-testid="clear-prompt-filter"
          >
            Clear Filter
          </Button>
        </div>
      )}

      {/* Live Feed: New Posts Notification */}
      {newPostsQueue.length > 0 && (
        <button
          onClick={showNewPosts}
          className="w-full mb-4 py-2.5 px-4 rounded-xl border border-honey/50 text-sm font-medium flex items-center justify-center gap-2 transition-all duration-300 hover:shadow-md animate-in slide-in-from-top-2 fade-in duration-300"
          style={{
            background: 'linear-gradient(135deg, rgba(244,185,66,0.12) 0%, rgba(217,140,47,0.08) 100%)',
            color: '#D4A828',
          }}
          data-testid="new-posts-btn"
        >
          <ArrowUp className="w-4 h-4" />
          {newPostsQueue.length === 1
            ? '1 new post'
            : `${newPostsQueue.length} new posts`}
          <span className="text-xs opacity-70">— tap to see</span>
        </button>
      )}

      {filteredPosts.length === 0 ? (
        <Card className="p-8 text-center border-honey/30" data-testid="hive-empty-state">
          <span className="text-4xl block mb-3">🐝</span>
          <p className="italic text-muted-foreground mb-4" style={{ fontFamily: '"DM Serif Display", serif', color: '#3A4D63' }}>
            {feedMode === 'following' && activeFilter === 'all'
              ? 'No posts yet.'
              : feedMode === 'following'
                ? `No ${FEED_FILTERS.find(f => f.key === activeFilter)?.label || ''} posts yet.`
                : activeFilter === 'all'
                  ? 'No posts yet.'
                  : `No ${FEED_FILTERS.find(f => f.key === activeFilter)?.label || ''} posts yet.`}
          </p>
          {feedMode === 'following' ? (
            <Button onClick={() => navigate('/nectar')} className="bg-[#D4A828] text-white hover:bg-[#E8CA5A] rounded-full" data-testid="find-collectors-btn">
              browse collectors
            </Button>
          ) : (
            <Button onClick={() => {}} className="bg-[#D4A828] text-white hover:bg-[#E8CA5A] rounded-full" data-testid="hive-empty-cta">
              post something
            </Button>
          )}
        </Card>
      ) : (
        <div className="space-y-4">
          {(() => {
            const isGold = user?.golden_hive || user?.golden_hive_verified;
            const UPSELL_POSITIONS = [5, 12];
            const upsellCard = (key) => (
              <div
                key={key}
                style={{
                  background: 'linear-gradient(135deg, rgba(30,42,58,0.08), rgba(30,42,58,0.12))',
                  border: '1px solid rgba(30,42,58,0.15)',
                  borderRadius: '10px',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                }}
                data-testid="gold-upsell-card"
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                  <span style={{ fontSize: '16px', flexShrink: 0 }}>✦</span>
                  <span style={{ fontSize: '11px', color: '#1E2A3A', lineHeight: 1.4 }}>Unlock advanced filters, Silent Spins, and the Gold Collector badge</span>
                </div>
                <a
                  href="/gold"
                  style={{
                    flexShrink: 0, padding: '7px 16px', borderRadius: '7px', fontSize: '10px', fontWeight: 700,
                    background: 'linear-gradient(135deg, #D4A828, #E8CA5A, #D4A828)', color: '#1E2A3A',
                    border: 'none', cursor: 'pointer', textDecoration: 'none', whiteSpace: 'nowrap',
                    boxShadow: '0 2px 4px rgba(212,168,40,0.25), inset 0 1px 0 rgba(255,255,255,0.2)',
                    display: 'inline-block',
                  }}
                  data-testid="gold-upsell-cta"
                >
                  Go Gold
                </a>
              </div>
            );
            const items = [];
            filteredPosts.forEach((post, idx) => {
              if (!isGold && UPSELL_POSITIONS.includes(idx)) {
                items.push(upsellCard(`upsell-${idx}`));
              }
              items.push(
                <PostCard
                  key={post.id}
                  post={post}
                  onLike={handleLike}
                  onCommentCountChange={updatePostCommentCount}
                  onDelete={handleDeletePost}
                  onAlbumClick={handleAlbumClick}
                  onPin={handlePinPost}
                  onToggleFeature={handleToggleFeature}
                  onToggleReleaseNote={handleToggleReleaseNote}
                  token={token}
                  API={API}
                  currentUserId={user?.id}
                  isAdmin={user?.is_admin}
                  highlighted={post.id === targetPostId}
                  autoOpenComments={post.id === targetPostId && !!targetCommentId}
                  imgPriority={idx < 5}
                />
              );
            });
            return items;
          })()}
        </div>
      )}

      {/* Infinite Scroll Sentinel */}
      {filteredPosts.length > 0 && hasMore && feedMode === 'all' && (
        <InfiniteScrollSentinel onIntersect={loadMore} loading={loadingMore} />
      )}
      {filteredPosts.length > 0 && !hasMore && feedMode === 'all' && (
        <p className="text-center text-sm text-muted-foreground pt-6 pb-2 italic">you've reached the beginning of the hive.</p>
      )}

      {/* Back to Top — handled globally in App.js */}

    </div>
  );
};

export default HivePage;
