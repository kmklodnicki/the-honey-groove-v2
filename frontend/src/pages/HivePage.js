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
import { Heart, MessageCircle, Share2, Disc, Send, ChevronDown, ChevronUp, MoreVertical, Trash2, Play, Plus, Loader2, Pin, Reply, ArrowUp, Sparkles, Check } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
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
    { key: 'NOW_SPINNING', emoji: '\u{1F3B5}', text: 'Now Spinning' },
    { key: 'ISO', emoji: '\u{1F50D}', text: 'ISO' },
    { key: 'NEW_HAUL', emoji: '\u{1F4E6}', text: 'Haul' },
    { key: 'NOTE', emoji: '\u{1F4DD}', text: 'Notes' },
    { key: 'POLL', emoji: '\u{1F4CA}', text: 'Polls' },
    { key: 'listing', emoji: '\u{1F3F7}\uFE0F', text: 'For Sale/Trade' },
    { key: 'RELEASE_NOTE', emoji: '\u270F\uFE0F', text: 'Release Notes' },
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
        <h1 className="font-heading text-3xl text-vinyl-black">The Hive</h1>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-honey animate-pulse" />
          Live Feed
        </div>
      </div>

      {/* Feed Mode Toggle: All | Following */}
      <div className="flex items-center justify-between mb-3" data-testid="feed-mode-toggle">
        <div className="flex w-52 bg-[#F3EBE0] rounded-full p-1">
          <button
            onClick={() => setFeedMode('all')}
            className={`flex-1 py-1.5 rounded-full text-sm font-medium text-center transition-all duration-250 ${
              feedMode === 'all'
                ? 'shadow-sm'
                : 'hover:text-[#354B66]'
            }`}
            style={feedMode === 'all'
              ? { background: '#1E2A3A', color: '#E8CA5A', boxShadow: '0 2px 4px rgba(30,42,58,0.2), 0 4px 12px rgba(30,42,58,0.12)' }
              : { color: '#7A8694', background: 'rgba(255,255,255,0.5)' }
            }
            data-testid="feed-mode-all"
          >
            All
          </button>
          <button
            onClick={() => setFeedMode('following')}
            className={`flex-1 py-1.5 rounded-full text-sm font-medium text-center transition-all duration-250 ${
              feedMode === 'following'
                ? 'shadow-sm'
                : 'hover:text-[#354B66]'
            }`}
            style={feedMode === 'following'
              ? { background: '#1E2A3A', color: '#E8CA5A', boxShadow: '0 2px 4px rgba(30,42,58,0.2), 0 4px 12px rgba(30,42,58,0.12)' }
              : { color: '#7A8694', background: 'rgba(255,255,255,0.5)' }
            }
            data-testid="feed-mode-following"
          >
            Following
          </button>
        </div>
      </div>

      {/* Composer Bar */}
      <ComposerBar onPostCreated={handlePostCreated} records={records} />

      {/* Daily Prompt */}
      <DailyPromptCard records={records} onPostCreated={handlePostCreated} />

      {/* Feed Filter — Dropdown */}
      <div className="mb-4 flex justify-center lg:justify-start" data-testid="feed-filter-bar">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium border transition-colors w-auto justify-center"
              style={activeFilter !== 'all'
                ? { background: '#1E2A3A', borderColor: '#1E2A3A', color: '#E8CA5A', boxShadow: '0 2px 4px rgba(30,42,58,0.2), 0 4px 12px rgba(30,42,58,0.12)' }
                : { background: 'rgba(255,255,255,0.5)', borderColor: '#E5DBC8', color: '#7A8694' }
              }
              data-testid="feed-filter-trigger"
            >
              <span>{(() => { const f = FEED_FILTERS.find(f => f.key === activeFilter); return f ? `${f.emoji} ${f.text}` : 'All'; })()}</span>
              <ChevronDown className="w-4 h-4 shrink-0" style={{ color: activeFilter !== 'all' ? '#E8CA5A' : '#7A8694' }} />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="center"
            className="rounded-xl border-2 p-1"
            style={{ borderColor: '#E5DBC8', backdropFilter: 'blur(12px)', background: 'rgba(255,255,255,0.95)', width: '280px', maxWidth: '80vw' }}
          >
            {FEED_FILTERS.map((f, idx) => (
              <React.Fragment key={f.key}>
                <DropdownMenuItem
                  onClick={() => setActiveFilter(f.key)}
                  className="rounded-lg px-3 py-2.5 cursor-pointer flex items-center justify-center gap-2 text-sm font-medium transition-colors hover:bg-[#F0E6C8]"
                  style={activeFilter === f.key ? { background: '#1E2A3A', color: '#E8CA5A' } : { color: '#354B66' }}
                  data-testid={`filter-${f.key}`}
                >
                  <span className="shrink-0">{f.emoji}</span>
                  <span>{f.text}</span>
                  {activeFilter === f.key && <Check className="w-4 h-4 shrink-0 ml-auto" style={{ color: '#E8CA5A' }} />}
                </DropdownMenuItem>
                {idx < FEED_FILTERS.length - 1 && (
                  <div className="mx-3 my-0.5" style={{ borderBottom: '1px solid rgba(229,219,200,0.5)' }} />
                )}
              </React.Fragment>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
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
          {filteredPosts.map((post, idx) => (
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
          ))}
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
