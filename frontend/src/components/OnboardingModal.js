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
import { Disc, X, Loader2, Search, Check, ChevronRight } from 'lucide-react';
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

  // Step 1: Build collection
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [addedRecords, setAddedRecords] = useState([]);

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
    } catch { toast.error('Failed'); }
  };

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
    } catch { toast.error('Failed to post'); }
    finally { setSubmitting(false); }
  };

  const skipAndEnter = async () => {
    try {
      await axios.put(`${API}/auth/me`, { onboarding_completed: true }, { headers: { Authorization: `Bearer ${token}` } });
      updateUser(prev => ({ ...prev, onboarding_completed: true }));
      onComplete?.();
    } catch { onComplete?.(); }
  };

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
              <p className="text-sm text-muted-foreground mt-1">add at least 3 records to get started. search by artist or album.</p>
            </div>

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

            {/* Added records horizontal scroll */}
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
            <p className="text-xs text-muted-foreground text-center">{addedRecords.length}/3 records added</p>

            <Button
              onClick={goStep2}
              disabled={addedRecords.length < 3}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white"
              data-testid="onboarding-step1-next"
            >
              looks good <ChevronRight className="w-4 h-4 ml-1" />
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
              post and enter the hive 🐝
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
