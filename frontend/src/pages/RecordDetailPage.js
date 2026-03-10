import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
  Disc, Users, BarChart3, Heart, Clock, ArrowLeft,
  Loader2, Calendar, Music2, Play, User, TrendingUp, ShoppingBag, ArrowRightLeft
} from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import { toast } from 'sonner';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';
import { PostTypeBadge } from '../components/PostCards';
import SEOHead from '../components/SEOHead';
import { RarityPill, RarityCard } from '../components/RarityBadge';
import VariantCompletion from '../components/VariantCompletion';

const RecordDetailPage = () => {
  usePageTitle('Record Details');
  const { recordId } = useParams();
  const { token, API, user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [spinning, setSpinning] = useState(false);
  const [rarity, setRarity] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/records/${recordId}/detail`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
        if (res.data.record?.discogs_id) {
          axios.get(`${API}/vinyl/rarity/${res.data.record.discogs_id}`)
            .then(r => setRarity(r.data))
            .catch(() => {});
        }
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
    <div className="min-h-screen flex items-center justify-center pt-16 md:pt-24">
      <Loader2 className="w-8 h-8 animate-spin text-honey-amber" />
    </div>
  );

  if (!data) return null;

  const { record, owner, community, market_value, related_posts } = data;
  const isOwner = owner?.id === user?.id;

  const recordTitle = `${record.artist} - ${record.title}${record.color_variant ? ` (${record.color_variant})` : ''}${record.year ? ` [${record.year}]` : ''}`;
  const recordDesc = `${record.artist} - ${record.title}${record.color_variant ? ` — ${record.color_variant} pressing` : ''}${record.year ? ` (${record.year})` : ''} in a collector's vinyl library on The Honey Groove. ${community?.total_owners || 0} collectors own this record.`;

  return (
    <div className="max-w-4xl mx-auto px-4 pt-16 md:pt-24 pb-28" data-testid="record-detail-page">
      <SEOHead
        title={recordTitle}
        description={recordDesc}
        url={`/record/${recordId}`}
        image={record.cover_url}
        type="music.song"
        vinylMeta={{
          artist: record.artist,
          album: record.title,
          variant: record.color_variant,
          year: record.year,
          format: record.format || 'Vinyl',
        }}
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'MusicRecording',
          name: record.title,
          byArtist: { '@type': 'MusicGroup', name: record.artist },
          image: record.cover_url,
          url: `https://thehoneygroove.com/record/${recordId}`,
          ...(record.year && { datePublished: String(record.year) }),
          additionalProperty: [
            ...(record.color_variant ? [{ '@type': 'PropertyValue', name: 'Variant', value: record.color_variant }] : []),
            ...(record.format ? [{ '@type': 'PropertyValue', name: 'Format', value: record.format }] : []),
          ],
        }}
      />
      {/* Back nav */}
      <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-sm text-stone-500 hover:text-vinyl-black mb-8 transition-colors group" data-testid="back-btn">
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" /> Back
      </button>

      {/* Hero section */}
      <div className="flex flex-col md:flex-row gap-8 mb-10" data-testid="record-hero">
        {/* Album art */}
        <div className="shrink-0">
          <div className="w-full md:w-80 aspect-square rounded-2xl overflow-hidden bg-honey/10 shadow-lg shadow-black/5">
            {record.cover_url ? (
              <AlbumArt src={record.cover_url} alt={`${record.artist} ${record.title}${record.color_variant ? ` ${record.color_variant}` : ''} vinyl record`} className="w-full h-full object-cover" data-testid="record-cover" />
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

          {record.color_variant && (
            <p className="text-sm font-medium text-vinyl-black/80 mb-4" data-testid="record-variant">
              {record.color_variant}
            </p>
          )}

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
            {rarity?.tier && <RarityPill tier={rarity.tier} size="sm" />}
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

          {/* Global Rarity Card */}
          {rarity?.tier && (
            <div className="mb-6">
              <RarityCard rarity={rarity} />
            </div>
          )}

          {/* Owner */}
          {owner && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>Added by</span>
              <Link to={`/profile/${owner.username}`} className="flex items-center gap-1.5 text-vinyl-black hover:text-honey-amber transition-colors" data-testid="record-owner-link">
                <img src={resolveImageUrl(owner.avatar_url)} alt={`${owner.username} avatar`} className="w-5 h-5 rounded-full" />
                <span className="font-medium">@{owner.username}</span>
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8" data-testid="stats-grid">
        <StatCard icon={Play} label="Your Spins" value={record.spin_count || 0} noSpinsLabel />
        <StatCard icon={BarChart3} label="Community Spins" value={community.total_spins || 0} />
        <StatCard icon={Users} label="Collectors" value={community.total_owners || 0} />
        <StatCard icon={Heart} label="Wanted" value={community.wantlist_count || 0} />
      </div>

      {/* Variant Completion */}
      {record.discogs_id && (
        <div className="mb-8">
          <VariantCompletion discogsId={record.discogs_id} />
        </div>
      )}

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
              <p className="font-heading text-lg text-vinyl-black">${market_value.low?.toFixed(2) || '·'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">Median</p>
              <p className="font-heading text-xl text-honey-amber font-bold">${market_value.median?.toFixed(2) || '·'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">High</p>
              <p className="font-heading text-lg text-vinyl-black">${market_value.high?.toFixed(2) || '·'}</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Based on Discogs marketplace data</p>
        </Card>
      )}

      {/* List / Trade action buttons (only for record owner) */}
      {isOwner && (
        <div className="flex gap-3 mb-8" data-testid="listing-actions">
          <Button
            variant="outline"
            className="flex-1 h-11 gap-2 border-amber-400 text-amber-700 hover:bg-amber-50 hover:border-amber-500"
            onClick={() => navigate(`/honeypot?create=sale&artist=${encodeURIComponent(record.artist)}&album=${encodeURIComponent(record.title)}&discogs_id=${record.discogs_id || ''}&cover_url=${encodeURIComponent(record.cover_url || '')}&year=${record.year || ''}`)}
            data-testid="list-for-sale-btn"
          >
            <ShoppingBag className="w-4 h-4" />
            List for Sale
          </Button>
          <Button
            variant="outline"
            className="flex-1 h-11 gap-2 border-stone-300 text-stone-700 hover:bg-stone-50 hover:border-stone-400"
            style={{ background: 'rgba(255,246,230,0.5)' }}
            onClick={() => navigate(`/honeypot?create=trade&artist=${encodeURIComponent(record.artist)}&album=${encodeURIComponent(record.title)}&discogs_id=${record.discogs_id || ''}&cover_url=${encodeURIComponent(record.cover_url || '')}&year=${record.year || ''}`)}
            data-testid="offer-to-trade-btn"
          >
            <ArrowRightLeft className="w-4 h-4" />
            Offer to Trade
          </Button>
        </div>
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
                <img src={resolveImageUrl(o.avatar_url)} alt={`${o.username} avatar`} className="w-6 h-6 rounded-full" />
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
                      <img src={resolveImageUrl(post.user.avatar_url)} alt={`${post.user.username} avatar`} className="w-8 h-8 rounded-full" />
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
      {record.notes && record.notes !== 'Imported from Discogs' && (
        <div className="mt-8" data-testid="record-notes">
          <h3 className="font-heading text-lg mb-2">Notes</h3>
          <p className="text-sm text-vinyl-black/70 bg-honey/5 rounded-xl p-4 border border-honey/10">{record.notes}</p>
        </div>
      )}
    </div>
  );
};

// ── Helper components ──

const StatCard = ({ icon: Icon, label, value, noSpinsLabel }) => (
  <Card className="p-4 border-honey/15 text-center">
    <Icon className="w-5 h-5 text-honey-amber mx-auto mb-1.5" />
    {noSpinsLabel && value === 0 ? (
      <p className="text-sm text-muted-foreground mt-1">no logged spins</p>
    ) : (
      <p className="font-heading text-2xl text-vinyl-black">{value}</p>
    )}
    <p className="text-xs text-muted-foreground">{label}</p>
  </Card>
);

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
