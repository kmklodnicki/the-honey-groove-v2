import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { Disc, Users, Calendar, Edit, UserPlus, UserMinus, Hexagon, BarChart3, Share2 } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

const ProfilePage = () => {
  const { username } = useParams();
  const { user, token, API } = useAuth();
  const [profile, setProfile] = useState(null);
  const [records, setRecords] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('collection');

  const isOwnProfile = user?.username === username;

  useEffect(() => {
    fetchProfile();
  }, [username]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const [profileRes, recordsRes] = await Promise.all([
        axios.get(`${API}/users/${username}`),
        axios.get(`${API}/users/${username}/records`)
      ]);

      setProfile(profileRes.data);
      setRecords(recordsRes.data);

      if (token && !isOwnProfile) {
        const followRes = await axios.get(`${API}/follow/check/${username}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setIsFollowing(followRes.data.is_following);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleFollow = async () => {
    if (!token) {
      toast.error('Please sign in to follow users');
      return;
    }

    try {
      if (isFollowing) {
        await axios.delete(`${API}/follow/${username}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success(`Unfollowed @${username}`);
      } else {
        await axios.post(`${API}/follow/${username}`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success(`Now following @${username}`);
      }
      setIsFollowing(!isFollowing);
      fetchProfile();
    } catch (error) {
      console.error('Follow error:', error);
      toast.error('Failed to update follow status');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-24">
        <div className="flex items-start gap-6 mb-8">
          <Skeleton className="w-24 h-24 rounded-full" />
          <div className="flex-1 space-y-3">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-24 text-center">
        <h1 className="font-heading text-2xl mb-2">User not found</h1>
        <p className="text-muted-foreground">@{username} doesn't exist</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8">
      {/* Profile Header */}
      <Card className="p-6 border-honey/30 mb-6">
        <div className="flex flex-col md:flex-row items-start gap-6">
          <Avatar className="w-24 h-24 border-4 border-honey">
            <AvatarImage src={profile.avatar_url} />
            <AvatarFallback className="text-3xl bg-honey text-vinyl-black">
              {profile.username?.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="font-heading text-2xl text-vinyl-black">@{profile.username}</h1>
                {profile.bio && <p className="text-muted-foreground mt-1">{profile.bio}</p>}
                <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  Joined {format(new Date(profile.created_at), 'MMMM yyyy')}
                </div>
              </div>

              {isOwnProfile ? (
                <Link to="/settings">
                  <Button variant="outline" className="gap-2" data-testid="edit-profile-btn">
                    <Edit className="w-4 h-4" />
                    Edit Profile
                  </Button>
                </Link>
              ) : (
                <Button
                  onClick={handleFollow}
                  className={isFollowing 
                    ? "bg-transparent border-2 border-vinyl-black text-vinyl-black hover:bg-vinyl-black hover:text-white" 
                    : "bg-honey text-vinyl-black hover:bg-honey-amber"
                  }
                  data-testid="follow-btn"
                >
                  {isFollowing ? (
                    <>
                      <UserMinus className="w-4 h-4 mr-2" />
                      Following
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-4 h-4 mr-2" />
                      Follow
                    </>
                  )}
                </Button>
              )}
            </div>

            {/* Stats */}
            <div className="flex gap-6 mt-4">
              <div className="text-center">
                <div className="font-heading text-2xl text-vinyl-black">{profile.collection_count}</div>
                <div className="text-sm text-muted-foreground">Records</div>
              </div>
              <div className="text-center">
                <div className="font-heading text-2xl text-vinyl-black">{profile.spin_count}</div>
                <div className="text-sm text-muted-foreground">Spins</div>
              </div>
              <div className="text-center">
                <div className="font-heading text-2xl text-vinyl-black">{profile.followers_count}</div>
                <div className="text-sm text-muted-foreground">Followers</div>
              </div>
              <div className="text-center">
                <div className="font-heading text-2xl text-vinyl-black">{profile.following_count}</div>
                <div className="text-sm text-muted-foreground">Following</div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6">
          <TabsTrigger value="collection" className="data-[state=active]:bg-honey">
            <Disc className="w-4 h-4 mr-2" />
            Collection
          </TabsTrigger>
          {isOwnProfile && (
            <TabsTrigger value="weekly" className="data-[state=active]:bg-honey">
              <BarChart3 className="w-4 h-4 mr-2" />
              Weekly
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="collection">
          {records.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <Disc className="w-12 h-12 text-honey mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">No records yet</h3>
              <p className="text-muted-foreground">
                {isOwnProfile ? "Start building your collection!" : `@${username} hasn't added any records yet`}
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {records.map(record => (
                <Link to={`/record/${record.id}`} key={record.id}>
                  <Card className="border-honey/30 overflow-hidden hover:shadow-honey transition-all hover:-translate-y-1">
                    <div className="aspect-square bg-vinyl-black">
                      {record.cover_url ? (
                        <img src={record.cover_url} alt={record.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Disc className="w-12 h-12 text-honey" />
                        </div>
                      )}
                    </div>
                    <div className="p-3">
                      <h4 className="font-medium text-sm truncate">{record.title}</h4>
                      <p className="text-xs text-muted-foreground truncate">{record.artist}</p>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>

        {isOwnProfile && (
          <TabsContent value="weekly">
            <WeeklySummarySection token={token} API={API} />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
};

const WeeklySummarySection = ({ token, API }) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`${API}/weekly-summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch weekly summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    try {
      const response = await axios.post(`${API}/share/generate`, 
        { graphic_type: 'weekly_summary' },
        { 
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `honeygroove_weekly_${new Date().toISOString().split('T')[0]}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Weekly summary downloaded!');
    } catch (error) {
      console.error('Share error:', error);
      toast.error('Failed to generate share image');
    }
  };

  if (loading) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <Card className="p-6 border-honey/30">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Hexagon className="w-8 h-8 text-honey" />
          <h2 className="font-heading text-2xl">HoneyGroove Weekly</h2>
        </div>
        <Button
          variant="outline"
          onClick={handleShare}
          className="gap-2"
          data-testid="share-weekly-btn"
        >
          <Share2 className="w-4 h-4" />
          Share
        </Button>
      </div>

      {summary?.total_spins === 0 ? (
        <p className="text-center text-muted-foreground py-8">
          No spins this week. Start playing some records!
        </p>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="text-center p-6 bg-honey/10 rounded-xl">
            <div className="font-heading text-5xl text-honey-amber">{summary?.total_spins || 0}</div>
            <div className="text-muted-foreground">Spins This Week</div>
          </div>
          
          <div className="space-y-4">
            <div className="p-4 bg-white/50 rounded-xl border border-honey/20">
              <div className="text-xs text-honey-amber font-medium uppercase tracking-wide">Top Artist</div>
              <div className="font-heading text-lg">{summary?.top_artist || 'N/A'}</div>
            </div>
            <div className="p-4 bg-white/50 rounded-xl border border-honey/20">
              <div className="text-xs text-honey-amber font-medium uppercase tracking-wide">Top Album</div>
              <div className="font-heading text-lg">{summary?.top_album || 'N/A'}</div>
            </div>
            <div className="p-4 bg-honey/20 rounded-xl">
              <div className="text-xs text-honey-amber font-medium uppercase tracking-wide">Listening Mood</div>
              <div className="font-heading text-lg">{summary?.listening_mood || 'Quiet week'}</div>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};

export default ProfilePage;
