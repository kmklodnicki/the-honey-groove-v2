import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import MentionTextarea from './MentionTextarea';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { Disc, Package, Search, Loader2, X, Feather, ImagePlus, Tag, Shuffle, ChevronDown, Music, RefreshCw, Camera } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import AlbumArt from './AlbumArt';
import RecordSearchResult from './RecordSearchResult';

const MOOD_CONFIG = {
  'New Arrival': { emoji: '\u{1F4E6}', bg: '#1a1a08', btnColor: '#c8861a', placeholder: 'what just came in the mail?' },
  'Deep Listening': { emoji: '\u{1F9D8}', bg: '#0a1a2a', btnColor: '#4a7aaa', placeholder: 'what are you really hearing right now?' },
  'In The Zone': { emoji: '\u{1F3AF}', bg: '#0a1a0a', btnColor: '#2a6a2a', placeholder: 'locked in. what are you working to?' },
  'Me Time': { emoji: '\u{1F9CD}', bg: '#1a1230', btnColor: '#6a3a9a', placeholder: 'just you and the record...' },
  'Cleaning Session': { emoji: '\u{1F9FC}', bg: '#0a2a1a', btnColor: '#3a9a5a', placeholder: 'fresh grooves only...' },
  'Spin Party': { emoji: '\u{1FA69}', bg: '#1a0a2a', btnColor: '#aa3a8a', placeholder: "who's pulling up?" },
  'Limited Edition': { emoji: '\u{1F48E}', bg: '#0a0a2a', btnColor: '#5a5aaa', placeholder: 'how rare is this one?' },
  'Vibe Check': { emoji: '\u2728', bg: '#2a1a08', btnColor: '#aa7a3a', placeholder: "what's the vibe?" },
  'Late Night': { emoji: '\u{1F319}', bg: '#0a0a1a', btnColor: '#4a4a8a', placeholder: 'what are you listening to at this hour?' },
  'Background': { emoji: '\u2615', bg: '#1a1208', btnColor: '#8a6a3a', placeholder: "what's on in the background?" },
  'In My Feels': { emoji: '\u{1F972}', bg: '#1a1a2a', btnColor: '#5a5a8a', placeholder: 'some records just hit different...' },
  'Daydreaming': { emoji: '\u2601\uFE0F', bg: '#0a1a2a', btnColor: '#6a8aaa', placeholder: 'where is this record taking you?' },
};
const MOOD_KEYS = Object.keys(MOOD_CONFIG);

const ComposerBar = ({ onPostCreated, records = [] }) => {
  const { token, API, user } = useAuth();
  const isAdmin = user?.is_admin === true;
  const [activeModal, setActiveModal] = useState(null);
  const openModal = (key) => { resetAll(); setActiveModal(key); };
  const closeModal = () => setActiveModal(null);
  const [submitting, setSubmitting] = useState(false);

  // Now Spinning (merged with mood)
  const [spinRecordId, setSpinRecordId] = useState('');
  const [spinTrack, setSpinTrack] = useState('');
  const [spinCaption, setSpinCaption] = useState('');
  const [spinMood, setSpinMood] = useState('');
  const [spinSearch, setSpinSearch] = useState('');
  const [spinSearchResults, setSpinSearchResults] = useState([]);
  const [spinSelectedRecord, setSpinSelectedRecord] = useState(null);
  const spinSearchTimer = useRef(null);
  const [spinTracks, setSpinTracks] = useState([]);
  const [spinTracksLoading, setSpinTracksLoading] = useState(false);
  const [spinTrackDropdownOpen, setSpinTrackDropdownOpen] = useState(false);
  const [spinTrackSearch, setSpinTrackSearch] = useState('');
  const [spinTracksFetched, setSpinTracksFetched] = useState(false);
  const [spinTrackManual, setSpinTrackManual] = useState(false);

  // New Haul
  const [haulStoreName, setHaulStoreName] = useState('');
  const [haulCaption, setHaulCaption] = useState('');
  const [haulSearch, setHaulSearch] = useState('');
  const [haulResults, setHaulResults] = useState([]);
  const [haulItems, setHaulItems] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // ISO
  const [isoArtist, setIsoArtist] = useState('');
  const [isoAlbum, setIsoAlbum] = useState('');
  const [isoPressing, setIsoPressing] = useState('');
  const [isoCondition, setIsoCondition] = useState('');
  const [isoPriceMin, setIsoPriceMin] = useState('');
  const [isoPriceMax, setIsoPriceMax] = useState('');
  const [isoCaption, setIsoCaption] = useState('');
  const [isoDiscogsQuery, setIsoDiscogsQuery] = useState('');
  const [isoDiscogsResults, setIsoDiscogsResults] = useState([]);
  const [isoSearchLoading, setIsoSearchLoading] = useState(false);
  const [isoSelectedRelease, setIsoSelectedRelease] = useState(null);
  const [isoManualMode, setIsoManualMode] = useState(false);
  const [isoIntent, setIsoIntent] = useState(null);

  // A Note
  const [noteText, setNoteText] = useState('');
  const [noteRecordId, setNoteRecordId] = useState('');
  const [noteShowRecordPicker, setNoteShowRecordPicker] = useState(false);
  const [noteImageUrl, setNoteImageUrl] = useState('');
  const [noteUploading, setNoteUploading] = useState(false);
  const noteFileRef = useRef(null);
  // Dedicated photo state for Spinning/Haul
  const [postPhoto, setPostPhoto] = useState(null);
  const [postPhotoPreview, setPostPhotoPreview] = useState(null);
  const postPhotoInputRef = useRef(null);
  // Randomizer
  const [randRecord, setRandRecord] = useState(null);
  const [randCaption, setRandCaption] = useState('');
  const [randLoading, setRandLoading] = useState(false);
  const [randAnimating, setRandAnimating] = useState(false);

  const resetAll = () => {
    setSpinRecordId(''); setSpinTrack(''); setSpinCaption(''); setSpinMood('');
    setSpinSearch(''); setSpinSearchResults([]); setSpinSelectedRecord(null);
    setSpinTracks([]); setSpinTracksLoading(false); setSpinTrackDropdownOpen(false); setSpinTrackSearch(''); setSpinTracksFetched(false);
    setHaulStoreName(''); setHaulCaption(''); setHaulItems([]); setHaulSearch(''); setHaulResults([]);
    setIsoArtist(''); setIsoAlbum(''); setIsoPressing(''); setIsoCondition('');
    setIsoPriceMin(''); setIsoPriceMax(''); setIsoCaption('');
    setIsoDiscogsQuery(''); setIsoDiscogsResults([]); setIsoSelectedRelease(null); setIsoManualMode(false); setIsoIntent(null);
    setNoteText(''); setNoteRecordId(''); setNoteShowRecordPicker(false); setNoteImageUrl(''); setNoteUploading(false);
    setRandRecord(null); setRandCaption(''); setRandLoading(false); setRandAnimating(false);
    setPostPhoto(null); setPostPhotoPreview(null);
    if (postPhotoInputRef.current) postPhotoInputRef.current.value = '';
  };
  const handlePhotoSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPostPhoto(file);
      setPostPhotoPreview(URL.createObjectURL(file));
    }
  };

  const clearPostPhoto = () => {
    setPostPhoto(null);
    setPostPhotoPreview(null);
    if (postPhotoInputRef.current) postPhotoInputRef.current.value = '';
  };
  const haulSearchTimer = useRef(null);
  const isoSearchTimer = useRef(null);

  useEffect(() => {
    return () => {
      if (haulSearchTimer.current) clearTimeout(haulSearchTimer.current);
      if (isoSearchTimer.current) clearTimeout(isoSearchTimer.current);
      if (spinSearchTimer.current) clearTimeout(spinSearchTimer.current);
    };
  }, []);

  // Close track dropdown when clicking outside
  const trackDropdownRef = useRef(null);
  useEffect(() => {
    if (!spinTrackDropdownOpen) return;
    const handleClickOutside = (e) => {
      if (trackDropdownRef.current && !trackDropdownRef.current.contains(e.target)) {
        setSpinTrackDropdownOpen(false);
        setSpinTrackSearch('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [spinTrackDropdownOpen]);

  // Local collection search for Now Spinning
  const searchCollection = useCallback((query) => {
    if (spinSearchTimer.current) clearTimeout(spinSearchTimer.current);
    if (!query || query.length < 2) { setSpinSearchResults([]); return; }
    spinSearchTimer.current = setTimeout(() => {
      const words = query.toLowerCase().split(/\s+/).filter(Boolean);
      const scored = records
        .filter(r => {
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
        .sort((a, b) => b._score - a._score);
      setSpinSearchResults(scored);
    }, 300);
  }, [records]);

  const selectSpinRecord = (rec) => {
    setSpinSelectedRecord(rec);
    setSpinRecordId(rec.id);
    setSpinSearch('');
    setSpinSearchResults([]);
    setSpinTrack('');
    setSpinTracks([]);
    setSpinTrackSearch('');
    setSpinTracksFetched(false);
    // Fetch tracklist if the record has a discogs_id
    if (rec.discogs_id) {
      fetchTracklist(rec.discogs_id);
    }
  };

  const fetchTracklist = (discogsId, isRetry = false) => {
    setSpinTracksLoading(true);
    setSpinTracksFetched(false);
    setSpinTracks([]);
    setSpinTrack('');
    setSpinTrackSearch('');
    setSpinTrackManual(false);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    axios.get(`${API}/discogs/release/${discogsId}`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    }).then(resp => {
      console.log('[Tracklist] Raw API response for', discogsId, resp.data);
      const raw = resp.data;
      const trackArray = raw.tracklist || raw.tracks || [];
      const tracks = trackArray.filter(t => t && (t.title || t.name));
      const normalized = tracks.map(t => ({
        position: t.position || '',
        title: t.title || t.name || '',
        duration: t.duration || '',
      }));
      console.log('[Tracklist] Parsed', normalized.length, 'tracks');
      setSpinTracks(normalized);
      setSpinTracksLoading(false);
      setSpinTracksFetched(true);
      // Auto-open the dropdown so user sees tracks immediately
      if (normalized.length > 0) setSpinTrackDropdownOpen(true);
    }).catch(err => {
      console.warn('[Tracklist] Fetch failed for', discogsId, err.message, isRetry ? '(retry)' : '');
      clearTimeout(timeout);
      if (!isRetry) {
        // Silent retry after 2s on first failure
        setTimeout(() => fetchTracklist(discogsId, true), 2000);
      } else {
        setSpinTracks([]);
        setSpinTracksLoading(false);
        setSpinTracksFetched(true);
      }
    }).finally(() => {
      clearTimeout(timeout);
    });
  };

  const deselectSpinRecord = () => {
    setSpinSelectedRecord(null);
    setSpinRecordId('');
    setSpinTrack('');
    setSpinTracks([]);
    setSpinTracksLoading(false);
    setSpinTrackDropdownOpen(false);
    setSpinTrackSearch('');
    setSpinTracksFetched(false);
  };

  const searchDiscogs = useCallback((query) => {
    if (!query || query.length < 2) { setHaulResults([]); setSearchLoading(false); return; }
    if (haulSearchTimer.current) clearTimeout(haulSearchTimer.current);
    haulSearchTimer.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const resp = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(query)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setHaulResults(resp.data.slice(0, 8));
      } catch { setHaulResults([]); }
      finally { setSearchLoading(false); }
    }, 350);
  }, [API, token]);

  const searchDiscogsForISO = useCallback((query) => {
    if (!query || query.length < 2) { setIsoDiscogsResults([]); setIsoSearchLoading(false); return; }
    if (isoSearchTimer.current) clearTimeout(isoSearchTimer.current);
    isoSearchTimer.current = setTimeout(async () => {
      setIsoSearchLoading(true);
      try {
        const resp = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(query)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setIsoDiscogsResults(resp.data.slice(0, 8));
      } catch { setIsoDiscogsResults([]); }
      finally { setIsoSearchLoading(false); }
    }, 350);
  }, [API, token]);

  const selectIsoRelease = (release) => {
    setIsoSelectedRelease(release); setIsoDiscogsResults([]); setIsoDiscogsQuery('');
    setIsoArtist(release.artist); setIsoAlbum(release.title);
  };

  const addHaulItem = (item) => {
    if (haulItems.find(h => h.discogs_id === item.discogs_id)) return;
    setHaulItems(prev => [...prev, { discogs_id: item.discogs_id, title: item.title, artist: item.artist, cover_url: item.cover_url, year: item.year }]);
    setHaulSearch(''); setHaulResults([]);
  };

  // Randomizer helpers
  const fetchRandomRecord = useCallback(async () => {
    setRandLoading(true);
    setRandAnimating(true);
    try {
      const resp = await axios.get(`${API}/collection/random`, { headers: { Authorization: `Bearer ${token}` } });
      setTimeout(() => { setRandRecord(resp.data); setRandAnimating(false); }, 400);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not pick a random record');
      setRandAnimating(false);
    } finally { setRandLoading(false); }
  }, [API, token]);

  const openRandomizer = () => { resetAll(); setActiveModal('RANDOMIZER'); fetchRandomRecord(); };

  const submitRandomPost = async () => {
    if (!randRecord) return;
    setSubmitting(true);
    try {
      await axios.post(`${API}/composer/randomizer`, {
        record_id: randRecord.id,
        caption: randCaption || null,
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('posted to the hive.');
      trackEvent('randomizer_post');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  // Upload photo helper
  const uploadPostPhoto = async () => {
    if (!postPhoto) return null;
    const formData = new FormData();
    formData.append('file', postPhoto);
    const res = await axios.post(`${API}/upload`, formData, {
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
    });
    return res.data.url;
  };

  // Submit handlers
  const submitNowSpinning = async () => {
    if (!spinRecordId) { toast.error('select a record first.'); return; }
    setSubmitting(true);
    try {
      let photoUrl = null;
      if (postPhoto) photoUrl = await uploadPostPhoto();
      await axios.post(`${API}/composer/now-spinning`, {
        record_id: spinRecordId,
        track: spinTrack || null,
        caption: spinCaption || null,
        mood: spinMood || null,
        photo_url: photoUrl,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success('now spinning posted.');
      trackEvent('now_spinning_posted');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const submitNewHaul = async () => {
    if (haulItems.length === 0) { toast.error('add at least one record.'); return; }
    setSubmitting(true);
    try {
      let photoUrl = null;
      if (postPhoto) photoUrl = await uploadPostPhoto();
      await axios.post(`${API}/composer/new-haul`, {
        store_name: haulStoreName || null, caption: haulCaption || null, items: haulItems,
        image_url: photoUrl,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success('haul posted.');
      trackEvent('haul_posted');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const submitISO = async () => {
    const artist = isoArtist || isoSelectedRelease?.artist;
    const album = isoAlbum || isoSelectedRelease?.title;
    if (!artist || !album) { toast.error('artist and album are required.'); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/composer/iso`, {
        artist, album,
        discogs_id: isoSelectedRelease?.discogs_id || null,
        cover_url: isoSelectedRelease?.cover_url || null,
        year: isoSelectedRelease?.year || null,
        pressing_notes: isoPressing || null,
        condition_pref: isoCondition || null,
        target_price_min: isoPriceMin ? parseFloat(isoPriceMin) : null,
        target_price_max: isoPriceMax ? parseFloat(isoPriceMax) : null,
        caption: isoCaption || null,
        intent: isoIntent || 'seeking',
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success(isoIntent === 'dreaming' ? 'added to dream list.' : 'iso posted.');
      trackEvent('iso_posted');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const handleNoteImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const { validateImageFile } = await import('../utils/imageUpload');
    const err = validateImageFile(file);
    if (err) { toast.error(err); return; }
    setNoteUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const r = await axios.post(`${API}/upload`, formData, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
      });
      setNoteImageUrl(r.data.url);
    } catch { toast.error('upload failed. try again.'); }
    finally { setNoteUploading(false); }
  };

  const submitNote = async () => {
    if (!noteText.trim()) { toast.error('write something first.'); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/composer/note`, {
        text: noteText.trim(),
        record_id: noteRecordId || null,
        image_url: noteImageUrl || null,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success('note posted.');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const moodCfg = spinMood ? MOOD_CONFIG[spinMood] : null;
  const noteRecord = records.find(r => r.id === noteRecordId);

  const spectrum = [
    { key: 'NOW_SPINNING', label: 'Now Spinning', icon: Disc },
    { key: 'NEW_HAUL', label: 'Haul', icon: Package },
    { key: 'ISO', label: 'ISO', icon: Search },
    { key: 'NOTE', label: 'Note', icon: Feather },
    { key: 'RANDOMIZER', label: 'Randomizer', icon: Shuffle },
  ];

  return (
    <>
      {/* Composer Bar — Command Center */}
      <div className="bg-white rounded-xl border border-honey/30 p-4 mb-6 shadow-sm" data-testid="composer-bar">
        <p className="text-sm text-muted-foreground mb-1">What's on the turntable?</p>
        <p className="text-[10px] text-muted-foreground/70 mb-3 italic">Only posts with comments will be shared in The Hive.</p>
        <div className="flex flex-row gap-1.5 justify-between w-full">
          {spectrum.map(chip => {
            const Icon = chip.icon;
            return (
              <button
                key={chip.key}
                onClick={() => chip.key === 'RANDOMIZER' ? openRandomizer() : openModal(chip.key)}
                className="h-9 w-9 aspect-square md:w-auto md:aspect-auto md:px-4 md:py-2 rounded-full text-sm font-semibold flex items-center justify-center gap-1.5 whitespace-nowrap transition-all hover:scale-105 hover:shadow-md"
                style={{ background: '#FDE68A', color: '#78350F', border: '1px solid rgba(0,0,0,0.05)' }}
                data-testid={`composer-chip-${chip.key.toLowerCase()}`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="hidden md:inline">{chip.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ═══ Now Spinning Modal (merged with Mood) ═══ */}
      <Dialog open={activeModal === 'NOW_SPINNING'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md max-h-[90vh] flex flex-col overflow-hidden p-0">
          <div className="px-6 pt-6 pb-2 shrink-0">
            <DialogHeader>
              <DialogTitle className="font-heading flex items-center gap-2" style={{ color: '#D98C2F' }}>
                <Disc className="w-5 h-5" /> Now Spinning
                {spinMood && <span className="text-sm font-normal ml-1">· {MOOD_CONFIG[spinMood].emoji} {spinMood}</span>}
              </DialogTitle>
              <DialogDescription>
                Share what you're listening to right now
              </DialogDescription>
            </DialogHeader>
          </div>

          {/* Scrollable content area */}
          <div className="flex-1 overflow-y-auto px-6 min-h-0">
            <div className="space-y-3 pb-2">
              <div>
                <label className="text-sm font-medium mb-1 block">Record</label>
                {!spinSelectedRecord ? (
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="search your vault..."
                      value={spinSearch}
                      onChange={e => { setSpinSearch(e.target.value); searchCollection(e.target.value); }}
                      className="pl-9 border-honey/50"
                      data-testid="spin-record-search"
                    />
                    {spinSearchResults.length > 0 && (
                      <div className="absolute z-50 left-0 right-0 mt-1 border rounded-lg max-h-52 overflow-y-auto shadow-lg bg-white" style={{ borderColor: 'rgba(200,134,26,0.3)' }}>
                        {spinSearchResults.map(r => (
                          <RecordSearchResult key={r.id} record={r} onClick={() => selectSpinRecord(r)} size="sm" testId={`spin-result-${r.id}`} />
                        ))}
                      </div>
                    )}
                    {spinSearch.length >= 2 && spinSearchResults.length === 0 && (
                      <div className="absolute z-50 left-0 right-0 mt-1 border rounded-lg p-4 text-center shadow-lg bg-white" style={{ borderColor: 'rgba(200,134,26,0.3)' }}>
                        <p className="text-sm" style={{ color: '#8A6B4A' }}>
                          no results in your vault
                        </p>
                        <a href="/add-record" className="text-xs mt-1 inline-block hover:underline"
                          style={{ color: '#C8861A' }}
                          data-testid="spin-add-record-link">
                          add it first &rarr;
                        </a>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-3 rounded-lg p-2" style={{ background: 'rgba(244,185,66,0.1)' }}>
                    {spinSelectedRecord.cover_url ? (
                      <AlbumArt src={spinSelectedRecord.cover_url} alt={`${spinSelectedRecord.artist} ${spinSelectedRecord.title} vinyl record`} className="w-10 h-10 rounded-md object-cover shadow-sm" />
                    ) : (
                      <div className="w-10 h-10 rounded-md bg-stone-100 flex items-center justify-center"><Disc className="w-5 h-5 text-stone-400" /></div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{spinSelectedRecord.title}</p>
                      <p className="text-xs truncate" style={{ color: '#8A6B4A' }}>{spinSelectedRecord.artist}</p>
                    </div>
                    <button onClick={deselectSpinRecord} className="p-1 rounded-full hover:bg-black/10"
                      style={{ color: '#8A6B4A' }}
                      data-testid="spin-deselect-record">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Track selector — searchable dropdown when tracks available */}
              <div className="relative" ref={trackDropdownRef}>
                {spinTracksLoading ? (
                  <div className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm" style={{ border: '1px solid rgba(200,134,26,0.5)', background: '#FFFDF5' }} data-testid="spin-track-loading">
                    <div className="flex gap-1 items-end h-4">
                      <span className="w-1 rounded-full animate-pulse" style={{ background: '#C8861A', height: '8px', animationDelay: '0ms', animationDuration: '800ms' }} />
                      <span className="w-1 rounded-full animate-pulse" style={{ background: '#C8861A', height: '12px', animationDelay: '200ms', animationDuration: '800ms' }} />
                      <span className="w-1 rounded-full animate-pulse" style={{ background: '#C8861A', height: '16px', animationDelay: '400ms', animationDuration: '800ms' }} />
                      <span className="w-1 rounded-full animate-pulse" style={{ background: '#C8861A', height: '10px', animationDelay: '600ms', animationDuration: '800ms' }} />
                    </div>
                    <span style={{ color: '#8A6B4A' }}>Fetching tracks... 🐝</span>
                  </div>
                ) : spinTrackManual ? (
                  <div className="space-y-1.5">
                    <Input
                      placeholder="Type the track name..."
                      value={spinTrack}
                      onChange={e => setSpinTrack(e.target.value)}
                      style={{ border: '1px solid rgba(200,134,26,0.5)', background: '#FFFDF5' }}
                      autoFocus
                      data-testid="spin-track-manual-input"
                    />
                    {spinTracks.length > 0 && (
                      <button
                        onClick={() => { setSpinTrackManual(false); setSpinTrack(''); }}
                        className="text-xs underline transition-colors"
                        style={{ color: '#C8861A' }}
                        data-testid="spin-track-back-to-list"
                      >
                        Back to tracklist
                      </button>
                    )}
                  </div>
                ) : spinTracks.length > 0 ? (
                  <select
                    value={spinTrack}
                    onChange={e => {
                      if (e.target.value === '__manual__') {
                        setSpinTrackManual(true);
                        setSpinTrack('');
                      } else {
                        setSpinTrack(e.target.value);
                      }
                    }}
                    className="w-full rounded-md text-sm px-3 py-2 appearance-none cursor-pointer"
                    style={{
                      border: '1px solid rgba(200,134,26,0.5)',
                      background: '#FFFDF5',
                      color: spinTrack ? '#1a1a1a' : '#8A6B4A',
                      backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'12\' height=\'12\' viewBox=\'0 0 12 12\'%3E%3Cpath d=\'M2 4l4 4 4-4\' fill=\'none\' stroke=\'%23C8861A\' stroke-width=\'1.5\'/%3E%3C/svg%3E")',
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 10px center',
                      paddingRight: '30px',
                    }}
                    data-testid="spin-track-select"
                  >
                    <option value="">Select a track...</option>
                    {spinTracks.map((t, idx) => {
                      const label = t.position ? `${t.position} — ${t.title}` : t.title;
                      return (
                        <option key={idx} value={label}>{label}{t.duration ? ` (${t.duration})` : ''}</option>
                      );
                    })}
                    <option value="__manual__">-- Manual Input --</option>
                  </select>
                ) : (
                  <div className="flex items-center gap-1.5">
                    <Input
                      placeholder={spinTracksFetched ? 'No tracklist found — type a track name' : 'Track (optional)'}
                      value={spinTrack}
                      onChange={e => setSpinTrack(e.target.value)}
                      style={{ border: '1px solid rgba(200,134,26,0.5)', background: '#FFFDF5' }}
                      data-testid="spin-track-manual-input" />
                    {spinTracksFetched && spinSelectedRecord?.discogs_id && (
                      <button
                        onClick={() => fetchTracklist(spinSelectedRecord.discogs_id)}
                        className="shrink-0 p-2 rounded-md transition-colors hover:bg-amber-50"
                        title="Retry fetching tracklist"
                        data-testid="spin-track-refresh"
                      >
                        <RefreshCw className="w-4 h-4" style={{ color: '#C8861A' }} />
                      </button>
                    )}
                  </div>
                )}
              </div>

              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: '#8A6B4A' }}>
                  how does it feel?
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {MOOD_KEYS.map(m => {
                    const mc = MOOD_CONFIG[m];
                    const isSelected = spinMood === m;
                    return (
                      <button key={m}
                        onClick={() => setSpinMood(isSelected ? '' : m)}
                        className="px-2 py-1.5 rounded-lg text-[11px] font-medium transition-all leading-tight"
                        style={{
                          background: isSelected ? 'linear-gradient(135deg, #FFB300, #FFA000)' : '#FFF8E1',
                          color: isSelected ? '#000' : '#3E2723',
                          border: isSelected ? '2px solid #FFA000' : '1.5px solid rgba(255,179,0,0.2)',
                          transform: isSelected ? 'scale(1.04)' : 'scale(1)',
                          transition: 'transform 180ms ease-in-out, background 200ms, border 200ms, color 200ms',
                        }}
                        data-testid={`mood-${m.toLowerCase().replace(/\s/g, '-')}`}>
                        {mc.emoji} {m}
                      </button>
                    );
                  })}
                </div>
              </div>

              <MentionTextarea
                placeholder={moodCfg ? moodCfg.placeholder : "Right now I'm..."}
                value={spinCaption} onChange={setSpinCaption}
                className="resize-none"
                style={{ borderColor: 'rgba(200,134,26,0.5)' }}
                rows={2} data-testid="spin-caption-input" />
              {!spinCaption.trim() && (
                <p className="text-xs italic mt-1" style={{ color: '#C8861A' }} data-testid="spin-caption-helper">
                  Tell the hive what you love about this record! 🐝
                </p>
              )}

              {/* Photo upload */}
              <input type="file" accept="image/*" ref={postPhotoInputRef} onChange={handlePhotoSelect} className="hidden" data-testid="spin-photo-input" />
              {postPhotoPreview ? (
                <div className="relative inline-block rounded-lg overflow-hidden border border-honey/30" data-testid="spin-photo-preview">
                  <img src={postPhotoPreview} alt="Upload preview" className="h-20 w-20 object-cover" />
                  <button onClick={clearPostPhoto} className="absolute top-0.5 right-0.5 bg-black/60 text-white rounded-full p-0.5" data-testid="spin-photo-remove">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => postPhotoInputRef.current?.click()}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-dashed border-honey/40 text-stone-500 hover:text-stone-700 hover:border-honey/60 transition-colors"
                  data-testid="spin-photo-upload-btn"
                >
                  <Camera className="w-3.5 h-3.5" /> Add a photo
                </button>
              )}
            </div>
          </div>

          {/* Sticky footer — always visible */}
          <div className="shrink-0 px-6 pb-5 pt-3 border-t border-honey/15 bg-white">
            <Button onClick={submitNowSpinning} disabled={submitting || !spinRecordId || !spinCaption.trim()}
              className="w-full rounded-full transition-all duration-200 text-white"
              style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)' }}
              data-testid="spin-submit-btn">
              {submitting ? (
                <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Spinning your record...</>
              ) : (
                <><Disc className="w-4 h-4 mr-2" /> {spinMood ? `Post Now Spinning · ${MOOD_CONFIG[spinMood].emoji} ${spinMood}` : 'Post Now Spinning'}</>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* ═══ New Haul Modal ═══ */}
      <Dialog open={activeModal === 'NEW_HAUL'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2"><Package className="w-5 h-5 text-amber-600" /> New Haul</DialogTitle>
            <DialogDescription>Share your latest finds</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <Input placeholder="Where'd you find them? (store, thrift, eBay...)" value={haulStoreName} onChange={e => setHaulStoreName(e.target.value)} className="border-honey/50" data-testid="haul-store-input" />
            <div>
              <label className="text-sm font-medium mb-1 block">Records found</label>
              <div className="relative">
                <Input placeholder="Search Discogs to add records..." value={haulSearch}
                  onChange={e => { setHaulSearch(e.target.value); searchDiscogs(e.target.value); }}
                  className="border-honey/50" data-testid="haul-search-input" />
                {searchLoading && <Loader2 className="w-4 h-4 animate-spin absolute right-3 top-3 text-muted-foreground" />}
              </div>
              {haulResults.length > 0 && (
                <div className="mt-1 border border-honey/30 rounded-lg max-h-40 overflow-y-auto bg-white">
                  {haulResults.map(r => (
                    <RecordSearchResult key={r.discogs_id} record={r} onClick={() => addHaulItem(r)} size="sm" testId={`haul-result-${r.discogs_id}`} />
                  ))}
                </div>
              )}
            </div>
            {haulItems.length > 0 && (
              <div className="space-y-2">
                {haulItems.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-honey/10 rounded-lg px-3 py-2">
                    <AlbumArt src={item.cover_url} alt={`${item.artist} ${item.title} vinyl record`} className="w-8 h-8 rounded object-cover" />
                    <span className="flex-1 text-sm truncate">{item.artist} · {item.title}</span>
                    <button onClick={() => setHaulItems(prev => prev.filter((_, i) => i !== idx))} className="text-muted-foreground hover:text-red-500"><X className="w-4 h-4" /></button>
                  </div>
                ))}
                <p className="text-xs text-muted-foreground">{haulItems.length} record{haulItems.length !== 1 ? 's' : ''}</p>
              </div>
            )}
            <MentionTextarea placeholder="I just got..." value={haulCaption} onChange={setHaulCaption} className="border-honey/50 resize-none" rows={2} data-testid="haul-caption-input" />
            {/* Photo Upload Section */}
            <div className="mt-2 mb-4 px-1">
              <input 
                type="file" 
                ref={postPhotoInputRef} 
                className="hidden" 
                accept="image/*" 
                onChange={handlePhotoSelect} 
            />
  
            {!postPhotoPreview ? (
              <button 
                type="button"
                onClick={() => postPhotoInputRef.current.click()}
                className="flex items-center gap-2 text-stone-500 hover:text-amber-600 transition text-sm font-medium border border-dashed border-stone-300 rounded-lg p-3 w-full justify-center"
              >
                <ImagePlus size={18} />
                Add a photo of your haul (Optional)
              </button>
            ) : (
              <div className="relative w-full aspect-video group">
                <img 
        src={postPhotoPreview} 
        className="w-full h-full object-cover rounded-xl border border-stone-200 shadow-sm" 
      />
      <button 
        onClick={clearPostPhoto}
        className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1.5 shadow-md hover:bg-red-600 transition"
      >
        <X size={14} />
      </button>
    </div>
  )}
</div>
            <Button onClick={submitNewHaul} disabled={submitting || haulItems.length === 0 || !haulCaption.trim()} className="w-full bg-amber-100 text-amber-800 hover:bg-amber-200 rounded-full" data-testid="haul-submit-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Package className="w-4 h-4 mr-2" />}
              Post Haul ({haulItems.length} record{haulItems.length !== 1 ? 's' : ''})
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* ═══ ISO Modal ═══ */}
      <Dialog open={activeModal === 'ISO'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2"><Search className="w-5 h-5 text-blue-600" /> In Search Of</DialogTitle>
            <DialogDescription>Let the community know what you're looking for</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            {/* Step 1: Intent Selection */}
            {!isoIntent ? (
              <div className="space-y-3" data-testid="iso-intent-selection">
                <p className="text-sm text-muted-foreground text-center">What's your vibe?</p>
                <button
                  onClick={() => setIsoIntent('dreaming')}
                  className="w-full rounded-2xl p-4 text-left transition-all hover:scale-[1.01] active:scale-[0.99]"
                  style={{
                    background: 'rgba(255,255,255,0.7)',
                    backdropFilter: 'blur(16px)',
                    WebkitBackdropFilter: 'blur(16px)',
                    border: '1.5px solid rgba(218,165,32,0.2)',
                    boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
                  }}
                  data-testid="iso-intent-dreaming"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">☁️</span>
                    <div>
                      <p className="font-heading text-base text-vinyl-black">Just Dreaming</p>
                      <p className="text-xs text-muted-foreground">Add to your wish list. No rush.</p>
                    </div>
                  </div>
                </button>
                <button
                  onClick={() => setIsoIntent('seeking')}
                  className="w-full rounded-2xl p-4 text-left transition-all hover:scale-[1.01] active:scale-[0.99]"
                  style={{
                    background: 'linear-gradient(135deg, rgba(255,215,0,0.08), rgba(218,165,32,0.12))',
                    backdropFilter: 'blur(16px)',
                    WebkitBackdropFilter: 'blur(16px)',
                    border: '1.5px solid rgba(218,165,32,0.35)',
                    boxShadow: '0 2px 16px rgba(218,165,32,0.1)',
                  }}
                  data-testid="iso-intent-seeking"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🔍</span>
                    <div>
                      <p className="font-heading text-base text-vinyl-black">Actively Seeking</p>
                      <p className="text-xs text-muted-foreground">Alert the hive. You're on the hunt.</p>
                    </div>
                  </div>
                </button>
              </div>
            ) : (
              <>
                {/* Intent indicator + change */}
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
                    style={isoIntent === 'dreaming'
                      ? { background: 'rgba(200,200,220,0.15)', backdropFilter: 'blur(8px)', border: '1px solid rgba(200,200,220,0.3)', color: '#6B7280' }
                      : { background: 'rgba(255,215,0,0.12)', border: '1px solid rgba(218,165,32,0.3)', color: '#92702A' }
                    }
                    data-testid="iso-intent-badge"
                  >
                    {isoIntent === 'dreaming' ? '☁️ Just Dreaming' : '🔥 Actively Seeking'}
                  </span>
                  <button onClick={() => { setIsoIntent(null); setIsoSelectedRelease(null); setIsoManualMode(false); setIsoDiscogsQuery(''); setIsoDiscogsResults([]); }} className="text-xs text-muted-foreground hover:text-vinyl-black" data-testid="iso-change-intent">Change</button>
                </div>

                {/* Step 2: Search / Manual Entry */}
                {!isoSelectedRelease && !isoManualMode ? (
                  <>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input placeholder="Search Discogs for an album..." value={isoDiscogsQuery}
                        onChange={e => { setIsoDiscogsQuery(e.target.value); searchDiscogsForISO(e.target.value); }}
                        className="pl-9 border-honey/50" data-testid="iso-discogs-search" />
                      {isoSearchLoading && <Loader2 className="w-4 h-4 animate-spin absolute right-3 top-3 text-muted-foreground" />}
                    </div>
                    {isoDiscogsResults.length > 0 && (
                      <div className="border border-honey/30 rounded-lg max-h-48 overflow-y-auto bg-white">
                        {isoDiscogsResults.map(r => (
                          <RecordSearchResult key={r.discogs_id} record={r} onClick={() => selectIsoRelease(r)} size="sm" testId={`iso-discogs-result-${r.discogs_id}`} />
                        ))}
                      </div>
                    )}
                    <button onClick={() => setIsoManualMode(true)} className="text-sm text-honey-amber hover:underline" data-testid="iso-manual-entry-btn">Or enter manually</button>
                  </>
                ) : isoSelectedRelease ? (
                  <div className="flex items-center gap-3 bg-blue-50 rounded-lg p-3">
                    {isoSelectedRelease.cover_url ? <AlbumArt src={isoSelectedRelease.cover_url} alt={`${isoSelectedRelease.artist} ${isoSelectedRelease.title} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow" /> : <Disc className="w-14 h-14 text-blue-300" />}
                    <div className="flex-1 min-w-0"><p className="font-heading text-base">{isoSelectedRelease.title}</p><p className="text-sm text-muted-foreground">{isoSelectedRelease.artist} {isoSelectedRelease.year ? `(${isoSelectedRelease.year})` : ''}</p></div>
                    <button onClick={() => { setIsoSelectedRelease(null); setIsoArtist(''); setIsoAlbum(''); }} className="text-xs text-muted-foreground hover:text-red-500">Change</button>
                  </div>
                ) : null}

                {(isoManualMode || isoSelectedRelease) && (
                  <>
                    {isoManualMode && (
                      <>
                        <Input placeholder="Artist *" value={isoArtist} onChange={e => setIsoArtist(e.target.value)} className="border-honey/50" data-testid="iso-artist-input" />
                        <Input placeholder="Album *" value={isoAlbum} onChange={e => setIsoAlbum(e.target.value)} className="border-honey/50" data-testid="iso-album-input" />
                      </>
                    )}
                    <Input placeholder="Press / condition preference" value={isoPressing} onChange={e => setIsoPressing(e.target.value)} className="border-honey/50" />
                    <div className="grid grid-cols-2 gap-3">
                      <Input placeholder="Min budget ($)" type="number" value={isoPriceMin} onChange={e => setIsoPriceMin(e.target.value)} className="border-honey/50" />
                      <Input placeholder="Max budget ($)" type="number" value={isoPriceMax} onChange={e => setIsoPriceMax(e.target.value)} className="border-honey/50" />
                    </div>
                    <MentionTextarea placeholder="I'm looking for this because..." value={isoCaption} onChange={setIsoCaption} className="border-honey/50 resize-none" rows={2} data-testid="iso-caption-input" />
                    <Button onClick={submitISO} disabled={submitting || !isoCaption.trim() || (isoManualMode && (!isoArtist || !isoAlbum)) || (!isoManualMode && !isoSelectedRelease)}
                      className="w-full rounded-full"
                      style={isoIntent === 'dreaming'
                        ? { background: '#f3f4f6', color: '#374151' }
                        : { background: 'linear-gradient(135deg, #FFD700, #DAA520)', color: '#2A1A06' }
                      }
                      data-testid="iso-submit-btn">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                      {isoIntent === 'dreaming' ? 'Add to Dream List' : 'Post to the Hive'}
                    </Button>
                  </>
                )}
              </>
            )}
          </div> 
    </DialogContent> {/* <--- Add this */}
  </Dialog>

      {/* ═══ A Note Modal ═══ */}
      <Dialog open={activeModal === 'NOTE'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="sr-only">A Note</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <MentionTextarea
              placeholder="Thinking about..."
              value={noteText}
              onChange={v => setNoteText(isAdmin ? v : v.slice(0, 1500))}
              className="border-stone-200 resize-none text-base min-h-[120px] focus-visible:ring-amber-300"
              rows={4}
              maxLength={isAdmin ? undefined : 1500}
              data-testid="note-text-input"
            />
            <div className="flex items-center justify-between">
              {isAdmin ? (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200" data-testid="admin-changelog-badge">
                  <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  Admin: Change Log Mode
                </span>
              ) : (
                <span className={`text-xs ${noteText.length > 260 ? 'text-amber-600 font-medium' : 'text-muted-foreground'}`}>
                  {noteText.length}/1500
                </span>
              )}
              <div className="flex items-center gap-3">
                {/* Tag a record */}
                <button
                  onClick={() => setNoteShowRecordPicker(!noteShowRecordPicker)}
                  className="text-xs text-stone-400 hover:text-amber-600 flex items-center gap-1 transition-colors"
                  data-testid="note-tag-record-btn"
                >
                  <Tag className="w-3.5 h-3.5" /> tag a record
                </button>
                {/* Image upload */}
                <button
                  onClick={() => noteFileRef.current?.click()}
                  className="text-xs text-stone-400 hover:text-amber-600 flex items-center gap-1 transition-colors"
                  data-testid="note-add-image-btn"
                >
                  <ImagePlus className="w-3.5 h-3.5" /> add image
                </button>
                <input ref={noteFileRef} type="file" accept=".jpg,.jpeg,.png,.webp,.heic,.heif" className="hidden" onChange={handleNoteImageUpload} />
              </div>
            </div>

            {/* Record picker dropdown */}
            {noteShowRecordPicker && (
              <Select value={noteRecordId} onValueChange={v => { setNoteRecordId(v); setNoteShowRecordPicker(false); }}>
                <SelectTrigger className="border-stone-200" data-testid="note-record-select">
                  <SelectValue placeholder="Choose from your vault" />
                </SelectTrigger>
                <SelectContent>
                  {records.map(r => (
                    <SelectItem key={r.id} value={r.id}>{r.artist} · {r.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* Tagged record preview */}
            {noteRecord && (
              <div className="flex items-center gap-2 bg-stone-50 rounded-lg px-3 py-2" data-testid="note-tagged-record">
                {noteRecord.cover_url ? (
                  <AlbumArt src={noteRecord.cover_url} alt={`${noteRecord.artist} ${noteRecord.title} vinyl record`} className="w-8 h-8 rounded object-cover" />
                ) : (
                  <div className="w-8 h-8 rounded bg-stone-200 flex items-center justify-center"><Disc className="w-4 h-4 text-stone-400" /></div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate">{noteRecord.title}</p>
                  <p className="text-xs text-muted-foreground truncate">{noteRecord.artist}</p>
                </div>
                <button onClick={() => setNoteRecordId('')} className="text-muted-foreground hover:text-red-500"><X className="w-3.5 h-3.5" /></button>
              </div>
            )}

            {/* Image preview */}
            {noteUploading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> uploading...</div>
            )}
            {noteImageUrl && (
              <div className="relative inline-block" data-testid="note-image-preview">
                <img src={noteImageUrl} alt="" className="max-h-40 rounded-lg object-cover" />
                <button onClick={() => setNoteImageUrl('')} className="absolute top-1 right-1 bg-black/60 rounded-full p-0.5 text-white hover:bg-black/80">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            <Button
              onClick={submitNote}
              disabled={submitting || !noteText.trim()}
              className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white"
              data-testid="note-submit-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Feather className="w-4 h-4 mr-2" />}
              post to the hive
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* ═══ Randomizer Modal ═══ */}
      <Dialog open={activeModal === 'RANDOMIZER'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2 text-amber-700">
              <Shuffle className="w-5 h-5" /> Randomizer
            </DialogTitle>
            <DialogDescription>What record should you spin today?</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            {/* Record display */}
            {randAnimating ? (
              <div className="flex flex-col items-center py-8" data-testid="randomizer-shuffling">
                <div className="w-40 h-40 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center honey-shimmer">
                  <Shuffle className="w-10 h-10 text-amber-600 animate-spin" />
                </div>
                <p className="text-sm text-muted-foreground mt-3">shuffling your vault...</p>
              </div>
            ) : randRecord ? (
              <div className="flex flex-col items-center" data-testid="randomizer-result">
                <div className="w-40 h-40 rounded-xl overflow-hidden shadow-lg border border-honey/30">
                  {randRecord.cover_url ? (
                    <AlbumArt src={randRecord.cover_url} alt={`${randRecord.artist} ${randRecord.title}`} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-stone-100 flex items-center justify-center"><Disc className="w-12 h-12 text-stone-300" /></div>
                  )}
                </div>
                <p className="font-heading text-base mt-3 text-center" data-testid="randomizer-album">{randRecord.title}</p>
                <p className="text-sm text-muted-foreground text-center" data-testid="randomizer-artist">{randRecord.artist}</p>
                {(randRecord.color_variant || randRecord.pressing_notes) && (
                  <p className="text-xs text-amber-600 mt-0.5" data-testid="randomizer-variant">{randRecord.color_variant || randRecord.pressing_notes}</p>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center py-8 text-muted-foreground">
                <Disc className="w-10 h-10 mb-2 opacity-50" />
                <p className="text-sm">No records found in your vault</p>
              </div>
            )}

            {/* Caption */}
            {randRecord && !randAnimating && (
              <>
                <MentionTextarea
                  placeholder="Thinking about..."
                  value={randCaption} onChange={setRandCaption}
                  className="border-honey/50 resize-none"
                  rows={2} data-testid="randomizer-caption-input"
                />

                {/* Buttons */}
                <div className="space-y-2">
                  <Button onClick={submitRandomPost} disabled={submitting || !randCaption.trim()}
                    className="w-full rounded-full bg-honey text-vinyl-black hover:bg-honey-amber"
                    data-testid="randomizer-post-btn">
                    {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Feather className="w-4 h-4 mr-2" />}
                    Post to Hive
                  </Button>
                  <div className="flex gap-2">
                    <Button onClick={() => { setRandCaption(''); fetchRandomRecord(); }} disabled={randLoading}
                      variant="outline" className="flex-1 rounded-full border-honey/50"
                      data-testid="randomizer-try-another-btn">
                      <Shuffle className="w-4 h-4 mr-2" /> Try Another
                    </Button>
                    <Button onClick={closeModal} variant="ghost" className="flex-1 rounded-full text-muted-foreground"
                      data-testid="randomizer-cancel-btn">
                      Cancel
                    </Button>
                  </div>
                </div>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ComposerBar;
