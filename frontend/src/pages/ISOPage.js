import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Skeleton } from '../components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Search, Plus, CheckCircle2, Loader2, Trash2, Filter } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

const ISO_TAGS = ['OG Press', 'Factory Sealed', 'Any', 'Promo'];
const FILTER_OPTIONS = ['All', 'OPEN', 'FOUND'];

const ISOPage = () => {
  const { user, token, API } = useAuth();
  const [isos, setIsos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [filter, setFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [artist, setArtist] = useState('');
  const [album, setAlbum] = useState('');
  const [pressing, setPressing] = useState('');
  const [condition, setCondition] = useState('');
  const [priceMin, setPriceMin] = useState('');
  const [priceMax, setPriceMax] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);
  const [caption, setCaption] = useState('');

  const fetchISOs = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/iso`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsos(resp.data);
    } catch {
      toast.error('Failed to load ISOs');
    } finally {
      setLoading(false);
    }
  }, [API, token]);

  useEffect(() => { fetchISOs(); }, [fetchISOs]);

  const toggleTag = (tag) => {
    setSelectedTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]);
  };

  const resetForm = () => {
    setArtist(''); setAlbum(''); setPressing(''); setCondition('');
    setPriceMin(''); setPriceMax(''); setSelectedTags([]); setCaption('');
  };

  const handleCreate = async () => {
    if (!artist.trim() || !album.trim()) { toast.error('Artist and album required'); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/composer/iso`, {
        artist: artist.trim(),
        album: album.trim(),
        pressing_notes: pressing || null,
        condition_pref: condition || null,
        tags: selectedTags.length > 0 ? selectedTags : null,
        target_price_min: priceMin ? parseFloat(priceMin) : null,
        target_price_max: priceMax ? parseFloat(priceMax) : null,
        caption: caption || null,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success('ISO posted!');
      setShowCreate(false);
      resetForm();
      fetchISOs();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarkFound = async (id) => {
    try {
      await axios.put(`${API}/iso/${id}/found`, {}, { headers: { Authorization: `Bearer ${token}` }});
      setIsos(prev => prev.map(i => i.id === id ? { ...i, status: 'FOUND' } : i));
      toast.success('Marked as found!');
    } catch { toast.error('Failed'); }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/iso/${id}`, { headers: { Authorization: `Bearer ${token}` }});
      setIsos(prev => prev.filter(i => i.id !== id));
      toast.success('ISO removed');
    } catch { toast.error('Failed'); }
  };

  const filtered = isos.filter(iso => {
    if (filter !== 'All' && iso.status !== filter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return iso.artist.toLowerCase().includes(q) || iso.album.toLowerCase().includes(q);
    }
    return true;
  });

  const openCount = isos.filter(i => i.status === 'OPEN').length;
  const foundCount = isos.filter(i => i.status === 'FOUND').length;

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-24">
        <Skeleton className="h-10 w-48 mb-6" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 w-full mb-3" />)}
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8" data-testid="iso-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading text-3xl text-vinyl-black">ISO</h1>
          <p className="text-sm text-muted-foreground">In Search Of — your vinyl wish list</p>
        </div>
        <Button onClick={() => setShowCreate(true)} className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2" data-testid="create-iso-btn">
          <Plus className="w-4 h-4" /> New ISO
        </Button>
      </div>

      {/* Stats Bar */}
      <div className="flex gap-4 mb-4">
        <div className="bg-purple-50 px-4 py-2 rounded-lg">
          <span className="text-2xl font-heading text-purple-700">{openCount}</span>
          <span className="text-xs text-purple-600 ml-1">hunting</span>
        </div>
        <div className="bg-green-50 px-4 py-2 rounded-lg">
          <span className="text-2xl font-heading text-green-700">{foundCount}</span>
          <span className="text-xs text-green-600 ml-1">found</span>
        </div>
      </div>

      {/* Search + Filter */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search your ISOs..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="pl-9 border-honey/50" data-testid="iso-search" />
        </div>
        <div className="flex gap-1">
          {FILTER_OPTIONS.map(f => (
            <Button key={f} size="sm" variant={filter === f ? 'default' : 'outline'} onClick={() => setFilter(f)}
              className={`rounded-full text-xs ${filter === f ? 'bg-vinyl-black text-white' : ''}`} data-testid={`iso-filter-${f.toLowerCase()}`}>
              {f === 'All' ? <Filter className="w-3 h-3 mr-1" /> : null} {f}
            </Button>
          ))}
        </div>
      </div>

      {/* ISO List */}
      {filtered.length === 0 ? (
        <Card className="p-8 text-center border-honey/30">
          <Search className="w-12 h-12 text-purple-300 mx-auto mb-4" />
          <h3 className="font-heading text-xl mb-2">
            {isos.length === 0 ? 'No ISOs yet' : 'No results'}
          </h3>
          <p className="text-muted-foreground text-sm">
            {isos.length === 0 ? 'Tap "New ISO" to start your vinyl hunt!' : 'Try a different filter or search term.'}
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map(iso => (
            <Card key={iso.id} className={`p-4 border-honey/30 transition-all ${iso.status === 'FOUND' ? 'opacity-60 bg-green-50/30' : 'hover:shadow-md'}`} data-testid={`iso-item-${iso.id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="font-heading text-lg">{iso.album}</h4>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                      iso.status === 'FOUND' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'
                    }`}>{iso.status}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{iso.artist}</p>

                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {(iso.tags || []).map(tag => (
                      <span key={tag} className="px-2 py-0.5 rounded-full text-xs bg-honey/20 text-honey-amber font-medium">{tag}</span>
                    ))}
                  </div>

                  <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
                    {iso.pressing_notes && <span>Press: {iso.pressing_notes}</span>}
                    {iso.condition_pref && <span>Cond: {iso.condition_pref}</span>}
                    {(iso.target_price_min || iso.target_price_max) && (
                      <span>Budget: {iso.target_price_min ? `$${iso.target_price_min}` : '?'} – {iso.target_price_max ? `$${iso.target_price_max}` : '?'}</span>
                    )}
                  </div>

                  <p className="text-xs text-muted-foreground mt-1">{formatDistanceToNow(new Date(iso.created_at), { addSuffix: true })}</p>
                </div>

                <div className="flex gap-1 shrink-0">
                  {iso.status === 'OPEN' && (
                    <Button size="sm" variant="ghost" className="text-green-600 hover:bg-green-50 h-8 px-2" onClick={() => handleMarkFound(iso.id)} data-testid={`mark-found-${iso.id}`}>
                      <CheckCircle2 className="w-4 h-4" />
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" className="text-red-400 hover:bg-red-50 h-8 px-2" onClick={() => handleDelete(iso.id)} data-testid={`delete-iso-${iso.id}`}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create ISO Modal */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="sm:max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2"><Search className="w-5 h-5 text-purple-600" /> New ISO</DialogTitle>
            <DialogDescription>What vinyl are you hunting?</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <Input placeholder="Artist *" value={artist} onChange={e => setArtist(e.target.value)} className="border-honey/50" data-testid="iso-form-artist" />
            <Input placeholder="Album *" value={album} onChange={e => setAlbum(e.target.value)} className="border-honey/50" data-testid="iso-form-album" />
            <Input placeholder="Press / year preference" value={pressing} onChange={e => setPressing(e.target.value)} className="border-honey/50" />
            <Input placeholder="Condition preference" value={condition} onChange={e => setCondition(e.target.value)} className="border-honey/50" />

            {/* Tags */}
            <div>
              <label className="text-sm font-medium mb-2 block">Tags</label>
              <div className="flex flex-wrap gap-2">
                {ISO_TAGS.map(tag => (
                  <button key={tag} onClick={() => toggleTag(tag)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                      selectedTags.includes(tag) ? 'bg-honey text-vinyl-black shadow-sm' : 'bg-honey/10 text-muted-foreground hover:bg-honey/20'
                    }`} data-testid={`iso-tag-${tag.toLowerCase().replace(/\s/g, '-')}`}>
                    {tag}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input placeholder="Min budget ($)" type="number" value={priceMin} onChange={e => setPriceMin(e.target.value)} className="border-honey/50" />
              <Input placeholder="Max budget ($)" type="number" value={priceMax} onChange={e => setPriceMax(e.target.value)} className="border-honey/50" />
            </div>
            <Textarea placeholder="Caption for The Hive (optional)" value={caption} onChange={e => setCaption(e.target.value)} className="border-honey/50 resize-none" rows={2} />
            <Button onClick={handleCreate} disabled={submitting || !artist.trim() || !album.trim()} className="w-full bg-purple-100 text-purple-800 hover:bg-purple-200 rounded-full" data-testid="iso-form-submit">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
              Post ISO
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ISOPage;
