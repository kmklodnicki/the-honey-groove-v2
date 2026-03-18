import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import {
  Loader2, Copy, Download, Plus, Users, Key, KeyRound, Check, X, Trash2,
  MessageSquare, Grid3X3, Flag, Settings, ChevronRight, Search,
  ToggleLeft, ToggleRight, Pencil, Calendar, Hash, Shield, DollarSign, ArrowRightLeft, AlertTriangle, Flame, Heart, Clock, BarChart2
} from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import { useSearchParams, Link } from 'react-router-dom';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';

const AdminPage = () => {
  usePageTitle('Admin Panel');
  const { token, API } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const section = searchParams.get('section') || 'beta';
  const headers = { Authorization: `Bearer ${token}` };

  const setSection = (s) => setSearchParams({ section: s });

  const NAV = [
    { key: 'beta', label: 'Beta & Invites', icon: Users },
    { key: 'users', label: 'User Management', icon: Shield },
    { key: 'prompts', label: 'Daily Prompts', icon: MessageSquare },
    { key: 'bingo', label: 'Bingo Squares', icon: Grid3X3 },
    { key: 'holds', label: 'Hold Disputes', icon: Shield },
    { key: 'sale_disputes', label: 'Sale Disputes', icon: AlertTriangle },
    { key: 'offplatform', label: 'Off-Platform Alerts', icon: Flag },
    { key: 'reports', label: 'Reports', icon: Flag },
    { key: 'feedback', label: 'Feedback & Bug Reports', icon: Heart },
    { key: 'watchtower', label: 'Watchtower', icon: AlertTriangle },
    { key: 'gate', label: 'The Gate', icon: Shield },
    { key: 'golden_hive', label: 'Verification', icon: Shield },
    { key: 'test_listings', label: 'Test Listings', icon: Flag },
    { key: 'settings', label: 'Platform Settings', icon: Settings },
    { key: 'beekeeper', label: 'Beekeeper', icon: BarChart2 },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-24 pr-10" data-testid="admin-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-6">Admin Panel</h1>

      {/* Tab nav */}
      <div className="flex flex-wrap gap-2 mb-6 pb-1">
        {NAV.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setSection(key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all border ${
              section === key
                ? 'bg-[#E8A820] text-[#2A1A06] border-[#C8861A] shadow-sm'
                : 'bg-white text-[#8A6B4A] border-[#C8861A]/15 hover:bg-[#C8861A]/5 hover:border-[#C8861A]/30'
            }`}
            data-testid={`admin-nav-${key}`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {section === 'beta' && <BetaSection API={API} headers={headers} token={token} />}
      {section === 'users' && <UserManagementSection API={API} headers={headers} />}
      {section === 'prompts' && <PromptsSection API={API} headers={headers} />}
      {section === 'bingo' && <BingoSection API={API} headers={headers} />}
      {section === 'holds' && <HoldDisputesSection API={API} headers={headers} />}
      {section === 'sale_disputes' && <SaleDisputesSection API={API} headers={headers} />}
      {section === 'offplatform' && <OffPlatformAlertsSection API={API} headers={headers} />}
      {section === 'reports' && <ReportsSection API={API} headers={headers} />}
      {section === 'feedback' && <FeedbackSection API={API} headers={headers} />}
      {section === 'watchtower' && <WatchtowerSection API={API} headers={headers} />}
      {section === 'gate' && <GateSection API={API} headers={headers} />}
      {section === 'golden_hive' && <GoldenHiveAdminSection API={API} headers={headers} />}
      {section === 'test_listings' && <TestListingsSection API={API} headers={headers} />}
      {section === 'settings' && <SettingsSection API={API} headers={headers} />}
      {section === 'beekeeper' && <BeekeeperSection API={API} headers={headers} />}
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
  const [sendingInvite, setSendingInvite] = useState(null);

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
    } catch { toast.error('something went wrong.'); }
  };

  const generateCodes = async (count) => {
    setGenerating(true);
    try {
      const res = await axios.post(`${API}/admin/invite-codes/generate`, { count }, { headers });
      setCodes([...res.data, ...codes]);
      toast.success(`Generated ${res.data.length} code(s)`);
    } catch { toast.error('something went wrong.'); }
    setGenerating(false);
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(`${window.location.origin}/join?code=${code}`);
    toast.success('Invite link copied');
  };

  const copyCodeText = (code) => {
    navigator.clipboard.writeText(code);
    toast.success('Code copied');
  };

  const sendInviteToSignup = async (signup) => {
    setSendingInvite(signup.id);
    try {
      const res = await axios.post(`${API}/admin/beta-signups/${signup.id}/send-invite`, {}, { headers });
      setSignups(prev => prev.map(s => s.id === signup.id ? {
        ...s,
        invite_status: 'sent',
        invite_code: res.data.invite_code,
        invite_code_id: res.data.invite_code_id,
        invite_sent_at: res.data.invite_sent_at,
      } : s));
      toast.success(`invite sent to ${signup.email}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'failed to send invite.');
    }
    setSendingInvite(null);
  };

  const exportCSV = async () => {
    try {
      const res = await axios.get(`${API}/admin/beta-signups/export`, { headers, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = 'beta_signups.csv'; document.body.appendChild(a); a.click(); a.remove();
    } catch { toast.error('export failed. try again.'); }
  };

  const getInviteStatus = (s) => {
    if (s.invite_status === 'used') return 'used';
    if (s.invite_status === 'sent') return 'sent';
    return 'not_sent';
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
                  <th className="px-3 py-2.5">Date</th><th className="px-3 py-2.5">Status</th>
                  <th className="px-3 py-2.5">Action</th><th className="px-3 py-2.5">Code</th>
                </tr></thead>
                <tbody>
                  {signups.map(s => {
                    const status = getInviteStatus(s);
                    return (
                    <tr key={s.id} className="border-b border-honey/10 hover:bg-honey/5" data-testid={`signup-row-${s.id}`}>
                      <td className="px-3 py-2.5 font-medium">{s.first_name}</td>
                      <td className="px-3 py-2.5 text-honey-amber">{s.instagram_handle?.startsWith('@') ? s.instagram_handle : `@${s.instagram_handle}`}</td>
                      <td className="px-3 py-2.5">{s.email}</td>
                      <td className="px-3 py-2.5 text-xs max-w-[120px] truncate">{s.feature_interest}</td>
                      <td className="px-3 py-2.5 text-muted-foreground text-xs whitespace-nowrap">{fmtDate(s.submitted_at)}</td>
                      <td className="px-3 py-2.5">
                        {status === 'not_sent' && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-stone-100 text-stone-500" data-testid={`invite-status-${s.id}`}>not sent</span>
                        )}
                        {status === 'sent' && (
                          <div>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#E8A820]/15 text-[#C8861A]" data-testid={`invite-status-${s.id}`}>sent</span>
                            {s.invite_sent_at && <p className="text-[9px] text-muted-foreground mt-0.5">{fmtDate(s.invite_sent_at)}</p>}
                          </div>
                        )}
                        {status === 'used' && (
                          <div>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 text-green-700 inline-flex items-center gap-0.5" data-testid={`invite-status-${s.id}`}>
                              <Check className="w-3 h-3" /> joined
                            </span>
                            {s.invite_used_at && <p className="text-[9px] text-muted-foreground mt-0.5">{fmtDate(s.invite_used_at)}</p>}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2.5">
                        {status !== 'used' && (
                          <Button
                            size="sm" variant="outline"
                            onClick={() => sendInviteToSignup(s)}
                            disabled={sendingInvite === s.id}
                            className="h-7 text-xs border-[#C8861A]/40 text-[#C8861A] hover:bg-[#E8A820]/10"
                            data-testid={`send-invite-${s.id}`}
                          >
                            {sendingInvite === s.id ? <Loader2 className="w-3 h-3 animate-spin" /> : (
                              <>{status === 'sent' ? 'Resend' : 'Send Invite'}</>
                            )}
                          </Button>
                        )}
                      </td>
                      <td className="px-3 py-2.5">
                        {s.invite_code && (
                          <button
                            onClick={() => copyCodeText(s.invite_code)}
                            className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-[#C8861A] transition-colors"
                            title="Click to copy code"
                            data-testid={`copy-code-${s.id}`}
                          >
                            <span className="font-mono">code: {s.invite_code}</span>
                            <Copy className="w-3 h-3" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );})}
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
                      <td className="px-3 py-2.5 text-xs">{c.used_by_username ? `@${c.used_by_username}` : '·'}</td>
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
    } catch { toast.error('something went wrong.'); }
  };

  const updatePrompt = async (id, data) => {
    try {
      const res = await axios.put(`${API}/prompts/admin/${id}`, data, { headers });
      setPrompts(prompts.map(p => p.id === id ? { ...p, ...res.data } : p));
      setEditingId(null);
      toast.success('Updated');
    } catch { toast.error('something went wrong.'); }
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
            <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{prompt.scheduled_date?.split('T')[0] || '·'}</span>
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
    } catch { toast.error('something went wrong.'); }
  };

  const updateSquare = async (id, data) => {
    try {
      const res = await axios.put(`${API}/bingo/admin/squares/${id}`, data, { headers });
      setSquares(squares.map(s => s.id === id ? { ...s, ...res.data } : s));
      setEditingId(null);
      toast.success('Updated');
    } catch { toast.error('something went wrong.'); }
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
// MUTUAL HOLD DISPUTES SECTION
// ═══════════════════════════════════════════════
const HoldDisputesSection = ({ API, headers }) => {
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(null);
  const [notes, setNotes] = useState({});
  const [partialInit, setPartialInit] = useState({});
  const [partialResp, setPartialResp] = useState({});
  const [showPartial, setShowPartial] = useState(null);

  const fetchDisputes = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/admin/hold-disputes`, { headers });
      setDisputes(res.data);
    } catch {}
    setLoading(false);
  }, [API]);

  useEffect(() => { fetchDisputes(); }, [fetchDisputes]);

  const resolve = async (tradeId, resolution) => {
    const n = (notes[tradeId] || '').trim();
    if (!n) { toast.error('Resolution notes required'); return; }
    setResolving(tradeId);
    try {
      const body = { resolution, notes: n };
      if (resolution === 'partial') {
        body.partial_refund_initiator = partialInit[tradeId] ? parseFloat(partialInit[tradeId]) : 0;
        body.partial_refund_responder = partialResp[tradeId] ? parseFloat(partialResp[tradeId]) : 0;
      }
      await axios.put(`${API}/admin/hold-disputes/${tradeId}/resolve`, body, { headers });
      toast.success('dispute resolved.');
      setNotes(p => ({ ...p, [tradeId]: '' }));
      setPartialInit(p => ({ ...p, [tradeId]: '' }));
      setPartialResp(p => ({ ...p, [tradeId]: '' }));
      setShowPartial(null);
      fetchDisputes();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to resolve'); }
    setResolving(null);
  };

  if (loading) return <LoadingSkeleton />;

  return (
    <div data-testid="admin-holds-section">
      <p className="text-sm font-['Cormorant_Garamond'] italic text-[#8A6B4A] mb-5">
        {disputes.length} active dispute{disputes.length !== 1 ? 's' : ''} with frozen holds
      </p>

      {disputes.length === 0 ? (
        <div className="bg-white border border-[#C8861A]/15 rounded-2xl p-14 text-center">
          <Shield className="w-10 h-10 text-[#C8861A]/25 mx-auto mb-3" />
          <p className="text-[#8A6B4A] text-sm font-['Cormorant_Garamond'] italic">No hold disputes. All clear.</p>
        </div>
      ) : (
        <div className="space-y-5">
          {disputes.map(trade => {
            const amt = trade.hold_amount || 0;
            return (
            <div key={trade.id} className="bg-white border border-[#C8861A]/15 rounded-2xl overflow-hidden" data-testid={`hold-dispute-${trade.id}`}>
              {/* Header */}
              <div className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg border border-[#C8861A] text-[#C8861A] text-xs font-bold bg-white">
                    <Shield className="w-3 h-3" /> HOLD FROZEN
                  </span>
                  <span className="text-xs font-mono text-[#8A6B4A]">{trade.id.slice(0, 8)}</span>
                </div>
                <span className="text-lg font-heading font-bold text-[#996012]">${amt} per party</span>
              </div>

              <div className="px-6 pb-6 space-y-5">
                {/* Parties + records */}
                <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-center">
                  <div className="space-y-2">
                    <p className="text-[10px] uppercase tracking-widest text-[#8A6B4A]">Proposer</p>
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-[#E8A820]/20 flex items-center justify-center text-xs font-bold text-[#996012]">
                        {(trade.initiator?.username || '?')[0].toUpperCase()}
                      </div>
                      <span className="text-sm font-medium text-[#2A1A06]">@{trade.initiator?.username || '?'}</span>
                    </div>
                    {trade.offered_record && (
                      <div className="flex items-center gap-2 mt-1">
                        <AlbumArt src={trade.offered_record.cover_url} alt={`${trade.offered_record.artist} ${trade.offered_record.title} vinyl record`} className="w-9 h-9 rounded object-cover" />
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-[#2A1A06] truncate">{trade.offered_record.title}</p>
                          <p className="text-[10px] text-[#8A6B4A]">{trade.offered_record.artist}</p>
                        </div>
                      </div>
                    )}
                  </div>

                  <ArrowRightLeft className="w-5 h-5 text-[#C8861A] shrink-0" />

                  <div className="space-y-2">
                    <p className="text-[10px] uppercase tracking-widest text-[#8A6B4A]">Recipient</p>
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-[#E8A820]/20 flex items-center justify-center text-xs font-bold text-[#996012]">
                        {(trade.responder?.username || '?')[0].toUpperCase()}
                      </div>
                      <span className="text-sm font-medium text-[#2A1A06]">@{trade.responder?.username || '?'}</span>
                    </div>
                    {trade.listing_record && (
                      <div className="flex items-center gap-2 mt-1">
                        <AlbumArt src={trade.listing_record.cover_url} alt={`${trade.listing_record.artist} ${trade.listing_record.title} vinyl record`} className="w-9 h-9 rounded object-cover" />
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-[#2A1A06] truncate">{trade.listing_record.album}</p>
                          <p className="text-[10px] text-[#8A6B4A]">{trade.listing_record.artist}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Dispute details */}
                {trade.dispute && (
                  <div className="bg-[#FAF6EE] rounded-xl p-4 border-l-[3px] border-[#C8861A]">
                    <p className="text-[10px] uppercase tracking-wider text-[#8A6B4A] mb-1.5">
                      Dispute by @{trade.dispute.opened_by === trade.initiator_id ? trade.initiator?.username : trade.responder?.username}
                      {' '}&middot; {fmtDate(trade.dispute.opened_at)}
                    </p>
                    <p className="text-[#2A1A06] text-base font-['Cormorant_Garamond'] leading-relaxed">{trade.dispute.reason}</p>
                    {trade.dispute.photo_urls?.length > 0 && (
                      <div className="flex gap-2 mt-3">
                        {trade.dispute.photo_urls.map((url, i) => (
                          <a key={i} href={url} target="_blank" rel="noreferrer">
                            <img src={url} alt={`evidence ${i + 1}`} className="w-14 h-14 rounded-lg object-cover border border-[#C8861A]/20" />
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Resolution notes */}
                <Textarea
                  placeholder="Resolution notes (required) · explain your decision..."
                  value={notes[trade.id] || ''}
                  onChange={e => setNotes(p => ({ ...p, [trade.id]: e.target.value }))}
                  className="bg-[#FAF6EE] border-[#C8861A]/20 rounded-xl text-sm resize-none focus:ring-[#C8861A]/30 focus:border-[#C8861A]/40"
                  rows={2}
                  data-testid={`dispute-notes-${trade.id}`}
                />

                {/* Partial split inputs */}
                {showPartial === trade.id && (
                  <div className="bg-[#FAF6EE] rounded-xl p-4 border border-[#C8861A]/15 space-y-3">
                    <p className="text-xs text-[#8A6B4A]">Enter refund amount for each party. Total must equal ${amt} per party.</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] uppercase tracking-wider text-[#8A6B4A]">Refund @{trade.initiator?.username}</label>
                        <div className="relative mt-1">
                          <DollarSign className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#8A6B4A]" />
                          <Input type="number" min="0" max={amt} value={partialInit[trade.id] || ''}
                            onChange={e => setPartialInit(p => ({ ...p, [trade.id]: e.target.value }))}
                            className="pl-8 h-9 text-sm bg-white border-[#C8861A]/20 rounded-xl"
                            placeholder="0.00" data-testid={`partial-init-${trade.id}`} />
                        </div>
                      </div>
                      <div>
                        <label className="text-[10px] uppercase tracking-wider text-[#8A6B4A]">Refund @{trade.responder?.username}</label>
                        <div className="relative mt-1">
                          <DollarSign className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#8A6B4A]" />
                          <Input type="number" min="0" max={amt} value={partialResp[trade.id] || ''}
                            onChange={e => setPartialResp(p => ({ ...p, [trade.id]: e.target.value }))}
                            className="pl-8 h-9 text-sm bg-white border-[#C8861A]/20 rounded-xl"
                            placeholder="0.00" data-testid={`partial-resp-${trade.id}`} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action buttons · brand-aligned */}
                <div className="grid grid-cols-2 gap-2.5">
                  <Button size="sm"
                    className="h-10 rounded-xl bg-[#E8A820] text-[#2A1A06] font-medium hover:bg-[#D49A18] border-0"
                    disabled={resolving === trade.id}
                    onClick={() => {
                      if (window.confirm(`Both holds will be fully reversed. Each party receives $${amt} back within 2 to 5 business days. This action is final.`))
                        resolve(trade.id, 'full_reversal');
                    }}
                    data-testid={`resolve-full_reversal-${trade.id}`}
                  >
                    {resolving === trade.id ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : null}
                    Release Both Holds
                  </Button>
                  <Button size="sm" variant="outline"
                    className="h-10 rounded-xl bg-white text-red-700 border-red-300 hover:bg-red-50 font-medium"
                    disabled={resolving === trade.id}
                    onClick={() => {
                      const disputeOpener = trade.dispute?.opened_by;
                      const offenderRole = disputeOpener === trade.initiator_id ? 'penalize_responder' : 'penalize_initiator';
                      const offenderName = disputeOpener === trade.initiator_id ? trade.responder?.username : trade.initiator?.username;
                      if (window.confirm(`@${offenderName}'s hold of $${amt} will be captured. The victim's hold will be fully reversed. This action is final.`))
                        resolve(trade.id, offenderRole);
                    }}
                    data-testid={`resolve-capture-offender-${trade.id}`}
                  >
                    Capture Offender & Refund Victim
                  </Button>
                  <Button size="sm" variant="outline"
                    className="h-10 rounded-xl bg-white text-amber-700 border-amber-300 hover:bg-amber-50 font-medium"
                    disabled={resolving === trade.id}
                    onClick={() => resolve(trade.id, 'extend_investigation')}
                    data-testid={`resolve-extend-${trade.id}`}
                  >
                    <Clock className="w-3.5 h-3.5 mr-1.5" /> Extend Investigation
                  </Button>
                  <Button size="sm" variant="outline"
                    className="h-10 rounded-xl bg-white text-[#8A6B4A] border-[#8A6B4A]/40 hover:bg-[#C8861A]/5 font-medium"
                    disabled={resolving === trade.id}
                    onClick={() => {
                      if (showPartial === trade.id) resolve(trade.id, 'partial');
                      else setShowPartial(trade.id);
                    }}
                    data-testid={`resolve-partial-${trade.id}`}
                  >
                    Custom Split
                  </Button>
                </div>
                <p className="text-center font-['Cormorant_Garamond'] italic text-[#8A6B4A] text-sm">
                  All resolutions are final. Stripe refunds take 2 to 5 business days.
                </p>
              </div>
            </div>
            );
          })}
        </div>
      )}
    </div>
  );
};


// ═══════════════════════════════════════════════
// SALE DISPUTES SECTION
// ═══════════════════════════════════════════════
const SALE_DISPUTE_REASON_LABELS = {
  record_not_as_described: 'Record not as described',
  damaged_during_shipping: 'Damaged during shipping',
  wrong_record_sent: 'Wrong record sent',
  missing_item: 'Missing item',
  counterfeit_fake_pressing: 'Counterfeit / fake pressing',
};

const SaleDisputesSection = ({ API, headers }) => {
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(null);
  const [resolveNotes, setResolveNotes] = useState({});

  useEffect(() => {
    axios.get(`${API}/admin/sale-disputes`, { headers })
      .then(r => setDisputes(r.data || []))
      .catch(() => toast.error('Failed to load sale disputes'))
      .finally(() => setLoading(false));
  }, [API]);

  const handleResolve = async (orderId, outcome) => {
    const action = outcome === 'approved' ? 'approve the buyer (refund)' : 'reject the dispute (seller keeps payout)';
    if (!window.confirm(`Are you sure you want to ${action}? This action is final.`)) return;
    setResolving(orderId);
    try {
      await axios.post(`${API}/admin/sale-disputes/${orderId}/resolve`, {
        outcome,
        notes: resolveNotes[orderId] || '',
      }, { headers });
      toast.success(`Dispute ${outcome === 'approved' ? 'approved — refund issued' : 'rejected — payout proceeding'}`);
      setDisputes(prev => prev.filter(d => d.id !== orderId));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to resolve dispute');
    } finally {
      setResolving(null);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-[#C8861A]" /></div>;

  return (
    <div className="space-y-4" data-testid="admin-sale-disputes-section">
      <div className="flex items-center gap-3 mb-4">
        <h2 className="font-heading text-xl text-vinyl-black">Sale Disputes</h2>
        <span className="px-2 py-0.5 rounded-full text-xs bg-red-100 text-red-700 font-medium">{disputes.length} open</span>
      </div>

      {disputes.length === 0 ? (
        <div className="text-center py-8 bg-honey/5 rounded-2xl border border-honey/10">
          <p className="text-muted-foreground text-sm">No open sale disputes. All clear.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {disputes.map(order => (
            <div key={order.id} className="bg-white border border-red-200 rounded-2xl overflow-hidden" data-testid={`sale-dispute-${order.id}`}>
              {/* Header */}
              <div className="p-4 border-b border-red-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{order.album} — {order.artist}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Order #{order.order_number || order.id?.substring(0, 8)} · ${order.total?.toFixed(2)}
                    </p>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] bg-red-100 text-red-700 font-medium">Payout on Hold</span>
                </div>
                <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                  <span>Buyer: @{order.buyer_username || order.buyer_id}</span>
                  <span>Seller: @{order.seller_username || order.seller_id}</span>
                  <span>Opened: {order.dispute?.opened_at ? new Date(order.dispute.opened_at).toLocaleDateString() : 'N/A'}</span>
                </div>
              </div>

              {/* Dispute details */}
              <div className="p-4 space-y-3">
                <div>
                  <p className="text-xs font-medium text-red-700 mb-1">Reason</p>
                  <p className="text-sm">{SALE_DISPUTE_REASON_LABELS[order.dispute?.reason] || order.dispute?.reason}</p>
                  {order.dispute?.description && <p className="text-sm text-muted-foreground mt-1">{order.dispute.description}</p>}
                </div>

                {/* Buyer evidence */}
                {order.dispute?.photo_urls?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-red-700 mb-1">Buyer Evidence</p>
                    <div className="flex gap-2 overflow-x-auto">
                      {order.dispute.photo_urls.map((url, i) => (
                        <a key={i} href={url} target="_blank" rel="noopener noreferrer">
                          <img src={url} alt={`evidence-${i}`} className="w-20 h-20 rounded-lg object-cover border border-red-200 hover:opacity-80 transition-opacity" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Seller response */}
                {order.dispute?.response && (
                  <div className="pl-3 border-l-2 border-amber-300">
                    <p className="text-xs font-medium text-amber-700 mb-1">Seller Response</p>
                    <p className="text-sm">{order.dispute.response.text}</p>
                    {order.dispute.response.photo_urls?.length > 0 && (
                      <div className="flex gap-2 mt-1 overflow-x-auto">
                        {order.dispute.response.photo_urls.map((url, i) => (
                          <a key={i} href={url} target="_blank" rel="noopener noreferrer">
                            <img src={url} alt={`resp-${i}`} className="w-20 h-20 rounded-lg object-cover border" />
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Admin resolution notes */}
                <Textarea
                  placeholder="Add resolution notes..."
                  value={resolveNotes[order.id] || ''}
                  onChange={e => setResolveNotes(prev => ({ ...prev, [order.id]: e.target.value }))}
                  className="text-sm resize-none"
                  rows={2}
                  data-testid={`dispute-notes-${order.id}`}
                />

                {/* Resolution buttons */}
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    size="sm"
                    className="h-10 rounded-xl bg-green-600 text-white font-medium hover:bg-green-700"
                    disabled={resolving === order.id}
                    onClick={() => handleResolve(order.id, 'approved')}
                    data-testid={`approve-dispute-${order.id}`}
                  >
                    {resolving === order.id ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null}
                    Approve (Refund Buyer)
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-10 rounded-xl bg-white text-red-600 border-red-200 hover:bg-red-50 font-medium"
                    disabled={resolving === order.id}
                    onClick={() => handleResolve(order.id, 'rejected')}
                    data-testid={`reject-dispute-${order.id}`}
                  >
                    Reject (Pay Seller)
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};



// ═══════════════════════════════════════════════
// REPORTS REVIEW SECTION
// ═══════════════════════════════════════════════
const REPORT_STATUSES = ['Pending', 'Reviewing', 'Resolved'];
const STATUS_COLORS = {
  Pending: 'bg-yellow-100 text-yellow-700',
  Reviewing: 'bg-blue-100 text-blue-700',
  Resolved: 'bg-green-100 text-green-700',
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
    } catch { toast.error('something went wrong.'); }
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
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [togglingMaintenance, setTogglingMaintenance] = useState(false);
  const [runningDisconnect, setRunningDisconnect] = useState(false);
  const [disconnectResult, setDisconnectResult] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/admin/settings`, { headers });
        const feeSetting = res.data.find(s => s.key === 'platform_fee_percent');
        if (feeSetting) setFee(String(feeSetting.value));
        else setFee('6');
        const maintSetting = res.data.find(s => s.key === 'maintenance_mode');
        if (maintSetting) setMaintenanceMode(Boolean(maintSetting.value));
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
    } catch { toast.error('something went wrong.'); }
    setSaving(false);
  };

  const toggleMaintenance = async () => {
    const newState = !maintenanceMode;
    const confirmed = window.confirm(
      newState
        ? 'Enable maintenance mode? All non-admin users will see a maintenance screen.'
        : 'Disable maintenance mode? The site will be live for all users again.'
    );
    if (!confirmed) return;
    setTogglingMaintenance(true);
    try {
      await axios.post(`${API}/admin/maintenance`, { enabled: newState }, { headers });
      setMaintenanceMode(newState);
      toast.success(newState ? 'Maintenance mode enabled' : 'Maintenance mode disabled');
    } catch { toast.error('Failed to toggle maintenance mode'); }
    setTogglingMaintenance(false);
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

      {/* BLOCK-325: Maintenance Mode Toggle */}
      <Card className={`p-6 max-w-md mt-4 ${maintenanceMode ? 'border-amber-400 bg-amber-50/50' : 'border-honey/30'}`} data-testid="maintenance-mode-section">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-heading text-lg mb-1">Maintenance Mode</h3>
            <p className="text-xs text-muted-foreground">When enabled, all non-admin users see a "tuning up" screen.</p>
          </div>
          <button
            onClick={toggleMaintenance}
            disabled={togglingMaintenance}
            className="shrink-0 ml-4 transition-all hover:scale-105"
            data-testid="maintenance-toggle-btn"
          >
            {togglingMaintenance ? (
              <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
            ) : maintenanceMode ? (
              <ToggleRight className="w-10 h-10 text-amber-500" />
            ) : (
              <ToggleLeft className="w-10 h-10 text-stone-400" />
            )}
          </button>
        </div>
        {maintenanceMode && (
          <div className="mt-3 px-3 py-2 rounded-lg text-xs font-medium" style={{ background: 'rgba(218,165,32,0.15)', color: '#92702A', border: '1px solid rgba(218,165,32,0.3)' }} data-testid="maintenance-active-badge">
            Maintenance mode is ACTIVE — only admins can access the site.
          </div>
        )}
      </Card>

      {/* BLOCK 473: Great Disconnect Migration */}
      <Card className="p-6 border-red-200 max-w-md mt-4" data-testid="great-disconnect-section">
        <h3 className="font-heading text-lg mb-1 text-red-700">The Great Disconnect</h3>
        <p className="text-xs text-muted-foreground mb-4">
          Purge all manually-entered Discogs credentials, reset migration flags, and temporarily hide unverified listings.
        </p>
        {disconnectResult ? (
          <div className="text-xs space-y-1 bg-red-50 p-3 rounded-lg border border-red-200" data-testid="disconnect-result">
            <p className="font-semibold text-red-700">Migration complete:</p>
            <p>Users reset: {disconnectResult.users_reset}</p>
            <p>Tokens deleted: {disconnectResult.tokens_deleted}</p>
            <p>Listings hidden: {disconnectResult.listings_hidden}</p>
          </div>
        ) : (
          <Button
            variant="destructive"
            onClick={async () => {
              if (!window.confirm('This will disconnect ALL users from Discogs and hide unverified listings. Are you sure?')) return;
              setRunningDisconnect(true);
              try {
                const r = await axios.post(`${API}/admin/great-disconnect`, {}, { headers });
                setDisconnectResult(r.data);
                toast.success('Great Disconnect migration complete');
              } catch (err) {
                toast.error(err.response?.data?.detail || 'Migration failed');
              } finally {
                setRunningDisconnect(false);
              }
            }}
            disabled={runningDisconnect}
            className="rounded-full gap-2"
            data-testid="great-disconnect-btn"
          >
            {runningDisconnect ? <Loader2 className="w-4 h-4 animate-spin" /> : <AlertTriangle className="w-4 h-4" />}
            Run Great Disconnect
          </Button>
        )}
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
    {[1, 2, 3].map(i => <div key={i} className="h-16 bg-honey/10 rounded-xl honey-shimmer" />)}
  </div>
);

const fmtDate = (iso) => {
  try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
  catch { return iso; }
};

// ═══════════════════════════════════════════════
// OFF-PLATFORM ALERTS SECTION
// ═══════════════════════════════════════════════
const OffPlatformAlertsSection = ({ API, headers }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/admin/offplatform-alerts`, { headers });
      setAlerts(resp.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, headers]);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  const dismiss = async (alertId) => {
    try {
      await axios.put(`${API}/admin/offplatform-alerts/${alertId}/dismiss`, {}, { headers });
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'dismissed' } : a));
      toast.success('Alert dismissed');
    } catch { toast.error('Failed to dismiss'); }
  };

  if (loading) return <LoadingSkeleton />;

  const openAlerts = alerts.filter(a => a.status === 'open');
  const dismissedAlerts = alerts.filter(a => a.status === 'dismissed');

  return (
    <div className="space-y-6" data-testid="offplatform-alerts-section">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-xl text-[#2A1A06]">Off-Platform Payment Alerts</h2>
          <p className="text-sm text-[#8A6B4A] mt-1">Listings flagged for mentioning outside payment methods</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-yellow-100 text-yellow-700">
          {openAlerts.length} open
        </span>
      </div>

      {alerts.length === 0 ? (
        <Card className="p-8 text-center border-[#C8861A]/15">
          <Flag className="w-10 h-10 text-[#C8861A]/30 mx-auto mb-3" />
          <p className="text-[#8A6B4A] text-sm">No off-platform alerts yet</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {[...openAlerts, ...dismissedAlerts].map(alert => (
            <Card key={alert.id} className={`p-4 border-[#C8861A]/15 ${alert.status === 'dismissed' ? 'opacity-50' : ''}`} data-testid={`offplatform-alert-${alert.id}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-sm font-medium text-[#2A1A06]">@{alert.username}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${alert.status === 'open' ? 'bg-yellow-100 text-yellow-700' : 'bg-stone-100 text-stone-500'}`}>
                      {alert.status}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {(alert.keywords || []).map(kw => (
                      <span key={kw} className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-red-50 text-red-600 border border-red-200">
                        {kw}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-[#8A6B4A] line-clamp-2">{alert.description_snippet}</p>
                  <p className="text-[10px] text-[#8A6B4A]/60 mt-1">{fmtDate(alert.created_at)}</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <a href={`/honeypot/listing/${alert.listing_id}`} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-[#C8861A] hover:underline whitespace-nowrap">
                    View Listing
                  </a>
                  {alert.status === 'open' && (
                    <Button size="sm" variant="outline" onClick={() => dismiss(alert.id)}
                      className="text-xs h-7 rounded-full border-[#C8861A]/30 text-[#8A6B4A]"
                      data-testid={`dismiss-alert-${alert.id}`}>
                      Dismiss
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════
// USER MANAGEMENT SECTION
// ═══════════════════════════════════════════════
const UserManagementSection = ({ API, headers }) => {
  const { user: currentAdmin } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [confirmModal, setConfirmModal] = useState(null); // { userId, username, action: 'grant'|'revoke' }
  const [removeModal, setRemoveModal] = useState(null); // { userId, username }
  const [actionLoading, setActionLoading] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (roleFilter !== 'all') params.append('role_filter', roleFilter);
      const res = await axios.get(`${API}/admin/users?${params}`, { headers });
      setUsers(res.data);
    } catch { toast.error('could not load users.'); }
    finally { setLoading(false); }
  }, [API, headers, search, roleFilter]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const handleRoleChange = async () => {
    if (!confirmModal) return;
    setActionLoading(true);
    try {
      const isAdmin = confirmModal.action === 'grant';
      await axios.post(`${API}/admin/users/role`, { user_id: confirmModal.userId, is_admin: isAdmin }, { headers });
      toast.success(`@${confirmModal.username} is now ${isAdmin ? 'an admin' : 'a standard user'}.`);
      setConfirmModal(null);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'could not update role.');
    } finally { setActionLoading(false); }
  };

  const handleRemoveUser = async () => {
    if (!removeModal) return;
    setActionLoading(true);
    try {
      await axios.delete(`${API}/admin/users/${removeModal.userId}`, { headers });
      toast.success(`@${removeModal.username} has been removed.`);
      setRemoveModal(null);
      setUsers(prev => prev.filter(u => u.id !== removeModal.userId));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'could not remove user.');
    } finally { setActionLoading(false); }
  };

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—';

  return (
    <div data-testid="user-management-section">
      {/* Search + filter + user count */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by username or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 border-honey/50"
            data-testid="user-search"
          />
        </div>
        <div className="flex gap-1 items-center">
          {['all', 'admin', 'standard'].map(f => (
            <Button key={f} size="sm"
              variant={roleFilter === f ? 'default' : 'outline'}
              onClick={() => setRoleFilter(f)}
              className={`rounded-full text-xs capitalize ${roleFilter === f ? 'bg-[#E8A820] text-[#2A1A06] hover:bg-[#C8861A]' : ''}`}
              data-testid={`filter-${f}`}>
              {f === 'all' ? 'All Users' : f === 'admin' ? 'Admins' : 'Standard'}
            </Button>
          ))}
          {!loading && (
            <span className="ml-2 inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#E8A820]/10 text-[#C8861A] border border-[#C8861A]/20 whitespace-nowrap" data-testid="user-count-badge">
              <Users className="w-3 h-3 mr-1" />{users.length} {users.length === 1 ? 'user' : 'users'}
            </span>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-honey-amber" /></div>
      ) : users.length === 0 ? (
        <Card className="p-8 text-center border-honey/30">
          <Users className="w-10 h-10 text-honey/40 mx-auto mb-3" />
          <p className="text-muted-foreground text-sm">No users found.</p>
        </Card>
      ) : (
        <div className="border border-honey/20 rounded-xl overflow-x-auto bg-white">
          {/* Header */}
          <div className="hidden sm:grid sm:grid-cols-[1fr_1fr_100px_120px_70px_120px] gap-3 px-4 py-2.5 bg-honey/5 border-b border-honey/15 text-xs font-medium text-[#8A6B4A] min-w-[700px]">
            <span>Username</span><span>Email</span><span>Joined</span><span>Title</span><span>Role</span><span className="text-right">Actions</span>
          </div>
          {/* Rows */}
          <div className="divide-y divide-[#C8861A]/10">
            {users.map(u => (
              <div key={u.id} className="flex flex-col sm:grid sm:grid-cols-[1fr_1fr_100px_120px_70px_120px] gap-1 sm:gap-3 px-4 py-3 items-start sm:items-center hover:bg-honey/5 transition-colors min-w-[700px]"
                data-testid={`user-row-${u.username}`}>
                <div className="flex items-center gap-2 min-w-0">
                  <img src={resolveImageUrl(u.avatar_url)} alt="" className="w-7 h-7 rounded-full shrink-0" />
                  <Link to={`/profile/${u.username}`} className="text-sm font-medium truncate hover:underline" style={{ color: '#C8861A' }} data-testid={`admin-user-link-${u.username}`}>@{u.username}</Link>
                  {(u.is_verified || u.golden_hive) && <span className="shrink-0 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">Verified</span>}
                  {u.is_gold_member && <span className="shrink-0 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-amber-100 text-amber-700 border border-amber-200">Gold</span>}
                </div>
                <span className="text-xs text-muted-foreground break-all">{u.email}</span>
                <span className="text-xs text-muted-foreground">{fmtDate(u.created_at)}</span>
                <Input
                  defaultValue={u.title_label || ''}
                  placeholder="title label"
                  className="h-7 text-xs border-honey/30 w-full"
                  data-testid={`title-label-input-${u.username}`}
                  onBlur={async (e) => {
                    const val = e.target.value.trim();
                    if (val === (u.title_label || '')) return;
                    try {
                      await axios.put(`${API}/admin/users/title-label`, { user_id: u.id, title_label: val || null }, { headers });
                      toast.success(`Title label updated for @${u.username}`);
                      u.title_label = val || null;
                    } catch { toast.error('Failed to update title label'); }
                  }}
                  onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }}
                />
                <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold w-fit ${
                  u.is_admin ? 'bg-[#E8A820]/15 text-[#C8861A] border border-[#C8861A]/30' : 'bg-gray-100 text-gray-600'
                }`}>
                  {u.is_admin ? 'Admin' : 'User'}
                </span>
                <div className="flex items-center gap-1.5 justify-end min-w-[100px]">
                  <button
                    onClick={async () => {
                      if (!window.confirm(`Send a temporary password to @${u.username} (${u.email})?`)) return;
                      try {
                        const res = await axios.post(`${API}/admin/users/${u.id}/temp-password`, {}, { headers });
                        toast.success(res.data.detail || `Temp password sent to @${u.username}`);
                      } catch (err) { toast.error(err.response?.data?.detail || 'Failed to send temp password'); }
                    }}
                    className="p-1.5 rounded-full text-[#C8861A] hover:bg-[#C8861A]/10 transition-colors"
                    title="Send temp password"
                    data-testid={`temp-pw-${u.username}`}
                  >
                    <KeyRound className="w-3.5 h-3.5" />
                  </button>
                  {u.is_admin ? (
                    <Button size="sm" variant="outline"
                      onClick={() => setConfirmModal({ userId: u.id, username: u.username, action: 'revoke' })}
                      className="text-[11px] h-7 rounded-full border-[#8A6B4A]/30 text-[#8A6B4A]"
                      data-testid={`revoke-admin-${u.username}`}>
                      Revoke Admin
                    </Button>
                  ) : (
                    <Button size="sm" variant="outline"
                      onClick={() => setConfirmModal({ userId: u.id, username: u.username, action: 'grant' })}
                      className="text-[11px] h-7 rounded-full border-[#C8861A]/30 text-[#C8861A]"
                      data-testid={`make-admin-${u.username}`}>
                      Make Admin
                    </Button>
                  )}
                  <button
                    onClick={() => setRemoveModal({ userId: u.id, username: u.username })}
                    className="p-1.5 rounded-full text-stone-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                    title="Remove user"
                    data-testid={`remove-user-${u.username}`}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setConfirmModal(null)}>
          <div className="bg-[#FAF6EE] rounded-2xl p-6 max-w-sm mx-4 shadow-xl" onClick={e => e.stopPropagation()} data-testid="role-confirm-modal">
            <h3 className="font-heading text-xl text-vinyl-black mb-3">
              {confirmModal.action === 'grant' ? 'Grant Admin Access?' : 'Revoke Admin Access?'}
            </h3>
            <p className="text-sm text-vinyl-black/70 font-serif italic leading-relaxed mb-5">
              {confirmModal.action === 'grant'
                ? `Are you sure you want to grant admin access to @${confirmModal.username}? They will have full access to the admin panel including user data, listings, disputes, and all settings.`
                : `Are you sure you want to revoke admin access from @${confirmModal.username}? They will lose access to the admin panel.`}
            </p>
            <div className="flex flex-col gap-2">
              <Button
                variant="outline"
                onClick={handleRoleChange}
                disabled={actionLoading}
                className="w-full rounded-full border-vinyl-black/30 text-vinyl-black"
                data-testid="confirm-role-btn">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {confirmModal.action === 'grant' ? 'Yes, grant access' : 'Yes, revoke access'}
              </Button>
              <Button
                onClick={() => setConfirmModal(null)}
                className="w-full bg-[#E8A820] text-vinyl-black hover:bg-[#C8861A] rounded-full"
                data-testid="cancel-role-btn">
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Remove User Confirmation Modal */}
      {removeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setRemoveModal(null)}>
          <div className="bg-[#FAF6EE] rounded-2xl p-6 max-w-sm mx-4 shadow-xl" onClick={e => e.stopPropagation()} data-testid="remove-user-modal">
            <h3 className="font-heading text-xl text-vinyl-black mb-3">Remove User?</h3>
            <p className="text-sm text-vinyl-black/70 font-serif italic leading-relaxed mb-5">
              Are you sure you want to remove <strong>@{removeModal.username}</strong>? This will permanently delete their account, posts, comments, collection, and all associated data. This action cannot be undone.
            </p>
            <div className="flex flex-col gap-2">
              <Button
                variant="outline"
                onClick={handleRemoveUser}
                disabled={actionLoading}
                className="w-full rounded-full border-red-300 text-red-600 hover:bg-red-50"
                data-testid="confirm-remove-btn">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Trash2 className="w-4 h-4 mr-2" />}
                Yes, remove user
              </Button>
              <Button
                onClick={() => setRemoveModal(null)}
                className="w-full bg-[#E8A820] text-vinyl-black hover:bg-[#C8861A] rounded-full"
                data-testid="cancel-remove-btn">
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
// FEEDBACK & BUG REPORTS
// ═══════════════════════════════════════════════
const FeedbackSection = ({ API, headers }) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all' | 'bug' | 'feedback'

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const params = filter !== 'all' ? `?mode=${filter}` : '';
        const resp = await axios.get(`${API}/reports/admin/feedback${params}`, { headers });
        setEntries(resp.data.entries || []);
      } catch { toast.error('Failed to load feedback'); }
      finally { setLoading(false); }
    };
    load();
  }, [API, headers, filter]);

  const FILTERS = [
    { key: 'all', label: 'All' },
    { key: 'bug', label: 'Report a Bug' },
    { key: 'feedback', label: 'General Feedback' },
  ];

  return (
    <div data-testid="admin-feedback-section">
      <h2 className="font-heading text-xl text-vinyl-black mb-4">Feedback & Bug Reports</h2>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4" data-testid="feedback-filters">
        {FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
              filter === f.key
                ? 'bg-amber-100 text-amber-800 border-amber-300 shadow-sm'
                : 'bg-white text-stone-500 border-stone-200 hover:border-amber-200'
            }`}
            data-testid={`feedback-filter-${f.key}`}
          >
            {f.label}
            {f.key === 'all' && ` (${entries.length})`}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-amber-500" /></div>
      ) : entries.length === 0 ? (
        <p className="text-sm text-stone-400 py-6 text-center">No submissions yet.</p>
      ) : (
        <div className="space-y-3">
          {entries.map(entry => (
            <Card key={entry.report_id} className="p-4 border-stone-200/60" data-testid={`feedback-entry-${entry.report_id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  {/* Type badge + user */}
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium border ${
                      entry.target_type === 'feedback'
                        ? 'bg-violet-100 text-violet-700 border-violet-200'
                        : 'bg-orange-100 text-orange-700 border-orange-200'
                    }`} data-testid="feedback-type-badge">
                      {entry.target_type === 'feedback' ? (
                        <><Heart className="w-3 h-3" /> General Feedback</>
                      ) : (
                        <><AlertTriangle className="w-3 h-3" /> Bug Report</>
                      )}
                    </span>
                    {entry.reporter?.username && (
                      <span className="text-xs text-stone-500">@{entry.reporter.username}</span>
                    )}
                    {entry.reporter?.email && (
                      <span className="text-[10px] text-stone-400">{entry.reporter.email}</span>
                    )}
                  </div>

                  {/* Reason (bug reports only) */}
                  {entry.target_type === 'bug' && entry.reason && (
                    <p className="text-xs text-amber-700 font-medium mb-1">
                      Reason: {entry.reason}
                    </p>
                  )}

                  {/* Message */}
                  <p className="text-sm text-stone-700 whitespace-pre-wrap leading-relaxed">
                    {entry.notes}
                  </p>

                  {/* Screenshot */}
                  {entry.screenshot_url && (
                    <a href={entry.screenshot_url} target="_blank" rel="noopener noreferrer" className="inline-block mt-2">
                      <img src={entry.screenshot_url} alt="Screenshot" className="w-20 h-20 object-cover rounded border border-stone-200" />
                    </a>
                  )}

                  {/* Meta */}
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-stone-400">
                    <span>{new Date(entry.created_at).toLocaleString()}</span>
                    {entry.page_url && <span className="truncate max-w-[200px]">{entry.page_url}</span>}
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      entry.status === 'OPEN' ? 'bg-yellow-100 text-yellow-700' :
                      entry.status === 'REVIEWING' ? 'bg-blue-100 text-blue-700' :
                      'bg-green-100 text-green-700'
                    }`}>{entry.status}</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};


// THE WATCHTOWER — REPORT MODERATION QUEUE
// ═══════════════════════════════════════════════
const WatchtowerSection = ({ API, headers }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [processing, setProcessing] = useState(null);

  const fetchReports = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filter) params.set('target_type', filter);
      if (statusFilter) params.set('status', statusFilter);
      const resp = await axios.get(`${API}/reports/admin/queue?${params.toString()}`, { headers });
      setReports(resp.data);
    } catch { toast.error('Failed to load reports'); }
    finally { setLoading(false); }
  }, [API, headers, filter, statusFilter]);

  useEffect(() => { fetchReports(); }, [fetchReports]);

  const handleAction = async (reportId, action) => {
    setProcessing(reportId);
    try {
      await axios.post(`${API}/reports/admin/${reportId}/action`, { action }, { headers });
      toast.success(`Action '${action}' applied`);
      fetchReports();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setProcessing(null); }
  };

  const typeColors = { listing: 'bg-blue-100 text-blue-700', seller: 'bg-purple-100 text-purple-700', order: 'bg-orange-100 text-orange-700', bug: 'bg-gray-100 text-gray-700' };
  const statusColors = { OPEN: 'bg-red-100 text-red-700', REVIEWING: 'bg-amber-100 text-amber-700', RESOLVED: 'bg-emerald-100 text-emerald-700', DISMISSED: 'bg-gray-100 text-gray-500' };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-honey" /></div>;

  return (
    <div className="space-y-4" data-testid="admin-watchtower-section">
      <div className="flex items-center gap-3 flex-wrap">
        <h2 className="font-heading text-xl text-vinyl-black">The Watchtower</h2>
        <span className="text-xs text-muted-foreground bg-amber-50 px-2 py-1 rounded-full border border-amber-200">{reports.length} reports</span>
      </div>

      <div className="flex gap-2 flex-wrap">
        {['', 'listing', 'seller', 'order', 'bug'].map(t => (
          <button key={t || 'all'} onClick={() => setFilter(t)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${filter === t ? 'bg-honey text-vinyl-black' : 'bg-honey/10 text-muted-foreground hover:bg-honey/20'}`}
            data-testid={`watchtower-filter-${t || 'all'}`}>{t || 'All'}
          </button>
        ))}
        <div className="w-px h-6 bg-honey/20 self-center" />
        {['', 'OPEN', 'REVIEWING', 'RESOLVED'].map(s => (
          <button key={s || 'any'} onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${statusFilter === s ? 'bg-honey text-vinyl-black' : 'bg-honey/10 text-muted-foreground hover:bg-honey/20'}`}
            data-testid={`watchtower-status-${s || 'any'}`}>{s || 'Any Status'}
          </button>
        ))}
      </div>

      {reports.length === 0 ? (
        <Card className="p-8 text-center border-honey/20">
          <AlertTriangle className="w-8 h-8 text-honey mx-auto mb-3 opacity-50" />
          <p className="text-sm text-muted-foreground">No reports matching filters</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {reports.map(r => (
            <Card key={r.report_id} className="p-4 border-honey/20" data-testid={`report-card-${r.report_id}`}>
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${typeColors[r.target_type] || ''}`}>{r.target_type}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${statusColors[r.status] || ''}`}>{r.status}</span>
                    <span className="text-xs text-muted-foreground">by @{r.reporter?.username || r.reporter_username}</span>
                    <span className="text-xs text-muted-foreground">{new Date(r.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="text-sm font-medium">{r.reason}</p>
                  {r.notes && <p className="text-xs text-muted-foreground mt-0.5">{r.notes}</p>}
                  {r.target_info && (
                    <p className="text-xs text-amber-700 mt-0.5">
                      {r.target_info.artist && `${r.target_info.artist} - ${r.target_info.album}`}
                      {r.target_info.username && `@${r.target_info.username}`}
                    </p>
                  )}
                </div>
                <div className="flex gap-1.5 shrink-0 flex-wrap">
                  {r.status === 'OPEN' && (
                    <>
                      <Button size="sm" onClick={() => handleAction(r.report_id, 'REVIEWING')} disabled={processing === r.report_id}
                        className="rounded-full text-xs bg-amber-500 text-white hover:bg-amber-600 h-7" data-testid={`watchtower-review-${r.report_id}`}>Review</Button>
                      <Button size="sm" variant="outline" onClick={() => handleAction(r.report_id, 'DISMISSED')} disabled={processing === r.report_id}
                        className="rounded-full text-xs h-7" data-testid={`watchtower-dismiss-${r.report_id}`}>Dismiss</Button>
                    </>
                  )}
                  {r.status === 'REVIEWING' && (
                    <>
                      <Button size="sm" onClick={() => handleAction(r.report_id, 'RESOLVED')} disabled={processing === r.report_id}
                        className="rounded-full text-xs bg-emerald-600 text-white hover:bg-emerald-700 h-7" data-testid={`watchtower-resolve-${r.report_id}`}>Resolve</Button>
                      {r.target_type === 'listing' && (
                        <Button size="sm" variant="outline" onClick={() => handleAction(r.report_id, 'REMOVE_LISTING')} disabled={processing === r.report_id}
                          className="rounded-full text-xs text-red-600 border-red-300 h-7" data-testid={`watchtower-remove-listing-${r.report_id}`}>Remove Listing</Button>
                      )}
                      {r.target_type === 'seller' && (
                        <>
                          <Button size="sm" variant="outline" onClick={() => handleAction(r.report_id, 'WARN_SELLER')} disabled={processing === r.report_id}
                            className="rounded-full text-xs text-amber-600 border-amber-300 h-7" data-testid={`watchtower-warn-${r.report_id}`}>Warn</Button>
                          <Button size="sm" variant="outline" onClick={() => handleAction(r.report_id, 'SUSPEND_SELLER')} disabled={processing === r.report_id}
                            className="rounded-full text-xs text-red-600 border-red-300 h-7" data-testid={`watchtower-suspend-${r.report_id}`}>Suspend</Button>
                        </>
                      )}
                      <Button size="sm" variant="outline" onClick={() => handleAction(r.report_id, 'DISMISSED')} disabled={processing === r.report_id}
                        className="rounded-full text-xs h-7">Dismiss</Button>
                    </>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};


// ═══════════════════════════════════════════════
// THE GATE — VERIFICATION QUEUE
// ═══════════════════════════════════════════════
const GateSection = ({ API, headers }) => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unblurred, setUnblurred] = useState({});
  const [processing, setProcessing] = useState(null);

  const fetchQueue = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/verification/admin/queue`, { headers });
      setQueue(resp.data);
    } catch { toast.error('Failed to load verification queue'); }
    finally { setLoading(false); }
  }, [API, headers]);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  const handleUnblur = async (requestId) => {
    try {
      const resp = await axios.get(`${API}/verification/admin/unblur/${requestId}`, { headers });
      setUnblurred(prev => ({ ...prev, [requestId]: resp.data.original_image_url }));
    } catch { toast.error('Failed to unblur'); }
  };

  const [denyTarget, setDenyTarget] = useState(null);
  const [denyReason, setDenyReason] = useState('');

  const QUICK_REASONS = ['Blurry', 'Expired', 'Wrong Document', 'Name Does Not Match'];

  const handleApprove = async (requestId) => {
    setProcessing(requestId);
    try {
      await axios.post(`${API}/verification/admin/approve/${requestId}`, {}, { headers });
      toast.success('Verification approved — Golden Hive granted');
      fetchQueue();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setProcessing(null); }
  };

  const openDenyModal = (requestId) => {
    setDenyTarget(requestId);
    setDenyReason('');
  };

  const submitDeny = async () => {
    if (!denyTarget) return;
    setProcessing(denyTarget);
    try {
      await axios.post(`${API}/verification/admin/deny/${denyTarget}`, { reason: denyReason, notes: denyReason }, { headers });
      toast.success('Verification denied');
      fetchQueue();
      setDenyTarget(null);
      setDenyReason('');
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setProcessing(null); }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-honey" /></div>;

  return (
    <div className="space-y-4" data-testid="admin-gate-section">
      <div className="flex items-center gap-3">
        <h2 className="font-heading text-xl text-vinyl-black">The Gate</h2>
        <span className="text-xs text-muted-foreground bg-amber-50 px-2 py-1 rounded-full border border-amber-200">{queue.length} pending</span>
      </div>

      {queue.length === 0 ? (
        <Card className="p-8 text-center border-honey/20">
          <Shield className="w-8 h-8 text-honey mx-auto mb-3 opacity-50" />
          <p className="text-sm text-muted-foreground">No pending verification requests</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {queue.map(req => (
            <Card key={req.id} className="p-4 border-honey/20" data-testid={`gate-request-${req.id}`}>
              <div className="flex items-start gap-4">
                {/* ID Photo (blurred by default) */}
                <div className="w-32 h-24 rounded-lg overflow-hidden bg-gray-100 border border-honey/20 shrink-0 relative group">
                  <img
                    src={unblurred[req.id] ? resolveImageUrl(unblurred[req.id]) : resolveImageUrl(req.blurred_image_url)}
                    alt="Verification ID"
                    className="w-full h-full object-cover"
                  />
                  {!unblurred[req.id] && (
                    <button
                      onClick={() => handleUnblur(req.id)}
                      className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity"
                      data-testid={`unblur-btn-${req.id}`}
                    >
                      <span className="text-white text-xs font-medium bg-black/60 px-3 py-1.5 rounded-full">Unblur</span>
                    </button>
                  )}
                </div>

                {/* User Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {req.user?.profile_pic && (
                      <img src={resolveImageUrl(req.user.profile_pic)} alt="" className="w-6 h-6 rounded-full object-cover" />
                    )}
                    <span className="font-heading text-sm font-bold">@{req.user?.username || req.username}</span>
                    {req.user?.country && <span className="text-xs">{req.user.country}</span>}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{req.user?.email}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Submitted {new Date(req.submitted_at).toLocaleDateString()}</p>
                </div>

                {/* Actions */}
                <div className="flex gap-2 shrink-0">
                  <Button
                    onClick={() => handleApprove(req.id)}
                    disabled={processing === req.id}
                    className="bg-emerald-600 text-white hover:bg-emerald-700 rounded-full text-xs px-4"
                    data-testid={`approve-btn-${req.id}`}
                  >
                    {processing === req.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 mr-1" />}
                    Approve
                  </Button>
                  <Button
                    onClick={() => openDenyModal(req.id)}
                    disabled={processing === req.id}
                    variant="outline"
                    className="border-red-300 text-red-600 hover:bg-red-50 rounded-full text-xs px-4"
                    data-testid={`deny-btn-${req.id}`}
                  >
                    <X className="w-3 h-3 mr-1" />
                    Deny
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Denial Reasons Modal */}
      <Dialog open={!!denyTarget} onOpenChange={(open) => { if (!open) { setDenyTarget(null); setDenyReason(''); } }}>
        <DialogContent className="sm:max-w-sm" aria-describedby="deny-reason-desc">
          <DialogHeader>
            <DialogTitle className="font-heading" style={{ color: '#D98C2F' }}>
              Reason for Denial
            </DialogTitle>
            <p id="deny-reason-desc" className="text-sm text-muted-foreground mt-1">
              This will be included in the user's notification and email.
            </p>
          </DialogHeader>
          <div className="space-y-3 pt-2" data-testid="deny-reason-modal">
            <div className="flex flex-wrap gap-2">
              {QUICK_REASONS.map(r => (
                <button
                  key={r}
                  onClick={() => setDenyReason(r)}
                  className="text-xs px-3 py-1.5 rounded-full font-medium transition-all"
                  style={{
                    background: denyReason === r ? 'linear-gradient(135deg, #FFB300, #FFA000)' : '#FFF8E1',
                    color: denyReason === r ? '#000' : '#3E2723',
                    border: denyReason === r ? '2px solid #FFA000' : '2px solid rgba(255,179,0,0.2)',
                  }}
                  data-testid={`quick-reason-${r.toLowerCase().replace(/\s/g, '-')}`}
                >
                  {r}
                </button>
              ))}
            </div>
            <Input
              placeholder="Or type a custom reason..."
              value={denyReason}
              onChange={(e) => setDenyReason(e.target.value)}
              className="border-honey/50"
              data-testid="deny-reason-input"
            />
            <div className="flex gap-2 pt-1">
              <Button
                onClick={() => { setDenyTarget(null); setDenyReason(''); }}
                variant="outline"
                className="flex-1 rounded-full"
              >
                Cancel
              </Button>
              <Button
                onClick={submitDeny}
                disabled={processing === denyTarget}
                className="flex-1 rounded-full text-white"
                style={{ background: 'linear-gradient(135deg, #EF4444, #DC2626)' }}
                data-testid="submit-deny-btn"
              >
                {processing === denyTarget ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Deny Verification'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}; 

const GoldenHiveAdminSection = ({ API, headers }) => {
  const [search, setSearch] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [processing, setProcessing] = useState(null);

  const handleSearch = async () => {
    if (!search.trim()) return;
    setSearching(true);
    try {
      const r = await axios.get(`${API}/admin/users?q=${encodeURIComponent(search)}&limit=10`, { headers });
      setResults(r.data || []);
    } catch { toast.error('Search failed'); }
    finally { setSearching(false); }
  };

  const handleVerify = async (userId, verified) => {
    setProcessing(userId);
    try {
      await axios.post(`${API}/admin/verify/${userId}`, { verified }, { headers });
      toast.success(verified ? 'User verified.' : 'Verification revoked.');
      setResults(prev => prev.map(u => u.id === userId ? { ...u, is_verified: verified } : u));
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed.'); }
    finally { setProcessing(null); }
  };

  return (
    <div className="space-y-6" data-testid="admin-verification-section">
      <div>
        <h2 className="font-heading text-xl text-vinyl-black mb-1">Verification — Manual Control</h2>
        <p className="text-sm text-muted-foreground">Search for a user to manually grant or revoke their Verified badge.</p>
      </div>
      <div className="flex gap-2">
        <Input value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder="Search by username or email" className="rounded-xl" data-testid="verify-admin-search" />
        <Button onClick={handleSearch} disabled={searching} className="rounded-xl bg-honey text-vinyl-black hover:bg-honey-amber">
          {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
        </Button>
      </div>
      {results.length > 0 && (
        <div className="space-y-3">
          {results.map(u => (
            <Card key={u.id} className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">@{u.username}</p>
                  <p className="text-xs text-muted-foreground">{u.email}</p>
                  <div className="flex gap-1.5 mt-1">
                    {u.is_verified && <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">Verified</span>}
                    {u.golden_hive_verified && <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-amber-100 text-amber-700 border border-amber-200">Legacy Golden</span>}
                  </div>
                </div>
                <div className="flex gap-2">
                  {!u.is_verified ? (
                    <Button size="sm" onClick={() => handleVerify(u.id, true)} disabled={processing === u.id}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-full text-xs px-4" data-testid={`verify-user-${u.id}`}>
                      <Check className="w-3 h-3 mr-1" /> Verify
                    </Button>
                  ) : (
                    <Button size="sm" variant="outline" onClick={() => handleVerify(u.id, false)} disabled={processing === u.id}
                      className="border-red-300 text-red-600 hover:bg-red-50 rounded-full text-xs px-4" data-testid={`revoke-verify-${u.id}`}>
                      <X className="w-3 h-3 mr-1" /> Revoke
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};


export default AdminPage;

// ═══════════════════════════════════════════════
// TEST LISTINGS SECTION
// ═══════════════════════════════════════════════
const TestListingsSection = ({ API, headers }) => {
  const [listings, setListings] = useState([]);
  const [allListings, setAllListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [toggling, setToggling] = useState(null);

  const fetchTestListings = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/admin/test-listings`, { headers });
      setListings(r.data);
    } catch { }
  }, [API, headers]);

  const fetchAllActive = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/listings?limit=200`, { headers });
      setAllListings(r.data);
    } catch { }
  }, [API, headers]);

  useEffect(() => {
    Promise.all([fetchTestListings(), fetchAllActive()]).finally(() => setLoading(false));
  }, [fetchTestListings, fetchAllActive]);

  const toggleFlag = async (listingId, newVal) => {
    setToggling(listingId);
    try {
      await axios.patch(`${API}/listings/${listingId}/test-flag`, { is_test_listing: newVal }, { headers });
      toast.success(newVal ? 'Marked as test listing' : 'Unmarked — now visible to all');
      await Promise.all([fetchTestListings(), fetchAllActive()]);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update');
    } finally {
      setToggling(null);
    }
  };

  const filteredActive = allListings.filter(l =>
    !l.is_test_listing && (
      !search ||
      l.album?.toLowerCase().includes(search.toLowerCase()) ||
      l.artist?.toLowerCase().includes(search.toLowerCase()) ||
      l.user?.username?.toLowerCase().includes(search.toLowerCase())
    )
  );

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-amber-500" /></div>;

  return (
    <div className="space-y-6" data-testid="admin-test-listings">
      <div>
        <h2 className="font-heading text-xl text-[#2A1A06] mb-1">Test Listing Manager</h2>
        <p className="text-sm text-[#8A6B4A]">Flag listings as test so they're hidden from regular users. Only you and admins can see them.</p>
      </div>

      {/* Currently flagged test listings */}
      <div>
        <h3 className="text-sm font-semibold text-[#2A1A06] mb-3 flex items-center gap-2">
          <Flag className="w-4 h-4 text-red-500" /> Flagged Test Listings ({listings.length})
        </h3>
        {listings.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">No test listings flagged.</p>
        ) : (
          <div className="space-y-2">
            {listings.map(l => (
              <Card key={l.id} className="p-3 flex items-center gap-3 border-red-200 bg-red-50/40" data-testid={`test-listing-${l.id}`}>
                {l.photo_urls?.[0] && (
                  <img src={l.photo_urls[0]} alt="" className="w-12 h-12 rounded-lg object-cover border border-red-200" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#2A1A06] truncate">{l.artist} — {l.album}</p>
                  <p className="text-xs text-muted-foreground">
                    {l.user?.username ? `@${l.user.username}` : 'Unknown'} · ${l.price || 0} · {l.status}
                  </p>
                </div>
                <Button size="sm" variant="outline"
                  onClick={() => toggleFlag(l.id, false)}
                  disabled={toggling === l.id}
                  className="border-green-300 text-green-700 hover:bg-green-50 rounded-full text-xs px-3"
                  data-testid={`unflag-test-${l.id}`}>
                  {toggling === l.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 mr-1" />}
                  Unflag
                </Button>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Search & flag active listings */}
      <div>
        <h3 className="text-sm font-semibold text-[#2A1A06] mb-3">Flag a Listing as Test</h3>
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search active listings by album, artist, or seller..."
            value={search} onChange={e => setSearch(e.target.value)}
            className="pl-9 border-[#C8861A]/30"
            data-testid="test-listing-search" />
        </div>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {filteredActive.slice(0, 20).map(l => (
            <Card key={l.id} className="p-3 flex items-center gap-3" data-testid={`active-listing-${l.id}`}>
              {l.photo_urls?.[0] && (
                <img src={l.photo_urls[0]} alt="" className="w-12 h-12 rounded-lg object-cover border border-stone-200" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#2A1A06] truncate">{l.artist} — {l.album}</p>
                <p className="text-xs text-muted-foreground">
                  {l.user?.username ? `@${l.user.username}` : 'Unknown'} · ${l.price || 0} · {l.listing_type}
                </p>
              </div>
              <Button size="sm" variant="outline"
                onClick={() => toggleFlag(l.id, true)}
                disabled={toggling === l.id}
                className="border-red-300 text-red-600 hover:bg-red-50 rounded-full text-xs px-3"
                data-testid={`flag-test-${l.id}`}>
                {toggling === l.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Flag className="w-3 h-3 mr-1" />}
                Mark Test
              </Button>
            </Card>
          ))}
          {filteredActive.length === 0 && <p className="text-sm text-muted-foreground py-4">No matching active listings.</p>}
        </div>
      </div>
    </div>
  );
};


// ═══════════════════════════════════════════════
// BEEKEEPER SECTION
// ═══════════════════════════════════════════════
const BeekeeperSection = ({ API, headers }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/admin/beekeeper`, { headers })
      .then(r => setData(r.data))
      .catch(() => toast.error('Failed to load Beekeeper metrics.'))
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-[#C8861A]" /></div>;
  if (!data) return null;

  return (
    <div className="space-y-6" data-testid="beekeeper-section">
      <h2 className="font-heading text-xl text-vinyl-black">Honeypot Teaser Metrics</h2>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="p-5 border border-[#F5E6CC]" data-testid="beekeeper-notify-count">
          <p className="text-xs text-[#8A6B4A] mb-1">Notify Me Signups</p>
          <p className="text-3xl font-bold text-[#2A1A06]">{data.notify_count}</p>
        </Card>
        <Card className="p-5 border border-[#F5E6CC]" data-testid="beekeeper-gold-count">
          <p className="text-xs text-[#8A6B4A] mb-1">Gold Members</p>
          <p className="text-3xl font-bold text-[#2A1A06]">{data.gold_member_count}</p>
        </Card>
      </div>

      {/* Daily views */}
      <div>
        <h3 className="font-medium text-[#2A1A06] mb-3 text-sm">Daily Teaser Views (last 30 days)</h3>
        {data.daily_views.length === 0 ? (
          <p className="text-sm text-muted-foreground" data-testid="beekeeper-no-views">No teaser views recorded yet.</p>
        ) : (
          <div className="overflow-x-auto" data-testid="beekeeper-views-table">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#F5E6CC]">
                  <th className="text-left py-2 pr-4 text-[#8A6B4A] font-medium">Date</th>
                  <th className="text-right py-2 text-[#8A6B4A] font-medium">Views</th>
                </tr>
              </thead>
              <tbody>
                {data.daily_views.map(({ date, views }) => (
                  <tr key={date} className="border-b border-[#F5E6CC]/50" data-testid={`beekeeper-row-${date}`}>
                    <td className="py-2 pr-4 text-[#2A1A06]">{date}</td>
                    <td className="py-2 text-right font-medium text-[#2A1A06]">{views}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
