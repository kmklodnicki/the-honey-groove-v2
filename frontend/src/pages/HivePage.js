import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Heart, MessageCircle, Share2, Disc, Send, ChevronDown, ChevronUp, MoreVertical, Trash2, Play, ShoppingBag, ArrowRightLeft, Plus, Calendar, Music2, Loader2 } from 'lucide-react';
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

const PostCard = ({ post, onLike, onCommentCountChange, onDelete, onAlbumClick, token, API, currentUserId }) => {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loadingComments, setLoadingComments] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

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

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/posts/${post.id}/comments`,
        { post_id: post.id, content: newComment.trim() },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      setComments([...comments, response.data]);
      setNewComment('');
      onCommentCountChange(post.id, 1);
    } catch (error) {
      toast.error('something went wrong. please try again.');
    } finally {
      setSubmitting(false);
    }
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
    <Card className="border-honey/30 overflow-hidden hover:shadow-honey transition-shadow" data-testid={`post-${post.id}`}>
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
              <PostTypeBadge type={post.post_type} mood={post.mood} />
            </div>
            <p className="text-xs text-muted-foreground">{timeAgo}</p>
          </div>
          {isOwner && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="p-1.5 rounded-full hover:bg-honey/10 transition-colors" data-testid={`post-menu-${post.id}`}>
                  <MoreVertical className="w-4 h-4 text-muted-foreground" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setDeleteDialogOpen(true)} className="text-red-600" data-testid={`delete-post-${post.id}`}>
                  <Trash2 className="mr-2 h-4 w-4" /> Delete Post
                </DropdownMenuItem>
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
              <div className="py-3 space-y-3 max-h-64 overflow-y-auto">
                {comments.length === 0 ? (
                  <p className="text-center text-sm text-muted-foreground py-2">No comments yet. Be the first!</p>
                ) : (
                  comments.map(comment => (
                    <div key={comment.id} className="flex gap-2" data-testid={`comment-${comment.id}`}>
                      <Link to={`/profile/${comment.user?.username}`}>
                        <BeeAvatar user={comment.user} className="h-8 w-8" />
                      </Link>
                      <div className="flex-1 bg-white rounded-lg px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Link to={`/profile/${comment.user?.username}`} className="font-medium text-sm hover:underline">
                            @{comment.user?.username}
                          </Link>
                          <span className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
                          </span>
                        </div>
                        <p className="text-sm mt-1">{comment.content}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
              <form onSubmit={handleSubmitComment} className="flex gap-2 pt-2 border-t border-honey/20">
                <Input
                  placeholder="Write a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
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
  const [posts, setPosts] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false);

  // Album detail modal state
  const [albumModal, setAlbumModal] = useState(null); // { record }
  const [albumModalLoading, setAlbumModalLoading] = useState(false);
  const [albumOwnership, setAlbumOwnership] = useState(null);
  const [albumRelease, setAlbumRelease] = useState(null);
  const [spinningAlbum, setSpinningAlbum] = useState(false);
  const [addingAlbum, setAddingAlbum] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchFeed = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/feed`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPosts(response.data);
    } catch (error) {
      toast.error('something went wrong loading the hive.');
    } finally {
      setLoading(false);
    }
  }, [API, token]);

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

      {/* Daily Prompt */}
      <DailyPromptCard records={records} onPostCreated={handlePostCreated} />

      {posts.length === 0 ? (
        <Card className="p-8 text-center border-honey/30" data-testid="hive-empty-state">
          <span className="text-4xl block mb-3">🐝</span>
          <p className="italic text-muted-foreground mb-4" style={{ fontFamily: '"DM Serif Display", serif', color: '#8A6B4A' }}>
            the hive is just getting started. be the first to post.
          </p>
          <Button onClick={() => {}} className="bg-amber-500 text-white hover:bg-amber-600 rounded-full" data-testid="hive-empty-cta">
            post something
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {posts.map(post => (
            <PostCard
              key={post.id}
              post={post}
              onLike={handleLike}
              onCommentCountChange={updatePostCommentCount}
              onDelete={handleDeletePost}
              onAlbumClick={handleAlbumClick}
              token={token}
              API={API}
              currentUserId={user?.id}
            />
          ))}
        </div>
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
                  <AlbumArt src={albumModal.record.cover_url} alt="" className="w-20 h-20 rounded-lg object-cover shadow" />
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
