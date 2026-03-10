import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Disc, Plus, Search, Play, Trash2, MoreVertical, ArrowUpDown, Gem, DollarSign, TrendingUp, RefreshCw, Heart, ArrowRight, ShoppingBag, Cloud, Sparkles, CheckSquare, Square, ListChecks } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import DiscogsImport from '../components/DiscogsImport';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import { VariantTag } from '../components/PostCards';
import SEOHead from '../components/SEOHead';

// Counting animation hook
const useCountUp = (target, duration = 1400, enabled = true) => {
  const [value, setValue] = useState(0);
  const prevTarget = useRef(0);
  useEffect(() => {
    if (!enabled || target <= 0) { setValue(target); prevTarget.current = target; return; }
    const start = prevTarget.current;
    prevTarget.current = target;
    const diff = target - start;
    if (diff === 0) return;
    const startTime = performance.now();
    let raf;
    const step = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      setValue(start + diff * eased);
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration, enabled]);
  return value;
};

const SORT_OPTIONS = [
  { value: 'artist_asc', label: 'Artist A → Z' },
  { value: 'artist_desc', label: 'Artist Z → A' },
  { value: 'title_asc', label: 'Album Title A → Z' },
  { value: 'title_desc', label: 'Album Title Z → A' },
  { value: 'newest', label: 'Newest Added' },
  { value: 'oldest', label: 'Oldest Added' },
  { value: 'most_spins', label: 'Most Spins' },
  { value: 'least_spins', label: 'Least Spins' },
  { value: 'recently_spun', label: 'Recently Spun' },
  { value: 'never_spun', label: 'No Logged Spins' },
  { value: 'highest_value', label: 'Highest Value' },
];

const CollectionPage = () => {
  usePageTitle('Your Collection');
  const { user, token, API } = useAuth();
  const [records, setRecords] = useState([]);
  const [spins, setSpins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [spinningRecordId, setSpinningRecordId] = useState(null);
  const [collectionValue, setCollectionValue] = useState(null);
  const [hiddenGems, setHiddenGems] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [valueMap, setValueMap] = useState({});
  const searchParamsCollection = new URLSearchParams(window.location.search);
  const [collectionTab, setCollectionTab] = useState(searchParamsCollection.get('tab') === 'wishlist' ? 'wishlist' : 'owned');
  const [wishlistItems, setWishlistItems] = useState([]);
  const [wishlistValue, setWishlistValue] = useState(null);
  const [dreamSubtractMsg, setDreamSubtractMsg] = useState(null);
  const [countKey, setCountKey] = useState(0);
  // Confirmation dialog for "Collection Cleanse" moves
  const [cleanseTarget, setCleanseTarget] = useState(null); // { id, title, type: 'dreaming'|'hunt' }
  // Multi-select mode
  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const navigate = useNavigate();

  // Trigger counting animation when switching to dreaming tab
  const handleTabChange = (val) => {
    setCollectionTab(val);
    if (val === 'wishlist') setCountKey(k => k + 1);
  };

  const fetchData = useCallback(async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [recordsRes, spinsRes, valueRes, gemsRes, valMapRes] = await Promise.all([
        axios.get(`${API}/records`, { headers }),
        axios.get(`${API}/spins`, { headers }),
        axios.get(`${API}/valuation/collection`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/valuation/hidden-gems`, { headers }).catch(() => ({ data: [] })),
        axios.get(`${API}/valuation/record-values`, { headers }).catch(() => ({ data: {} })),
      ]);
      setRecords(recordsRes.data);
      setSpins(spinsRes.data);
      setCollectionValue(valueRes.data);
      setHiddenGems(gemsRes.data || []);
      setValueMap(valMapRes.data || {});
      // Fetch wishlist (WISHLIST ISO items)
      Promise.all([
        axios.get(`${API}/iso`, { headers }).then(r => setWishlistItems((r.data || []).filter(i => i.status === 'WISHLIST'))),
        axios.get(`${API}/valuation/wishlist`, { headers }).then(r => setWishlistValue(r.data)),
      ]).catch(() => {});
    } catch (error) {
      console.error('Failed to fetch records:', error);
      toast.error('something went wrong loading your collection.');
    } finally {
      setLoading(false);
    }
  }, [API, token]);

  const handleRefreshValues = async () => {
    setRefreshing(true);
    try {
      const resp = await axios.post(`${API}/valuation/refresh`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(resp.data.message);
      // Poll after a delay to show new values
      setTimeout(fetchData, 5000);
    } catch { toast.error('could not refresh values. try again.'); }
    finally { setRefreshing(false); }
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleLogSpin = async (record) => {
    setSpinningRecordId(record.id);
    try {
      await axios.post(`${API}/spins`, 
        { record_id: record.id },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      toast.success(`now spinning: ${record.title}`);
      fetchData(); // Refresh to update spin count
    } catch (error) {
      console.error('Failed to log spin:', error);
      toast.error('could not log spin. try again.');
    } finally {
      setSpinningRecordId(null);
    }
  };

  const handleDeleteRecord = async (recordId) => {
    if (!confirm('Are you sure you want to remove this record from your collection?')) return;

    try {
      await axios.delete(`${API}/records/${recordId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecords(records.filter(r => r.id !== recordId));
      toast.success('record removed.');
    } catch (error) {
      console.error('Failed to delete record:', error);
      toast.error('could not remove record. try again.');
    }
  };

  // Confirmation-based moves (Collection Cleanse)
  const requestMoveToDreaming = (recordId) => {
    const rec = records.find(r => r.id === recordId);
    setCleanseTarget({ id: recordId, title: rec?.title || 'this record', type: 'dreaming' });
  };
  const requestMoveToHunt = (recordId) => {
    const rec = records.find(r => r.id === recordId);
    setCleanseTarget({ id: recordId, title: rec?.title || 'this record', type: 'hunt' });
  };

  const handleConfirmCleanse = async () => {
    if (!cleanseTarget) return;
    const { id, type } = cleanseTarget;
    setCleanseTarget(null);
    try {
      if (type === 'dreaming') {
        const res = await axios.post(`${API}/records/${id}/move-to-wishlist`, {}, { headers: { Authorization: `Bearer ${token}` }});
        setRecords(prev => prev.filter(r => r.id !== id));
        // Optimistically update Reality value
        const itemVal = valueMap[id] || 0;
        if (itemVal > 0 && collectionValue) {
          setCollectionValue(prev => prev ? { ...prev, total_value: Math.max(0, prev.total_value - itemVal) } : prev);
          setWishlistValue(prev => prev ? { ...prev, total_value: prev.total_value + itemVal } : prev);
        }
        toast.success(res.data.message || 'moved to dreaming.');
      } else {
        const res = await axios.post(`${API}/records/${id}/move-to-iso`, {}, { headers: { Authorization: `Bearer ${token}` }});
        setRecords(prev => prev.filter(r => r.id !== id));
        toast.success(res.data.message || 'back on the hunt.');
      }
    } catch { toast.error('could not move record.'); }
  };

  // Multi-select helpers
  const toggleSelect = (id) => setSelectedIds(prev => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });
  const exitSelectMode = () => { setSelectMode(false); setSelectedIds(new Set()); };
  const selectAll = () => setSelectedIds(new Set(sortedAndFilteredRecords.map(r => r.id)));

  const handleBulkDreamify = async () => {
    if (selectedIds.size === 0) return;
    try {
      const res = await axios.post(`${API}/records/bulk-move-to-wishlist`, { record_ids: [...selectedIds] }, { headers: { Authorization: `Bearer ${token}` }});
      setRecords(prev => prev.filter(r => !selectedIds.has(r.id)));
      exitSelectMode();
      toast.success(`Collection Refined. Your shelf is looking lighter.`);
    } catch { toast.error('bulk move failed.'); }
  };
  const handleBulkHuntify = async () => {
    if (selectedIds.size === 0) return;
    try {
      const res = await axios.post(`${API}/records/bulk-move-to-iso`, { record_ids: [...selectedIds] }, { headers: { Authorization: `Bearer ${token}` }});
      setRecords(prev => prev.filter(r => !selectedIds.has(r.id)));
      exitSelectMode();
      toast.success(`Collection Refined. Your shelf is looking lighter.`);
    } catch { toast.error('bulk move failed.'); }
  };

  const handleWishlistToISO = async (isoId) => {
    try {
      const item = wishlistItems.find(i => i.id === isoId);
      const res = await axios.put(`${API}/iso/${isoId}/promote`, {}, { headers: { Authorization: `Bearer ${token}` }});
      setWishlistItems(prev => prev.filter(i => i.id !== isoId));
      toast.success(res.data.message || `${item?.album || 'Record'} is now on the hunt.`);
      // Show subtraction message and update dream debt counter
      if (item?.discogs_id && wishlistValue) {
        // Fetch this item's value from the valuation cache
        try {
          const valRes = await axios.get(`${API}/valuation/record-value/${item.discogs_id}`, { headers: { Authorization: `Bearer ${token}` } });
          const itemVal = valRes.data?.median_value || 0;
          if (itemVal > 0) {
            setDreamSubtractMsg(`Subtracting $${itemVal.toLocaleString('en-US', { minimumFractionDigits: 2 })} from your Value of ISOs... and adding it to your Collection.`);
            setWishlistValue(prev => prev ? { ...prev, total_value: Math.max(0, prev.total_value - itemVal) } : prev);
            setTimeout(() => setDreamSubtractMsg(null), 4000);
          }
        } catch {
          // Silently proceed; value subtraction is cosmetic
        }
      }
    } catch { toast.error('could not promote to wantlist.'); }
  };

  const handleDeleteWishlistItem = async (isoId) => {
    try {
      await axios.delete(`${API}/iso/${isoId}`, { headers: { Authorization: `Bearer ${token}` }});
      setWishlistItems(prev => prev.filter(i => i.id !== isoId));
      toast.success('removed from wishlist.');
    } catch { toast.error('could not remove.'); }
  };

  // Get the most recent spin date for each record
  const getLastSpinDate = (recordId) => {
    const recordSpins = spins.filter(s => s.record_id === recordId);
    if (recordSpins.length === 0) return null;
    return new Date(Math.max(...recordSpins.map(s => new Date(s.created_at))));
  };

  // Filter and sort records
  const sortedAndFilteredRecords = useMemo(() => {
    // First filter by search query
    let filtered = records.filter(record => 
      record.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      record.artist.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Then sort
    switch (sortBy) {
      case 'artist_asc':
        filtered.sort((a, b) => a.artist.localeCompare(b.artist));
        break;
      case 'artist_desc':
        filtered.sort((a, b) => b.artist.localeCompare(a.artist));
        break;
      case 'title_asc':
        filtered.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case 'title_desc':
        filtered.sort((a, b) => b.title.localeCompare(a.title));
        break;
      case 'newest':
        filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        break;
      case 'oldest':
        filtered.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        break;
      case 'most_spins':
        filtered.sort((a, b) => (b.spin_count || 0) - (a.spin_count || 0));
        break;
      case 'least_spins':
        filtered.sort((a, b) => (a.spin_count || 0) - (b.spin_count || 0));
        break;
      case 'recently_spun':
        filtered.sort((a, b) => {
          const aDate = getLastSpinDate(a.id);
          const bDate = getLastSpinDate(b.id);
          if (!aDate && !bDate) return 0;
          if (!aDate) return 1;
          if (!bDate) return -1;
          return bDate - aDate;
        });
        break;
      case 'never_spun':
        filtered.sort((a, b) => {
          const aSpins = a.spin_count || 0;
          const bSpins = b.spin_count || 0;
          if (aSpins === 0 && bSpins === 0) return a.title.localeCompare(b.title);
          if (aSpins === 0) return -1;
          if (bSpins === 0) return 1;
          return aSpins - bSpins;
        });
        break;
      case 'highest_value':
        filtered.sort((a, b) => (valueMap[b.id] || 0) - (valueMap[a.id] || 0));
        break;
      default:
        break;
    }

    return filtered;
  }, [records, searchQuery, sortBy, spins, valueMap]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8 pt-16 md:pt-24">
        <h1 className="font-heading text-3xl mb-6">My Collection</h1>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Card key={i} className="aspect-square">
              <Skeleton className="w-full h-full" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8">
      <SEOHead
        title={`My Collection — ${records.length} Records`}
        description={`Your vinyl collection on The Honey Groove. ${records.length} records owned, ${wishlistItems.length} on the wishlist.`}
        url="/collection"
        noIndex
      />
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="font-heading text-3xl text-vinyl-black">My Collection</h1>
          <p className="text-muted-foreground">{records.length} owned · {wishlistItems.length} dreaming</p>
        </div>
        <Link to={`/add-record?mode=${collectionTab === 'wishlist' ? 'dreaming' : 'reality'}`}>
          <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2" data-testid="add-record-btn">
            <Plus className="w-4 h-4" />
            {collectionTab === 'wishlist' ? 'Add to Dreaming' : 'Add to Collection'}
          </Button>
        </Link>
      </div>

      <Tabs value={collectionTab} onValueChange={handleTabChange}>
        {/* Collection Value Toggle */}
        {collectionValue && collectionValue.total_value > 0 && wishlistValue && wishlistValue.total_value > 0 && (
          <div className="flex items-center justify-center gap-4 mb-4 p-3 rounded-xl border border-honey/20 bg-gradient-to-r from-honey/5 to-stone-50" data-testid="reality-check-toggle">
            <button
              onClick={() => handleTabChange('owned')}
              className={`text-center transition-all px-4 py-1.5 rounded-full text-sm font-medium ${collectionTab === 'owned' ? 'bg-honey/20 text-vinyl-black' : 'text-stone-400 hover:text-stone-600'}`}
              data-testid="toggle-reality">
              <span className="block font-heading text-lg">${collectionValue.total_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              <span className="text-[10px] uppercase tracking-wide">Collection Value</span>
            </button>
            <span className="text-stone-300 text-xs">vs</span>
            <button
              onClick={() => handleTabChange('wishlist')}
              className={`text-center transition-all px-4 py-1.5 rounded-full text-sm font-medium ${collectionTab === 'wishlist' ? 'bg-stone-100 text-vinyl-black' : 'text-stone-400 hover:text-stone-600'}`}
              data-testid="toggle-dreaming">
              <span className="block font-heading text-lg">${wishlistValue.total_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              <span className="text-[10px] uppercase tracking-wide">Value of ISOs</span>
            </button>
          </div>
        )}

        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-2">
          <TabsTrigger value="owned" className="data-[state=active]:bg-honey text-sm gap-1.5" data-testid="tab-owned">
            <Sparkles className="w-3.5 h-3.5" /> Collection ({records.length})
          </TabsTrigger>
          <TabsTrigger value="wishlist" className="data-[state=active]:bg-honey text-sm gap-1.5" data-testid="tab-wishlist">
            <Cloud className="w-3.5 h-3.5" /> Dreaming ({wishlistItems.length})
          </TabsTrigger>
        </TabsList>

        {/* ====== COLLECTION (OWNED) TAB ====== */}
        <TabsContent value="owned">
          {/* Collection Tagline */}
          <div className="mb-4 px-1 transition-opacity duration-500" data-testid="reality-header">
            <p className="font-heading text-lg">
              <span style={{ background: 'linear-gradient(90deg, #C8861A, #E8A820, #D4A017)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>The Gold Standard{collectionValue && collectionValue.total_value > 0 ? `: $${collectionValue.total_value.toLocaleString(undefined, { maximumFractionDigits: 0 })} worth of wax on your shelf.` : '.'}</span>
            </p>
            <p className="text-sm text-stone-500 font-serif italic">Your collection, curated and captured in the light.</p>
          </div>

          {/* Collection Value Banner */}
          {collectionValue && collectionValue.valued_count > 0 && (
            <Card className="p-4 mb-5 border-honey/30 bg-gradient-to-r from-honey/5 to-honey/15" data-testid="collection-value-banner">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-honey/20 flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-honey-amber" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">estimated value</p>
                    <p className="font-heading text-2xl text-vinyl-black" data-testid="collection-total-value">
                      ${collectionValue.total_value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                    </p>
                    <p className="text-[10px] text-muted-foreground">based on Discogs market data · {collectionValue.valued_count} of {collectionValue.total_count} records valued</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={handleRefreshValues} disabled={refreshing}
                  className="text-xs text-honey-amber hover:bg-honey/10 rounded-full" data-testid="refresh-values-btn">
                  <RefreshCw className={`w-3.5 h-3.5 mr-1 ${refreshing ? 'animate-spin' : ''}`} /> {refreshing ? 'Refreshing...' : 'Refresh'}
                </Button>
              </div>
            </Card>
          )}

          {/* Hidden Gems */}
          {hiddenGems.length > 0 && (
            <div className="mb-6" data-testid="hidden-gems-section">
              <div className="flex items-center gap-2 mb-3">
                <Gem className="w-4 h-4 text-honey-amber" />
                <h2 className="font-heading text-base text-vinyl-black">Hidden Gems</h2>
                <span className="text-[10px] text-muted-foreground ml-1">your most valuable records</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {hiddenGems.map((gem, idx) => (
                  <Link key={gem.id} to={`/record/${gem.id}`}>
                    <Card className="p-3 border-honey/30 flex items-center gap-3 hover:shadow-md transition-all cursor-pointer" data-testid={`hidden-gem-${idx}`}>
                    <div className="relative shrink-0">
                      <AlbumArt src={gem.cover_url} alt={`${gem.artist} - ${gem.title} Vinyl Record`} className="w-14 h-14 rounded-lg object-cover shadow-sm" />
                      <span className="absolute -top-1.5 -left-1.5 w-5 h-5 bg-honey rounded-full flex items-center justify-center text-[10px] font-bold text-vinyl-black shadow">
                        {idx + 1}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{gem.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{gem.artist}</p>
                      <p className="text-xs font-medium text-honey-amber mt-0.5" data-testid={`gem-value-${idx}`}>
                        ${gem.median_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        {gem.low_value && gem.high_value && (
                          <span className="text-[10px] text-muted-foreground font-normal ml-1">
                            (${gem.low_value.toFixed(0)} · ${gem.high_value.toFixed(0)})
                          </span>
                        )}
                      </p>
                    </div>
                  </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Your Week in Wax CTA */}
          {collectionValue && collectionValue.valued_count > 0 && (
            <WaxReportCTA />
          )}

          {/* Search and Sort Controls */}
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search collection..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 border-honey/50"
                data-testid="collection-search"
              />
            </div>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-full sm:w-[200px] border-honey/50" data-testid="sort-select">
                <ArrowUpDown className="w-4 h-4 mr-2" />
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map(option => (
                  <SelectItem key={option.value} value={option.value} data-testid={`sort-${option.value}`}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant={selectMode ? "default" : "outline"}
              size="sm"
              onClick={selectMode ? exitSelectMode : () => setSelectMode(true)}
              className={`gap-1.5 shrink-0 ${selectMode ? 'bg-honey text-vinyl-black hover:bg-honey-amber' : 'border-honey/50 text-stone-600'}`}
              data-testid="select-mode-btn"
            >
              <ListChecks className="w-4 h-4" />
              {selectMode ? 'Cancel' : 'Select'}
            </Button>
          </div>

          {/* Multi-select action bar */}
          {selectMode && (
            <div className="flex items-center gap-3 mb-4 p-3 rounded-xl bg-honey/10 border border-honey/30" data-testid="bulk-action-bar">
              <span className="text-sm font-medium text-stone-600">{selectedIds.size} selected</span>
              <Button variant="ghost" size="sm" onClick={selectAll} className="text-xs text-honey-amber hover:text-honey" data-testid="select-all-btn">Select All</Button>
              <div className="ml-auto flex gap-2">
                <Button
                  size="sm"
                  disabled={selectedIds.size === 0}
                  onClick={handleBulkDreamify}
                  className="bg-stone-100 text-stone-700 hover:bg-stone-200 gap-1.5 rounded-full text-xs"
                  data-testid="bulk-dreamify-btn"
                >
                  <Cloud className="w-3.5 h-3.5" /> Dreamify
                </Button>
                <Button
                  size="sm"
                  disabled={selectedIds.size === 0}
                  onClick={handleBulkHuntify}
                  className="bg-amber-100 text-amber-800 hover:bg-amber-200 gap-1.5 rounded-full text-xs"
                  data-testid="bulk-huntify-btn"
                >
                  <ArrowRight className="w-3.5 h-3.5" /> Huntify
                </Button>
              </div>
            </div>
          )}

          {/* Discogs Import */}
          <div className="mb-6">
            <DiscogsImport onImportComplete={fetchData} />
          </div>

          {records.length === 0 ? (
            <Card className="p-12 text-center border-honey/30">
              <div className="w-20 h-20 bg-honey/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Disc className="w-10 h-10 text-honey-amber" />
              </div>
              <h3 className="font-heading text-2xl mb-2">Your collection is empty</h3>
              <p className="text-muted-foreground mb-6">Start building your vinyl collection today!</p>
              <Link to="/add-record">
                <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2">
                  <Plus className="w-4 h-4" />
                  Add Your First Record
                </Button>
              </Link>
            </Card>
          ) : sortedAndFilteredRecords.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <p className="text-muted-foreground">No records match your search</p>
            </Card>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {sortedAndFilteredRecords.map(record => (
                <RecordCard 
                  key={record.id} 
                  record={record}
                  onSpin={handleLogSpin}
                  onDelete={handleDeleteRecord}
                  onMoveToWishlist={requestMoveToDreaming}
                  onMoveToISO={requestMoveToHunt}
                  isSpinning={spinningRecordId === record.id}
                  value={valueMap[record.id]}
                  selectMode={selectMode}
                  isSelected={selectedIds.has(record.id)}
                  onToggleSelect={toggleSelect}
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* ====== DREAMING TAB ====== */}
        <TabsContent value="wishlist">
          {/* "If only I had..." Wishlist Value Header */}
          <DreamDebtHeader
            totalValue={wishlistValue?.total_value || 0}
            itemCount={wishlistItems.length}
            countKey={countKey}
            subtractMsg={dreamSubtractMsg}
          />

          {wishlistItems.length === 0 ? (
            <Card className="p-12 text-center border-stone-200/60">
              <Cloud className="w-12 h-12 text-stone-300 mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2 text-stone-500">Nothing here yet...</h3>
              <p className="text-sm text-stone-400 mb-4">Move records from your collection to dream about them here.</p>
            </Card>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {wishlistItems.map(item => (
                <WishlistCard key={item.id} item={item} onPromote={handleWishlistToISO} onDelete={handleDeleteWishlistItem} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Collection Cleanse Confirmation Dialog */}
      <AlertDialog open={!!cleanseTarget} onOpenChange={(open) => { if (!open) setCleanseTarget(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">
              {cleanseTarget?.type === 'dreaming' ? 'Moving to Dream Items?' : 'Back on the hunt?'}
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              {cleanseTarget?.type === 'dreaming' ? (
                <span>This will remove <strong>{cleanseTarget?.title}</strong> from your Gold Standard and add it to your Dream Items.</span>
              ) : (
                <span>This will move <strong>{cleanseTarget?.title}</strong> to your Actively Seeking list for a potential upgrade or replacement.</span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="border-amber-100 hover:bg-amber-50/50" data-testid="cleanse-cancel-btn">Keep it</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmCleanse}
              style={cleanseTarget?.type === 'dreaming'
                ? { background: '#FFB300', color: '#fff', boxShadow: '0 4px 18px rgba(255, 179, 0, 0.35)' }
                : { background: 'linear-gradient(135deg, #E8A820, #C8861A)', color: '#fff' }}
              className="border-0 font-medium"
              data-testid="cleanse-confirm-btn"
            >
              {cleanseTarget?.type === 'dreaming' ? 'Add to Dream Items' : 'Move to Actively Seeking'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

const DreamDebtHeader = ({ totalValue, itemCount, countKey, subtractMsg }) => {
  const animatedValue = useCountUp(totalValue, 1400, true);
  // Reset count animation on key change (tab switch)
  const [localKey, setLocalKey] = useState(countKey);
  const [showAnim, setShowAnim] = useState(false);
  useEffect(() => {
    if (countKey !== localKey) {
      setLocalKey(countKey);
      setShowAnim(true);
    }
  }, [countKey, localKey]);
  // After animation completes, stop re-triggering
  useEffect(() => { if (showAnim) { const t = setTimeout(() => setShowAnim(false), 1500); return () => clearTimeout(t); } }, [showAnim]);

  const displayValue = showAnim ? animatedValue : totalValue;
  const hasDreams = itemCount > 0;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-stone-200/60 bg-gradient-to-br from-amber-50/40 via-white to-stone-50/40 p-5 mb-6 transition-all duration-500" data-testid="dream-debt-banner">
      {totalValue > 5000 && (
        <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide bg-gradient-to-r from-yellow-400 via-amber-400 to-yellow-500 text-amber-950 shadow-sm" data-testid="delusional-badge-collection">
          Certified Delusional
        </div>
      )}
      {hasDreams ? (
        <>
          <p className="text-xs font-medium uppercase tracking-widest text-stone-400 mb-1">Value of ISOs</p>
          <p className="font-heading text-2xl sm:text-3xl text-vinyl-black leading-tight" data-testid="dream-debt-headline">
            If only I had{' '}
            <span className="font-serif italic" style={{ color: '#C8861A' }} data-testid="dream-debt-amount">
              ${displayValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            ...{' '}
            <span className="text-base font-light text-stone-400 font-serif italic">(Value of ISOs)</span>
          </p>
          <p className="text-xs text-stone-400 mt-2">{itemCount} record{itemCount !== 1 ? 's' : ''} dreaming</p>
        </>
      ) : (
        <>
          <p className="text-xs font-medium uppercase tracking-widest text-stone-400 mb-1">Dreaming</p>
          <p className="font-heading text-xl sm:text-2xl text-stone-500 leading-tight font-serif italic" data-testid="dream-debt-empty">
            Your dreams are currently free. Go find some grails.
          </p>
        </>
      )}
      {subtractMsg && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mt-3 animate-pulse font-serif italic" data-testid="dream-subtract-msg">
          {subtractMsg}
        </p>
      )}
    </div>
  );
};

const RecordCard = ({ record, onSpin, onDelete, onMoveToWishlist, onMoveToISO, isSpinning, value, selectMode, isSelected, onToggleSelect }) => {
  return (
    <Card 
      className={`relative group border-honey/20 overflow-hidden hover:shadow-honey transition-all hover:-translate-y-1 ${isSelected ? 'ring-2 ring-honey shadow-honey' : ''} ${selectMode ? 'cursor-pointer' : ''}`}
      style={{ backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)', background: 'rgba(255,255,255,0.75)' }}
      data-testid={`record-card-${record.id}`}
      onClick={selectMode ? () => onToggleSelect(record.id) : undefined}
    >
      {selectMode && (
        <div className="absolute top-2 left-2 z-10" data-testid={`select-checkbox-${record.id}`}>
          {isSelected ? <CheckSquare className="w-5 h-5 text-honey drop-shadow" /> : <Square className="w-5 h-5 text-stone-400 drop-shadow" />}
        </div>
      )}
      <Link to={selectMode ? '#' : `/record/${record.id}`} onClick={selectMode ? (e) => e.preventDefault() : undefined}>
        <div className="relative aspect-square bg-vinyl-black">
          {record.cover_url ? (
            <AlbumArt 
              src={record.cover_url} 
              alt={`${record.artist} - ${record.title} Vinyl Record`}
              className={`w-full h-full object-cover ${isSpinning ? 'animate-spin-slow' : ''}`}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Disc className={`w-16 h-16 text-honey ${isSpinning ? 'animate-spin-slow' : ''}`} />
            </div>
          )}
          
          {/* Spin count badge */}
          {record.spin_count > 0 && (
            <div className="absolute bottom-2 left-2 bg-honey text-vinyl-black text-xs px-2 py-1 rounded-full font-medium">
              {record.spin_count} {record.spin_count === 1 ? 'spin' : 'spins'}
            </div>
          )}

          {/* Variant pill overlay */}
          {record.color_variant && (
            <div
              className="absolute top-2 left-2 max-w-[70%] truncate uppercase text-[10px] tracking-wider font-medium px-2 py-0.5 rounded-full z-[5]"
              style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)', border: '1px solid #FFD700', color: '#FFD700' }}
              data-testid={`variant-${record.id}`}
            >
              {record.color_variant}
            </div>
          )}

          {/* Never spun indicator */}
          {record.spin_count === 0 && (
            <div className="absolute bottom-2 left-2 bg-white/80 text-muted-foreground text-xs px-2 py-1 rounded-full">
              no logged spins
            </div>
          )}

          {/* Value badge */}
          {value > 0 && (
            <div className="absolute top-2 right-2 bg-vinyl-black/80 text-honey text-[10px] px-1.5 py-0.5 rounded-full font-medium" data-testid={`record-value-${record.id}`}>
              ${value.toFixed(0)}
            </div>
          )}
        </div>
      </Link>

      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <Link to={`/record/${record.id}`} className="flex-1 min-w-0">
            <h4 className="font-medium text-sm truncate hover:text-honey-amber transition-colors">
              {record.title}
            </h4>
            <p className="text-xs text-muted-foreground truncate">{record.artist}</p>
          </Link>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onSpin(record)} data-testid={`spin-btn-${record.id}`}>
                <Play className="w-4 h-4 mr-2" />
                Log Spin
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onMoveToWishlist(record.id)} data-testid={`wishlist-btn-${record.id}`}>
                <Heart className="w-4 h-4 mr-2" />
                Move to Dream Items
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onMoveToISO(record.id)} data-testid={`iso-btn-${record.id}`}>
                <ArrowRight className="w-4 h-4 mr-2" />
                Move to Actively Seeking
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => onDelete(record.id)} 
                className="text-red-600"
                data-testid={`delete-btn-${record.id}`}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Remove Completely
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Quick spin button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.preventDefault();
            onSpin(record);
          }}
          disabled={isSpinning}
          className="w-full mt-2 h-8 text-xs gap-1 bg-honey/10 hover:bg-honey/30"
        >
          <Play className="w-3 h-3" />
          {isSpinning ? 'Spinning...' : 'Spin Now'}
        </Button>
      </div>
    </Card>
  );
};


const WishlistCard = ({ item, onPromote, onDelete }) => (
  <Card className="group overflow-hidden border-stone-200/60 hover:shadow-md transition-all" data-testid={`wishlist-card-${item.id}`}>
    <Link to={item.discogs_id ? `/record/discogs-${item.discogs_id}` : '#'} className="block">
      <div className="relative aspect-square bg-stone-100">
        {item.cover_url ? (
          <AlbumArt src={item.cover_url} alt={`${item.artist} - ${item.album}`} className="w-full h-full object-cover opacity-70 group-hover:opacity-90 transition-opacity" />
        ) : (
          <div className="w-full h-full flex items-center justify-center"><Disc className="w-10 h-10 text-stone-300" /></div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
        {item.color_variant && (
          <div
            className="absolute top-2 left-2 max-w-[70%] truncate uppercase text-[10px] tracking-wider font-medium px-2 py-0.5 rounded-full z-[5]"
            style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)', border: '1px solid #FFD700', color: '#FFD700' }}
            data-testid={`variant-wishlist-${item.id}`}
          >
            {item.color_variant}
          </div>
        )}
      </div>
    </Link>
    <div className="p-3">
      <p className="font-medium text-sm truncate">{item.album}</p>
      <p className="text-xs text-muted-foreground truncate">{item.artist}</p>
      <div className="flex gap-1.5 mt-2">
        <Button size="sm" onClick={() => onPromote(item.id)}
          className="flex-1 h-7 text-[11px] rounded-full bg-gradient-to-r from-yellow-400 via-amber-400 to-yellow-500 text-amber-950 hover:from-yellow-500 hover:to-amber-500 font-medium"
          data-testid={`promote-btn-${item.id}`}>
          <Sparkles className="w-3 h-3 mr-1" /> Bring to Collection
        </Button>
        <Button size="sm" variant="ghost" onClick={() => onDelete(item.id)}
          className="h-7 w-7 p-0 text-stone-400 hover:text-red-500"
          data-testid={`delete-wishlist-${item.id}`}>
          <Trash2 className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  </Card>
);


const WaxReportCTA = () => (
  <Link to="/wax-reports" className="block mb-6 group" data-testid="wax-report-cta">
    <Card className="p-4 border-0 shadow-sm hover:shadow-md transition-all rounded-2xl" style={{ background: '#FAEDC7', border: '1px solid rgba(200,134,26,0.15)' }}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: 'rgba(200,134,26,0.08)' }}>
            <TrendingUp className="w-5 h-5" style={{ color: '#C8861A' }} />
          </div>
          <div>
            <p className="font-heading text-base" style={{ color: '#2A1A06' }}>your week in wax</p>
            <p className="text-[11px]" style={{ color: '#8A6B4A' }}>weekly report</p>
          </div>
        </div>
        <span className="text-xs font-medium group-hover:translate-x-0.5 transition-transform" style={{ color: '#C8861A' }}>View &rarr;</span>
      </div>
    </Card>
  </Link>
);

export default CollectionPage;
