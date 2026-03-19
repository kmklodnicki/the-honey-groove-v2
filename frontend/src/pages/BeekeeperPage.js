import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import {
  Loader2, RefreshCw, CheckCircle, XCircle, Pencil, Search,
  Users, BarChart2, Droplets, ListChecks, Shield, AlertTriangle,
  ChevronRight, ChevronDown, Ban, AlertCircle, Star, Trash2,
} from 'lucide-react';

// ─── Helpers ───────────────────────────────────────────────────────────────

const THEME_PRESETS = ['honey', 'midnight', 'forest', 'rose', 'slate', 'plum'];
const THEME_COLORS = {
  honey: '#C8861A', midnight: '#7B68EE', forest: '#74C69D',
  rose: '#D98FA1', slate: '#85A7C0', plum: '#D7BDE2',
};
const REJECT_REASONS = [
  { value: 'duplicate', label: 'Duplicate — a similar room exists' },
  { value: 'inappropriate', label: 'Inappropriate content' },
  { value: 'vague', label: 'Too vague — needs more detail' },
  { value: 'spam', label: 'Spam' },
];

function timeAgo(iso) {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// ─── Tab: Queue ─────────────────────────────────────────────────────────────

function QueueTab({ API, headers }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [rejectDialog, setRejectDialog] = useState(null); // { slug, name }
  const [rejectReason, setRejectReason] = useState('duplicate');
  const [rejectNote, setRejectNote] = useState('');
  const [editDialog, setEditDialog] = useState(null); // room data
  const [editForm, setEditForm] = useState({});
  const [actionLoading, setActionLoading] = useState(null);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const params = filter !== 'all' ? `?type=${filter}` : '';
      const res = await axios.get(`${API}/beekeeper/queue${params}`, { headers });
      setItems(res.data.items || []);
    } catch {
      toast.error('Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, [API, headers, filter]);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  const approve = async (slug) => {
    setActionLoading(slug + '_approve');
    try {
      await axios.post(`${API}/beekeeper/rooms/${slug}/approve`, {}, { headers });
      toast.success('Room approved!');
      fetchQueue();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to approve');
    } finally {
      setActionLoading(null);
    }
  };

  const reject = async () => {
    if (!rejectDialog) return;
    setActionLoading(rejectDialog.slug + '_reject');
    try {
      await axios.post(`${API}/beekeeper/rooms/${rejectDialog.slug}/reject`, {
        reason: rejectReason, note: rejectNote,
      }, { headers });
      toast.success('Room rejected, creator notified');
      setRejectDialog(null);
      setRejectNote('');
      fetchQueue();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to reject');
    } finally {
      setActionLoading(null);
    }
  };

  const saveEdit = async () => {
    if (!editDialog) return;
    setActionLoading(editDialog.slug + '_edit');
    try {
      await axios.put(`${API}/beekeeper/rooms/${editDialog.slug}/edit`, editForm, { headers });
      toast.success('Room edited and approved!');
      setEditDialog(null);
      fetchQueue();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to edit');
    } finally {
      setActionLoading(null);
    }
  };

  const openEdit = (room) => {
    setEditDialog(room);
    setEditForm({
      name: room.name,
      description: room.tagline || '',
      theme_preset: room.theme_preset || 'honey',
    });
  };

  return (
    <div>
      {/* Filter pills */}
      <div className="flex gap-2 mb-5">
        {['all', 'rooms', 'reports'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-all ${filter === f ? 'bg-amber-400 text-amber-900 border-amber-500' : 'bg-white text-stone-500 border-stone-200 hover:border-amber-300'}`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <button onClick={fetchQueue} className="ml-auto text-stone-400 hover:text-stone-600 transition-colors" aria-label="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-amber-400" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-stone-400">
          <CheckCircle className="w-10 h-10 mx-auto mb-3 text-green-400" />
          <p className="font-medium">Queue is clear</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(item => (
            item.item_type === 'room'
              ? <RoomQueueCard
                  key={item.id}
                  item={item}
                  actionLoading={actionLoading}
                  onApprove={approve}
                  onReject={(slug, name) => { setRejectDialog({ slug, name }); setRejectReason('duplicate'); setRejectNote(''); }}
                  onEdit={openEdit}
                />
              : <ReportQueueCard key={item.id} item={item} />
          ))}
        </div>
      )}

      {/* Reject dialog */}
      {rejectDialog && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="font-semibold text-lg text-stone-800 mb-1">Reject room</h3>
            <p className="text-sm text-stone-500 mb-4">"{rejectDialog.name}"</p>
            <div className="space-y-2 mb-4">
              {REJECT_REASONS.map(r => (
                <label key={r.value} className="flex items-center gap-3 p-3 rounded-xl border cursor-pointer hover:bg-stone-50 transition-colors">
                  <input type="radio" name="reason" value={r.value} checked={rejectReason === r.value}
                    onChange={() => setRejectReason(r.value)} className="accent-amber-500" />
                  <span className="text-sm text-stone-700">{r.label}</span>
                </label>
              ))}
            </div>
            <textarea
              value={rejectNote}
              onChange={e => setRejectNote(e.target.value)}
              placeholder="Optional note to creator..."
              className="w-full border border-stone-200 rounded-xl p-3 text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-amber-300 mb-4"
            />
            <div className="flex gap-3">
              <button onClick={() => setRejectDialog(null)}
                className="flex-1 py-2 rounded-xl border border-stone-200 text-stone-600 text-sm font-medium hover:bg-stone-50 transition-colors">
                Cancel
              </button>
              <button onClick={reject} disabled={actionLoading}
                className="flex-1 py-2 rounded-xl bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors disabled:opacity-50">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit dialog */}
      {editDialog && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="font-semibold text-lg text-stone-800 mb-4">Edit & Approve</h3>
            <div className="space-y-3 mb-4">
              <div>
                <label className="block text-xs font-medium text-stone-500 mb-1">Room Name</label>
                <input value={editForm.name || ''} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full border border-stone-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-300" />
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-500 mb-1">Description</label>
                <textarea value={editForm.description || ''} onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))}
                  className="w-full border border-stone-200 rounded-xl px-3 py-2 text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-amber-300" />
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-500 mb-1">Theme</label>
                <div className="flex gap-2 flex-wrap">
                  {THEME_PRESETS.map(t => (
                    <button key={t} onClick={() => setEditForm(f => ({ ...f, theme_preset: t }))}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${editForm.theme_preset === t ? 'ring-2 ring-offset-1' : ''}`}
                      style={{ borderColor: THEME_COLORS[t], color: THEME_COLORS[t], ringColor: THEME_COLORS[t] }}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setEditDialog(null)}
                className="flex-1 py-2 rounded-xl border border-stone-200 text-stone-600 text-sm font-medium hover:bg-stone-50 transition-colors">
                Cancel
              </button>
              <button onClick={saveEdit} disabled={actionLoading}
                className="flex-1 py-2 rounded-xl bg-amber-500 text-white text-sm font-medium hover:bg-amber-600 transition-colors disabled:opacity-50">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Save & Approve'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function RoomQueueCard({ item, actionLoading, onApprove, onReject, onEdit }) {
  const room = item.data;
  const creator = item.creator;
  const accentColor = THEME_COLORS[room.theme_preset] || '#C8861A';
  const isGold = creator?.golden_hive_verified || creator?.golden_hive;

  return (
    <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl flex-shrink-0"
          style={{ background: room.theme?.bgGradient || '#FFF3E0' }}>
          {room.emoji || '🍯'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-stone-800 text-sm">{room.name}</h3>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ background: accentColor + '20', color: accentColor }}>
              {room.type}
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-stone-100 text-stone-500">
              {room.theme_preset}
            </span>
          </div>
          {room.tagline && <p className="text-xs text-stone-500 mb-2 line-clamp-2">{room.tagline}</p>}
          <div className="flex items-center gap-2 text-xs text-stone-400">
            <span>by @{creator?.username || 'unknown'}</span>
            {isGold && <span className="text-amber-500 font-medium">Gold</span>}
            <span>·</span>
            <span>{timeAgo(item.submitted_at)}</span>
          </div>
        </div>
      </div>
      <div className="flex gap-2 mt-4">
        <button onClick={() => onApprove(room.slug)}
          disabled={actionLoading === room.slug + '_approve'}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-green-500 text-white text-xs font-medium hover:bg-green-600 transition-colors disabled:opacity-50"
          data-testid={`approve-${room.slug}`}>
          {actionLoading === room.slug + '_approve' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
          Approve
        </button>
        <button onClick={() => onEdit(room)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-100 text-amber-700 text-xs font-medium hover:bg-amber-200 transition-colors"
          data-testid={`edit-${room.slug}`}>
          <Pencil className="w-3.5 h-3.5" /> Edit & Approve
        </button>
        <button onClick={() => onReject(room.slug, room.name)}
          disabled={actionLoading === room.slug + '_reject'}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-50 text-red-500 text-xs font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
          data-testid={`reject-${room.slug}`}>
          <XCircle className="w-3.5 h-3.5" /> Reject
        </button>
      </div>
    </div>
  );
}

function ReportQueueCard({ item }) {
  const report = item.data;
  return (
    <div className="bg-white rounded-2xl border border-orange-200 p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-stone-800">{report.type || 'Report'}</span>
            <span className="px-2 py-0.5 rounded-full text-xs bg-orange-100 text-orange-700">{report.target_type}</span>
          </div>
          {report.reason && <p className="text-xs text-stone-600 mb-1">{report.reason}</p>}
          <div className="text-xs text-stone-400">
            by @{item.reporter?.username || 'unknown'} · {timeAgo(item.submitted_at)}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Tab: Honey Drop ────────────────────────────────────────────────────────

function HoneyDropTab({ API, headers }) {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [blurb, setBlurb] = useState('');
  const [scheduleDate, setScheduleDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [submitting, setSubmitting] = useState(false);
  const [today, setToday] = useState(null);

  useEffect(() => {
    // Load suggestions
    axios.get(`${API}/beekeeper/honey-drop/suggestions`, { headers })
      .then(r => setSuggestions(r.data.suggestions || []))
      .catch(() => {});

    // Load today's drop
    axios.get(`${API}/honey-drop/today`)
      .then(r => setToday(r.data))
      .catch(() => {});
  }, [API, headers]);

  const searchDiscogs = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await axios.get(`${API}/discogs/search`, {
        params: { q: query, type: 'release' },
        headers,
      });
      setSearchResults(res.data.results || res.data || []);
    } catch {
      toast.error('Discogs search failed');
    } finally {
      setSearching(false);
    }
  };

  const schedule = async () => {
    if (!selected) return toast.error('Select a record first');
    setSubmitting(true);
    try {
      await axios.post(`${API}/beekeeper/honey-drop`, {
        date: scheduleDate,
        discogs_id: selected.discogs_id || selected.id,
        blurb,
      }, { headers });
      toast.success(`Honey Drop scheduled for ${scheduleDate}!`);
      setSelected(null);
      setBlurb('');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to schedule');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid md:grid-cols-2 gap-6">
      {/* Left: search + suggestions */}
      <div>
        <h3 className="font-semibold text-stone-700 mb-3 text-sm">Search Discogs</h3>
        <div className="flex gap-2 mb-4">
          <input value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && searchDiscogs()}
            placeholder="Artist, album title..."
            className="flex-1 border border-stone-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-300" />
          <button onClick={searchDiscogs} disabled={searching}
            className="px-3 py-2 rounded-xl bg-amber-500 text-white hover:bg-amber-600 transition-colors disabled:opacity-50">
            {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          </button>
        </div>

        {searchResults.length > 0 && (
          <div className="space-y-2 mb-6 max-h-64 overflow-y-auto">
            {searchResults.slice(0, 10).map(r => (
              <button key={r.id || r.discogs_id} onClick={() => setSelected(r)}
                className={`w-full flex items-center gap-3 p-2 rounded-xl border text-left transition-all hover:border-amber-300 ${selected?.id === r.id ? 'border-amber-400 bg-amber-50' : 'border-stone-200'}`}>
                <AlbumArt src={r.cover_image || r.cover_url} alt={r.title} className="w-10 h-10 rounded-lg flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-stone-800 truncate">{r.title}</p>
                  <p className="text-xs text-stone-400 truncate">{r.artist || r.label?.[0]}</p>
                </div>
              </button>
            ))}
          </div>
        )}

        <h3 className="font-semibold text-stone-700 mb-3 text-sm">Suggestions (want/own ratio)</h3>
        <div className="space-y-2">
          {suggestions.map(s => (
            <button key={s.discogs_id} onClick={() => setSelected(s)}
              className={`w-full flex items-center gap-3 p-2 rounded-xl border text-left transition-all hover:border-amber-300 ${selected?.discogs_id === s.discogs_id ? 'border-amber-400 bg-amber-50' : 'border-stone-200'}`}>
              <AlbumArt src={s.cover_url} alt={s.album} className="w-10 h-10 rounded-lg flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-stone-800 truncate">{s.album}</p>
                <p className="text-xs text-stone-400 truncate">{s.artist}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-xs text-amber-600 font-medium">{s.want_count} wants</p>
                <p className="text-xs text-stone-400">{s.own_count} own</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Right: selected + scheduler */}
      <div>
        {selected && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-4">
            <div className="flex gap-3 mb-3">
              <AlbumArt src={selected.cover_image || selected.cover_url} alt={selected.title || selected.album}
                className="w-16 h-16 rounded-xl flex-shrink-0" />
              <div>
                <p className="font-semibold text-stone-800 text-sm">{selected.title || selected.album}</p>
                <p className="text-xs text-stone-500">{selected.artist}</p>
                {selected.want_count && <p className="text-xs text-amber-600 mt-1">{selected.want_count} wants · {selected.own_count} own</p>}
                {selected.estimated_value > 0 && <p className="text-xs text-stone-500">~${selected.estimated_value}</p>}
              </div>
            </div>
            <textarea value={blurb} onChange={e => setBlurb(e.target.value)}
              placeholder="Write a 2-3 sentence editorial blurb..."
              className="w-full border border-amber-200 rounded-xl p-3 text-sm resize-none h-24 focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white mb-3" />
            <div className="flex gap-3 items-center">
              <div className="flex-1">
                <label className="block text-xs font-medium text-stone-500 mb-1">Schedule date</label>
                <input type="date" value={scheduleDate} onChange={e => setScheduleDate(e.target.value)}
                  className="w-full border border-amber-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white" />
              </div>
              <button onClick={schedule} disabled={submitting}
                className="mt-5 px-4 py-2 rounded-xl bg-amber-500 text-white text-sm font-medium hover:bg-amber-600 transition-colors disabled:opacity-50 whitespace-nowrap flex items-center gap-2">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Droplets className="w-4 h-4" />}
                Schedule Drop
              </button>
            </div>
          </div>
        )}

        {today && (
          <div>
            <h3 className="font-semibold text-stone-700 mb-3 text-sm">Today's Drop</h3>
            <div className="bg-white border border-stone-200 rounded-2xl p-4 flex gap-3">
              <AlbumArt src={today.record?.cover_url} alt={today.record?.title} className="w-14 h-14 rounded-xl flex-shrink-0" />
              <div>
                <p className="font-semibold text-stone-800 text-sm">{today.record?.title}</p>
                <p className="text-xs text-stone-500">{today.record?.artist}</p>
                {today.auto_selected && <span className="text-xs text-stone-400 italic">Auto-selected</span>}
                {today.blurb && <p className="text-xs text-stone-600 mt-1 line-clamp-2">{today.blurb}</p>}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Tab: Metrics ────────────────────────────────────────────────────────────

function MetricsTab({ API, headers }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/beekeeper/metrics`, { headers });
      setData(res.data);
    } catch {
      toast.error('Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMetrics(); }, []);

  if (loading) return <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-amber-400" /></div>;
  if (!data) return null;

  const panels = [
    {
      title: 'Overview', color: '#E8A820',
      rows: [
        ['Total users', data.overview?.total_users?.toLocaleString()],
        ['Active (7d)', data.overview?.active_7d?.toLocaleString()],
        ['Active (30d)', data.overview?.active_30d?.toLocaleString()],
        ['New this week', data.overview?.new_this_week?.toLocaleString()],
        ['Queue items', data.overview?.queue_count?.toLocaleString()],
      ]
    },
    {
      title: 'Revenue', color: '#4CAF50',
      rows: [
        ['Gold members', data.revenue?.gold_count?.toLocaleString()],
        ['Est. MRR', `$${data.revenue?.gold_mrr_estimate?.toLocaleString()}`],
        ['GMV this month', `$${(data.revenue?.marketplace_gmv_month || 0).toFixed(2)}`],
        ['Sales this month', data.revenue?.sales_this_month?.toLocaleString()],
      ]
    },
    {
      title: 'Engagement', color: '#9C27B0',
      rows: [
        ['Posts (7d)', data.engagement?.posts_7d?.toLocaleString()],
        ['Active streaks', data.engagement?.active_streaks?.toLocaleString()],
        ['Longest streak', `${data.engagement?.longest_streak} days`],
      ]
    },
    {
      title: 'Marketplace', color: '#2196F3',
      rows: [
        ['Active listings', data.marketplace?.active_listings?.toLocaleString()],
        ['Sales this week', data.marketplace?.sales_this_week?.toLocaleString()],
        ['Active disputes', data.marketplace?.active_disputes?.toLocaleString()],
      ]
    },
    {
      title: 'Growth', color: '#FF5722',
      rows: [
        ['Signups this week', data.growth?.signups_this_week?.toLocaleString()],
        ['Onboarding rate', `${data.growth?.onboarding_completion_rate}%`],
        ['Discogs imported', data.growth?.discogs_imported?.toLocaleString()],
        ['Manual only', data.growth?.manual_only?.toLocaleString()],
      ]
    },
    {
      title: 'Rooms', color: '#607D8B',
      rows: [
        ['Active rooms', data.rooms?.total_active_rooms?.toLocaleString()],
        ['Pending rooms', data.rooms?.pending_rooms?.toLocaleString()],
        ['Most popular', data.rooms?.most_popular_room ? `${data.rooms.most_popular_room.name} (${data.rooms.most_popular_room.member_count})` : '—'],
        ['Room posts (7d)', data.rooms?.room_posts_7d?.toLocaleString()],
        ['At room limit', data.rooms?.users_at_room_limit?.toLocaleString()],
      ]
    },
    {
      title: 'Email & Waitlist', color: '#795548',
      rows: [
        ['Newsletter signups', data.email?.newsletter_subscribers?.toLocaleString()],
        ['Teaser views (total)', data.email?.teaser_views_total?.toLocaleString()],
        ['Teaser views (week)', data.email?.teaser_views_week?.toLocaleString()],
      ]
    },
  ];

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button onClick={fetchMetrics}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-stone-200 text-stone-500 text-sm hover:bg-stone-50 transition-colors">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {panels.map(panel => (
          <div key={panel.title} className="bg-white rounded-2xl border border-stone-200 p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full" style={{ background: panel.color }} />
              <h3 className="font-semibold text-stone-700 text-sm">{panel.title}</h3>
            </div>
            <div className="space-y-2">
              {panel.rows.map(([label, value]) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="text-xs text-stone-400">{label}</span>
                  <span className="text-xs font-semibold text-stone-800">{value ?? '—'}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Tab: Users ──────────────────────────────────────────────────────────────

function UsersTab({ API, headers }) {
  const [query, setQuery] = useState('');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const searchTimeout = useRef(null);

  const search = useCallback(async (q) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/beekeeper/users`, { params: { q }, headers });
      setUsers(res.data.users || []);
    } catch {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  }, [API, headers]);

  useEffect(() => {
    search('');
  }, [search]);

  const handleQueryChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => search(val), 350);
  };

  const openDetail = async (user) => {
    setSelected(user);
    setDetail(null);
    setDetailLoading(true);
    try {
      const res = await axios.get(`${API}/beekeeper/users/${user.id}`, { headers });
      setDetail(res.data);
    } catch {
      toast.error('Failed to load user detail');
    } finally {
      setDetailLoading(false);
    }
  };

  const doAction = async (userId, action, extra = {}) => {
    setActionLoading(action);
    try {
      await axios.post(`${API}/beekeeper/users/${userId}/action`, { action, ...extra }, { headers });
      toast.success(`Action "${action}" completed`);
      // Refresh detail
      const res = await axios.get(`${API}/beekeeper/users/${userId}`, { headers });
      setDetail(res.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || `Action failed`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="grid md:grid-cols-5 gap-6 min-h-[500px]">
      {/* User list */}
      <div className="md:col-span-2">
        <div className="relative mb-3">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
          <input value={query} onChange={handleQueryChange}
            placeholder="Search username or email..."
            className="w-full border border-stone-200 rounded-xl pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-300" />
        </div>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-amber-400" /></div>
        ) : (
          <div className="space-y-1 max-h-[600px] overflow-y-auto">
            {users.map(u => (
              <button key={u.id} onClick={() => openDetail(u)}
                className={`w-full text-left p-3 rounded-xl border transition-all hover:border-amber-300 ${selected?.id === u.id ? 'border-amber-400 bg-amber-50' : 'border-stone-100 bg-white hover:bg-stone-50'}`}>
                <div className="flex items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-sm font-medium text-stone-800">@{u.username}</span>
                      {u.golden_hive_verified && <span className="text-amber-500 text-xs">Gold</span>}
                      {u.is_banned && <span className="text-red-500 text-xs">Banned</span>}
                    </div>
                    <p className="text-xs text-stone-400 truncate">{u.email}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-stone-500">{u.records_count} records</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* User detail */}
      <div className="md:col-span-3">
        {!selected && (
          <div className="flex items-center justify-center h-full text-stone-400 text-sm">
            Select a user to view details
          </div>
        )}
        {selected && detailLoading && (
          <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-amber-400" /></div>
        )}
        {selected && detail && !detailLoading && (
          <UserDetail user={detail.user} stats={detail.stats} moderation={detail.moderation}
            onAction={(action, extra) => doAction(detail.user.id, action, extra)}
            actionLoading={actionLoading} />
        )}
      </div>
    </div>
  );
}

function UserDetail({ user, stats, moderation, onAction, actionLoading }) {
  const [suspendDays, setSuspendDays] = useState(7);
  const [warnNote, setWarnNote] = useState('');
  const [showWarnInput, setShowWarnInput] = useState(false);

  return (
    <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-start gap-4 mb-4 pb-4 border-b border-stone-100">
        <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 font-bold text-lg flex-shrink-0">
          {user.username?.[0]?.toUpperCase() || '?'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <h3 className="font-semibold text-stone-800">@{user.username}</h3>
            {user.golden_hive_verified && <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Gold</span>}
            {user.is_admin && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Admin</span>}
            {user.is_banned && <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">Banned</span>}
          </div>
          <p className="text-xs text-stone-400">{user.email}</p>
          {user.created_at && <p className="text-xs text-stone-400">Joined {new Date(user.created_at).toLocaleDateString()}</p>}
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          ['Records', stats?.records],
          ['Posts', stats?.posts],
          ['Listings', stats?.listings],
          ['Trades', stats?.trades],
          ['Followers', stats?.followers],
          ['Following', stats?.following],
        ].map(([label, val]) => (
          <div key={label} className="text-center p-2 bg-stone-50 rounded-xl">
            <p className="text-sm font-semibold text-stone-800">{val ?? 0}</p>
            <p className="text-xs text-stone-400">{label}</p>
          </div>
        ))}
      </div>

      {/* Moderation history */}
      {(moderation?.warnings?.length > 0 || moderation?.suspended_until || moderation?.is_banned) && (
        <div className="mb-4 p-3 bg-orange-50 rounded-xl border border-orange-200">
          <p className="text-xs font-medium text-orange-700 mb-1">Moderation History</p>
          {moderation.warnings?.map((w, i) => (
            <p key={i} className="text-xs text-orange-600">⚠ Warning: {w.note} ({new Date(w.issued_at).toLocaleDateString()})</p>
          ))}
          {moderation.suspended_until && (
            <p className="text-xs text-orange-600">🔒 Suspended until {new Date(moderation.suspended_until).toLocaleDateString()}</p>
          )}
          {moderation.is_banned && (
            <p className="text-xs text-red-600">🚫 Banned{moderation.ban_reason ? `: ${moderation.ban_reason}` : ''}</p>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="space-y-2">
        <div className="flex gap-2 flex-wrap">
          {!user.golden_hive_verified && (
            <ActionBtn icon={Star} label="Grant Gold" color="amber"
              onClick={() => onAction('grant-gold')} loading={actionLoading === 'grant-gold'} />
          )}
          {!user.discogs_oauth_verified && (
            <ActionBtn icon={Shield} label="Verify" color="blue"
              onClick={() => onAction('verify')} loading={actionLoading === 'verify'} />
          )}
          {user.is_banned ? (
            <ActionBtn icon={CheckCircle} label="Unban" color="green"
              onClick={() => onAction('unban')} loading={actionLoading === 'unban'} />
          ) : (
            <ActionBtn icon={Ban} label="Ban" color="red"
              onClick={() => onAction('ban', { note: 'Banned by admin' })} loading={actionLoading === 'ban'} />
          )}
          {moderation?.suspended_until ? (
            <ActionBtn icon={CheckCircle} label="Unsuspend" color="green"
              onClick={() => onAction('unsuspend')} loading={actionLoading === 'unsuspend'} />
          ) : null}
        </div>

        {/* Warn with note */}
        {!showWarnInput ? (
          <button onClick={() => setShowWarnInput(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-orange-50 text-orange-600 text-xs font-medium hover:bg-orange-100 transition-colors border border-orange-200">
            <AlertCircle className="w-3.5 h-3.5" /> Warn
          </button>
        ) : (
          <div className="flex gap-2">
            <input value={warnNote} onChange={e => setWarnNote(e.target.value)}
              placeholder="Warning reason..."
              className="flex-1 border border-orange-200 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-orange-300" />
            <button onClick={() => { onAction('warn', { note: warnNote }); setShowWarnInput(false); setWarnNote(''); }}
              disabled={actionLoading === 'warn'}
              className="px-3 py-1.5 rounded-xl bg-orange-500 text-white text-xs font-medium hover:bg-orange-600 transition-colors disabled:opacity-50">
              {actionLoading === 'warn' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Send'}
            </button>
            <button onClick={() => setShowWarnInput(false)} className="px-2 text-stone-400 hover:text-stone-600">
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Suspend */}
        <div className="flex gap-2 items-center">
          <select value={suspendDays} onChange={e => setSuspendDays(e.target.value)}
            className="border border-stone-200 rounded-xl px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-amber-300">
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
          <ActionBtn icon={AlertTriangle} label="Suspend" color="orange"
            onClick={() => onAction('suspend', { duration_days: suspendDays })} loading={actionLoading === 'suspend'} />
        </div>
      </div>
    </div>
  );
}

function ActionBtn({ icon: Icon, label, color, onClick, loading }) {
  const colorMap = {
    amber: 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100',
    blue: 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
    green: 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
    red: 'bg-red-50 text-red-600 border-red-200 hover:bg-red-100',
    orange: 'bg-orange-50 text-orange-600 border-orange-200 hover:bg-orange-100',
  };
  return (
    <button onClick={onClick} disabled={loading}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors disabled:opacity-50 ${colorMap[color] || colorMap.amber}`}>
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Icon className="w-3.5 h-3.5" />}
      {label}
    </button>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const TABS = [
  { key: 'queue', label: 'Queue', icon: ListChecks },
  { key: 'honey-drop', label: 'Honey Drop', icon: Droplets },
  { key: 'metrics', label: 'Metrics', icon: BarChart2 },
  { key: 'users', label: 'Users', icon: Users },
];

export default function BeekeeperPage() {
  usePageTitle('Beekeeper');
  const { token, API } = useAuth();
  const [activeTab, setActiveTab] = useState('queue');
  const [queueCount, setQueueCount] = useState(null);
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${API}/beekeeper/queue/count`, { headers })
      .then(r => setQueueCount(r.data.total))
      .catch(() => {});
  }, [API]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 pb-24" data-testid="beekeeper-page">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-2xl">🐝</span>
        <h1 className="font-heading text-2xl text-stone-800">Beekeeper</h1>
      </div>

      {/* Tab nav */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all border flex-shrink-0 ${
              activeTab === key
                ? 'bg-amber-400 text-amber-900 border-amber-500 shadow-sm'
                : 'bg-white text-stone-500 border-stone-200 hover:bg-stone-50 hover:border-stone-300'
            }`}
            data-testid={`beekeeper-tab-${key}`}>
            <Icon className="w-4 h-4" />
            {label}
            {key === 'queue' && queueCount > 0 && (
              <span className="bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[20px] text-center leading-none">
                {queueCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'queue' && <QueueTab API={API} headers={headers} />}
        {activeTab === 'honey-drop' && <HoneyDropTab API={API} headers={headers} />}
        {activeTab === 'metrics' && <MetricsTab API={API} headers={headers} />}
        {activeTab === 'users' && <UsersTab API={API} headers={headers} />}
      </div>
    </div>
  );
}
