import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
  Disc, Users, BarChart3, Heart, Clock, ArrowLeft,
  Loader2, Calendar, Music2, Play, User, TrendingUp
} from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import { toast } from 'sonner';

const RecordDetailPage = () => {
  usePageTitle('Record Details');
  const { recordId } = useParams();
  const { token, API, user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [spinning, setSpinning] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/records/${recordId}/detail`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
      } catch {
        toast.error('record not found.');
        navigate('/collection');
      }
      setLoading(false);
    })();
  }, [recordId, API, token, navigate]);

  const logSpin = async () => {
    setSpinning(true);
    try {
      await axios.post(`${API}/spins`, { record_id: recordId }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(prev => ({
        ...prev,
        record: { ...prev.record, spin_count: (prev.record.spin_count || 0) + 1 },
        community: { ...prev.community, total_spins: (prev.community.total_spins || 0) + 1 },
      }));
      toast.success('spin logged.');
    } catch { toast.error('could not log spin. try again.'); }
    setSpinning(false);
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center pt-20">
      <Loader2 className="w-8 h-8 animate-spin text-honey-amber" />
    </div>
  );

  if (!data) return null;

  const { record, owner, community, market_value, related_posts } = data;
  const isOwner = owner?.id === user?.id;

  return (
    <div className="max-w-4xl mx-auto px-4 pt-20 pb-28" data-testid="record-detail-page">
      {/* Back nav */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-vinyl-black mb-6 transition-colors" data-testid="back-btn">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      {/* Hero section */}
      <div className="flex flex-col md:flex-row gap-8 mb-10" data-testid="record-hero">
        {/* Album art */}
        <div className="shrink-0">
          <div className="w-full md:w-80 aspect-square rounded-2xl overflow-hidden bg-honey/10 shadow-lg shadow-black/5">
            {record.cover_url ? (
              <img src={record.cover_url} alt={record.title} className="w-full h-full object-cover" data-testid="record-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Disc className="w-20 h-20 text-honey/30" />
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h1 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-1 leading-tight" data-testid="record-title">
            {record.title}
          </h1>
          <p className="text-xl text-honey-amber font-serif italic mb-4" data-testid="record-artist">
            {record.artist}
          </p>

          <div className="flex flex-wrap gap-2 mb-6">
            {record.year && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-honey/10 text-sm text-vinyl-black/70">
                <Calendar className="w-3.5 h-3.5" /> {record.year}
              </span>
            )}
            {record.format && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-honey/10 text-sm text-vinyl-black/70">
                <Disc className="w-3.5 h-3.5" /> {record.format}
              </span>
            )}
            {record.discogs_id && (
              <a href={`https://www.discogs.com/release/${record.discogs_id}`} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-vinyl-black/5 text-sm text-vinyl-black/70 hover:bg-vinyl-black/10 transition-colors">
                <Music2 className="w-3.5 h-3.5" /> Discogs
              </a>
            )}
          </div>

          {/* Spin button */}
          {isOwner && (
            <Button onClick={logSpin} disabled={spinning}
              className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full px-6 py-3 text-base font-medium mb-6"
              data-testid="spin-btn">
              {spinning ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
              Log a Spin
            </Button>
          )}

          {/* Owner */}
          {owner && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>Added by</span>
              <Link to={`/profile/${owner.username}`} className="flex items-center gap-1.5 text-vinyl-black hover:text-honey-amber transition-colors" data-testid="record-owner-link">
                <img src={owner.avatar_url} alt="" className="w-5 h-5 rounded-full" />
                <span className="font-medium">@{owner.username}</span>
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8" data-testid="stats-grid">
        <StatCard icon={Play} label="Your Spins" value={record.spin_count || 0} />
        <StatCard icon={BarChart3} label="Community Spins" value={community.total_spins || 0} />
        <StatCard icon={Users} label="Collectors" value={community.total_owners || 0} />
        <StatCard icon={Heart} label="Wanted" value={community.wantlist_count || 0} />
      </div>

      {/* Market value */}
      {market_value && (
        <Card className="p-5 border-honey/20 mb-8" data-testid="market-value-card">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-honey-amber" />
            <h3 className="font-heading text-lg">Market Value</h3>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">Low</p>
              <p className="font-heading text-lg text-vinyl-black">${market_value.low?.toFixed(2) || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">Median</p>
              <p className="font-heading text-xl text-honey-amber font-bold">${market_value.median?.toFixed(2) || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">High</p>
              <p className="font-heading text-lg text-vinyl-black">${market_value.high?.toFixed(2) || '—'}</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Based on Discogs marketplace data</p>
        </Card>
      )}

      {/* Community owners */}
      {community.owners?.length > 0 && (
        <div className="mb-8" data-testid="community-owners">
          <h3 className="font-heading text-lg mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-honey-amber" /> In {community.total_owners} Collection{community.total_owners !== 1 ? 's' : ''}
          </h3>
          <div className="flex flex-wrap gap-2">
            {community.owners.map((o) => (
              <Link key={o.id} to={`/profile/${o.username}`}
                className="flex items-center gap-2 px-3 py-2 rounded-full bg-honey/8 hover:bg-honey/15 transition-colors"
                data-testid={`owner-${o.username}`}>
                <img src={o.avatar_url} alt="" className="w-6 h-6 rounded-full" />
                <span className="text-sm font-medium">@{o.username}</span>
              </Link>
            ))}
            {community.total_owners > 12 && (
              <span className="flex items-center px-3 py-2 rounded-full bg-honey/8 text-sm text-muted-foreground">
                +{community.total_owners - 12} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Related posts */}
      {related_posts?.length > 0 && (
        <div data-testid="related-posts">
          <h3 className="font-heading text-lg mb-3 flex items-center gap-2">
            <Disc className="w-4 h-4 text-honey-amber" /> Hive Activity
          </h3>
          <div className="space-y-2">
            {related_posts.map((post) => (
              <Card key={post.id} className="p-4 border-honey/15 hover:border-honey/30 transition-colors" data-testid={`post-${post.id}`}>
                <div className="flex items-start gap-3">
                  {post.user && (
                    <Link to={`/profile/${post.user.username}`}>
                      <img src={post.user.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                    </Link>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      {post.user && (
                        <Link to={`/profile/${post.user.username}`} className="font-medium text-sm hover:text-honey-amber transition-colors">
                          @{post.user.username}
                        </Link>
                      )}
                      <PostTypeBadge type={post.post_type} />
                    </div>
                    {post.caption && <p className="text-sm text-vinyl-black/80 line-clamp-2">{post.caption}</p>}
                    <p className="text-xs text-muted-foreground mt-1">
                      <TimeAgo date={post.created_at} />
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {record.notes && (
        <div className="mt-8" data-testid="record-notes">
          <h3 className="font-heading text-lg mb-2">Notes</h3>
          <p className="text-sm text-vinyl-black/70 bg-honey/5 rounded-xl p-4 border border-honey/10">{record.notes}</p>
        </div>
      )}
    </div>
  );
};

// ── Helper components ──

const StatCard = ({ icon: Icon, label, value }) => (
  <Card className="p-4 border-honey/15 text-center">
    <Icon className="w-5 h-5 text-honey-amber mx-auto mb-1.5" />
    <p className="font-heading text-2xl text-vinyl-black">{value}</p>
    <p className="text-xs text-muted-foreground">{label}</p>
  </Card>
);

const PostTypeBadge = ({ type }) => {
  const labels = {
    'NOW_SPINNING': 'Now Spinning',
    'ADDED_TO_COLLECTION': 'Added',
    'NEW_HAUL': 'Haul',
    'ISO': 'ISO',
    'NOTE': 'Note',
  };
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-honey/15 text-honey-amber">
      {labels[type] || type}
    </span>
  );
};

const TimeAgo = ({ date }) => {
  const diff = Date.now() - new Date(date).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return <span>just now</span>;
  if (mins < 60) return <span>{mins}m ago</span>;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return <span>{hrs}h ago</span>;
  const days = Math.floor(hrs / 24);
  if (days < 7) return <span>{days}d ago</span>;
  return <span>{new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>;
};

export default RecordDetailPage;
