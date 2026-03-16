import React, { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Skeleton } from '../components/ui/skeleton';
import { ArrowLeft, Search, Disc, Plus, X, Package, Share2 } from 'lucide-react';
import { toast } from 'sonner';
import debounce from 'lodash.debounce';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';

const CreateHaulPage = () => {
  usePageTitle('New Haul');
  const { token, API } = useAuth();
  const navigate = useNavigate();
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [items, setItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [creating, setCreating] = useState(false);

  const searchDiscogs = async (query) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const response = await axios.get(`${API}/discogs/search`, {
        params: { q: query },
        headers: { Authorization: `Bearer ${token}` }
      });
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setSearching(false);
    }
  };

  const debouncedSearch = useCallback(
    debounce((query) => searchDiscogs(query), 500),
    [token]
  );

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    debouncedSearch(query);
  };

  const addItem = (record) => {
    if (items.find(item => item.discogs_id === record.discogs_id)) {
      toast.error('Record already added to haul');
      return;
    }
    // Auto-detect format from Discogs data
    const fmt = (record.format || '').toLowerCase();
    let format = 'Vinyl';
    if (fmt.includes('cd')) format = 'CD';
    else if (fmt.includes('cassette')) format = 'Cassette';
    setItems([...items, { ...record, itemFormat: format }]);
    setSearchQuery('');
    setSearchResults([]);
    toast.success(`Added ${record.title}`);
  };

  const removeItem = (discogsId) => {
    setItems(items.filter(item => item.discogs_id !== discogsId));
  };

  const updateItemFormat = (discogsId, format) => {
    setItems(items.map(item => item.discogs_id === discogsId ? { ...item, itemFormat: format } : item));
  };

  const handleCreateHaul = async () => {
    if (!title.trim()) {
      toast.error('Please enter a title for your haul');
      return;
    }

    if (items.length === 0) {
      toast.error('Please add at least one record to your haul');
      return;
    }

    setCreating(true);
    try {
      const haulData = {
        title: title.trim(),
        description: description.trim() || null,
        items: items.map(item => ({
          discogs_id: item.discogs_id,
          title: item.title,
          artist: item.artist,
          cover_url: item.cover_url,
          year: item.year,
          format: item.itemFormat || 'Vinyl',
        }))
      };

      const response = await axios.post(`${API}/hauls`, haulData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(`Haul created with ${items.length} records!`);
      navigate('/collection');
    } catch (error) {
      console.error('Create haul error:', error);
      toast.error('Failed to create haul');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-24 md:pb-8">
      <Button 
        variant="ghost" 
        onClick={() => navigate(-1)}
        className="mb-6 gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>

      <div className="flex items-center gap-3 mb-6">
        <Package className="w-8 h-8 text-honey" />
        <h1 className="font-heading text-3xl text-vinyl-black">Create Haul</h1>
      </div>

      {/* Haul Details */}
      <Card className="p-6 border-honey/30 mb-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="title">Haul Title *</Label>
            <Input
              id="title"
              placeholder="e.g., Record Store Day Finds, Estate Sale Haul..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-2 border-honey/50"
              data-testid="haul-title"
            />
          </div>
          <div>
            <Label htmlFor="description">Description (optional)</Label>
            <Textarea
              id="description"
              placeholder="Tell us about this haul..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-2 border-honey/50"
              rows={3}
              data-testid="haul-description"
            />
          </div>
        </div>
      </Card>

      {/* Added Items */}
      {items.length > 0 && (
        <Card className="p-6 border-honey/30 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading text-lg">Records in this haul ({items.length})</h3>
          </div>
          <div className="space-y-3">
            {items.map(item => (
              <div 
                key={item.discogs_id}
                className="flex items-center gap-3 p-3 bg-honey/10 rounded-lg"
              >
                {item.cover_url ? (
                  <AlbumArt src={item.cover_url} alt={item.title} className="w-12 h-12 rounded object-cover" isUnofficial={item.is_unofficial} />
                ) : (
                  <div className="w-12 h-12 rounded bg-vinyl-black flex items-center justify-center">
                    <Disc className="w-5 h-5 text-honey" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-sm truncate">{item.title}</h4>
                  <p className="text-xs text-muted-foreground truncate">{item.artist}</p>
                  {/* Format pills */}
                  <div className="flex items-center gap-1 mt-1">
                    {['Vinyl', 'CD', 'Cassette'].map(fmt => (
                      <button
                        key={fmt}
                        type="button"
                        onClick={() => updateItemFormat(item.discogs_id, fmt)}
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium transition-all border ${
                          (item.itemFormat || 'Vinyl') === fmt
                            ? 'bg-vinyl-black text-white border-vinyl-black'
                            : 'bg-white text-stone-400 border-stone-200 hover:border-stone-300'
                        }`}
                        data-testid={`haul-format-${item.discogs_id}-${fmt.toLowerCase()}`}
                      >
                        {fmt}
                      </button>
                    ))}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeItem(item.discogs_id)}
                  className="text-red-500 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Search to Add */}
      <Card className="p-6 border-honey/30 mb-6">
        <h3 className="font-heading text-lg mb-4">Add Records</h3>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search for records to add..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="pl-9 border-honey/50"
            data-testid="haul-search"
          />
        </div>

        {/* Search Results */}
        {searching ? (
          <div className="mt-4 space-y-2">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : searchResults.length > 0 ? (
          <div className="mt-4 space-y-2 max-h-64 overflow-y-auto">
            {searchResults.map(result => (
              <div 
                key={result.discogs_id}
                className="flex items-center gap-3 p-3 rounded-lg border border-honey/30 hover:border-honey hover:bg-honey/5 cursor-pointer transition-colors"
                onClick={() => addItem(result)}
              >
                {result.cover_url ? (
                  <AlbumArt src={result.cover_url} alt={result.title} className="w-12 h-12 rounded object-cover" isUnofficial={result.is_unofficial} />
                ) : (
                  <div className="w-12 h-12 rounded bg-vinyl-black flex items-center justify-center">
                    <Disc className="w-5 h-5 text-honey" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-sm truncate">{result.title}</h4>
                  <p className="text-xs text-muted-foreground truncate">{result.artist}</p>
                </div>
                <Plus className="w-5 h-5 text-honey" />
              </div>
            ))}
          </div>
        ) : null}
      </Card>

      {/* Create Button */}
      <Button
        onClick={handleCreateHaul}
        disabled={creating || items.length === 0 || !title.trim()}
        className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2 h-12"
        data-testid="create-haul-btn"
      >
        <Package className="w-5 h-5" />
        {creating ? 'Creating Haul...' : `Create Haul with ${items.length} Record${items.length !== 1 ? 's' : ''}`}
      </Button>
    </div>
  );
};

export default CreateHaulPage;
