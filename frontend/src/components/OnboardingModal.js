import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Dialog, DialogContent } from './ui/dialog';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Disc, Loader2, Search, ChevronRight, ExternalLink, X } from 'lucide-react';
import { toast } from 'sonner';
import AlbumArt from './AlbumArt';
import RecordSearchResult from './RecordSearchResult';

const MOOD_OPTIONS = [
  'Late Night', 'Good Morning', 'Rainy Day', 'Road Trip', 'Golden Hour',
  'Deep Focus', 'Party Mode', 'Lazy Afternoon', 'Melancholy', 'Upbeat Vibes',
  'Cozy Evening', 'Workout',
];

const OnboardingModal = ({ open, onComplete }) => {
  const { token, API, updateUser, user: authUser } = useAuth();
  const navigate = useNavigate();
  // If user needs first_name, start at step 0 (first name), else step 1
  const needsFirstName = !authUser?.first_name;
  const [step, setStep] = useState(needsFirstName ? 0 : 1);
  const totalSteps = needsFirstName ? 4 : 3;
  const [submitting, setSubmitting] = useState(false);

  // Step 0: First Name
  const [onboardFirstName, setOnboardFirstName] = useState('');

  // Step 1: Build collection (manual search)
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [addedRecords, setAddedRecords] = useState([]);

  // Step 1: Discogs OAuth
  const [oauthLoading, setOauthLoading] = useState(false);

  // Step 2: Now Spinning
  const [spinRecord, setSpinRecord] = useState(null); // { discogs_id, title, artist, cover_url, record_id }
  const [spinSearch, setSpinSearch] = useState('');
  const [spinResults, setSpinResults] = useState([]);
  const [spinSearching, setSpinSearching] = useState(false);
  const [caption, setCaption] = useState('');
  const [mood, setMood] = useState('');

  // Step 3: Country
  const [onboardCountry, setOnboardCountry] = useState('');

  const COUNTRIES = [
    'US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'NL', 'SE', 'IT', 'ES', 'BR', 'MX', 'NZ', 'IE', 'NO', 'DK', 'FI', 'BE', 'AT', 'CH', 'PT', 'PL', 'CZ', 'KR', 'TW', 'SG', 'ZA', 'AR', 'CL', 'CO', 'PH', 'IN', 'IL', 'GR', 'HU', 'RO', 'HR', 'SK', 'BG', 'RS', 'UA', 'TH', 'MY', 'ID', 'VN', 'HK', 'AE', 'SA',
  ];

  const searchTimerRef = useRef(null);
  const spinTimerRef = useRef(null);
  useEffect(() => { return () => { if (searchTimerRef.current) clearTimeout(searchTimerRef.current); if (spinTimerRef.current) clearTimeout(spinTimerRef.current); }; }, []);

  const searchDiscogs = useCallback((q) => {
    if (!q || q.length < 2) { setSearchResults([]); setSearchLoading(false); return; }
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const r = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(q)}`, { headers: { Authorization: `Bearer ${token}` } });
        setSearchResults(r.data?.slice(0, 8) || []);
      } catch { setSearchResults([]); }
      finally { setSearchLoading(false); }
    }, 350);
  }, [API, token]);

  const addRecord = async (record) => {
    if (addedRecords.find(r => r.discogs_id === record.discogs_id)) return;
    try {
      const resp = await axios.post(`${API}/records`, {
        title: record.title, artist: record.artist, cover_url: record.cover_url,
        discogs_id: record.discogs_id, year: record.year, format: Array.isArray(record.format) ? record.format.join(', ') : record.format,
      }, { headers: { Authorization: `Bearer ${token}` } });
      setAddedRecords(prev => [...prev, { ...record, record_id: resp.data.id }]);
      setSearchQuery(''); setSearchResults([]);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to add'); }
  };

  // Discogs OAuth connect
  const handleDiscogsOAuth = async () => {
    setOauthLoading(true);
    try {
      const origin = encodeURIComponent(window.location.origin);
      const resp = await axios.get(`${API}/discogs/oauth/start?frontend_origin=${origin}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      window.location.href = resp.data.authorization_url;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start Discogs connection');
      setOauthLoading(false);
    }
  };

  const goStep2 = () => { setStep(2); };

  // Step 2: search for a record to spin
  const searchSpin = useCallback((q) => {
    if (!q || q.length < 2) { setSpinResults([]); setSpinSearching(false); return; }
    if (spinTimerRef.current) clearTimeout(spinTimerRef.current);
    spinTimerRef.current = setTimeout(async () => {
      setSpinSearching(true);
      try {
        const r = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(q)}`, { headers: { Authorization: `Bearer ${token}` } });
        setSpinResults(r.data?.slice(0, 6) || []);
      } catch { setSpinResults([]); }
      finally { setSpinSearching(false); }
    }, 350);
  }, [API, token]);

  const pickSpinRecord = async (record) => {
    // Check if already in addedRecords from Step 1
    const existing = addedRecords.find(r => r.discogs_id === record.discogs_id);
    if (existing?.record_id) {
      setSpinRecord({ ...record, record_id: existing.record_id });
    } else {
      // Add to collection first
      try {
        const resp = await axios.post(`${API}/records`, {
          title: record.title, artist: record.artist, cover_url: record.cover_url,
          discogs_id: record.discogs_id, year: record.year, format: Array.isArray(record.format) ? record.format.join(', ') : record.format,
        }, { headers: { Authorization: `Bearer ${token}` } });
        setSpinRecord({ ...record, record_id: resp.data.id });
      } catch (e) {
        if (e.response?.status === 409) {
          // Already in collection - fetch the record_id
          try {
            const check = await axios.get(`${API}/records/check-ownership?discogs_id=${record.discogs_id}`, { headers: { Authorization: `Bearer ${token}` } });
            setSpinRecord({ ...record, record_id: check.data.record_id });
          } catch { setSpinRecord({ ...record, record_id: null }); }
        } else {
          toast.error('could not add record.');
          return;
        }
      }
    }
    setSpinSearch('');
    setSpinResults([]);
  };

  const postAndEnter = async () => {
    setSubmitting(true);
    try {
      if (spinRecord?.record_id) {
        await axios.post(`${API}/composer/now-spinning`, {
          record_id: spinRecord.record_id, caption: caption || null, mood: mood || null,
        }, { headers: { Authorization: `Bearer ${token}` } });
      }
      await axios.put(`${API}/auth/me`, { onboarding_completed: true, ...(onboardCountry ? { country: onboardCountry } : {}) }, { headers: { Authorization: `Bearer ${token}` } });
      updateUser(prev => ({ ...prev, onboarding_completed: true, ...(onboardCountry ? { country: onboardCountry } : {}) }));
      onComplete?.();
    } catch { toast.error('could not post. try again.'); }
    finally { setSubmitting(false); }
  };

  const skipAndEnter = async () => {
    try {
      await axios.put(`${API}/auth/me`, { onboarding_completed: true, ...(onboardCountry ? { country: onboardCountry } : {}) }, { headers: { Authorization: `Bearer ${token}` } });
      updateUser(prev => ({ ...prev, onboarding_completed: true, ...(onboardCountry ? { country: onboardCountry } : {}) }));
      onComplete?.();
    } catch { onComplete?.(); }
  };

  const importProgressPercent = 0;

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto [&>button]:hidden" aria-describedby="onboarding-desc" onPointerDownOutside={e => e.preventDefault()} onEscapeKeyDown={e => e.preventDefault()}>
        <span id="onboarding-desc" className="sr-only">Onboarding flow</span>

        {/* Progress */}
        <div className="flex items-center justify-center gap-2 mb-4" data-testid="onboarding-progress">
          {Array.from({ length: totalSteps }, (_, i) => i + (needsFirstName ? 0 : 1)).map(s => (
            <div key={s} className="flex items-center gap-1">
              <div className={`w-10 h-1 rounded-full transition-colors ${s <= step ? 'bg-amber-500' : 'bg-stone-200'}`} />
            </div>
          ))}
          <span className="text-xs text-muted-foreground ml-2">Step {step - (needsFirstName ? 0 : 1) + 1} of {totalSteps}</span>
        </div>

        {/* Step 0: First Name (only if needed) */}
        {step === 0 && needsFirstName && (
          <div className="space-y-4" data-testid="onboarding-step-firstname">
            <div className="text-center">
              <h2 className="font-heading text-2xl italic" style={{ fontFamily: '"Playfair Display", serif' }}>What should we call you? 🐝</h2>
              <p className="text-sm text-muted-foreground mt-1">Private. This is only used to address you in community emails.</p>
            </div>
            <Input
              placeholder="Your first name"
              value={onboardFirstName}
              onChange={e => setOnboardFirstName(e.target.value.slice(0, 50))}
              className="border-amber-200 text-center text-lg"
              data-testid="onboarding-first-name-input"
              autoFocus
            />
            <Button
              onClick={async () => {
                if (!onboardFirstName.trim()) return;
                try {
                  await axios.put(`${API}/auth/me`, { first_name: onboardFirstName.trim() }, { headers: { Authorization: `Bearer ${token}` } });
                  updateUser(prev => ({ ...prev, first_name: onboardFirstName.trim() }));
                  setStep(1);
                } catch { toast.error('Could not save. Try again.'); }
              }}
              disabled={!onboardFirstName.trim()}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white disabled:opacity-40"
              data-testid="onboarding-firstname-next"
            >
              Next <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}

        {/* Step 1: Build Collection */}
        {step === 1 && (
          <div className="space-y-4" data-testid="onboarding-step-1">
            <div className="text-center">
              <h2 className="font-heading text-2xl italic" style={{ fontFamily: '"Playfair Display", serif' }}>connect your vault.</h2>
              <p className="text-sm text-muted-foreground mt-1">import your vinyl vault from Discogs in one tap.</p>
            </div>

            {/* Prominent Discogs OAuth Button */}
            <Button
              onClick={handleDiscogsOAuth}
              disabled={oauthLoading}
              className="w-full rounded-xl py-6 gap-3 font-bold text-base transition-all hover:shadow-lg"
              style={{ background: 'linear-gradient(135deg, #FFD700, #F4B521)', color: '#1A1A1A', border: '1.5px solid #DAA520', boxShadow: '0 0 20px rgba(255,215,0,0.3)' }}
              onMouseEnter={e => { e.currentTarget.style.background = '#E5AB00'; e.currentTarget.style.boxShadow = '0 0 28px rgba(255,215,0,0.5)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'linear-gradient(135deg, #FFD700, #F4B521)'; e.currentTarget.style.boxShadow = '0 0 20px rgba(255,215,0,0.3)'; }}
              data-testid="onboarding-discogs-oauth-btn"
            >
              {oauthLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <ExternalLink className="w-5 h-5" />
              )}
              {oauthLoading ? 'Connecting...' : 'Connect with Discogs'}
            </Button>
            <p className="text-[10px] text-muted-foreground text-center">Secure OAuth login. We never see your Discogs password.</p>

            {/* Divider */}
            <div className="flex items-center gap-3 text-[10px] text-muted-foreground uppercase tracking-wider">
              <div className="flex-1 h-px bg-stone-200" />
              <span>or search manually</span>
              <div className="flex-1 h-px bg-stone-200" />
            </div>

            {/* Manual search */}
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
                  <RecordSearchResult key={r.discogs_id} record={r} onClick={() => addRecord(r)} size="sm" testId={`onboarding-result-${r.discogs_id}`} />
                ))}
              </div>
            )}

            {addedRecords.length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-2" data-testid="onboarding-added-records">
                {addedRecords.map((r, i) => (
                  <div key={i} className="shrink-0 relative group">
                    {r.cover_url ? (
                      <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} className="w-16 h-16 rounded-lg object-cover shadow-sm" />
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
            {addedRecords.length > 0 && <p className="text-xs text-muted-foreground text-center">{addedRecords.length} records added</p>}

            <Button
              onClick={goStep2}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white"
              data-testid="onboarding-step1-next"
            >
              {addedRecords.length > 0 ? 'continue' : 'skip for now'} <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}

        {/* Step 2: Drop the needle */}
        {step === 2 && (
          <div className="space-y-4" data-testid="onboarding-step-2">
            <div className="text-center">
              <h2 className="font-heading text-2xl italic" style={{ fontFamily: '"Playfair Display", serif' }}>what's on the turntable right now?</h2>
              <p className="text-sm text-muted-foreground mt-1">share what you're spinning. totally optional.</p>
            </div>

            {/* Selected record preview */}
            {spinRecord && (
              <div className="flex items-center gap-3 bg-amber-50 rounded-xl p-3" data-testid="onboarding-spin-selected">
                {spinRecord.cover_url ? (
                  <AlbumArt src={spinRecord.cover_url} alt={`${spinRecord.artist} ${spinRecord.title} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow-sm" />
                ) : (
                  <div className="w-14 h-14 rounded-lg bg-amber-100 flex items-center justify-center"><Disc className="w-6 h-6 text-amber-400" /></div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{spinRecord.title}</p>
                  <p className="text-xs text-muted-foreground truncate">{spinRecord.artist}</p>
                </div>
                <button onClick={() => setSpinRecord(null)} className="p-1 rounded-full hover:bg-amber-100 transition-colors" data-testid="onboarding-spin-clear">
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>
            )}

            {/* Search for record */}
            {!spinRecord && (
              <>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="search for a record..."
                    value={spinSearch}
                    onChange={e => { setSpinSearch(e.target.value); searchSpin(e.target.value); }}
                    className="pl-9 border-amber-200"
                    data-testid="onboarding-spin-search"
                  />
                  {spinSearching && <Loader2 className="w-4 h-4 animate-spin absolute right-3 top-3 text-amber-400" />}
                </div>

                {spinResults.length > 0 && (
                  <div className="border border-amber-200/50 rounded-lg max-h-48 overflow-y-auto bg-white">
                    {spinResults.map(r => (
                      <RecordSearchResult key={r.discogs_id} record={r} onClick={() => pickSpinRecord(r)} size="sm" testId={`onboarding-spin-result-${r.discogs_id}`} />
                    ))}
                  </div>
                )}

                {/* Quick picks from Step 1 */}
                {addedRecords.length > 0 && !spinSearch && (
                  <div data-testid="onboarding-quick-picks">
                    <p className="text-xs text-muted-foreground mb-2">quick pick from your vault</p>
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {addedRecords.slice(0, 8).map((r, i) => (
                        <button key={i} onClick={() => pickSpinRecord(r)} className="shrink-0 group" data-testid={`onboarding-quick-pick-${i}`}>
                          {r.cover_url ? (
                            <AlbumArt src={r.cover_url} alt={`${r.artist} ${r.title} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow-sm group-hover:ring-2 ring-amber-400 transition-all" />
                          ) : (
                            <div className="w-14 h-14 rounded-lg bg-stone-100 flex items-center justify-center group-hover:ring-2 ring-amber-400 transition-all"><Disc className="w-5 h-5 text-stone-400" /></div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Mood */}
            <div>
              <p className="text-xs text-muted-foreground mb-1.5">set the mood</p>
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
              onClick={() => setStep(3)}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white"
              data-testid="onboarding-step2-next"
            >
              next
            </Button>

            <button onClick={() => setStep(3)} className="w-full text-center text-xs text-muted-foreground hover:text-amber-600 transition-colors" data-testid="onboarding-skip">
              skip for now
            </button>
          </div>
        )}

        {/* Step 3: Country */}
        {step === 3 && (
          <div className="space-y-4" data-testid="onboarding-step-3">
            <div className="text-center">
              <h2 className="font-heading text-2xl italic" style={{ fontFamily: '"Playfair Display", serif' }}>where are you based?</h2>
              <p className="text-sm text-muted-foreground mt-1">helps with shipping for marketplace listings.</p>
            </div>

            <select
              value={onboardCountry}
              onChange={(e) => setOnboardCountry(e.target.value)}
              className="flex h-10 w-full rounded-md border border-amber-200 bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
              data-testid="onboarding-country"
            >
              <option value="">Select your country</option>
              {COUNTRIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            <Button
              onClick={postAndEnter}
              disabled={submitting || !onboardCountry}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white disabled:opacity-40"
              data-testid="onboarding-post-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {spinRecord ? 'post and enter the hive' : 'enter the hive'}
            </Button>

            <p className="text-xs text-center text-muted-foreground">Country is required to continue.</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default OnboardingModal;
