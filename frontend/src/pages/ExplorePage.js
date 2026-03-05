import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Heart, MessageCircle, Share2, Disc, Package, TrendingUp, Hexagon, Lock } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

const ExplorePage = () => {
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [buzzing, setBuzzing] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('feed');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [postsRes, buzzingRes] = await Promise.all([
        axios.get(`${API}/explore`),
        axios.get(`${API}/buzzing`)
      ]);
      setPosts(postsRes.data);
      setBuzzing(buzzingRes.data);
    } catch (error) {
      console.error('Failed to fetch explore data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (postId, isLiked) => {
    if (!token) {
      toast.error('Please sign in to like posts');
      return;
    }

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

  // Show login overlay for non-authenticated users
  if (!user) {
    return (
      <div className="min-h-screen bg-honey-cream relative">
        {/* Blurred Background Content */}
        <div className="max-w-4xl mx-auto px-4 py-8 pt-24 pb-24 filter blur-md pointer-events-none select-none">
          <div className="flex items-center gap-3 mb-6">
            <h1 className="font-heading text-3xl text-vinyl-black">Explore</h1>
            <Hexagon className="w-6 h-6 text-honey" />
          </div>

          <div className="bg-honey/10 p-2 rounded-lg mb-6 flex gap-2">
            <div className="bg-honey px-4 py-2 rounded">Latest</div>
            <div className="px-4 py-2">Buzzing Now</div>
          </div>

          {/* Fake posts for blur effect */}
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <Card key={i} className="p-4 border-honey/30">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-honey/30" />
                  <div>
                    <div className="h-4 w-24 bg-honey/30 rounded mb-1" />
                    <div className="h-3 w-16 bg-honey/20 rounded" />
                  </div>
                </div>
                <div className="flex gap-4 bg-honey/10 rounded-xl p-4">
                  <div className="w-20 h-20 rounded-lg bg-vinyl-black/50" />
                  <div className="flex-1">
                    <div className="h-5 w-32 bg-honey/30 rounded mb-2" />
                    <div className="h-4 w-24 bg-honey/20 rounded" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Login Overlay */}
        <div className="fixed inset-0 flex items-center justify-center z-50 bg-honey-cream/30 backdrop-blur-sm">
          <Card className="p-8 max-w-md mx-4 border-honey/30 bg-white/95 shadow-xl text-center">
            <div className="w-16 h-16 bg-honey/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-honey-amber" />
            </div>
            <h2 className="font-heading text-2xl text-vinyl-black mb-2">Join the Hive</h2>
            <p className="text-muted-foreground mb-6">
              Sign in to explore what vinyl collectors are spinning, discover new music, and connect with the community.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                onClick={() => navigate('/login')}
                className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full px-8"
                data-testid="explore-login-btn"
              >
                Sign In
              </Button>
              <Button
                onClick={() => navigate('/signup')}
                variant="outline"
                className="rounded-full px-8"
                data-testid="explore-signup-btn"
              >
                Create Account
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-4">
              Test account: demo@honeygroove.com / demo123
            </p>
          </Card>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-24">
        <h1 className="font-heading text-3xl mb-6">Explore</h1>
        <div className="grid gap-4">
          {[1, 2, 3].map(i => (
            <Card key={i} className="p-6">
              <Skeleton className="h-32 w-full" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="font-heading text-3xl text-vinyl-black">Explore</h1>
        <Hexagon className="w-6 h-6 text-honey animate-pulse" />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="w-full justify-start bg-honey/10 mb-6">
          <TabsTrigger value="feed" className="data-[state=active]:bg-honey">
            Latest
          </TabsTrigger>
          <TabsTrigger value="buzzing" className="data-[state=active]:bg-honey">
            <TrendingUp className="w-4 h-4 mr-1" />
            Buzzing Now
          </TabsTrigger>
        </TabsList>

        <TabsContent value="feed">
          {posts.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <div className="w-16 h-16 bg-honey/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Disc className="w-8 h-8 text-honey-amber" />
              </div>
              <h3 className="font-heading text-xl mb-2">No posts yet</h3>
              <p className="text-muted-foreground">Be the first to share something!</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {posts.map(post => (
                <ExplorePostCard 
                  key={post.id} 
                  post={post} 
                  onLike={handleLike}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="buzzing">
          <div className="mb-4">
            <p className="text-muted-foreground">What's spinning around The Hive this week</p>
          </div>
          {buzzing.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <h3 className="font-heading text-xl mb-2">No buzzing records yet</h3>
              <p className="text-muted-foreground">Start spinning to see what's trending!</p>
            </Card>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {buzzing.map((record, idx) => (
                <BuzzingCard key={record.id} record={record} rank={idx + 1} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

const ExplorePostCard = ({ post, onLike }) => {
  const timeAgo = formatDistanceToNow(new Date(post.created_at), { addSuffix: true });

  const getPostLabel = (postType) => {
    switch (postType) {
      case 'spin': return 'is spinning';
      case 'haul': return 'shared a haul';
      case 'record_added': return 'added to collection';
      default: return 'posted';
    }
  };

  return (
    <Card className="border-honey/30 overflow-hidden hover:shadow-honey transition-shadow" data-testid={`explore-post-${post.id}`}>
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
              <span className="text-sm text-muted-foreground">{getPostLabel(post.post_type)}</span>
            </div>
            <p className="text-xs text-muted-foreground">{timeAgo}</p>
          </div>
        </div>
      </div>

      {post.record && (
        <Link to={`/record/${post.record.id}`} className="block px-4 py-2">
          <div className="flex gap-4 bg-honey/10 rounded-xl p-4">
            {post.record.cover_url ? (
              <img src={post.record.cover_url} alt={post.record.title} className="w-20 h-20 rounded-lg object-cover shadow-md" />
            ) : (
              <div className="w-20 h-20 rounded-lg bg-vinyl-black flex items-center justify-center">
                <Disc className="w-8 h-8 text-honey" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-vinyl-black truncate">{post.record.title}</h4>
              <p className="text-sm text-muted-foreground truncate">{post.record.artist}</p>
            </div>
          </div>
        </Link>
      )}

      {post.haul && (
        <div className="px-4 py-2">
          <div className="bg-honey/10 rounded-xl p-4">
            <h4 className="font-medium mb-2">{post.haul.title}</h4>
            <p className="text-sm text-muted-foreground">{post.haul.items?.length} records</p>
          </div>
        </div>
      )}

      <div className="px-4 py-3 flex items-center gap-4 border-t border-honey/20">
        <button 
          onClick={() => onLike(post.id, post.is_liked)}
          className={`flex items-center gap-1.5 text-sm transition-colors ${post.is_liked ? 'text-red-500' : 'text-muted-foreground hover:text-red-500'}`}
        >
          <Heart className={`w-4 h-4 ${post.is_liked ? 'fill-current' : ''}`} />
          {post.likes_count > 0 && post.likes_count}
        </button>
        <button className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <MessageCircle className="w-4 h-4" />
          {post.comments_count > 0 && post.comments_count}
        </button>
      </div>
    </Card>
  );
};

const BuzzingCard = ({ record, rank }) => (
  <Link to={`/record/${record.id}`}>
    <Card className="border-honey/30 overflow-hidden group hover:shadow-honey transition-all hover:-translate-y-1" data-testid={`buzzing-${record.id}`}>
      <div className="relative aspect-square">
        {record.cover_url ? (
          <img src={record.cover_url} alt={record.title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-vinyl-black flex items-center justify-center">
            <Disc className="w-12 h-12 text-honey" />
          </div>
        )}
        <div className="absolute top-2 left-2 w-8 h-8 bg-honey rounded-full flex items-center justify-center font-bold text-vinyl-black text-sm">
          {rank}
        </div>
        <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          {record.buzz_count} spins
        </div>
      </div>
      <div className="p-3">
        <h4 className="font-medium text-sm truncate">{record.title}</h4>
        <p className="text-xs text-muted-foreground truncate">{record.artist}</p>
      </div>
    </Card>
  </Link>
);

export default ExplorePage;
