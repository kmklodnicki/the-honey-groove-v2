import React, { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Dialog, DialogContent } from './ui/dialog';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from './ui/select';
import { Textarea } from './ui/textarea';
import { Progress } from './ui/progress';
import { Disc, Loader2, Search, Check, ChevronRight, ExternalLink, CheckCircle2, AlertCircle, X } from 'lucide-react';
import { toast } from 'sonner';

const MOOD_OPTIONS = [
  'Late Night', 'Good Morning', 'Rainy Day', 'Road Trip', 'Golden Hour',
  'Deep Focus', 'Party Mode', 'Lazy Afternoon', 'Melancholy', 'Upbeat Vibes',
  'Cozy Evening', 'Workout',
];

const OnboardingModal = ({ open, onComplete }) => {
  const { token, API, updateUser } = useAuth();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);

  // Step 1: Build collection (manual search)
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [addedRecords, setAddedRecords] = useState([]);

  // Step 1: Discogs import flow
  const [showDiscogsConnect, setShowDiscogsConnect] = useState(false);
  const [discogsUsername, setDiscogsUsername] = useState('');
  const [discogsConnecting, setDiscogsConnecting] = useState(false);
  const [discogsConnected, setDiscogsConnected] = useState(false);
  const [discogsImporting, setDiscogsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(null);
  const [importDone, setImportDone] = useState(false);

  // Step 2: Follow people
  const [suggestions, setSuggestions] = useState([]);
  const [followedIds, setFollowedIds] = useState(new Set());
  const [sugLoading, setSugLoading] = useState(false);

  // Step 3: First post
  const [selectedRecord, setSelectedRecord] = useState('');
  const [caption, setCaption] = useState('');
  const [mood, setMood] = useState('');

  const searchDiscogs = useCallback(async (q) => {
    if (!q || q.length < 2) { setSearchResults([]); return; }
    setSearchLoading(true);
    try {
      const r = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(q)}`, { headers: { Authorization: `Bearer ${token}` } });
      setSearchResults(r.data?.slice(0, 8) || []);
    } catch { setSearchResults([]); }
    finally { setSearchLoading(false); }
  }, [API, token]);

  const addRecord = async (record) => {
    if (addedRecords.find(r => r.discogs_id === record.discogs_id)) return;
    try {
      await axios.post(`${API}/records`, {
        title: record.title, artist: record.artist, cover_url: record.cover_url,
        discogs_id: record.discogs_id, year: record.year, format: Array.isArray(record.format) ? record.format.join(', ') : record.format,
      }, { headers: { Authorization: `Bearer ${token}` } });
      setAddedRecords(prev => [...prev, record]);
      setSearchQuery(''); setSearchResults([]);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to add'); }
  };

  // Discogs connect via username
  const handleDiscogsConnect = async (e) => {
    e.preventDefault();
    if (!discogsUsername.trim()) return;
    setDiscogsConnecting(true);
    try {
      const resp = await axios.post(`${API}/discogs/connect-token`,
        { discogs_username: discogsUsername.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setDiscogsConnected(true);
      setShowDiscogsConnect(false);
      toast.success(`connected to discogs as ${discogsUsername.trim()}${resp.data.collection_count ? ` (${resp.data.collection_count} records found)` : ''}.`);
      // Start import immediately
      startImport();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to connect');
    } finally {
      setDiscogsConnecting(false);
    }
  };

  const startImport = async () => {
    setDiscogsImporting(true);
    setImportProgress({ status: 'in_progress', total: 0, imported: 0, skipped: 0 });
    try {
      const resp = await axios.post(`${API}/discogs/import`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setImportProgress(resp.data);
      // Start polling
      pollImport();
    } catch (err) {
      setDiscogsImporting(false);
      toast.error(err.response?.data?.detail || 'Failed to start import');
    }
  };

  const pollImport = () => {
    const interval = setInterval(async () => {
      try {
        const resp = await axios.get(`${API}/discogs/import/progress`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setImportProgress(resp.data);
        if (resp.data.status === 'completed' || resp.data.status === 'error') {
          clearInterval(interval);
          setDiscogsImporting(false);
          if (resp.data.status === 'completed' && resp.data.imported > 0) {
            setImportDone(true);
            toast.success(`imported ${resp.data.imported} records from discogs.`);
          } else if (resp.data.status === 'error') {
            toast.error(resp.data.error_message || 'Import failed');
          }
        }
      } catch { /* ignore poll errors */ }
    }, 2000);
  };

  const loadSuggestions = useCallback(async () => {
    setSugLoading(true);
    try {
      const r = await axios.get(`${API}/users/discover/suggestions`, { headers: { Authorization: `Bearer ${token}` } });
      setSuggestions(r.data?.slice(0, 10) || []);
    } catch { /* ignore */ }
    finally { setSugLoading(false); }
  }, [API, token]);

  const toggleFollow = async (userId) => {
    try {
      await axios.post(`${API}/users/${userId}/follow`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setFollowedIds(prev => {
        const next = new Set(prev);
        if (next.has(userId)) next.delete(userId);
        else next.add(userId);
        return next;
      });
    } catch { toast.error('something went wrong.'); }
  };

  const canProceedStep1 = addedRecords.length >= 3 || importDone;
  const goStep2 = () => { setStep(2); loadSuggestions(); };
  const goStep3 = () => { setStep(3); };

  const postAndEnter = async () => {
    setSubmitting(true);
    try {
      if (selectedRecord) {
        await axios.post(`${API}/composer/now-spinning`, {
          record_id: selectedRecord, caption: caption || null, mood: mood || null,
        }, { headers: { Authorization: `Bearer ${token}` } });
      }
      await axios.put(`${API}/auth/me`, { onboarding_completed: true }, { headers: { Authorization: `Bearer ${token}` } });
      updateUser(prev => ({ ...prev, onboarding_completed: true }));
      onComplete?.();
    } catch { toast.error('could not post. try again.'); }
    finally { setSubmitting(false); }
  };

  const skipAndEnter = async () => {
    try {
      await axios.put(`${API}/auth/me`, { onboarding_completed: true }, { headers: { Authorization: `Bearer ${token}` } });
      updateUser(prev => ({ ...prev, onboarding_completed: true }));
      onComplete?.();
    } catch { onComplete?.(); }
  };

  const importProgressPercent = importProgress?.total > 0
    ? Math.round(((importProgress.imported + importProgress.skipped) / importProgress.total) * 100)
    : 0;

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto [&>button]:hidden" aria-describedby="onboarding-desc" onPointerDownOutside={e => e.preventDefault()} onEscapeKeyDown={e => e.preventDefault()}>
        <span id="onboarding-desc" className="sr-only">Onboarding flow</span>

        {/* Progress */}
        <div className="flex items-center justify-center gap-2 mb-4" data-testid="onboarding-progress">
          {[1, 2, 3].map(s => (
            <div key={s} className="flex items-center gap-1">
              <div className={`w-8 h-1 rounded-full transition-colors ${s <= step ? 'bg-amber-500' : 'bg-stone-200'}`} />
            </div>
          ))}
          <span className="text-xs text-muted-foreground ml-2">Step {step} of 3</span>
        </div>

        {/* Step 1: Build Collection */}
        {step === 1 && (
          <div className="space-y-4" data-testid="onboarding-step-1">
            <div className="text-center">
              <h2 className="font-heading text-2xl italic" style={{ fontFamily: '"Playfair Display", serif' }}>start with what you love.</h2>
              <p className="text-sm text-muted-foreground mt-1">add records manually or import from Discogs.</p>
            </div>

            {/* Discogs Import Section */}
            {!showDiscogsConnect && !discogsImporting && !importDone && (
              <Button
                variant="outline"
                onClick={() => setShowDiscogsConnect(true)}
                className="w-full border-stone-200 hover:border-amber-300 hover:bg-amber-50/50 rounded-xl py-5 gap-2"
                data-testid="onboarding-discogs-import-btn"
              >
                <ExternalLink className="w-4 h-4" />
                Import from Discogs
              </Button>
            )}

            {/* Discogs username input */}
            {showDiscogsConnect && !discogsImporting && !importDone && (
              <form onSubmit={handleDiscogsConnect} className="space-y-2 p-3 bg-stone-50 rounded-xl" data-testid="onboarding-discogs-form">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">Enter your Discogs username</p>
                  <button type="button" onClick={() => setShowDiscogsConnect(false)} className="text-muted-foreground hover:text-stone-600">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="e.g. djshadow"
                    value={discogsUsername}
                    onChange={(e) => setDiscogsUsername(e.target.value)}
                    className="border-amber-200 flex-1"
                    data-testid="onboarding-discogs-username"
                    autoFocus
                  />
                  <Button type="submit" disabled={!discogsUsername.trim() || discogsConnecting}
                    className="bg-amber-500 hover:bg-amber-600 text-white rounded-lg px-4">
                    {discogsConnecting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Connect'}
                  </Button>
                </div>
                <p className="text-[10px] text-muted-foreground">Your collection must be set to public on Discogs.</p>
              </form>
            )}

            {/* Import progress */}
            {discogsImporting && importProgress && (
              <div className="p-3 bg-amber-50 rounded-xl space-y-2" data-testid="onboarding-import-progress">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-amber-500" />
                    Importing your collection...
                  </span>
                  <span className="text-muted-foreground text-xs">
                    {importProgress.imported + importProgress.skipped} / {importProgress.total || '...'}
                  </span>
                </div>
                <Progress value={importProgressPercent} className="h-1.5" />
                <div className="flex gap-3 text-[10px] text-muted-foreground">
                  <span className="text-green-600">{importProgress.imported} imported</span>
                  <span>{importProgress.skipped} skipped</span>
                </div>
              </div>
            )}

            {/* Import done */}
            {importDone && importProgress && (
              <div className="p-3 bg-green-50 rounded-xl flex items-center gap-2" data-testid="onboarding-import-done">
                <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-green-700">{importProgress.imported} records imported from Discogs</p>
                  {importProgress.skipped > 0 && <p className="text-[10px] text-green-600">{importProgress.skipped} duplicates skipped</p>}
                </div>
              </div>
            )}

            {/* Divider */}
            {!discogsImporting && (
              <div className="flex items-center gap-3 text-[10px] text-muted-foreground uppercase tracking-wider">
                <div className="flex-1 h-px bg-stone-200" />
                <span>or search manually</span>
                <div className="flex-1 h-px bg-stone-200" />
              </div>
            )}

            {/* Manual search */}
            {!discogsImporting && (
              <>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="search Discogs..."
                    value={searchQuery}
                    onChange={e => { setSearchQuery(e.target.value); searchDiscogs(e.target.value); }}
                    className="pl-9 border-amber-200"
                    data-testid="onboarding-search"
                  />
                  {searchLoading && <Loader2 className="w-4 h-4 animate-spin absolute right-3 top-3 text-amber-400" />}
                </div>

                {searchResults.length > 0 && (
                  <div className="border border-amber-200/50 rounded-lg max-h-48 overflow-y-auto bg-white">
                    {searchResults.map(r => (
                      <button key={r.discogs_id} onClick={() => addRecord(r)}
                        className="w-full text-left px-3 py-2 hover:bg-amber-50 flex items-center gap-2.5 text-sm border-b border-amber-100 last:border-0"
                        data-testid={`onboarding-result-${r.discogs_id}`}
                      >
                        {r.cover_url ? <img src={r.cover_url} alt="" className="w-10 h-10 rounded object-cover" /> : <Disc className="w-10 h-10 text-stone-300" />}
                        <div className="min-w-0 flex-1"><p className="font-medium truncate">{r.title}</p><p className="text-xs text-muted-foreground truncate">{r.artist}</p></div>
                      </button>
                    ))}
                  </div>
                )}

                {addedRecords.length > 0 && (
                  <div className="flex gap-2 overflow-x-auto pb-2" data-testid="onboarding-added-records">
                    {addedRecords.map((r, i) => (
                      <div key={i} className="shrink-0 relative group">
                        {r.cover_url ? (
                          <img src={r.cover_url} alt="" className="w-16 h-16 rounded-lg object-cover shadow-sm" />
                        ) : (
                          <div className="w-16 h-16 rounded-lg bg-stone-100 flex items-center justify-center"><Disc className="w-6 h-6 text-stone-400" /></div>
                        )}
                        <button onClick={() => setAddedRecords(prev => prev.filter((_, j) => j !== i))}
                          className="absolute -top-1 -right-1 bg-black/60 rounded-full p-0.5 text-white opacity-0 group-hover:opacity-100 transition-opacity">
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                {!importDone && <p className="text-xs text-muted-foreground text-center">{addedRecords.length}/3 records added</p>}
              </>
            )}

            <Button
              onClick={goStep2}
              disabled={!canProceedStep1 || discogsImporting}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white"
              data-testid="onboarding-step1-next"
            >
              {importDone ? 'continue' : 'looks good'} <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}

        {/* Step 2: Find your people */}
        {step === 2 && (
          <div className="space-y-4" data-testid="onboarding-step-2">
            <div className="text-center">
              <h2 className="font-heading text-2xl italic" style={{ fontFamily: '"Playfair Display", serif' }}>the hive is better together.</h2>
              <p className="text-sm text-muted-foreground mt-1">follow a few collectors to fill your feed.</p>
            </div>

            {sugLoading ? (
              <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-amber-400" /></div>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {suggestions.map(u => (
                  <div key={u.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-amber-50/50" data-testid={`onboarding-suggest-${u.username}`}>
                    <Avatar className="h-10 w-10 border border-amber-200">
                      <AvatarImage src={u.avatar_url} />
                      <AvatarFallback className="bg-amber-50 text-sm">{u.username?.[0]?.toUpperCase()}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium">@{u.username}</p>
                      <p className="text-xs text-muted-foreground">{u.record_count} records</p>
                    </div>
                    <Button
                      size="sm"
                      variant={followedIds.has(u.id) ? 'default' : 'outline'}
                      className={`rounded-full text-xs ${followedIds.has(u.id) ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'border-amber-300 text-amber-700'}`}
                      onClick={() => toggleFollow(u.id)}
                      data-testid={`onboarding-follow-${u.username}`}
                    >
                      {followedIds.has(u.id) ? <><Check className="w-3 h-3 mr-1" /> Following</> : 'Follow'}
                    </Button>
                  </div>
                ))}
              </div>
            )}

            <Button
              onClick={goStep3}
              disabled={followedIds.size < 1}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white"
              data-testid="onboarding-step2-next"
            >
              let's go <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}

        {/* Step 3: Drop the needle */}
        {step === 3 && (
          <div className="space-y-4" data-testid="onboarding-step-3">
            <div className="text-center">
              <h2 className="font-heading text-2xl italic" style={{ fontFamily: '"Playfair Display", serif' }}>what's on the turntable right now?</h2>
              <p className="text-sm text-muted-foreground mt-1">post your first Now Spinning. it only takes a second.</p>
            </div>

            <Select value={selectedRecord} onValueChange={setSelectedRecord}>
              <SelectTrigger className="border-amber-200" data-testid="onboarding-record-select">
                <SelectValue placeholder="Choose a record you just added" />
              </SelectTrigger>
              <SelectContent>
                {addedRecords.map(r => (
                  <SelectItem key={r.discogs_id} value={String(r.discogs_id)}>{r.artist} — {r.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div className="flex flex-wrap gap-1.5">
              {MOOD_OPTIONS.map(m => (
                <button key={m} onClick={() => setMood(mood === m ? '' : m)}
                  className={`px-3 py-1.5 rounded-full text-xs transition-all ${mood === m ? 'bg-amber-500 text-white' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'}`}
                  data-testid={`onboarding-mood-${m.toLowerCase().replace(/\s/g, '-')}`}
                >
                  {m}
                </button>
              ))}
            </div>

            <Textarea
              placeholder="add a caption..."
              value={caption}
              onChange={e => setCaption(e.target.value)}
              className="border-amber-200 resize-none"
              rows={2}
              data-testid="onboarding-caption"
            />

            <Button
              onClick={postAndEnter}
              disabled={submitting}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white"
              data-testid="onboarding-post-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              post and enter the hive
            </Button>

            <button onClick={skipAndEnter} className="w-full text-center text-xs text-muted-foreground hover:text-amber-600 transition-colors" data-testid="onboarding-skip">
              skip for now
            </button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default OnboardingModal;
