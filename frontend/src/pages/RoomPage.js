import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useVariantModal } from '../context/VariantModalContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Skeleton } from '../components/ui/skeleton';
import { Users, Music } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import BeeAvatar from '../components/BeeAvatar';
import { PostCard } from '../components/HivePostCard';

const RoomPage = () => {
  const { slug } = useParams();
  const { user, token, API } = useAuth();
  const navigate = useNavigate();

  const [room, setRoom] = useState(null);
  const [isMember, setIsMember] = useState(false);
  const [feed, setFeed] = useState([]);
  const [charts, setCharts] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [showGoldDialog, setShowGoldDialog] = useState(false);

  usePageTitle(room?.name || 'Room');

  const headers = { Authorization: `Bearer ${token}` };

  const fetchRoom = useCallback(async () => {
    try {
      const [roomRes, memberRes] = await Promise.all([
        axios.get(`${API}/rooms/${slug}`),
        axios.get(`${API}/rooms/${slug}/membership`, { headers }),
      ]);
      setRoom(roomRes.data);
      setIsMember(memberRes.data.is_member);
    } catch {
      toast.error('Could not load room.');
    }
  }, [API, slug, token]);

  const fetchFeedAndSidebar = useCallback(async () => {
    try {
      const [feedRes, chartsRes, membersRes] = await Promise.all([
        axios.get(`${API}/rooms/${slug}/feed`, { headers }),
        axios.get(`${API}/rooms/${slug}/charts`),
        axios.get(`${API}/rooms/${slug}/members`),
      ]);
      setFeed(feedRes.data);
      setCharts(chartsRes.data);
      setMembers(membersRes.data);
    } catch {
      // Non-fatal — sidebar can be empty
    }
  }, [API, slug, token]);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchRoom(), fetchFeedAndSidebar()]).finally(() => setLoading(false));
  }, [fetchRoom, fetchFeedAndSidebar]);

  const handleJoin = async () => {
    setJoining(true);
    try {
      await axios.post(`${API}/rooms/${slug}/join`, {}, { headers });
      setIsMember(true);
      setRoom(prev => prev ? { ...prev, member_count: (prev.member_count || 0) + 1 } : prev);
      toast.success(`Joined ${room?.name}!`);
    } catch (err) {
      if (err.response?.status === 403) {
        setShowGoldDialog(true);
      } else {
        toast.error('Could not join room.');
      }
    } finally {
      setJoining(false);
    }
  };

  const handleLeave = async () => {
    try {
      await axios.delete(`${API}/rooms/${slug}/leave`, { headers });
      setIsMember(false);
      setRoom(prev => prev ? { ...prev, member_count: Math.max(0, (prev.member_count || 1) - 1) } : prev);
      toast.success(`Left ${room?.name}.`);
    } catch {
      toast.error('Could not leave room.');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Skeleton className="h-40 w-full rounded-2xl mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-4">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 rounded-xl" />)}
          </div>
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!room) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-muted-foreground">Room not found.</p>
      </div>
    );
  }

  const theme = room.theme || {};
  const accentColor = theme.accentColor || '#C8861A';
  const bgGradient = theme.bgGradient || 'linear-gradient(135deg, #FFF3E0, #FFE0B2)';

  return (
    <div
      style={{ '--room-accent': accentColor, '--room-bg': bgGradient }}
      className="max-w-4xl mx-auto pb-24 md:pb-8"
      data-testid="room-page"
    >
      {/* Themed header */}
      <div
        className="w-full px-6 py-8 rounded-2xl mb-6 flex flex-col items-center text-center"
        style={{ background: bgGradient }}
        data-testid="room-header"
      >
        <span className="text-5xl mb-3">{room.emoji}</span>
        <h1
          className="font-heading text-3xl font-bold mb-1"
          style={{ color: theme.textColor || '#2A1A06', fontFamily: 'DM Serif Display, serif' }}
        >
          {room.name}
        </h1>
        <p className="text-sm mb-3" style={{ color: theme.textColor ? theme.textColor + 'CC' : '#2A1A0699' }}>
          {room.tagline}
        </p>
        <p className="text-sm font-semibold mb-4" style={{ color: accentColor }}>
          <Users className="inline w-4 h-4 mr-1" />
          {(room.member_count || 0).toLocaleString()} {room.member_count === 1 ? 'member' : 'members'}
        </p>
        {isMember ? (
          <Button
            variant="outline"
            onClick={handleLeave}
            className="rounded-full px-6"
            style={{ borderColor: accentColor, color: accentColor }}
            data-testid="leave-room-btn"
          >
            Leave Room
          </Button>
        ) : (
          <Button
            onClick={handleJoin}
            disabled={joining}
            className="rounded-full px-6 text-white font-semibold"
            style={{ background: accentColor }}
            data-testid="join-room-btn"
          >
            {joining ? 'Joining…' : 'Join Room'}
          </Button>
        )}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 px-4">
        {/* Feed */}
        <div className="md:col-span-2 space-y-4" data-testid="room-feed">
          {feed.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <Music className="w-8 h-8 mx-auto mb-2 text-honey-amber" />
              <p className="text-sm text-muted-foreground">No posts yet in this room. Be the first to spin something!</p>
            </Card>
          ) : (
            feed.map((post, idx) => (
              <PostCard key={post.id || idx} post={post} token={token} API={API} currentUserId={user?.id} />
            ))
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Charts */}
          <Card className="p-4 border-honey/30" data-testid="room-charts">
            <h3 className="font-heading text-base font-bold mb-3" style={{ color: accentColor }}>
              Top Records
            </h3>
            {charts.length === 0 ? (
              <p className="text-xs text-muted-foreground">No chart data yet.</p>
            ) : (
              <ol className="space-y-2">
                {charts.map((item, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span
                      className="w-5 h-5 flex items-center justify-center rounded-full text-[10px] font-bold shrink-0"
                      style={idx === 0
                        ? { background: '#DAA520', color: '#fff' }
                        : { background: '#E5E7EB', color: '#374151' }
                      }
                    >
                      {idx + 1}
                    </span>
                    {item.record?.cover_url && (
                      <div className="w-8 h-8 rounded overflow-hidden shrink-0 bg-honey/10">
                        <AlbumArt src={item.record.cover_url} alt={item.record?.title} className="w-full h-full object-cover" />
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="text-xs font-medium truncate">{item.record?.title}</p>
                      <p className="text-[10px] text-muted-foreground truncate">{item.record?.artist}</p>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </Card>

          {/* Members */}
          <Card className="p-4 border-honey/30" data-testid="room-members">
            <h3 className="font-heading text-base font-bold mb-3" style={{ color: accentColor }}>
              Members
            </h3>
            {members.length === 0 ? (
              <p className="text-xs text-muted-foreground">No members yet — be the first!</p>
            ) : (
              <>
                <div className="flex flex-wrap gap-2">
                  {members.slice(0, 12).map(u => (
                    <div key={u.id} className="w-8 h-8" title={`@${u.username}`}>
                      <BeeAvatar user={u} className="h-8 w-8 cursor-pointer" onClick={() => navigate(`/profile/${u.username}`)} />
                    </div>
                  ))}
                </div>
                {members.length > 12 && (
                  <p className="text-xs text-muted-foreground mt-2">+{members.length - 12} more</p>
                )}
              </>
            )}
          </Card>
        </div>
      </div>

      {/* Gold upsell dialog */}
      <Dialog open={showGoldDialog} onOpenChange={setShowGoldDialog}>
        <DialogContent className="sm:max-w-xs" aria-describedby="gold-room-desc">
          <DialogHeader>
            <DialogTitle className="font-heading text-center" style={{ color: '#D98C2F' }}>
              Upgrade to Gold
            </DialogTitle>
            <p id="gold-room-desc" className="text-sm text-center text-muted-foreground mt-1">
              Free members can join up to 3 rooms. Upgrade to Gold for unlimited rooms.
            </p>
          </DialogHeader>
          <div className="flex flex-col gap-3 pt-3">
            <Button
              onClick={() => { setShowGoldDialog(false); navigate('/gold'); }}
              className="w-full rounded-full py-3 text-sm font-semibold text-white"
              style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)' }}
              data-testid="gold-upsell-btn"
            >
              Get Gold — Unlimited Rooms
            </Button>
            <Button
              variant="ghost"
              onClick={() => setShowGoldDialog(false)}
              className="w-full rounded-full text-sm"
            >
              Maybe later
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RoomPage;
