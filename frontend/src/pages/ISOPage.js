import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '../components/ui/alert-dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { Search, Plus, CheckCircle2, Loader2, Trash2, Tag, DollarSign, Disc, ArrowRightLeft, ShoppingBag, Camera, X, MessageSquare, Shield, HelpCircle } from 'lucide-react';
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from '../components/ui/tooltip';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { formatDistanceToNow } from 'date-fns';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import Fuse from 'fuse.js';
import { ProposeTradeModal } from './TradesPage';
import { usePageTitle } from '../hooks/usePageTitle';
import ExpressCheckout from '../components/ExpressCheckout';
import ListingDetailModal from '../components/ListingDetailModal';
import EssentialsUpsellModal from '../components/EssentialsUpsellModal';
import AlbumArt from '../components/AlbumArt';
import RecordSearchResult from '../components/RecordSearchResult';
import StripeGateModal from '../components/StripeGateModal';
import CountryGateModal from '../components/CountryGateModal';
import { countryFlag } from '../utils/countryFlag';
import { TitleBadge } from '../components/TitleBadge';
import { TagPill, ListingTypeBadge } from '../components/PostCards';
import { useVariantModal } from '../context/VariantModalContext';
import confetti from 'canvas-confetti';
import { ISOCard, CommunityISOCard, ActiveTradeCard, ListingCard, STATUS_CONFIG } from '../components/honeypot/HoneypotCards';

const ISO_TAGS = ['OG Press', 'Factory Sealed', 'Any', 'Promo'];
const FILTER_OPTIONS = ['All', 'OPEN', 'FOUND'];
import { GRADE_OPTIONS } from '../utils/grading';
import SEOHead from '../components/SEOHead';

const IsoMatchCover = ({ coverUrl }) => {
  return <AlbumArt src={coverUrl} className="w-8 h-8 rounded shrink-0" />;
};

const ISOPage = () => {
  usePageTitle('The Honeypot');
  const { user, token, API } = useAuth();
  const { openVariantModal } = useVariantModal();
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
  const [marketSearch, setMarketSearch] = useState('');
  const HONEYPOT_PAGE_SIZE = 24;
  const [visibleListings, setVisibleListings] = useState(HONEYPOT_PAGE_SIZE);
  const [tradeTarget, setTradeTarget] = useState(null);
  const [offerTarget, setOfferTarget] = useState(null);
  const [offerAmount, setOfferAmount] = useState('');
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [expressCheckout, setExpressCheckout] = useState(null); // { clientSecret, amount, listingId }
  const [platformFee, setPlatformFee] = useState(6);
  const [selectedListingId, setSelectedListingId] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [stripeEnabled, setStripeEnabled] = useState(false);
  const [showStripeGate, setShowStripeGate] = useState(false);
  const [showCountryGate, setShowCountryGate] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null); // listing or iso id pending delete
  const [deleteConfirmType, setDeleteConfirmType] = useState(null); // 'listing' or 'iso'
  const [showEssentialsUpsell, setShowEssentialsUpsell] = useState(false);
  const [showHowTradesWork, setShowHowTradesWork] = useState(false);
  const pendingCheckoutRef = useRef(null);

  // Check Stripe status
  useEffect(() => {
    if (token) {
      axios.get(`${API}/stripe/status`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => setStripeEnabled(r.data.stripe_connected))
        .catch(() => {});
    }
  }, [API, token]);

  // Fetch dynamic platform fee
  useEffect(() => {
    axios.get(`${API}/platform-fee`).then(r => setPlatformFee(r.data.platform_fee_percent)).catch(() => {});
  }, [API]);

  // Deep link: open listing modal from URL /honeypot/listing/:id
  useEffect(() => {
    const path = window.location.pathname;
    const match = path.match(/^\/honeypot\/listing\/(.+)$/);
    if (match) {
      setSelectedListingId(match[1]);
      setActiveTab('shop');
    }
    // Pre-fill search from ?q= param (e.g., from Variant Detail "Buy Now" bridge)
    const q = searchParams.get('q');
    if (q) { setMarketSearch(q); setActiveTab('shop'); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle Stripe payment return
  useEffect(() => {
    const paymentStatus = searchParams.get('payment');
    const sessionId = searchParams.get('session_id');
    if (!paymentStatus) return;
    setSearchParams({}, { replace: true });
    if (paymentStatus === 'cancelled') { toast.info('payment cancelled.'); return; }
    if (paymentStatus === 'success' && sessionId) {
      const checkStatus = async () => {
        try {
          const resp = await axios.get(`${API}/payments/status/${sessionId}`, { headers: { Authorization: `Bearer ${token}` } });
          if (resp.data.status === 'PAID') { trackEvent('purchase_completed', { amount: resp.data.amount }); toast.success(`payment of $${resp.data.amount} confirmed.`); fetchData(); }
          else toast.info('payment is processing. you\'ll be notified when complete.');
        } catch { toast.error('could not verify payment. try again.'); }
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
  const [pricingAssist, setPricingAssist] = useState(null);
  const [sellerStats, setSellerStats] = useState(null);
  const [showInsurancePrompt, setShowInsurancePrompt] = useState(false);
  const [insuranceChoice, setInsuranceChoice] = useState(null);
  const [internationalShipping, setInternationalShipping] = useState(false);
  const [listIntlShippingCost, setListIntlShippingCost] = useState('');
  const [listShippingCost, setListShippingCost] = useState('6.00');
  const [payoutEstimate, setPayoutEstimate] = useState(null);
  const [pulseData, setPulseData] = useState(null);
  const [unofficialAcked, setUnofficialAcked] = useState(false);

  // BLOCK 592: Auto-detect unofficial from selected release
  const isUnofficial = selectedRelease?.is_unofficial || false;

  const fetchData = useCallback(async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [isoRes, communityRes, listingsRes, myListRes, matchesRes, tradesRes, statsRes] = await Promise.all([
        axios.get(`${API}/iso`, { headers }),
        axios.get(`${API}/iso/community`, { headers }),
        axios.get(`${API}/listings?limit=200`),
        axios.get(`${API}/listings/my`, { headers }),
        axios.get(`${API}/listings/iso-matches`, { headers }),
        axios.get(`${API}/trades`, { headers }),
        axios.get(`${API}/seller/stats`, { headers }).catch(() => ({ data: { completed_transactions: 0 } })),
      ]);
      setIsos(isoRes.data);
      setCommunityIsos(communityRes.data);
      setListings(listingsRes.data);
      setMyListings(myListRes.data);
      setIsoMatches(matchesRes.data);
      setTrades(tradesRes.data);
      setSellerStats(statsRes.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Prefill listing form from query params (from record detail "List for Sale" / "Offer to Trade")
  useEffect(() => {
    const createType = searchParams.get('create');
    if (createType === 'sale' || createType === 'trade') {
      const artist = searchParams.get('artist') || '';
      const album = searchParams.get('album') || '';
      const discogs_id = searchParams.get('discogs_id') || '';
      const cover_url = searchParams.get('cover_url') || '';
      const year = searchParams.get('year') || '';
      const is_unofficial = searchParams.get('is_unofficial') === 'true';
      setActiveTab('shop');
      setShowCreate('listing');
      setListArtist(artist);
      setListAlbum(album);
      setListType(createType === 'trade' ? 'TRADE' : 'BUY_NOW');
      if (discogs_id) {
        setSelectedRelease({ discogs_id: parseInt(discogs_id), artist, title: album, cover_url, year: year ? parseInt(year) : null, is_unofficial });
      }
      setSearchParams({}, { replace: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Discogs search with debounce
  const searchTimerRef = useRef(null);
  const searchDiscogs = (query) => {
    setDiscogsQuery(query);
    if (!query || query.length < 2) { setDiscogsResults([]); return; }
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const resp = await axios.get(`${API}/discogs/search?q=${encodeURIComponent(query)}`, { headers: { Authorization: `Bearer ${token}` } });
        setDiscogsResults(resp.data.slice(0, 10));
      } catch { setDiscogsResults([]); }
      finally { setSearchLoading(false); }
    }, 350);
  };

  const selectRelease = (release) => {
    setSelectedRelease(release); setDiscogsResults([]); setDiscogsQuery('');
    if (showCreate === 'iso') { setIsoArtist(release.artist); setIsoAlbum(release.title); }
    else if (showCreate === 'listing') {
      setListArtist(release.artist); setListAlbum(release.title);
      // Fetch pricing assist for the listing modal
      if (release.discogs_id) {
        setPricingAssist(null);
        setPulseData(null);
        axios.get(`${API}/valuation/pricing-assist/${release.discogs_id}`, {
          headers: { Authorization: `Bearer ${token}` }
        }).then(r => { if (r.data && r.data.low !== null) setPricingAssist(r.data); }).catch(() => {});
        axios.get(`${API}/valuation/pulse/${release.discogs_id}`, {
          headers: { Authorization: `Bearer ${token}` }
        }).then(r => { if (r.data) setPulseData(r.data); }).catch(() => {});
      }
    }
  };

  const resetForm = () => {
    setSelectedRelease(null); setManualMode(false); setDiscogsQuery(''); setDiscogsResults([]);
    setIsoArtist(''); setIsoAlbum(''); setIsoPressing(''); setIsoCondition('');
    setIsoPriceMin(''); setIsoPriceMax(''); setIsoTags([]); setIsoCaption('');
    setListArtist(''); setListAlbum(''); setListCondition(''); setListPressing('');
    setListType('BUY_NOW'); setListPrice(''); setListDesc('');
    listPhotos.forEach(p => p.preview && URL.revokeObjectURL(p.preview));
    setListPhotos([]); setUploadingPhotos(false); setPricingAssist(null);
    setShowInsurancePrompt(false); setInsuranceChoice(null);
    setInternationalShipping(false);
    setListIntlShippingCost('');
    setUnofficialAcked(false);
    setListShippingCost('6.00'); setPayoutEstimate(null); setPulseData(null);
  };

  // Live payout estimator
  useEffect(() => {
    const price = parseFloat(listPrice);
    const ship = parseFloat(listShippingCost) || 0;
    if (!price || price <= 0 || listType === 'TRADE') { setPayoutEstimate(null); return; }
    const t = setTimeout(() => {
      axios.post(`${API}/estimate-payout`, { price, shipping_cost: ship }, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(r => setPayoutEstimate(r.data)).catch(() => setPayoutEstimate(null));
    }, 300);
    return () => clearTimeout(t);
  }, [listPrice, listShippingCost, listType, API, token]);

  const openModal = (type) => {
    if (type === 'listing' && !stripeEnabled) {
      setShowStripeGate(true);
      return;
    }
    if (type === 'listing' && !user?.country) {
      setShowCountryGate(true);
      return;
    }
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
    if (!artist || !album) { toast.error('artist and album are required.'); return; }
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
      toast.success('iso posted.');
      trackEvent('iso_posted');
      closeModal(); fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSubmitting(false); }
  };

  // Photo helpers
  const handlePhotoSelect = async (e) => {
    const files = Array.from(e.target.files || []);
    const remaining = 10 - listPhotos.length;
    if (remaining <= 0) { toast.error('maximum 10 photos.'); return; }
    const { validateImageFile, prepareImageForUpload } = require('../utils/imageUpload');
    const valid = [];
    for (const file of files.slice(0, remaining)) {
      const err = validateImageFile(file);
      if (err) { toast.error(err); continue; }
      const prepared = await prepareImageForUpload(file);
      valid.push({ file: prepared, preview: URL.createObjectURL(prepared), url: null });
    }
    if (valid.length) setListPhotos(prev => [...prev, ...valid]);
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
      urls.push(`${API}/files/serve/${resp.data.path}`);
    }
    return urls;
  };

  // Submit Listing
  const submitListing = async () => {
    const artist = listArtist || selectedRelease?.artist;
    const album = listAlbum || selectedRelease?.title;
    if (!artist || !album) { toast.error('artist and album are required.'); return; }
    if (listType !== 'TRADE' && !listPrice) { toast.error('price is required for buy/offer listings.'); return; }
    if (listType !== 'TRADE' && parseFloat(listPrice) < 0.01) { toast.error('minimum price is $0.01.'); return; }
    if (listPhotos.length === 0) { toast.error('at least 1 photo is required.'); return; }
    if (!listCondition) { toast.error('condition is required.'); return; }

    // BLOCK 592 / v2.5.3: Unofficial compliance check
    if (isUnofficial && !unofficialAcked) {
      toast.error('You must acknowledge the unofficial release terms before listing.');
      return;
    }

    // Show insurance prompt for items over $75 (only if not yet shown)
    const priceVal = parseFloat(listPrice);
    if (listType !== 'TRADE' && priceVal > 75 && insuranceChoice === null && !showInsurancePrompt) {
      setShowInsurancePrompt(true);
      return;
    }

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
        shipping_cost: listShippingCost ? parseFloat(listShippingCost) : null,
        description: listDesc || null,
        photo_urls: photoUrls,
        insured: insuranceChoice,
        international_shipping: internationalShipping,
        international_shipping_cost: internationalShipping && listIntlShippingCost ? parseFloat(listIntlShippingCost) : null,
        is_unofficial: isUnofficial,
        unofficial_acknowledged: isUnofficial ? unofficialAcked : false,
      }, { headers: { Authorization: `Bearer ${token}` }});
      toast.success('listing posted.');
      closeModal(); fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); setUploadingPhotos(false); }
    finally { setSubmitting(false); }
  };

  // "Upgrade to Collection" modal state
  const [acquireTarget, setAcquireTarget] = useState(null);
  const [acquireMediaCond, setAcquireMediaCond] = useState('');
  const [acquireSleeveCond, setAcquireSleeveCond] = useState('');
  const [acquirePrice, setAcquirePrice] = useState('');
  const [acquireSubmitting, setAcquireSubmitting] = useState(false);

  const handleMarkFound = (id) => {
    const iso = isos.find(i => i.id === id);
    setAcquireTarget(iso || { id });
    setAcquireMediaCond('');
    setAcquireSleeveCond('');
    setAcquirePrice('');
  };

  const handleAcquireConfirm = async () => {
    if (!acquireTarget) return;
    setAcquireSubmitting(true);
    try {
      const res = await axios.post(`${API}/iso/${acquireTarget.id}/acquire`, {
        media_condition: acquireMediaCond || null,
        sleeve_condition: acquireSleeveCond || null,
        price_paid: acquirePrice ? parseFloat(acquirePrice) : null,
      }, { headers: { Authorization: `Bearer ${token}` }});
      setIsos(prev => prev.filter(i => i.id !== acquireTarget.id));
      setAcquireTarget(null);
      confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 }, colors: ['#E8A820', '#C8861A', '#8A6B4A', '#FFD700'] });
      toast.success(`Congrats! ${res.data.title || 'Your record'} is now in your Collection.`);
      setTimeout(() => navigate('/collection'), 1500);
    } catch { toast.error('something went wrong.'); }
    finally { setAcquireSubmitting(false); }
  };
  const handleDeleteIso = async (id) => {
    try { await axios.delete(`${API}/iso/${id}`, { headers: { Authorization: `Bearer ${token}` }}); setIsos(prev => prev.filter(i => i.id !== id)); toast.success('iso removed.'); } catch { toast.error('something went wrong.'); }
  };
  const handleDemoteISO = async (id) => {
    try {
      const res = await axios.put(`${API}/iso/${id}/demote`, {}, { headers: { Authorization: `Bearer ${token}` }});
      setIsos(prev => prev.filter(i => i.id !== id));
      toast.success(res.data.message || 'Moved back to Dreams.');
    } catch { toast.error('could not move back to dreams.'); }
  };
  const handleDeleteListing = async (id) => {
    try { await axios.delete(`${API}/listings/${id}`, { headers: { Authorization: `Bearer ${token}` }}); setMyListings(prev => prev.filter(l => l.id !== id)); setListings(prev => prev.filter(l => l.id !== id)); toast.success('listing removed.'); } catch { toast.error('something went wrong.'); }
  };
  const confirmDelete = () => {
    if (deleteConfirmType === 'listing') handleDeleteListing(deleteConfirmId);
    else if (deleteConfirmType === 'iso') handleDeleteIso(deleteConfirmId);
    setDeleteConfirmId(null);
    setDeleteConfirmType(null);
  };

  // ── Essentials upsell check ──
  const ESSENTIALS_SEEN_KEY = 'honeygroove_essentials_prompt_seen';

  const proceedToCheckout = async () => {
    const pending = pendingCheckoutRef.current;
    if (!pending) return;
    pendingCheckoutRef.current = null;
    setPaymentLoading(true);
    try {
      const body = pending.type === 'offer'
        ? { listing_id: pending.listing.id, offer_amount: pending.offerAmount }
        : { listing_id: pending.listing.id };
      // Try express checkout (PaymentIntent) first
      const resp = await axios.post(`${API}/payments/create-intent`, body, { headers: { Authorization: `Bearer ${token}` } });
      if (resp.data.client_secret) {
        setExpressCheckout({
          clientSecret: resp.data.client_secret,
          amount: resp.data.amount,
          listingId: pending.listing.id,
          album: pending.listing.album,
          artist: pending.listing.artist,
        });
        setPaymentLoading(false);
        return;
      }
      // Fallback to redirect checkout
      const resp2 = await axios.post(`${API}/payments/checkout`, { ...body, origin_url: window.location.origin }, { headers: { Authorization: `Bearer ${token}` } });
      if (resp2.data.url) window.location.href = resp2.data.url;
      else toast.error('could not start checkout. try again.');
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail || '';
      if (status === 409) {
        toast.error('Buzzkill! Someone else just grabbed this record. Keep hunting!');
        navigate('/nectar');
      } else if (status === 400 && detail.toLowerCase().includes('card')) {
        toast.error(detail || 'Your card was declined. Please check your details and try again.');
      } else if (status === 400 && detail.toLowerCase().includes('price')) {
        toast.error(detail || 'There is a price issue with this listing. Please contact the seller.');
      } else if (status === 400 && detail.toLowerCase().includes('stripe')) {
        toast.error(detail || 'The seller has not set up payments yet.');
      } else {
        toast.error(detail || 'Payment could not be processed. Please try again.');
      }
    } finally {
      setPaymentLoading(false);
      if (pending.type === 'offer') { setOfferTarget(null); setOfferAmount(''); }
    }
  };

  const maybeShowUpsell = (listing, type, offerAmt) => {
    pendingCheckoutRef.current = { listing, type, offerAmount: offerAmt };
    const seen = localStorage.getItem(ESSENTIALS_SEEN_KEY);
    if (!seen) {
      localStorage.setItem(ESSENTIALS_SEEN_KEY, 'true');
      setShowEssentialsUpsell(true);
    } else {
      proceedToCheckout();
    }
  };

  const handleBuyNow = (listing) => {
    if (!user?.country) { setShowCountryGate(true); return; }
    maybeShowUpsell(listing, 'buy');
  };

  const handleMakeOfferSubmit = () => {
    if (!user?.country) { setShowCountryGate(true); return; }
    if (!offerTarget || !offerAmount) return;
    maybeShowUpsell(offerTarget, 'offer', parseFloat(offerAmount));
  };

  // Derived data
  const shopListingsRaw = listings.filter(l => l.listing_type === 'BUY_NOW' || l.listing_type === 'MAKE_OFFER');
  const tradeListingsRaw = listings.filter(l => l.listing_type === 'TRADE');

  // Fuse.js fuzzy search for marketplace
  const fuseOptions = {
    keys: ['artist', 'album', 'pressing_notes', 'color_variant', 'description'],
    threshold: 0.35,
    includeScore: true,
    shouldSort: true,
  };
  const fuseShop = new Fuse(shopListingsRaw, fuseOptions);
  const fuseTrade = new Fuse(tradeListingsRaw, fuseOptions);

  const shopListings = marketSearch.trim()
    ? fuseShop.search(marketSearch.trim()).map(r => r.item)
    : shopListingsRaw;
  const tradeListings = marketSearch.trim()
    ? fuseTrade.search(marketSearch.trim()).map(r => r.item)
    : tradeListingsRaw;
  const activeTrades = trades.filter(t => ['PROPOSED', 'COUNTERED', 'ACCEPTED', 'HOLD_PENDING', 'SHIPPING', 'CONFIRMING', 'DISPUTED'].includes(t.status));
  const filteredIsos = isos.filter(iso => {
    if (filter !== 'All' && iso.status !== filter) return false;
    if (searchQuery) { const q = searchQuery.toLowerCase(); return iso.artist.toLowerCase().includes(q) || iso.album.toLowerCase().includes(q); }
    return true;
  });
  const openCount = isos.filter(i => i.status === 'OPEN').length;

  const handleSetPriceAlert = async (isoId, targetPrice) => {
    try {
      await axios.put(`${API}/valuation/wantlist/${isoId}/price-alert`, { target_price: targetPrice }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsos(prev => prev.map(i => i.id === isoId ? { ...i, price_alert: targetPrice } : i));
      toast.success(targetPrice ? `Price alert set at $${targetPrice}` : 'Price alert removed');
    } catch { toast.error('could not set price alert.'); }
  };

  // Dynamic labels
  const ctaLabels = { shop: 'List a Record', trade: 'List for Trade', iso: 'Add to Actively Seeking' };
  const modalTitles = { shop: 'List a Record', trade: 'List for Trade', iso: 'Add to Actively Seeking' };

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
                <RecordSearchResult key={r.discogs_id} record={r} onClick={() => selectRelease(r)} size="sm" testId={`discogs-result-${r.discogs_id}`} />
              ))}
            </div>
          )}
          <button onClick={() => setManualMode(true)} className="text-sm text-honey-amber hover:underline" data-testid="manual-entry-btn">Or enter manually</button>
        </>
      ) : selectedRelease ? (
        <div className="flex items-center gap-3 bg-honey/10 rounded-lg p-3">
          <AlbumArt src={selectedRelease.cover_url} alt={`${selectedRelease.artist} ${selectedRelease.title} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow" isUnofficial={isUnofficial} />
          <div className="flex-1 min-w-0"><p className="font-heading text-base truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{selectedRelease.title}</p><p className="text-sm text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{selectedRelease.artist} {selectedRelease.year ? `(${selectedRelease.year})` : ''}</p></div>
          <button onClick={() => { setSelectedRelease(null); setManualMode(false); }} className="text-xs text-muted-foreground hover:text-red-500">Change</button>
        </div>
      ) : null}
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-3 md:pt-2">
        <Skeleton className="h-10 w-48 mb-6" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 w-full mb-3" />)}
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-32 md:pb-8" data-testid="honeypot-page">
      <SEOHead
        title="The Honeypot — Vinyl Marketplace"
        description="Browse vinyl records for sale and trade on The Honey Groove. Find rare pressings, colored vinyl, limited editions, and connect directly with collectors."
        url="/honeypot"
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'CollectionPage',
          name: 'The Honeypot — Vinyl Marketplace',
          url: 'https://thehoneygroove.com/honeypot',
          description: 'Vinyl records for sale and trade. Find rare pressings and colored vinyl from collectors worldwide.',
        }}
      />
      <StripeGateModal open={showStripeGate} onClose={() => setShowStripeGate(false)} />
      <CountryGateModal open={showCountryGate} onClose={() => setShowCountryGate(false)} />
      <EssentialsUpsellModal
        open={showEssentialsUpsell}
        onClose={() => setShowEssentialsUpsell(false)}
        onProceed={() => { setShowEssentialsUpsell(false); proceedToCheckout(); }}
      />
      {/* Sticky Glass Vault Header with Search — synced with Collection style */}
      <div
        className="sticky top-0 z-[1000] rounded-2xl overflow-hidden mb-6"
        style={{
          background: 'rgba(252, 248, 232, 0.5)',
          backdropFilter: 'blur(12px) saturate(180%)',
          WebkitBackdropFilter: 'blur(12px) saturate(180%)',
          border: '1px solid rgba(255, 255, 255, 0.6)',
          boxShadow: '0 8px 32px rgba(200,134,26,0.06), 0 1px 2px rgba(0,0,0,0.03)',
        }}
        data-testid="honeypot-glass-header"
      >
        {/* Ambient Hive Glow — synced with Collection */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'linear-gradient(135deg, rgba(255,215,0,0.08) 0%, rgba(218,165,32,0.06) 50%, rgba(200,134,26,0.04) 100%)' }} aria-hidden="true" />

        <div className="relative p-4 sm:p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="ml-10 md:ml-0">
              <h1 className="font-heading text-2xl sm:text-3xl text-vinyl-black" data-testid="honeypot-title">The Honeypot</h1>
              <p className="text-xs sm:text-sm text-muted-foreground">buy, trade, and hunt with collectors like you.</p>
            </div>
            <Button onClick={() => openModal(activeTab === 'iso' ? 'iso' : 'listing')}
              className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2 shrink-0" data-testid="honeypot-cta-btn">
              <span className="hidden sm:inline">{ctaLabels[activeTab]}</span>
              <span className="sm:hidden">New</span>
            </Button>
          </div>

          {/* Glass Search Bar */}
          <div className="relative" data-testid="honeypot-search-bar">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#C8861A]/60 pointer-events-none" />
            <input
              type="text"
              placeholder="Search artist, album, or variant..."
              value={marketSearch}
              onChange={e => setMarketSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm placeholder:text-stone-400 outline-none transition-all duration-200"
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 215, 0, 0.3)',
                color: '#2A1A06',
              }}
              onFocus={e => { e.target.style.borderColor = '#DAA520'; e.target.style.boxShadow = '0 0 0 3px rgba(218,165,32,0.15)'; }}
              onBlur={e => { e.target.style.borderColor = 'rgba(255, 215, 0, 0.3)'; e.target.style.boxShadow = 'none'; }}
              data-testid="honeypot-fuzzy-search"
            />
            {marketSearch && (
              <button onClick={() => setMarketSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600" data-testid="clear-market-search">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-3" data-testid="iso-tabs">
          <TabsTrigger value="shop" className="data-[state=active]:bg-honey data-[state=active]:shadow-none text-xs sm:text-sm px-1.5 sm:px-3" data-testid="tab-shop">
            Shop ({shopListings.length})
          </TabsTrigger>
          <TabsTrigger value="iso" className="data-[state=active]:bg-honey data-[state=active]:shadow-none text-xs sm:text-sm px-1.5 sm:px-3" data-testid="tab-iso">
            Seeking ({openCount})
          </TabsTrigger>
          <TabsTrigger value="trade" className="data-[state=active]:bg-honey data-[state=active]:shadow-none text-xs sm:text-sm px-1.5 sm:px-3" data-testid="tab-trade">
            Trade ({tradeListings.length})
          </TabsTrigger>
        </TabsList>

        {/* ====== SHOP TAB ====== */}
        <TabsContent value="shop">
          {/* ISO Matches */}
          {isoMatches.length > 0 && (
            <Card className="p-4 border-[#C8861A]/15 bg-amber-50/30 mb-6" data-testid="iso-matches-banner">
              <p className="text-sm font-medium text-[#C8861A] mb-2">ISO Matches Found!</p>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {isoMatches.map(m => (
                  <div key={m.id} className="flex-shrink-0 bg-white rounded-lg p-3 border border-[#C8861A]/15 w-48 cursor-pointer hover:shadow-md hover:border-[#C8861A]/30 transition-all"
                    onClick={() => setSelectedListingId(m.id)} data-testid={`iso-match-card-${m.id}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <IsoMatchCover coverUrl={m.cover_url} />
                      <div className="min-w-0 flex-1"><p className="text-xs font-medium truncate">{m.album}</p><p className="text-xs text-muted-foreground truncate">{m.artist}</p></div>
                    </div>
                    <ListingTypeBadge type={m.listing_type} price={m.price} size="sm" />
                    <Link to={`/profile/${m.user?.username}`} onClick={e => e.stopPropagation()}
                      className="text-xs text-muted-foreground hover:text-[#C8861A] hover:underline ml-1" data-testid={`iso-match-seller-${m.id}`}>by @{m.user?.username}</Link>
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
            <div>
              <div className="divide-y divide-[#C8861A]/10 border border-honey/20 rounded-xl overflow-hidden bg-white">
                {shopListings.slice(0, visibleListings).map(listing => (
                  <ListingCard key={listing.id} listing={listing} currentUserId={user?.id}
                    onBuyNow={handleBuyNow} onMakeOffer={(l) => setOfferTarget(l)}
                    onClick={() => setSelectedListingId(listing.id)} />
                ))}
              </div>
              {shopListings.length > visibleListings && (
                <div className="flex justify-center mt-4">
                  <Button
                    variant="outline"
                    onClick={() => setVisibleListings(prev => prev + HONEYPOT_PAGE_SIZE)}
                    className="rounded-full border-honey/40 text-honey-amber hover:bg-honey/10 gap-2"
                    data-testid="load-more-listings"
                  >
                    Show More ({shopListings.length - visibleListings} remaining)
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* My Shop Listings */}
          {myListings.filter(l => l.listing_type !== 'TRADE').length > 0 && (
            <div className="mt-8">
              <h3 className="font-heading text-lg text-vinyl-black mb-3">Your Listings</h3>
              <div className="divide-y divide-[#C8861A]/10 border border-honey/20 rounded-xl overflow-hidden bg-white">
                {myListings.filter(l => l.listing_type !== 'TRADE').map(listing => (
                  <div key={listing.id} className="relative">
                    <ListingCard listing={listing} onClick={() => setSelectedListingId(listing.id)} />
                    <Button size="sm" variant="ghost" onClick={() => { setDeleteConfirmId(listing.id); setDeleteConfirmType('listing'); }}
                      className="absolute top-3 right-3 text-[#8A6B4A]/60 hover:bg-[#8A6B4A]/10 h-8 w-8 p-0" data-testid={`delete-listing-${listing.id}`}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* ====== WANTLIST (READY TO BUY) TAB ====== */}
        <TabsContent value="iso">
          {/* Actively Seeking Header */}
          <div className="mb-5 p-4 rounded-xl bg-gradient-to-r from-amber-50/80 to-stone-50" data-testid="wantlist-header">
            <p className="font-heading text-lg text-vinyl-black">The Hunt is On.</p>
            <p className="text-sm text-stone-500 font-serif italic">You're actively looking, and we're actively matching. No more gatekeeping.</p>
          </div>

          {/* Your Hunt List */}
          <h3 className="font-heading text-lg text-vinyl-black mb-3" data-testid="your-wantlist-title">Actively Seeking</h3>
          <div className="flex gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input placeholder="Search your ISOs..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="pl-9 border-honey/50" data-testid="iso-search" />
            </div>
            <div className="flex gap-1">
              {FILTER_OPTIONS.map(f => (
                <Button key={f} size="sm" variant={filter === f ? 'default' : 'outline'} onClick={() => setFilter(f)}
                  className={`rounded-full text-xs ${filter === f ? 'bg-[#E8A820] text-[#2A1A06] hover:bg-[#C8861A]' : ''}`} data-testid={`iso-filter-${f.toLowerCase()}`}>{f}</Button>
              ))}
            </div>
          </div>
          {filteredIsos.length === 0 ? (
            <Card className="p-6 text-center border-honey/30 mb-8">
              <Search className="w-10 h-10 text-[#C8861A]/30 mx-auto mb-3" />
              <h3 className="font-heading text-lg mb-1">{isos.length === 0 ? 'No ISOs yet' : 'No results'}</h3>
              <p className="text-muted-foreground text-sm">{isos.length === 0 ? 'Tap "Add to Actively Seeking" to start your vinyl hunt!' : 'Try a different filter.'}</p>
            </Card>
          ) : (
            <div className="space-y-3 mb-8">
              {filteredIsos.map(iso => <ISOCard key={iso.id} iso={iso} isOwn={true} onMarkFound={handleMarkFound} onDelete={(id) => { setDeleteConfirmId(id); setDeleteConfirmType('iso'); }} onSetPriceAlert={handleSetPriceAlert} onDemote={handleDemoteISO} />)}
            </div>
          )}

          {/* The Community Hunt */}
          <h3 className="font-heading text-lg text-vinyl-black mb-3" data-testid="community-hunt-title">The Community Hunt</h3>
          {communityIsos.length === 0 ? (
            <Card className="p-6 text-center border-honey/30">
              <Search className="w-10 h-10 text-[#C8861A]/30 mx-auto mb-3" />
              <p className="text-muted-foreground text-sm">No community ISOs right now. Check back later!</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {communityIsos.map(iso => (
                <CommunityISOCard key={iso.id} iso={iso} onHaveThis={(l) => {
                  navigate(`/messages?to=${l.user_id}&contextType=iso&contextRecord=${encodeURIComponent(l.artist + ' · ' + l.album)}&contextAction=I have this`);
                }} onOpenVariant={iso.discogs_id ? () => openVariantModal({
                  artist: iso.artist, album: iso.album,
                  variant: iso.color_variant || 'Standard',
                  discogs_id: iso.discogs_id, cover_url: iso.cover_url,
                }) : null} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* ====== TRADE TAB ====== */}
        <TabsContent value="trade">
          {/* How Trades Work CTA */}
          <button
            onClick={() => setShowHowTradesWork(true)}
            className="flex items-center gap-1.5 text-sm text-[#C8861A] hover:text-[#996012] hover:underline mb-5 transition-colors"
            data-testid="how-trades-work-btn"
          >
            <HelpCircle className="w-4 h-4" /> How do trades work?
          </button>

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
            <div>
              <div className="divide-y divide-[#C8861A]/10 border border-honey/20 rounded-xl overflow-hidden bg-white">
                {tradeListings.slice(0, visibleListings).map(listing => (
                  <ListingCard key={listing.id} listing={listing} currentUserId={user?.id} onProposeTrade={(l) => { if (!user?.country) { setShowCountryGate(true); return; } setTradeTarget(l); }}
                    onClick={() => setSelectedListingId(listing.id)} />
                ))}
              </div>
              {tradeListings.length > visibleListings && (
                <div className="flex justify-center mt-4">
                  <Button
                    variant="outline"
                    onClick={() => setVisibleListings(prev => prev + HONEYPOT_PAGE_SIZE)}
                    className="rounded-full border-honey/40 text-honey-amber hover:bg-honey/10 gap-2"
                    data-testid="load-more-trades"
                  >
                    Show More ({tradeListings.length - visibleListings} remaining)
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* My Trade Listings */}
          {myListings.filter(l => l.listing_type === 'TRADE').length > 0 && (
            <div className="mt-8">
              <h3 className="font-heading text-lg text-vinyl-black mb-3">Your Trade Listings</h3>
              <div className="divide-y divide-[#C8861A]/10 border border-honey/20 rounded-xl overflow-hidden bg-white">
                {myListings.filter(l => l.listing_type === 'TRADE').map(listing => (
                  <div key={listing.id} className="relative">
                    <ListingCard listing={listing} onClick={() => setSelectedListingId(listing.id)} />
                    <Button size="sm" variant="ghost" onClick={() => { setDeleteConfirmId(listing.id); setDeleteConfirmType('listing'); }}
                      className="absolute top-3 right-3 text-[#8A6B4A]/60 hover:bg-[#8A6B4A]/10 h-8 w-8 p-0" data-testid={`delete-listing-${listing.id}`}>
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
            <DialogTitle className="font-heading flex items-center gap-2"><Search className="w-5 h-5 text-[#C8861A]" /> {modalTitles.iso}</DialogTitle>
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
                  className="w-full bg-[#E8A820]/15 text-[#C8861A] hover:bg-[#E8A820]/25 rounded-full" data-testid="iso-form-submit">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                  Add to Actively Seeking
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
                  <SelectContent>{GRADE_OPTIONS.map(g => <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>)}</SelectContent>
                </Select>
                <Input placeholder="Press / year (e.g. 1973 US press)" value={listPressing} onChange={e => setListPressing(e.target.value)} className="border-honey/50" />

                {activeTab !== 'trade' && (
                  <div>
                    <label className="text-sm font-medium mb-2 block">Listing Type</label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { key: 'BUY_NOW', label: 'Buy Now', icon: DollarSign, color: 'bg-amber-100/60 text-[#C8861A]' },
                        { key: 'MAKE_OFFER', label: 'Offer', icon: ShoppingBag, color: 'bg-amber-100/60 text-[#C8861A]' },
                        { key: 'TRADE', label: 'Trade', icon: ArrowRightLeft, color: 'bg-[#E8A820]/15 text-[#C8861A] border border-[#C8861A]/30' },
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
                  <div className="space-y-2">
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input placeholder="Price" type="number" min="0.01" step="0.01" value={listPrice} onChange={e => setListPrice(e.target.value)} className="pl-9 border-honey/50" data-testid="list-price-input" />
                    </div>
                    {listPrice && parseFloat(listPrice) > 0 && parseFloat(listPrice) < 0.50 && (
                      <p className="text-[11px] text-amber-700 bg-amber-50/80 border border-amber-200/60 rounded-lg px-3 py-1.5" data-testid="low-price-warning">
                        heads up: processing fees may exceed this price. you might receive $0 after fees.
                      </p>
                    )}
                    {pricingAssist && pricingAssist.low !== null && !isUnofficial && (
                      <p className="text-[11px] text-muted-foreground pl-1" data-testid="pricing-assist-hint">
                        recent sales: ${pricingAssist.low?.toFixed(2)} · ${pricingAssist.high?.toFixed(2)} on Discogs
                        {pulseData?.confident && parseFloat(listPrice) >= pulseData.hot_low && parseFloat(listPrice) <= pulseData.hot_high && (
                          <span className="ml-1.5 text-orange-500 font-semibold" data-testid="pulse-hot-badge" title={`Hot range: $${pulseData.hot_low} - $${pulseData.hot_high} (median $${pulseData.median})`}>in the hot zone</span>
                        )}
                      </p>
                    )}
                    {isUnofficial && (
                      <p className="text-[11px] text-stone-400 pl-1 italic" data-testid="unofficial-manual-price-notice">
                        Auto-pricing disabled for unofficial releases. Enter price manually.
                      </p>
                    )}
                    {pulseData?.confident && !isUnofficial && (
                      <p className="text-[11px] text-amber-600 pl-1" data-testid="pulse-suggest">
                        Honey Pulse Suggests: ${pulseData.hot_low?.toFixed(2)} - ${pulseData.hot_high?.toFixed(2)}
                      </p>
                    )}
                    {sellerStats && sellerStats.completed_transactions < 3 && parseFloat(listPrice) > 150 && (
                      <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2" data-testid="new-seller-restriction-msg">
                        New sellers can list items up to $150. Complete 3 transactions to unlock higher value listings.
                      </p>
                    )}

                    {/* Domestic Shipping */}
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input placeholder="Domestic Shipping" type="number" value={listShippingCost} onChange={e => setListShippingCost(e.target.value)} className="pl-9 border-honey/50" data-testid="list-shipping-cost-input" />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">domestic</span>
                    </div>

                    {/* International Shipping */}
                    <label className="flex items-center gap-2.5 cursor-pointer group" data-testid="international-shipping-checkbox">
                      <input
                        type="checkbox"
                        checked={internationalShipping}
                        onChange={(e) => setInternationalShipping(e.target.checked)}
                        className="w-4 h-4 rounded border-honey/50 text-honey accent-[#E8A820] cursor-pointer"
                      />
                      <span className="text-sm text-foreground group-hover:text-[#C8861A] transition-colors">Offer International Shipping</span>
                    </label>
                    <div className="relative">
                      <DollarSign className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground transition-opacity ${!internationalShipping ? 'opacity-50' : ''}`} />
                      <Input
                        placeholder="International Shipping"
                        type="number"
                        value={listIntlShippingCost}
                        onChange={e => setListIntlShippingCost(e.target.value)}
                        disabled={!internationalShipping}
                        className={`pl-9 border-honey/50 transition-opacity ${!internationalShipping ? 'opacity-50 cursor-not-allowed' : ''}`}
                        data-testid="list-intl-shipping-cost-input"
                      />
                      <span className={`absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground transition-opacity ${!internationalShipping ? 'opacity-50' : ''}`}>intl</span>
                    </div>

                    {/* Payout Estimator */}
                    {payoutEstimate && (
                      <div className="bg-amber-50/70 border border-amber-200/60 rounded-xl p-3 space-y-1.5" data-testid="payout-estimator">
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>listing price</span>
                          <span>${payoutEstimate.price.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>platform fee ({payoutEstimate.fee_percent}%{payoutEstimate.is_inner_hive ? ' · inner hive' : ''})</span>
                          <span className="text-red-500">-${payoutEstimate.fee_amount.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>shipping</span>
                          <span className="text-red-500">-${payoutEstimate.shipping_cost.toFixed(2)}</span>
                        </div>
                        <div className="border-t border-amber-200/60 pt-1.5 flex items-center justify-between">
                          <span className="text-sm font-semibold text-amber-800">Take Home Honey</span>
                          <span className="text-sm font-bold text-amber-800" data-testid="take-home-honey">${payoutEstimate.take_home.toFixed(2)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <Textarea placeholder="Description (optional)" value={listDesc} onChange={e => setListDesc(e.target.value)} className="border-honey/50 resize-none" rows={2} />

                <div>
                  <label className="text-sm font-medium mb-2 block">Photos <span className="text-muted-foreground font-normal">(1-10 required)</span></label>
                  <div className="grid grid-cols-4 gap-2">
                    {listPhotos.map((photo, idx) => (
                      <div key={idx} className="relative aspect-square rounded-lg overflow-hidden border border-honey/30 group">
                        <img src={photo.preview} alt={`Listing photo ${idx + 1}`} className="w-full h-full object-cover" />
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
                        <input type="file" accept=".jpg,.jpeg,.png,.webp,.heic,.heif" multiple onChange={handlePhotoSelect} className="hidden" />
                      </label>
                    )}
                  </div>
                </div>

                {/* Shipping Insurance Prompt */}
                {showInsurancePrompt && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-3" data-testid="insurance-prompt">
                    <p className="text-sm text-amber-800 font-medium">For items over $75 we recommend adding shipping insurance to protect you and your buyer.</p>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => { setInsuranceChoice(true); setShowInsurancePrompt(false); }}
                        className="flex-1 bg-[#E8A820]/15 text-[#C8861A] hover:bg-[#E8A820]/25 rounded-full text-xs"
                        data-testid="insurance-add-btn"
                      >
                        Got it, I'll add insurance
                      </Button>
                      <Button
                        onClick={() => { setInsuranceChoice(false); setShowInsurancePrompt(false); }}
                        variant="outline"
                        className="flex-1 rounded-full text-xs border-amber-300 text-amber-700"
                        data-testid="insurance-skip-btn"
                      >
                        Skip for now
                      </Button>
                    </div>
                  </div>
                )}

                {/* BLOCK 592 / v2.5.3: Unofficial Release Compliance Checkbox */}
                {isUnofficial && (
                  <div className="rounded-xl p-4 space-y-2.5" style={{ background: 'rgba(74,74,74,0.05)', border: '1px solid rgba(74,74,74,0.15)' }} data-testid="unofficial-compliance">
                    <div className="flex items-start gap-1.5">
                      <span className="inline-flex items-center text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full shrink-0" style={{ background: '#4A4A4A', color: '#fff' }}>Unofficial</span>
                      <p className="text-xs text-stone-500">This release is flagged as unofficial. You must acknowledge the terms below.</p>
                    </div>
                    <label className="flex items-start gap-2.5 cursor-pointer group" data-testid="unofficial-ack-checkbox">
                      <input
                        type="checkbox"
                        checked={unofficialAcked}
                        onChange={e => setUnofficialAcked(e.target.checked)}
                        className="mt-0.5 w-4 h-4 accent-amber-600 rounded"
                      />
                      <span className="text-xs leading-relaxed text-stone-600">
                        {user?.golden_hive_verified
                          ? 'I confirm this is an unofficial pressing and have described its condition accurately to protect my Golden Hive status.'
                          : 'I confirm this is an unofficial pressing and have described its condition accurately. I understand that transparency on unofficial items is a requirement for maintaining account standing and working toward Golden Hive verification.'}
                      </span>
                    </label>
                  </div>
                )}

                <Button onClick={submitListing} disabled={submitting || listPhotos.length === 0 || (manualMode && (!listArtist || !listAlbum)) || (!manualMode && !selectedRelease) || (sellerStats && sellerStats.completed_transactions < 3 && parseFloat(listPrice) > 150) || (isUnofficial && !unofficialAcked)}
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
            <p className="text-xs text-muted-foreground">{platformFee}% platform fee applies. You'll be redirected to secure checkout.</p>
            <Button onClick={handleMakeOfferSubmit} disabled={paymentLoading || !offerAmount}
              className="w-full bg-[#C8861A] text-white hover:bg-[#B07516] rounded-full" data-testid="submit-offer-btn">
              {paymentLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <DollarSign className="w-4 h-4 mr-2" />}
              Pay ${offerAmount || '0'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <ListingDetailModal
        listingId={selectedListingId}
        open={!!selectedListingId}
        onClose={() => { setSelectedListingId(null); window.history.replaceState({}, '', '/honeypot'); }}
        onBuyNow={handleBuyNow}
        onMakeOffer={(l) => setOfferTarget(l)}
        onProposeTrade={(l) => { if (!user?.country) { setShowCountryGate(true); return; } setTradeTarget(l); }}
      />

      {/* ===== Upgrade to Collection Modal ===== */}
      <Dialog open={!!acquireTarget} onOpenChange={(open) => { if (!open) setAcquireTarget(null); }}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-[#C8861A]" /> Upgrade to Collection
            </DialogTitle>
            <DialogDescription>
              {acquireTarget?.album && acquireTarget?.artist
                ? <><span className="font-semibold text-foreground">{acquireTarget.album}</span> by {acquireTarget.artist}</>
                : 'Finalize the details before adding to your vault.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div>
              <label className="text-sm font-medium mb-1.5 block">Media Condition</label>
              <Select value={acquireMediaCond} onValueChange={setAcquireMediaCond}>
                <SelectTrigger className="border-honey/50" data-testid="acquire-media-condition">
                  <SelectValue placeholder="Select media condition" />
                </SelectTrigger>
                <SelectContent>
                  {GRADE_OPTIONS.map(g => <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Sleeve Condition</label>
              <Select value={acquireSleeveCond} onValueChange={setAcquireSleeveCond}>
                <SelectTrigger className="border-honey/50" data-testid="acquire-sleeve-condition">
                  <SelectValue placeholder="Select sleeve condition" />
                </SelectTrigger>
                <SelectContent>
                  {GRADE_OPTIONS.map(g => <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Price Paid <span className="text-muted-foreground font-normal">(optional)</span></label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="0.00"
                  type="number"
                  value={acquirePrice}
                  onChange={e => setAcquirePrice(e.target.value)}
                  className="pl-9 border-honey/50"
                  data-testid="acquire-price-paid"
                />
              </div>
            </div>
            <Button
              onClick={handleAcquireConfirm}
              disabled={acquireSubmitting}
              className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
              data-testid="acquire-confirm-btn"
            >
              {acquireSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
              Bring to Collection
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteConfirmId} onOpenChange={(open) => { if (!open) { setDeleteConfirmId(null); setDeleteConfirmType(null); } }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Are you sure you want to delete this {deleteConfirmType === 'iso' ? 'ISO' : 'listing'}?</AlertDialogTitle>
            <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-listing">Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-red-600 text-white hover:bg-red-700" data-testid="confirm-delete-listing">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* How Trades Work Modal */}
      <Dialog open={showHowTradesWork} onOpenChange={setShowHowTradesWork}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl flex items-center gap-2">
              <ArrowRightLeft className="w-5 h-5 text-[#C8861A]" /> How Trading Works: The 4-Step Groove
            </DialogTitle>
            <DialogDescription>Secure, scam-free vinyl trading.</DialogDescription>
          </DialogHeader>
          <div className="space-y-5 pt-2">
            {/* Step 1 */}
            <div className="flex gap-3" data-testid="trade-step-1">
              <div className="w-8 h-8 rounded-full bg-[#E8A820]/20 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-sm font-bold text-[#996012]">1</span>
              </div>
              <div>
                <p className="font-heading text-sm font-semibold text-[#2A1A06]">Agree & Value</p>
                <p className="text-sm text-muted-foreground leading-relaxed">Both parties agree on the exchange. The system sets the hold amount based on Discogs Median value.</p>
              </div>
            </div>
            {/* Step 2 */}
            <div className="flex gap-3" data-testid="trade-step-2">
              <div className="w-8 h-8 rounded-full bg-[#E8A820]/20 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-sm font-bold text-[#996012]">2</span>
              </div>
              <div>
                <p className="font-heading text-sm font-semibold text-[#2A1A06]">Activate the Mutual Hold</p>
                <p className="text-sm text-muted-foreground leading-relaxed">Collectors authorize the Mutual Hold. No money is moved yet — it's just a pending safety authorization. This ensures everyone is incentivized to ship their wax safely.</p>
              </div>
            </div>
            {/* Step 3 */}
            <div className="flex gap-3" data-testid="trade-step-3">
              <div className="w-8 h-8 rounded-full bg-[#E8A820]/20 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-sm font-bold text-[#996012]">3</span>
              </div>
              <div>
                <p className="font-heading text-sm font-semibold text-[#2A1A06]">Secure Shipping</p>
                <p className="text-sm text-muted-foreground leading-relaxed">Both parties upload tracking. The system monitors the journey.</p>
              </div>
            </div>
            {/* Step 4 */}
            <div className="flex gap-3" data-testid="trade-step-4">
              <div className="w-8 h-8 rounded-full bg-[#E8A820]/20 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-sm font-bold text-[#996012]">4</span>
              </div>
              <div>
                <p className="font-heading text-sm font-semibold text-[#2A1A06]">Instant Release</p>
                <p className="text-sm text-muted-foreground leading-relaxed">Once both sides confirm receipt and condition, the holds are reversed. Cost to you: <strong>$0</strong>.</p>
              </div>
            </div>

            {/* Dispute Section */}
            <div className="bg-red-50/50 border border-red-200/50 rounded-xl p-4 space-y-3" data-testid="trade-dispute-info">
              <p className="font-heading text-sm font-semibold text-red-800 flex items-center gap-1.5">
                <Shield className="w-4 h-4" /> What happens if you Dispute?
              </p>
              <p className="text-sm text-red-700/80 leading-relaxed">
                If a record arrives damaged, is the wrong pressing, or never shows up, you can hit the <strong>Dispute</strong> button before the 48-hour release window closes.
              </p>
              <div className="space-y-2 pl-1">
                <div className="flex gap-2">
                  <span className="text-red-400 mt-0.5 shrink-0">1.</span>
                  <p className="text-sm text-red-700/80"><strong>Hold Locked:</strong> The Mutual Holds are frozen and will not be released.</p>
                </div>
                <div className="flex gap-2">
                  <span className="text-red-400 mt-0.5 shrink-0">2.</span>
                  <p className="text-sm text-red-700/80"><strong>Human Review:</strong> A Honey Groove moderator steps in to review photos, tracking data, and chat history.</p>
                </div>
                <div className="flex gap-2">
                  <span className="text-red-400 mt-0.5 shrink-0">3.</span>
                  <p className="text-sm text-red-700/80"><strong>Resolution:</strong> If the dispute is valid (e.g., you were scammed), the offender's hold is captured to compensate you, and their account is flagged or banned. The honest collector is always made whole.</p>
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Express Checkout Modal (Apple Pay / Google Pay + Card) */}
      <Dialog open={!!expressCheckout} onOpenChange={(open) => { if (!open) { setExpressCheckout(null); } }}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto" data-testid="express-checkout-modal">
          <DialogHeader>
            <DialogTitle className="text-lg font-heading">Checkout</DialogTitle>
            {expressCheckout && (
              <DialogDescription className="text-sm">
                {expressCheckout.album} {expressCheckout.artist ? `by ${expressCheckout.artist}` : ''} — ${expressCheckout.amount?.toFixed(2)}
              </DialogDescription>
            )}
          </DialogHeader>
          {expressCheckout && (
            <ExpressCheckout
              clientSecret={expressCheckout.clientSecret}
              amount={expressCheckout.amount}
              listingId={expressCheckout.listingId}
              onSuccess={() => { setExpressCheckout(null); fetchData(); toast.success('Payment confirmed!'); }}
              onCancel={() => setExpressCheckout(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ISOPage;
