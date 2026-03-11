import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
import { Disc, Plus, Search, Play, Trash2, MoreVertical, ArrowUpDown, Gem, TrendingUp, RefreshCw, Heart, ArrowRight, ShoppingBag, Cloud, Sparkles, CheckSquare, Square, ListChecks, AlertTriangle } from 'lucide-react';
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
import BackToTop from '../components/BackToTop';
import ValuationAssistantModal from '../components/ValuationAssistantModal';

// Counting animation hook
const useCountUp = (target, duration = 1400, enabled = true) => {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!enabled || target <= 0) { setValue(target); return; }
    const startVal = 0;
    const startTime = Date.now();
    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(startVal + (target - startVal) * eased);
      if (progress >= 1) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration, enabled]);
  return value;
};

// Honeycomb SVG icon
const HoneycombIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L17.5 5.5V12.5L12 16L6.5 12.5V5.5L12 2Z" />
    <path d="M12 16L17.5 19.5V22L12 24L6.5 22V19.5L12 16Z" opacity="0.4" />
  </svg>
);

// Treasury Header — Premium Collection & Dream Value Dashboard
const TreasuryHeader = ({ collectionValue, dreamValue, dreamPendingCount, dreamLoading, collectionTab, onTabChange, valuedCount, totalCount, onRefresh, refreshing, onPendingClick }) => {
  const animCollection = useCountUp(collectionValue, 1600, true);
  const animDream = useCountUp(dreamValue, 1600, true);

  return (
    <div
      className="relative rounded-2xl overflow-hidden mb-5"
      style={{
        background: 'rgba(255, 255, 255, 0.01)',
        backdropFilter: 'blur(60px) saturate(210%)',
        WebkitBackdropFilter: 'blur(60px) saturate(210%)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
      }}
      data-testid="treasury-header"
    >
      {/* Ambient Hive Glow — permanent honey sunset trapped behind the glass */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'linear-gradient(90deg, #FFD700 0%, #FF8C00 50%, #8B4513 100%)',
          filter: 'blur(80px)',
          opacity: 0.4,
        }}
        aria-hidden="true"
      />
      <div className="relative p-5 sm:p-6">
        <div className="relative flex flex-col sm:flex-row items-stretch sm:items-center gap-4 sm:gap-0">
          {/* Collection Value */}
          <button
            onClick={() => onTabChange('owned')}
            className={`flex-1 flex items-center gap-3 sm:gap-4 rounded-xl px-4 py-3 transition-all duration-300 ${collectionTab === 'owned' ? 'ring-1 ring-[#DAA520]/40' : 'hover:bg-white/10'}`}
            data-testid="treasury-collection-btn"
          >
            <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ background: 'linear-gradient(135deg, #DAA520, #E8A820)', boxShadow: '0 2px 8px rgba(218,165,32,0.4)' }}>
              <HoneycombIcon className="w-5 h-5 text-white" />
            </div>
            <div className="text-left">
              <p className="text-[10px] font-medium uppercase tracking-widest text-stone-500">Collection Value</p>
              <p className="font-serif text-2xl font-bold leading-tight" style={{ color: '#1A1A1A' }} data-testid="treasury-collection-value">
                ${Math.round(animCollection).toLocaleString()}
              </p>
              {valuedCount != null && (
                <p className="text-[10px] text-stone-400 mt-0.5">{valuedCount} of {totalCount} valued</p>
              )}
            </div>
          </button>

          {/* Divider */}
          <div className="hidden sm:flex flex-col items-center justify-center px-3">
            <div className="w-px h-10 bg-gradient-to-b from-transparent via-[#DAA520]/30 to-transparent" />
            <span className="text-[9px] font-bold uppercase tracking-wider text-[#DAA520]/50 my-1">vs</span>
            <div className="w-px h-10 bg-gradient-to-b from-transparent via-[#DAA520]/30 to-transparent" />
          </div>
          <div className="sm:hidden h-px mx-4 bg-gradient-to-r from-transparent via-[#DAA520]/20 to-transparent" />

          {/* Dream Value */}
          <button
            onClick={() => onTabChange('wishlist')}
            className={`flex-1 flex items-center gap-3 sm:gap-4 rounded-xl px-4 py-3 transition-all duration-300 ${collectionTab === 'wishlist' ? 'ring-1 ring-[#DAA520]/40' : 'hover:bg-white/10'}`}
            data-testid="treasury-dream-btn"
          >
            <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ background: 'linear-gradient(135deg, #C8861A, #D4A017)', boxShadow: '0 2px 8px rgba(200,134,26,0.3)' }}>
              <Cloud className="w-5 h-5 text-white" />
            </div>
            <div className="text-left">
              <p className="text-[10px] font-medium uppercase tracking-widest text-stone-500">Dream Records</p>
              {dreamLoading ? (
                <div className="h-8 w-24 rounded-md honey-shimmer mt-1" data-testid="treasury-dream-shimmer" />
              ) : (
                <p className="font-serif text-2xl font-bold leading-tight" style={{ color: '#1A1A1A' }} data-testid="treasury-dream-value">
                  ${Math.round(animDream).toLocaleString()}
                </p>
              )}
              <p className="text-[10px] text-stone-400 mt-0.5">
                {dreamPendingCount > 0 ? (
                  <button
                    onClick={e => { e.stopPropagation(); onPendingClick?.(); }}
                    className="flex items-center gap-1 text-amber-600 hover:text-amber-700 transition-colors group/pending"
                    title="The Hive doesn't have a price for these grails yet. Click to help set the benchmark!"
                    data-testid="treasury-pending-btn"
                  >
                    <AlertTriangle className="w-3 h-3 shrink-0" />
                    <span className="underline decoration-dotted group-hover/pending:decoration-solid">{dreamPendingCount} record{dreamPendingCount !== 1 ? 's' : ''} pending valuation</span>
                  </button>
                ) : 'if only...'}
              </p>
            </div>
          </button>
        </div>

        {/* Refresh pull-tab — bottom-centered circular gold glass button */}
        <div className="flex justify-center mt-3">
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 disabled:opacity-50 active:scale-95"
            style={{
              background: 'linear-gradient(135deg, rgba(218,165,32,0.25), rgba(200,134,26,0.15))',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              border: '1.5px solid rgba(218,165,32,0.4)',
              boxShadow: '0 2px 8px rgba(218,165,32,0.15), inset 0 1px 0 rgba(255,255,255,0.3)',
            }}
            data-testid="treasury-refresh-btn"
            aria-label="Refresh collection values"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#C8861A] ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  );
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
  const [dreamlistValue, setDreamlistValue] = useState(null);
  const [dreamSubtractMsg, setDreamSubtractMsg] = useState(null);
  const [countKey, setCountKey] = useState(0);
  // Confirmation dialog for "Collection Cleanse" moves
  const [cleanseTarget, setCleanseTarget] = useState(null); // { id, title, type: 'dreaming'|'hunt' }
  // Multi-select mode
  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [valuationModalOpen, setValuationModalOpen] = useState(false);
  const [valuationFocusItem, setValuationFocusItem] = useState(null);
  const navigate = useNavigate();

  // Auto-open valuation modal if ?filter=pending_value
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('filter') === 'pending_value') {
      setCollectionTab('wishlist');
      setValuationModalOpen(true);
      // Clean the URL param
      params.delete('filter');
      const newUrl = params.toString() ? `?${params.toString()}` : window.location.pathname;
      window.history.replaceState({}, '', newUrl);
    }
  }, []);

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
      // Fetch wishlist (WISHLIST ISO items) and dream value
      Promise.all([
        axios.get(`${API}/iso/dreamlist`, { headers }).then(r => setWishlistItems(r.data || [])),
        axios.get(`${API}/valuation/dreamlist`, { headers }).then(r => setDreamlistValue(r.data)),
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

  // Open the ValuationAssistantModal focused on a specific record
  const handleValueThis = (record) => {
    setValuationFocusItem({
      record_id: record.id,
      discogs_id: record.discogs_id || record.release_id,
      album: record.album || record.title,
      artist: record.artist,
      cover_url: record.cover_url || record.thumb,
    });
    setValuationModalOpen(true);
  };

  // Handle callback from ValuationAssistantModal
  const handleValuationUpdate = (result) => {
    if (result?.type === 'record_valued') {
      // Instant persistence: update the valueMap for this record
      setValueMap(prev => ({ ...prev, [result.record_id]: result.value }));
    } else if (typeof result === 'number') {
      // Dream value update from pending items mode
      setDreamlistValue(prev => prev ? { ...prev, total_value: result } : prev);
    }
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
        // Optimistically update Collection value
        const itemVal = valueMap[id] || 0;
        if (itemVal > 0 && collectionValue) {
          setCollectionValue(prev => prev ? { ...prev, total_value: Math.max(0, prev.total_value - itemVal) } : prev);
        }
        toast.success(res.data.message || 'moved to Dream List.');
        // Refetch dreamlist data from backend to stay in sync
        Promise.all([
          axios.get(`${API}/iso/dreamlist`, { headers: { Authorization: `Bearer ${token}` } }).then(r => setWishlistItems(r.data || [])),
          axios.get(`${API}/valuation/dreamlist`, { headers: { Authorization: `Bearer ${token}` } }).then(r => setDreamlistValue(r.data)),
        ]).catch(() => {});
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
      const updatedWishlist = wishlistItems.filter(i => i.id !== isoId);
      setWishlistItems(updatedWishlist);
      toast.success(res.data.message || `${item?.album || 'Record'} is now on the hunt.`);

      // If this was the last dream list item, force value to 0 immediately
      if (updatedWishlist.length === 0) {
        setDreamlistValue({ total_value: 0, valued_count: 0, total_count: 0, pending_count: 0 });
        setDreamSubtractMsg(null);
      } else if (item?.discogs_id && dreamlistValue) {
        // Show subtraction message and update dream value
        try {
          const valRes = await axios.get(`${API}/valuation/record-value/${item.discogs_id}`, { headers: { Authorization: `Bearer ${token}` } });
          const itemVal = valRes.data?.median_value || 0;
          if (itemVal > 0) {
            setDreamSubtractMsg(`Subtracting $${itemVal.toLocaleString('en-US', { minimumFractionDigits: 2 })} from your Value of Dream Records... and adding it to your Collection.`);
            setDreamlistValue(prev => prev ? { ...prev, total_value: Math.max(0, prev.total_value - itemVal) } : prev);
            setTimeout(() => setDreamSubtractMsg(null), 4000);
          }
        } catch {
          // Silently proceed; value subtraction is cosmetic
        }
      }
    } catch { toast.error('could not promote to Actively Seeking.'); }
  };

  const handleWishlistToCollection = async (isoId) => {
    try {
      const item = wishlistItems.find(i => i.id === isoId);
      const res = await axios.post(`${API}/iso/${isoId}/convert-to-collection`, {}, { headers: { Authorization: `Bearer ${token}` }});
      const updatedWishlist = wishlistItems.filter(i => i.id !== isoId);
      setWishlistItems(updatedWishlist);
      toast.success(res.data.message || `${item?.album || 'Record'} added to your collection!`);
      // Refresh collection data
      fetchData();
    } catch { toast.error('could not add to collection.'); }
  };

  const handleDeleteWishlistItem = async (isoId) => {
    try {
      await axios.delete(`${API}/iso/${isoId}`, { headers: { Authorization: `Bearer ${token}` }});
      const updatedWishlist = wishlistItems.filter(i => i.id !== isoId);
      setWishlistItems(updatedWishlist);
      toast.success('removed from Dream List.');
      // If this was the last item, force dream value to 0
      if (updatedWishlist.length === 0) {
        setDreamlistValue({ total_value: 0, valued_count: 0, total_count: 0, pending_count: 0 });
      } else {
        // Refetch dream value from backend to stay accurate
        axios.get(`${API}/valuation/dreamlist`, { headers: { Authorization: `Bearer ${token}` } })
          .then(r => setDreamlistValue(r.data)).catch(() => {});
      }
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
        <h1 className="font-heading text-3xl mb-6 ml-12 md:ml-0">My Collection</h1>
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
    <div className="max-w-6xl mx-auto px-4 py-8 pt-[64px] md:pt-24 pb-24 md:pb-8 honey-fade-in">
      <SEOHead
        title={`My Collection — ${records.length} Records`}
        description={`Your vinyl collection on The Honey Groove. ${records.length} records owned, ${wishlistItems.length} on the Dream List.`}
        url="/collection"
        noIndex
      />
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div className="ml-12 md:ml-0">
          <h1 className="font-heading text-3xl text-vinyl-black">My Collection</h1>
          <p className="text-muted-foreground">{records.length} owned · {wishlistItems.length} on Dream List</p>
        </div>
        <Link to={`/add-record?mode=${collectionTab === 'wishlist' ? 'dreaming' : 'reality'}`}>
          <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2" data-testid="add-record-btn">
            <Plus className="w-4 h-4" />
            {collectionTab === 'wishlist' ? 'Add to Dream List' : 'Add to Collection'}
          </Button>
        </Link>
      </div>

      <Tabs value={collectionTab} onValueChange={handleTabChange}>
        {/* Treasury Dashboard — Premium Value Display */}
        {collectionValue && collectionValue.total_value > 0 && (
          <TreasuryHeader
            collectionValue={collectionValue?.total_value || 0}
            dreamValue={dreamlistValue?.total_value || 0}
            dreamPendingCount={dreamlistValue?.pending_count || 0}
            dreamLoading={dreamlistValue === null}
            collectionTab={collectionTab}
            onTabChange={handleTabChange}
            valuedCount={collectionValue?.valued_count}
            totalCount={collectionValue?.total_count}
            onRefresh={handleRefreshValues}
            refreshing={refreshing}
            onPendingClick={() => { setValuationFocusItem(null); setValuationModalOpen(true); }}
          />
        )}

        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-2">
          <TabsTrigger value="owned" className="data-[state=active]:bg-honey text-sm gap-1.5" data-testid="tab-owned">
            <Sparkles className="w-3.5 h-3.5" /> Collection ({records.length})
          </TabsTrigger>
          <TabsTrigger value="wishlist" className="data-[state=active]:bg-honey text-sm gap-1.5" data-testid="tab-wishlist">
            <Cloud className="w-3.5 h-3.5" /> Dream List ({wishlistItems.length})
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
                      <AlbumArt src={gem.cover_url} alt={`${gem.artist} ${gem.title}${gem.color_variant ? ` ${gem.color_variant}` : ''} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow-sm" />
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
                  onValueThis={handleValueThis}
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* ====== DREAMING TAB ====== */}
        <TabsContent value="wishlist">
          {/* "If only I had..." Wishlist Value Header */}
          <DreamDebtHeader
            totalValue={wishlistItems.length === 0 ? 0 : (dreamlistValue?.total_value || 0)}
            itemCount={wishlistItems.length}
            countKey={countKey}
            subtractMsg={dreamSubtractMsg}
            pendingCount={dreamlistValue?.pending_count || 0}
            onPendingClick={() => { setValuationFocusItem(null); setValuationModalOpen(true); }}
          />
          <p className="text-sm text-muted-foreground mt-9 mb-5 px-4 leading-relaxed" data-testid="dreamlist-helper-text">These are your dream records. If you want to actively search for a record on this list, move it to Actively Seeking.</p>

          {wishlistItems.length === 0 ? (
            <Card className="p-12 text-center border-stone-200/60">
              <Cloud className="w-12 h-12 text-stone-300 mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2 text-stone-500">Nothing here yet...</h3>
              <p className="text-sm text-stone-400 mb-4">Move records from your collection to dream about them here.</p>
            </Card>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {wishlistItems.map(item => (
                <WishlistCard key={item.id} item={item} onPromote={handleWishlistToISO} onAddToCollection={handleWishlistToCollection} onDelete={handleDeleteWishlistItem} />
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
      <ValuationAssistantModal
        open={valuationModalOpen}
        onClose={() => { setValuationModalOpen(false); setValuationFocusItem(null); }}
        onValuesUpdated={handleValuationUpdate}
        focusItem={valuationFocusItem}
      />
      <BackToTop />
    </div>
  );
};

const DreamDebtHeader = ({ totalValue, itemCount, countKey, subtractMsg, pendingCount, onPendingClick }) => {
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
          <p className="text-xs font-medium uppercase tracking-widest text-stone-400 mb-1">Value of Dream Records</p>
          <p className="font-heading text-2xl sm:text-3xl text-vinyl-black leading-tight" data-testid="dream-debt-headline">
            If only I had{' '}
            <span className="font-serif italic" style={{ color: '#C8861A' }} data-testid="dream-debt-amount">
              ${displayValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            {pendingCount > 0 && (
              <button
                onClick={onPendingClick}
                className="text-sm font-normal text-stone-400 ml-1 underline decoration-dotted cursor-pointer hover:text-amber-600 transition-colors"
                title="The Hive doesn't have a price for these grails yet. Click to help set the benchmark!"
                data-testid="dream-pending-count"
              >
                (+{pendingCount} pending)
              </button>
            )}
            ...{' '}
            <span className="text-base font-light text-stone-400 font-serif italic">(Value of Dream Records)</span>
          </p>
          <p className="text-xs text-stone-400 mt-2">{itemCount} record{itemCount !== 1 ? 's' : ''} on Dream List</p>
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

const RecordCard = ({ record, onSpin, onDelete, onMoveToWishlist, onMoveToISO, isSpinning, value, selectMode, isSelected, onToggleSelect, onValueThis }) => {
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
        <div className="relative aspect-square bg-stone-200">
          {record.cover_url ? (
            <AlbumArt 
              src={record.cover_url} 
              alt={`${record.artist} ${record.title}${record.color_variant ? ` ${record.color_variant}` : ''} vinyl record`}
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

          {/* Variant pill overlay with scrim */}
          {record.color_variant && (
            <>
              <div className="absolute top-0 left-0 w-1/2 h-1/2 z-[4] pointer-events-none rounded-tl-2xl" style={{ background: 'linear-gradient(135deg, rgba(0,0,0,0.25) 0%, transparent 60%)' }} />
              {record.discogs_id ? (
                <Link
                  to={`/variant/${record.discogs_id}`}
                  onClick={e => e.stopPropagation()}
                  className="absolute top-2 left-2 max-w-[70%] truncate uppercase text-[10px] font-bold px-2 py-0.5 rounded-full z-[5] cursor-pointer transition-transform duration-150 hover:scale-105"
                  style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                  data-testid={`variant-${record.id}`}
                >
                  {record.color_variant}
                </Link>
              ) : (
                <div
                  className="absolute top-2 left-2 max-w-[70%] truncate uppercase text-[10px] font-bold px-2 py-0.5 rounded-full z-[5]"
                  style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
                  data-testid={`variant-${record.id}`}
                >
                  {record.color_variant}
                </div>
              )}
            </>
          )}

          {/* Edition number pill */}
          {record.edition_number && (
            <div
              className={`absolute ${record.color_variant ? 'top-8' : 'top-2'} left-2 uppercase text-[9px] font-bold px-2 py-0.5 rounded-full z-[5]`}
              style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
              data-testid={`edition-${record.id}`}
            >
              No. {record.edition_number}
            </div>
          )}

          {/* Never spun indicator */}
          {record.spin_count === 0 && (
            <div className="absolute bottom-2 left-2 bg-white/80 text-muted-foreground text-xs px-2 py-1 rounded-full">
              no logged spins
            </div>
          )}

          {/* Multi-copy badge */}
          {record.total_copies > 1 && (
            <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide z-[5]"
              style={{ background: 'rgba(255,255,255,0.85)', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)', color: '#996012', border: '1px solid rgba(218,165,32,0.4)' }}
              data-testid={`copy-badge-${record.id}`}>
              Copy {record.copy_number} of {record.total_copies}
            </div>
          )}

          {/* Value badge — glassy prominent OR "Value This" button */}
          {value > 0 ? (
            <div className="absolute top-2 right-2 px-2.5 py-1 rounded-full font-black z-[5]"
              style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', fontSize: '18px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
              data-testid={`record-value-${record.id}`}>
              ${value.toFixed(0)}
            </div>
          ) : record.discogs_id && onValueThis ? (
            <button
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); onValueThis(record); }}
              className="absolute top-2 right-2 px-2.5 py-1 rounded-full text-[11px] font-bold z-[5] transition-all hover:scale-105"
              style={{ background: 'rgba(255,255,255,0.85)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#C8861A', border: '2px solid #DAA520', boxShadow: '0 4px 16px 0 rgba(0,0,0,0.08)' }}
              data-testid={`value-this-btn-${record.id}`}
            >
              Value This
            </button>
          ) : null}
        </div>
      </Link>

      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <Link to={`/record/${record.id}`} className="flex-1 min-w-0">
            <h4 className="font-medium text-sm truncate hover:text-honey-amber transition-colors">
              {record.title}
            </h4>
            <p className="text-xs text-muted-foreground truncate">{record.artist}</p>
            {record.color_variant && (
              record.discogs_id ? (
                <Link to={`/variant/${record.discogs_id}`} onClick={e => e.stopPropagation()} className="text-[11px] text-honey-amber font-medium truncate mt-0.5 block hover:underline cursor-pointer transition-transform duration-150 hover:scale-105 origin-left" data-testid={`variant-label-${record.id}`}>
                  {record.color_variant}
                </Link>
              ) : (
                <p className="text-[11px] text-honey-amber font-medium truncate mt-0.5" data-testid={`variant-label-${record.id}`}>
                  {record.color_variant}
                </p>
              )
            )}
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


const WishlistCard = ({ item, onPromote, onAddToCollection, onDelete }) => (
  <Card className="group overflow-hidden border-stone-200/60 hover:shadow-md transition-all" data-testid={`wishlist-card-${item.id}`}>
    <Link to={item.discogs_id ? `/variant/${item.discogs_id}` : '#'} className="block">
      <div className="relative aspect-square bg-stone-100">
        {item.cover_url ? (
          <AlbumArt src={item.cover_url} alt={`${item.artist} ${item.album}${item.color_variant ? ` ${item.color_variant}` : ''} vinyl record`} className="w-full h-full object-cover opacity-70 group-hover:opacity-90 transition-opacity" />
        ) : (
          <div className="w-full h-full flex items-center justify-center"><Disc className="w-10 h-10 text-stone-300" /></div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
        {item.color_variant && (
          <>
            <div className="absolute top-0 left-0 w-1/2 h-1/2 z-[4] pointer-events-none" style={{ background: 'linear-gradient(135deg, rgba(0,0,0,0.25) 0%, transparent 60%)' }} />
            <div
              className="absolute top-2 left-2 max-w-[70%] truncate uppercase text-[10px] font-bold px-2 py-0.5 rounded-full z-[5]"
              style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
              data-testid={`variant-wishlist-${item.id}`}
            >
              {item.color_variant}
            </div>
          </>
        )}
        {item.preferred_number && (
          <div
            className={`absolute ${item.color_variant ? 'top-8' : 'top-2'} left-2 uppercase text-[9px] font-bold px-2 py-0.5 rounded-full z-[5]`}
            style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', letterSpacing: '0.5px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
            data-testid={`preferred-number-${item.id}`}
          >
            Seeking No. {item.preferred_number}
          </div>
        )}
        {item.median_value > 0 ? (
          <div className="absolute top-2 right-2 px-2.5 py-1 rounded-full font-black z-[5]"
            style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: '#000', fontSize: '18px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
            data-testid={`median-value-${item.id}`}>
            ${Math.round(item.median_value)}
            {item.value_source && item.value_source !== 'discogs' && (
              <span className="text-[8px] font-normal ml-0.5 opacity-60">{item.value_source === 'community' ? 'c' : 'm'}</span>
            )}
          </div>
        ) : (
          <div className="absolute top-2 right-2 px-2.5 py-1 rounded-full font-black z-[5]"
            style={{ background: 'rgba(255,215,0,0.2)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)', color: 'rgba(0,0,0,0.5)', fontSize: '14px', letterSpacing: '1px', border: '2px solid #DAA520', boxShadow: '0 8px 32px 0 rgba(0,0,0,0.1), inset 0 0 0 0.5px rgba(255,215,0,0.4)' }}
            data-testid={`median-value-placeholder-${item.id}`}>
            ---
          </div>
        )}
      </div>
    </Link>
    <div className="p-3">
      <p className="font-medium text-sm truncate">{item.album}</p>
      <p className="text-xs text-muted-foreground truncate">{item.artist}</p>
      <div className="flex flex-col gap-2 mt-2">
        <Button size="sm" onClick={() => onAddToCollection(item.id)}
          className="w-full h-8 text-[0.8rem] rounded-full font-semibold border-0"
          style={{ background: '#FFD700', color: '#1A1A1A' }}
          data-testid={`add-to-collection-btn-${item.id}`}>
          Add to Collection
        </Button>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => onPromote(item.id)}
            className="flex-1 h-8 text-[0.8rem] rounded-full font-semibold"
            style={{ background: 'transparent', border: '1.5px solid #DAA520', color: '#8B6914' }}
            data-testid={`actively-seeking-btn-${item.id}`}>
            Actively Seeking
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onDelete(item.id)}
            className="h-8 w-8 p-0 shrink-0 text-stone-400 hover:text-red-500"
            data-testid={`delete-wishlist-${item.id}`}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
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
