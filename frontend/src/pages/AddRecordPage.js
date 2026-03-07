import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Skeleton } from '../components/ui/skeleton';
import { Search, Disc, Plus, Check, ArrowLeft, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { usePageTitle } from '../hooks/usePageTitle';
import RecordSearchResult from '../components/RecordSearchResult';
import AlbumArt from '../components/AlbumArt';

const AddRecordPage = () => {
  usePageTitle('Add Record');
  const { token, API } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [notes, setNotes] = useState('');
  const [adding, setAdding] = useState(false);

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
    setSearchResults([]);
    setSearchQuery('');
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
      const recordData = manualMode ? {
        title: manualTitle,
        artist: manualArtist,
        year: manualYear ? parseInt(manualYear) : null,
        notes: notes || null
      } : {
        discogs_id: selectedRecord.discogs_id,
        title: selectedRecord.title,
        artist: selectedRecord.artist,
        cover_url: selectedRecord.cover_url,
        year: selectedRecord.year,
        format: selectedRecord.format,
        notes: notes || null
      };

      await axios.post(`${API}/records`, recordData, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 15000,
      });

      toast.success('record added to your collection.');
      trackEvent('collection_record_added');
      navigate('/collection');
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
    <div className="max-w-2xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8">
      <Button 
        variant="ghost" 
        onClick={() => navigate(-1)}
        className="mb-4 gap-2"
        data-testid="back-btn"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>

      <h1 className="font-heading text-3xl text-vinyl-black mb-6">Add Record</h1>

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
              className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
              data-testid="confirm-add-btn"
            >
              {adding ? 'Adding...' : (
                <>
                  <Check className="w-4 h-4" />
                  Add to Collection
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
                className="flex-1 bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
                data-testid="manual-add-btn"
              >
                {adding ? 'Adding...' : 'Add Record'}
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
  );
};

export default AddRecordPage;
