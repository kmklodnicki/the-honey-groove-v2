import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Heart, MessageCircle, Share2, Disc, Send, ChevronDown, ChevronUp, MoreVertical, Trash2, Play, Plus, Loader2, Pin, Reply, ArrowUp, Sparkles } from 'lucide-react';
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
import { TitleBadge } from '../components/TitleBadge';
import { usePageTitle } from '../hooks/usePageTitle';
import { DailyPromptCard } from '../components/DailyPrompt';
import OnboardingModal from '../components/OnboardingModal';
import AlbumArt from '../components/AlbumArt';
import SEOHead from '../components/SEOHead';
import { useVariantModal } from '../context/VariantModalContext';

// Bee Avatar Component
const BeeAvatar = ({ user, className = "h-10 w-10" }) => {
  const firstLetter = user?.username?.charAt(0).toUpperCase() || '?';
  const hasCustomAvatar = user?.avatar_url && !user.avatar_url.includes('dicebear');
  return (
    <Avatar className={`${className} border-2 border-honey/30`}>
      {hasCustomAvatar && <AvatarImage src={resolveImageUrl(user.avatar_url)} alt={user?.username} />}
      <AvatarFallback className="bg-honey-soft text-vinyl-black relative">
        <span className="font-heading">{firstLetter}</span>
        <svg viewBox="0 0 24 24" className="absolute -bottom-0.5 -right-0.5 w-3 h-3" fill="none">
          <ellipse cx="12" cy="14" rx="5" ry="4" fill="#1F1F1F"/>
          <ellipse cx="12" cy="13" rx="3.5" ry="2" fill="#F4B942"/>
          <circle cx="12" cy="9" r="2.5" fill="#1F1F1F"/>
        </svg>
      </AvatarFallback>
    </Avatar>
  );
};

import CommentThread from '../components/CommentItem';

const PostCard = ({ post, onLike, onCommentCountChange, onDelete, onAlbumClick, onPin, onToggleFeature, token, API, currentUserId, isAdmin, highlighted, autoOpenComments }) => {
  const [showComments, setShowComments] = useState(!!autoOpenComments);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loadingComments, setLoadingComments] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [replyTo, setReplyTo] = useState(null); // { id, username }
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionResults, setMentionResults] = useState([]);
  const [showMentions, setShowMentions] = useState(false);
  const commentInputRef = React.useRef(null);
  const mentionTimerRef = React.useRef(null);
  const cardRef = useRef(null);

  const isOwner = post.user_id === currentUserId;

  const timeAgo = formatDistanceToNow(new Date(post.created_at), { addSuffix: true });

  const fetchComments = async () => {
    setLoadingComments(true);
    try {
      const response = await axios.get(`${API}/posts/${post.id}/comments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleToggleComments = () => {
    if (!showComments && comments.length === 0) fetchComments();
    setShowComments(!showComments);
  };

  // Auto-scroll and auto-open comments when targeted from notification
  useEffect(() => {
    if (highlighted && cardRef.current) {
      setTimeout(() => {
        cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 300);
    }
    if (autoOpenComments && comments.length === 0) {
      fetchComments();
    }
  }, [highlighted, autoOpenComments]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/posts/${post.id}/comments`,
        { post_id: post.id, content: newComment.trim(), parent_id: replyTo?.id || null },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      if (replyTo) {
        // Add reply nested under parent
        setComments(prev => prev.map(c => {
          if (c.id === replyTo.id) {
            return { ...c, replies: [...(c.replies || []), response.data] };
          }
          return c;
        }));
      } else {
        setComments(prev => [...prev, { ...response.data, replies: [] }]);
      }
      setNewComment('');
      setReplyTo(null);
      setShowMentions(false);
      onCommentCountChange(post.id, 1);
    } catch (error) {
      toast.error('something went wrong. please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = (comment) => {
    setReplyTo({ id: comment.id, username: comment.user?.username });
    setNewComment(`@${comment.user?.username} `);
    setTimeout(() => commentInputRef.current?.focus(), 50);
  };

  const handleCommentLike = async (commentId, isLiked) => {
    try {
      if (isLiked) {
        await axios.delete(`${API}/comments/${commentId}/like`, { headers: { Authorization: `Bearer ${token}` } });
      } else {
        await axios.post(`${API}/comments/${commentId}/like`, {}, { headers: { Authorization: `Bearer ${token}` } });
      }
      const updateLike = (list) => list.map(c => {
        if (c.id === commentId) return { ...c, is_liked: !isLiked, likes_count: isLiked ? c.likes_count - 1 : c.likes_count + 1 };
        if (c.replies?.length) return { ...c, replies: updateLike(c.replies) };
        return c;
      });
      setComments(prev => updateLike(prev));
    } catch { /* ignore */ }
  };

  const handleCommentInputChange = (e) => {
    const val = e.target.value;
    setNewComment(val);
    // Detect @mention trigger
    const cursorPos = e.target.selectionStart;
    const textBeforeCursor = val.slice(0, cursorPos);
    const atMatch = textBeforeCursor.match(/@(\w*)$/);
    if (atMatch && atMatch[1].length >= 1) {
      const query = atMatch[1];
      setMentionQuery(query);
      if (mentionTimerRef.current) clearTimeout(mentionTimerRef.current);
      mentionTimerRef.current = setTimeout(async () => {
        try {
          const res = await axios.get(`${API}/mention-search`, { params: { q: query }, headers: { Authorization: `Bearer ${token}` } });
          setMentionResults(res.data);
          setShowMentions(res.data.length > 0);
        } catch { setShowMentions(false); }
      }, 200);
    } else {
      setShowMentions(false);
    }
  };

  const insertMention = (username) => {
    const cursorPos = commentInputRef.current?.selectionStart || newComment.length;
    const textBeforeCursor = newComment.slice(0, cursorPos);
    const textAfterCursor = newComment.slice(cursorPos);
    const replaced = textBeforeCursor.replace(/@(\w*)$/, `@${username} `);
    setNewComment(replaced + textAfterCursor);
    setShowMentions(false);
    setTimeout(() => commentInputRef.current?.focus(), 50);
  };

  const handleShare = async (format) => {
    if (!post.record) { toast.error('nothing to share.'); return; }
    try {
      const response = await axios.post(`${API}/share/generate`,
        { graphic_type: 'now_spinning', record_id: post.record.id, format },
        { headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `honeygroove_${format}_${Date.now()}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`${format === 'story' ? 'story' : 'square'} image downloaded.`);
      setShareDialogOpen(false);
    } catch {
      toast.error('something went wrong. please try again.');
    }
  };

  return (
    <Card ref={cardRef} className={`border-honey/30 overflow-hidden hover:shadow-honey transition-all ${highlighted ? 'ring-2 ring-honey shadow-lg shadow-honey/20' : ''} ${post.is_new_feature ? 'shadow-md' : ''}`} style={post.is_new_feature ? { backgroundColor: '#f3faf5' } : undefined} data-testid={`post-${post.id}`}>
      {/* Pinned indicator */}
      {post.is_pinned && (
        <div className="px-4 py-1.5 bg-honey/10 border-b border-honey/20 flex items-center gap-1.5 text-xs text-honey-amber" data-testid={`pinned-${post.id}`}>
          <Pin className="w-3 h-3" /> pinned
        </div>
      )}
      {/* Header */}
      <div className="p-4 pb-2">
        <div className="flex items-center gap-3">
          <Link to={`/profile/${post.user?.username}`}>
            <BeeAvatar user={post.user} />
          </Link>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <Link to={`/profile/${post.user?.username}`} className="font-medium hover:underline">
                @{post.user?.username}
              </Link>
              {post.user?.founding_member && (
                <span title="founding member of the Honey Groove" className="inline-block ml-1 cursor-help" style={{ color: '#C8861A', fontSize: '12px' }}>🍯</span>
              )}
              {post.user?.title_label && <TitleBadge label={post.user.title_label} />}
              <PostTypeBadge type={post.post_type} mood={post.mood} />
              {post.is_new_feature && <NewFeatureBadge />}
            </div>
            <p className="text-xs text-muted-foreground">{timeAgo}</p>
          </div>
          {(isOwner || isAdmin) && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="p-1.5 rounded-full hover:bg-honey/10 transition-colors" data-testid={`post-menu-${post.id}`}>
                  <MoreVertical className="w-4 h-4 text-muted-foreground" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {isOwner && (
                  <DropdownMenuItem onClick={() => setDeleteDialogOpen(true)} className="text-red-600" data-testid={`delete-post-${post.id}`}>
                    <Trash2 className="mr-2 h-4 w-4" /> Delete Post
                  </DropdownMenuItem>
                )}
                {isAdmin && (
                  <DropdownMenuItem onClick={() => onPin(post.id, post.is_pinned)} data-testid={`pin-post-${post.id}`}>
                    <Pin className="mr-2 h-4 w-4" /> {post.is_pinned ? 'Unpin Post' : 'Pin to Top'}
                  </DropdownMenuItem>
                )}
                {isAdmin && (
                  <DropdownMenuItem onClick={() => onToggleFeature(post.id, post.is_new_feature)} data-testid={`toggle-feature-${post.id}`}>
                    <Sparkles className="mr-2 h-4 w-4" /> {post.is_new_feature ? 'Remove New Feature' : 'Tag as New Feature'}
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>

      {/* Post Type-Specific Body */}
      <div className="px-4 py-2">
        <PostCardBody post={post} onAlbumClick={onAlbumClick} />
      </div>

      {/* Actions */}
      <div className="px-4 py-3 flex items-center gap-4 border-t border-honey/20">
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onLike(post.id, post.is_liked); }}
          className={`flex items-center gap-1.5 text-sm transition-all p-2 -m-2 rounded-full ${post.is_liked ? 'text-amber-600 honey-like-burst' : 'text-muted-foreground hover:text-amber-500'}`}
          style={{ touchAction: 'manipulation' }}
          data-testid={`like-btn-${post.id}`}
        >
          <Heart className={`w-4 h-4 transition-all duration-200 ${post.is_liked ? 'fill-current scale-110 honey-like-pop' : 'hover:scale-110'}`} />
          {post.likes_count > 0 && <span className={post.is_liked ? 'count-bump' : ''}>{post.likes_count}</span>}
        </button>
        <button
          onClick={handleToggleComments}
          className={`flex items-center gap-1.5 text-sm transition-colors ${showComments ? 'text-honey-amber' : 'text-muted-foreground hover:text-honey-amber'}`}
          data-testid={`comment-btn-${post.id}`}
        >
          <MessageCircle className={`w-4 h-4 ${showComments ? 'fill-honey/30' : ''}`} />
          {post.comments_count > 0 && post.comments_count}
          {showComments ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
        {/* Share button — hidden until feature is ready */}
      </div>

      {/* Comments */}
      {showComments && (
        <div className="px-4 pb-4 border-t border-honey/20 bg-honey/5">
          {loadingComments ? (
            <div className="py-4 text-center text-sm text-muted-foreground">Loading comments...</div>
          ) : (
            <>
              <div className="py-3 space-y-3 max-h-80 overflow-y-auto">
                {comments.length === 0 ? (
                  <p className="text-center text-sm text-muted-foreground py-2">No comments yet. Be the first!</p>
                ) : (
                  comments.map(comment => (
                    <CommentThread key={comment.id} comment={comment} onReply={handleReply} onLike={handleCommentLike} />
                  ))
                )}
              </div>
              {/* Reply indicator */}
              {replyTo && (
                <div className="flex items-center gap-2 pt-2 text-xs text-honey-amber">
                  <Reply className="w-3 h-3" />
                  <span>replying to @{replyTo.username}</span>
                  <button onClick={() => { setReplyTo(null); setNewComment(''); }} className="ml-auto text-muted-foreground hover:text-red-500">cancel</button>
                </div>
              )}
              {/* Mention autocomplete */}
              <div className="relative">
                {showMentions && (
                  <div className="absolute bottom-full left-0 right-0 bg-white border border-honey/30 rounded-lg shadow-lg z-10 max-h-40 overflow-y-auto mb-1" data-testid="mention-dropdown">
                    {mentionResults.map(u => (
                      <button key={u.id} onClick={() => insertMention(u.username)} className="w-full flex items-center gap-2 px-3 py-2 hover:bg-honey/10 text-sm text-left" data-testid={`mention-${u.username}`}>
                        <BeeAvatar user={u} className="h-6 w-6" />
                        <span>@{u.username}</span>
                      </button>
                    ))}
                  </div>
                )}
                <form onSubmit={handleSubmitComment} className="flex gap-2 pt-2 border-t border-honey/20">
                  <Input
                    ref={commentInputRef}
                    placeholder={replyTo ? `Reply to @${replyTo.username}...` : "Write a comment..."}
                    value={newComment}
                    onChange={handleCommentInputChange}
                    onKeyDown={(e) => { if (e.key === 'Enter') e.preventDefault(); }}
                    className="flex-1 h-9 text-sm border-honey/50"
                    data-testid={`comment-input-${post.id}`}
                  />
                  <Button
                    type="submit"
                    size="sm"
                    disabled={submitting || !newComment.trim()}
                    className="bg-honey text-vinyl-black hover:bg-honey-amber h-9 px-3"
                    data-testid={`comment-submit-${post.id}`}
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </form>
              </div>
            </>
          )}
        </div>
      )}

      {/* Share Dialog — hidden until feature is ready */}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Are you sure you want to delete this post?</AlertDialogTitle>
            <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid={`cancel-delete-${post.id}`}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => onDelete(post.id)}
              className="bg-red-600 text-white hover:bg-red-700"
              data-testid={`confirm-delete-${post.id}`}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
};

const HivePage = () => {
  usePageTitle('The Hive');
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [posts, setPosts] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [showBackToTop, setShowBackToTop] = useState(false);
  // Following filter works by fetching the user's following list
  const [followingIds, setFollowingIds] = useState([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false);

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
    { key: 'all', label: 'All' },
    { key: 'NOW_SPINNING', label: 'Now Spinning' },
    { key: 'NEW_HAUL', label: 'New Haul' },
    { key: 'ISO', label: 'ISO' },
    { key: 'listing', label: 'For Sale/Trade' },
    { key: 'NOTE', label: 'A Note' },
    { key: 'NEW_FEATURE', label: 'New Feature' },
  ];

  const headers = { Authorization: `Bearer ${token}` };

  const FEED_LIMIT = 50;

  const fetchFeed = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/feed`, {
        params: { limit: FEED_LIMIT, skip: 0 },
        headers: { Authorization: `Bearer ${token}` }
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
    } catch (error) {
      toast.error('something went wrong loading the hive.');
    } finally {
      setLoading(false);
    }
  }, [API, token, targetPostId]);

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const response = await axios.get(`${API}/feed`, {
        params: { limit: FEED_LIMIT, skip: posts.length },
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
  };

  const fetchRecords = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/records`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecords(response.data);
    } catch { /* ignore */ }
  }, [API, token]);

  useEffect(() => {
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

  // Back to top scroll listener
  useEffect(() => {
    const onScroll = () => setShowBackToTop(window.scrollY > 300);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' });

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
    // Apply content type filter
    if (activeFilter === 'all') return result;
    if (activeFilter === 'listing') return result.filter(p => p.post_type === 'listing_sale' || p.post_type === 'listing_trade');
    if (activeFilter === 'NEW_FEATURE') return result.filter(p => p.is_new_feature);
    return result.filter(p => p.post_type === activeFilter);
  }, [posts, feedMode, activeFilter, followingIds, user?.id, promptFilter]);

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


  // Album detail — open unified variant modal
  const handleAlbumClick = (record) => {
    openVariantModal({
      artist: record.artist,
      album: record.title || record.album,
      variant: record.color_variant || record.variant || '',
      discogs_id: record.discogs_id,
      cover_url: record.cover_url,
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
      <div className="max-w-2xl mx-auto px-4 py-8 pt-16 md:pt-24">
        <h1 className="font-heading text-3xl mb-6">The Hive</h1>
        {[1, 2, 3].map(i => (
          <Card key={i} className="mb-4 p-6">
            <div className="flex items-start gap-4">
              <Skeleton className="w-12 h-12 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-32 w-full rounded-lg" />
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8">
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
        <div className="mb-4 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200/50 text-center"
          style={{ animation: 'bingoCelebFadeIn 300ms ease-out' }}
          data-testid="welcome-banner"
        >
          <p className="text-amber-700 font-medium italic" style={{ fontFamily: '"DM Serif Display", serif' }}>
            welcome to the hive. 🐝 you're in.
          </p>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-3xl text-vinyl-black">The Hive</h1>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="w-2 h-2 bg-honey rounded-full animate-pulse" />
          Live Feed
        </div>
      </div>

      {/* Composer Bar */}
      <ComposerBar onPostCreated={handlePostCreated} records={records} />

      {/* Feed Mode Toggle: All | Following */}
      <div className="flex items-center mb-3" data-testid="feed-mode-toggle">
        <div className="flex w-52 bg-stone-100 rounded-full p-1">
          <button
            onClick={() => setFeedMode('all')}
            className={`flex-1 py-1.5 rounded-full text-sm font-medium text-center transition-all duration-250 ${
              feedMode === 'all'
                ? 'text-white shadow-sm'
                : 'text-stone-500 hover:text-stone-700'
            }`}
            style={feedMode === 'all' ? { background: 'linear-gradient(135deg, #F4B942 0%, #C8861A 100%)' } : {}}
            data-testid="feed-mode-all"
          >
            All
          </button>
          <button
            onClick={() => setFeedMode('following')}
            className={`flex-1 py-1.5 rounded-full text-sm font-medium text-center transition-all duration-250 ${
              feedMode === 'following'
                ? 'text-white shadow-sm'
                : 'text-stone-500 hover:text-stone-700'
            }`}
            style={feedMode === 'following' ? { background: 'linear-gradient(135deg, #F4B942 0%, #C8861A 100%)' } : {}}
            data-testid="feed-mode-following"
          >
            Following
          </button>
        </div>
      </div>

      {/* Content Filter Bar */}
      <div className="flex flex-wrap gap-1.5 mb-4" data-testid="feed-filter-bar">
        {FEED_FILTERS.map(f => {
          const s = PILL_STYLES[f.key] || PILL_STYLES.all;
          const isActive = activeFilter === f.key;
          return (
            <button
              key={f.key}
              onClick={() => setActiveFilter(f.key)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all border ${
                isActive
                  ? `${s.bg} ${s.text} ${s.border} shadow-sm font-semibold`
                  : `bg-white ${s.text} ${s.border} hover:${s.bg}`
              }`}
              style={!isActive ? { opacity: 0.65 } : undefined}
              data-testid={`filter-${f.key}`}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      {/* Prompt Filter Banner */}
      {promptFilter && promptFilterText && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200/60 flex items-center justify-between gap-3" data-testid="prompt-filter-banner">
          <p className="text-sm text-amber-800 font-medium italic truncate">
            Viewing responses to: {promptFilterText}
          </p>
          <Button
            size="sm" variant="ghost"
            onClick={() => setSearchParams({})}
            className="shrink-0 text-xs text-amber-600 hover:text-amber-800"
            data-testid="clear-prompt-filter"
          >
            Clear Filter
          </Button>
        </div>
      )}

      {/* Daily Prompt */}
      <DailyPromptCard records={records} onPostCreated={handlePostCreated} />

      {filteredPosts.length === 0 ? (
        <Card className="p-8 text-center border-honey/30" data-testid="hive-empty-state">
          <span className="text-4xl block mb-3">🐝</span>
          <p className="italic text-muted-foreground mb-4" style={{ fontFamily: '"DM Serif Display", serif', color: '#8A6B4A' }}>
            {feedMode === 'following' && activeFilter === 'all'
              ? 'nothing here yet. follow some collectors to see their posts.'
              : feedMode === 'following'
                ? `no ${FEED_FILTERS.find(f => f.key === activeFilter)?.label || ''} posts from people you follow yet.`
                : activeFilter === 'all'
                  ? 'the hive is just getting started. be the first to post.'
                  : `no ${FEED_FILTERS.find(f => f.key === activeFilter)?.label || ''} posts yet.`}
          </p>
          {feedMode === 'following' ? (
            <Button onClick={() => navigate('/nectar')} className="bg-amber-500 text-white hover:bg-amber-600 rounded-full" data-testid="find-collectors-btn">
              browse collectors
            </Button>
          ) : (
            <Button onClick={() => {}} className="bg-amber-500 text-white hover:bg-amber-600 rounded-full" data-testid="hive-empty-cta">
              post something
            </Button>
          )}
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredPosts.map(post => (
            <PostCard
              key={post.id}
              post={post}
              onLike={handleLike}
              onCommentCountChange={updatePostCommentCount}
              onDelete={handleDeletePost}
              onAlbumClick={handleAlbumClick}
              onPin={handlePinPost}
              onToggleFeature={handleToggleFeature}
              token={token}
              API={API}
              currentUserId={user?.id}
              isAdmin={user?.is_admin}
              highlighted={post.id === targetPostId}
              autoOpenComments={post.id === targetPostId && !!targetCommentId}
            />
          ))}
        </div>
      )}

      {/* View Older Posts */}
      {filteredPosts.length > 0 && hasMore && activeFilter === 'all' && feedMode === 'all' && (
        <div className="flex justify-center pt-6 pb-2">
          <Button
            onClick={loadMore}
            disabled={loadingMore}
            variant="outline"
            className="rounded-full border-honey/50 text-honey-amber hover:bg-honey/10 px-6"
            data-testid="load-more-btn"
          >
            {loadingMore ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            {loadingMore ? 'loading...' : 'view older posts'}
          </Button>
        </div>
      )}
      {filteredPosts.length > 0 && !hasMore && activeFilter === 'all' && feedMode === 'all' && (
        <p className="text-center text-sm text-muted-foreground pt-6 pb-2 italic">you've reached the beginning of the hive.</p>
      )}

      {/* Back to Top */}
      {showBackToTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 z-40 w-10 h-10 rounded-full bg-vinyl-black text-white shadow-lg flex items-center justify-center hover:bg-vinyl-black/80 transition-all animate-in fade-in slide-in-from-bottom-4 duration-300"
          data-testid="back-to-top-btn"
          aria-label="Back to top"
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      )}

    </div>
  );
};

export default HivePage;
