import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Skeleton } from '../components/ui/skeleton';
import { Search, Disc, Plus, Check, ArrowLeft, Loader2, Sparkles, Cloud } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { usePageTitle } from '../hooks/usePageTitle';
import RecordSearchResult from '../components/RecordSearchResult';
import AlbumArt from '../components/AlbumArt';
import DuplicateConfirmationModal from '../components/DuplicateConfirmationModal';

const AddRecordPage = () => {
  usePageTitle('Add Record');
  const { token, API } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode') || 'reality'; // 'reality' or 'dreaming'
  const isDreaming = mode === 'dreaming';

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [notes, setNotes] = useState('');
  const [colorVariant, setColorVariant] = useState('');
  const [editionNumber, setEditionNumber] = useState('');
  const [adding, setAdding] = useState(false);

  // Duplicate detection state
  const [dupModal, setDupModal] = useState({ open: false, copyCount: 0, title: '' });
  const pendingAddRef = useRef(null);

  // Manual entry state
  const [manualMode, setManualMode] = useState(false);
  const [manualTitle, setManualTitle] = useState('');
  const [manualArtist, setManualArtist] = useState('');
  const [manualYear, setManualYear] = useState('');

  const searchTimerRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    if (abortRef.current) abortRef.current.abort();
    if (query.length < 2) { setSearchResults([]); setSearching(false); return; }
    setSearching(true);
    searchTimerRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const response = await axios.get(`${API}/discogs/search`, {
          params: { q: query }, headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        setSearchResults(response.data);
      } catch (err) {
        if (!axios.isCancel(err)) { toast.error('Search failed. Try again.'); setSearchResults([]); }
      } finally {
        if (!controller.signal.aborted) setSearching(false);
      }
    }, 300);
  };

  const handleSelectRecord = (record) => {
    setSelectedRecord(record);
    setColorVariant(record.color_variant || '');
    setSearchResults([]);
    setSearchQuery('');
  };

  const executeAdd = async (recordData) => {
    await axios.post(`${API}/records`, recordData, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 15000,
    });
    toast.success('Added to Collection. Your Gold Standard just grew.');
    trackEvent('collection_record_added');
    navigate('/collection');
  };

  const handleDupConfirm = async () => {
    setDupModal({ open: false, copyCount: 0, title: '' });
    if (!pendingAddRef.current) return;
    setAdding(true);
    try {
      // Generate a unique instance_id for the new copy
      const data = { ...pendingAddRef.current, instance_id: Date.now() };
      await executeAdd(data);
    } catch (error) {
      console.error('Add error:', error);
      toast.error(error.response?.data?.detail || "couldn't add that record. please try again.");
    } finally {
      setAdding(false);
      pendingAddRef.current = null;
    }
  };

  const handleDupCancel = () => {
    setDupModal({ open: false, copyCount: 0, title: '' });
    pendingAddRef.current = null;
    setAdding(false);
  };

  const handleAddRecord = async () => {
    if (!selectedRecord && !manualMode) {
      toast.error('Please select or enter a record');
      return;
    }

    if (manualMode && (!manualTitle || !manualArtist)) {
      toast.error('Please enter title and artist');
      return;
    }

    setAdding(true);
    try {
      if (isDreaming) {
        // Add to Dreaming (WISHLIST ISO) — no duplicate check needed
        const isoData = manualMode ? {
          artist: manualArtist,
          album: manualTitle,
          year: manualYear ? parseInt(manualYear) : null,
          color_variant: colorVariant || null,
          notes: notes || null,
          preferred_number: editionNumber ? parseInt(editionNumber) : null,
        } : {
          discogs_id: selectedRecord.discogs_id,
          artist: selectedRecord.artist,
          album: selectedRecord.title,
          cover_url: selectedRecord.cover_url,
          year: selectedRecord.year,
          color_variant: colorVariant || selectedRecord.color_variant || null,
          notes: notes || null,
          preferred_number: editionNumber ? parseInt(editionNumber) : null,
        };
        await axios.post(`${API}/iso`, { ...isoData, status: 'WISHLIST', priority: 'LOW' }, {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 15000,
        });
        toast.success('Added to your Dream List. Keep building that millionaire mood board.');
        trackEvent('dreaming_record_added');
        navigate('/collection?tab=wishlist');
      } else {
        // Add to Collection — check for duplicates first
        const recordData = manualMode ? {
          title: manualTitle,
          artist: manualArtist,
          year: manualYear ? parseInt(manualYear) : null,
          notes: notes || null,
          color_variant: colorVariant || null,
          edition_number: editionNumber ? parseInt(editionNumber) : null,
        } : {
          discogs_id: selectedRecord.discogs_id,
          title: selectedRecord.title,
          artist: selectedRecord.artist,
          cover_url: selectedRecord.cover_url,
          year: selectedRecord.year,
          format: selectedRecord.format,
          notes: notes || null,
          color_variant: colorVariant || selectedRecord.color_variant || null,
          edition_number: editionNumber ? parseInt(editionNumber) : null,
        };

        // Duplicate detection: check ownership before adding
        const checkParams = recordData.discogs_id
          ? { discogs_id: recordData.discogs_id }
          : { artist: recordData.artist, title: recordData.title };
        const ownerCheck = await axios.get(`${API}/records/check-ownership`, {
          params: checkParams,
          headers: { Authorization: `Bearer ${token}` },
        });

        if (ownerCheck.data.in_collection) {
          // Show duplicate modal — store pending data
          pendingAddRef.current = recordData;
          setDupModal({
            open: true,
            copyCount: ownerCheck.data.copy_count || 1,
            title: recordData.title,
          });
          return; // Don't setAdding(false) — modal handles it
        }

        await executeAdd(recordData);
      }
    } catch (error) {
      console.error('Add error:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error("couldn't add that record. please try again.");
      }
    } finally {
      setAdding(false);
    }
  };

  return (
    <>
    <div className="max-w-2xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-24 md:pb-8">
      <Button 
        variant="ghost" 
        onClick={() => navigate(-1)}
        className="mb-4 gap-2"
        data-testid="back-btn"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>

      <div className="flex items-center gap-3 mb-6">
        {isDreaming ? <Cloud className="w-6 h-6 text-stone-400" /> : <Sparkles className="w-6 h-6 text-honey-amber" />}
        <div>
          <h1 className="font-heading text-3xl text-vinyl-black">{isDreaming ? 'Add to Dream List' : 'Add to Collection'}</h1>
          <p className="text-sm text-muted-foreground font-serif italic">{isDreaming ? 'The millionaire mood board grows.' : 'Your Gold Standard just got richer.'}</p>
        </div>
      </div>

      {selectedRecord ? (
        // Selected record preview
        <Card className="p-6 border-honey/30 mb-6">
          <div className="flex gap-4">
            {selectedRecord.cover_url ? (
              <AlbumArt 
                src={selectedRecord.cover_url} 
                alt={selectedRecord.title}
                className="w-32 h-32 rounded-lg object-cover shadow-md"
              />
            ) : (
              <div className="w-32 h-32 rounded-lg bg-vinyl-black flex items-center justify-center">
                <Disc className="w-12 h-12 text-honey" />
              </div>
            )}
            <div className="flex-1">
              <h3 className="font-heading text-xl">{selectedRecord.title}</h3>
              <p className="text-muted-foreground">{selectedRecord.artist}</p>
              {selectedRecord.year && <p className="text-sm text-muted-foreground mt-1">{selectedRecord.year}</p>}
              {selectedRecord.format && (
                <span className="inline-block mt-2 text-xs bg-honey/20 px-2 py-1 rounded-full">
                  {selectedRecord.format}
                </span>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedRecord(null)}
              className="text-muted-foreground"
            >
              Change
            </Button>
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <Label htmlFor="variant">Color Variant (optional)</Label>
              <Input
                id="variant"
                placeholder="e.g. Blue Marble, 180g Black, Limited Edition Clear..."
                value={colorVariant}
                onChange={(e) => setColorVariant(e.target.value.slice(0, 80))}
                className="mt-2 border-honey/50"
                data-testid="record-variant"
              />
              <p className="text-[10px] text-muted-foreground mt-1">The specific pressing or color of your vinyl</p>
            </div>
            <div>
              <Label htmlFor="edition">{isDreaming ? 'Preferred Edition Number (optional)' : 'Edition Number (optional)'}</Label>
              <Input
                id="edition"
                type="number"
                min="1"
                placeholder={isDreaming ? "e.g. 1 (your lucky number)" : "e.g. 42 of 500"}
                value={editionNumber}
                onChange={(e) => setEditionNumber(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="mt-2 border-honey/50"
                data-testid="record-edition-number"
              />
              <p className="text-[10px] text-muted-foreground mt-1">{isDreaming ? 'The specific number you\'re hunting for' : 'For numbered limited editions — displays as "No. 42" on your card'}</p>
            </div>
            <div>
              <Label htmlFor="notes">Notes (optional)</Label>
              <Textarea
                id="notes"
                placeholder="Add notes about this record..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-2 border-honey/50"
                data-testid="record-notes"
              />
            </div>

            <Button
              onClick={handleAddRecord}
              disabled={adding}
              className={`w-full rounded-full gap-2 ${isDreaming ? 'bg-stone-200 text-stone-700 hover:bg-stone-300' : 'bg-honey text-vinyl-black hover:bg-honey-amber'}`}
              data-testid="confirm-add-btn"
            >
              {adding ? 'Adding...' : (
                <>
                  {isDreaming ? <Cloud className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                  {isDreaming ? 'Save to Dreams' : 'Confirm to Collection'}
                </>
              )}
            </Button>
          </div>
        </Card>
      ) : manualMode ? (
        // Manual entry form
        <Card className="p-6 border-honey/30 mb-6">
          <h3 className="font-heading text-lg mb-4">Enter Record Details</h3>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Album Title *</Label>
              <Input
                id="title"
                placeholder="Album title"
                value={manualTitle}
                onChange={(e) => setManualTitle(e.target.value)}
                className="mt-2 border-honey/50"
                data-testid="manual-title"
              />
            </div>
            <div>
              <Label htmlFor="artist">Artist *</Label>
              <Input
                id="artist"
                placeholder="Artist name"
                value={manualArtist}
                onChange={(e) => setManualArtist(e.target.value)}
                className="mt-2 border-honey/50"
                data-testid="manual-artist"
              />
            </div>
            <div>
              <Label htmlFor="year">Year (optional)</Label>
              <Input
                id="year"
                type="number"
                placeholder="Release year"
                value={manualYear}
                onChange={(e) => setManualYear(e.target.value)}
                className="mt-2 border-honey/50"
                data-testid="manual-year"
              />
            </div>
            <div>
              <Label htmlFor="variant-manual">Color Variant (optional)</Label>
              <Input
                id="variant-manual"
                placeholder="e.g. Blue Marble, 180g Black..."
                value={colorVariant}
                onChange={(e) => setColorVariant(e.target.value.slice(0, 80))}
                className="mt-2 border-honey/50"
                data-testid="manual-variant"
              />
            </div>
            <div>
              <Label htmlFor="edition-manual">{isDreaming ? 'Preferred Edition Number (optional)' : 'Edition Number (optional)'}</Label>
              <Input
                id="edition-manual"
                type="number"
                min="1"
                placeholder={isDreaming ? "e.g. 1 (your lucky number)" : "e.g. 42 of 500"}
                value={editionNumber}
                onChange={(e) => setEditionNumber(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="mt-2 border-honey/50"
                data-testid="manual-edition-number"
              />
            </div>
            <div>
              <Label htmlFor="notes">Notes (optional)</Label>
              <Textarea
                id="notes"
                placeholder="Add notes about this record..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-2 border-honey/50"
              />
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setManualMode(false)}
                className="flex-1"
              >
                Back to Search
              </Button>
              <Button
                onClick={handleAddRecord}
                disabled={adding || !manualTitle || !manualArtist}
                className={`flex-1 rounded-full gap-2 ${isDreaming ? 'bg-stone-200 text-stone-700 hover:bg-stone-300' : 'bg-honey text-vinyl-black hover:bg-honey-amber'}`}
                data-testid="manual-add-btn"
              >
                {adding ? 'Adding...' : isDreaming ? 'Save to Dreams' : 'Confirm to Collection'}
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        // Search interface
        <>
          <Card className="p-6 border-honey/30 mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                placeholder="Search by artist or album name..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="pl-10 h-12 text-lg border-honey/50"
                data-testid="discogs-search"
              />
              {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin text-amber-400" />}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Search powered by Discogs database
            </p>
          </Card>

          {/* Search Results */}
          {searching && searchResults.length === 0 ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <Card key={i} className="p-4 flex gap-4">
                  <Skeleton className="w-16 h-16 rounded" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </Card>
              ))}
            </div>
          ) : searchResults.length > 0 ? (
            <div className="space-y-1 border border-honey/30 rounded-lg p-2 bg-white">
              {searchResults.map(result => (
                <RecordSearchResult
                  key={result.discogs_id}
                  record={result}
                  onClick={() => handleSelectRecord(result)}
                  size="md"
                  testId={`search-result-${result.discogs_id}`}
                  actions={<Plus className="w-5 h-5 text-honey" />}
                />
              ))}
            </div>
          ) : searchQuery.length >= 2 && !searching ? (
            <Card className="p-6 text-center border-honey/30">
              <p className="text-muted-foreground mb-4">No results found for "{searchQuery}"</p>
              <Button 
                variant="outline" 
                onClick={() => setManualMode(true)}
                className="gap-2"
                data-testid="manual-entry-btn"
              >
                <Plus className="w-4 h-4" />
                Add Manually
              </Button>
            </Card>
          ) : null}

          {/* Manual entry option */}
          {searchQuery.length < 2 && (
            <div className="text-center mt-8">
              <p className="text-muted-foreground mb-3">Can't find your record?</p>
              <Button 
                variant="outline" 
                onClick={() => setManualMode(true)}
                className="gap-2"
                data-testid="manual-entry-btn"
              >
                <Plus className="w-4 h-4" />
                Add Manually
              </Button>
            </div>
          )}
        </>
      )}
    </div>

    <DuplicateConfirmationModal
      open={dupModal.open}
      copyCount={dupModal.copyCount}
      recordTitle={dupModal.title}
      onConfirm={handleDupConfirm}
      onCancel={handleDupCancel}
    />
    </>
  );
};

export default AddRecordPage;
