import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import {
  Loader2, Copy, Download, Plus, Users, Key, Check, X,
  MessageSquare, Grid3X3, Flag, Settings, ChevronRight,
  ToggleLeft, ToggleRight, Pencil, Calendar, Hash
} from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import { useSearchParams } from 'react-router-dom';

const AdminPage = () => {
  usePageTitle('Admin Panel');
  const { token, API } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const section = searchParams.get('section') || 'beta';
  const headers = { Authorization: `Bearer ${token}` };

  const setSection = (s) => setSearchParams({ section: s });

  const NAV = [
    { key: 'beta', label: 'Beta & Invites', icon: Users },
    { key: 'prompts', label: 'Daily Prompts', icon: MessageSquare },
    { key: 'bingo', label: 'Bingo Squares', icon: Grid3X3 },
    { key: 'reports', label: 'Reports', icon: Flag },
    { key: 'settings', label: 'Platform Settings', icon: Settings },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 pt-24 pb-24" data-testid="admin-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-6">Admin Panel</h1>

      {/* Tab nav */}
      <div className="flex gap-1.5 mb-6 overflow-x-auto pb-1 scrollbar-hide">
        {NAV.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setSection(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              section === key
                ? 'bg-honey text-vinyl-black'
                : 'bg-honey/10 text-vinyl-black/60 hover:bg-honey/20'
            }`}
            data-testid={`admin-nav-${key}`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {section === 'beta' && <BetaSection API={API} headers={headers} token={token} />}
      {section === 'prompts' && <PromptsSection API={API} headers={headers} />}
      {section === 'bingo' && <BingoSection API={API} headers={headers} />}
      {section === 'reports' && <ReportsSection API={API} headers={headers} />}
      {section === 'settings' && <SettingsSection API={API} headers={headers} />}
    </div>
  );
};


// ═══════════════════════════════════════════════
// BETA & INVITES SECTION
// ═══════════════════════════════════════════════
const BetaSection = ({ API, headers, token }) => {
  const [tab, setTab] = useState('signups');
  const [signups, setSignups] = useState([]);
  const [codes, setCodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingNote, setEditingNote] = useState(null);
  const [noteValue, setNoteValue] = useState('');
  const [generating, setGenerating] = useState(false);

  const fetch = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([
        axios.get(`${API}/admin/beta-signups`, { headers }),
        axios.get(`${API}/admin/invite-codes`, { headers }),
      ]);
      setSignups(s.data);
      setCodes(c.data);
    } catch {}
    setLoading(false);
  }, [API]);

  useEffect(() => { fetch(); }, [fetch]);

  const saveNote = async (id) => {
    try {
      await axios.patch(`${API}/admin/beta-signups/${id}/notes`, { notes: noteValue }, { headers });
      setSignups(signups.map(s => s.id === id ? { ...s, notes: noteValue } : s));
      setEditingNote(null);
      toast.success('Note saved');
    } catch { toast.error('Failed'); }
  };

  const generateCodes = async (count) => {
    setGenerating(true);
    try {
      const res = await axios.post(`${API}/admin/invite-codes/generate`, { count }, { headers });
      setCodes([...res.data, ...codes]);
      toast.success(`Generated ${res.data.length} code(s)`);
    } catch { toast.error('Failed'); }
    setGenerating(false);
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(`${window.location.origin}/join?code=${code}`);
    toast.success('Invite link copied');
  };

  const exportCSV = async () => {
    try {
      const res = await axios.get(`${API}/admin/beta-signups/export`, { headers, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = 'beta_signups.csv'; document.body.appendChild(a); a.click(); a.remove();
    } catch { toast.error('Export failed'); }
  };

  if (loading) return <LoadingSkeleton />;

  return (
    <div data-testid="admin-beta-section">
      <div className="flex gap-2 mb-4">
        <Button size="sm" variant={tab === 'signups' ? 'default' : 'outline'} onClick={() => setTab('signups')}
          className={tab === 'signups' ? 'bg-honey text-vinyl-black' : ''}>
          <Users className="w-4 h-4 mr-1" /> Signups ({signups.length})
        </Button>
        <Button size="sm" variant={tab === 'codes' ? 'default' : 'outline'} onClick={() => setTab('codes')}
          className={tab === 'codes' ? 'bg-honey text-vinyl-black' : ''}>
          <Key className="w-4 h-4 mr-1" /> Invite Codes ({codes.length})
        </Button>
      </div>

      {tab === 'signups' && (
        <Card className="p-0 overflow-hidden border-honey/30">
          <div className="flex items-center justify-between p-4 border-b border-honey/20 bg-honey/5">
            <span className="font-medium text-sm">{signups.length} signup{signups.length !== 1 ? 's' : ''}</span>
            <Button variant="outline" size="sm" onClick={exportCSV} data-testid="export-csv-btn">
              <Download className="w-4 h-4 mr-1" /> CSV
            </Button>
          </div>
          {signups.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground text-sm">No signups yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="signups-table">
                <thead><tr className="border-b border-honey/20 text-left text-muted-foreground text-xs">
                  <th className="px-3 py-2.5">Name</th><th className="px-3 py-2.5">Instagram</th>
                  <th className="px-3 py-2.5">Email</th><th className="px-3 py-2.5">Feature</th>
                  <th className="px-3 py-2.5">Date</th><th className="px-3 py-2.5 min-w-[160px]">Notes</th>
                </tr></thead>
                <tbody>
                  {signups.map(s => (
                    <tr key={s.id} className="border-b border-honey/10 hover:bg-honey/5">
                      <td className="px-3 py-2.5 font-medium">{s.first_name}</td>
                      <td className="px-3 py-2.5 text-honey-amber">@{s.instagram_handle}</td>
                      <td className="px-3 py-2.5">{s.email}</td>
                      <td className="px-3 py-2.5 text-xs">{s.feature_interest}</td>
                      <td className="px-3 py-2.5 text-muted-foreground text-xs whitespace-nowrap">{fmtDate(s.submitted_at)}</td>
                      <td className="px-3 py-2.5">
                        {editingNote === s.id ? (
                          <div className="flex gap-1">
                            <Input value={noteValue} onChange={e => setNoteValue(e.target.value)} className="h-7 text-xs border-honey/30"
                              onKeyDown={e => e.key === 'Enter' && saveNote(s.id)} autoFocus />
                            <Button size="sm" variant="ghost" onClick={() => saveNote(s.id)} className="h-7 px-1.5"><Check className="w-3 h-3" /></Button>
                            <Button size="sm" variant="ghost" onClick={() => setEditingNote(null)} className="h-7 px-1.5"><X className="w-3 h-3" /></Button>
                          </div>
                        ) : (
                          <button onClick={() => { setEditingNote(s.id); setNoteValue(s.notes || ''); }}
                            className="text-left text-xs text-muted-foreground hover:text-vinyl-black cursor-pointer">
                            {s.notes || 'add note...'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {tab === 'codes' && (
        <Card className="p-0 overflow-hidden border-honey/30">
          <div className="flex items-center justify-between p-4 border-b border-honey/20 bg-honey/5 flex-wrap gap-2">
            <span className="font-medium text-sm">Invite Codes</span>
            <div className="flex gap-1.5">
              <Button size="sm" onClick={() => generateCodes(1)} disabled={generating} className="bg-honey text-vinyl-black hover:bg-honey-amber" data-testid="gen-1-btn">
                {generating ? <Loader2 className="w-3 h-3 animate-spin" /> : <><Plus className="w-3 h-3 mr-1" />1</>}
              </Button>
              {[10, 25, 50].map(n => (
                <Button key={n} size="sm" variant="outline" onClick={() => generateCodes(n)} disabled={generating}>+{n}</Button>
              ))}
            </div>
          </div>
          {codes.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground text-sm">No codes yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="codes-table">
                <thead><tr className="border-b border-honey/20 text-left text-muted-foreground text-xs">
                  <th className="px-3 py-2.5">Code</th><th className="px-3 py-2.5">Status</th>
                  <th className="px-3 py-2.5">Created</th><th className="px-3 py-2.5">Used By</th>
                  <th className="px-3 py-2.5">Actions</th>
                </tr></thead>
                <tbody>
                  {codes.map(c => (
                    <tr key={c.id} className="border-b border-honey/10 hover:bg-honey/5">
                      <td className="px-3 py-2.5 font-mono text-xs font-medium">{c.code}</td>
                      <td className="px-3 py-2.5">
                        <StatusBadge status={c.status} colors={c.status === 'unused' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'} />
                      </td>
                      <td className="px-3 py-2.5 text-muted-foreground text-xs">{fmtDate(c.created_at)}</td>
                      <td className="px-3 py-2.5 text-xs">{c.used_by_username ? `@${c.used_by_username}` : '—'}</td>
                      <td className="px-3 py-2.5">
                        {c.status === 'unused' && (
                          <Button size="sm" variant="ghost" onClick={() => copyCode(c.code)} className="h-7 text-xs">
                            <Copy className="w-3 h-3 mr-1" /> Copy Link
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};


// ═══════════════════════════════════════════════
// DAILY PROMPTS SECTION
// ═══════════════════════════════════════════════
const PromptsSection = ({ API, headers }) => {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ text: '', scheduled_date: '' });

  const fetch = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/prompts/admin/all`, { headers });
      setPrompts(res.data);
    } catch {}
    setLoading(false);
  }, [API]);

  useEffect(() => { fetch(); }, [fetch]);

  const createPrompt = async () => {
    if (!form.text || !form.scheduled_date) { toast.error('Text and date required'); return; }
    try {
      const res = await axios.post(`${API}/prompts/admin/create`, form, { headers });
      setPrompts([...prompts, { ...res.data, response_count: 0 }]);
      setForm({ text: '', scheduled_date: '' });
      setShowCreate(false);
      toast.success('Prompt created');
    } catch { toast.error('Failed'); }
  };

  const updatePrompt = async (id, data) => {
    try {
      const res = await axios.put(`${API}/prompts/admin/${id}`, data, { headers });
      setPrompts(prompts.map(p => p.id === id ? { ...p, ...res.data } : p));
      setEditingId(null);
      toast.success('Updated');
    } catch { toast.error('Failed'); }
  };

  const toggleActive = (p) => updatePrompt(p.id, { active: !p.active });

  if (loading) return <LoadingSkeleton />;

  return (
    <div data-testid="admin-prompts-section">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-muted-foreground">{prompts.length} prompt{prompts.length !== 1 ? 's' : ''}</p>
        <Button size="sm" onClick={() => setShowCreate(!showCreate)} className="bg-honey text-vinyl-black hover:bg-honey-amber" data-testid="create-prompt-btn">
          <Plus className="w-4 h-4 mr-1" /> New Prompt
        </Button>
      </div>

      {showCreate && (
        <Card className="p-4 mb-4 border-honey/30 space-y-3">
          <Textarea placeholder="Enter prompt text..." value={form.text} onChange={e => setForm({ ...form, text: e.target.value })}
            className="border-honey/30 text-sm" rows={2} data-testid="prompt-text-input" />
          <div className="flex gap-2 items-center">
            <Input type="date" value={form.scheduled_date} onChange={e => setForm({ ...form, scheduled_date: e.target.value })}
              className="border-honey/30 text-sm w-auto" data-testid="prompt-date-input" />
            <Button size="sm" onClick={createPrompt} className="bg-honey text-vinyl-black" data-testid="prompt-save-btn">Save</Button>
            <Button size="sm" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
          </div>
        </Card>
      )}

      <Card className="p-0 overflow-hidden border-honey/30">
        {prompts.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground text-sm">No prompts yet. Create one to get started.</div>
        ) : (
          <div className="divide-y divide-honey/10">
            {prompts.map(p => (
              <PromptRow key={p.id} prompt={p} editing={editingId === p.id}
                onEdit={() => { setEditingId(p.id); setForm({ text: p.text, scheduled_date: p.scheduled_date?.split('T')[0] || '' }); }}
                onCancel={() => setEditingId(null)}
                onSave={(data) => updatePrompt(p.id, data)}
                onToggle={() => toggleActive(p)}
                form={form} setForm={setForm} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

const PromptRow = ({ prompt, editing, onEdit, onCancel, onSave, onToggle, form, setForm }) => (
  <div className="flex items-start gap-3 p-3 hover:bg-honey/5" data-testid={`prompt-row-${prompt.id}`}>
    <button onClick={onToggle} className="mt-1 shrink-0" title={prompt.active ? 'Active' : 'Inactive'}>
      {prompt.active
        ? <ToggleRight className="w-5 h-5 text-green-500" />
        : <ToggleLeft className="w-5 h-5 text-muted-foreground" />}
    </button>
    <div className="flex-1 min-w-0">
      {editing ? (
        <div className="space-y-2">
          <Textarea value={form.text} onChange={e => setForm({ ...form, text: e.target.value })} className="border-honey/30 text-sm" rows={2} />
          <div className="flex gap-2 items-center">
            <Input type="date" value={form.scheduled_date} onChange={e => setForm({ ...form, scheduled_date: e.target.value })} className="border-honey/30 text-sm w-auto" />
            <Button size="sm" onClick={() => onSave({ text: form.text, scheduled_date: form.scheduled_date })} className="bg-honey text-vinyl-black h-7">Save</Button>
            <Button size="sm" variant="ghost" onClick={onCancel} className="h-7">Cancel</Button>
          </div>
        </div>
      ) : (
        <>
          <p className={`text-sm ${prompt.active ? 'text-vinyl-black' : 'text-muted-foreground line-through'}`}>{prompt.text}</p>
          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{prompt.scheduled_date?.split('T')[0] || '—'}</span>
            <span className="flex items-center gap-1"><Hash className="w-3 h-3" />{prompt.response_count || 0} responses</span>
          </div>
        </>
      )}
    </div>
    {!editing && (
      <Button size="sm" variant="ghost" onClick={onEdit} className="shrink-0 h-7 px-2">
        <Pencil className="w-3 h-3" />
      </Button>
    )}
  </div>
);


// ═══════════════════════════════════════════════
// BINGO SQUARES SECTION
// ═══════════════════════════════════════════════
const BingoSection = ({ API, headers }) => {
  const [squares, setSquares] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ text: '', emoji: '' });
  const [editingId, setEditingId] = useState(null);

  const fetch = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/bingo/admin/squares`, { headers });
      setSquares(res.data);
    } catch {}
    setLoading(false);
  }, [API]);

  useEffect(() => { fetch(); }, [fetch]);

  const createSquare = async () => {
    if (!form.text) { toast.error('Text required'); return; }
    try {
      const res = await axios.post(`${API}/bingo/admin/squares`, form, { headers });
      setSquares([...squares, res.data]);
      setForm({ text: '', emoji: '' });
      setShowCreate(false);
      toast.success('Square created');
    } catch { toast.error('Failed'); }
  };

  const updateSquare = async (id, data) => {
    try {
      const res = await axios.put(`${API}/bingo/admin/squares/${id}`, data, { headers });
      setSquares(squares.map(s => s.id === id ? { ...s, ...res.data } : s));
      setEditingId(null);
      toast.success('Updated');
    } catch { toast.error('Failed'); }
  };

  if (loading) return <LoadingSkeleton />;

  const active = squares.filter(s => s.active);
  const inactive = squares.filter(s => !s.active);

  return (
    <div data-testid="admin-bingo-section">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-muted-foreground">{active.length} active / {inactive.length} inactive</p>
        <Button size="sm" onClick={() => setShowCreate(!showCreate)} className="bg-honey text-vinyl-black hover:bg-honey-amber" data-testid="create-square-btn">
          <Plus className="w-4 h-4 mr-1" /> New Square
        </Button>
      </div>

      {showCreate && (
        <Card className="p-4 mb-4 border-honey/30 space-y-3">
          <div className="flex gap-2">
            <Input placeholder="Square text (e.g. 'Spin a 7-inch')" value={form.text}
              onChange={e => setForm({ ...form, text: e.target.value })} className="border-honey/30 text-sm flex-1" data-testid="square-text-input" />
            <Input placeholder="Emoji" value={form.emoji} onChange={e => setForm({ ...form, emoji: e.target.value })}
              className="border-honey/30 text-sm w-20 text-center" maxLength={4} data-testid="square-emoji-input" />
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={createSquare} className="bg-honey text-vinyl-black" data-testid="square-save-btn">Save</Button>
            <Button size="sm" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
          </div>
        </Card>
      )}

      <Card className="p-0 overflow-hidden border-honey/30">
        {squares.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground text-sm">No squares yet.</div>
        ) : (
          <div className="divide-y divide-honey/10">
            {squares.map(s => (
              <div key={s.id} className="flex items-center gap-3 p-3 hover:bg-honey/5" data-testid={`square-row-${s.id}`}>
                <button onClick={() => updateSquare(s.id, { active: !s.active })} className="shrink-0">
                  {s.active ? <ToggleRight className="w-5 h-5 text-green-500" /> : <ToggleLeft className="w-5 h-5 text-muted-foreground" />}
                </button>
                <span className="text-xl shrink-0 w-8 text-center">{s.emoji || '🎵'}</span>
                {editingId === s.id ? (
                  <div className="flex-1 flex gap-2 items-center">
                    <Input value={form.text} onChange={e => setForm({ ...form, text: e.target.value })} className="border-honey/30 text-sm flex-1 h-8" autoFocus />
                    <Input value={form.emoji} onChange={e => setForm({ ...form, emoji: e.target.value })} className="border-honey/30 text-sm w-16 h-8 text-center" maxLength={4} />
                    <Button size="sm" onClick={() => updateSquare(s.id, { text: form.text })} className="bg-honey text-vinyl-black h-7">Save</Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditingId(null)} className="h-7">Cancel</Button>
                  </div>
                ) : (
                  <>
                    <span className={`flex-1 text-sm ${s.active ? '' : 'text-muted-foreground line-through'}`}>{s.text}</span>
                    <Button size="sm" variant="ghost" onClick={() => { setEditingId(s.id); setForm({ text: s.text, emoji: s.emoji || '' }); }} className="shrink-0 h-7 px-2">
                      <Pencil className="w-3 h-3" />
                    </Button>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};


// ═══════════════════════════════════════════════
// REPORTS REVIEW SECTION
// ═══════════════════════════════════════════════
const REPORT_STATUSES = ['Pending', 'Reviewed', 'Actioned', 'Dismissed'];
const STATUS_COLORS = {
  Pending: 'bg-yellow-100 text-yellow-700',
  Reviewed: 'bg-blue-100 text-blue-700',
  Actioned: 'bg-red-100 text-red-700',
  Dismissed: 'bg-zinc-100 text-zinc-600',
};

const ReportsSection = ({ API, headers }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const fetch = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/reports/admin`, { headers });
      setReports(res.data);
    } catch {}
    setLoading(false);
  }, [API]);

  useEffect(() => { fetch(); }, [fetch]);

  const updateStatus = async (id, status) => {
    try {
      const res = await axios.put(`${API}/reports/admin/${id}`, { status }, { headers });
      setReports(reports.map(r => r.id === id ? res.data : r));
      toast.success(`Report marked as ${status}`);
    } catch { toast.error('Failed'); }
  };

  if (loading) return <LoadingSkeleton />;

  const filtered = filter === 'all' ? reports : reports.filter(r => r.status === filter);

  return (
    <div data-testid="admin-reports-section">
      <div className="flex gap-1.5 mb-4 flex-wrap">
        {['all', ...REPORT_STATUSES].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              filter === s ? 'bg-vinyl-black text-white' : 'bg-honey/10 text-vinyl-black/60 hover:bg-honey/20'
            }`}>
            {s === 'all' ? `All (${reports.length})` : `${s} (${reports.filter(r => r.status === s).length})`}
          </button>
        ))}
      </div>

      <Card className="p-0 overflow-hidden border-honey/30">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground text-sm">
            {reports.length === 0 ? 'No reports yet.' : 'No reports with this status.'}
          </div>
        ) : (
          <div className="divide-y divide-honey/10">
            {filtered.map(r => (
              <div key={r.id} className="p-4 hover:bg-honey/5" data-testid={`report-row-${r.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <StatusBadge status={r.type} colors="bg-vinyl-black/10 text-vinyl-black" />
                      <StatusBadge status={r.status} colors={STATUS_COLORS[r.status]} />
                    </div>
                    <p className="text-sm font-medium">{r.reason}</p>
                    {r.content_preview && <p className="text-xs text-muted-foreground mt-0.5 truncate">{r.content_preview}</p>}
                    <p className="text-xs text-muted-foreground mt-1">
                      by @{r.reporter_username} &middot; {fmtDate(r.created_at)}
                      {r.notes && <span className="ml-2 italic">"{r.notes}"</span>}
                    </p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    {REPORT_STATUSES.filter(s => s !== r.status).map(s => (
                      <Button key={s} size="sm" variant="outline" onClick={() => updateStatus(r.id, s)}
                        className="h-7 text-xs px-2" data-testid={`report-action-${s.toLowerCase()}`}>
                        {s}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};


// ═══════════════════════════════════════════════
// PLATFORM SETTINGS SECTION
// ═══════════════════════════════════════════════
const SettingsSection = ({ API, headers }) => {
  const [fee, setFee] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/admin/settings`, { headers });
        const feeSetting = res.data.find(s => s.key === 'platform_fee_percent');
        if (feeSetting) setFee(String(feeSetting.value));
        else setFee('6');
      } catch {}
      setLoading(false);
    })();
  }, [API]);

  const saveFee = async () => {
    const val = parseFloat(fee);
    if (isNaN(val) || val < 0 || val > 50) { toast.error('Enter a valid fee (0-50)'); return; }
    setSaving(true);
    try {
      await axios.post(`${API}/admin/settings`, { key: 'platform_fee_percent', value: val }, { headers });
      toast.success(`Platform fee updated to ${val}%`);
    } catch { toast.error('Failed'); }
    setSaving(false);
  };

  if (loading) return <LoadingSkeleton />;

  return (
    <div data-testid="admin-settings-section">
      <Card className="p-6 border-honey/30 max-w-md">
        <h3 className="font-heading text-lg mb-1">Platform Fee</h3>
        <p className="text-xs text-muted-foreground mb-4">Applied to all Honeypot marketplace transactions.</p>
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Input type="number" value={fee} onChange={e => setFee(e.target.value)} min="0" max="50" step="0.5"
              className="border-honey/30 pr-8 text-lg font-medium" data-testid="fee-input" />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">%</span>
          </div>
          <Button onClick={saveFee} disabled={saving} className="bg-honey text-vinyl-black hover:bg-honey-amber" data-testid="fee-save-btn">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save'}
          </Button>
        </div>
      </Card>
    </div>
  );
};


// ═══════════════════════════════════════════════
// SHARED COMPONENTS
// ═══════════════════════════════════════════════
const StatusBadge = ({ status, colors }) => (
  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colors}`}>
    {status}
  </span>
);

const LoadingSkeleton = () => (
  <div className="space-y-3">
    {[1, 2, 3].map(i => <div key={i} className="h-16 bg-honey/10 rounded-xl animate-pulse" />)}
  </div>
);

const fmtDate = (iso) => {
  try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
  catch { return iso; }
};

export default AdminPage;
