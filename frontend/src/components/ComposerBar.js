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
import { Disc, Package, Search, Loader2, X, Feather, ImagePlus, Tag, Shuffle, ChevronDown, Music, RefreshCw, Camera, BarChart3, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { validateImageFile, prepareImageForUpload } from '../utils/imageUpload';
import AlbumArt from './AlbumArt';
import RecordSearchResult from './RecordSearchResult';

const MOOD_CONFIG = {
  'New Arrival': { emoji: '\u{1F4E6}', bg: '#1a1a08', btnColor: '#c8861a', placeholder: 'what just came in the mail?' },
  'Deep Listening': { emoji: '\u{1F9D8}', bg: '#0a1a2a', btnColor: '#4a7aaa', placeholder: 'what are you really hearing right now?' },
  'In The Zone': { emoji: '\u{1F3AF}', bg: '#0a1a0a', btnColor: '#2a6a2a', placeholder: 'locked in. what are you working to?' },
  'Me Time': { emoji: '\u{1F9CD}', bg: '#1a1230', btnColor: '#6a3a9a', placeholder: 'just you and the record...' },
  'Cleaning Session': { emoji: '\u{1F9FC}', bg: '#0a2a1a', btnColor: '#3a9a5a', placeholder: 'fresh grooves only...' },
  'Spin Party': { emoji: '\u{1FAA9}', bg: '#1a0a2a', btnColor: '#aa3a8a', placeholder: "who's pulling up?" },
  'Limited Edition': { emoji: '\u{1F48E}', bg: '#0a0a2a', btnColor: '#5a5aaa', placeholder: 'how rare is this one?' },
  'Vibe Check': { emoji: '\u2728', bg: '#2a1a08', btnColor: '#aa7a3a', placeholder: "what's the vibe?" },
  'Late Night': { emoji: '\u{1F319}', bg: '#0a0a1a', btnColor: '#4a4a8a', placeholder: 'what are you listening to at this hour?' },
  'Background': { emoji: '\u2615', bg: '#1a1208', btnColor: '#8a6a3a', placeholder: "what's on in the background?" },
  'In My Feels': { emoji: '\u{1F972}', bg: '#1a1a2a', btnColor: '#5a5a8a', placeholder: 'some records just hit different...' },
  'Daydreaming': { emoji: '\u2601\uFE0F', bg: '#0a1a2a', btnColor: '#6a8aaa', placeholder: 'where is this record taking you?' },
};
const MOOD_KEYS = Object.keys(MOOD_CONFIG);

const ComposerBar = React.forwardRef(({ onPostCreated, records = [] }, ref) => {
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
  const [postToHive, setPostToHive] = useState(true);
  const [haulPostToHive, setHaulPostToHive] = useState(true);
  const [isoPostToHive, setIsoPostToHive] = useState(true);

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
  const [isoShowCount, setIsoShowCount] = useState(6);
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
  const [noteSearch, setNoteSearch] = useState('');
  const [noteSearchResults, setNoteSearchResults] = useState([]);
  const noteSearchTimerRef = useRef(null);
  // Dedicated photo state for Spinning/Haul
  const [postPhoto, setPostPhoto] = useState(null);
  const [postPhotoPreview, setPostPhotoPreview] = useState(null);
  const postPhotoInputRef = useRef(null);
  // Randomizer
  const [randRecord, setRandRecord] = useState(null);
  const [randCaption, setRandCaption] = useState('');
  const [randLoading, setRandLoading] = useState(false);
  const [randAnimating, setRandAnimating] = useState(false);

  // Poll
  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptions, setPollOptions] = useState(['', '']);

  const resetAll = () => {
    setSpinRecordId(''); setSpinTrack(''); setSpinCaption(''); setSpinMood('');
    setSpinSearch(''); setSpinSearchResults([]); setSpinSelectedRecord(null);
    setSpinTracks([]); setSpinTracksLoading(false); setSpinTrackDropdownOpen(false); setSpinTrackSearch(''); setSpinTracksFetched(false);
    setPostToHive(true);
    setHaulStoreName(''); setHaulCaption(''); setHaulItems([]); setHaulSearch(''); setHaulResults([]);
    setHaulPostToHive(true);
    setIsoArtist(''); setIsoAlbum(''); setIsoPressing(''); setIsoCondition('');
    setIsoPriceMin(''); setIsoPriceMax(''); setIsoCaption('');
    setIsoDiscogsQuery(''); setIsoDiscogsResults([]); setIsoSelectedRelease(null); setIsoManualMode(false); setIsoIntent(null);
    setIsoPostToHive(true);
    setNoteText(''); setNoteRecordId(''); setNoteShowRecordPicker(false); setNoteImageUrl(''); setNoteUploading(false); setNoteSearch(''); setNoteSearchResults([]);
    setRandRecord(null); setRandCaption(''); setRandLoading(false); setRandAnimating(false);
    setPollQuestion(''); setPollOptions(['', '']);
    setPostPhoto(null); setPostPhotoPreview(null);
    if (postPhotoInputRef.current) postPhotoInputRef.current.value = '';
  };

  // Expose openSpinWithRecord to parent components via ref
  React.useImperativeHandle(ref, () => ({
    openSpinWithRecord: (record) => {
      resetAll();
      setSpinRecordId(record.id);
      setSpinSelectedRecord(record);
      setActiveModal('NOW_SPINNING');
    }
  }));

  const handlePhotoSelect = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const err = validateImageFile(file);
      if (err) { toast.error(err); e.target.value = ''; return; }
      const prepared = await prepareImageForUpload(file);
      setPostPhoto(prepared);
      setPostPhotoPreview(URL.createObjectURL(prepared));
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
      if (noteSearchTimerRef.current) clearTimeout(noteSearchTimerRef.current);
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

  // Local collection search for Note record tagging
  const searchCollectionForNote = useCallback((query) => {
    if (noteSearchTimerRef.current) clearTimeout(noteSearchTimerRef.current);
    if (!query || query.length < 2) { setNoteSearchResults([]); return; }
    noteSearchTimerRef.current = setTimeout(() => {
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
      setNoteSearchResults(scored);
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
    if (!query || query.length < 2) { setIsoDiscogsResults([]); setIsoSearchLoading(false); setIsoShowCount(6); return; }
    if (isoSearchTimer.current) clearTimeout(isoSearchTimer.current);
    isoSearchTimer.current = setTimeout(async () => {
      setIsoSearchLoading(true);
      try {
        const resp = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(query)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setIsoDiscogsResults(resp.data || []);
        setIsoShowCount(6);
      } catch { setIsoDiscogsResults([]); }
      finally { setIsoSearchLoading(false); }
    }, 350);
  }, [API, token]);

  const selectIsoRelease = (release) => {
    setIsoSelectedRelease(release); setIsoDiscogsResults([]); setIsoDiscogsQuery(''); setIsoShowCount(6);
    setIsoArtist(release.artist); setIsoAlbum(release.title);
  };

  const addHaulItem = (item) => {
    if (haulItems.find(h => h.discogs_id === item.discogs_id)) return;
    setHaulItems(prev => [...prev, { discogs_id: item.discogs_id, title: item.title, artist: item.artist, imageUrl: item.imageUrl, imageSmall: item.imageSmall, cover_url: item.cover_url, year: item.year, imageSource: item.imageSource, spotifyAlbumId: item.spotifyAlbumId }]);
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
    try {
      const res = await axios.post(`${API}/upload`, formData, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
      });
      return res.data.url;
    } catch (err) {
      const detail = err.response?.data?.detail || 'image upload failed. try a different photo.';
      toast.error(detail);
      throw err;
    }
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
        post_to_hive: postToHive,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success(postToHive ? 'now spinning posted.' : 'spin logged silently.');
      trackEvent(postToHive ? 'now_spinning_posted' : 'silent_spin_logged');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const submitNewHaul = async () => {
    if (haulItems.length === 0) { toast.error('add at least one record.'); return; }
    if (haulPostToHive && !haulCaption.trim()) { toast.error('a caption is required to share with the hive.'); return; }
    setSubmitting(true);
    try {
      let photoUrl = null;
      if (postPhoto) photoUrl = await uploadPostPhoto();
      await axios.post(`${API}/composer/new-haul`, {
        store_name: haulStoreName || null, caption: haulCaption || null, items: haulItems,
        image_url: photoUrl, post_to_hive: haulPostToHive,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success(haulPostToHive ? 'haul posted to the hive.' : 'haul logged to your vault.');
      trackEvent(haulPostToHive ? 'haul_posted' : 'silent_haul_logged');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const submitISO = async () => {
    const artist = isoArtist || isoSelectedRelease?.artist;
    const album = isoAlbum || isoSelectedRelease?.title;
    if (!artist || !album) { toast.error('artist and album are required.'); return; }
    if (isoPostToHive && !isoCaption.trim()) { toast.error('a caption is required to share with the hive.'); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/composer/iso`, {
        artist, album,
        discogs_id: isoSelectedRelease?.discogs_id || null,
        cover_url: isoSelectedRelease?.cover_url || null,
        year: isoSelectedRelease?.year || null,
        color_variant: isoSelectedRelease?.color_variant || null,
        pressing_notes: isoPressing || null,
        condition_pref: isoCondition || null,
        target_price_min: isoPriceMin ? parseFloat(isoPriceMin) : null,
        target_price_max: isoPriceMax ? parseFloat(isoPriceMax) : null,
        caption: isoCaption || null,
        intent: isoIntent || 'seeking',
        post_to_hive: isoPostToHive,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success(isoPostToHive ? (isoIntent === 'dreaming' ? 'dream added & shared with the hive.' : 'iso posted to the hive.') : (isoIntent === 'dreaming' ? 'added to dream list.' : 'iso saved.'));
      trackEvent(isoPostToHive ? 'iso_posted' : 'silent_iso_logged');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post'); }
    finally { setSubmitting(false); }
  };

  const handleNoteImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const { validateImageFile, prepareImageForUpload } = await import('../utils/imageUpload');
    const err = validateImageFile(file);
    if (err) { toast.error(err); return; }
    setNoteUploading(true);
    try {
      const prepared = await prepareImageForUpload(file);
      const formData = new FormData();
      formData.append('file', prepared);
      const r = await axios.post(`${API}/upload`, formData, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
      });
      setNoteImageUrl(r.data.url);
    } catch (uploadErr) { toast.error(uploadErr.response?.data?.detail || 'upload failed. try again.'); }
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

  const submitPoll = async () => {
    const q = pollQuestion.trim();
    if (!q) { toast.error('write a question first.'); return; }
    if (q.length > 500) { toast.error('question must be 500 characters or less.'); return; }
    const opts = pollOptions.map(o => o.trim()).filter(Boolean);
    if (opts.length < 2) { toast.error('add at least 2 options.'); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/composer/poll`, { question: q, options: opts }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('poll posted!');
      closeModal(); onPostCreated?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to post poll'); }
    finally { setSubmitting(false); }
  };

  const moodCfg = spinMood ? MOOD_CONFIG[spinMood] : null;
  const noteRecord = records.find(r => r.id === noteRecordId);

  const spectrum = [
    { key: 'NOW_SPINNING', label: 'Now Spinning', icon: Music },
    { key: 'NEW_HAUL', label: 'Haul', icon: Package },
    { key: 'ISO', label: 'ISO', icon: Search },
    { key: 'NOTE', label: 'Note', icon: Feather },
    { key: 'RANDOMIZER', label: 'Randomizer', icon: Shuffle },
    { key: 'POLL', label: 'Poll', icon: BarChart3 },
  ];

  return (
    <>
      {/* Composer Bar — Command Center */}
      <div className="bg-white rounded-xl border border-honey/30 p-4 max-sm:p-3 mb-6 shadow" data-testid="composer-bar">
        <p className="text-sm text-muted-foreground mb-1">What's on the turntable?</p>
        <p className="text-[10px] text-muted-foreground/70 mb-3 italic">Only posts with comments will be shared in The Hive.</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {spectrum.map(chip => {
            const Icon = chip.icon;
            return (
              <button
                key={chip.key}
                onClick={() => chip.key === 'RANDOMIZER' ? openRandomizer() : openModal(chip.key)}
                className="h-10 rounded-xl text-sm font-semibold flex items-center justify-center gap-1.5 transition-all hover:scale-[1.03] hover:shadow-md"
                style={{ background: '#FDE68A', color: '#78350F', border: '1px solid rgba(0,0,0,0.05)', padding: '0 10px' }}
                onMouseEnter={e => { e.currentTarget.style.background = '#FBBF24'; e.currentTarget.style.borderColor = '#DAA520'; }}
                onMouseLeave={e => { e.currentTarget.style.background = '#FDE68A'; e.currentTarget.style.borderColor = 'rgba(0,0,0,0.05)'; }}
                data-testid={`composer-chip-${chip.key.toLowerCase()}`}
              >
                {chip.emoji ? <span className="text-sm shrink-0 leading-none">{chip.emoji}</span> : <Icon className="w-4 h-4 shrink-0" style={{ color: '#78350F' }} />}
                <span className="text-xs sm:text-sm" style={{ whiteSpace: 'nowrap' }}>{chip.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ═══ Now Spinning Modal (merged with Mood) ═══ */}
      <Dialog open={activeModal === 'NOW_SPINNING'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md max-h-[90dvh] flex flex-col overflow-hidden p-0 max-sm:max-w-[95vw] max-sm:max-h-[88dvh]">
          <div className="px-6 max-sm:px-4 pt-6 max-sm:pt-4 pb-2 shrink-0">
            <DialogHeader>
              <DialogTitle className="font-heading flex items-center gap-2 shrink" style={{ color: '#D4A828' }}>
                <Music className="w-5 h-5 shrink-0" /> <span className="shrink">Now Spinning</span>
                {spinMood && <span className="text-sm font-normal ml-1">· {MOOD_CONFIG[spinMood].emoji} {spinMood}</span>}
              </DialogTitle>
              <DialogDescription>
                Share what you're listening to right now
              </DialogDescription>
            </DialogHeader>
          </div>

          {/* Scrollable content area */}
          <div className="flex-1 overflow-y-auto px-6 max-sm:px-4 min-h-0">
            <div className="space-y-3 max-sm:space-y-2 pb-2">
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
                        <p className="text-sm" style={{ color: '#3A4D63' }}>
                          no results in your vault
                        </p>
                        <a href="/add-record" className="text-xs mt-1 inline-block hover:underline"
                          style={{ color: '#D4A828' }}
                          data-testid="spin-add-record-link">
                          add it first &rarr;
                        </a>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-3 rounded-lg p-2" style={{ background: 'rgba(244,185,66,0.1)' }}>
                    {(spinSelectedRecord.imageUrl || spinSelectedRecord.cover_url) ? (
                      <AlbumArt src={spinSelectedRecord.imageSmall || spinSelectedRecord.imageUrl || spinSelectedRecord.cover_url} alt={`${spinSelectedRecord.artist} ${spinSelectedRecord.title} vinyl record`} className="w-10 h-10 max-sm:w-8 max-sm:h-8 rounded-md object-cover shadow-sm" />
                    ) : (
                      <div className="w-10 h-10 max-sm:w-8 max-sm:h-8 rounded-md bg-[#F3EBE0] flex items-center justify-center"><Disc className="w-5 h-5 text-[#7A8694]" /></div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{spinSelectedRecord.title}</p>
                      <p className="text-xs truncate" style={{ color: '#3A4D63' }}>{spinSelectedRecord.artist}</p>
                    </div>
                    <button onClick={deselectSpinRecord} className="p-1 rounded-full hover:bg-black/10"
                      style={{ color: '#3A4D63' }}
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
                      <span className="w-1 rounded-full animate-pulse" style={{ background: '#D4A828', height: '8px', animationDelay: '0ms', animationDuration: '800ms' }} />
                      <span className="w-1 rounded-full animate-pulse" style={{ background: '#D4A828', height: '12px', animationDelay: '200ms', animationDuration: '800ms' }} />
                      <span className="w-1 rounded-full animate-pulse" style={{ background: '#D4A828', height: '16px', animationDelay: '400ms', animationDuration: '800ms' }} />
                      <span className="w-1 rounded-full animate-pulse" style={{ background: '#D4A828', height: '10px', animationDelay: '600ms', animationDuration: '800ms' }} />
                    </div>
                    <span style={{ color: '#3A4D63' }}>Fetching tracks... 🐝</span>
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
                        style={{ color: '#D4A828' }}
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
                      color: spinTrack ? '#1a1a1a' : '#3A4D63',
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
                        className="shrink-0 p-2 rounded-md transition-colors hover:bg-[#F0E6C8]"
                        title="Retry fetching tracklist"
                        data-testid="spin-track-refresh"
                      >
                        <RefreshCw className="w-4 h-4" style={{ color: '#D4A828' }} />
                      </button>
                    )}
                  </div>
                )}
              </div>

              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: '#3A4D63' }}>
                  how does it feel?
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {MOOD_KEYS.map(m => {
                    const mc = MOOD_CONFIG[m];
                    const isSelected = spinMood === m;
                    return (
                      <button key={m}
                        onClick={() => setSpinMood(isSelected ? '' : m)}
                        className="flex items-center justify-center rounded-lg font-medium transition-all whitespace-nowrap"
                        style={{
                          height: '36px',
                          fontSize: '10.5px',
                          padding: '0 6px',
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
                <p className="text-xs italic mt-1" style={{ color: '#D4A828' }} data-testid="spin-caption-helper">
                  Tell the hive what you love about this record! 🐝
                </p>
              )}

              {/* Photo upload */}
              <input type="file" accept="image/*" ref={postPhotoInputRef} onChange={handlePhotoSelect} className="hidden" data-testid="spin-photo-input" />
              {postPhotoPreview ? (
                <div className="relative inline-block rounded-lg overflow-hidden border border-honey/30" data-testid="spin-photo-preview">
                  <img src={postPhotoPreview} alt="Upload preview" className="h-20 w-20 object-cover max-sm:h-16 max-sm:w-16" />
                  <button onClick={clearPostPhoto} className="absolute top-0.5 right-0.5 bg-black/60 text-white rounded-full p-0.5" data-testid="spin-photo-remove">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => postPhotoInputRef.current?.click()}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-dashed border-honey/40 text-[#3A4D63] hover:text-[#3A4D63] hover:border-honey/60 transition-colors"
                  data-testid="spin-photo-upload-btn"
                >
                  <Camera className="w-3.5 h-3.5" /> Add a photo
                </button>
              )}
            </div>
          </div>

          {/* Sticky footer — always visible */}
          <div className="shrink-0 px-6 max-sm:px-4 pt-3 max-sm:pt-2 border-t border-honey/15 bg-white" style={{ paddingBottom: 'max(1.25rem, env(safe-area-inset-bottom, 0.75rem))' }}>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-[#3A4D63] flex items-center gap-1.5 cursor-pointer" data-testid="post-to-hive-label">
                Post to Hive
              </label>
              <button
                type="button"
                role="switch"
                aria-checked={postToHive}
                onClick={() => setPostToHive(!postToHive)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${postToHive ? 'bg-[#D4A828]' : 'bg-[#E5DBC8]'}`}
                data-testid="post-to-hive-toggle"
              >
                <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${postToHive ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </button>
            </div>
            {!postToHive && <p className="text-xs text-[#7A8694] mb-2" data-testid="silent-spin-hint">Silent spin — logged to your Vault only, not posted to the feed.</p>}
            <Button onClick={submitNowSpinning} disabled={submitting || !spinRecordId || (!postToHive ? false : !spinCaption.trim())}
              className="w-full rounded-full transition-all duration-200 text-white"
              style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)' }}
              data-testid="spin-submit-btn">
              {submitting ? (
                <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Spinning your record...</>
              ) : (
                <><Disc className="w-4 h-4 mr-2" /> {postToHive ? (spinMood ? `Post Now Spinning · ${MOOD_CONFIG[spinMood].emoji} ${spinMood}` : 'Post Now Spinning') : 'Log Silent Spin'}</>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* ═══ New Haul Modal ═══ */}
      <Dialog open={activeModal === 'NEW_HAUL'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-lg max-h-[90dvh] flex flex-col overflow-hidden p-0 max-sm:max-w-[95vw] max-sm:max-h-[88dvh]">
          <div className="px-6 max-sm:px-4 pt-6 max-sm:pt-4 pb-2 shrink-0">
            <DialogHeader>
              <DialogTitle className="font-heading flex items-center gap-2"><Package className="w-5 h-5 text-[#D4A828]" /> New Haul</DialogTitle>
              <DialogDescription>Share your latest finds</DialogDescription>
            </DialogHeader>
          </div>
          <div className="flex-1 overflow-y-auto px-6 max-sm:px-4 min-h-0">
          <div className="space-y-4 pt-2 pb-4">
            {/* 1. Records found — primary focus */}
            <div>
              <label className="text-sm font-medium mb-1 block">Records found</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input placeholder="Search Discogs to add records..." value={haulSearch}
                  onChange={e => { setHaulSearch(e.target.value); searchDiscogs(e.target.value); }}
                  className="pl-9 border-honey/50" data-testid="haul-search-input" />
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
            {/* Selected items with prominent album art */}
            {haulItems.length > 0 && (
              <div className="space-y-2">
                {haulItems.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-3 rounded-lg p-2" style={{ background: 'rgba(244,185,66,0.1)' }}>
                    <AlbumArt src={item.imageSmall || item.imageUrl || item.cover_url} alt={`${item.artist} ${item.title} vinyl record`} className="w-12 h-12 rounded-md object-cover shadow-sm" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{item.title}</p>
                      <p className="text-xs truncate" style={{ color: '#3A4D63' }}>{item.artist}</p>
                      {item.imageSource === 'spotify' && (
                        <a
                          href={item.spotifyAlbumId
                            ? `https://open.spotify.com/album/${item.spotifyAlbumId}`
                            : `https://open.spotify.com/search/${encodeURIComponent(`${item.artist || ''} ${item.title || ''}`.trim())}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={e => e.stopPropagation()}
                          className="inline-flex items-center gap-1 mt-0.5 text-[10px] text-[#7A8694] hover:text-[#1DB954] transition-colors"
                          data-testid={`haul-spotify-link-${idx}`}
                        >
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
                          Spotify
                        </a>
                      )}
                    </div>
                    <button onClick={() => setHaulItems(prev => prev.filter((_, i) => i !== idx))} className="p-1 rounded-full hover:bg-black/10 text-muted-foreground hover:text-red-500"><X className="w-4 h-4" /></button>
                  </div>
                ))}
                <p className="text-xs text-muted-foreground">{haulItems.length} record{haulItems.length !== 1 ? 's' : ''}</p>
              </div>
            )}
            {/* 2. Location — optional */}
            <div>
              <label className="text-xs font-medium mb-1 block" style={{ color: '#3A4D63' }}>📍 Where'd you find them? <span className="text-muted-foreground font-normal">(optional)</span></label>
              <Input placeholder="Record store, thrift shop, eBay..." value={haulStoreName} onChange={e => setHaulStoreName(e.target.value)} className="border-honey/50" data-testid="haul-store-input" />
            </div>
            {/* 3. Caption */}
            <MentionTextarea placeholder="I just got..." value={haulCaption} onChange={setHaulCaption} className="border-honey/50 resize-none" rows={2} data-testid="haul-caption-input" style={{ borderColor: 'rgba(200,134,26,0.5)' }} />
            {/* 4. Photo Upload */}
            <div className="px-1">
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
                  className="flex items-center gap-2 text-[#3A4D63] hover:text-[#D4A828] transition text-sm font-medium border border-dashed border-[#E5DBC8] rounded-lg p-3 w-full justify-center"
                >
                  <ImagePlus size={18} />
                  Add a photo of your haul (Optional)
                </button>
              ) : (
                <div className="relative w-full max-h-[200px] overflow-hidden rounded-xl group">
                  <img src={postPhotoPreview} className="w-full h-full object-cover border border-[#E5DBC8] shadow-sm" alt="Haul preview" />
                  <button 
                    onClick={clearPostPhoto}
                    className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1.5 shadow-md hover:bg-red-600 transition"
                  >
                    <X size={14} />
                  </button>
                </div>
              )}
            </div>
          </div>
          </div>
          {/* Sticky footer — always visible */}
          <div className="shrink-0 px-6 max-sm:px-4 pt-3 max-sm:pt-2 border-t border-honey/15 bg-white" style={{ paddingBottom: 'max(1rem, env(safe-area-inset-bottom, 0.75rem))' }}>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-[#3A4D63]" data-testid="haul-hive-label">
                Post to Hive
              </label>
              <button
                type="button"
                role="switch"
                aria-checked={haulPostToHive}
                onClick={() => setHaulPostToHive(!haulPostToHive)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${haulPostToHive ? 'bg-[#D4A828]' : 'bg-[#E5DBC8]'}`}
                data-testid="haul-post-to-hive-toggle"
              >
                <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${haulPostToHive ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </button>
            </div>
            {!haulPostToHive && <p className="text-xs text-[#7A8694] mb-2" data-testid="haul-silent-hint">Silent haul — logged to your Vault only, not posted to the feed.</p>}
            <Button onClick={() => {
              if (haulPostToHive && !haulCaption.trim()) { toast.error('a caption is required to share with the hive.'); return; }
              submitNewHaul();
            }} disabled={submitting || haulItems.length === 0} className="w-full bg-[#F0E6C8] text-[#1E2A3A] hover:bg-[#E8CA5A] rounded-full" data-testid="haul-submit-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Package className="w-4 h-4 mr-2" />}
              {haulPostToHive ? `Post Haul (${haulItems.length} record${haulItems.length !== 1 ? 's' : ''})` : `Log Haul to Vault (${haulItems.length})`}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* ═══ ISO Modal ═══ */}
      <Dialog open={activeModal === 'ISO'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md max-h-[90dvh] flex flex-col overflow-hidden p-0 max-sm:max-w-[95vw] max-sm:max-h-[88dvh]">
          <div className="px-6 max-sm:px-4 pt-6 max-sm:pt-4 pb-2 shrink-0">
            <DialogHeader>
              <DialogTitle className="font-heading flex items-center gap-2"><Search className="w-5 h-5 text-blue-600" /> In Search Of</DialogTitle>
              <DialogDescription>Let the community know what you're looking for</DialogDescription>
            </DialogHeader>
          </div>
          <div className="flex-1 overflow-y-auto px-6 max-sm:px-4 min-h-0">
          <div className="space-y-4 pt-2 pb-4">
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
                      <div>
                        <div className="border border-honey/30 rounded-lg max-h-48 overflow-y-auto bg-white">
                          {isoDiscogsResults.slice(0, isoShowCount).map(r => (
                            <RecordSearchResult key={r.discogs_id} record={r} onClick={() => selectIsoRelease(r)} size="sm" testId={`iso-discogs-result-${r.discogs_id}`} />
                          ))}
                        </div>
                        {isoDiscogsResults.length > isoShowCount && (
                          <button
                            onClick={() => setIsoShowCount(prev => prev + 6)}
                            className="w-full py-2 text-sm font-medium text-honey-amber hover:bg-honey/10 rounded-b-lg border border-t-0 border-honey/20 transition-colors"
                            data-testid="iso-composer-view-more-btn"
                          >
                            View More ({isoDiscogsResults.length - isoShowCount} remaining)
                          </button>
                        )}
                      </div>
                    )}
                    <button onClick={() => setIsoManualMode(true)} className="text-sm text-honey-amber hover:underline" data-testid="iso-manual-entry-btn">Or enter manually</button>
                  </>
                ) : isoSelectedRelease ? (
                  <div className="flex items-center gap-3 bg-blue-50 rounded-lg p-3">
                    {(isoSelectedRelease.imageUrl || isoSelectedRelease.cover_url) ? <AlbumArt src={isoSelectedRelease.imageSmall || isoSelectedRelease.imageUrl || isoSelectedRelease.cover_url} alt={`${isoSelectedRelease.artist} ${isoSelectedRelease.title} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow" /> : <Disc className="w-14 h-14 text-blue-300" />}
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
                    <MentionTextarea placeholder="I'm looking for this because..." value={isoCaption} onChange={setIsoCaption} className="border-honey/50 resize-none" rows={2} data-testid="iso-caption-input" style={{ borderColor: 'rgba(200,134,26,0.5)' }} />
                  </>
                )}
              </>
            )}
          </div>
          </div>
          {/* Sticky footer with toggle — only show when record is selected */}
          {(isoManualMode || isoSelectedRelease) && (
          <div className="shrink-0 px-6 max-sm:px-4 pt-3 max-sm:pt-2 border-t border-honey/15 bg-white" style={{ paddingBottom: 'max(1rem, env(safe-area-inset-bottom, 0.75rem))' }}>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-[#3A4D63]" data-testid="iso-hive-label">
                Post to Hive
              </label>
              <button
                type="button"
                role="switch"
                aria-checked={isoPostToHive}
                onClick={() => setIsoPostToHive(!isoPostToHive)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${isoPostToHive ? 'bg-[#D4A828]' : 'bg-[#E5DBC8]'}`}
                data-testid="iso-post-to-hive-toggle"
              >
                <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${isoPostToHive ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </button>
            </div>
            {!isoPostToHive && <p className="text-xs text-[#7A8694] mb-2" data-testid="iso-silent-hint">{isoIntent === 'dreaming' ? 'Added to your Dream List only.' : 'Saved privately — not posted to the feed.'}</p>}
            <Button onClick={submitISO} disabled={submitting || (isoManualMode && (!isoArtist || !isoAlbum)) || (!isoManualMode && !isoSelectedRelease)}
              className="w-full rounded-full"
              style={isoIntent === 'dreaming'
                ? { background: '#f3f4f6', color: '#374151' }
                : { background: 'linear-gradient(135deg, #FFD700, #DAA520)', color: '#1E2A3A' }
              }
              data-testid="iso-submit-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
              {isoPostToHive
                ? (isoIntent === 'dreaming' ? 'Add to Dream List & Share' : 'Post ISO to the Hive')
                : (isoIntent === 'dreaming' ? 'Add to Dream List' : 'Save ISO Privately')
              }
            </Button>
          </div>
          )}
    </DialogContent>
  </Dialog>

      {/* ═══ A Note Modal ═══ */}
      <Dialog open={activeModal === 'NOTE'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md max-h-[90dvh] flex flex-col overflow-hidden p-0 max-sm:max-w-[95vw] max-sm:max-h-[88dvh]">
          <div className="px-6 max-sm:px-4 pt-6 max-sm:pt-4 pb-2 shrink-0">
            <DialogHeader>
              <DialogTitle className="sr-only">A Note</DialogTitle>
            </DialogHeader>
          </div>
          <div className="flex-1 overflow-y-auto px-6 pb-6 min-h-0">
          <div className="space-y-3">
            <MentionTextarea
              placeholder="Thinking about..."
              value={noteText}
              onChange={v => setNoteText(isAdmin ? v : v.slice(0, 1500))}
              className="border-[#E5DBC8] resize-none text-base min-h-[120px] focus-visible:ring-[#D4A828]"
              rows={4}
              maxLength={isAdmin ? undefined : 1500}
              data-testid="note-text-input"
            />
            <div className="flex items-center justify-between">
              {isAdmin ? (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#F0E6C8] text-[#D4A828] border border-[#E5DBC8]" data-testid="admin-changelog-badge">
                  <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  Admin: Change Log Mode
                </span>
              ) : (
                <span className={`text-xs ${noteText.length > 260 ? 'text-[#D4A828] font-medium' : 'text-muted-foreground'}`}>
                  {noteText.length}/1500
                </span>
              )}
              <div className="flex items-center gap-3">
                {/* Tag a record */}
                <button
                  onClick={() => setNoteShowRecordPicker(!noteShowRecordPicker)}
                  className="text-xs text-[#7A8694] hover:text-[#D4A828] flex items-center gap-1 transition-colors"
                  data-testid="note-tag-record-btn"
                >
                  <Tag className="w-3.5 h-3.5" /> tag a record
                </button>
                {/* Image upload */}
                <button
                  onClick={() => noteFileRef.current?.click()}
                  className="text-xs text-[#7A8694] hover:text-[#D4A828] flex items-center gap-1 transition-colors"
                  data-testid="note-add-image-btn"
                >
                  <ImagePlus className="w-3.5 h-3.5" /> add image
                </button>
                <input ref={noteFileRef} type="file" accept=".jpg,.jpeg,.png,.webp,.heic,.heif" className="hidden" onChange={handleNoteImageUpload} />
              </div>
            </div>

            {/* Record search picker */}
            {noteShowRecordPicker && (
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="search your vault..."
                  value={noteSearch}
                  onChange={e => { setNoteSearch(e.target.value); searchCollectionForNote(e.target.value); }}
                  className="pl-9 border-[#E5DBC8]"
                  data-testid="note-record-search"
                  autoFocus
                />
                {noteSearchResults.length > 0 && (
                  <div className="absolute z-50 left-0 right-0 mt-1 border rounded-lg max-h-52 overflow-y-auto shadow-lg bg-white" style={{ borderColor: 'rgba(200,134,26,0.3)' }}>
                    {noteSearchResults.map(r => (
                      <RecordSearchResult key={r.id} record={r} onClick={() => { setNoteRecordId(r.id); setNoteShowRecordPicker(false); setNoteSearch(''); setNoteSearchResults([]); }} size="sm" testId={`note-result-${r.id}`} />
                    ))}
                  </div>
                )}
                {noteSearch.length >= 2 && noteSearchResults.length === 0 && (
                  <div className="absolute z-50 left-0 right-0 mt-1 border rounded-lg p-3 text-center shadow-lg bg-white" style={{ borderColor: 'rgba(200,134,26,0.3)' }}>
                    <p className="text-sm" style={{ color: '#3A4D63' }}>no results in your vault</p>
                  </div>
                )}
              </div>
            )}

            {/* Tagged record preview */}
            {noteRecord && (
              <div className="flex items-center gap-2 bg-[#FFFBF2] rounded-lg px-3 py-2" data-testid="note-tagged-record">
                {(noteRecord.imageUrl || noteRecord.cover_url) ? (
                  <AlbumArt src={noteRecord.imageSmall || noteRecord.imageUrl || noteRecord.cover_url} alt={`${noteRecord.artist} ${noteRecord.title} vinyl record`} className="w-8 h-8 rounded object-cover" />
                ) : (
                  <div className="w-8 h-8 rounded bg-[#F3EBE0] flex items-center justify-center"><Disc className="w-4 h-4 text-[#7A8694]" /></div>
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
              className="w-full rounded-full bg-[#D4A828] hover:bg-[#E8CA5A] text-white"
              data-testid="note-submit-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Feather className="w-4 h-4 mr-2" />}
              post to the hive
            </Button>
          </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* ═══ Randomizer Modal ═══ */}
      <Dialog open={activeModal === 'RANDOMIZER'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-sm max-h-[90dvh] flex flex-col overflow-hidden p-0 max-sm:max-w-[95vw] max-sm:max-h-[88dvh]">
          <div className="px-6 max-sm:px-4 pt-6 max-sm:pt-4 pb-2 shrink-0">
            <DialogHeader>
              <DialogTitle className="font-heading flex items-center gap-2 text-[#D4A828]">
                <Shuffle className="w-5 h-5" /> Randomizer
              </DialogTitle>
              <DialogDescription>What record should you spin today?</DialogDescription>
            </DialogHeader>
          </div>
          <div className="flex-1 overflow-y-auto px-6 pb-6 min-h-0">
          <div className="space-y-4 pt-2">
            {/* Record display */}
            {randAnimating ? (
              <div className="flex flex-col items-center py-8" data-testid="randomizer-shuffling">
                <div className="w-40 h-40 rounded-xl bg-gradient-to-br from-[#F0E6C8] to-[#F0E6C8] flex items-center justify-center honey-shimmer">
                  <Shuffle className="w-10 h-10 text-[#D4A828] animate-spin" />
                </div>
                <p className="text-sm text-muted-foreground mt-3">shuffling your vault...</p>
              </div>
            ) : randRecord ? (
              <div className="flex flex-col items-center" data-testid="randomizer-result">
                <div className="w-40 h-40 rounded-xl overflow-hidden shadow-lg border border-honey/30">
                  {(randRecord.imageUrl || randRecord.cover_url) ? (
                    <AlbumArt src={randRecord.imageSmall || randRecord.imageUrl || randRecord.cover_url} alt={`${randRecord.artist} ${randRecord.title}`} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-[#F3EBE0] flex items-center justify-center"><Disc className="w-12 h-12 text-[#7A8694]" /></div>
                  )}
                </div>
                <p className="font-heading text-base mt-3 text-center" data-testid="randomizer-album">{randRecord.title}</p>
                <p className="text-sm text-muted-foreground text-center" data-testid="randomizer-artist">{randRecord.artist}</p>
                {(randRecord.color_variant || randRecord.pressing_notes) && (
                  <p className="text-xs text-[#D4A828] mt-0.5" data-testid="randomizer-variant">{randRecord.color_variant || randRecord.pressing_notes}</p>
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
          </div>
        </DialogContent>
      </Dialog>

      {/* ═══ Poll Modal ═══ */}
      <Dialog open={activeModal === 'POLL'} onOpenChange={(o) => !o && closeModal()}>
        <DialogContent className="sm:max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-heading" style={{ color: '#8B6914' }}>
              <span className="text-lg">📊</span> Create a Poll
            </DialogTitle>
            <DialogDescription>Ask the hive a question.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-medium text-[#3A4D63] mb-1 block">Question</label>
              <Textarea
                placeholder="What's your question?"
                value={pollQuestion}
                onChange={(e) => setPollQuestion(e.target.value.slice(0, 500))}
                className="resize-none focus:border-[#D4A828]"
                style={{ borderColor: 'rgba(218,165,32,0.3)' }}
                rows={2}
                data-testid="poll-question-input"
              />
              <span className="text-xs text-[#7A8694] float-right mt-0.5">{pollQuestion.length}/500</span>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-[#3A4D63]">Options</label>
              {pollOptions.map((opt, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <Input
                    placeholder={`Option ${i + 1}`}
                    value={opt}
                    onChange={(e) => {
                      const next = [...pollOptions];
                      next[i] = e.target.value;
                      setPollOptions(next);
                    }}
                    className="flex-1 focus:border-[#D4A828]"
                    style={{ borderColor: 'rgba(218,165,32,0.2)' }}
                    data-testid={`poll-option-input-${i}`}
                  />
                  {pollOptions.length > 2 && (
                    <button
                      type="button"
                      onClick={() => setPollOptions(pollOptions.filter((_, j) => j !== i))}
                      className="p-1.5 rounded-full hover:bg-red-50 text-[#7A8694] hover:text-red-500 transition-colors"
                      data-testid={`poll-remove-option-${i}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
              {pollOptions.length < 6 && (
                <button
                  type="button"
                  onClick={() => setPollOptions([...pollOptions, ''])}
                  className="flex items-center gap-1.5 text-xs hover:opacity-80 font-medium py-1"
                  style={{ color: '#DAA520' }}
                  data-testid="poll-add-option-btn"
                >
                  <Plus className="w-3.5 h-3.5" /> Add option
                </button>
              )}
            </div>

            <Button
              onClick={submitPoll}
              disabled={submitting || !pollQuestion.trim() || pollOptions.filter(o => o.trim()).length < 2}
              className="w-full rounded-full text-white hover:opacity-90"
              style={{ background: '#DAA520' }}
              data-testid="poll-post-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <span className="mr-2">📊</span>}
              Post Poll
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
});

export default ComposerBar;
