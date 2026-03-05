import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { Heart, MessageCircle, Share2, Disc, Package, BarChart3 } from 'lucide-react';
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
              getPostIcon={getPostIcon}
              getPostLabel={getPostLabel}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const PostCard = ({ post, onLike, getPostIcon, getPostLabel }) => {
  const timeAgo = formatDistanceToNow(new Date(post.created_at), { addSuffix: true });

  return (
    <Card className="border-honey/30 overflow-hidden hover:shadow-honey transition-shadow" data-testid={`post-${post.id}`}>
      {/* Post Header */}
      <div className="p-4 pb-2">
        <div className="flex items-center gap-3">
          <Link to={`/profile/${post.user?.username}`}>
            <Avatar className="h-10 w-10 border-2 border-honey/30">
              <AvatarImage src={post.user?.avatar_url} />
              <AvatarFallback className="bg-honey text-vinyl-black">
                {post.user?.username?.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
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
        <button className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-vinyl-black transition-colors">
          <MessageCircle className="w-4 h-4" />
          {post.comments_count > 0 && post.comments_count}
        </button>
        <button className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-vinyl-black transition-colors ml-auto">
          <Share2 className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
};

export default HivePage;
