import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { Disc, Edit, UserPlus, UserMinus, Loader2, Search, Play, CheckCircle2, ArrowRightLeft, CreditCard, Star, MessageCircle, MapPin, Flame, ShoppingBag } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { FollowListModal } from '../components/FollowList';
import { usePageTitle } from '../hooks/usePageTitle';
import { StreakBadge } from '../components/DailyPrompt';
import { MoodBoardTab } from '../components/MoodBoardTab';

const ProfilePage = () => {
  usePageTitle('Profile');
  const { username } = useParams();
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [records, setRecords] = useState([]);
  const [spins, setSpins] = useState([]);
  const [isos, setIsos] = useState([]);
  const [trades, setTrades] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [followLoading, setFollowLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('collection');
  const [followListType, setFollowListType] = useState(null);
  const [stripeStatus, setStripeStatus] = useState(null);
  const [stripeLoading, setStripeLoading] = useState(false);
  const [ratings, setRatings] = useState(null);
  const [collectionValue, setCollectionValue] = useState(null);
  const [promptStreak, setPromptStreak] = useState(null);

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
      if (token && isOwnProfile) {
        axios.get(`${API}/stripe/status`, { headers: { Authorization: `Bearer ${token}` }}).then(r => setStripeStatus(r.data)).catch(() => {});
      }
      axios.get(`${API}/users/${username}/ratings`).then(r => setRatings(r.data)).catch(() => {});
      axios.get(`${API}/valuation/collection/${username}`).then(r => setCollectionValue(r.data)).catch(() => {});
      axios.get(`${API}/prompts/streak/${username}`).then(r => setPromptStreak(r.data)).catch(() => {});
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
    if (activeTab === 'trades' && trades.length === 0) {
      axios.get(`${API}/users/${username}/trades`)
        .then(r => setTrades(r.data))
        .catch(() => {});
    }
  }, [activeTab, API, username, spins.length, isos.length, trades.length]);

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

  const handleStripeConnect = async () => {
    setStripeLoading(true);
    try {
      const resp = await axios.post(`${API}/stripe/connect`, {}, { headers: { Authorization: `Bearer ${token}` }});
      if (resp.data.url) window.location.href = resp.data.url;
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setStripeLoading(false); }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24">
        <Skeleton className="h-48 w-full rounded-xl mb-6" />
        <Skeleton className="h-12 w-64 mb-4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24 text-center">
        <h2 className="font-heading text-2xl mb-2">User not found</h2>
        <p className="text-muted-foreground">@{username} doesn't exist.</p>
      </div>
    );
  }

  const firstLetter = profile.username?.charAt(0).toUpperCase() || '?';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8" data-testid="profile-page">
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
                <div className="flex gap-2">
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
                  <Button
                    size="sm" variant="outline"
                    onClick={() => navigate(`/messages?to=${profile.id}`)}
                    className="rounded-full border-vinyl-black/30"
                    data-testid="profile-message-btn"
                  >
                    <MessageCircle className="w-4 h-4 mr-1" /> Message
                  </Button>
                </div>
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
            {profile.setup && (
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1" data-testid="profile-setup">
                🎚️ {profile.setup}
              </p>
            )}
            {(profile.location || profile.city || profile.region) && (
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <MapPin className="w-3 h-3" /> {profile.location || `${profile.city || ''}${profile.region ? `, ${profile.region}` : ''}`}
              </p>
            )}
            {profile.favorite_genre && (
              <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 text-xs font-medium" data-testid="profile-genre">
                {profile.favorite_genre}
              </span>
            )}
            {profile.founding_member && (
              <div className="mt-1.5 inline-block" data-testid="founding-badge">
                <span className="italic text-xs" style={{ color: '#C8861A', fontFamily: '"DM Serif Display", serif' }}>
                  🐝 founding member
                </span>
              </div>
            )}

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
              {profile.completed_transactions > 0 && (
                <div className="text-center" data-testid="profile-transactions">
                  <div className="font-heading text-2xl text-vinyl-black flex items-center justify-center gap-1">
                    <ShoppingBag className="w-4 h-4 text-honey-amber" /> {profile.completed_transactions}
                  </div>
                  <div className="text-xs text-muted-foreground">Sales</div>
                </div>
              )}
              {collectionValue && collectionValue.total_value > 0 && (
                <div className="text-center" data-testid="profile-collection-value">
                  <div className="font-heading text-2xl text-honey-amber">
                    ${collectionValue.total_value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-xs text-muted-foreground">Est. Value</div>
                </div>
              )}
              {promptStreak && promptStreak.streak > 0 && (
                <div className="text-center" data-testid="profile-streak">
                  <div className="font-heading text-2xl text-orange-500 flex items-center justify-center gap-1">
                    <Flame className="w-5 h-5" /> {promptStreak.streak}
                  </div>
                  <div className="text-xs text-muted-foreground">Day Streak</div>
                </div>
              )}
            </div>

            {/* Trade rating */}
            {ratings && ratings.count > 0 && (
              <div className="flex items-center gap-1 mt-2" data-testid="profile-trade-rating">
                <div className="flex gap-0.5">{[1,2,3,4,5].map(v => <Star key={v} className={`w-3.5 h-3.5 ${v <= Math.round(ratings.average) ? 'fill-honey text-honey' : 'text-gray-300'}`} />)}</div>
                <span className="text-xs text-muted-foreground ml-1">{ratings.average} ({ratings.count} trade{ratings.count !== 1 ? 's' : ''})</span>
              </div>
            )}

            {/* Prompt Streak */}
            <div className="mt-2">
              <StreakBadge username={profile.username} />
            </div>

            {/* Stripe Connect */}
            {isOwnProfile && stripeStatus && (
              <div className="mt-3">
                {stripeStatus.stripe_connected ? (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700" data-testid="stripe-connected-badge">
                    <CreditCard className="w-3 h-3" /> Stripe Connected
                  </span>
                ) : (
                  <Button size="sm" onClick={handleStripeConnect} disabled={stripeLoading}
                    className="rounded-full bg-[#635bff] text-white hover:bg-[#5146e0] gap-1" data-testid="stripe-connect-btn">
                    {stripeLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <CreditCard className="w-3 h-3" />}
                    Connect with Stripe
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Pinned Wax Report */}
      <WaxReportPin username={username} API={API} token={token} />

      {/* 4 Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-5">
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
          <TabsTrigger value="mood" className="data-[state=active]:bg-honey text-xs sm:text-sm" data-testid="tab-mood">
            Mood Board
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
            <EmptyState icon={Search} title="No ISOs yet" sub={isOwnProfile ? 'Post an ISO from The Hive to start searching!' : `@${username} isn't searching for anything right now`} />
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
          {trades.length === 0 ? (
            <EmptyState icon={ArrowRightLeft} title="No trades yet" sub={isOwnProfile ? 'Propose a trade from The Honeypot!' : `@${username} hasn't completed any trades yet`} />
          ) : (
            <div className="space-y-3">
              {trades.map(trade => {
                const isInit = trade.initiator_id === profile.id;
                const otherUser = isInit ? trade.responder : trade.initiator;
                const statusColors = {
                  ACCEPTED: 'bg-green-100 text-green-700',
                  COMPLETED: 'bg-green-100 text-green-700',
                  SHIPPING: 'bg-purple-100 text-purple-700',
                  CONFIRMING: 'bg-cyan-100 text-cyan-700',
                };
                return (
                  <Card key={trade.id} className="p-4 border-honey/30" data-testid={`profile-trade-${trade.id}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${statusColors[trade.status] || 'bg-gray-100 text-gray-600'}`}>
                        {trade.status}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(trade.updated_at), { addSuffix: true })}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {trade.offered_record?.cover_url ? (
                          <img src={trade.offered_record.cover_url} alt="" className="w-10 h-10 rounded object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>
                        )}
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{trade.offered_record?.title || 'Unknown'}</p>
                          <p className="text-xs text-muted-foreground truncate">{trade.offered_record?.artist}</p>
                        </div>
                      </div>
                      <ArrowRightLeft className="w-4 h-4 text-honey shrink-0" />
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {trade.listing_record?.cover_url ? (
                          <img src={trade.listing_record.cover_url} alt="" className="w-10 h-10 rounded object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>
                        )}
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{trade.listing_record?.album || 'Unknown'}</p>
                          <p className="text-xs text-muted-foreground truncate">{trade.listing_record?.artist}</p>
                        </div>
                      </div>
                    </div>
                    {otherUser && (
                      <p className="text-xs text-muted-foreground mt-2">
                        Trade with <Link to={`/profile/${otherUser.username}`} className="text-honey-amber hover:underline">@{otherUser.username}</Link>
                      </p>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
          {isOwnProfile && (
            <Link to="/trades" className="block mt-4">
              <Button variant="outline" className="w-full rounded-full border-honey/30 text-honey-amber hover:bg-honey/10" data-testid="view-all-trades-btn">
                View All Trades
              </Button>
            </Link>
          )}
        </TabsContent>

        {/* Mood Board Tab */}
        <TabsContent value="mood">
          <MoodBoardTab username={username} />
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

const WaxReportPin = ({ username, API, token }) => {
  const [report, setReport] = useState(null);
  useEffect(() => {
    axios.get(`${API}/wax-reports/latest/${username}`)
      .then(r => setReport(r.data))
      .catch(() => {});
  }, [API, username]);

  if (!report) return null;

  let weekRange = '';
  try {
    const ws = new Date(report.week_start);
    const we = new Date(report.week_end);
    we.setDate(we.getDate() - 1);
    weekRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} — ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { weekRange = ''; }

  return (
    <Link to={`/wax-reports/${report.id}`} className="block mb-4" data-testid="profile-wax-pin">
      <Card className="p-4 rounded-2xl shadow-sm hover:shadow-md transition-all" style={{ background: '#FAEDC7', border: '1px solid rgba(200,134,26,0.15)' }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0" style={{ background: 'rgba(200,134,26,0.08)' }}>
            <Disc className="w-4 h-4" style={{ color: '#C8861A' }} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-heading" style={{ color: '#2A1A06' }}>your week in wax</p>
            <p className="text-[11px] truncate" style={{ color: '#8A6B4A' }}>
              {weekRange} · {report.total_spins} spins · {report.personality?.label?.slice(0, 40)}...
            </p>
          </div>
          <span className="text-[11px] shrink-0" style={{ color: '#C8861A' }}>View &rarr;</span>
        </div>
      </Card>
    </Link>
  );
};

export default ProfilePage;
