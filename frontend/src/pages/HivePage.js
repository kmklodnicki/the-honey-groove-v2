import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Heart, MessageCircle, Share2, Disc, Package, BarChart3, Send, ChevronDown, ChevronUp, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

const HivePage = () => {
  const { user, token, API } = useAuth();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeed();
  }, []);

  const fetchFeed = async () => {
    try {
      const response = await axios.get(`${API}/feed`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPosts(response.data);
    } catch (error) {
      console.error('Failed to fetch feed:', error);
      toast.error('Failed to load The Hive');
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (postId, isLiked) => {
    try {
      if (isLiked) {
        await axios.delete(`${API}/posts/${postId}/like`, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await axios.post(`${API}/posts/${postId}/like`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      
      setPosts(posts.map(post => {
        if (post.id === postId) {
          return {
            ...post,
            is_liked: !isLiked,
            likes_count: isLiked ? post.likes_count - 1 : post.likes_count + 1
          };
        }
        return post;
      }));
    } catch (error) {
      console.error('Like error:', error);
    }
  };

  const updatePostCommentCount = (postId, delta) => {
    setPosts(posts.map(post => {
      if (post.id === postId) {
        return {
          ...post,
          comments_count: post.comments_count + delta
        };
      }
      return post;
    }));
  };

  const getPostIcon = (postType) => {
    switch (postType) {
      case 'spin':
        return <Disc className="w-4 h-4 text-honey-amber" />;
      case 'haul':
        return <Package className="w-4 h-4 text-honey-amber" />;
      case 'weekly_summary':
        return <BarChart3 className="w-4 h-4 text-honey-amber" />;
      default:
        return <Disc className="w-4 h-4 text-honey-amber" />;
    }
  };

  const getPostLabel = (postType) => {
    switch (postType) {
      case 'spin':
        return 'is spinning';
      case 'haul':
        return 'shared a haul';
      case 'record_added':
        return 'added to collection';
      case 'weekly_summary':
        return 'shared their weekly';
      default:
        return 'posted';
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 pt-24">
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
    <div className="max-w-2xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-3xl text-vinyl-black">The Hive</h1>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="w-2 h-2 bg-honey rounded-full animate-pulse" />
          Live Feed
        </div>
      </div>

      {posts.length === 0 ? (
        <Card className="p-8 text-center border-honey/30">
          <div className="w-16 h-16 bg-honey/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Disc className="w-8 h-8 text-honey-amber" />
          </div>
          <h3 className="font-heading text-xl mb-2">The Hive is quiet</h3>
          <p className="text-muted-foreground mb-4">
            Follow some collectors or add records to see activity here!
          </p>
          <Link to="/explore">
            <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full">
              Explore Collectors
            </Button>
          </Link>
        </Card>
      ) : (
        <div className="space-y-4">
          {posts.map(post => (
            <PostCard 
              key={post.id} 
              post={post} 
              onLike={handleLike}
              onCommentCountChange={updatePostCommentCount}
              getPostIcon={getPostIcon}
              getPostLabel={getPostLabel}
              token={token}
              API={API}
            />
          ))}
        </div>
      )}
    </div>
  );
};

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

const PostCard = ({ post, onLike, onCommentCountChange, getPostIcon, getPostLabel, token, API }) => {
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
    if (!showComments && comments.length === 0) {
      fetchComments();
    }
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
      toast.success('Comment added!');
    } catch (error) {
      console.error('Failed to add comment:', error);
      toast.error('Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleShare = async (format) => {
    if (!post.record) {
      toast.error('Nothing to share');
      return;
    }

    try {
      const response = await axios.post(`${API}/share/generate`, 
        { 
          graphic_type: 'now_spinning', 
          record_id: post.record.id,
          format: format
        },
        { 
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      const formatSuffix = format === 'story' ? '_story' : '';
      a.download = `now_spinning${formatSuffix}_${post.record.artist}_${post.record.title}.png`.replace(/[^a-z0-9_.-]/gi, '_');
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`${format === 'story' ? 'Story' : 'Square'} image downloaded!`);
      setShareDialogOpen(false);
    } catch (error) {
      console.error('Share error:', error);
      toast.error('Failed to generate share image');
    }
  };

  return (
    <Card className="border-honey/30 overflow-hidden hover:shadow-honey transition-shadow" data-testid={`post-${post.id}`}>
      {/* Post Header */}
      <div className="p-4 pb-2">
        <div className="flex items-center gap-3">
          <Link to={`/profile/${post.user?.username}`}>
            <BeeAvatar user={post.user} />
          </Link>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <Link to={`/profile/${post.user?.username}`} className="font-medium hover:underline">
                @{post.user?.username}
              </Link>
              {getPostIcon(post.post_type)}
              <span className="text-sm text-muted-foreground">{getPostLabel(post.post_type)}</span>
            </div>
            <p className="text-xs text-muted-foreground">{timeAgo}</p>
          </div>
        </div>
      </div>

      {/* Post Content */}
      {post.record && (
        <Link to={`/record/${post.record.id}`} className="block px-4 py-2">
          <div className="flex gap-4 bg-honey/10 rounded-xl p-4 hover:bg-honey/20 transition-colors">
            {post.record.cover_url ? (
              <img 
                src={post.record.cover_url} 
                alt={post.record.title}
                className="w-20 h-20 rounded-lg object-cover shadow-md"
              />
            ) : (
              <div className="w-20 h-20 rounded-lg bg-vinyl-black flex items-center justify-center">
                <Disc className="w-8 h-8 text-honey" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-vinyl-black truncate">{post.record.title}</h4>
              <p className="text-sm text-muted-foreground truncate">{post.record.artist}</p>
              {post.record.year && (
                <p className="text-xs text-muted-foreground mt-1">{post.record.year}</p>
              )}
            </div>
          </div>
        </Link>
      )}

      {post.haul && (
        <Link to={`/haul/${post.haul.id}`} className="block px-4 py-2">
          <div className="bg-honey/10 rounded-xl p-4 hover:bg-honey/20 transition-colors">
            <h4 className="font-medium text-vinyl-black mb-2">{post.haul.title}</h4>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {post.haul.items?.slice(0, 4).map((item, idx) => (
                <div key={idx} className="flex-shrink-0">
                  {item.cover_url ? (
                    <img 
                      src={item.cover_url} 
                      alt={item.title}
                      className="w-16 h-16 rounded object-cover"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded bg-vinyl-black flex items-center justify-center">
                      <Disc className="w-6 h-6 text-honey" />
                    </div>
                  )}
                </div>
              ))}
              {post.haul.items?.length > 4 && (
                <div className="w-16 h-16 rounded bg-honey/30 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-medium">+{post.haul.items.length - 4}</span>
                </div>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{post.haul.items?.length} records</p>
          </div>
        </Link>
      )}

      {/* Post Actions */}
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

      {/* Comments Section */}
      {showComments && (
        <div className="px-4 pb-4 border-t border-honey/20 bg-honey/5">
          {loadingComments ? (
            <div className="py-4 text-center text-sm text-muted-foreground">Loading comments...</div>
          ) : (
            <>
              {/* Comment List */}
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

              {/* Add Comment Form */}
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
            <DialogTitle className="font-heading">Share This Spin</DialogTitle>
            <DialogDescription>Choose a format for your shareable graphic</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-sm text-muted-foreground">Choose a format for your shareable graphic:</p>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => handleShare('square')}
                className="p-4 border-2 border-honey/30 rounded-xl hover:border-honey hover:bg-honey/10 transition-all text-center group"
                data-testid="share-square-btn"
              >
                <div className="w-16 h-16 bg-honey/20 rounded-lg mx-auto mb-2 group-hover:bg-honey/30 transition-colors flex items-center justify-center">
                  <div className="w-10 h-10 border-2 border-honey-amber rounded"></div>
                </div>
                <p className="font-medium">Square</p>
                <p className="text-xs text-muted-foreground">1080 × 1080</p>
                <p className="text-xs text-muted-foreground">Instagram Feed</p>
              </button>
              <button
                onClick={() => handleShare('story')}
                className="p-4 border-2 border-honey/30 rounded-xl hover:border-honey hover:bg-honey/10 transition-all text-center group"
                data-testid="share-story-btn"
              >
                <div className="w-16 h-16 bg-honey/20 rounded-lg mx-auto mb-2 group-hover:bg-honey/30 transition-colors flex items-center justify-center">
                  <div className="w-6 h-10 border-2 border-honey-amber rounded"></div>
                </div>
                <p className="font-medium">Story</p>
                <p className="text-xs text-muted-foreground">1080 × 1920</p>
                <p className="text-xs text-muted-foreground">Instagram Story</p>
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default HivePage;
