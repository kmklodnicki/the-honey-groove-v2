import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Heart, MessageCircle, Share2, Disc, Send, ChevronDown, ChevronUp } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import ComposerBar from '../components/ComposerBar';
import { PostTypeBadge, PostCardBody } from '../components/PostCards';
import { usePageTitle } from '../hooks/usePageTitle';
import { DailyPromptCard } from '../components/DailyPrompt';
import OnboardingModal from '../components/OnboardingModal';

// Bee Avatar Component
const BeeAvatar = ({ user, className = "h-10 w-10" }) => {
  const firstLetter = user?.username?.charAt(0).toUpperCase() || '?';
  const hasCustomAvatar = user?.avatar_url && !user.avatar_url.includes('dicebear');
  return (
    <Avatar className={`${className} border-2 border-honey/30`}>
      {hasCustomAvatar && <AvatarImage src={user.avatar_url} alt={user?.username} />}
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

const PostCard = ({ post, onLike, onCommentCountChange, token, API }) => {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loadingComments, setLoadingComments] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);

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
                <span title="founding member of the Honey Groove 🐝" className="inline-block ml-1 cursor-help" style={{ color: '#C8861A', fontSize: '12px' }}>🍯</span>
              )}
              <PostTypeBadge type={post.post_type} mood={post.mood} />
            </div>
            <p className="text-xs text-muted-foreground">{timeAgo}</p>
          </div>
        </div>
      </div>

      {/* Post Type-Specific Body */}
      <div className="px-4 py-2">
        <PostCardBody post={post} />
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
        {post.record && (
          <button
            onClick={() => setShareDialogOpen(true)}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-vinyl-black transition-colors ml-auto"
            data-testid={`share-btn-${post.id}`}
          >
            <Share2 className="w-4 h-4" />
          </button>
        )}
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

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading">Share This Post</DialogTitle>
            <DialogDescription>Choose a format for your shareable graphic</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <button onClick={() => handleShare('square')} className="p-4 border-2 border-honey/30 rounded-xl hover:border-honey hover:bg-honey/10 transition-all text-center" data-testid="share-square-btn">
              <div className="w-16 h-16 bg-honey/20 rounded-lg mx-auto mb-2 flex items-center justify-center">
                <div className="w-10 h-10 border-2 border-honey-amber rounded" />
              </div>
              <p className="font-medium">Square</p>
              <p className="text-xs text-muted-foreground">1080 × 1080</p>
            </button>
            <button onClick={() => handleShare('story')} className="p-4 border-2 border-honey/30 rounded-xl hover:border-honey hover:bg-honey/10 transition-all text-center" data-testid="share-story-btn">
              <div className="w-16 h-16 bg-honey/20 rounded-lg mx-auto mb-2 flex items-center justify-center">
                <div className="w-6 h-10 border-2 border-honey-amber rounded" />
              </div>
              <p className="font-medium">Story</p>
              <p className="text-xs text-muted-foreground">1080 × 1920</p>
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

const HivePage = () => {
  usePageTitle('The Hive');
  const { user, token, API } = useAuth();
  const [posts, setPosts] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false);

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
              token={token}
              API={API}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default HivePage;
