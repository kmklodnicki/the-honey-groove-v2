import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Skeleton } from '../components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { Search, Plus, CheckCircle2, Loader2, Trash2, Tag, DollarSign, Disc, ArrowRightLeft, ShoppingBag, Camera, X, ChevronLeft, ChevronRight, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { ProposeTradeModal } from './TradesPage';

const ISO_TAGS = ['OG Press', 'Factory Sealed', 'Any', 'Promo'];
const FILTER_OPTIONS = ['All', 'OPEN', 'FOUND'];
const LISTING_CONDITIONS = ['Mint', 'Near Mint', 'Very Good Plus', 'Very Good', 'Good Plus', 'Good', 'Fair'];

const STATUS_CONFIG = {
  PROPOSED: { label: 'Proposed', color: 'bg-amber-100 text-amber-700' },
  COUNTERED: { label: 'Countered', color: 'bg-blue-100 text-blue-700' },
  ACCEPTED: { label: 'Accepted', color: 'bg-green-100 text-green-700' },
  DECLINED: { label: 'Declined', color: 'bg-red-100 text-red-700' },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-100 text-gray-600' },
  SHIPPING: { label: 'Shipping', color: 'bg-purple-100 text-purple-700' },
  CONFIRMING: { label: 'Confirming', color: 'bg-cyan-100 text-cyan-700' },
  COMPLETED: { label: 'Completed', color: 'bg-green-100 text-green-700' },
  DISPUTED: { label: 'Disputed', color: 'bg-red-100 text-red-700' },
};

const ISOPage = () => {
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('shop');
  const [isos, setIsos] = useState([]);
  const [communityIsos, setCommunityIsos] = useState([]);
  const [listings, setListings] = useState([]);
  const [myListings, setMyListings] = useState([]);
  const [isoMatches, setIsoMatches] = useState([]);
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(null);
  const [filter, setFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [tradeTarget, setTradeTarget] = useState(null);
  const [offerTarget, setOfferTarget] = useState(null);
  const [offerAmount, setOfferAmount] = useState('');
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  // Handle Stripe payment return
  useEffect(() => {
    const paymentStatus = searchParams.get('payment');
    const sessionId = searchParams.get('session_id');
    if (!paymentStatus) return;
    setSearchParams({}, { replace: true });
    if (paymentStatus === 'cancelled') { toast.info('Payment cancelled'); return; }
    if (paymentStatus === 'success' && sessionId) {
      const checkStatus = async () => {
        try {
          const resp = await axios.get(`${API}/payments/status/${sessionId}`, { headers: { Authorization: `Bearer ${token}` } });
          if (resp.data.status === 'PAID') { toast.success(`Payment of $${resp.data.amount} confirmed!`); fetchData(); }
          else toast.info('Payment is being processed. You\'ll be notified when complete.');
        } catch { toast.error('Could not verify payment status'); }
      };
      checkStatus();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Discogs search state
  const [discogsQuery, setDiscogsQuery] = useState('');
  const [discogsResults, setDiscogsResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [selectedRelease, setSelectedRelease] = useState(null);
  const [manualMode, setManualMode] = useState(false);

  // ISO form
  const [isoArtist, setIsoArtist] = useState('');
  const [isoAlbum, setIsoAlbum] = useState('');
  const [isoPressing, setIsoPressing] = useState('');
  const [isoCondition, setIsoCondition] = useState('');
  const [isoPriceMin, setIsoPriceMin] = useState('');
  const [isoPriceMax, setIsoPriceMax] = useState('');
  const [isoTags, setIsoTags] = useState([]);
  const [isoCaption, setIsoCaption] = useState('');

  // Listing form
  const [listArtist, setListArtist] = useState('');
  const [listAlbum, setListAlbum] = useState('');
  const [listCondition, setListCondition] = useState('');
  const [listPressing, setListPressing] = useState('');
  const [listType, setListType] = useState('BUY_NOW');
  const [listPrice, setListPrice] = useState('');
  const [listDesc, setListDesc] = useState('');
  const [listPhotos, setListPhotos] = useState([]);
  const [uploadingPhotos, setUploadingPhotos] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [isoRes, communityRes, listingsRes, myListRes, matchesRes, tradesRes] = await Promise.all([
        axios.get(`${API}/iso`, { headers }),
        axios.get(`${API}/iso/community`, { headers }),
        axios.get(`${API}/listings?limit=50`),
        axios.get(`${API}/listings/my`, { headers }),
        axios.get(`${API}/listings/iso-matches`, { headers }),
        axios.get(`${API}/trades`, { headers }),
      ]);
      setIsos(isoRes.data);
      setCommunityIsos(communityRes.data);
      setListings(listingsRes.data);
      setMyListings(myListRes.data);
      setIsoMatches(matchesRes.data);
      setTrades(tradesRes.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Discogs search
  const searchDiscogs = async (query) => {
    setDiscogsQuery(query);
    if (!query || query.length < 2) { setDiscogsResults([]); return; }
    setSearchLoading(true);
    try {
      const resp = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(query)}`, { headers: { Authorization: `Bearer ${token}` } });
      setDiscogsResults(resp.data.slice(0, 10));
    } catch { setDiscogsResults([]); }
    finally { setSearchLoading(false); }
  };

  const selectRelease = (release) => {
    setSelectedRelease(release); setDiscogsResults([]); setDiscogsQuery('');
    if (showCreate === 'iso') { setIsoArtist(release.artist); setIsoAlbum(release.title); }
    else if (showCreate === 'listing') { setListArtist(release.artist); setListAlbum(release.title); }
  };

  const resetForm = () => {
    setSelectedRelease(null); setManualMode(false); setDiscogsQuery(''); setDiscogsResults([]);
    setIsoArtist(''); setIsoAlbum(''); setIsoPressing(''); setIsoCondition('');
    setIsoPriceMin(''); setIsoPriceMax(''); setIsoTags([]); setIsoCaption('');
    setListArtist(''); setListAlbum(''); setListCondition(''); setListPressing('');
    setListType('BUY_NOW'); setListPrice(''); setListDesc('');
    listPhotos.forEach(p => p.preview && URL.revokeObjectURL(p.preview));
    setListPhotos([]); setUploadingPhotos(false);
  };

  const openModal = (type) => {
    resetForm();
    if (type === 'listing' && activeTab === 'trade') setListType('TRADE');
    else if (type === 'listing') setListType('BUY_NOW');
    setShowCreate(type);
  };
  const closeModal = () => { setShowCreate(null); resetForm(); };
  const toggleTag = (tag) => setIsoTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]);

  // Submit ISO
  const submitISO = async () => {
    const artist = isoArtist || selectedRelease?.artist;
    const album = isoAlbum || selectedRelease?.title;
    if (!artist || !album) { toast.error('Artist and album required'); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/composer/iso`, {
        artist, album,
        discogs_id: selectedRelease?.discogs_id || null,
        cover_url: selectedRelease?.cover_url || null,
        year: selectedRelease?.year || null,
        pressing_notes: isoPressing || null,
        condition_pref: isoCondition || null,
        tags: isoTags.length > 0 ? isoTags : null,
        target_price_min: isoPriceMin ? parseFloat(isoPriceMin) : null,
        target_price_max: isoPriceMax ? parseFloat(isoPriceMax) : null,
        caption: isoCaption || null,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success('ISO posted!');
      closeModal(); fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSubmitting(false); }
  };

  // Photo helpers
  const handlePhotoSelect = (e) => {
    const files = Array.from(e.target.files || []);
    const remaining = 10 - listPhotos.length;
    if (remaining <= 0) { toast.error('Maximum 10 photos'); return; }
    const toAdd = files.slice(0, remaining).map(file => ({ file, preview: URL.createObjectURL(file), url: null }));
    setListPhotos(prev => [...prev, ...toAdd]);
  };
  const removePhoto = (idx) => {
    setListPhotos(prev => { const r = prev[idx]; if (r.preview) URL.revokeObjectURL(r.preview); return prev.filter((_, i) => i !== idx); });
  };
  const uploadAllPhotos = async () => {
    const urls = [];
    for (const photo of listPhotos) {
      if (photo.url) { urls.push(photo.url); continue; }
      const formData = new FormData(); formData.append('file', photo.file);
      const resp = await axios.post(`${API}/upload`, formData, { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } });
      urls.push(resp.data.path);
    }
    return urls;
  };

  // Submit Listing
  const submitListing = async () => {
    const artist = listArtist || selectedRelease?.artist;
    const album = listAlbum || selectedRelease?.title;
    if (!artist || !album) { toast.error('Artist and album required'); return; }
    if (listType !== 'TRADE' && !listPrice) { toast.error('Price required for Buy/Offer listings'); return; }
    if (listPhotos.length === 0) { toast.error('At least 1 photo is required'); return; }
    if (!listCondition) { toast.error('Condition is required'); return; }
    setSubmitting(true);
    try {
      setUploadingPhotos(true);
      const photoUrls = await uploadAllPhotos();
      setUploadingPhotos(false);
      await axios.post(`${API}/listings`, {
        artist, album,
        discogs_id: selectedRelease?.discogs_id || null,
        cover_url: selectedRelease?.cover_url || null,
        year: selectedRelease?.year || null,
        condition: listCondition || null,
        pressing_notes: listPressing || null,
        listing_type: listType,
        price: listPrice ? parseFloat(listPrice) : null,
        description: listDesc || null,
        photo_urls: photoUrls,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success('Listing posted!');
      closeModal(); fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); setUploadingPhotos(false); }
    finally { setSubmitting(false); }
  };

  const handleMarkFound = async (id) => {
    try { await axios.put(`${API}/iso/${id}/found`, {}, { headers: { Authorization: `Bearer ${token}` }}); setIsos(prev => prev.map(i => i.id === id ? { ...i, status: 'FOUND' } : i)); toast.success('Marked as found!'); } catch { toast.error('Failed'); }
  };
  const handleDeleteIso = async (id) => {
    try { await axios.delete(`${API}/iso/${id}`, { headers: { Authorization: `Bearer ${token}` }}); setIsos(prev => prev.filter(i => i.id !== id)); toast.success('ISO removed'); } catch { toast.error('Failed'); }
  };
  const handleDeleteListing = async (id) => {
    try { await axios.delete(`${API}/listings/${id}`, { headers: { Authorization: `Bearer ${token}` }}); setMyListings(prev => prev.filter(l => l.id !== id)); setListings(prev => prev.filter(l => l.id !== id)); toast.success('Listing removed'); } catch { toast.error('Failed'); }
  };

  const handleBuyNow = async (listing) => {
    setPaymentLoading(true);
    try {
      const resp = await axios.post(`${API}/payments/checkout`, { listing_id: listing.id, origin_url: window.location.origin }, { headers: { Authorization: `Bearer ${token}` } });
      if (resp.data.url) window.location.href = resp.data.url;
      else toast.error('Failed to create checkout');
    } catch (err) { toast.error(err.response?.data?.detail || 'Payment failed'); }
    finally { setPaymentLoading(false); }
  };

  const handleMakeOfferSubmit = async () => {
    if (!offerTarget || !offerAmount) return;
    setPaymentLoading(true);
    try {
      const resp = await axios.post(`${API}/payments/checkout`, { listing_id: offerTarget.id, offer_amount: parseFloat(offerAmount), origin_url: window.location.origin }, { headers: { Authorization: `Bearer ${token}` } });
      if (resp.data.url) window.location.href = resp.data.url;
      else toast.error('Failed to create checkout');
    } catch (err) { toast.error(err.response?.data?.detail || 'Payment failed'); }
    finally { setPaymentLoading(false); setOfferTarget(null); setOfferAmount(''); }
  };

  // Derived data
  const shopListings = listings.filter(l => l.listing_type === 'BUY_NOW' || l.listing_type === 'MAKE_OFFER');
  const tradeListings = listings.filter(l => l.listing_type === 'TRADE');
  const activeTrades = trades.filter(t => ['PROPOSED', 'COUNTERED', 'ACCEPTED', 'SHIPPING', 'CONFIRMING', 'DISPUTED'].includes(t.status));
  const filteredIsos = isos.filter(iso => {
    if (filter !== 'All' && iso.status !== filter) return false;
    if (searchQuery) { const q = searchQuery.toLowerCase(); return iso.artist.toLowerCase().includes(q) || iso.album.toLowerCase().includes(q); }
    return true;
  });
  const openCount = isos.filter(i => i.status === 'OPEN').length;
  const foundCount = isos.filter(i => i.status === 'FOUND').length;

  // Dynamic labels
  const ctaLabels = { shop: 'List a Record', trade: 'List for Trade', iso: 'Add to Wantlist' };
  const modalTitles = { shop: 'List a Record', trade: 'List for Trade', iso: 'Add to Wantlist' };

  // Discogs picker
  const DiscogsPicker = () => (
    <div className="space-y-3">
      {!selectedRelease && !manualMode ? (
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input placeholder="Search Discogs for an album..." value={discogsQuery} onChange={e => searchDiscogs(e.target.value)} className="pl-9 border-honey/50" data-testid="discogs-picker-search" autoFocus />
            {searchLoading && <Loader2 className="w-4 h-4 animate-spin absolute right-3 top-3 text-muted-foreground" />}
          </div>
          {discogsResults.length > 0 && (
            <div className="border border-honey/30 rounded-lg max-h-48 overflow-y-auto bg-white">
              {discogsResults.map(r => (
                <button key={r.discogs_id} onClick={() => selectRelease(r)} className="w-full text-left px-3 py-2 hover:bg-honey/10 flex items-center gap-3 text-sm border-b border-honey/10 last:border-0" data-testid={`discogs-result-${r.discogs_id}`}>
                  {r.cover_url ? <img src={r.cover_url} alt="" className="w-10 h-10 rounded object-cover" /> : <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-5 h-5 text-honey" /></div>}
                  <div className="min-w-0 flex-1"><p className="font-medium truncate">{r.title}</p><p className="text-xs text-muted-foreground truncate">{r.artist} {r.year ? `(${r.year})` : ''}</p></div>
                </button>
              ))}
            </div>
          )}
          <button onClick={() => setManualMode(true)} className="text-sm text-honey-amber hover:underline" data-testid="manual-entry-btn">Or enter manually</button>
        </>
      ) : selectedRelease ? (
        <div className="flex items-center gap-3 bg-honey/10 rounded-lg p-3">
          {selectedRelease.cover_url ? <img src={selectedRelease.cover_url} alt="" className="w-14 h-14 rounded-lg object-cover shadow" /> : <div className="w-14 h-14 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
          <div className="flex-1 min-w-0"><p className="font-heading text-base">{selectedRelease.title}</p><p className="text-sm text-muted-foreground">{selectedRelease.artist} {selectedRelease.year ? `(${selectedRelease.year})` : ''}</p></div>
          <button onClick={() => { setSelectedRelease(null); setManualMode(false); }} className="text-xs text-muted-foreground hover:text-red-500">Change</button>
        </div>
      ) : null}
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-24">
        <Skeleton className="h-10 w-48 mb-6" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 w-full mb-3" />)}
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8" data-testid="honeypot-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading text-3xl text-vinyl-black" data-testid="honeypot-title">The Honeypot</h1>
          <p className="text-sm text-muted-foreground mt-1">buy, trade, and hunt with collectors like you.</p>
        </div>
        <Button onClick={() => openModal(activeTab === 'iso' ? 'iso' : 'listing')}
          className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2" data-testid="honeypot-cta-btn">
          <span className="hidden sm:inline">{ctaLabels[activeTab]}</span>
          <span className="sm:hidden">New</span>
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-3">
          <TabsTrigger value="shop" className="data-[state=active]:bg-honey text-sm" data-testid="tab-shop">
            Shop ({shopListings.length})
          </TabsTrigger>
          <TabsTrigger value="iso" className="data-[state=active]:bg-honey text-sm" data-testid="tab-iso">
            ISO ({openCount})
          </TabsTrigger>
          <TabsTrigger value="trade" className="data-[state=active]:bg-honey text-sm" data-testid="tab-trade">
            Trade ({tradeListings.length})
          </TabsTrigger>
        </TabsList>

        {/* ====== SHOP TAB ====== */}
        <TabsContent value="shop">
          {/* ISO Matches */}
          {isoMatches.length > 0 && (
            <Card className="p-4 border-purple-200 bg-purple-50/50 mb-6" data-testid="iso-matches-banner">
              <p className="text-sm font-medium text-purple-700 mb-2">ISO Matches Found!</p>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {isoMatches.map(m => (
                  <div key={m.id} className="flex-shrink-0 bg-white rounded-lg p-3 border border-purple-200 w-48">
                    <div className="flex items-center gap-2 mb-1">
                      {m.cover_url ? <img src={m.cover_url} alt="" className="w-8 h-8 rounded object-cover" /> : <Disc className="w-8 h-8 text-purple-400" />}
                      <div className="min-w-0 flex-1"><p className="text-xs font-medium truncate">{m.album}</p><p className="text-xs text-muted-foreground truncate">{m.artist}</p></div>
                    </div>
                    <span className="text-xs text-purple-600 font-medium">{m.listing_type === 'TRADE' ? 'Trade' : `$${m.price}`}</span>
                    <span className="text-xs text-muted-foreground ml-1">by @{m.user?.username}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Browse All (Buy Now + Make Offer) */}
          {shopListings.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <ShoppingBag className="w-12 h-12 text-honey mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">No listings yet</h3>
              <p className="text-muted-foreground text-sm mb-4">Be the first to list a record for sale!</p>
              <Button onClick={() => openModal('listing')} className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2">
                <Tag className="w-4 h-4" /> List a Record
              </Button>
            </Card>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {shopListings.map(listing => (
                <ListingCard key={listing.id} listing={listing} currentUserId={user?.id}
                  onBuyNow={handleBuyNow} onMakeOffer={(l) => setOfferTarget(l)} />
              ))}
            </div>
          )}

          {/* My Shop Listings */}
          {myListings.filter(l => l.listing_type !== 'TRADE').length > 0 && (
            <div className="mt-8">
              <h3 className="font-heading text-lg text-vinyl-black mb-3">Your Listings</h3>
              <div className="space-y-3">
                {myListings.filter(l => l.listing_type !== 'TRADE').map(listing => (
                  <div key={listing.id} className="relative">
                    <ListingCard listing={listing} />
                    <Button size="sm" variant="ghost" onClick={() => handleDeleteListing(listing.id)}
                      className="absolute top-3 right-3 text-red-400 hover:bg-red-50 h-8 w-8 p-0" data-testid={`delete-listing-${listing.id}`}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* ====== ISO TAB ====== */}
        <TabsContent value="iso">
          {/* Stats */}
          <div className="flex gap-4 mb-4">
            <div className="bg-purple-50 px-4 py-2 rounded-lg">
              <span className="text-2xl font-heading text-purple-700">{openCount}</span>
              <span className="text-xs text-purple-600 ml-1">searching</span>
            </div>
            <div className="bg-green-50 px-4 py-2 rounded-lg">
              <span className="text-2xl font-heading text-green-700">{foundCount}</span>
              <span className="text-xs text-green-600 ml-1">found</span>
            </div>
          </div>

          {/* Your Hunt List */}
          <h3 className="font-heading text-lg text-vinyl-black mb-3" data-testid="your-wantlist-title">Your Wantlist</h3>
          <div className="flex gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input placeholder="Search your ISOs..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="pl-9 border-honey/50" data-testid="iso-search" />
            </div>
            <div className="flex gap-1">
              {FILTER_OPTIONS.map(f => (
                <Button key={f} size="sm" variant={filter === f ? 'default' : 'outline'} onClick={() => setFilter(f)}
                  className={`rounded-full text-xs ${filter === f ? 'bg-vinyl-black text-white' : ''}`} data-testid={`iso-filter-${f.toLowerCase()}`}>{f}</Button>
              ))}
            </div>
          </div>
          {filteredIsos.length === 0 ? (
            <Card className="p-6 text-center border-honey/30 mb-8">
              <Search className="w-10 h-10 text-purple-300 mx-auto mb-3" />
              <h3 className="font-heading text-lg mb-1">{isos.length === 0 ? 'No ISOs yet' : 'No results'}</h3>
              <p className="text-muted-foreground text-sm">{isos.length === 0 ? 'Tap "Add to Wantlist" to start your vinyl hunt!' : 'Try a different filter.'}</p>
            </Card>
          ) : (
            <div className="space-y-3 mb-8">
              {filteredIsos.map(iso => <ISOCard key={iso.id} iso={iso} isOwn={true} onMarkFound={handleMarkFound} onDelete={handleDeleteIso} />)}
            </div>
          )}

          {/* The Community Hunt */}
          <h3 className="font-heading text-lg text-vinyl-black mb-3" data-testid="community-hunt-title">The Community Hunt</h3>
          {communityIsos.length === 0 ? (
            <Card className="p-6 text-center border-honey/30">
              <Search className="w-10 h-10 text-purple-300 mx-auto mb-3" />
              <p className="text-muted-foreground text-sm">No community ISOs right now. Check back later!</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {communityIsos.map(iso => (
                <CommunityISOCard key={iso.id} iso={iso} onHaveThis={(l) => {
                  navigate(`/messages?to=${l.user_id}&contextType=iso&contextRecord=${encodeURIComponent(l.artist + ' — ' + l.album)}&contextAction=I have this`);
                }} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* ====== TRADE TAB ====== */}
        <TabsContent value="trade">
          {/* Active Trades */}
          <h3 className="font-heading text-lg text-vinyl-black mb-3" data-testid="active-trades-title">Active Trades</h3>
          {activeTrades.length === 0 ? (
            <Card className="p-6 text-center border-honey/30 mb-8">
              <ArrowRightLeft className="w-10 h-10 text-honey mx-auto mb-3" />
              <h3 className="font-heading text-lg mb-1">No active trades</h3>
              <p className="text-muted-foreground text-sm">Browse trade listings below to propose a trade!</p>
            </Card>
          ) : (
            <div className="space-y-3 mb-8">
              {activeTrades.map(t => <ActiveTradeCard key={t.id} trade={t} currentUserId={user?.id} />)}
            </div>
          )}

          {/* Browse Trades */}
          <h3 className="font-heading text-lg text-vinyl-black mb-3" data-testid="browse-trades-title">Browse Trades</h3>
          {tradeListings.length === 0 ? (
            <Card className="p-6 text-center border-honey/30">
              <ArrowRightLeft className="w-10 h-10 text-honey/40 mx-auto mb-3" />
              <p className="text-muted-foreground text-sm">No trade listings yet. Be the first!</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {tradeListings.map(listing => (
                <ListingCard key={listing.id} listing={listing} currentUserId={user?.id} onProposeTrade={(l) => setTradeTarget(l)} />
              ))}
            </div>
          )}

          {/* My Trade Listings */}
          {myListings.filter(l => l.listing_type === 'TRADE').length > 0 && (
            <div className="mt-8">
              <h3 className="font-heading text-lg text-vinyl-black mb-3">Your Trade Listings</h3>
              <div className="space-y-3">
                {myListings.filter(l => l.listing_type === 'TRADE').map(listing => (
                  <div key={listing.id} className="relative">
                    <ListingCard listing={listing} />
                    <Button size="sm" variant="ghost" onClick={() => handleDeleteListing(listing.id)}
                      className="absolute top-3 right-3 text-red-400 hover:bg-red-50 h-8 w-8 p-0" data-testid={`delete-listing-${listing.id}`}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* ===== Create ISO Modal ===== */}
      <Dialog open={showCreate === 'iso'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2"><Search className="w-5 h-5 text-purple-600" /> {modalTitles.iso}</DialogTitle>
            <DialogDescription>What vinyl are you searching for?</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <DiscogsPicker />
            {(manualMode || selectedRelease) && (
              <>
                {manualMode && (
                  <>
                    <Input placeholder="Artist *" value={isoArtist} onChange={e => setIsoArtist(e.target.value)} className="border-honey/50" data-testid="iso-form-artist" />
                    <Input placeholder="Album *" value={isoAlbum} onChange={e => setIsoAlbum(e.target.value)} className="border-honey/50" data-testid="iso-form-album" />
                  </>
                )}
                <Input placeholder="Press / year preference" value={isoPressing} onChange={e => setIsoPressing(e.target.value)} className="border-honey/50" />
                <Input placeholder="Condition preference" value={isoCondition} onChange={e => setIsoCondition(e.target.value)} className="border-honey/50" />
                <div>
                  <label className="text-sm font-medium mb-2 block">Tags</label>
                  <div className="flex flex-wrap gap-2">
                    {ISO_TAGS.map(tag => (
                      <button key={tag} onClick={() => toggleTag(tag)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${isoTags.includes(tag) ? 'bg-honey text-vinyl-black shadow-sm' : 'bg-honey/10 text-muted-foreground hover:bg-honey/20'}`}
                        data-testid={`iso-tag-${tag.toLowerCase().replace(/\s/g, '-')}`}>{tag}</button>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Input placeholder="Min budget ($)" type="number" value={isoPriceMin} onChange={e => setIsoPriceMin(e.target.value)} className="border-honey/50" />
                  <Input placeholder="Max budget ($)" type="number" value={isoPriceMax} onChange={e => setIsoPriceMax(e.target.value)} className="border-honey/50" />
                </div>
                <Textarea placeholder="Caption for The Hive (optional)" value={isoCaption} onChange={e => setIsoCaption(e.target.value)} className="border-honey/50 resize-none" rows={2} />
                <Button onClick={submitISO} disabled={submitting || (manualMode && (!isoArtist || !isoAlbum)) || (!manualMode && !selectedRelease)}
                  className="w-full bg-purple-100 text-purple-800 hover:bg-purple-200 rounded-full" data-testid="iso-form-submit">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                  Add to Wantlist
                </Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* ===== List Record Modal ===== */}
      <Dialog open={showCreate === 'listing'} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent className="sm:max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2"><Tag className="w-5 h-5 text-honey-amber" /> {modalTitles[activeTab] || 'List a Record'}</DialogTitle>
            <DialogDescription>{activeTab === 'trade' ? 'List vinyl for trade with the community' : 'Sell or trade vinyl with the community'}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <DiscogsPicker />
            {(manualMode || selectedRelease) && (
              <>
                {manualMode && (
                  <>
                    <Input placeholder="Artist *" value={listArtist} onChange={e => setListArtist(e.target.value)} className="border-honey/50" data-testid="list-form-artist" />
                    <Input placeholder="Album *" value={listAlbum} onChange={e => setListAlbum(e.target.value)} className="border-honey/50" data-testid="list-form-album" />
                  </>
                )}
                <Select value={listCondition} onValueChange={setListCondition}>
                  <SelectTrigger className="border-honey/50" data-testid="list-condition-select"><SelectValue placeholder="Condition" /></SelectTrigger>
                  <SelectContent>{LISTING_CONDITIONS.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
                </Select>
                <Input placeholder="Press / year (e.g. 1973 US press)" value={listPressing} onChange={e => setListPressing(e.target.value)} className="border-honey/50" />

                {activeTab !== 'trade' && (
                  <div>
                    <label className="text-sm font-medium mb-2 block">Listing Type</label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { key: 'BUY_NOW', label: 'Buy Now', icon: DollarSign, color: 'bg-green-100 text-green-700' },
                        { key: 'MAKE_OFFER', label: 'Offer', icon: ShoppingBag, color: 'bg-blue-100 text-blue-700' },
                        { key: 'TRADE', label: 'Trade', icon: ArrowRightLeft, color: 'bg-purple-100 text-purple-700' },
                      ].map(t => (
                        <button key={t.key} onClick={() => setListType(t.key)}
                          className={`px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-1 justify-center transition-all ${listType === t.key ? `${t.color} ring-2 ring-offset-1 ring-current shadow-sm` : 'bg-gray-50 text-muted-foreground hover:bg-gray-100'}`}
                          data-testid={`list-type-${t.key.toLowerCase()}`}>
                          <t.icon className="w-3 h-3" /> {t.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {listType !== 'TRADE' && (
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input placeholder="Price" type="number" value={listPrice} onChange={e => setListPrice(e.target.value)} className="pl-9 border-honey/50" data-testid="list-price-input" />
                  </div>
                )}

                <Textarea placeholder="Description (optional)" value={listDesc} onChange={e => setListDesc(e.target.value)} className="border-honey/50 resize-none" rows={2} />

                <div>
                  <label className="text-sm font-medium mb-2 block">Photos <span className="text-muted-foreground font-normal">(1-10 required)</span></label>
                  <div className="grid grid-cols-4 gap-2">
                    {listPhotos.map((photo, idx) => (
                      <div key={idx} className="relative aspect-square rounded-lg overflow-hidden border border-honey/30 group">
                        <img src={photo.preview} alt="" className="w-full h-full object-cover" />
                        <button onClick={() => removePhoto(idx)} className="absolute top-1 right-1 bg-black/60 rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity" data-testid={`remove-photo-${idx}`}>
                          <X className="w-3 h-3 text-white" />
                        </button>
                        {idx === 0 && <span className="absolute bottom-1 left-1 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded">Cover</span>}
                      </div>
                    ))}
                    {listPhotos.length < 10 && (
                      <label className="aspect-square rounded-lg border-2 border-dashed border-honey/40 flex flex-col items-center justify-center cursor-pointer hover:border-honey hover:bg-honey/5 transition-all" data-testid="add-photo-btn">
                        <Camera className="w-5 h-5 text-honey mb-1" />
                        <span className="text-[10px] text-muted-foreground">{listPhotos.length === 0 ? 'Add photos' : `${listPhotos.length}/10`}</span>
                        <input type="file" accept="image/*" multiple onChange={handlePhotoSelect} className="hidden" />
                      </label>
                    )}
                  </div>
                </div>

                <Button onClick={submitListing} disabled={submitting || listPhotos.length === 0 || (manualMode && (!listArtist || !listAlbum)) || (!manualMode && !selectedRelease)}
                  className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="list-form-submit">
                  {submitting ? (<><Loader2 className="w-4 h-4 animate-spin mr-2" />{uploadingPhotos ? 'Uploading photos...' : 'Posting...'}</>) : (<><Tag className="w-4 h-4 mr-2" />{listType === 'TRADE' ? 'List for Trade' : `List for $${listPrice || '0'}`}</>)}
                </Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Propose Trade Modal */}
      <ProposeTradeModal open={!!tradeTarget} onOpenChange={(open) => { if (!open) setTradeTarget(null); }}
        listing={tradeTarget} token={token} API={API} onSuccess={fetchData} />

      {/* Make Offer Modal */}
      <Dialog open={!!offerTarget} onOpenChange={(open) => { if (!open) { setOfferTarget(null); setOfferAmount(''); } }}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle className="font-heading">Make an Offer</DialogTitle>
            <DialogDescription>{offerTarget?.album} by {offerTarget?.artist}{offerTarget?.price && <span className="block text-xs mt-1">Listed at ${offerTarget.price}</span>}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input placeholder="Your offer amount" type="number" value={offerAmount} onChange={e => setOfferAmount(e.target.value)} className="pl-9 border-honey/50 text-lg" data-testid="offer-amount-input" />
            </div>
            <p className="text-xs text-muted-foreground">4% platform fee applies. You'll be redirected to secure checkout.</p>
            <Button onClick={handleMakeOfferSubmit} disabled={paymentLoading || !offerAmount}
              className="w-full bg-blue-600 text-white hover:bg-blue-700 rounded-full" data-testid="submit-offer-btn">
              {paymentLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <DollarSign className="w-4 h-4 mr-2" />}
              Pay ${offerAmount || '0'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ISO Card Component (for user's own ISOs)
const ISOCard = ({ iso, isOwn, onMarkFound, onDelete }) => (
  <Card className={`p-4 border-honey/30 transition-all ${iso.status === 'FOUND' ? 'opacity-60 bg-green-50/30' : 'hover:shadow-md'}`} data-testid={`iso-item-${iso.id}`}>
    <div className="flex items-start gap-3">
      {iso.cover_url ? <img src={iso.cover_url} alt="" className="w-14 h-14 rounded-lg object-cover shadow" />
        : <div className="w-14 h-14 rounded-lg bg-purple-100 flex items-center justify-center shrink-0"><Search className="w-6 h-6 text-purple-400" /></div>}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h4 className="font-heading text-base">{iso.album}</h4>
          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${iso.status === 'FOUND' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'}`}>{iso.status}</span>
        </div>
        <p className="text-sm text-muted-foreground">{iso.artist}{iso.year ? ` (${iso.year})` : ''}</p>
        <div className="flex flex-wrap gap-1.5 mt-1">
          {(iso.tags || []).map(tag => <span key={tag} className="px-2 py-0.5 rounded-full text-xs bg-honey/20 text-honey-amber font-medium">{tag}</span>)}
        </div>
        <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
          {iso.pressing_notes && <span>Press: {iso.pressing_notes}</span>}
          {iso.condition_pref && <span>Cond: {iso.condition_pref}</span>}
          {(iso.target_price_min || iso.target_price_max) && <span>Budget: {iso.target_price_min ? `$${iso.target_price_min}` : '?'} – {iso.target_price_max ? `$${iso.target_price_max}` : '?'}</span>}
        </div>
      </div>
      {isOwn && iso.status === 'OPEN' && (
        <div className="flex gap-1 shrink-0">
          <Button size="sm" variant="ghost" className="text-green-600 hover:bg-green-50 h-8 px-2" onClick={() => onMarkFound(iso.id)} data-testid={`mark-found-${iso.id}`}><CheckCircle2 className="w-4 h-4" /></Button>
          <Button size="sm" variant="ghost" className="text-red-400 hover:bg-red-50 h-8 px-2" onClick={() => onDelete(iso.id)}><Trash2 className="w-4 h-4" /></Button>
        </div>
      )}
    </div>
  </Card>
);

// Community ISO Card (other users' ISOs with "I have this" button)
const CommunityISOCard = ({ iso, onHaveThis }) => (
  <Card className="p-4 border-honey/30 hover:shadow-md transition-all" data-testid={`community-iso-${iso.id}`}>
    <div className="flex items-start gap-3">
      {iso.cover_url ? <img src={iso.cover_url} alt="" className="w-14 h-14 rounded-lg object-cover shadow" />
        : <div className="w-14 h-14 rounded-lg bg-purple-100 flex items-center justify-center shrink-0"><Search className="w-6 h-6 text-purple-400" /></div>}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h4 className="font-heading text-base">{iso.album}</h4>
          <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-700">SEARCHING</span>
        </div>
        <p className="text-sm text-muted-foreground">{iso.artist}{iso.year ? ` (${iso.year})` : ''}</p>
        {iso.user && (
          <Link to={`/profile/${iso.user.username}`} className="text-xs text-honey-amber hover:underline">@{iso.user.username}</Link>
        )}
        <div className="flex flex-wrap gap-1.5 mt-1">
          {(iso.tags || []).map(tag => <span key={tag} className="px-2 py-0.5 rounded-full text-xs bg-honey/20 text-honey-amber font-medium">{tag}</span>)}
        </div>
        <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
          {iso.pressing_notes && <span>Press: {iso.pressing_notes}</span>}
          {iso.condition_pref && <span>Cond: {iso.condition_pref}</span>}
          {(iso.target_price_min || iso.target_price_max) && <span>Budget: {iso.target_price_min ? `$${iso.target_price_min}` : '?'} – {iso.target_price_max ? `$${iso.target_price_max}` : '?'}</span>}
        </div>
      </div>
      <Button size="sm" className="bg-green-100 text-green-700 hover:bg-green-200 rounded-full gap-1 shrink-0" onClick={() => onHaveThis(iso)} data-testid={`i-have-this-${iso.id}`}>
        <MessageSquare className="w-3 h-3" /> I have this
      </Button>
    </div>
  </Card>
);

// Active Trade Card (compact, for the Trade tab)
const ActiveTradeCard = ({ trade, currentUserId }) => {
  const isInitiator = trade.initiator_id === currentUserId;
  const otherUser = isInitiator ? trade.responder : trade.initiator;
  const sc = STATUS_CONFIG[trade.status] || STATUS_CONFIG.PROPOSED;
  return (
    <Link to="/trades" data-testid={`active-trade-${trade.id}`}>
      <Card className="p-4 border-honey/30 hover:shadow-md transition-all cursor-pointer">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {trade.offered_record?.cover_url ? <img src={trade.offered_record.cover_url} alt="" className="w-10 h-10 rounded object-cover" />
              : <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>}
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{trade.offered_record?.title || 'Your record'}</p>
              <p className="text-xs text-muted-foreground">with @{otherUser?.username || '?'}</p>
            </div>
          </div>
          <ArrowRightLeft className="w-4 h-4 text-honey shrink-0" />
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>
            <p className="text-sm font-medium truncate">{trade.listing_record?.album || 'Their record'}</p>
          </div>
          <span className={`px-2 py-1 rounded-full text-xs font-bold shrink-0 ${sc.color}`}>{sc.label}</span>
        </div>
      </Card>
    </Link>
  );
};

// Listing Card Component
const ListingCard = ({ listing, currentUserId, onProposeTrade, onBuyNow, onMakeOffer }) => {
  const [photoIdx, setPhotoIdx] = useState(0);
  const photos = listing.photo_urls || [];
  const typeConfig = {
    BUY_NOW: { label: 'Buy Now', color: 'bg-green-100 text-green-700' },
    MAKE_OFFER: { label: 'Make Offer', color: 'bg-blue-100 text-blue-700' },
    TRADE: { label: 'Trade', color: 'bg-purple-100 text-purple-700' },
  };
  const tc = typeConfig[listing.listing_type] || typeConfig.BUY_NOW;
  const mainImage = photos.length > 0 ? photos[photoIdx] : listing.cover_url;
  const isOwn = listing.user_id === currentUserId || listing.user?.id === currentUserId;
  const isTrade = listing.listing_type === 'TRADE';
  const isBuyNow = listing.listing_type === 'BUY_NOW';
  const isMakeOffer = listing.listing_type === 'MAKE_OFFER';

  return (
    <Card className="border-honey/30 overflow-hidden hover:shadow-md transition-all" data-testid={`listing-${listing.id}`}>
      <div className="relative aspect-square bg-honey/10">
        {mainImage ? <img src={mainImage} alt="" className="w-full h-full object-cover" />
          : <div className="w-full h-full flex items-center justify-center"><Disc className="w-12 h-12 text-honey" /></div>}
        {photos.length > 1 && (
          <>
            <button onClick={(e) => { e.stopPropagation(); setPhotoIdx(i => (i - 1 + photos.length) % photos.length); }}
              className="absolute left-1 top-1/2 -translate-y-1/2 bg-black/50 text-white rounded-full p-1 hover:bg-black/70" data-testid={`listing-photo-prev-${listing.id}`}>
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={(e) => { e.stopPropagation(); setPhotoIdx(i => (i + 1) % photos.length); }}
              className="absolute right-1 top-1/2 -translate-y-1/2 bg-black/50 text-white rounded-full p-1 hover:bg-black/70" data-testid={`listing-photo-next-${listing.id}`}>
              <ChevronRight className="w-4 h-4" />
            </button>
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
              {photos.map((_, i) => <span key={i} className={`w-1.5 h-1.5 rounded-full ${i === photoIdx ? 'bg-white' : 'bg-white/50'}`} />)}
            </div>
          </>
        )}
      </div>
      <div className="p-3">
        <h4 className="font-heading text-base truncate">{listing.album}</h4>
        <p className="text-sm text-muted-foreground truncate">{listing.artist}{listing.year ? ` (${listing.year})` : ''}</p>
        <div className="flex items-center gap-2 mt-2">
          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${tc.color}`}>{tc.label}</span>
          {listing.price && <span className="text-sm font-heading">${listing.price}</span>}
          {listing.condition && <span className="text-xs text-muted-foreground">{listing.condition}</span>}
        </div>
        {listing.user && <Link to={`/profile/${listing.user.username}`} className="text-xs text-muted-foreground hover:underline mt-1 block">@{listing.user.username}</Link>}
        {!isOwn && (
          <div className="mt-2 space-y-1.5">
            {isBuyNow && onBuyNow && (
              <button onClick={() => onBuyNow(listing)} className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-green-600 text-white hover:bg-green-700 transition-all" data-testid={`buy-now-${listing.id}`}>
                <DollarSign className="w-3 h-3" /> Buy Now — ${listing.price}
              </button>
            )}
            {isMakeOffer && onMakeOffer && (
              <button onClick={() => onMakeOffer(listing)} className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition-all" data-testid={`make-offer-${listing.id}`}>
                <DollarSign className="w-3 h-3" /> Make an Offer
              </button>
            )}
            {isTrade && onProposeTrade && (
              <button onClick={() => onProposeTrade(listing)} className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 hover:bg-purple-200 transition-all" data-testid={`propose-trade-${listing.id}`}>
                <ArrowRightLeft className="w-3 h-3" /> Propose Trade
              </button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default ISOPage;
