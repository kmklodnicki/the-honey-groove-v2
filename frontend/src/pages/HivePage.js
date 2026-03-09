import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Heart, MessageCircle, Share2, Disc, Send, ChevronDown, ChevronUp, MoreVertical, Trash2, Play, ShoppingBag, ArrowRightLeft, Plus, Calendar, Music2, Loader2, Pin, Reply, ArrowUp } from 'lucide-react';
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
import { PostTypeBadge, PostCardBody } from '../components/PostCards';
import { TitleBadge } from '../components/TitleBadge';
import { usePageTitle } from '../hooks/usePageTitle';
import { DailyPromptCard } from '../components/DailyPrompt';
import OnboardingModal from '../components/OnboardingModal';
import AlbumArt from '../components/AlbumArt';

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

const PostCard = ({ post, onLike, onCommentCountChange, onDelete, onAlbumClick, onPin, token, API, currentUserId, isAdmin, highlighted, autoOpenComments }) => {
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
    <Card ref={cardRef} className={`border-honey/30 overflow-hidden hover:shadow-honey transition-all ${highlighted ? 'ring-2 ring-honey shadow-lg shadow-honey/20' : ''}`} data-testid={`post-${post.id}`}>
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
          onClick={() => onLike(post.id, post.is_liked)}
          className={`flex items-center gap-1.5 text-sm transition-colors ${post.is_liked ? 'text-red-500' : 'text-muted-foreground hover:text-red-500'}`}
          data-testid={`like-btn-${post.id}`}
        >
          <Heart className={`w-4 h-4 ${post.is_liked ? 'fill-current' : ''}`} />
          {post.likes_count > 0 && post.likes_count}
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
  // Following filter works because /feed already returns only followed users + self
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false);

  const targetPostId = searchParams.get('post');
  const targetCommentId = searchParams.get('comment');

  // Album detail modal state
  const [albumModal, setAlbumModal] = useState(null); // { record }
  const [albumModalLoading, setAlbumModalLoading] = useState(false);
  const [albumOwnership, setAlbumOwnership] = useState(null);
  const [albumRelease, setAlbumRelease] = useState(null);
  const [spinningAlbum, setSpinningAlbum] = useState(false);
  const [addingAlbum, setAddingAlbum] = useState(false);

  const [activeFilter, setActiveFilter] = useState('all');

  const FEED_FILTERS = [
    { key: 'all', label: 'All', activeClass: 'bg-stone-700 text-white', inactiveClass: 'bg-stone-100 text-stone-500 hover:bg-stone-200' },
    { key: 'NOW_SPINNING', label: 'Now Spinning', activeClass: 'bg-blue-400 text-white', inactiveClass: 'bg-blue-50 text-blue-400 hover:bg-blue-100' },
    { key: 'NEW_HAUL', label: 'New Haul', activeClass: 'bg-pink-400 text-white', inactiveClass: 'bg-pink-50 text-pink-400 hover:bg-pink-100' },
    { key: 'ISO', label: 'ISO', activeClass: 'bg-orange-400 text-white', inactiveClass: 'bg-orange-50 text-orange-400 hover:bg-orange-100' },
    { key: 'listing', label: 'For Sale/Trade', activeClass: 'bg-green-400 text-white', inactiveClass: 'bg-green-50 text-green-400 hover:bg-green-100' },
    { key: 'NOTE', label: 'A Note', activeClass: 'bg-yellow-400 text-yellow-900', inactiveClass: 'bg-yellow-50 text-yellow-500 hover:bg-yellow-100' },
    { key: 'following', label: 'Following', activeClass: 'bg-purple-400 text-white', inactiveClass: 'bg-purple-50 text-purple-400 hover:bg-purple-100' },
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
    if (activeFilter === 'all') return posts;
    if (activeFilter === 'following') return posts.filter(p => p.user_id !== user?.id);
    if (activeFilter === 'listing') return posts.filter(p => p.post_type === 'listing_sale' || p.post_type === 'listing_trade');
    return posts.filter(p => p.post_type === activeFilter);
  }, [posts, activeFilter, user?.id]);

  const handleLike = async (postId, isLiked) => {
    try {
      if (isLiked) {
        await axios.delete(`${API}/posts/${postId}/like`, { headers: { Authorization: `Bearer ${token}` }});
      } else {
        await axios.post(`${API}/posts/${postId}/like`, {}, { headers: { Authorization: `Bearer ${token}` }});
      }
      setPosts(prev => prev.map(post => {
        if (post.id === postId) {
          return { ...post, is_liked: !isLiked, likes_count: isLiked ? post.likes_count - 1 : post.likes_count + 1 };
        }
        return post;
      }));
    } catch { /* ignore */ }
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

  // Album detail modal
  const handleAlbumClick = async (record) => {
    setAlbumModalLoading(true);
    setAlbumOwnership(null);
    setAlbumRelease(null);
    setAlbumModal({ record });

    const discogsId = record.discogs_id;
    const ownershipPromise = discogsId
      ? axios.get(`${API}/records/check-ownership?discogs_id=${discogsId}`, { headers }).catch(() => null)
      : record.id
        ? axios.get(`${API}/records/check-ownership?artist=${encodeURIComponent(record.artist)}&title=${encodeURIComponent(record.title)}`, { headers }).catch(() => null)
        : Promise.resolve(null);
    const releasePromise = discogsId
      ? axios.get(`${API}/discogs/release/${discogsId}`, { headers }).catch(() => null)
      : Promise.resolve(null);

    const [ownerResp, releaseResp] = await Promise.all([ownershipPromise, releasePromise]);
    if (ownerResp?.data) setAlbumOwnership(ownerResp.data);
    else setAlbumOwnership({ in_collection: !!record.id, record_id: record.id || null });
    if (releaseResp?.data) setAlbumRelease(releaseResp.data);
    setAlbumModalLoading(false);
  };

  const handleAlbumAddToCollection = async () => {
    if (!albumModal?.record) return;
    setAddingAlbum(true);
    const r = albumModal.record;
    try {
      const res = await axios.post(`${API}/records`, {
        discogs_id: r.discogs_id,
        title: r.title,
        artist: r.artist,
        cover_url: r.cover_url,
        year: r.year,
        format: albumRelease?.format?.[0] || 'Vinyl',
      }, { headers });
      toast.success('added to your collection!');
      setAlbumOwnership({ in_collection: true, record_id: res.data.id });
      fetchRecords();
    } catch (err) {
      if (err.response?.status === 409) toast.info('already in your collection.');
      else toast.error('could not add. try again.');
    }
    setAddingAlbum(false);
  };

  const handleAlbumSpin = async () => {
    if (!albumOwnership?.record_id) return;
    setSpinningAlbum(true);
    try {
      await axios.post(`${API}/spins`, { record_id: albumOwnership.record_id }, { headers });
      toast.success('spin logged!');
    } catch { toast.error('could not log spin. try again.'); }
    setSpinningAlbum(false);
  };

  const handleAlbumAddWantlist = async () => {
    const r = albumModal?.record;
    if (!r) return;
    try {
      await axios.post(`${API}/composer/iso`, {
        artist: r.artist, album: r.title, discogs_id: r.discogs_id, cover_url: r.cover_url, year: r.year,
      }, { headers });
      toast.success('added to your wantlist!');
    } catch (err) {
      if (err.response?.status === 409) toast.info('already on your wantlist.');
      else toast.error('could not add. try again.');
    }
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

      {/* Filter Bar */}
      <div className="flex flex-wrap gap-1.5 mb-4" data-testid="feed-filter-bar">
        {FEED_FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setActiveFilter(f.key)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
              activeFilter === f.key ? f.activeClass + ' shadow-sm' : f.inactiveClass
            }`}
            data-testid={`filter-${f.key}`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Daily Prompt */}
      <DailyPromptCard records={records} onPostCreated={handlePostCreated} />

      {filteredPosts.length === 0 ? (
        <Card className="p-8 text-center border-honey/30" data-testid="hive-empty-state">
          <span className="text-4xl block mb-3">🐝</span>
          <p className="italic text-muted-foreground mb-4" style={{ fontFamily: '"DM Serif Display", serif', color: '#8A6B4A' }}>
            {activeFilter === 'following'
              ? 'nothing here yet. follow some collectors to see their posts.'
              : activeFilter === 'all'
                ? 'the hive is just getting started. be the first to post.'
                : `no ${FEED_FILTERS.find(f => f.key === activeFilter)?.label || ''} posts yet.`}
          </p>
          {activeFilter === 'following' ? (
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
      {filteredPosts.length > 0 && hasMore && activeFilter === 'all' && (
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
      {filteredPosts.length > 0 && !hasMore && activeFilter === 'all' && (
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

      {/* Album Detail Modal */}
      <Dialog open={!!albumModal} onOpenChange={(open) => { if (!open) { setAlbumModal(null); setAlbumOwnership(null); setAlbumRelease(null); } }}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto" aria-describedby="album-modal-desc">
          <DialogHeader>
            <DialogTitle className="font-heading text-lg">Album Details</DialogTitle>
            <p id="album-modal-desc" className="sr-only">Details and actions for this album</p>
          </DialogHeader>
          {albumModal && (
            <div>
              {/* Album card */}
              <div className="flex items-center gap-4 mb-3 bg-honey/10 rounded-xl p-3">
                {albumModal.record?.cover_url ? (
                  <AlbumArt src={albumModal.record.cover_url} alt={`${albumModal.record.title} by ${albumModal.record.artist}`} className="w-20 h-20 rounded-lg object-cover shadow" />
                ) : (
                  <div className="w-20 h-20 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-8 h-8 text-honey" /></div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-heading text-base leading-tight" data-testid="hive-modal-album-title">{albumModal.record?.title}</p>
                  <p className="text-sm text-honey-amber italic" data-testid="hive-modal-album-artist">{albumModal.record?.artist}{albumModal.record?.year ? ` (${albumModal.record.year})` : ''}</p>
                </div>
              </div>

              {/* Variant / Pressing Details */}
              {(albumRelease || albumModal.record?.format) && (
                <div className="flex flex-wrap gap-1.5 mb-4" data-testid="hive-modal-variant-details">
                  {(albumRelease?.year || albumModal.record?.year) && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                      <Calendar className="w-3 h-3" /> {albumRelease?.year || albumModal.record?.year}
                    </span>
                  )}
                  {albumRelease?.label?.[0] && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                      {albumRelease.label[0]}
                    </span>
                  )}
                  {albumRelease?.catno && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                      {albumRelease.catno}
                    </span>
                  )}
                  {albumRelease?.format?.[0] && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                      <Disc className="w-3 h-3" /> {albumRelease.format.join(', ')}
                    </span>
                  )}
                  {albumRelease?.country && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-honey/10 text-xs text-vinyl-black/70">
                      {albumRelease.country}
                    </span>
                  )}
                  {albumRelease?.color_variant && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-xs text-amber-800 font-medium">
                      {albumRelease.color_variant}
                    </span>
                  )}
                </div>
              )}

              {/* Contextual Action Buttons */}
              {albumModalLoading ? (
                <div className="flex justify-center py-3"><Loader2 className="w-5 h-5 animate-spin text-honey-amber" /></div>
              ) : albumOwnership?.in_collection ? (
                <div className="flex flex-wrap gap-2 mb-4" data-testid="hive-modal-owner-actions">
                  <Button size="sm" className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs"
                    onClick={handleAlbumSpin} disabled={spinningAlbum} data-testid="hive-modal-log-spin">
                    {spinningAlbum ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Play className="w-3 h-3 mr-1" />} Log a Spin
                  </Button>
                  <Button size="sm" variant="outline" className="rounded-full text-xs border-honey/50 text-honey-amber hover:bg-honey/10"
                    onClick={() => {
                      const r = albumModal.record;
                      setAlbumModal(null);
                      navigate(`/honeypot?create=sale&artist=${encodeURIComponent(r.artist)}&album=${encodeURIComponent(r.title)}&discogs_id=${r.discogs_id || ''}&cover_url=${encodeURIComponent(r.cover_url || '')}&year=${r.year || ''}`);
                    }} data-testid="hive-modal-list-sale">
                    <ShoppingBag className="w-3 h-3 mr-1" /> List for Sale
                  </Button>
                  <Button size="sm" variant="outline" className="rounded-full text-xs border-honey/50 text-honey-amber hover:bg-honey/10"
                    onClick={() => {
                      const r = albumModal.record;
                      setAlbumModal(null);
                      navigate(`/honeypot?create=trade&artist=${encodeURIComponent(r.artist)}&album=${encodeURIComponent(r.title)}&discogs_id=${r.discogs_id || ''}&cover_url=${encodeURIComponent(r.cover_url || '')}&year=${r.year || ''}`);
                    }} data-testid="hive-modal-offer-trade">
                    <ArrowRightLeft className="w-3 h-3 mr-1" /> Offer to Trade
                  </Button>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2 mb-4" data-testid="hive-modal-nonowner-actions">
                  <Button size="sm" className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-xs"
                    onClick={handleAlbumAddToCollection} disabled={addingAlbum} data-testid="hive-modal-add-collection">
                    {addingAlbum ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Plus className="w-3 h-3 mr-1" />} Add to Collection
                  </Button>
                  <Button size="sm" variant="outline" className="rounded-full text-xs border-honey/50 text-honey-amber hover:bg-honey/10"
                    onClick={handleAlbumAddWantlist} data-testid="hive-modal-add-wantlist">
                    <Heart className="w-3 h-3 mr-1" /> Add to Wantlist
                  </Button>
                </div>
              )}

              {/* Discogs link */}
              {albumModal.record?.discogs_id && (
                <a href={`https://www.discogs.com/release/${albumModal.record.discogs_id}`} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-vinyl-black/5 text-xs text-vinyl-black/60 hover:bg-vinyl-black/10 transition-colors" data-testid="hive-modal-discogs-link">
                  <Music2 className="w-3 h-3" /> View on Discogs
                </a>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HivePage;
