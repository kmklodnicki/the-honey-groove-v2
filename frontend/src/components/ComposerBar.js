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
import { Disc, Package, Search, Loader2, X, Feather, ImagePlus, Tag, Shuffle } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import AlbumArt from './AlbumArt';
import RecordSearchResult from './RecordSearchResult';

const MOOD_CONFIG = {
  'Late Night': { emoji: '\u{1F56F}\uFE0F', bg: '#1a1230', btnColor: '#6a3a9a', placeholder: 'what are you listening to at this hour?' },
  'Good Morning': { emoji: '\u2600\uFE0F', bg: '#fff8e8', btnColor: '#e8a820', placeholder: 'slow mornings, good records, nowhere to be...' },
  'Rainy Day': { emoji: '\u{1F327}\uFE0F', bg: '#1a2a3a', btnColor: '#4a7aaa', placeholder: 'set the scene...' },
  'Road Trip': { emoji: '\u{1F697}', bg: '#1a2a1a', btnColor: '#4a8a4a', placeholder: 'where are you headed?' },
  'Golden Hour': { emoji: '\u{1F305}', bg: '#2a1a08', btnColor: '#c8861a', placeholder: 'the light is perfect right now...' },
  'Deep Focus': { emoji: '\u{1F3A7}', bg: '#0a1a0a', btnColor: '#2a6a2a', placeholder: 'what are you working on?' },
  'Party Mode': { emoji: '\u{1F942}', bg: '#1a0a2a', btnColor: '#aa3a8a', placeholder: "who's coming over?" },
  'Lazy Afternoon': { emoji: '\u{1F6CB}\uFE0F', bg: '#2a1a0a', btnColor: '#aa7a3a', placeholder: 'not moving from this spot...' },
  'Melancholy': { emoji: '\u{1F494}', bg: '#1a1a2a', btnColor: '#5a5a8a', placeholder: 'some records just hit different...' },
  'Upbeat Vibes': { emoji: '\u2728', bg: '#1a2a1a', btnColor: '#3a9a5a', placeholder: "what's got you feeling good?" },
  'Cozy Evening': { emoji: '\u{1F9F8}', bg: '#2a1808', btnColor: '#aa5a2a', placeholder: 'candles lit, record spinning...' },
  'Workout': { emoji: '\u{1F525}', bg: '#2a0a0a', btnColor: '#cc3a2a', placeholder: "what's keeping you going?" },
};
const MOOD_KEYS = Object.keys(MOOD_CONFIG);

const ComposerBar = ({ onPostCreated, records = [] }) => {
  const { token, API } = useAuth();
  const [activeModal, setActiveModal] = useState(null);
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

  // A Note
  const [noteText, setNoteText] = useState('');
  const [noteRecordId, setNoteRecordId] = useState('');
  const [noteShowRecordPicker, setNoteShowRecordPicker] = useState(false);
  const [noteImageUrl, setNoteImageUrl] = useState('');
  const [noteUploading, setNoteUploading] = useState(false);
  const noteFileRef = useRef(null);

  // Randomizer
  const [randRecord, setRandRecord] = useState(null);
  const [randCaption, setRandCaption] = useState('');
  const [randLoading, setRandLoading] = useState(false);
  const [randAnimating, setRandAnimating] = useState(false);

  const resetAll = () => {
    setSpinRecordId(''); setSpinTrack(''); setSpinCaption(''); setSpinMood('');
    setSpinSearch(''); setSpinSearchResults([]); setSpinSelectedRecord(null);
    setHaulStoreName(''); setHaulCaption(''); setHaulItems([]); setHaulSearch(''); setHaulResults([]);
    setIsoArtist(''); setIsoAlbum(''); setIsoPressing(''); setIsoCondition('');
    setIsoPriceMin(''); setIsoPriceMax(''); setIsoCaption('');
    setIsoDiscogsQuery(''); setIsoDiscogsResults([]); setIsoSelectedRelease(null); setIsoManualMode(false);
    setNoteText(''); setNoteRecordId(''); setNoteShowRecordPicker(false); setNoteImageUrl(''); setNoteUploading(false);
    setRandRecord(null); setRandCaption(''); setRandLoading(false); setRandAnimating(false);
  };

  const openModal = (type) => { resetAll(); setActiveModal(type); };
  const closeModal = () => { setActiveModal(null); resetAll(); };

  const haulSearchTimer = useRef(null);
  const isoSearchTimer = useRef(null);

  useEffect(() => {
    return () => {
      if (haulSearchTimer.current) clearTimeout(haulSearchTimer.current);
      if (isoSearchTimer.current) clearTimeout(isoSearchTimer.current);
      if (spinSearchTimer.current) clearTimeout(spinSearchTimer.current);
    };
  }, []);

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
  };

  const deselectSpinRecord = () => {
    setSpinSelectedRecord(null);
    setSpinRecordId('');
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

  // Submit handlers
  const submitNowSpinning = async () => {
    if (!spinRecordId) { toast.error('select a record first.'); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/composer/now-spinning`, {
        record_id: spinRecordId,
        track: spinTrack || null,
        caption: spinCaption || null,
        mood: spinMood || null,
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
      await axios.post(`${API}/composer/new-haul`, {
        store_name: haulStoreName || null, caption: haulCaption || null, items: haulItems,
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
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success('iso posted.');
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

  const chips = [
    { key: 'NOW_SPINNING', label: 'Now Spinning', icon: Disc, color: 'bg-honey text-vinyl-black' },
    { key: 'NEW_HAUL', label: 'New Haul', icon: Package, color: 'bg-amber-100 text-amber-800' },
    { key: 'ISO', label: 'ISO', icon: Search, color: 'bg-amber-100 text-amber-800 border border-amber-300' },
  ];

  return (
    <>
      {/* Composer Bar */}
      <div className="bg-white rounded-xl border border-honey/30 p-4 mb-6 shadow-sm" data-testid="composer-bar">
        <p className="text-sm text-muted-foreground mb-3">What's on the turntable?</p>
        <div className="flex flex-wrap gap-2">
          {chips.map(chip => (
            <button key={chip.key} onClick={() => openModal(chip.key)}
              className={`${chip.color} px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 transition-all hover:scale-105 hover:shadow-md`}
              data-testid={`composer-chip-${chip.key.toLowerCase()}`}>
              <chip.icon className="w-4 h-4" /> {chip.label}
            </button>
          ))}
          {/* A Note · outlined pill, lighter visual weight */}
          <button onClick={() => openModal('NOTE')}
            className="px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 transition-all hover:scale-105 hover:shadow-sm border border-stone-300 text-stone-500 hover:border-amber-400 hover:text-amber-700 bg-transparent"
            data-testid="composer-chip-note">
            <Feather className="w-4 h-4" /> A Note
          </button>
          {/* Randomizer */}
          <button onClick={openRandomizer}
            className="px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 transition-all hover:scale-105 hover:shadow-md bg-gradient-to-r from-amber-100 to-orange-100 text-amber-800 border border-amber-300/50"
            data-testid="composer-chip-randomizer">
            <Shuffle className="w-4 h-4" /> Randomizer
          </button>
        </div>
      </div>

      {/* ═══ Now Spinning Modal (merged with Mood) ═══ */}
      <Dialog open={activeModal === 'NOW_SPINNING'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent
          className="sm:max-w-md transition-colors duration-300"
          style={moodCfg ? { backgroundColor: moodCfg.bg, borderColor: moodCfg.btnColor + '40' } : {}}
        >
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2"
              style={moodCfg ? { color: moodCfg.btnColor } : { color: '#D98C2F' }}>
              <Disc className="w-5 h-5" /> Now Spinning
            </DialogTitle>
            <DialogDescription style={moodCfg ? { color: '#aaa' } : {}}>
              Share what you're listening to right now
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div>
              <label className="text-sm font-medium mb-1 block" style={moodCfg ? { color: moodCfg.btnColor } : {}}>Record</label>
              {!spinSelectedRecord ? (
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" style={moodCfg ? { color: '#888' } : {}} />
                  <Input
                    placeholder="search your collection..."
                    value={spinSearch}
                    onChange={e => { setSpinSearch(e.target.value); searchCollection(e.target.value); }}
                    className="pl-9 border-honey/50"
                    style={moodCfg ? { background: 'rgba(255,255,255,0.08)', color: '#ddd', borderColor: moodCfg.btnColor + '60' } : {}}
                    data-testid="spin-record-search"
                    autoFocus
                  />
                  {spinSearchResults.length > 0 && (
                    <div className="absolute z-50 left-0 right-0 mt-1 border rounded-lg max-h-52 overflow-y-auto shadow-lg"
                      style={moodCfg ? { background: moodCfg.bg, borderColor: moodCfg.btnColor + '40' } : { background: '#fff', borderColor: 'rgba(200,134,26,0.3)' }}>
                      {spinSearchResults.map(r => (
                        <RecordSearchResult key={r.id} record={r} onClick={() => selectSpinRecord(r)} size="sm" testId={`spin-result-${r.id}`} />
                      ))}
                    </div>
                  )}
                  {spinSearch.length >= 2 && spinSearchResults.length === 0 && (
                    <div className="absolute z-50 left-0 right-0 mt-1 border rounded-lg p-4 text-center shadow-lg"
                      style={moodCfg ? { background: moodCfg.bg, borderColor: moodCfg.btnColor + '40' } : { background: '#fff', borderColor: 'rgba(200,134,26,0.3)' }}>
                      <p className="text-sm" style={{ color: moodCfg ? '#999' : '#8A6B4A' }}>
                        no results in your collection 🐝
                      </p>
                      <a href="/add-record" className="text-xs mt-1 inline-block hover:underline"
                        style={{ color: moodCfg ? moodCfg.btnColor : '#C8861A' }}
                        data-testid="spin-add-record-link">
                        add it first →
                      </a>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-3 rounded-lg p-2.5"
                  style={moodCfg ? { background: 'rgba(255,255,255,0.08)', borderColor: moodCfg.btnColor + '40' } : { background: 'rgba(244,185,66,0.1)' }}>
                  {spinSelectedRecord.cover_url ? (
                    <AlbumArt src={spinSelectedRecord.cover_url} alt={`${spinSelectedRecord.artist} ${spinSelectedRecord.title} vinyl record`} className="w-11 h-11 rounded-md object-cover shadow-sm" />
                  ) : (
                    <div className="w-11 h-11 rounded-md bg-stone-100 flex items-center justify-center"><Disc className="w-5 h-5 text-stone-400" /></div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={moodCfg ? { color: '#eee' } : {}}>{spinSelectedRecord.title}</p>
                    <p className="text-xs truncate" style={{ color: moodCfg ? '#aaa' : '#8A6B4A' }}>{spinSelectedRecord.artist}</p>
                  </div>
                  <button onClick={deselectSpinRecord} className="p-1 rounded-full hover:bg-black/10"
                    style={moodCfg ? { color: '#999' } : { color: '#8A6B4A' }}
                    data-testid="spin-deselect-record">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            <Input placeholder="Track (optional)" value={spinTrack} onChange={e => setSpinTrack(e.target.value)}
              className="border-honey/50"
              style={moodCfg ? { background: 'rgba(255,255,255,0.08)', color: '#eee', borderColor: moodCfg.btnColor + '60' } : {}}
              data-testid="spin-track-input" />

            <div>
              <label className="text-sm font-medium mb-2 block" style={moodCfg ? { color: moodCfg.btnColor } : { color: '#8A6B4A' }}>
                how does it feel?
              </label>
              <div className="grid grid-cols-3 gap-2">
                {MOOD_KEYS.map(m => {
                  const mc = MOOD_CONFIG[m];
                  const isSelected = spinMood === m;
                  return (
                    <button key={m}
                      onClick={() => setSpinMood(isSelected ? '' : m)}
                      className="px-3 py-2 rounded-lg text-xs font-medium transition-all"
                      style={{
                        background: isSelected ? mc.btnColor + '26' : (moodCfg ? 'rgba(255,255,255,0.08)' : '#faf5ff'),
                        color: isSelected ? mc.btnColor : (moodCfg ? '#ccc' : '#7e22ce'),
                        border: isSelected ? `2px solid ${mc.btnColor}` : '2px solid transparent',
                        transform: isSelected ? 'scale(1.06)' : 'scale(1)',
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
              placeholder={moodCfg ? moodCfg.placeholder : 'add a note...'}
              value={spinCaption} onChange={setSpinCaption}
              className="resize-none"
              style={moodCfg ? { background: 'rgba(255,255,255,0.08)', color: '#eee', borderColor: moodCfg.btnColor + '60' } : { borderColor: 'rgba(200,134,26,0.5)' }}
              rows={2} data-testid="spin-caption-input" />

            <Button onClick={submitNowSpinning} disabled={submitting || !spinRecordId}
              className="w-full rounded-full transition-all duration-200"
              style={moodCfg ? { backgroundColor: moodCfg.btnColor, color: '#fff' } : { backgroundColor: '#F4B942', color: '#1F1F1F' }}
              data-testid="spin-submit-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Disc className="w-4 h-4 mr-2" />}
              {moodCfg ? `Post Now Spinning · ${MOOD_CONFIG[spinMood].emoji} ${spinMood}` : 'Post Now Spinning'}
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
            <MentionTextarea placeholder="Caption (optional)" value={haulCaption} onChange={setHaulCaption} className="border-honey/50 resize-none" rows={2} data-testid="haul-caption-input" />
            <Button onClick={submitNewHaul} disabled={submitting || haulItems.length === 0} className="w-full bg-amber-100 text-amber-800 hover:bg-amber-200 rounded-full" data-testid="haul-submit-btn">
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
            {!isoSelectedRelease && !isoManualMode ? (
              <>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input placeholder="Search Discogs for an album..." value={isoDiscogsQuery}
                    onChange={e => { setIsoDiscogsQuery(e.target.value); searchDiscogsForISO(e.target.value); }}
                    className="pl-9 border-honey/50" data-testid="iso-discogs-search" autoFocus />
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
                <MentionTextarea placeholder="Caption (optional)" value={isoCaption} onChange={setIsoCaption} className="border-honey/50 resize-none" rows={2} data-testid="iso-caption-input" />
                <Button onClick={submitISO} disabled={submitting || (isoManualMode && (!isoArtist || !isoAlbum)) || (!isoManualMode && !isoSelectedRelease)}
                  className="w-full bg-blue-100 text-blue-800 hover:bg-blue-200 rounded-full" data-testid="iso-submit-btn">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                  Post ISO
                </Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* ═══ A Note Modal ═══ */}
      <Dialog open={activeModal === 'NOTE'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="sr-only">A Note</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <MentionTextarea
              placeholder="what's on your mind?"
              value={noteText}
              onChange={v => setNoteText(v.slice(0, 1500))}
              className="border-stone-200 resize-none text-base min-h-[120px] focus-visible:ring-amber-300"
              rows={4}
              maxLength={1500}
              autoFocus
              data-testid="note-text-input"
            />
            <div className="flex items-center justify-between">
              <span className={`text-xs ${noteText.length > 260 ? 'text-amber-600 font-medium' : 'text-muted-foreground'}`}>
                {noteText.length}/1500
              </span>
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
                  <SelectValue placeholder="Choose from your collection" />
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
                <div className="w-40 h-40 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center animate-pulse">
                  <Shuffle className="w-10 h-10 text-amber-600 animate-spin" />
                </div>
                <p className="text-sm text-muted-foreground mt-3">shuffling your collection...</p>
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
                <p className="text-sm">No records found in your collection</p>
              </div>
            )}

            {/* Caption */}
            {randRecord && !randAnimating && (
              <>
                <MentionTextarea
                  placeholder="Add a caption (optional)"
                  value={randCaption} onChange={setRandCaption}
                  className="border-honey/50 resize-none"
                  rows={2} data-testid="randomizer-caption-input"
                />

                {/* Buttons */}
                <div className="space-y-2">
                  <Button onClick={submitRandomPost} disabled={submitting}
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
