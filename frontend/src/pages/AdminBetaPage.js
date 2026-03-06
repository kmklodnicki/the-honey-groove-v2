import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Loader2, Copy, Download, Plus, Users, Key, Check } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';

const AdminBetaPage = () => {
  usePageTitle('Admin · Beta & Invites');
  const { token, API } = useAuth();
  const [tab, setTab] = useState('signups');

  // Beta signups state
  const [signups, setSignups] = useState([]);
  const [signupsLoading, setSignupsLoading] = useState(true);
  const [editingNote, setEditingNote] = useState(null);
  const [noteValue, setNoteValue] = useState('');

  // Invite codes state
  const [codes, setCodes] = useState([]);
  const [codesLoading, setCodesLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchSignups = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/admin/beta-signups`, { headers });
      setSignups(res.data);
    } catch { /* handled */ }
    setSignupsLoading(false);
  }, [API, token]);

  const fetchCodes = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/admin/invite-codes`, { headers });
      setCodes(res.data);
    } catch { /* handled */ }
    setCodesLoading(false);
  }, [API, token]);

  useEffect(() => {
    fetchSignups();
    fetchCodes();
  }, [fetchSignups, fetchCodes]);

  const saveNote = async (id) => {
    try {
      await axios.patch(`${API}/admin/beta-signups/${id}/notes`, { notes: noteValue }, { headers });
      setSignups(signups.map(s => s.id === id ? { ...s, notes: noteValue } : s));
      setEditingNote(null);
      toast.success('Note saved');
    } catch { toast.error('Failed to save note'); }
  };

  const generateCodes = async (count) => {
    setGenerating(true);
    try {
      const res = await axios.post(`${API}/admin/invite-codes/generate`, { count }, { headers });
      setCodes([...res.data, ...codes]);
      toast.success(`Generated ${res.data.length} invite code(s)`);
    } catch { toast.error('Failed to generate codes'); }
    setGenerating(false);
  };

  const copyCode = (code) => {
    const url = `${window.location.origin}/join?code=${code}`;
    navigator.clipboard.writeText(url);
    toast.success('Invite link copied');
  };

  const exportCSV = async () => {
    try {
      const res = await axios.get(`${API}/admin/beta-signups/export`, {
        headers,
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'beta_signups.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch { toast.error('Failed to export CSV'); }
  };

  const formatDate = (iso) => {
    try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return iso; }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8" data-testid="admin-beta-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-6">Beta & Invite Management</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={tab === 'signups' ? 'default' : 'outline'}
          onClick={() => setTab('signups')}
          className={tab === 'signups' ? 'bg-honey text-vinyl-black' : ''}
          data-testid="admin-tab-signups"
        >
          <Users className="w-4 h-4 mr-2" /> Beta Signups ({signups.length})
        </Button>
        <Button
          variant={tab === 'codes' ? 'default' : 'outline'}
          onClick={() => setTab('codes')}
          className={tab === 'codes' ? 'bg-honey text-vinyl-black' : ''}
          data-testid="admin-tab-codes"
        >
          <Key className="w-4 h-4 mr-2" /> Invite Codes ({codes.length})
        </Button>
      </div>

      {/* Beta Signups Tab */}
      {tab === 'signups' && (
        <Card className="p-0 overflow-hidden border-honey/30">
          <div className="flex items-center justify-between p-4 border-b border-honey/20 bg-honey/5">
            <span className="font-heading text-lg">{signups.length} signup{signups.length !== 1 ? 's' : ''}</span>
            <Button variant="outline" size="sm" onClick={exportCSV} data-testid="export-csv-btn">
              <Download className="w-4 h-4 mr-2" /> Export CSV
            </Button>
          </div>
          {signupsLoading ? (
            <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-honey-amber" /></div>
          ) : signups.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">No signups yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="signups-table">
                <thead>
                  <tr className="border-b border-honey/20 text-left text-muted-foreground">
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Instagram</th>
                    <th className="px-4 py-3 font-medium">Email</th>
                    <th className="px-4 py-3 font-medium">Feature Interest</th>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {signups.map((s) => (
                    <tr key={s.id} className="border-b border-honey/10 hover:bg-honey/5">
                      <td className="px-4 py-3 font-medium">{s.first_name}</td>
                      <td className="px-4 py-3 text-honey-amber">@{s.instagram_handle}</td>
                      <td className="px-4 py-3">{s.email}</td>
                      <td className="px-4 py-3">{s.feature_interest}</td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatDate(s.submitted_at)}</td>
                      <td className="px-4 py-3 min-w-[200px]">
                        {editingNote === s.id ? (
                          <div className="flex gap-1">
                            <Input
                              value={noteValue}
                              onChange={(e) => setNoteValue(e.target.value)}
                              className="h-8 text-xs border-honey/30"
                              onKeyDown={(e) => e.key === 'Enter' && saveNote(s.id)}
                              autoFocus
                            />
                            <Button size="sm" variant="ghost" onClick={() => saveNote(s.id)} className="h-8 px-2">
                              <Check className="w-3 h-3" />
                            </Button>
                          </div>
                        ) : (
                          <button
                            onClick={() => { setEditingNote(s.id); setNoteValue(s.notes || ''); }}
                            className="text-left text-xs text-muted-foreground hover:text-vinyl-black cursor-pointer w-full min-h-[28px]"
                            data-testid={`note-edit-${s.id}`}
                          >
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

      {/* Invite Codes Tab */}
      {tab === 'codes' && (
        <Card className="p-0 overflow-hidden border-honey/30">
          <div className="flex items-center justify-between p-4 border-b border-honey/20 bg-honey/5 flex-wrap gap-2">
            <span className="font-heading text-lg">Invite Codes</span>
            <div className="flex gap-2 flex-wrap">
              <Button size="sm" onClick={() => generateCodes(1)} disabled={generating} className="bg-honey text-vinyl-black hover:bg-honey-amber" data-testid="gen-1-btn">
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Plus className="w-4 h-4 mr-1" /> 1 Code</>}
              </Button>
              <Button size="sm" variant="outline" onClick={() => generateCodes(10)} disabled={generating} data-testid="gen-10-btn">+ 10</Button>
              <Button size="sm" variant="outline" onClick={() => generateCodes(25)} disabled={generating} data-testid="gen-25-btn">+ 25</Button>
              <Button size="sm" variant="outline" onClick={() => generateCodes(50)} disabled={generating} data-testid="gen-50-btn">+ 50</Button>
            </div>
          </div>
          {codesLoading ? (
            <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-honey-amber" /></div>
          ) : codes.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">No invite codes generated yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="codes-table">
                <thead>
                  <tr className="border-b border-honey/20 text-left text-muted-foreground">
                    <th className="px-4 py-3 font-medium">Code</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Created</th>
                    <th className="px-4 py-3 font-medium">Used By</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {codes.map((c) => (
                    <tr key={c.id} className="border-b border-honey/10 hover:bg-honey/5">
                      <td className="px-4 py-3 font-mono text-sm font-medium">{c.code}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          c.status === 'unused' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatDate(c.created_at)}</td>
                      <td className="px-4 py-3">
                        {c.used_by_username ? (
                          <span>@{c.used_by_username} ({c.used_by_email})</span>
                        ) : (
                          <span className="text-muted-foreground">·</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {c.status === 'unused' && (
                          <Button size="sm" variant="ghost" onClick={() => copyCode(c.code)} data-testid={`copy-code-${c.code}`}>
                            <Copy className="w-4 h-4 mr-1" /> Copy Link
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

export default AdminBetaPage;
