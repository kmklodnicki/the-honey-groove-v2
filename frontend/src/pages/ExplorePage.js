import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { Disc, Users, Search, TrendingUp, Lock } from 'lucide-react';
import { UserRow } from '../components/FollowList';
import { PostTypeBadge, PostCardBody } from '../components/PostCards';
import { formatDistanceToNow } from 'date-fns';

const ExplorePage = () => {
  const { user, token, API } = useAuth();
  const [activeTab, setActiveTab] = useState('feed');
  const [posts, setPosts] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchExploreFeed = useCallback(async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const resp = await axios.get(`${API}/explore?limit=30`, { headers });
      setPosts(resp.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  const fetchSuggestions = useCallback(async () => {
    if (!token) return;
    try {
      const resp = await axios.get(`${API}/users/discover/suggestions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuggestions(resp.data);
    } catch { /* ignore */ }
  }, [API, token]);

  useEffect(() => {
    fetchExploreFeed();
    fetchSuggestions();
  }, [fetchExploreFeed, fetchSuggestions]);

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (!query.trim() || query.length < 2) { setSearchResults([]); return; }
    if (!token) return;
    setSearching(true);
    try {
      const resp = await axios.get(`${API}/users/search?query=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSearchResults(resp.data);
    } catch { setSearchResults([]); }
    finally { setSearching(false); }
  };

  if (!user) {
    // Guest blurred view
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-24">
        <h1 className="font-heading text-3xl text-vinyl-black mb-6">Explore</h1>
        <div className="relative">
          <div className="blur-md pointer-events-none">
            {[1, 2, 3].map(i => (
              <Card key={i} className="mb-4 p-6 border-honey/30">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-full bg-honey/30" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-32 bg-honey/20 rounded" />
                    <div className="h-20 w-full bg-honey/10 rounded-lg" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Card className="p-8 text-center shadow-lg border-honey/30 bg-white/95">
              <Lock className="w-10 h-10 text-honey mx-auto mb-3" />
              <h3 className="font-heading text-xl mb-2">Join The Hive</h3>
              <p className="text-muted-foreground text-sm mb-4">Sign in to explore the vinyl community</p>
              <div className="flex gap-3 justify-center">
                <Link to="/login"><Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full">Log In</Button></Link>
                <Link to="/signup"><Button variant="outline" className="rounded-full">Sign Up</Button></Link>
              </div>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8" data-testid="explore-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-6">Explore</h1>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6">
          <TabsTrigger value="feed" className="data-[state=active]:bg-honey" data-testid="explore-tab-feed">
            <TrendingUp className="w-4 h-4 mr-2" /> Feed
          </TabsTrigger>
          <TabsTrigger value="people" className="data-[state=active]:bg-honey" data-testid="explore-tab-people">
            <Users className="w-4 h-4 mr-2" /> People
          </TabsTrigger>
        </TabsList>

        {/* Feed Tab */}
        <TabsContent value="feed">
          {loading ? (
            [1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full mb-4 rounded-xl" />)
          ) : posts.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <Disc className="w-12 h-12 text-honey mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">Nothing here yet</h3>
              <p className="text-muted-foreground text-sm">Be the first to post!</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {posts.map(post => (
                <Card key={post.id} className="border-honey/30 overflow-hidden" data-testid={`explore-post-${post.id}`}>
                  <div className="p-4 pb-2">
                    <div className="flex items-center gap-3">
                      <Link to={`/profile/${post.user?.username}`} className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-honey-soft flex items-center justify-center text-sm font-heading border-2 border-honey/30">
                          {post.user?.username?.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium text-sm hover:underline">@{post.user?.username}</span>
                      </Link>
                      <PostTypeBadge type={post.post_type} />
                      <span className="text-xs text-muted-foreground ml-auto">
                        {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                  <div className="px-4 py-2 pb-4">
                    <PostCardBody post={post} />
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* People Tab */}
        <TabsContent value="people">
          {/* Search */}
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search collectors by username..."
              value={searchQuery}
              onChange={e => handleSearch(e.target.value)}
              className="pl-9 border-honey/50"
              data-testid="people-search"
            />
          </div>

          {/* Search Results */}
          {searchQuery.trim().length >= 2 && (
            <div className="mb-8">
              <h3 className="text-sm font-medium text-muted-foreground mb-3">Search Results</h3>
              {searching ? (
                <Skeleton className="h-16 w-full" />
              ) : searchResults.length === 0 ? (
                <p className="text-sm text-muted-foreground">No users found for "{searchQuery}"</p>
              ) : (
                <Card className="border-honey/30 divide-y divide-honey/10 px-4">
                  {searchResults.map(u => (
                    <UserRow key={u.id} u={u} currentUserId={user?.id} token={token} API={API} onFollowChange={fetchSuggestions} />
                  ))}
                </Card>
              )}
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-3">Suggested Collectors</h3>
              <Card className="border-honey/30 divide-y divide-honey/10 px-4" data-testid="suggestions-list">
                {suggestions.map(u => (
                  <UserRow key={u.id} u={u} currentUserId={user?.id} token={token} API={API} onFollowChange={fetchSuggestions} />
                ))}
              </Card>
            </div>
          )}

          {suggestions.length === 0 && !searchQuery && (
            <Card className="p-8 text-center border-honey/30">
              <Users className="w-12 h-12 text-honey mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">You're following everyone!</h3>
              <p className="text-muted-foreground text-sm">Invite more collectors to join The Hive.</p>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ExplorePage;
