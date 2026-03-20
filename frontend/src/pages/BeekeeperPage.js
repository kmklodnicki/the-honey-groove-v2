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
  Music2, Play, Square, RotateCcw, ImageIcon, ShieldCheck,
} from 'lucide-react';

// ─── Helpers ───────────────────────────────────────────────────────────────

const THEME_PRESETS = ['honey', 'midnight', 'forest', 'rose', 'slate', 'plum'];
const THEME_COLORS = {
  honey: '#D4A828', midnight: '#7B68EE', forest: '#74C69D',
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
  const [artistRooms, setArtistRooms] = useState([]);
  const [artistRoomsOpen, setArtistRoomsOpen] = useState(false);
  const [nicknameDialog, setNicknameDialog] = useState(null); // { slug, name, nickname }
  const [nicknameValue, setNicknameValue] = useState('');
  const [nicknameSaving, setNicknameSaving] = useState(false);

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

  const fetchArtistRooms = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/beekeeper/rooms/artist`, { headers });
      setArtistRooms(res.data || []);
    } catch { /* non-fatal */ }
  }, [API, headers]);

  const openNicknameDialog = (room) => {
    setNicknameDialog(room);
    setNicknameValue(room.nickname || '');
  };

  const saveNickname = async () => {
    if (!nicknameDialog) return;
    setNicknameSaving(true);
    try {
      await axios.put(`${API}/beekeeper/rooms/${nicknameDialog.slug}/nickname`, { nickname: nicknameValue }, { headers });
      toast.success('Nickname saved');
      setNicknameDialog(null);
      fetchArtistRooms();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to save nickname');
    } finally {
      setNicknameSaving(false);
    }
  };

  useEffect(() => { fetchQueue(); fetchArtistRooms(); }, [fetchQueue, fetchArtistRooms]);

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
            className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-all ${filter === f ? 'bg-[#D4A828] text-white border-[#D4A828]' : 'bg-white text-[#3A4D63] border-[#E5DBC8] hover:border-[#D4A828]'}`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <button onClick={fetchQueue} className="ml-auto text-[#7A8694] hover:text-[#3A4D63] transition-colors" aria-label="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-[#D4A828]" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-[#7A8694]">
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
            <h3 className="font-semibold text-lg text-[#1E2A3A] mb-1">Reject room</h3>
            <p className="text-sm text-[#3A4D63] mb-4">"{rejectDialog.name}"</p>
            <div className="space-y-2 mb-4">
              {REJECT_REASONS.map(r => (
                <label key={r.value} className="flex items-center gap-3 p-3 rounded-xl border cursor-pointer hover:bg-[#FFFBF2] transition-colors">
                  <input type="radio" name="reason" value={r.value} checked={rejectReason === r.value}
                    onChange={() => setRejectReason(r.value)} className="accent-[#D4A828]" />
                  <span className="text-sm text-[#3A4D63]">{r.label}</span>
                </label>
              ))}
            </div>
            <textarea
              value={rejectNote}
              onChange={e => setRejectNote(e.target.value)}
              placeholder="Optional note to creator..."
              className="w-full border border-[#E5DBC8] rounded-xl p-3 text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-[#D4A828] mb-4"
            />
            <div className="flex gap-3">
              <button onClick={() => setRejectDialog(null)}
                className="flex-1 py-2 rounded-xl border border-[#E5DBC8] text-[#3A4D63] text-sm font-medium hover:bg-[#FFFBF2] transition-colors">
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

      {/* Artist Rooms — nickname management */}
      <div className="mt-8">
        <button
          onClick={() => setArtistRoomsOpen(o => !o)}
          className="flex items-center gap-2 text-sm font-semibold text-[#3A4D63] hover:text-[#1E2A3A] transition-colors mb-3"
          data-testid="artist-rooms-toggle"
        >
          {artistRoomsOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          Artist Rooms ({artistRooms.length})
          <span className="text-xs font-normal text-[#7A8694]">— set display nicknames</span>
        </button>
        {artistRoomsOpen && (
          <div className="space-y-2">
            {artistRooms.length === 0 ? (
              <p className="text-sm text-[#7A8694] pl-6">No artist rooms found.</p>
            ) : artistRooms.map(room => (
              <div key={room.slug} className="bg-white rounded-xl border border-[#E5DBC8] p-4 flex items-center gap-3 shadow-sm">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
                  style={{ background: room.theme?.bgGradient || '#FFF3E0' }}>
                  {room.emoji || '🎵'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#1E2A3A]">{room.nickname || room.name}</p>
                  {room.nickname && (
                    <p className="text-xs text-[#7A8694]">system name: {room.name}</p>
                  )}
                  <p className="text-xs text-[#7A8694]">{room.member_count || 0} members · /{room.slug}</p>
                </div>
                <button
                  onClick={() => openNicknameDialog(room)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F0E6C8] text-[#D4A828] text-xs font-medium hover:bg-[#E8CA5A] transition-colors flex-shrink-0"
                  data-testid={`nickname-${room.slug}`}
                >
                  <Pencil className="w-3 h-3" /> Nickname
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Nickname dialog */}
      {nicknameDialog && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="font-semibold text-lg text-[#1E2A3A] mb-1">Set Nickname</h3>
            <p className="text-sm text-[#3A4D63] mb-4">
              System name: <strong>{nicknameDialog.name}</strong><br />
              Slug &amp; match criteria stay unchanged. Leave blank to clear the nickname.
            </p>
            <input
              value={nicknameValue}
              onChange={e => setNicknameValue(e.target.value)}
              placeholder={nicknameDialog.name}
              maxLength={80}
              className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#D4A828] mb-4"
              data-testid="nickname-input"
              autoFocus
            />
            <div className="flex gap-3">
              <button onClick={() => setNicknameDialog(null)}
                className="flex-1 py-2 rounded-xl border border-[#E5DBC8] text-[#3A4D63] text-sm font-medium hover:bg-[#FFFBF2] transition-colors">
                Cancel
              </button>
              <button onClick={saveNickname} disabled={nicknameSaving}
                className="flex-1 py-2 rounded-xl bg-[#D4A828] text-white text-sm font-medium hover:bg-[#E8CA5A] transition-colors disabled:opacity-50"
                data-testid="nickname-save-btn">
                {nicknameSaving ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit dialog */}
      {editDialog && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="font-semibold text-lg text-[#1E2A3A] mb-4">Edit & Approve</h3>
            <div className="space-y-3 mb-4">
              <div>
                <label className="block text-xs font-medium text-[#3A4D63] mb-1">Room Name</label>
                <input value={editForm.name || ''} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#D4A828]" />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#3A4D63] mb-1">Description</label>
                <textarea value={editForm.description || ''} onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))}
                  className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-[#D4A828]" />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#3A4D63] mb-1">Theme</label>
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
                className="flex-1 py-2 rounded-xl border border-[#E5DBC8] text-[#3A4D63] text-sm font-medium hover:bg-[#FFFBF2] transition-colors">
                Cancel
              </button>
              <button onClick={saveEdit} disabled={actionLoading}
                className="flex-1 py-2 rounded-xl bg-[#D4A828] text-white text-sm font-medium hover:bg-[#E8CA5A] transition-colors disabled:opacity-50">
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
  const accentColor = THEME_COLORS[room.theme_preset] || '#D4A828';
  const isGold = creator?.golden_hive_verified || creator?.golden_hive;

  return (
    <div className="bg-white rounded-2xl border border-[#E5DBC8] p-5 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl flex-shrink-0"
          style={{ background: room.theme?.bgGradient || '#FFF3E0' }}>
          {room.emoji || '🍯'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-[#1E2A3A] text-sm">{room.name}</h3>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ background: accentColor + '20', color: accentColor }}>
              {room.type}
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-[#F3EBE0] text-[#3A4D63]">
              {room.theme_preset}
            </span>
          </div>
          {room.tagline && <p className="text-xs text-[#3A4D63] mb-2 line-clamp-2">{room.tagline}</p>}
          <div className="flex items-center gap-2 text-xs text-[#7A8694]">
            <span>by @{creator?.username || 'unknown'}</span>
            {isGold && <span className="text-[#D4A828] font-medium">Gold</span>}
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
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F0E6C8] text-[#D4A828] text-xs font-medium hover:bg-[#E8CA5A] transition-colors"
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
            <span className="text-sm font-medium text-[#1E2A3A]">{report.type || 'Report'}</span>
            <span className="px-2 py-0.5 rounded-full text-xs bg-orange-100 text-orange-700">{report.target_type}</span>
          </div>
          {report.reason && <p className="text-xs text-[#3A4D63] mb-1">{report.reason}</p>}
          <div className="text-xs text-[#7A8694]">
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
        <h3 className="font-semibold text-[#3A4D63] mb-3 text-sm">Search Discogs</h3>
        <div className="flex gap-2 mb-4">
          <input value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && searchDiscogs()}
            placeholder="Artist, album title..."
            className="flex-1 border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#D4A828]" />
          <button onClick={searchDiscogs} disabled={searching}
            className="px-3 py-2 rounded-xl bg-[#D4A828] text-white hover:bg-[#E8CA5A] transition-colors disabled:opacity-50">
            {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          </button>
        </div>

        {searchResults.length > 0 && (
          <div className="space-y-2 mb-6 max-h-64 overflow-y-auto">
            {searchResults.slice(0, 10).map(r => (
              <button key={r.id || r.discogs_id} onClick={() => setSelected(r)}
                className={`w-full flex items-center gap-3 p-2 rounded-xl border text-left transition-all hover:border-[#D4A828] ${selected?.id === r.id ? 'border-[#D4A828] bg-[#F0E6C8]' : 'border-[#E5DBC8]'}`}>
                <AlbumArt src={r.cover_image || r.cover_url} alt={r.title} className="w-10 h-10 rounded-lg flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-[#1E2A3A] truncate">{r.title}</p>
                  <p className="text-xs text-[#7A8694] truncate">{r.artist || r.label?.[0]}</p>
                </div>
              </button>
            ))}
          </div>
        )}

        <h3 className="font-semibold text-[#3A4D63] mb-3 text-sm">Suggestions (want/own ratio)</h3>
        <div className="space-y-2">
          {suggestions.map(s => (
            <button key={s.discogs_id} onClick={() => setSelected(s)}
              className={`w-full flex items-center gap-3 p-2 rounded-xl border text-left transition-all hover:border-[#D4A828] ${selected?.discogs_id === s.discogs_id ? 'border-[#D4A828] bg-[#F0E6C8]' : 'border-[#E5DBC8]'}`}>
              <AlbumArt src={s.cover_url} alt={s.album} className="w-10 h-10 rounded-lg flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-[#1E2A3A] truncate">{s.album}</p>
                <p className="text-xs text-[#7A8694] truncate">{s.artist}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-xs text-[#D4A828] font-medium">{s.want_count} wants</p>
                <p className="text-xs text-[#7A8694]">{s.own_count} own</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Right: selected + scheduler */}
      <div>
        {selected && (
          <div className="bg-[#F0E6C8] border border-[#E5DBC8] rounded-2xl p-4 mb-4">
            <div className="flex gap-3 mb-3">
              <AlbumArt src={selected.cover_image || selected.cover_url} alt={selected.title || selected.album}
                className="w-16 h-16 rounded-xl flex-shrink-0" />
              <div>
                <p className="font-semibold text-[#1E2A3A] text-sm">{selected.title || selected.album}</p>
                <p className="text-xs text-[#3A4D63]">{selected.artist}</p>
                {selected.want_count && <p className="text-xs text-[#D4A828] mt-1">{selected.want_count} wants · {selected.own_count} own</p>}
                {selected.estimated_value > 0 && <p className="text-xs text-[#3A4D63]">~${selected.estimated_value}</p>}
              </div>
            </div>
            <textarea value={blurb} onChange={e => setBlurb(e.target.value)}
              placeholder="Write a 2-3 sentence editorial blurb..."
              className="w-full border border-[#E5DBC8] rounded-xl p-3 text-sm resize-none h-24 focus:outline-none focus:ring-2 focus:ring-[#D4A828] bg-white mb-3" />
            <div className="flex gap-3 items-center">
              <div className="flex-1">
                <label className="block text-xs font-medium text-[#3A4D63] mb-1">Schedule date</label>
                <input type="date" value={scheduleDate} onChange={e => setScheduleDate(e.target.value)}
                  className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#D4A828] bg-white" />
              </div>
              <button onClick={schedule} disabled={submitting}
                className="mt-5 px-4 py-2 rounded-xl bg-[#D4A828] text-white text-sm font-medium hover:bg-[#E8CA5A] transition-colors disabled:opacity-50 whitespace-nowrap flex items-center gap-2">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Droplets className="w-4 h-4" />}
                Schedule Drop
              </button>
            </div>
          </div>
        )}

        {today && (
          <div>
            <h3 className="font-semibold text-[#3A4D63] mb-3 text-sm">Today's Drop</h3>
            <div className="bg-white border border-[#E5DBC8] rounded-2xl p-4 flex gap-3">
              <AlbumArt src={today.record?.cover_url} alt={today.record?.title} className="w-14 h-14 rounded-xl flex-shrink-0" />
              <div>
                <p className="font-semibold text-[#1E2A3A] text-sm">{today.record?.title}</p>
                <p className="text-xs text-[#3A4D63]">{today.record?.artist}</p>
                {today.auto_selected && <span className="text-xs text-[#7A8694] italic">Auto-selected</span>}
                {today.blurb && <p className="text-xs text-[#3A4D63] mt-1 line-clamp-2">{today.blurb}</p>}
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

  if (loading) return <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-[#D4A828]" /></div>;
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
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-[#E5DBC8] text-[#3A4D63] text-sm hover:bg-[#FFFBF2] transition-colors">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {panels.map(panel => (
          <div key={panel.title} className="bg-white rounded-2xl border border-[#E5DBC8] p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full" style={{ background: panel.color }} />
              <h3 className="font-semibold text-[#3A4D63] text-sm">{panel.title}</h3>
            </div>
            <div className="space-y-2">
              {panel.rows.map(([label, value]) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="text-xs text-[#7A8694]">{label}</span>
                  <span className="text-xs font-semibold text-[#1E2A3A]">{value ?? '—'}</span>
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

const USER_FILTERS = [
  { value: '', label: 'All' },
  { value: 'gold', label: 'Gold' },
  { value: 'verified', label: 'Verified' },
  { value: 'banned', label: 'Banned' },
  { value: 'suspended', label: 'Suspended' },
];
const USERS_PAGE_SIZE = 50;

function UsersTab({ API, headers }) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const searchTimeout = useRef(null);

  const search = useCallback(async (q, f, newSkip = 0, append = false) => {
    if (append) setLoadingMore(true);
    else setLoading(true);
    try {
      const res = await axios.get(`${API}/beekeeper/users`, {
        params: { q, filter: f, skip: newSkip, limit: USERS_PAGE_SIZE },
        headers,
      });
      const incoming = res.data.users || [];
      setUsers(prev => append ? [...prev, ...incoming] : incoming);
      setTotal(res.data.total || 0);
      setSkip(newSkip + incoming.length);
    } catch {
      toast.error('Search failed');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [API, headers]);

  useEffect(() => {
    setSkip(0);
    search(query, filter, 0, false);
  }, [filter]); // eslint-disable-line

  useEffect(() => {
    search('', '', 0, false);
  }, [search]);

  const handleQueryChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setSkip(0);
      search(val, filter, 0, false);
    }, 350);
  };

  const handleFilterChange = (f) => {
    setFilter(f);
    setSkip(0);
    search(query, f, 0, false);
  };

  const loadMore = () => search(query, filter, skip, true);

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
        <div className="relative mb-2">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#7A8694]" />
          <input value={query} onChange={handleQueryChange}
            placeholder="Search username or email..."
            className="w-full border border-[#E5DBC8] rounded-xl pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#D4A828]" />
        </div>
        {/* Filter chips */}
        <div className="flex gap-1.5 flex-wrap mb-2">
          {USER_FILTERS.map(f => (
            <button key={f.value} onClick={() => handleFilterChange(f.value)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${filter === f.value ? 'bg-[#D4A828] text-white border-[#D4A828]' : 'bg-white text-[#3A4D63] border-[#E5DBC8] hover:border-[#D4A828]'}`}>
              {f.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-[#7A8694] mb-2">{total} user{total !== 1 ? 's' : ''} · showing {users.length}</p>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-[#D4A828]" /></div>
        ) : (
          <div className="space-y-1 max-h-[600px] overflow-y-auto">
            {users.map(u => (
              <button key={u.id} onClick={() => openDetail(u)}
                className={`w-full text-left p-3 rounded-xl border transition-all hover:border-[#D4A828] ${selected?.id === u.id ? 'border-[#D4A828] bg-[#F0E6C8]' : 'border-[#E5DBC8] bg-white hover:bg-[#FFFBF2]'}`}>
                <div className="flex items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-sm font-medium text-[#1E2A3A]">@{u.username}</span>
                      {u.golden_hive_verified && <span className="text-[#D4A828] text-xs">Gold</span>}
                      {u.is_banned && <span className="text-red-500 text-xs">Banned</span>}
                    </div>
                    <p className="text-xs text-[#7A8694] truncate">{u.email}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-[#3A4D63]">{u.records_count} records</p>
                  </div>
                </div>
              </button>
            ))}
            {users.length < total && (
              <button onClick={loadMore} disabled={loadingMore}
                className="w-full py-2 rounded-xl border border-[#E5DBC8] text-xs text-[#3A4D63] hover:bg-[#FFFBF2] hover:border-[#D4A828] transition-all disabled:opacity-50 mt-1">
                {loadingMore ? <Loader2 className="w-3.5 h-3.5 animate-spin mx-auto" /> : `Load more (${total - users.length} remaining)`}
              </button>
            )}
          </div>
        )}
      </div>

      {/* User detail */}
      <div className="md:col-span-3">
        {!selected && (
          <div className="flex items-center justify-center h-full text-[#7A8694] text-sm">
            Select a user to view details
          </div>
        )}
        {selected && detailLoading && (
          <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-[#D4A828]" /></div>
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
    <div className="bg-white rounded-2xl border border-[#E5DBC8] p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-start gap-4 mb-4 pb-4 border-b border-[#E5DBC8]">
        <div className="w-12 h-12 rounded-full bg-[#F0E6C8] flex items-center justify-center text-[#D4A828] font-bold text-lg flex-shrink-0">
          {user.username?.[0]?.toUpperCase() || '?'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <h3 className="font-semibold text-[#1E2A3A]">@{user.username}</h3>
            {user.golden_hive_verified && <span className="text-xs px-2 py-0.5 rounded-full bg-[#F0E6C8] text-[#D4A828]">Gold</span>}
            {user.is_admin && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Admin</span>}
            {user.is_banned && <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">Banned</span>}
          </div>
          <p className="text-xs text-[#7A8694]">{user.email}</p>
          {user.created_at && <p className="text-xs text-[#7A8694]">Joined {new Date(user.created_at).toLocaleDateString()}</p>}
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
          <div key={label} className="text-center p-2 bg-[#FFFBF2] rounded-xl">
            <p className="text-sm font-semibold text-[#1E2A3A]">{val ?? 0}</p>
            <p className="text-xs text-[#7A8694]">{label}</p>
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
            <button onClick={() => setShowWarnInput(false)} className="px-2 text-[#7A8694] hover:text-[#3A4D63]">
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Suspend */}
        <div className="flex gap-2 items-center">
          <select value={suspendDays} onChange={e => setSuspendDays(e.target.value)}
            className="border border-[#E5DBC8] rounded-xl px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[#D4A828]">
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
    amber: 'bg-[#F0E6C8] text-[#D4A828] border-[#E5DBC8] hover:bg-[#F0E6C8]',
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

// ─── Tab: Matching ────────────────────────────────────────────────────────────

function MatchingTab({ API, headers }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [manualDialog, setManualDialog] = useState(null); // { discogsReleaseId, title, artists }
  const [manualInput, setManualInput] = useState('');
  const [manualLoading, setManualLoading] = useState(false);
  const [clearingId, setClearingId] = useState(null);
  const [activeFilter, setActiveFilter] = useState(null); // 'matched' | 'unmatched' | 'manual_override'
  const [filteredReleases, setFilteredReleases] = useState([]);
  const [filteredTotal, setFilteredTotal] = useState(0);
  const [filterLoading, setFilterLoading] = useState(false);

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/beekeeper/spotify-matching/stats`, { headers });
      setStats(res.data);
    } catch { /* non-fatal */ }
  }, [API, headers]);

  const fetchUnmatched = useCallback(async () => {
    // kept for legacy callers (doManualMatch, doClearMatch)
    if (activeFilter === 'unmatched') {
      const res = await axios.get(`${API}/beekeeper/spotify-matching/releases`, { headers, params: { status: 'unmatched', limit: 50 } });
      setFilteredReleases(res.data.releases || []);
      setFilteredTotal(res.data.total || 0);
    }
  }, [API, headers, activeFilter]);

  const fetchFiltered = useCallback(async (status) => {
    if (!status) { setFilteredReleases([]); setFilteredTotal(0); return; }
    setFilterLoading(true);
    try {
      const res = await axios.get(`${API}/beekeeper/spotify-matching/releases`, { headers, params: { status, limit: 50 } });
      setFilteredReleases(res.data.releases || []);
      setFilteredTotal(res.data.total || 0);
    } catch { /* non-fatal */ } finally {
      setFilterLoading(false);
    }
  }, [API, headers]);

  useEffect(() => {
    setLoading(true);
    fetchStats().finally(() => setLoading(false));
  }, [fetchStats]);

  // Poll while running
  useEffect(() => {
    if (!stats?.isRunning) return;
    const id = setInterval(() => fetchStats(), 3000);
    return () => clearInterval(id);
  }, [stats?.isRunning, fetchStats]);

  const handleFilterClick = (status) => {
    const next = activeFilter === status ? null : status;
    setActiveFilter(next);
    fetchFiltered(next);
  };

  const doClearMatch = async (releaseId) => {
    setClearingId(releaseId);
    try {
      await axios.delete(`${API}/beekeeper/spotify-matching/manual/${releaseId}`, { headers });
      toast.success('Match cleared');
      fetchStats();
      fetchFiltered(activeFilter);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Clear failed');
    } finally {
      setClearingId(null);
    }
  };

  const doAction = async (action) => {
    setActionLoading(action);
    try {
      await axios.post(`${API}/beekeeper/spotify-matching/${action}`, {}, { headers });
      toast.success(action === 'stop' ? 'Stop signal sent' : 'Started');
      await fetchStats();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Action failed');
    } finally {
      setActionLoading(null);
    }
  };

  const doManualMatch = async () => {
    if (!manualDialog || !manualInput.trim()) return;
    setManualLoading(true);
    try {
      await axios.post(
        `${API}/beekeeper/spotify-matching/manual/${manualDialog.discogsReleaseId}`,
        { spotifyUrl: manualInput.trim() },
        { headers }
      );
      toast.success('Manual match saved');
      setManualDialog(null);
      setManualInput('');
      fetchStats();
      fetchFiltered(activeFilter);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Match failed');
    } finally {
      setManualLoading(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-[#D4A828]" /></div>;

  const coveragePct = stats?.coveragePct ?? 0;

  return (
    <div className="space-y-6">
      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Pending', value: stats?.pending ?? '—', color: 'text-[#D4A828]', filter: null },
          { label: 'Matched', value: stats?.matched ?? '—', color: 'text-green-600', filter: 'matched' },
          { label: 'Unmatched', value: stats?.unmatched ?? '—', color: 'text-red-500', filter: 'unmatched' },
          { label: 'Manual', value: stats?.manual_override ?? '—', color: 'text-blue-600', filter: 'manual_override' },
        ].map(({ label, value, color, filter }) => (
          <div
            key={label}
            onClick={() => filter && handleFilterClick(filter)}
            className={`bg-white rounded-2xl border p-4 shadow-sm transition-all ${filter ? 'cursor-pointer hover:shadow-md' : ''} ${activeFilter === filter && filter ? 'border-[#D4A828] ring-1 ring-[#D4A828]/30' : 'border-[#E5DBC8]'}`}
          >
            <p className="text-xs text-[#7A8694] mb-1">{label}</p>
            <p className={`text-2xl font-semibold ${color}`}>{value}</p>
            {filter && <p className="text-xs text-[#7A8694] mt-1">{activeFilter === filter ? 'click to hide ↑' : 'click to view →'}</p>}
          </div>
        ))}
      </div>

      {/* Coverage progress */}
      <div className="bg-white rounded-2xl border border-[#E5DBC8] p-5 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-medium text-[#3A4D63]">Album art coverage</p>
          <p className="text-sm font-semibold text-[#D4A828]">{coveragePct}%</p>
        </div>
        <div className="h-2.5 bg-[#F3EBE0] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#D4A828] rounded-full transition-all duration-500"
            style={{ width: `${Math.min(coveragePct, 100)}%` }}
          />
        </div>
        <p className="text-xs text-[#7A8694] mt-2">
          {stats?.matched ?? 0} of {stats?.total ?? 0} releases have Spotify album art
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-2">
        {!stats?.isRunning ? (
          <>
            <button
              onClick={() => doAction('start')}
              disabled={!!actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-green-500 text-white text-sm font-medium hover:bg-green-600 transition-colors disabled:opacity-50"
              data-testid="start-matching-btn"
            >
              {actionLoading === 'start' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Start Matching
            </button>
            {(stats?.unmatched ?? 0) > 0 && (
              <button
                onClick={() => doAction('retry')}
                disabled={!!actionLoading}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#F0E6C8] text-[#D4A828] text-sm font-medium hover:bg-[#E8CA5A] transition-colors disabled:opacity-50"
                data-testid="retry-matching-btn"
              >
                {actionLoading === 'retry' ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
                Retry Unmatched ({stats.unmatched})
              </button>
            )}
          </>
        ) : (
          <button
            onClick={() => doAction('stop')}
            disabled={actionLoading === 'stop'}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-100 text-red-600 text-sm font-medium hover:bg-red-200 transition-colors disabled:opacity-50"
            data-testid="stop-matching-btn"
          >
            {actionLoading === 'stop' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />}
            Stop
          </button>
        )}
        <button
          onClick={() => { fetchStats(); fetchUnmatched(); }}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[#F3EBE0] text-[#3A4D63] text-sm font-medium hover:bg-[#F3EBE0] transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Running indicator */}
      {stats?.isRunning && (
        <div className="flex items-center gap-2 text-sm text-[#D4A828] bg-[#F0E6C8] rounded-xl px-4 py-2 border border-[#E5DBC8]">
          <Loader2 className="w-4 h-4 animate-spin" />
          Matching in progress…
        </div>
      )}

      {/* Last run result */}
      {stats?.lastRunResult && !stats?.isRunning && (
        <div className="bg-[#FFFBF2] rounded-xl border border-[#E5DBC8] px-4 py-3 text-sm text-[#3A4D63]">
          Last run: {stats.lastRunResult.processed} processed · {stats.lastRunResult.matched} matched · {stats.lastRunResult.unmatched} unmatched
        </div>
      )}

      {/* Filtered releases list */}
      {activeFilter && (
        <div className="bg-white rounded-2xl border border-[#E5DBC8] shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-[#E5DBC8] flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#3A4D63] capitalize">
              {activeFilter === 'manual_override' ? 'Manual overrides' : `${activeFilter} releases`}
            </h3>
            <span className="text-xs text-[#7A8694]">{filteredTotal} total</span>
          </div>
          {filterLoading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-[#D4A828]" /></div>
          ) : filteredReleases.length === 0 ? (
            <p className="text-sm text-[#7A8694] text-center py-8">No releases</p>
          ) : (
            <div className="divide-y divide-[#E5DBC8]">
              {filteredReleases.map(rel => (
                <div key={rel.discogsReleaseId} className="flex items-center gap-3 px-5 py-3">
                  {rel.spotifyImageUrl && (
                    <img src={rel.spotifyImageUrl} alt="" className="w-9 h-9 rounded-md object-cover flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[#1E2A3A] truncate">{rel.title || 'Unknown'}</p>
                    <p className="text-xs text-[#7A8694] truncate">
                      {(rel.artists || []).join(', ') || '—'} · {rel.year || '—'} · ID {rel.discogsReleaseId}
                    </p>
                    {rel.barcode?.length > 0 && (
                      <p className="text-xs text-[#7A8694] truncate">UPC: {rel.barcode[0]}</p>
                    )}
                  </div>
                  {activeFilter === 'unmatched' && (
                    <button
                      onClick={() => { setManualDialog(rel); setManualInput(''); }}
                      className="flex-shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#F0E6C8] text-[#D4A828] text-xs font-medium hover:bg-[#F0E6C8] transition-colors"
                    >
                      <Music2 className="w-3.5 h-3.5" />
                      Match
                    </button>
                  )}
                  {activeFilter === 'manual_override' && (
                    <button
                      onClick={() => doClearMatch(rel.discogsReleaseId)}
                      disabled={clearingId === rel.discogsReleaseId}
                      className="flex-shrink-0 px-3 py-1.5 rounded-xl bg-red-50 text-red-600 text-xs font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
                    >
                      {clearingId === rel.discogsReleaseId ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Clear'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Manual match dialog (simple inline) */}
      {manualDialog && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/30 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) setManualDialog(null); }}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h3 className="font-semibold text-[#1E2A3A] mb-1">Manual Spotify Match</h3>
            <p className="text-xs text-[#3A4D63] mb-4 line-clamp-1">
              {manualDialog.title} — {(manualDialog.artists || []).join(', ')}
            </p>
            <input
              value={manualInput}
              onChange={e => setManualInput(e.target.value)}
              placeholder="Paste Spotify album URL or album ID…"
              className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-[#D4A828]"
              autoFocus
            />
            <div className="flex gap-2">
              <button onClick={() => setManualDialog(null)}
                className="flex-1 px-4 py-2 rounded-xl border border-[#E5DBC8] text-sm text-[#3A4D63] hover:bg-[#FFFBF2] transition-colors">
                Cancel
              </button>
              <button onClick={doManualMatch} disabled={manualLoading || !manualInput.trim()}
                className="flex-1 px-4 py-2 rounded-xl bg-[#D4A828] text-white text-sm font-medium hover:bg-[#D4A828] transition-colors disabled:opacity-50">
                {manualLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Save Match'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Tab: Covers ──────────────────────────────────────────────────────────────

function CoversTab({ API, headers }) {
  const [submissions, setSubmissions] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);
  const [statusFilter, setStatusFilter] = useState('pending');

  const fetchSubmissions = useCallback(async (status) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/beekeeper/community-covers`, { headers, params: { status, limit: 50 } });
      setSubmissions(res.data.submissions || []);
      setTotal(res.data.total || 0);
    } catch { /* non-fatal */ } finally {
      setLoading(false);
    }
  }, [API, headers]);

  useEffect(() => { fetchSubmissions(statusFilter); }, [fetchSubmissions, statusFilter]);

  const doAction = async (id, action) => {
    setActionId(id + action);
    try {
      await axios.post(`${API}/beekeeper/community-covers/${id}/${action}`, {}, { headers });
      toast.success(action === 'approve' ? 'Cover approved' : 'Cover rejected');
      fetchSubmissions(statusFilter);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Action failed');
    } finally {
      setActionId(null);
    }
  };

  return (
    <div className="space-y-5">
      {/* Filter tabs */}
      <div className="flex gap-2">
        {['pending', 'approved', 'rejected'].map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors capitalize ${statusFilter === s ? 'bg-[#D4A828] text-white' : 'bg-[#F3EBE0] text-[#3A4D63] hover:bg-[#F3EBE0]'}`}
          >
            {s}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-[#D4A828]" /></div>
      ) : submissions.length === 0 ? (
        <div className="text-center py-16 text-[#7A8694]">
          <ImageIcon className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No {statusFilter} submissions</p>
        </div>
      ) : (
        <>
          <p className="text-xs text-[#7A8694]">{total} submission{total !== 1 ? 's' : ''}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {submissions.map(sub => (
              <div key={sub.id} className="bg-white rounded-2xl border border-[#E5DBC8] shadow-sm overflow-hidden">
                <img src={sub.imageUrl} alt="" className="w-full aspect-square object-cover" />
                <div className="p-4">
                  <p className="text-sm font-semibold text-[#1E2A3A] truncate">{sub.title || 'Unknown'}</p>
                  <p className="text-xs text-[#7A8694] truncate mb-1">{(sub.artists || []).join(', ') || '—'}</p>
                  <p className="text-xs text-[#7A8694]">by @{sub.submittedByUsername} · ID {sub.discogsReleaseId}</p>
                  <div className="flex gap-2 mt-3">
                    {statusFilter !== 'approved' && (
                      <button
                        onClick={() => doAction(sub.id, 'approve')}
                        disabled={!!actionId}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-green-50 text-green-700 text-xs font-medium hover:bg-green-100 transition-colors disabled:opacity-50"
                      >
                        {actionId === sub.id + 'approve' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                        Approve
                      </button>
                    )}
                    {statusFilter !== 'rejected' && (
                      <button
                        onClick={() => doAction(sub.id, 'reject')}
                        disabled={!!actionId}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-red-50 text-red-600 text-xs font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
                      >
                        {actionId === sub.id + 'reject' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
                        Reject
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Migration Tab ────────────────────────────────────────────────────────────

function MigrationTab({ API, headers }) {
  const [compliance, setCompliance] = useState(null);
  const [migration, setMigration] = useState(null);
  const [loadingCompliance, setLoadingCompliance] = useState(true);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const pollRef = useRef(null);

  const fetchCompliance = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/beekeeper/compliance/discogs`, { headers });
      setCompliance(res.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to load compliance data');
    } finally {
      setLoadingCompliance(false);
    }
  }, [API, headers]);

  const fetchMigrationStatus = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/beekeeper/migration/discogs/status`, { headers });
      setMigration(res.data);
      // Update compliance counts from migration status
      if (res.data.compliance) setCompliance(c => ({ ...c, ...res.data.compliance }));
      return res.data;
    } catch (e) {
      return null;
    }
  }, [API, headers]);

  useEffect(() => {
    fetchCompliance();
    fetchMigrationStatus();
  }, [fetchCompliance, fetchMigrationStatus]);

  // Poll while migration is running
  useEffect(() => {
    if (migration?.running) {
      pollRef.current = setInterval(async () => {
        const data = await fetchMigrationStatus();
        if (data && !data.running) {
          clearInterval(pollRef.current);
          fetchCompliance();
          toast.success('Migration complete');
        }
      }, 2000);
    } else {
      clearInterval(pollRef.current);
    }
    return () => clearInterval(pollRef.current);
  }, [migration?.running, fetchMigrationStatus, fetchCompliance]);

  const handleStart = async () => {
    setStarting(true);
    try {
      const res = await axios.post(`${API}/beekeeper/migration/discogs/start`, {}, { headers });
      setMigration(res.data);
      toast.success('Migration started');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to start migration');
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    setStopping(true);
    try {
      await axios.post(`${API}/beekeeper/migration/discogs/stop`, {}, { headers });
      toast.success('Stop signal sent');
      await fetchMigrationStatus();
    } catch (e) {
      toast.error('Failed to send stop signal');
    } finally {
      setStopping(false);
    }
  };

  const [cleaning, setCleaning] = useState(false);
  const handleCleanup = async () => {
    setCleaning(true);
    try {
      const res = await axios.post(`${API}/beekeeper/compliance/cleanup`, {}, { headers });
      toast.success(`Cleanup done — ${res.data.tokens_deleted} tokens deleted, ${res.data.usernames_cleared} usernames cleared`);
      await fetchCompliance();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Cleanup failed');
    } finally {
      setCleaning(false);
    }
  };

  const allClear = compliance?.all_clear;
  const isRunning = migration?.running;

  return (
    <div className="space-y-6" data-testid="migration-tab">

      {/* Compliance Audit */}
      <div className="bg-white rounded-2xl border border-[#E5DBC8] shadow-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-[#D4A828]" />
            <h2 className="font-semibold text-[#1E2A3A]">Discogs TOS Compliance Audit</h2>
          </div>
          <button onClick={fetchCompliance}
            className="text-xs text-[#7A8694] hover:text-[#3A4D63] flex items-center gap-1">
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>

        {loadingCompliance ? (
          <div className="flex items-center gap-2 text-[#7A8694] py-4">
            <Loader2 className="w-4 h-4 animate-spin" /> Checking...
          </div>
        ) : compliance ? (
          <>
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg mb-4 text-sm font-medium ${
              allClear ? 'bg-green-50 text-green-700' : 'bg-[#F0E6C8] text-[#D4A828]'
            }`}>
              {allClear
                ? <><CheckCircle className="w-4 h-4" /> All clear — no Restricted Data found</>
                : <><AlertTriangle className="w-4 h-4" /> Restricted Data detected — run migration</>}
            </div>

            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Records with Discogs image URLs', value: compliance.records_with_discogs_image_urls, bad: true },
                { label: 'Releases with images field', value: compliance.releases_with_images_field, bad: true },
                { label: 'Stored OAuth tokens', value: compliance.stored_oauth_tokens, bad: true },
                { label: 'Users with discogs_username', value: compliance.users_with_discogs_username, bad: false },
              ].map(({ label, value, bad }) => (
                <div key={label} className="bg-[#FFFBF2] rounded-xl p-3">
                  <p className="text-xs text-[#3A4D63] mb-1">{label}</p>
                  <p className={`text-xl font-semibold ${bad && value > 0 ? 'text-red-500' : value === 0 ? 'text-green-600' : 'text-[#3A4D63]'}`}>
                    {value ?? '—'}
                  </p>
                </div>
              ))}
            </div>
            {compliance.checked_at && (
              <p className="text-[10px] text-[#7A8694] mt-3">
                Checked {new Date(compliance.checked_at).toLocaleString()}
              </p>
            )}
          </>
        ) : null}
      </div>

      {/* Migration Control */}
      <div className="bg-white rounded-2xl border border-[#E5DBC8] shadow-sm p-5">
        <div className="flex items-center gap-2 mb-1">
          <ShieldCheck className="w-5 h-5 text-[#D4A828]" />
          <h2 className="font-semibold text-[#1E2A3A]">Beta User Migration</h2>
        </div>
        <p className="text-xs text-[#3A4D63] mb-4">
          Backfills <code className="bg-[#F3EBE0] px-1 rounded">releaseId</code> on all Discogs-imported records,
          clears stored OAuth tokens, removes Discogs CDN image URLs, and triggers Spotify matching for unlinked releases.
        </p>

        <div className="flex gap-2 mb-5 flex-wrap">
          <button onClick={handleStart} disabled={isRunning || starting}
            className="flex items-center gap-2 px-4 py-2 bg-[#D4A828] hover:bg-[#E8CA5A] text-white font-medium text-sm rounded-xl transition-all disabled:opacity-50"
            data-testid="migration-start-btn">
            {starting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isRunning ? 'Running…' : 'Start Migration'}
          </button>
          <button onClick={handleCleanup} disabled={cleaning || isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-[#1E2A3A] hover:bg-[#2A3B50] text-white font-medium text-sm rounded-xl transition-all disabled:opacity-50"
            data-testid="compliance-cleanup-btn">
            {cleaning ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
            Run Cleanup
          </button>
          {isRunning && (
            <button onClick={handleStop} disabled={stopping}
              className="flex items-center gap-2 px-4 py-2 bg-[#F3EBE0] hover:bg-[#F3EBE0] text-[#3A4D63] font-medium text-sm rounded-xl transition-all disabled:opacity-50"
              data-testid="migration-stop-btn">
              {stopping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />}
              Stop
            </button>
          )}
        </div>

        {migration && (
          <div className="space-y-4">
            {/* Progress bar */}
            {isRunning && migration.processed > 0 && (
              <div>
                <div className="flex justify-between text-xs text-[#3A4D63] mb-1">
                  <span>Processing records…</span>
                  <span>{migration.processed} processed · {migration.linked} linked</span>
                </div>
                <div className="h-2 bg-[#F3EBE0] rounded-full overflow-hidden">
                  <div className="h-full bg-[#D4A828] rounded-full transition-all"
                    style={{ width: migration.linked > 0 ? `${Math.min((migration.linked / Math.max(migration.processed, 1)) * 100, 100)}%` : '0%' }} />
                </div>
              </div>
            )}

            {/* Stats grid */}
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'Processed', value: migration.processed },
                { label: 'Linked', value: migration.linked },
                { label: 'Spotify triggered', value: migration.spotify_triggered },
                { label: 'Tokens deleted', value: migration.tokens_deleted },
                { label: 'Usernames cleared', value: migration.usernames_cleared },
                { label: 'Images cleared', value: migration.images_cleared },
              ].map(({ label, value }) => (
                <div key={label} className="bg-[#FFFBF2] rounded-xl p-3 text-center">
                  <p className="text-lg font-semibold text-[#1E2A3A]">{value ?? 0}</p>
                  <p className="text-[10px] text-[#3A4D63]">{label}</p>
                </div>
              ))}
            </div>

            {/* Timestamps */}
            <div className="flex gap-4 text-[10px] text-[#7A8694]">
              {migration.started_at && <span>Started: {new Date(migration.started_at).toLocaleString()}</span>}
              {migration.completed_at && <span>Completed: {new Date(migration.completed_at).toLocaleString()}</span>}
            </div>

            {/* Error log */}
            {migration.errors?.length > 0 && (
              <div className="border border-red-100 rounded-xl p-3">
                <p className="text-xs font-medium text-red-600 mb-2 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" /> {migration.errors.length} error{migration.errors.length !== 1 ? 's' : ''}
                </p>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {migration.errors.map((e, i) => (
                    <p key={i} className="text-[10px] text-red-500 font-mono">{e}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}


// ─── Tab: Testimonials ────────────────────────────────────────────────────────

const GOLD = '#D4A828';
const GOLD_LIGHT = '#E8CA5A';
const NAVY = '#1E2A3A';
const CREAM = '#F0E6C8';

function TestimonialPreview({ t }) {
  return (
    <div style={{
      background: NAVY, borderRadius: 16, padding: '28px 32px',
      border: '1px solid rgba(255,255,255,0.1)', maxWidth: 480,
    }}>
      <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 40, color: `${GOLD}33`, lineHeight: 1, marginBottom: 4 }}>"</div>
      <p style={{ color: '#fff', fontFamily: "'Playfair Display', serif", fontSize: 17, fontStyle: 'italic', lineHeight: 1.7, marginBottom: 20 }}>
        {t.quote || <em style={{ opacity: 0.4 }}>quote will appear here…</em>}
      </p>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 700, fontSize: 15, color: NAVY, fontFamily: "'Playfair Display', serif",
        }}>
          {(t.avatarLetter || '?')[0]?.toUpperCase()}
        </div>
        <div>
          <p style={{ color: '#fff', fontSize: 12, fontWeight: 700, margin: 0 }}>{t.username || '@username'}</p>
          <p style={{ color: CREAM, fontSize: 10, margin: 0, opacity: 0.7 }}>
            {t.label || 'beta collector'}{t.recordCount ? ` · ${t.recordCount} records` : ''}
          </p>
        </div>
      </div>
    </div>
  );
}

const BLANK_FORM = { quote: '', username: '', label: 'beta collector', avatarLetter: '', recordCount: '', isActive: true, linkedUserId: '', linkedUsername: '' };

function TestimonialsTab({ API, headers }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null | 'new' | testimonial object
  const [form, setForm] = useState(BLANK_FORM);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [hiveOpen, setHiveOpen] = useState(false);
  const [hivePosts, setHivePosts] = useState([]);
  const [hiveLoading, setHiveLoading] = useState(false);
  const [dragOver, setDragOver] = useState(null);
  const dragItem = useRef(null);
  // User autocomplete for linkedUserId
  const [userQuery, setUserQuery] = useState('');
  const [userResults, setUserResults] = useState([]);
  const [userSearching, setUserSearching] = useState(false);
  const userSearchTimer = useRef(null);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/beekeeper/testimonials`, { headers });
      setItems(res.data || []);
    } catch { toast.error('Failed to load testimonials'); }
    finally { setLoading(false); }
  }, [API, headers]);

  useEffect(() => { fetch_(); }, [fetch_]);

  const activeCount = items.filter(t => t.isActive).length;

  // ── Editor ──
  const openNew = () => { setForm(BLANK_FORM); setEditing('new'); };
  const openEdit = (t) => {
    setForm({ quote: t.quote, username: t.username, label: t.label, avatarLetter: t.avatarLetter, recordCount: t.recordCount, isActive: t.isActive, linkedUserId: t.linkedUserId || '', linkedUsername: t.linkedUsername || '' });
    setUserQuery(t.linkedUsername || '');
    setUserResults([]);
    setEditing(t);
  };
  const closeEditor = () => { setEditing(null); setForm(BLANK_FORM); setUserQuery(''); setUserResults([]); };

  const handleUserQueryChange = (q) => {
    setUserQuery(q);
    setUserResults([]);
    clearTimeout(userSearchTimer.current);
    if (!q.trim()) return;
    userSearchTimer.current = setTimeout(async () => {
      setUserSearching(true);
      try {
        const res = await axios.get(`${API}/beekeeper/users`, { headers, params: { q, limit: 6 } });
        setUserResults(res.data.users || []);
      } catch { /* silent */ }
      finally { setUserSearching(false); }
    }, 300);
  };

  const selectUser = (u) => {
    setForm(f => ({
      ...f,
      linkedUserId: u.id,
      linkedUsername: u.username,
      username: f.username || `@${u.username}`,
      avatarLetter: f.avatarLetter || u.username[0].toUpperCase(),
      recordCount: f.recordCount || u.records_count || '',
    }));
    setUserQuery(u.username);
    setUserResults([]);
  };

  const handleSave = async () => {
    if (!form.quote.trim() || !form.username.trim() || !form.avatarLetter.trim()) {
      toast.error('Quote, username, and avatar letter are required'); return;
    }
    setSaving(true);
    try {
      const { linkedUsername, ...rest } = form;
      const body = { ...rest, recordCount: Number(form.recordCount) || 0, linkedUserId: form.linkedUserId || null, linkedUsername: linkedUsername || null };
      if (editing === 'new') {
        await axios.post(`${API}/beekeeper/testimonials`, body, { headers });
        toast.success('Testimonial added');
      } else {
        await axios.put(`${API}/beekeeper/testimonials/${editing.id}`, body, { headers });
        toast.success('Testimonial updated');
      }
      closeEditor();
      fetch_();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Save failed'); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    setDeleting(id);
    try {
      await axios.delete(`${API}/beekeeper/testimonials/${id}`, { headers });
      toast.success('Deleted');
      fetch_();
    } catch { toast.error('Delete failed'); }
    finally { setDeleting(null); }
  };

  const handleToggleActive = async (t) => {
    try {
      await axios.put(`${API}/beekeeper/testimonials/${t.id}`, { isActive: !t.isActive }, { headers });
      setItems(prev => prev.map(x => x.id === t.id ? { ...x, isActive: !x.isActive } : x));
    } catch { toast.error('Update failed'); }
  };

  // ── Drag-to-reorder ──
  const handleDragStart = (i) => { dragItem.current = i; };
  const handleDragEnter = (i) => { setDragOver(i); };
  const handleDrop = async () => {
    if (dragItem.current === null || dragItem.current === dragOver) { setDragOver(null); return; }
    const reordered = [...items];
    const [moved] = reordered.splice(dragItem.current, 1);
    reordered.splice(dragOver, 0, moved);
    setItems(reordered);
    setDragOver(null);
    dragItem.current = null;
    try {
      await axios.put(`${API}/beekeeper/testimonials-reorder`, { orderedIds: reordered.map(t => t.id) }, { headers });
    } catch { toast.error('Reorder failed'); fetch_(); }
  };

  // ── Pull from Hive ──
  const openHive = async () => {
    setHiveOpen(true);
    setHiveLoading(true);
    try {
      const res = await axios.get(`${API}/beekeeper/testimonials/hive-posts`, { headers });
      setHivePosts(res.data || []);
    } catch { toast.error('Could not load Hive posts'); }
    finally { setHiveLoading(false); }
  };
  const pullPost = (post) => {
    setForm({ quote: post.text, username: post.username, label: 'beta collector', avatarLetter: post.avatarLetter, recordCount: post.recordCount, isActive: true, linkedUserId: post.linkedUserId || '' });
    setEditing('new');
    setHiveOpen(false);
  };

  // ── Seed ──
  const handleSeed = async () => {
    try {
      const res = await axios.post(`${API}/beekeeper/testimonials/seed`, {}, { headers });
      toast.success(res.data.message || `Seeded ${res.data.seeded} testimonials`);
      fetch_();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Seed failed'); }
  };

  if (editing) {
    return (
      <div className="max-w-2xl">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={closeEditor} className="text-sm text-[#3A4D63] hover:text-[#1E2A3A]">← Back</button>
          <h2 className="font-heading text-xl text-[#1E2A3A]">{editing === 'new' ? 'New Testimonial' : 'Edit Testimonial'}</h2>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Form */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#3A4D63] uppercase tracking-wide mb-1">Quote <span className="text-red-400">*</span></label>
              <textarea
                value={form.quote}
                onChange={e => setForm(f => ({ ...f, quote: e.target.value }))}
                maxLength={300}
                rows={5}
                className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#D4A828] resize-none"
                placeholder="Testimonial text…"
              />
              <p className="text-xs text-right mt-0.5" style={{ color: form.quote.length > 270 ? '#E53E3E' : '#9CA3AF' }}>{form.quote.length}/300</p>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#3A4D63] uppercase tracking-wide mb-1">Username <span className="text-red-400">*</span></label>
              <input value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#D4A828]" placeholder="@username" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[#3A4D63] uppercase tracking-wide mb-1">Label</label>
                <input value={form.label} onChange={e => setForm(f => ({ ...f, label: e.target.value }))} className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#D4A828]" placeholder="beta collector" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#3A4D63] uppercase tracking-wide mb-1">Avatar Letter <span className="text-red-400">*</span></label>
                <input value={form.avatarLetter} onChange={e => setForm(f => ({ ...f, avatarLetter: e.target.value.slice(-1).toUpperCase() }))} className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#D4A828] text-center font-bold text-lg" placeholder="J" maxLength={1} />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#3A4D63] uppercase tracking-wide mb-1">Record Count</label>
              <input type="number" value={form.recordCount} onChange={e => setForm(f => ({ ...f, recordCount: e.target.value }))} className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#D4A828]" placeholder="187" />
            </div>
            <div className="relative">
              <label className="block text-xs font-semibold text-[#3A4D63] uppercase tracking-wide mb-1">Linked User <span className="text-[#9CA3AF] font-normal">(optional)</span></label>
              <div className="relative">
                <input
                  value={userQuery}
                  onChange={e => handleUserQueryChange(e.target.value)}
                  onFocus={() => { if (userQuery) handleUserQueryChange(userQuery); }}
                  className="w-full border border-[#E5DBC8] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#D4A828]"
                  placeholder="Search by username…"
                  autoComplete="off"
                />
                {userSearching && <span className="absolute right-3 top-2.5 text-xs text-[#9CA3AF]">…</span>}
                {form.linkedUserId && !userResults.length && (
                  <div className="mt-1 flex items-center gap-2">
                    <span className="text-xs text-[#D4A828] font-medium">✓ {userQuery}</span>
                    <button type="button" onClick={() => { setForm(f => ({ ...f, linkedUserId: '', linkedUsername: '' })); setUserQuery(''); }} className="text-xs text-[#9CA3AF] hover:text-red-400">clear</button>
                  </div>
                )}
              </div>
              {userResults.length > 0 && (
                <div className="absolute z-20 w-full bg-white border border-[#E5DBC8] rounded-xl shadow-lg mt-1 overflow-hidden">
                  {userResults.map(u => (
                    <button
                      key={u.id}
                      type="button"
                      onMouseDown={() => selectUser(u)}
                      className="w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-[#FFFBF2] text-left border-b border-[#F5EFE6] last:border-0"
                    >
                      <span className="font-medium text-[#1E2A3A]">@{u.username}</span>
                      <span className="text-xs text-[#9CA3AF]">{u.records_count ?? 0} records</span>
                    </button>
                  ))}
                </div>
              )}
              <p className="text-xs text-[#9CA3AF] mt-1">If linked, record count auto-updates nightly from their Vault.</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setForm(f => ({ ...f, isActive: !f.isActive }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${form.isActive ? 'bg-[#D4A828]' : 'bg-gray-200'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${form.isActive ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
              <span className="text-sm text-[#3A4D63]">{form.isActive ? 'Active — visible on landing page' : 'Inactive — hidden from landing page'}</span>
            </div>
            <div className="flex gap-3 pt-2">
              <button onClick={handleSave} disabled={saving} className="flex-1 bg-[#D4A828] hover:bg-[#E8CA5A] text-white font-semibold rounded-xl py-2.5 text-sm transition-colors flex items-center justify-center gap-2">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                {editing === 'new' ? 'Add Testimonial' : 'Save Changes'}
              </button>
              <button onClick={closeEditor} className="px-5 bg-white border border-[#E5DBC8] text-[#3A4D63] rounded-xl py-2.5 text-sm hover:bg-gray-50">Cancel</button>
            </div>
          </div>

          {/* Live preview */}
          <div>
            <p className="text-xs font-semibold text-[#3A4D63] uppercase tracking-wide mb-3">Live Preview</p>
            <TestimonialPreview t={form} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header row */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <h2 className="font-heading text-xl text-[#1E2A3A]">Testimonials</h2>
          <span className="text-sm px-2.5 py-0.5 rounded-full bg-[#D4A828]/10 text-[#D4A828] font-semibold">{activeCount} active</span>
          {activeCount < 3 && (
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> fewer than 3 active
            </span>
          )}
        </div>
        <div className="flex gap-2">
          {items.length === 0 && (
            <button onClick={handleSeed} className="text-xs border border-[#E5DBC8] text-[#3A4D63] rounded-xl px-3 py-2 hover:bg-[#FFFBF2]">Seed defaults</button>
          )}
          <button onClick={openHive} className="flex items-center gap-1.5 border border-[#E5DBC8] text-[#3A4D63] rounded-xl px-3 py-2 text-sm hover:bg-[#FFFBF2]">
            🍯 Pull from Hive
          </button>
          <button onClick={openNew} className="flex items-center gap-1.5 bg-[#D4A828] text-white rounded-xl px-4 py-2 text-sm font-semibold hover:bg-[#E8CA5A]">
            + Add Testimonial
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-[#D4A828]" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-[#3A4D63]/60 text-sm">No testimonials yet. Seed the defaults or add one manually.</div>
      ) : (
        <div className="bg-white rounded-2xl border border-[#E5DBC8] overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-[40px_1fr_140px_80px_80px_100px] gap-3 px-4 py-2.5 bg-[#FFFBF2] border-b border-[#E5DBC8] text-xs font-semibold text-[#3A4D63] uppercase tracking-wide">
            <span>#</span><span>Quote</span><span>User</span><span>Records</span><span>Active</span><span>Actions</span>
          </div>
          {items.map((t, i) => (
            <div
              key={t.id}
              draggable
              onDragStart={() => handleDragStart(i)}
              onDragEnter={() => handleDragEnter(i)}
              onDragOver={e => e.preventDefault()}
              onDrop={handleDrop}
              onDragEnd={() => setDragOver(null)}
              className={`grid grid-cols-[40px_1fr_140px_80px_80px_100px] gap-3 px-4 py-3 border-b border-[#E5DBC8] last:border-0 items-center text-sm cursor-grab transition-colors ${dragOver === i ? 'bg-[#D4A828]/5' : 'hover:bg-[#FFFBF2]'} ${!t.isActive ? 'opacity-50' : ''}`}
            >
              <span className="text-[#9CA3AF] font-mono text-xs select-none">{i + 1}</span>
              <p className="truncate text-[#1E2A3A]" title={t.quote}>"{t.quote.slice(0, 70)}{t.quote.length > 70 ? '…' : ''}"</p>
              <div>
                <p className="font-semibold text-[#1E2A3A] text-xs">{t.username}</p>
                <p className="text-[#9CA3AF] text-xs">{t.label}</p>
              </div>
              <span className="text-[#3A4D63]">{t.recordCount}</span>
              <button
                onClick={() => handleToggleActive(t)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${t.isActive ? 'bg-[#D4A828]' : 'bg-gray-200'}`}
                title={t.isActive ? 'Click to deactivate' : 'Click to activate'}
              >
                <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${t.isActive ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </button>
              <div className="flex items-center gap-2">
                <button onClick={() => openEdit(t)} className="p-1.5 rounded-lg hover:bg-[#D4A828]/10 text-[#D4A828]" title="Edit"><Pencil className="w-3.5 h-3.5" /></button>
                <button onClick={() => handleDelete(t.id)} disabled={deleting === t.id} className="p-1.5 rounded-lg hover:bg-red-50 text-red-400" title="Delete">
                  {deleting === t.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-[#9CA3AF] mt-3">Drag rows to reorder. Changes save automatically. Inactive testimonials are hidden from the landing page.</p>

      {/* Pull from Hive modal */}
      {hiveOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40" onClick={() => setHiveOpen(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4 shadow-2xl max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-heading text-lg text-[#1E2A3A]">Pull from Hive</h3>
              <button onClick={() => setHiveOpen(false)} className="text-[#9CA3AF] hover:text-[#1E2A3A]"><X className="w-5 h-5" /></button>
            </div>
            <p className="text-sm text-[#3A4D63] mb-4">Select a high-engagement post to convert into a testimonial.</p>
            <div className="overflow-y-auto flex-1 space-y-3">
              {hiveLoading ? (
                <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-[#D4A828]" /></div>
              ) : hivePosts.length === 0 ? (
                <p className="text-center text-[#9CA3AF] text-sm py-8">No posts found.</p>
              ) : hivePosts.map(post => (
                <div key={post.postId} className="border border-[#E5DBC8] rounded-xl p-4 hover:border-[#D4A828] cursor-pointer transition-colors" onClick={() => pullPost(post)}>
                  <p className="text-sm text-[#1E2A3A] mb-2 line-clamp-3">"{post.text}"</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#3A4D63]">{post.username}</span>
                    <span className="text-xs text-[#9CA3AF]">❤️ {post.likesCount} · {post.recordCount} records</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// ─── Main Page ────────────────────────────────────────────────────────────────

const TABS = [
  { key: 'queue', label: 'Queue', icon: ListChecks },
  { key: 'honey-drop', label: 'Honey Drop', icon: Droplets },
  { key: 'metrics', label: 'Metrics', icon: BarChart2 },
  { key: 'users', label: 'Users', icon: Users },
  { key: 'matching', label: 'Matching', icon: Music2 },
  { key: 'covers', label: 'Covers', icon: ImageIcon },
  { key: 'migration', label: 'Migration', icon: ShieldCheck },
  { key: 'testimonials', label: 'Testimonials', icon: Star },
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
        <h1 className="font-heading text-2xl text-[#1E2A3A]">Beekeeper</h1>
      </div>

      {/* Tab nav */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all border flex-shrink-0 ${
              activeTab === key
                ? 'bg-[#D4A828] text-white border-[#D4A828] shadow-[0_2px_4px_#D4A82828]'
                : 'bg-white text-[#3A4D63] border-[#E5DBC8] hover:bg-[#FFFBF2] hover:border-[#D4A828] hover:text-[#1E2A3A]'
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
        {activeTab === 'matching' && <MatchingTab API={API} headers={headers} />}
        {activeTab === 'covers' && <CoversTab API={API} headers={headers} />}
        {activeTab === 'migration' && <MigrationTab API={API} headers={headers} />}
        {activeTab === 'testimonials' && <TestimonialsTab API={API} headers={headers} />}
      </div>
    </div>
  );
}
