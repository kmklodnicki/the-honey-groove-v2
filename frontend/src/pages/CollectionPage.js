import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Disc, Plus, Search, Play, Trash2, MoreVertical, ArrowUpDown, Gem, DollarSign, TrendingUp, RefreshCw } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { toast } from 'sonner';
import DiscogsImport from '../components/DiscogsImport';
import { usePageTitle } from '../hooks/usePageTitle';

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
  { value: 'never_spun', label: 'Never Spun' },
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
    } catch (error) {
      console.error('Failed to fetch records:', error);
      toast.error('Failed to load collection');
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
    } catch { toast.error('Failed to refresh values'); }
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
      toast.success(`Now spinning: ${record.title}`);
      fetchData(); // Refresh to update spin count
    } catch (error) {
      console.error('Failed to log spin:', error);
      toast.error('Failed to log spin');
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
      toast.success('Record removed from collection');
    } catch (error) {
      console.error('Failed to delete record:', error);
      toast.error('Failed to remove record');
    }
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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="font-heading text-3xl text-vinyl-black">My Collection</h1>
          <p className="text-muted-foreground">{records.length} records</p>
        </div>
        <Link to="/add-record">
          <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2" data-testid="add-record-btn">
            <Plus className="w-4 h-4" />
            Add Record
          </Button>
        </Link>
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
              <Card key={gem.id} className="p-3 border-honey/30 flex items-center gap-3 hover:shadow-sm transition-all" data-testid={`hidden-gem-${idx}`}>
                <div className="relative shrink-0">
                  {gem.cover_url ? <img src={gem.cover_url} alt="" className="w-14 h-14 rounded-lg object-cover shadow-sm" />
                    : <div className="w-14 h-14 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-7 h-7 text-honey" /></div>}
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
                        (${gem.low_value.toFixed(0)} — ${gem.high_value.toFixed(0)})
                      </span>
                    )}
                  </p>
                </div>
              </Card>
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
      </div>

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
              isSpinning={spinningRecordId === record.id}
              value={valueMap[record.id]}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const RecordCard = ({ record, onSpin, onDelete, isSpinning, value }) => {
  return (
    <Card 
      className="group border-honey/30 overflow-hidden hover:shadow-honey transition-all hover:-translate-y-1"
      data-testid={`record-card-${record.id}`}
    >
      <Link to={`/record/${record.id}`}>
        <div className="relative aspect-square bg-vinyl-black">
          {record.cover_url ? (
            <img 
              src={record.cover_url} 
              alt={record.title}
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

          {/* Never spun indicator */}
          {record.spin_count === 0 && (
            <div className="absolute bottom-2 left-2 bg-white/80 text-vinyl-black text-xs px-2 py-1 rounded-full font-medium">
              Unspun
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
              <DropdownMenuItem 
                onClick={() => onDelete(record.id)} 
                className="text-red-600"
                data-testid={`delete-btn-${record.id}`}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Remove
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
            <p className="text-[11px]" style={{ color: '#8A6B4A' }}>weekly report · shareable card</p>
          </div>
        </div>
        <span className="text-xs font-medium group-hover:translate-x-0.5 transition-transform" style={{ color: '#C8861A' }}>View &rarr;</span>
      </div>
    </Card>
  </Link>
);

export default CollectionPage;
