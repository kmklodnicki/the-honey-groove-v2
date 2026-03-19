import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useVariantModal } from '../context/VariantModalContext';
import axios from 'axios';
import html2canvas from 'html2canvas';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Skeleton } from '../components/ui/skeleton';
import { Users, Music, Share2, Trophy, Info } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import BeeAvatar from '../components/BeeAvatar';
import { PostCard } from '../components/HivePostCard';
import RoomShareCard from '../components/RoomShareCard';
import { resolveImageUrl } from '../utils/imageUrl';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../components/ui/tooltip';

const ROOM_TYPE_TOOLTIPS = {
  genre:     "Rooms built around musical genres. Automatically created from the most-collected genres across all Vaults on THG.",
  artist:    "Dedicated rooms for artists with 10+ collectors on THG. Gold members can also create artist rooms manually.",
  era:       "Rooms organized by decade. Automatically generated based on release years across the THG catalog.",
  vibe:      "Mood-based rooms created by Gold members. Late night spins, rainy day records, road trip vinyl. The fun ones.",
  collector: "Rooms organized by collecting style, not genre. Colored vinyl, rare pressings, picture discs. Gold members only.",
};

// Pre-flight: ensure an image is in the browser cache before canvas export
const preflightImage = (url) => new Promise((resolve) => {
  if (!url) { resolve(false); return; }
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = () => resolve(true);
  img.onerror = () => resolve(false);
  img.src = url;
});

const RoomPage = () => {
  const { slug } = useParams();
  const { user, token, API } = useAuth();
  const navigate = useNavigate();

  const [room, setRoom] = useState(null);
  const [isMember, setIsMember] = useState(false);
  const [roomsJoinedCount, setRoomsJoinedCount] = useState(0);
  const [roomsLimit, setRoomsLimit] = useState(null);
  const [feed, setFeed] = useState([]);
  const [charts, setCharts] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [showGoldDialog, setShowGoldDialog] = useState(false);
  const [exporting, setExporting] = useState(false);
  const shareRef = useRef(null);

  const isGold = user?.golden_hive || user?.golden_hive_verified;

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
      setRoomsJoinedCount(memberRes.data.rooms_joined_count ?? 0);
      setRoomsLimit(memberRes.data.rooms_limit ?? null);
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
      setRoomsJoinedCount(c => c + 1);
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

  const handleShare = useCallback(async () => {
    if (!shareRef.current) return;
    setExporting(true);
    try {
      // Pre-flight cover image if room has a featured record
      if (room?.cover_url) {
        await preflightImage(resolveImageUrl(room.cover_url));
      }
      shareRef.current.style.display = 'block';
      shareRef.current.style.position = 'fixed';
      shareRef.current.style.left = '-9999px';
      shareRef.current.style.top = '0';

      await new Promise(r => setTimeout(r, 500));

      const canvas = await html2canvas(shareRef.current, {
        width: 1080, height: 1920, scale: 1, useCORS: true, allowTaint: false, backgroundColor: null,
      });
      shareRef.current.style.display = 'none';

      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const file = new File([blob], `honeygroove-room-${slug}-${Date.now()}.png`, { type: 'image/png' });
        if (navigator.share && navigator.canShare?.({ files: [file] })) {
          await navigator.share({ files: [file], title: `${room?.name} — The Honey Groove` });
        } else {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = file.name; a.click();
          URL.revokeObjectURL(url);
        }
        setExporting(false);
      }, 'image/png');
    } catch {
      setExporting(false);
      if (shareRef.current) shareRef.current.style.display = 'none';
    }
  }, [room, slug]);

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
        <p className="text-sm font-semibold mb-3" style={{ color: accentColor }}>
          <Users className="inline w-4 h-4 mr-1" />
          {(room.member_count || 0).toLocaleString()} {room.member_count === 1 ? 'member' : 'members'}
        </p>
        {room.type && ROOM_TYPE_TOOLTIPS[room.type] && (
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <span
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium capitalize mb-4 cursor-default"
                  style={{ background: 'rgba(0,0,0,0.12)', color: theme.textColor || '#2A1A06' }}
                  data-testid="room-type-badge"
                >
                  {room.type}
                  <Info className="w-3 h-3 opacity-60" />
                </span>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[220px] text-center text-xs leading-snug">
                {ROOM_TYPE_TOOLTIPS[room.type]}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        {/* Free user room count pill — shown when not a member and limit exists */}
        {!isMember && !isGold && roomsLimit !== null && (
          <p
            className="text-xs font-medium mb-3 px-3 py-1 rounded-full"
            style={{ background: 'rgba(0,0,0,0.10)', color: theme.textColor || '#2A1A06' }}
            data-testid="rooms-count-pill"
          >
            {roomsJoinedCount} of {roomsLimit} free rooms joined
          </p>
        )}

        <div className="flex gap-2 items-center">
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
          <Button
            variant="outline"
            size="sm"
            onClick={handleShare}
            disabled={exporting}
            className="rounded-full px-4"
            style={{ borderColor: accentColor, color: accentColor }}
            data-testid="share-room-btn"
          >
            <Share2 className="w-4 h-4 mr-1" />
            {exporting ? 'Exporting…' : 'Share'}
          </Button>
        </div>
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
              <PostCard key={post.id || idx} post={post} token={token} API={API} currentUserId={user?.id} obscureIdentity={!isMember} />
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
                    <div
                      key={u.id}
                      className="relative w-8 h-8"
                      title={isMember ? (u.is_top_collector ? `@${u.username} — Top Collector` : `@${u.username}`) : 'Join to see members'}
                    >
                      {isMember ? (
                        <BeeAvatar user={u} className="h-8 w-8 cursor-pointer" onClick={() => navigate(`/profile/${u.username}`)} />
                      ) : (
                        <BeeAvatar user={null} className="h-8 w-8 blur-sm opacity-60 pointer-events-none select-none" />
                      )}
                      {isMember && u.is_top_collector && (
                        <span
                          className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center rounded-full text-[8px]"
                          style={{ background: '#DAA520', color: '#fff' }}
                          data-testid={`top-collector-badge-${u.id}`}
                        >
                          🏆
                        </span>
                      )}
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

      {/* Hidden share card for html2canvas export */}
      <RoomShareCard ref={shareRef} room={room} />

      {/* Gold upsell dialog */}
      <Dialog open={showGoldDialog} onOpenChange={setShowGoldDialog}>
        <DialogContent className="sm:max-w-sm" aria-describedby="gold-room-desc">
          <DialogHeader>
            <div className="text-center mb-1">
              <span className="text-3xl">🍯</span>
            </div>
            <DialogTitle className="font-heading text-center text-xl" style={{ color: '#D98C2F', fontFamily: 'DM Serif Display, serif' }}>
              You've filled your hive
            </DialogTitle>
          </DialogHeader>
          <div id="gold-room-desc" className="text-center space-y-3 pt-1">
            <p className="text-sm text-muted-foreground leading-relaxed">
              Free members can join <strong>3 rooms</strong>. You've used all 3 — and{' '}
              <strong>{room?.name}</strong> is waiting for you.
            </p>
            <div
              className="rounded-xl p-4 text-left space-y-2 text-sm"
              style={{ background: 'linear-gradient(135deg, #FFF8E7, #FFF3D0)', border: '1px solid #F5C842' }}
            >
              <p className="font-semibold text-amber-800 mb-1">Gold unlocks:</p>
              {[
                '🐝  Unlimited rooms — join every one that calls to you',
                '✨  Golden Hive badge on your profile & posts',
                '🎨  Create your own Vibe & Collector rooms',
                '📊  Advanced vault analytics & rarity scores',
              ].map((line, i) => (
                <p key={i} className="text-amber-900 text-xs leading-snug">{line}</p>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">Starting at <strong>$4.99 / month</strong></p>
          </div>
          <div className="flex flex-col gap-3 pt-2">
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
              className="w-full rounded-full text-sm text-muted-foreground"
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
