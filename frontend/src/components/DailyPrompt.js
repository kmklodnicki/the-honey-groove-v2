import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Textarea } from './ui/textarea';
import { Skeleton } from './ui/skeleton';
import { Loader2, Disc, Share2, Send, Download, Search, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import RecordSearchResult from './RecordSearchResult';
import AlbumArt from './AlbumArt';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Link } from 'react-router-dom';

// ─── Daily Prompt Card (top of Hive feed) ───

export const DailyPromptCard = ({ records, onPostCreated }) => {
  const { user, token, API } = useAuth();
  const [prompt, setPrompt] = useState(null);
  const [hasBuzzedIn, setHasBuzzedIn] = useState(false);
  const [buzzResponse, setBuzzResponse] = useState(null);
  const [streak, setStreak] = useState(0);
  const [buzzCount, setBuzzCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  // Carousel state
  const [responses, setResponses] = useState([]);
  const [carouselIdx, setCarouselIdx] = useState(0);
  const [loadingResponses, setLoadingResponses] = useState(false);

  const fetchPrompt = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/prompts/today`, { headers: { Authorization: `Bearer ${token}` } });
      setPrompt(r.data.prompt);
      setHasBuzzedIn(r.data.has_buzzed_in);
      setBuzzResponse(r.data.response);
      setStreak(r.data.streak);
      setBuzzCount(r.data.buzz_count || 0);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchPrompt(); }, [fetchPrompt]);

  // Fetch carousel responses after buzzing in
  const fetchResponses = useCallback(async () => {
    if (!prompt || !hasBuzzedIn) return;
    setLoadingResponses(true);
    try {
      const r = await axios.get(`${API}/prompts/${prompt.id}/responses`, { headers: { Authorization: `Bearer ${token}` } });
      setResponses(r.data);
      setCarouselIdx(0);
    } catch { /* ignore */ }
    finally { setLoadingResponses(false); }
  }, [API, token, prompt, hasBuzzedIn]);

  useEffect(() => { fetchResponses(); }, [fetchResponses]);

  if (loading) return <Skeleton className="h-32 w-full rounded-xl mb-4" />;
  if (!prompt) return null;

  const currentResp = responses[carouselIdx];

  return (
    <>
      <Card className="mb-4 p-5 border-amber-200/60 bg-gradient-to-br from-amber-50/80 to-orange-50/40 relative overflow-hidden" data-testid="daily-prompt-card">
        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-100/40 rounded-full -translate-y-8 translate-x-8" />
        <p className="text-[11px] uppercase tracking-widest text-amber-600/70 font-medium mb-2">Daily Prompt</p>
        <p className="font-heading text-xl md:text-2xl text-vinyl-black leading-snug mb-3 italic" data-testid="daily-prompt-text">
          {prompt.text}
        </p>

        {!hasBuzzedIn ? (
          /* ── GATEKEEPER: Pre-buzz state ── */
          <div>
            {buzzCount > 0 && (
              <p className="text-sm text-amber-700 mb-3 font-medium" data-testid="buzz-gate-msg">
                {buzzCount} member{buzzCount !== 1 ? 's' : ''} of the Hive {buzzCount === 1 ? 'has' : 'have'} buzzed in, it's your turn!
              </p>
            )}
            <div className="flex items-center justify-between">
              <Button onClick={() => setModalOpen(true)} className="bg-amber-500 hover:bg-amber-600 text-white rounded-full px-6 text-sm font-semibold shadow-sm" data-testid="buzz-in-btn">
                buzz in 🐝
              </Button>
              {streak > 0 && (
                <span className="flex items-center gap-1 text-sm text-amber-600 font-bold">🐝 {streak} {streak === 1 ? 'day' : 'days'} in a row</span>
              )}
            </div>
          </div>
        ) : (
          /* ── REVIEW MODE: Post-buzz carousel ── */
          <div data-testid="prompt-review-mode">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-sm text-amber-700 font-medium">buzzed in</span>
              {streak > 0 && <span className="flex items-center gap-1 text-sm text-amber-600 font-bold">🐝 {streak} {streak === 1 ? 'day' : 'days'} in a row</span>}
              {buzzCount > 0 && (
                <a href={`/hive?prompt_id=${prompt.id}`} className="text-xs text-amber-600 hover:text-amber-800 hover:underline font-medium transition ml-auto" data-testid="buzz-count-link">
                  {buzzCount} buzzed in
                </a>
              )}
            </div>

            {/* Carousel */}
            {loadingResponses ? (
              <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-amber-500" /></div>
            ) : responses.length > 0 && currentResp ? (
              <div className="relative" data-testid="prompt-carousel">
                <div className="flex items-center gap-3 transition-all duration-300">
                  {/* Album art */}
                  <div className="relative shrink-0 w-16 h-16 rounded-lg overflow-hidden bg-vinyl-black">
                    {currentResp.cover_url ? <AlbumArt src={currentResp.cover_url} alt={`${currentResp.record_artist || ''} ${currentResp.record_title || ''} vinyl record`} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
                    {currentResp.color_variant && (
                      <div className="absolute bottom-0.5 right-0.5 max-w-[90%] truncate uppercase text-[8px] font-bold px-1 py-0.5 rounded-full"
                        style={{ backgroundColor: 'rgba(0,0,0,0.80)', color: '#FFD700', letterSpacing: '0.5px', boxShadow: '0 2px 8px rgba(0,0,0,0.35)', border: '1px solid rgba(255,215,0,0.25)' }}>
                        {currentResp.color_variant}
                      </div>
                    )}
                  </div>
                  {/* Response content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <Link to={`/profile/${currentResp.username}`} className="text-xs font-bold text-vinyl-black hover:text-honey-amber transition" data-testid="carousel-username">
                        @{currentResp.username}
                      </Link>
                      {currentResp.username?.toLowerCase() === 'katieintheafterglow' && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-honey/20 text-amber-700 font-bold">Founder</span>}
                    </div>
                    <p className="text-sm font-medium truncate">{currentResp.record_title}</p>
                    <p className="text-xs text-muted-foreground truncate">{currentResp.record_artist}</p>
                    {currentResp.caption && <p className="text-xs text-stone-600 mt-1 italic line-clamp-2">{currentResp.caption}</p>}
                  </div>
                </div>
                {/* Navigation arrows */}
                {responses.length > 1 && (
                  <div className="flex items-center justify-between mt-3">
                    <Button size="sm" variant="ghost" onClick={() => setCarouselIdx(i => (i - 1 + responses.length) % responses.length)} className="rounded-full h-8 w-8 p-0" data-testid="carousel-prev">
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-[10px] text-muted-foreground">{carouselIdx + 1} / {responses.length}</span>
                    <Button size="sm" variant="ghost" onClick={() => setCarouselIdx(i => (i + 1) % responses.length)} className="rounded-full h-8 w-8 p-0" data-testid="carousel-next">
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}
      </Card>

      <BuzzInModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        prompt={prompt}
        records={records}
        onSuccess={(resp) => {
          setHasBuzzedIn(true);
          setBuzzResponse(resp);
          setStreak(resp.streak);
          setBuzzCount(c => c + 1);
          onPostCreated?.();
        }}
      />
    </>
  );
};

// ─── Buzz-In Modal ───

const BuzzInModal = ({ open, onOpenChange, prompt, records, onSuccess }) => {
  const { user, token, API } = useAuth();
  const [selectedRecordId, setSelectedRecordId] = useState('');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [buzzSearch, setBuzzSearch] = useState('');
  const [buzzSearchResults, setBuzzSearchResults] = useState([]);
  const buzzSearchTimer = useRef(null);
  const [discogsData, setDiscogsData] = useState(null);
  const [loadingDiscogs, setLoadingDiscogs] = useState(false);
  const [caption, setCaption] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [responseData, setResponseData] = useState(null);

  // Debounced local collection search
  const searchCollection = useCallback((query) => {
    if (buzzSearchTimer.current) clearTimeout(buzzSearchTimer.current);
    if (!query || query.length < 2) { setBuzzSearchResults([]); return; }
    buzzSearchTimer.current = setTimeout(() => {
      const words = query.toLowerCase().split(/\s+/).filter(Boolean);
      const scored = records
        ?.filter(r => {
          const hay = `${r.artist} ${r.title}`.toLowerCase();
          return words.every(w => hay.includes(w));
        })
        .map(r => {
          const hay = `${r.artist} ${r.title}`.toLowerCase();
          let score = 0;
          for (const w of words) {
            if (hay === w) score += 100;
            else if (hay.startsWith(w)) score += 60;
            else if (hay.includes(` ${w}`)) score += 40;
            else if (hay.includes(w)) score += 20;
          }
          return { ...r, _score: score };
        })
        .sort((a, b) => b._score - a._score) || [];
      setBuzzSearchResults(scored);
    }, 300);
  }, [records]);

  const selectBuzzRecord = (rec) => {
    setSelectedRecord(rec);
    setSelectedRecordId(rec.id);
    setBuzzSearch('');
    setBuzzSearchResults([]);
  };

  const deselectBuzzRecord = () => {
    setSelectedRecord(null);
    setSelectedRecordId('');
    setDiscogsData(null);
  };

  useEffect(() => {
    return () => { if (buzzSearchTimer.current) clearTimeout(buzzSearchTimer.current); };
  }, []);

  // Fetch Discogs data when record selected
  useEffect(() => {
    if (!selectedRecordId || !selectedRecord?.discogs_id) {
      setDiscogsData(null);
      return;
    }
    setLoadingDiscogs(true);
    axios.get(`${API}/prompts/discogs-hires/${selectedRecord.discogs_id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setDiscogsData(r.data))
      .catch(() => setDiscogsData(null))
      .finally(() => setLoadingDiscogs(false));
  }, [selectedRecordId, selectedRecord, API, token]);

  const displayData = discogsData || selectedRecord;
  const coverUrl = discogsData?.cover_url || selectedRecord?.cover_url;
  const labelText = discogsData?.label?.[0] || '';
  const yearText = discogsData?.year || selectedRecord?.year || '';

  const handleSubmit = async (postToHive) => {
    if (!selectedRecordId) { toast.error('select a record first.'); return; }
    setSubmitting(true);
    try {
      const r = await axios.post(`${API}/prompts/buzz-in`, {
        prompt_id: prompt.id,
        record_id: selectedRecordId,
        caption,
        post_to_hive: postToHive,
      }, { headers: { Authorization: `Bearer ${token}` } });
      setResponseData(r.data);
      trackEvent('daily_prompt_answered');
      toast.success(postToHive ? 'Buzzed in & posted to The Hive!' : 'Buzzed in!');
      onSuccess?.(r.data);
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSubmitting(false); }
  };

  const handleExport = async () => {
    if (!responseData) return;
    setExporting(true);
    try {
      const r = await axios.post(`${API}/prompts/export-card`, { response_id: responseData.id }, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });
      const blob = new Blob([r.data], { type: 'image/png' });
      trackEvent('export_card_generated', { card_type: 'daily_prompt' });
      const file = new File([blob], `honeygroove-prompt-${Date.now()}.png`, { type: 'image/png' });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: 'the Honey Groove · Daily Prompt' });
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = file.name; a.click();
        URL.revokeObjectURL(url);
        toast.success('card downloaded.');
      }
    } catch { toast.error('export failed. try again.'); }
    finally { setExporting(false); }
  };

  const reset = () => {
    setSelectedRecordId(''); setSelectedRecord(null); setBuzzSearch(''); setBuzzSearchResults([]);
    setDiscogsData(null); setCaption(''); setResponseData(null);
  };

  return (
    <Dialog open={open} onOpenChange={o => { if (!o) reset(); onOpenChange(o); }}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-heading text-xl">buzz in 🐝</DialogTitle>
          <DialogDescription className="italic text-amber-700">{prompt?.text}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          {!responseData ? (
            <>
              {/* Record search */}
              <div>
                <label className="text-sm font-medium mb-1 block text-amber-800">Record</label>
                {!selectedRecord ? (
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="search your collection..."
                      value={buzzSearch}
                      onChange={e => { setBuzzSearch(e.target.value); searchCollection(e.target.value); }}
                      className="pl-9 border-amber-200"
                      data-testid="buzz-record-search"
                      autoFocus
                    />
                    {buzzSearchResults.length > 0 && (
                      <div className="absolute z-50 left-0 right-0 mt-1 border border-amber-200/60 rounded-lg max-h-52 overflow-y-auto shadow-lg bg-white" data-testid="buzz-search-results">
                        {buzzSearchResults.map(r => (
                          <RecordSearchResult key={r.id} record={r} onClick={() => selectBuzzRecord(r)} size="sm" testId={`buzz-result-${r.id}`} />
                        ))}
                      </div>
                    )}
                    {buzzSearch.length >= 2 && buzzSearchResults.length === 0 && (
                      <div className="absolute z-50 left-0 right-0 mt-1 border border-amber-200/60 rounded-lg p-4 text-center shadow-lg bg-white" data-testid="buzz-no-results">
                        <p className="text-sm text-amber-700">no results in your collection</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-3 rounded-lg p-2.5 bg-amber-50/60 border border-amber-100" data-testid="buzz-selected-record">
                    {selectedRecord.cover_url ? (
                      <AlbumArt src={selectedRecord.cover_url} alt={`${selectedRecord.title} by ${selectedRecord.artist}`} className="w-11 h-11 rounded-md object-cover shadow-sm" />
                    ) : (
                      <div className="w-11 h-11 rounded-md bg-amber-100 flex items-center justify-center"><Disc className="w-5 h-5 text-amber-400" /></div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{selectedRecord.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{selectedRecord.artist}</p>
                    </div>
                    <button onClick={deselectBuzzRecord} className="p-1 rounded-full hover:bg-amber-100 text-amber-600" data-testid="buzz-deselect-record">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Live preview */}
              {selectedRecordId && (
                <div className="bg-[#FAF6EE] rounded-xl p-4 space-y-3 border border-amber-100" data-testid="buzz-preview">
                  <p className="text-center italic text-amber-700 text-sm">{prompt?.text}</p>
                  {loadingDiscogs ? (
                    <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-amber-400" /></div>
                  ) : (
                    <>
                      <div className="flex justify-center">
                        {coverUrl ? (
                          <img src={coverUrl} alt="" className="w-40 h-40 rounded-xl object-cover shadow-md" />
                        ) : (
                          <div className="w-40 h-40 rounded-xl bg-amber-100 flex items-center justify-center"><Disc className="w-10 h-10 text-amber-300" /></div>
                        )}
                      </div>
                      <div className="text-center">
                        <p className="font-heading text-lg">{displayData?.title || 'Unknown'}</p>
                        <p className="text-sm text-muted-foreground">{displayData?.artist || 'Unknown'}</p>
                        {(labelText || yearText) && (
                          <p className="text-xs text-amber-600 italic mt-1">
                            {[labelText, yearText].filter(Boolean).join(' · ')}
                          </p>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              <Textarea
                placeholder="Add a caption (optional)"
                value={caption} onChange={e => setCaption(e.target.value)}
                className="border-amber-200 resize-none" rows={2}
                data-testid="buzz-caption"
              />

              <div className="flex justify-center">
                <Button onClick={() => handleSubmit(true)} disabled={submitting || !selectedRecordId}
                  className="rounded-full bg-amber-500 hover:bg-amber-600 text-white w-full" data-testid="buzz-post-hive-btn">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Send className="w-4 h-4 mr-1" />}
                  post to the hive
                </Button>
              </div>
            </>
          ) : (
            /* Post-submit: success message */
            <div className="text-center space-y-4">
              <div className="bg-amber-50 rounded-xl p-4">
                <p className="text-amber-700 font-medium mb-1">buzzed in!</p>
                {responseData.streak > 0 && (
                  <p className="flex items-center justify-center gap-1 text-amber-600 font-bold text-lg">
                    {responseData.streak} {responseData.streak === 1 ? 'day' : 'days'} in a row
                  </p>
                )}
              </div>
              {/* save & share card — hidden until feature is ready */}
              <Button variant="ghost" onClick={() => onOpenChange(false)} className="w-full text-muted-foreground">
                done
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ─── Streak Badge (for ProfilePage) ───

export const StreakBadge = ({ username }) => {
  const { API } = useAuth();
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    if (!username) return;
    axios.get(`${API}/prompts/streak/${username}`)
      .then(r => setStreak(r.data.streak))
      .catch(() => {});
  }, [API, username]);

  if (streak <= 0) return null;
  return (
    <div className="flex items-center gap-1.5 text-amber-600 font-bold text-sm" data-testid="profile-streak-badge">
      🐝 {streak} {streak === 1 ? 'day' : 'days'} in a row
    </div>
  );
};

export default DailyPromptCard;
