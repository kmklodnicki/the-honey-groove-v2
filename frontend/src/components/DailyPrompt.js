import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Textarea } from './ui/textarea';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import MentionText from './MentionText';
import { Loader2, Disc, Share2, Send, Download, Search, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { useShareCard } from '../hooks/useShareCard';
import DailyPromptShareCard from './ShareCards/DailyPromptCard';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import RecordSearchResult from './RecordSearchResult';
import AlbumArt from './AlbumArt';
import { resolveImageUrl, proxyImageUrl } from '../utils/imageUrl';
import { prefetchImages } from '../utils/imagePrefetch';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Link, useSearchParams } from 'react-router-dom';
import PromptArchiveDrawer from './PromptArchiveDrawer';
import { useVariantModal } from '../context/VariantModalContext';

// ─── Daily Prompt Card (top of Hive feed) ───

// Hydrate from cache for instant render (SWR pattern)
const cachedPrompt = (() => {
  try {
    const raw = localStorage.getItem('hg_daily_prompt_cache');
    if (!raw) return null;
    const data = JSON.parse(raw);
    // Only use cache from today (UTC)
    const today = new Date().toISOString().slice(0, 10);
    if (data.date !== today) return null;
    return data;
  } catch { return null; }
})();

export const DailyPromptCard = ({ records, onPostCreated }) => {
  const { user, token, API } = useAuth();
  const { openVariantModal } = useVariantModal();
  const [prompt, setPrompt] = useState(cachedPrompt?.prompt || null);
  const [hasBuzzedIn, setHasBuzzedIn] = useState(cachedPrompt?.has_buzzed_in || false);
  const [buzzResponse, setBuzzResponse] = useState(cachedPrompt?.response || null);
  const [streak, setStreak] = useState(cachedPrompt?.streak || 0);
  const [missedYesterday, setMissedYesterday] = useState(false);
  const [buzzCount, setBuzzCount] = useState(cachedPrompt?.buzz_count || 0);
  const [loading, setLoading] = useState(!cachedPrompt);
  const hasFetchedRef = useRef(!!cachedPrompt);
  const [modalOpen, setModalOpen] = useState(false);
  // Carousel state
  const [responses, setResponses] = useState([]);
  const [carouselIdx, setCarouselIdx] = useState(0);
  const [loadingResponses, setLoadingResponses] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const { cardRef: cardShareRef, exporting: cardShareExporting, exportCard: exportCardShare } = useShareCard({
    cardType: 'daily_prompt',
    filename: 'thg-daily-prompt',
    title: 'My Daily Prompt answer — The Honey Groove',
    userId: user?.id,
  });

  // Guarded share handler — logs missing data and shows a helpful toast instead of
  // a generic html2canvas error when buzzResponse hasn't been enriched with cover data yet.
  const handleCardShare = useCallback(() => {
    const cover = buzzResponse?.cover_url;
    const title = buzzResponse?.record_title;
    const artist = buzzResponse?.record_artist;
    if (!cover || !title || !artist) {
      console.error('[DailyPrompt] Share card missing data:', { cover_url: cover, record_title: title, record_artist: artist, buzzResponse });
      toast.error('Record data still loading — try again in a moment.');
      return;
    }
    exportCardShare([resolveImageUrl(cover)]);
  }, [buzzResponse, exportCardShare]); // eslint-disable-line react-hooks/exhaustive-deps

  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get('highlight');
useEffect(() => {
    if (highlightId && responses.length > 0) {
      // Find where the post is in the array
      const targetIndex = responses.findIndex(r => String(r.id) === String(highlightId));
      
      if (targetIndex !== -1) {
        // Jump the carousel to that specific slide index
        setCarouselIdx(targetIndex);
      }
    }
  }, [highlightId, responses]);

  const fetchPrompt = useCallback(async (signal) => {
    if (!hasFetchedRef.current) setLoading(true);
    try {
      const r = await axios.get(`${API}/prompts/today`, {
        headers: { Authorization: `Bearer ${token}` },
        signal,
      });
      setPrompt(r.data.prompt || null);
      setHasBuzzedIn(r.data.has_buzzed_in || false);
      setBuzzResponse(r.data.response || null);
      setStreak(r.data.streak || 0);
      setMissedYesterday(r.data.missed_yesterday || false);
      setBuzzCount(r.data.buzz_count || 0);
      hasFetchedRef.current = true;
      // Cache for instant render on next visit (SWR pattern)
      try {
        const today = new Date().toISOString().slice(0, 10);
        localStorage.setItem('hg_daily_prompt_cache', JSON.stringify({
          date: today,
          prompt: r.data.prompt || null,
          has_buzzed_in: r.data.has_buzzed_in || false,
          response: r.data.response || null,
          streak: r.data.streak || 0,
          buzz_count: r.data.buzz_count || 0,
        }));
      } catch { /* quota exceeded — ignore */ }
    } catch (e) {
      if (e?.name === 'CanceledError' || e?.name === 'AbortError') return;
      setPrompt(null);
    }
    setLoading(false);
  }, [API, token]);

  useEffect(() => {
    const controller = new AbortController();
    fetchPrompt(controller.signal);
    return () => controller.abort();
  }, [fetchPrompt]);

  // Fetch carousel responses after buzzing in
  const fetchResponses = useCallback(async () => {
    if (!prompt || !hasBuzzedIn) return;
    setLoadingResponses(true);
    try {
      const r = await axios.get(`${API}/prompts/${prompt.id}/responses`, { headers: { Authorization: `Bearer ${token}` } });
      setResponses(r.data);
      setCarouselIdx(0);
      // Augment buzzResponse with cover data from the user's own carousel entry.
      // The API /prompts/today response never includes cover_url; the responses
      // endpoint does — this is the only way to restore cover data on page reload.
      const myResp = r.data.find(resp => resp.username === user?.username);
      if (myResp?.cover_url) {
        setBuzzResponse(prev => prev ? {
          ...prev,
          cover_url: prev.cover_url || myResp.cover_url,
          record_title: prev.record_title || myResp.record_title,
          record_artist: prev.record_artist || myResp.record_artist,
        } : prev);
      }
      // BLOCK 444: Prefetch current + next 3 slides' images
      const urls = r.data
        .slice(0, 4)
        .map(resp => resp.cover_url ? resolveImageUrl(resp.cover_url) : null)
        .filter(Boolean);
      prefetchImages(urls);
      // BLOCK 321: Also send all response images to SW for persistent cache
      const allUrls = r.data
        .map(resp => resp.cover_url ? resolveImageUrl(resp.cover_url) : null)
        .filter(Boolean);
      if (allUrls.length > 0 && navigator.serviceWorker?.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: 'PREFETCH_DAILY_PROMPT',
          urls: allUrls,
        });
      }
    } catch { /* ignore */ }
    finally { setLoadingResponses(false); }
  }, [API, token, prompt, hasBuzzedIn, user]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetchResponses(); }, [fetchResponses]);

  // BLOCK 444: Rolling buffer — prefetch 2 slides ahead as user navigates
  useEffect(() => {
    if (responses.length === 0) return;
    const ahead = [carouselIdx + 1, carouselIdx + 2]
      .filter(i => i < responses.length)
      .map(i => responses[i]?.cover_url ? resolveImageUrl(responses[i].cover_url) : null)
      .filter(Boolean);
    if (ahead.length > 0) prefetchImages(ahead);
  }, [carouselIdx, responses]);

  if (loading) return (
    <Card className="my-4 p-5 border-[#E5DBC8]/60 overflow-hidden" style={{ background: 'linear-gradient(135deg, rgba(255,179,0,0.08), rgba(255,160,0,0.04))' }}>
      <div className="h-4 w-24 rounded-full mb-3" style={{ background: 'rgba(200,134,26,0.12)' }} />
      <div className="h-7 w-4/5 rounded-full mb-3" style={{ background: 'rgba(200,134,26,0.08)' }} />
      <div className="h-10 w-32 rounded-full" style={{ background: 'rgba(200,134,26,0.1)' }} />
    </Card>
  );
  if (!prompt) return null;

  const currentResp = responses[carouselIdx];

  return (
    <>
      <Card className="my-4 border-[#E5DBC8]/60 overflow-hidden relative" style={{ background: '#FFFBF2' }} data-testid="daily-prompt-card">
        {/* Slate-blue header bar */}
        <div className="flex items-center justify-between px-4 py-2.5" style={{ background: '#354B66' }}>
          <p className="text-[11px] uppercase tracking-widest font-semibold" style={{ color: '#D4A828' }}>Daily Prompt</p>
          {buzzCount > 0 && (
            <a
              href={`/hive?prompt_id=${prompt.id}`}
              className="flex items-center gap-1 text-[11px] font-bold transition relative z-10"
              style={{ color: '#E8CA5A' }}
              data-testid="buzz-count-top"
            >
              <span style={{ background: '#1E2A3A', color: '#E8CA5A', borderRadius: '9999px', padding: '1px 7px', fontSize: '10px' }}>
                {buzzCount} buzzed in
              </span>
            </a>
          )}
        </div>
        {/* Card body */}
        <div className="p-5">
        <p className="font-heading text-xl md:text-2xl text-vinyl-black leading-snug mb-3 italic" data-testid="daily-prompt-text">
          {prompt.text}
        </p>

        {!hasBuzzedIn ? (
          /* ── GATEKEEPER: Pre-buzz state ── */
          <div>
            {buzzCount > 0 && (
              <p className="text-sm text-[#D4A828] mb-3 font-medium" data-testid="buzz-gate-msg">
                {buzzCount} member{buzzCount !== 1 ? 's' : ''} of the Hive {buzzCount === 1 ? 'has' : 'have'} buzzed in, it's your turn!
              </p>
            )}
            <div className="flex items-center justify-between">
              <Button onClick={() => setModalOpen(true)} className="text-white rounded-full px-6 text-sm font-semibold shadow-sm hover:opacity-90" style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)' }} data-testid="buzz-in-btn">
                buzz in 🐝
              </Button>
              {streak > 0 && (
                <span className="flex items-center gap-1 text-sm text-[#D4A828] font-bold">🐝 {streak} {streak === 1 ? 'day' : 'days'} in a row</span>
              )}
            </div>
          </div>
        ) : (
          /* ── REVIEW MODE: Post-buzz carousel ── */
          <div data-testid="prompt-review-mode">
            <div className="flex items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-3">
                <span className="text-sm text-[#D4A828] font-medium">buzzed in</span>
                {streak > 0 && <span className="flex items-center gap-1 text-sm text-[#D4A828] font-bold">🐝 {streak} {streak === 1 ? 'day' : 'days'} in a row</span>}
              </div>
              {buzzResponse && (
                <button
                  onClick={handleCardShare}
                  disabled={cardShareExporting}
                  className="flex items-center gap-1 text-xs font-semibold text-[#D4A828] hover:text-[#1E2A3A] transition"
                  data-testid="prompt-card-share-btn"
                >
                  {cardShareExporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Share2 className="w-3 h-3" />}
                  share
                </button>
              )}
            </div>

            {/* Carousel */}
            {loadingResponses ? (
              <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-[#D4A828]" /></div>
            ) : responses.length > 0 && currentResp ? (
              <div className="relative" data-testid="prompt-carousel">
                <Link
                  to={currentResp.post_id ? `/hive?post=${currentResp.post_id}` : '#'}
                  className={`flex items-center gap-3 transition-all duration-300 rounded-lg p-2 -m-2 ${currentResp.post_id ? 'hover:bg-[#F0E6C8]/40 cursor-pointer' : ''}`}
                  onClick={e => { if (!currentResp.post_id) e.preventDefault(); }}
                  data-testid="prompt-response-link"
                >
                  {/* Album art — GPU-accelerated with dominant color background */}
                  <div className="relative shrink-0 w-16 h-16 rounded-lg overflow-hidden"
                    style={{
                      backgroundColor: currentResp.dominant_color || '#FFB800',
                      transform: 'translateZ(0)',
                      willChange: 'transform',
                    }}
                    data-testid="prompt-album-art-container"
                  >
                    {currentResp.cover_url ? (
                      carouselIdx < 3 ? (
                        /* Priority: Direct <img> for first 3 slides — no AlbumArt state machine, zero delay */
                        <img
                          src={currentResp.proxy_cover_url ? `${API.replace('/api', '')}${currentResp.proxy_cover_url}` : resolveImageUrl(currentResp.cover_url)}
                          alt={`${currentResp.record_artist || ''} ${currentResp.record_title || ''} vinyl record`}
                          className="w-full h-full object-cover"
                          crossOrigin="anonymous"
                          fetchpriority="high"
                          decoding="sync"
                          loading="eager"
                          draggable={false}
                          onError={(e) => {
                            if (!e.target.dataset.proxied) {
                              e.target.dataset.proxied = '1';
                              e.target.src = proxyImageUrl(currentResp.cover_url);
                            }
                          }}
                        />
                      ) : (
                        <AlbumArt src={currentResp.proxy_cover_url ? `${API.replace('/api', '')}${currentResp.proxy_cover_url}` : currentResp.cover_url} alt={`${currentResp.record_artist || ''} ${currentResp.record_title || ''} vinyl record`} className="w-full h-full object-cover" blurDataUrl={currentResp.blur_data_url} thumbSrc={currentResp.thumb_url} />
                      )
                    ) : <div className="w-full h-full flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
                    {/* Variant pill — hidden on Spotify-sourced art (Spotify compliance §1.1) */}
                    {currentResp.color_variant && currentResp.image_source !== 'spotify' && (
                      <div
                        className="absolute bottom-0.5 right-0.5 max-w-[90%] truncate uppercase text-[8px] font-bold px-1 py-0.5 rounded-full cursor-pointer hover:scale-105 transition-transform"
                        style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          openVariantModal({
                            artist: currentResp.record_artist,
                            album: currentResp.record_title,
                            variant: currentResp.color_variant || 'Standard',
                            discogs_id: currentResp.discogs_id,
                            cover_url: currentResp.cover_url,
                          });
                        }}
                        data-testid="prompt-variant-pill"
                      >
                        {currentResp.color_variant}
                      </div>
                    )}
                  </div>
                  {/* Response content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span onClick={(e) => { e.preventDefault(); e.stopPropagation(); window.location.href = `/profile/${currentResp.username}`; }} className="text-xs font-bold text-vinyl-black hover:text-honey-amber transition cursor-pointer" data-testid="carousel-username">
                        @{currentResp.username}
                      </span>
                      {currentResp.username?.toLowerCase() === 'katieintheafterglow' && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-honey/20 text-[#D4A828] font-bold">Founder</span>}
                    </div>
                    <p className="text-sm font-medium truncate">{currentResp.record_title}</p>
                    <p className="text-xs text-muted-foreground truncate">{currentResp.record_artist}</p>
                    {currentResp.caption && <p className="text-xs text-[#3A4D63] mt-1 italic line-clamp-2"><MentionText text={currentResp.caption} /></p>}
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

        {/* Spotify link — Spotify compliance + dynamic per carousel item.
            Uses direct album URL (spotify_url from DB) when available; falls back
            to search. Updates automatically as the user arrows through responses.
            Hidden when the current response has no record info. */}
        {hasBuzzedIn && currentResp && (currentResp.record_title || currentResp.record_artist) && (
          <a
            href={
              currentResp.spotify_url ||
              `https://open.spotify.com/search/${encodeURIComponent(`${currentResp.record_artist || ''} ${currentResp.record_title || ''}`.trim())}`
            }
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            className="inline-flex items-center gap-1.5 mt-2 text-xs text-[#7A8694] hover:text-[#1DB954] transition-colors"
            data-testid="prompt-spotify-link"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
            Listen on Spotify
          </a>
        )}

        {/* Centered archive link — secondary explore action */}
        {/* Re-pollinate: only show when user missed yesterday's prompt */}
        {(() => {
          if (!missedYesterday) return null;
          return (
            <div className="flex justify-center mt-3">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={async () => {
                        try {
                          const res = await axios.post(`${API}/repollinate/checkout`, {}, { headers: { Authorization: `Bearer ${token}` } });
                          window.location.href = res.data.url;
                        } catch { toast.error('Could not start checkout.'); }
                      }}
                      className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold transition-all hover:scale-105 hover:shadow-md"
                      style={{ background: '#FDE68A', color: '#915527', border: '1px solid #E5C76B' }}
                      data-testid="repollinate-btn"
                    >
                      Re-pollinate 🐝
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="max-w-xs text-xs">
                    Lost your streak? No worries, just re-pollinate! You have 48 hours to save your daily spin. ($1.99 per transaction)
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          );
        })()}
        {/* Mini Groove — temporarily hidden */}
        {false && (
        <div className="text-center mt-4">
          <button
            onClick={() => setArchiveOpen(true)}
            className="text-[11px] text-[#D4A828]/50 hover:text-[#1E2A3A] hover:underline transition font-medium inline-flex items-center gap-1"
            data-testid="prompt-archive-link"
          >
            See what the Hive said yesterday <span className="text-[10px]">&rarr;</span>
          </button>
        </div>
        )}
        </div>{/* /p-5 body */}
      </Card>

      <DailyPromptShareCard
        ref={cardShareRef}
        promptQuestion={prompt?.text}
        record={{
          cover_url: buzzResponse?.cover_url,
          title: buzzResponse?.record_title,
          artist: buzzResponse?.record_artist,
        }}
        user={user}
      />

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

      {/* Mini Groove drawer — temporarily hidden */}
      {false && <PromptArchiveDrawer open={archiveOpen} onOpenChange={setArchiveOpen} />}
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
  const { cardRef: promptShareRef, exporting: promptShareExporting, exportCard: exportPromptCard } = useShareCard({
    cardType: 'daily_prompt',
    filename: 'thg-daily-prompt',
    title: `My Daily Prompt answer — The Honey Groove`,
    userId: user?.id,
  });

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
      onSuccess?.({ ...r.data, cover_url: discogsData?.cover_url || selectedRecord?.cover_url, record_title: displayData?.title || selectedRecord?.title, record_artist: displayData?.artist || selectedRecord?.artist });
    } catch (err) {
      // Retry once if prompt_id is stale (cleanup replaced it)
      if (err.response?.status === 404 && err.response?.data?.detail?.includes('not found')) {
        try {
          const fresh = await axios.get(`${API}/prompts/today`, { headers: { Authorization: `Bearer ${token}` } });
          const freshPrompt = fresh.data.prompt;
          if (freshPrompt && freshPrompt.id !== prompt.id) {
            setPrompt(freshPrompt);
            const retry = await axios.post(`${API}/prompts/buzz-in`, {
              prompt_id: freshPrompt.id,
              record_id: selectedRecordId,
              caption,
              post_to_hive: postToHive,
            }, { headers: { Authorization: `Bearer ${token}` } });
            setResponseData(retry.data);
            trackEvent('daily_prompt_answered');
            toast.success(postToHive ? 'Buzzed in & posted to The Hive!' : 'Buzzed in!');
            onSuccess?.({ ...retry.data, cover_url: discogsData?.cover_url || selectedRecord?.cover_url, record_title: displayData?.title || selectedRecord?.title, record_artist: displayData?.artist || selectedRecord?.artist });
            setSubmitting(false);
            return;
          }
        } catch { /* retry failed — fall through to original error */ }
      }
      toast.error(err.response?.data?.detail || 'Failed');
    }
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
          <DialogDescription className="italic text-[#D4A828]">{prompt?.text}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          {!responseData ? (
            <>
              {/* Record search */}
              <div>
                <label className="text-sm font-medium mb-1 block text-[#1E2A3A]">Record</label>
                {!selectedRecord ? (
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="search your vault..."
                      value={buzzSearch}
                      onChange={e => { setBuzzSearch(e.target.value); searchCollection(e.target.value); }}
                      className="pl-9 border-[#E5DBC8]"
                      data-testid="buzz-record-search"
                      autoFocus
                    />
                    {buzzSearchResults.length > 0 && (
                      <div className="absolute z-50 left-0 right-0 mt-1 border border-[#E5DBC8]/60 rounded-lg max-h-52 overflow-y-auto shadow-lg bg-white" data-testid="buzz-search-results">
                        {buzzSearchResults.map(r => (
                          <RecordSearchResult key={r.id} record={r} onClick={() => selectBuzzRecord(r)} size="sm" testId={`buzz-result-${r.id}`} />
                        ))}
                      </div>
                    )}
                    {buzzSearch.length >= 2 && buzzSearchResults.length === 0 && (
                      <div className="absolute z-50 left-0 right-0 mt-1 border border-[#E5DBC8]/60 rounded-lg p-4 text-center shadow-lg bg-white" data-testid="buzz-no-results">
                        <p className="text-sm text-[#D4A828]">no results in your vault</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-3 rounded-lg p-2.5 bg-[#F0E6C8]/60 border border-[#E5DBC8]" data-testid="buzz-selected-record">
                    {selectedRecord.cover_url ? (
                      <AlbumArt src={selectedRecord.cover_url} alt={`${selectedRecord.title} by ${selectedRecord.artist}`} className="w-11 h-11 rounded-md object-cover shadow-sm" />
                    ) : (
                      <div className="w-11 h-11 rounded-md bg-[#F0E6C8] flex items-center justify-center"><Disc className="w-5 h-5 text-[#D4A828]" /></div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{selectedRecord.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{selectedRecord.artist}</p>
                    </div>
                    <button onClick={deselectBuzzRecord} className="p-1 rounded-full hover:bg-[#F0E6C8] text-[#D4A828]" data-testid="buzz-deselect-record">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Live preview */}
              {selectedRecordId && (
                <div className="bg-[#FFFBF2] rounded-xl p-4 space-y-3 border border-[#E5DBC8]" data-testid="buzz-preview">
                  <p className="text-center italic text-[#D4A828] text-sm">{prompt?.text}</p>
                  {loadingDiscogs ? (
                    <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-[#D4A828]" /></div>
                  ) : (
                    <>
                      <div className="flex justify-center">
                        {coverUrl ? (
                          <img src={coverUrl} alt="" className="w-40 h-40 rounded-xl object-cover shadow-md" />
                        ) : (
                          <div className="w-40 h-40 rounded-xl bg-[#F0E6C8] flex items-center justify-center"><Disc className="w-10 h-10 text-[#D4A828]" /></div>
                        )}
                      </div>
                      <div className="text-center">
                        <p className="font-heading text-lg">{displayData?.title || 'Unknown'}</p>
                        <p className="text-sm text-muted-foreground">{displayData?.artist || 'Unknown'}</p>
                        {(labelText || yearText) && (
                          <p className="text-xs text-[#D4A828] italic mt-1">
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
                className="border-[#E5DBC8] resize-none" rows={2}
                data-testid="buzz-caption"
              />
              <p className="text-[10px] text-muted-foreground/70 italic">A comment is required to share on the feed.</p>

              <div className="flex justify-center">
                <Button onClick={() => handleSubmit(true)} disabled={submitting || !selectedRecordId || !caption.trim()}
                  className="rounded-full bg-[#D4A828] hover:bg-[#E8CA5A] text-white w-full" data-testid="buzz-post-hive-btn">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Send className="w-4 h-4 mr-1" />}
                  post to the hive
                </Button>
              </div>
            </>
          ) : (
            /* Post-submit: success message */
            <div className="text-center space-y-4">
              <div className="bg-[#F0E6C8] rounded-xl p-4">
                <p className="text-[#D4A828] font-medium mb-1">buzzed in!</p>
                {responseData.streak > 0 && (
                  <p className="flex items-center justify-center gap-1 text-[#D4A828] font-bold text-lg">
                    {responseData.streak} {responseData.streak === 1 ? 'day' : 'days'} in a row
                  </p>
                )}
              </div>
              <Button
                onClick={exportPromptCard}
                disabled={promptShareExporting}
                className="w-full rounded-full text-white font-semibold"
                style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)' }}
                data-testid="prompt-share-card-btn"
              >
                {promptShareExporting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Share2 className="w-4 h-4 mr-2" />}
                share your answer
              </Button>
              <Button variant="ghost" onClick={() => onOpenChange(false)} className="w-full text-muted-foreground">
                done
              </Button>
              <DailyPromptShareCard
                ref={promptShareRef}
                promptQuestion={prompt?.text}
                record={selectedRecord}
                user={user}
              />
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
    <div className="flex items-center gap-1.5 text-[#D4A828] font-bold text-sm" data-testid="profile-streak-badge">
      🐝 {streak} {streak === 1 ? 'day' : 'days'} in a row
    </div>
  );
};

export default DailyPromptCard;
