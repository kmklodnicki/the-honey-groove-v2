import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { Disc, Edit, UserPlus, UserMinus, Loader2, Search, Play, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { FollowListModal } from '../components/FollowList';

const ProfilePage = () => {
  const { username } = useParams();
  const { user, token, API } = useAuth();
  const [profile, setProfile] = useState(null);
  const [records, setRecords] = useState([]);
  const [spins, setSpins] = useState([]);
  const [isos, setIsos] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [followLoading, setFollowLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('collection');
  const [followListType, setFollowListType] = useState(null);

  const isOwnProfile = user?.username === username;

  const fetchProfile = useCallback(async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const [profileRes, recordsRes] = await Promise.all([
        axios.get(`${API}/users/${username}`, { headers }),
        axios.get(`${API}/users/${username}/records`, { headers }),
      ]);
      setProfile(profileRes.data);
      setRecords(recordsRes.data);

      if (token && !isOwnProfile) {
        const followRes = await axios.get(`${API}/follow/check/${username}`, { headers: { Authorization: `Bearer ${token}` }});
        setIsFollowing(followRes.data.is_following);
      }
    } catch {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  }, [API, token, username, isOwnProfile]);

  useEffect(() => {
    setLoading(true);
    setActiveTab('collection');
    fetchProfile();
  }, [fetchProfile]);

  // Lazy-load tab data
  useEffect(() => {
    if (activeTab === 'spinning' && spins.length === 0) {
      axios.get(`${API}/users/${username}/spins`)
        .then(r => setSpins(r.data))
        .catch(() => {});
    }
    if (activeTab === 'iso' && isos.length === 0) {
      axios.get(`${API}/users/${username}/iso`)
        .then(r => setIsos(r.data))
        .catch(() => {});
    }
  }, [activeTab, API, username, spins.length, isos.length]);

  const handleFollow = async () => {
    setFollowLoading(true);
    try {
      if (isFollowing) {
        await axios.delete(`${API}/follow/${username}`, { headers: { Authorization: `Bearer ${token}` }});
        setIsFollowing(false);
        setProfile(p => p ? { ...p, followers_count: p.followers_count - 1 } : p);
      } else {
        await axios.post(`${API}/follow/${username}`, {}, { headers: { Authorization: `Bearer ${token}` }});
        setIsFollowing(true);
        setProfile(p => p ? { ...p, followers_count: p.followers_count + 1 } : p);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    } finally {
      setFollowLoading(false);
    }
  };

  const handleMarkFound = async (isoId) => {
    try {
      await axios.put(`${API}/iso/${isoId}/found`, {}, { headers: { Authorization: `Bearer ${token}` }});
      setIsos(prev => prev.map(i => i.id === isoId ? { ...i, status: 'FOUND' } : i));
      toast.success('Marked as found!');
    } catch { toast.error('Failed'); }
  };

  const handleDeleteIso = async (isoId) => {
    try {
      await axios.delete(`${API}/iso/${isoId}`, { headers: { Authorization: `Bearer ${token}` }});
      setIsos(prev => prev.filter(i => i.id !== isoId));
      toast.success('ISO removed');
    } catch { toast.error('Failed'); }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-24">
        <Skeleton className="h-48 w-full rounded-xl mb-6" />
        <Skeleton className="h-12 w-64 mb-4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-24 text-center">
        <h2 className="font-heading text-2xl mb-2">User not found</h2>
        <p className="text-muted-foreground">@{username} doesn't exist.</p>
      </div>
    );
  }

  const firstLetter = profile.username?.charAt(0).toUpperCase() || '?';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8" data-testid="profile-page">
      {/* Profile Header */}
      <Card className="p-6 border-honey/30 mb-6">
        <div className="flex flex-col sm:flex-row items-start gap-6">
          <Avatar className="h-24 w-24 border-4 border-honey/30">
            {profile.avatar_url && <AvatarImage src={profile.avatar_url} />}
            <AvatarFallback className="bg-honey-soft text-vinyl-black text-3xl font-heading">
              {firstLetter}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="font-heading text-2xl" data-testid="profile-username">@{profile.username}</h1>
              {!isOwnProfile && token && (
                <Button
                  size="sm"
                  onClick={handleFollow}
                  disabled={followLoading}
                  className={`rounded-full ${isFollowing ? 'bg-white border border-vinyl-black/30 text-vinyl-black hover:bg-red-50 hover:text-red-600' : 'bg-honey text-vinyl-black hover:bg-honey-amber'}`}
                  data-testid="follow-btn"
                >
                  {followLoading ? <Loader2 className="w-4 h-4 animate-spin" /> :
                    isFollowing ? <><UserMinus className="w-4 h-4 mr-1" />Following</> :
                    <><UserPlus className="w-4 h-4 mr-1" />Follow</>
                  }
                </Button>
              )}
              {isOwnProfile && (
                <Link to="/settings">
                  <Button variant="outline" size="sm" className="rounded-full gap-1">
                    <Edit className="w-3 h-3" /> Edit
                  </Button>
                </Link>
              )}
            </div>
            {profile.bio && <p className="text-sm text-muted-foreground mt-1">{profile.bio}</p>}

            {/* Stats */}
            <div className="flex gap-6 mt-4" data-testid="profile-stats">
              <div className="text-center">
                <div className="font-heading text-2xl text-vinyl-black">{profile.collection_count}</div>
                <div className="text-xs text-muted-foreground">Records</div>
              </div>
              <button onClick={() => setFollowListType('following')} className="text-center hover:opacity-70 transition" data-testid="following-stat">
                <div className="font-heading text-2xl text-vinyl-black">{profile.following_count}</div>
                <div className="text-xs text-muted-foreground">Following</div>
              </button>
              <button onClick={() => setFollowListType('followers')} className="text-center hover:opacity-70 transition" data-testid="followers-stat">
                <div className="font-heading text-2xl text-vinyl-black">{profile.followers_count}</div>
                <div className="text-xs text-muted-foreground">Followers</div>
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* 4 Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-4">
          <TabsTrigger value="collection" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-collection">
            Collection
          </TabsTrigger>
          <TabsTrigger value="iso" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-iso">
            ISO
          </TabsTrigger>
          <TabsTrigger value="spinning" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-spinning">
            Spinning
          </TabsTrigger>
          <TabsTrigger value="trades" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-trades">
            Trades
          </TabsTrigger>
        </TabsList>

        {/* Collection Tab */}
        <TabsContent value="collection">
          {records.length === 0 ? (
            <EmptyState icon={Disc} title="No records yet" sub={isOwnProfile ? 'Start building your collection!' : `@${username} hasn't added any records yet`} />
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

        {/* ISO Tab */}
        <TabsContent value="iso">
          {isos.length === 0 ? (
            <EmptyState icon={Search} title="No ISOs yet" sub={isOwnProfile ? 'Post an ISO from The Hive to start hunting!' : `@${username} isn't searching for anything right now`} />
          ) : (
            <div className="space-y-3">
              {isos.map(iso => (
                <Card key={iso.id} className={`p-4 border-honey/30 ${iso.status === 'FOUND' ? 'opacity-60' : ''}`} data-testid={`iso-item-${iso.id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-heading text-lg">{iso.album}</h4>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                          iso.status === 'FOUND' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'
                        }`}>{iso.status}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{iso.artist}</p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {(iso.tags || []).map(tag => (
                          <span key={tag} className="px-2 py-0.5 rounded-full text-xs bg-honey/20 text-honey-amber font-medium">{tag}</span>
                        ))}
                        {iso.pressing_notes && <span className="text-xs text-muted-foreground">Press: {iso.pressing_notes}</span>}
                        {iso.condition_pref && <span className="text-xs text-muted-foreground">Cond: {iso.condition_pref}</span>}
                      </div>
                      {(iso.target_price_min || iso.target_price_max) && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Budget: {iso.target_price_min ? `$${iso.target_price_min}` : '?'} – {iso.target_price_max ? `$${iso.target_price_max}` : '?'}
                        </p>
                      )}
                    </div>
                    {isOwnProfile && iso.status === 'OPEN' && (
                      <div className="flex gap-1 shrink-0">
                        <Button size="sm" variant="ghost" className="text-green-600 hover:bg-green-50 h-8 px-2" onClick={() => handleMarkFound(iso.id)} data-testid={`mark-found-${iso.id}`}>
                          <CheckCircle2 className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" className="text-red-400 hover:bg-red-50 h-8 px-2" onClick={() => handleDeleteIso(iso.id)}>✕</Button>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Spinning Tab */}
        <TabsContent value="spinning">
          {spins.length === 0 ? (
            <EmptyState icon={Play} title="No spins yet" sub={isOwnProfile ? 'Spin a record to see your history here!' : `@${username} hasn't spun anything yet`} />
          ) : (
            <div className="space-y-3">
              {spins.map(spin => (
                <Card key={spin.id} className="p-4 border-honey/30 flex items-center gap-4" data-testid={`spin-${spin.id}`}>
                  {spin.record?.cover_url ? (
                    <img src={spin.record.cover_url} alt="" className="w-14 h-14 rounded-lg object-cover shadow" />
                  ) : (
                    <div className="w-14 h-14 rounded-lg bg-vinyl-black flex items-center justify-center">
                      <Disc className="w-6 h-6 text-honey" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{spin.record?.title || 'Unknown'}</p>
                    <p className="text-xs text-muted-foreground truncate">{spin.record?.artist || 'Unknown'}</p>
                    {spin.notes && <p className="text-xs text-honey-amber mt-0.5">Track: {spin.notes}</p>}
                  </div>
                  <p className="text-xs text-muted-foreground shrink-0">
                    {formatDistanceToNow(new Date(spin.created_at), { addSuffix: true })}
                  </p>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Trades Tab */}
        <TabsContent value="trades">
          <EmptyState icon={Disc} title="No trades yet" sub="The Market is coming soon! Trade records with other collectors." />
        </TabsContent>
      </Tabs>

      {/* Follow List Modal */}
      <FollowListModal
        open={!!followListType}
        onOpenChange={(open) => !open && setFollowListType(null)}
        username={username}
        listType={followListType || 'followers'}
        onFollowChange={fetchProfile}
      />
    </div>
  );
};

const EmptyState = ({ icon: Icon, title, sub }) => (
  <Card className="p-8 text-center border-honey/30">
    <Icon className="w-12 h-12 text-honey mx-auto mb-4" />
    <h3 className="font-heading text-xl mb-2">{title}</h3>
    <p className="text-muted-foreground text-sm">{sub}</p>
  </Card>
);

export default ProfilePage;
