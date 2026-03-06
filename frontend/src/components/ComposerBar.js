import React, { useState, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { Disc, Package, Search, Loader2, X, Feather, ImagePlus, Tag } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import AlbumArt from './AlbumArt';

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

  const resetAll = () => {
    setSpinRecordId(''); setSpinTrack(''); setSpinCaption(''); setSpinMood('');
    setHaulStoreName(''); setHaulCaption(''); setHaulItems([]); setHaulSearch(''); setHaulResults([]);
    setIsoArtist(''); setIsoAlbum(''); setIsoPressing(''); setIsoCondition('');
    setIsoPriceMin(''); setIsoPriceMax(''); setIsoCaption('');
    setIsoDiscogsQuery(''); setIsoDiscogsResults([]); setIsoSelectedRelease(null); setIsoManualMode(false);
    setNoteText(''); setNoteRecordId(''); setNoteShowRecordPicker(false); setNoteImageUrl(''); setNoteUploading(false);
  };

  const openModal = (type) => { resetAll(); setActiveModal(type); };
  const closeModal = () => { setActiveModal(null); resetAll(); };

  const searchDiscogs = useCallback(async (query) => {
    if (!query || query.length < 2) { setHaulResults([]); return; }
    setSearchLoading(true);
    try {
      const resp = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHaulResults(resp.data.slice(0, 8));
    } catch { setHaulResults([]); }
    finally { setSearchLoading(false); }
  }, [API, token]);

  const searchDiscogsForISO = useCallback(async (query) => {
    if (!query || query.length < 2) { setIsoDiscogsResults([]); return; }
    setIsoSearchLoading(true);
    try {
      const resp = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsoDiscogsResults(resp.data.slice(0, 8));
    } catch { setIsoDiscogsResults([]); }
    finally { setIsoSearchLoading(false); }
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
    if (!file.type.startsWith('image/')) { toast.error('images only.'); return; }
    if (file.size > 5 * 1024 * 1024) { toast.error('max 5mb.'); return; }
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
    { key: 'ISO', label: 'ISO', icon: Search, color: 'bg-blue-100 text-blue-800' },
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
              <Select value={spinRecordId} onValueChange={setSpinRecordId}>
                <SelectTrigger
                  className="border-honey/50"
                  style={moodCfg ? { background: 'rgba(255,255,255,0.08)', color: '#ddd', borderColor: moodCfg.btnColor + '60' } : {}}
                  data-testid="spin-record-select">
                  <SelectValue placeholder="Choose from your collection" />
                </SelectTrigger>
                <SelectContent>
                  {records.map(r => (
                    <SelectItem key={r.id} value={r.id}>{r.artist} · {r.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
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

            <Textarea
              placeholder={moodCfg ? moodCfg.placeholder : 'add a note...'}
              value={spinCaption} onChange={e => setSpinCaption(e.target.value)}
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
                    <button key={r.discogs_id} onClick={() => addHaulItem(r)} className="w-full text-left px-3 py-2 hover:bg-honey/10 flex items-center gap-2 text-sm border-b border-honey/10 last:border-0">
                      <AlbumArt src={r.cover_url} alt="" className="w-8 h-8 rounded object-cover" />
                      <span className="truncate">{r.artist} · {r.title}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            {haulItems.length > 0 && (
              <div className="space-y-2">
                {haulItems.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-honey/10 rounded-lg px-3 py-2">
                    <AlbumArt src={item.cover_url} alt="" className="w-8 h-8 rounded object-cover" />
                    <span className="flex-1 text-sm truncate">{item.artist} · {item.title}</span>
                    <button onClick={() => setHaulItems(prev => prev.filter((_, i) => i !== idx))} className="text-muted-foreground hover:text-red-500"><X className="w-4 h-4" /></button>
                  </div>
                ))}
                <p className="text-xs text-muted-foreground">{haulItems.length} record{haulItems.length !== 1 ? 's' : ''}</p>
              </div>
            )}
            <Textarea placeholder="Caption (optional)" value={haulCaption} onChange={e => setHaulCaption(e.target.value)} className="border-honey/50 resize-none" rows={2} data-testid="haul-caption-input" />
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
                      <button key={r.discogs_id} onClick={() => selectIsoRelease(r)} className="w-full text-left px-3 py-2 hover:bg-honey/10 flex items-center gap-3 text-sm border-b border-honey/10 last:border-0" data-testid={`iso-discogs-result-${r.discogs_id}`}>
                        {r.cover_url ? <AlbumArt src={r.cover_url} alt="" className="w-10 h-10 rounded object-cover" /> : <Disc className="w-10 h-10 text-honey/30" />}
                        <div className="min-w-0 flex-1"><p className="font-medium truncate">{r.title}</p><p className="text-xs text-muted-foreground truncate">{r.artist} {r.year ? `(${r.year})` : ''}</p></div>
                      </button>
                    ))}
                  </div>
                )}
                <button onClick={() => setIsoManualMode(true)} className="text-sm text-honey-amber hover:underline" data-testid="iso-manual-entry-btn">Or enter manually</button>
              </>
            ) : isoSelectedRelease ? (
              <div className="flex items-center gap-3 bg-blue-50 rounded-lg p-3">
                {isoSelectedRelease.cover_url ? <AlbumArt src={isoSelectedRelease.cover_url} alt="" className="w-14 h-14 rounded-lg object-cover shadow" /> : <Disc className="w-14 h-14 text-blue-300" />}
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
                <Textarea placeholder="Caption (optional)" value={isoCaption} onChange={e => setIsoCaption(e.target.value)} className="border-honey/50 resize-none" rows={2} data-testid="iso-caption-input" />
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
            <Textarea
              placeholder="what's on your mind?"
              value={noteText}
              onChange={e => { if (e.target.value.length <= 280) setNoteText(e.target.value); }}
              className="border-stone-200 resize-none text-base min-h-[120px] focus-visible:ring-amber-300"
              rows={4}
              autoFocus
              data-testid="note-text-input"
            />
            <div className="flex items-center justify-between">
              <span className={`text-xs ${noteText.length > 260 ? 'text-amber-600 font-medium' : 'text-muted-foreground'}`}>
                {noteText.length}/280
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
                <input ref={noteFileRef} type="file" accept="image/*" className="hidden" onChange={handleNoteImageUpload} />
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
                  <AlbumArt src={noteRecord.cover_url} alt="" className="w-8 h-8 rounded object-cover" />
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
    </>
  );
};

export default ComposerBar;
