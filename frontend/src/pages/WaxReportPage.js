import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import {
  ArrowLeft, TrendingUp, Music, Disc, Heart, Users, MessageSquare,
  Calendar, Clock, BarChart3, Download, Share2, RefreshCw, ChevronRight, Loader2,
} from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';
import { useShareCard } from '../hooks/useShareCard';
import WaxReportCard from '../components/ShareCards/WaxReportCard';

/* ═══════ Brand Colors ═══════ */
const C = {
  bg: '#FAEDC7', card: '#FFFFFF', textDark: '#2A1A06', textMuted: '#8A6B4A',
  amber: '#996012', amberAccent: '#C8861A', amberLight: '#E8A820', amberDark: '#7A5008',
  purple: '#6B47AD', green: '#339147',
  border: 'rgba(200,134,26,0.15)', divider: 'rgba(200,134,26,0.20)',
  barFill: 'rgba(232,168,32,0.65)', barTrack: 'rgba(200,134,26,0.08)',
};

const WaxReportPage = () => {
  usePageTitle('Your Week in Wax');
  const { reportId } = useParams();
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenLoading, setRegenLoading] = useState(false);
  const headers = { Authorization: `Bearer ${token}` };

  const isGold = user?.golden_hive || user?.golden_hive_verified;
  const { cardRef: waxShareRef, exporting: waxExporting, exportCard: exportWaxCard } = useShareCard({
    cardType: 'wax_report',
    filename: 'thg-wax-report',
    title: 'My Week in Wax — The Honey Groove',
    userId: user?.id,
  });

  const fetchReport = useCallback(async () => {
    try {
      let resp;
      if (reportId) {
        resp = await axios.get(`${API}/wax-reports/${reportId}`, { headers });
      } else {
        resp = await axios.get(`${API}/wax-reports/latest`, { headers });
      }
      setReport(resp.data);
    } catch (err) {
      if (err.response?.status === 404) {
        // No report yet — try generating one
        try {
          const gen = await axios.post(`${API}/wax-reports/generate`, {}, { headers });
          setReport(gen.data);
        } catch { toast.error('Could not generate your report'); }
      } else {
        toast.error('could not load report.');
      }
    } finally { setLoading(false); }
  }, [API, token, reportId]);

  useEffect(() => { fetchReport(); }, [fetchReport]);

  const handleShare = () => {
    if (!report) return;
    const topCover = report.listening_stats?.top_records?.[0]?.cover_url;
    exportWaxCard([topCover].filter(Boolean));
  };

  const handleRegenLabel = async () => {
    if (!report) return;
    setRegenLoading(true);
    try {
      const resp = await axios.post(`${API}/wax-reports/regenerate-label/${report.id}`, {}, { headers });
      setReport(prev => ({ ...prev, personality: resp.data.personality, closing_line: resp.data.closing_line, label_regenerated: true }));
      toast.success('personality updated.');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to regenerate');
    } finally { setRegenLoading(false); }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 pt-3 md:pt-2" style={{ background: C.bg, minHeight: '100vh' }}>
        <Skeleton className="h-8 w-48 mb-4" /><Skeleton className="h-6 w-64 mb-8" />
        {[1,2,3,4].map(i => <Skeleton key={i} className="h-40 w-full mb-4 rounded-2xl" />)}
      </div>
    );
  }

  if (!report) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 pt-3 md:pt-2 text-center" style={{ background: C.bg, minHeight: '100vh' }}>
        <p style={{ color: C.textMuted }}>No report found yet. Keep spinning!</p>
        <Link to="/collection" className="text-sm mt-2 inline-block" style={{ color: C.amberAccent }}>Back to Collection</Link>
      </div>
    );
  }

  const ls = report.listening_stats || {};
  const cv = report.collection_value || {};
  const wp = report.wantlist_pulse || {};
  const ss = report.social_stats || {};

  let weekRange = '';
  try {
    const ws = new Date(report.week_start);
    const we = new Date(report.week_end);
    we.setDate(we.getDate() - 1);
    weekRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} · ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { weekRange = ''; }

  return (
    <div className="min-h-screen pb-24 md:pb-8" style={{ background: C.bg }} data-testid="wax-report-page">
      <div className="max-w-2xl mx-auto px-4 py-8 pt-3 md:pt-2">
        {/* Back */}
        <Link to="/collection" className="inline-flex items-center gap-1.5 text-sm mb-6 transition-colors" style={{ color: C.textMuted }} data-testid="wax-back">
          <ArrowLeft className="w-4 h-4" /> back to collection
        </Link>

        {/* ═══ Header ═══ */}
        <div className="flex items-center gap-4 mb-2" data-testid="wax-header">
          {report.avatar_url
            ? <img src={resolveImageUrl(report.avatar_url)} alt="" className="w-14 h-14 rounded-full object-cover shadow" />
            : <div className="w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold" style={{ background: C.barTrack, color: C.amber }}>{(report.username || '?')[0].toUpperCase()}</div>}
          <div className="flex-1">
            <h1 className="font-heading text-2xl" style={{ color: C.textDark }}>your week in wax</h1>
            <p className="text-sm" style={{ color: C.textMuted }}>@{report.username} · {weekRange}</p>
          </div>
          <button
            onClick={handleShare}
            disabled={waxExporting}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all hover:scale-105 disabled:opacity-60"
            style={{ background: C.barTrack, color: C.amberAccent }}
            title="Share to Stories"
            data-testid="wax-share-btn"
          >
            {waxExporting
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Share2 className="w-4 h-4" />
            }
            Share
          </button>
        </div>

        {/* Hidden WaxReportCard — rendered off-screen for html2canvas */}
        <WaxReportCard
          ref={waxShareRef}
          report={report}
          user={user}
          isGold={isGold}
        />

        {/* ═══ Personality Label ═══ */}
        {report.personality && (
          <WaxCard testId="wax-personality">
            <div className="flex items-start justify-between gap-3">
              <p className="italic text-base" style={{ color: C.amberAccent }}>"{report.personality.label}"</p>
              {!report.label_regenerated && (
                <button onClick={handleRegenLabel} disabled={regenLoading}
                  className="shrink-0 text-xs flex items-center gap-1 px-2 py-1 rounded-full transition-colors"
                  style={{ color: C.textMuted, background: C.barTrack }}
                  data-testid="wax-regen-label">
                  <RefreshCw className={`w-3 h-3 ${regenLoading ? 'animate-spin' : ''}`} /> reroll
                </button>
              )}
            </div>
          </WaxCard>
        )}

        {/* ═══ Listening Stats ═══ */}
        <SectionTitle icon={<Music className="w-4 h-4" />} title="listening stats" />
        <WaxCard testId="wax-listening-stats">
          <div className="grid grid-cols-3 gap-4 mb-3">
            <StatBlock value={ls.total_spins} label="total spins" />
            <StatBlock value={ls.unique_records} label="unique records" />
            <StatBlock value={ls.avg_spins_per_record} label="avg per record" />
          </div>
          <Divider />
          <div className="grid grid-cols-3 gap-4 mt-3">
            <StatBlock value={ls.longest_listening_day?.day} label="longest day" small />
            <StatBlock value={ls.most_active_day} label="most active" small />
            <StatBlock value={ls.most_active_time} label="time of day" small />
          </div>
        </WaxCard>

        {/* ═══ Top 5s ═══ */}
        {report.top_artists?.length > 0 && (
          <>
            <SectionTitle icon={<TrendingUp className="w-4 h-4" />} title="top artists" />
            <WaxCard testId="wax-top-artists">
              {report.top_artists.map((a, i) => (
                <RankedRow key={i} rank={i + 1} label={a.artist} value={`${a.spins} spins`} />
              ))}
            </WaxCard>
          </>
        )}

        {report.top_records?.length > 0 && (
          <>
            <SectionTitle icon={<Disc className="w-4 h-4" />} title="top records" />
            <WaxCard testId="wax-top-records">
              {report.top_records.map((r, i) => (
                <div key={i} className="flex items-center gap-3 py-2">
                  <span className="font-heading text-sm w-6 text-right shrink-0" style={{ color: C.amber }}>{i + 1}</span>
                  {r.cover_url
                    ? <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} className="w-10 h-10 rounded-lg object-cover" isUnofficial={r.is_unofficial} />
                    : <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: C.barTrack }}><Disc className="w-5 h-5" style={{ color: C.amber }} /></div>}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: C.textDark }}>{r.title}</p>
                    <p className="text-xs truncate" style={{ color: C.amberAccent }}>{r.artist}</p>
                  </div>
                  <span className="text-xs shrink-0" style={{ color: C.amberAccent }}>{r.spins} spins</span>
                </div>
              ))}
            </WaxCard>
          </>
        )}

        {report.top_genres?.length > 0 && (
          <>
            <SectionTitle icon={<BarChart3 className="w-4 h-4" />} title="top genres" />
            <WaxCard testId="wax-top-genres">
              {report.top_genres.map((g, i) => (
                <RankedRow key={i} rank={i + 1} label={g.genre} value={`${g.spins} spins`} />
              ))}
            </WaxCard>
          </>
        )}

        {/* ═══ Era Breakdown ═══ */}
        {report.era_breakdown?.length > 0 && (
          <>
            <SectionTitle icon={<Clock className="w-4 h-4" />} title="era breakdown" />
            <WaxCard testId="wax-era">
              {report.era_breakdown.map((e, i) => (
                <div key={i} className="flex items-center gap-3 py-1.5">
                  <span className="text-xs w-10 text-right font-medium" style={{ color: C.textDark }}>{e.decade}</span>
                  <div className="flex-1 h-5 rounded-full overflow-hidden" style={{ background: C.barTrack }}>
                    <div className="h-full rounded-full transition-all" style={{
                      width: `${Math.max(e.pct, 3)}%`,
                      background: `linear-gradient(90deg, ${C.barFill}, rgba(200,134,26,0.35))`,
                    }} />
                  </div>
                  <span className="text-xs w-8 font-medium" style={{ color: C.amber }}>{e.pct}%</span>
                </div>
              ))}
            </WaxCard>
          </>
        )}

        {/* ═══ Mood Breakdown ═══ */}
        {report.mood_breakdown?.length > 0 && (
          <>
            <SectionTitle icon={<Heart className="w-4 h-4" />} title="vinyl mood" />
            <WaxCard testId="wax-moods">
              {report.mood_breakdown.map((m, i) => (
                <div key={i} className="flex items-center justify-between py-1.5 px-2 rounded-lg" style={{ border: `1px solid ${C.border}` }}>
                  <span className="text-sm" style={{ color: C.textDark }}>{m.mood}</span>
                  <span className="text-xs font-medium" style={{ color: C.amberAccent }}>{m.count}x</span>
                </div>
              ))}
            </WaxCard>
          </>
        )}

        {/* ═══ Collection Value ═══ */}
        <SectionTitle icon={<TrendingUp className="w-4 h-4" />} title="collection value" />
        <WaxCard testId="wax-collection-value">
          <div className="flex items-end gap-2 mb-1">
            <span className="font-heading text-3xl" style={{ color: C.amber }}>${cv.total_value?.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
            {cv.value_change !== 0 && (
              <span className="text-xs font-medium mb-1" style={{ color: cv.value_change > 0 ? C.green : '#c0392b' }}>
                {cv.value_change > 0 ? '+' : ''}{cv.value_change?.toFixed(0)} from last week
              </span>
            )}
          </div>
          <Divider />
          <div className="grid grid-cols-3 gap-3 mt-3">
            <StatBlock value={cv.over_50} label="over $50" small />
            <StatBlock value={cv.over_100} label="over $100" small />
            <StatBlock value={cv.over_200} label="over $200" small />
          </div>
          {cv.most_valuable && (
            <div className="mt-3 pt-3" style={{ borderTop: `1px solid ${C.divider}` }}>
              <p className="text-[11px] mb-1" style={{ color: C.textMuted }}>most valuable</p>
              <p className="text-sm font-medium" style={{ color: C.textDark }}>{cv.most_valuable.title}</p>
              <p className="text-xs" style={{ color: C.amberAccent }}>{cv.most_valuable.artist} · ${cv.most_valuable.value?.toFixed(2)}</p>
            </div>
          )}
          {cv.hidden_gem && (
            <div className="mt-2 px-3 py-2 rounded-lg" style={{ background: C.barTrack }}>
              <p className="text-[11px]" style={{ color: C.textMuted }}>hidden gem</p>
              <p className="text-sm" style={{ color: C.textDark }}>{cv.hidden_gem.title} <span style={{ color: C.amberAccent }}>(${cv.hidden_gem.value?.toFixed(0)})</span></p>
            </div>
          )}
        </WaxCard>

        {/* ═══ Wantlist Pulse ═══ */}
        <SectionTitle icon={<Heart className="w-4 h-4" style={{ color: C.purple }} />} title="dream list pulse" />
        <WaxCard testId="wax-wantlist" borderColor="rgba(107,71,173,0.20)">
          <div className="grid grid-cols-3 gap-4">
            <StatBlock value={wp.total} label="on Dream List" color={C.purple} />
            <StatBlock value={wp.matches_found} label="matches found" color={C.purple} />
            <StatBlock value={wp.longest_hunt_days ? `${wp.longest_hunt_days}d` : '·'} label="longest hunt" color={C.purple} />
          </div>
          {wp.trending && (
            <div className="mt-3 px-3 py-2 rounded-lg" style={{ background: 'rgba(107,71,173,0.06)' }}>
              <p className="text-[11px]" style={{ color: C.textMuted }}>trending on Dream Lists</p>
              <p className="text-sm" style={{ color: C.textDark }}>{wp.trending.artist} · {wp.trending.album} <span style={{ color: C.purple }}>({wp.trending.want_count} wants)</span></p>
            </div>
          )}
        </WaxCard>

        {/* ═══ Social Stats ═══ */}
        <SectionTitle icon={<Users className="w-4 h-4" />} title="social" />
        <WaxCard testId="wax-social">
          <div className="grid grid-cols-3 gap-4 mb-3">
            <StatBlock value={ss.new_followers} label="new followers" />
            <StatBlock value={ss.total_posts} label="posts" />
            <StatBlock value={ss.trades_completed} label="trades" />
          </div>
          {ss.most_liked_post && (
            <div className="mt-2 px-3 py-2 rounded-lg" style={{ background: C.barTrack }}>
              <p className="text-[11px]" style={{ color: C.textMuted }}>most liked post</p>
              <p className="text-sm truncate" style={{ color: C.textDark }}>{ss.most_liked_post.content}</p>
              <p className="text-xs" style={{ color: C.amberAccent }}>{ss.most_liked_post.likes} likes</p>
            </div>
          )}
        </WaxCard>

        {/* ═══ Closing Line ═══ */}
        {report.closing_line && (
          <WaxCard testId="wax-closing">
            <p className="text-center italic text-base" style={{ color: C.textDark }}>"{report.closing_line}"</p>
          </WaxCard>
        )}

        {/* ═══ Share Button — hidden until feature is ready ═══ */}

        {/* ═══ History Link ═══ */}
        <Link to="/wax-reports/history" className="flex items-center justify-center gap-1 mt-4 text-sm transition-colors"
          style={{ color: C.textMuted }} data-testid="wax-history-link">
          view past reports <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      {/* ═══ Share Card Modal — hidden until feature is ready ═══ */}
    </div>
  );
};

/* ═══════ Sub-Components ═══════ */

const WaxCard = ({ children, testId, borderColor }) => (
  <Card className="p-4 mb-3 rounded-2xl shadow-sm" style={{ background: '#fff', border: `1px solid ${borderColor || C.border}` }} data-testid={testId}>
    {children}
  </Card>
);

const SectionTitle = ({ icon, title }) => (
  <div className="flex items-center gap-2 mt-5 mb-2 px-1">
    <span style={{ color: C.amberAccent }}>{icon}</span>
    <h2 className="font-heading text-sm uppercase tracking-wide" style={{ color: C.textMuted }}>{title}</h2>
  </div>
);

const StatBlock = ({ value, label, color, small }) => (
  <div>
    <p className={`font-heading ${small ? 'text-base' : 'text-xl'}`} style={{ color: color || C.amber }}>{value ?? '·'}</p>
    <p className="text-[11px]" style={{ color: C.textMuted }}>{label}</p>
  </div>
);

const RankedRow = ({ rank, label, value }) => (
  <div className="flex items-center gap-3 py-1.5">
    <span className="font-heading text-sm w-6 text-right" style={{ color: C.amber }}>{rank}</span>
    <span className="flex-1 text-sm font-medium truncate" style={{ color: C.textDark }}>{label}</span>
    <span className="text-xs shrink-0" style={{ color: C.amberAccent }}>{value}</span>
  </div>
);

const Divider = () => <div style={{ height: 1, background: C.divider }} className="my-2" />;

export default WaxReportPage;
