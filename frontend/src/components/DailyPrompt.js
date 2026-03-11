import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Textarea } from './ui/textarea';
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
      // Preload the first response's image for LCP
      if (r.data.length > 0 && r.data[0].cover_url) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        link.href = r.data[0].cover_url;
        link.setAttribute('fetchpriority', 'high');
        document.head.appendChild(link);
      }
    } catch { /* ignore */ }
    finally { setLoadingResponses(false); }
  }, [API, token, prompt, hasBuzzedIn]);

  useEffect(() => { fetchResponses(); }, [fetchResponses]);

  if (loading) return (
    <Card className="my-4 p-5 border-orange-200/60 overflow-hidden" style={{ background: 'linear-gradient(135deg, rgba(255,179,0,0.08), rgba(255,160,0,0.04))' }}>
      <div className="h-4 w-24 rounded-full mb-3" style={{ background: 'rgba(200,134,26,0.12)' }} />
      <div className="h-7 w-4/5 rounded-full mb-3" style={{ background: 'rgba(200,134,26,0.08)' }} />
      <div className="h-10 w-32 rounded-full" style={{ background: 'rgba(200,134,26,0.1)' }} />
    </Card>
  );
  if (!prompt) return null;

  const currentResp = responses[carouselIdx];

  return (
    <>
      <Card className="my-4 p-5 border-orange-200/60 bg-gradient-to-br from-amber-50/80 to-orange-50/60 relative overflow-hidden" data-testid="daily-prompt-card">
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
              <Button onClick={() => setModalOpen(true)} className="text-white rounded-full px-6 text-sm font-semibold shadow-sm hover:opacity-90" style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)' }} data-testid="buzz-in-btn">
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
                <Link
                  to={currentResp.post_id ? `/hive?post=${currentResp.post_id}` : '#'}
                  className={`flex items-center gap-3 transition-all duration-300 rounded-lg p-2 -m-2 ${currentResp.post_id ? 'hover:bg-amber-100/40 cursor-pointer' : ''}`}
                  onClick={e => { if (!currentResp.post_id) e.preventDefault(); }}
                  data-testid="prompt-response-link"
                >
                  {/* Album art — GPU-accelerated with dominant color background */}
                  <div className="relative shrink-0 w-16 h-16 rounded-lg overflow-hidden"
                    style={{
                      backgroundColor: currentResp.dominant_color || '#1A1A1A',
                      transform: 'translateZ(0)',
                      willChange: 'transform',
                    }}
                    data-testid="prompt-album-art-container"
                  >
                    {currentResp.cover_url ? <AlbumArt src={currentResp.cover_url} alt={`${currentResp.record_artist || ''} ${currentResp.record_title || ''} vinyl record`} className="w-full h-full object-cover" blurDataUrl={currentResp.blur_data_url} thumbSrc={currentResp.thumb_url} priority={carouselIdx === 0} /> : <div className="w-full h-full flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
                    {currentResp.color_variant && (
                      <div className="absolute bottom-0.5 right-0.5 max-w-[90%] truncate uppercase text-[8px] font-bold px-1 py-0.5 rounded-full"
                        style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}>
                        {currentResp.color_variant}
                      </div>
                    )}
                    {/* Streaming overlay icons */}
                    {!currentResp.color_variant && (
                      <div className="absolute bottom-0.5 right-0.5 z-[7] flex items-center gap-0.5 pointer-events-auto">
                        {currentResp.record_artist && currentResp.record_title && (() => {
                          const q = encodeURIComponent(`${currentResp.record_artist} ${currentResp.record_title}`);
                          return (
                            <>
                              <a href={`https://open.spotify.com/search/${q}`} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                                className="w-5 h-5 rounded-full flex items-center justify-center transition-all hover:scale-110"
                                style={{ background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(6px)' }}
                                data-testid="prompt-streaming-spotify">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="rgba(255,255,255,0.6)"
                                  onMouseEnter={e => e.currentTarget.style.fill = '#1DB954'}
                                  onMouseLeave={e => e.currentTarget.style.fill = 'rgba(255,255,255,0.6)'}>
                                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                                </svg>
                              </a>
                              <a href={`https://music.apple.com/us/search?term=${q}`} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                                className="w-5 h-5 rounded-full flex items-center justify-center transition-all hover:scale-110"
                                style={{ background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(6px)' }}
                                data-testid="prompt-streaming-apple">
                                <svg width="9" height="9" viewBox="0 0 24 24" fill="rgba(255,255,255,0.6)"
                                  onMouseEnter={e => e.currentTarget.style.fill = '#FC3C44'}
                                  onMouseLeave={e => e.currentTarget.style.fill = 'rgba(255,255,255,0.6)'}>
                                  <path d="M23.994 6.124a9.23 9.23 0 00-.24-2.19c-.317-1.31-1.062-2.31-2.18-3.043a5.022 5.022 0 00-1.877-.726 10.496 10.496 0 00-1.564-.15c-.04-.003-.083-.01-.124-.013H5.986c-.152.01-.303.017-.455.026-.747.043-1.49.123-2.193.4-1.336.53-2.3 1.452-2.865 2.78-.192.448-.292.925-.363 1.408-.056.392-.088.785-.1 1.18 0 .032-.007.062-.01.093v12.223c.01.14.017.283.027.424.05.815.154 1.624.497 2.373.65 1.42 1.738 2.353 3.234 2.802.42.127.856.187 1.293.228.555.053 1.11.06 1.667.06h11.03a12.5 12.5 0 001.57-.1c.822-.106 1.596-.35 2.295-.81a5.046 5.046 0 001.88-2.207c.186-.42.293-.87.37-1.324.113-.675.138-1.358.137-2.04-.002-3.8 0-7.595-.003-11.393zm-6.423 3.99v5.712c0 .417-.058.827-.244 1.206-.29.59-.76.962-1.388 1.14-.35.1-.706.157-1.07.173-.95.042-1.8-.6-1.965-1.48-.18-.965.407-1.867 1.35-2.076.39-.086.784-.14 1.176-.208.254-.046.464-.175.56-.433.05-.14.073-.29.073-.443V10.12a.507.507 0 00-.4-.497c-.09-.02-.183-.03-.273-.042-.578-.074-1.156-.14-1.734-.218-.378-.05-.756-.104-1.132-.162a.475.475 0 00-.076-.003c-.318.008-.512.2-.512.52-.003 2.563-.002 5.124-.005 7.687 0 .373-.047.74-.2 1.084-.307.69-.827 1.1-1.566 1.27-.325.074-.655.117-.99.128a1.79 1.79 0 01-1.723-1.13 1.756 1.756 0 011.028-2.386c.395-.137.81-.2 1.22-.27.274-.047.5-.182.598-.463.045-.128.063-.266.063-.403V7.272c0-.37.148-.634.49-.803.126-.062.263-.1.4-.125l4.148-.753c.308-.056.617-.108.927-.153.088-.013.178-.01.265.004.282.05.435.233.454.52.003.058.004.117.004.176 0 1.262 0 2.524-.003 3.786z"/>
                                </svg>
                              </a>
                            </>
                          );
                        })()}
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
                </Link>
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
                placeholder="My take on today's prompt is..."
                value={caption} onChange={e => setCaption(e.target.value)}
                className="border-amber-200 resize-none" rows={2}
                data-testid="buzz-caption"
              />
              <p className="text-[10px] text-muted-foreground/70 italic">A comment is required to share on the feed.</p>

              <div className="flex justify-center">
                <Button onClick={() => handleSubmit(true)} disabled={submitting || !selectedRecordId || !caption.trim()}
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
