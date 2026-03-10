import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { X, Star, Loader2, ChevronLeft, ChevronRight, DollarSign, ArrowRightLeft, Disc, Check, Heart, AlertTriangle, Package, Flag, Flame, Pencil, Camera, Save } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { resolveImageUrl } from '../utils/imageUrl';
import AlbumArt from './AlbumArt';
import PhotoLightbox from './PhotoLightbox';
import ReportModal from './ReportModal';
import { GradeLabel } from './GradeLabel';
import { GRADE_OPTIONS } from '../utils/grading';
import SEOHead from './SEOHead';
import { RarityPill } from './RarityBadge';

const ListingDetailModal = ({ listingId, open, onClose, onBuyNow, onMakeOffer, onProposeTrade }) => {
  const { token, API, user: currentUser } = useAuth();
  const navigate = useNavigate();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [photoIdx, setPhotoIdx] = useState(0);
  const [expandedPhoto, setExpandedPhoto] = useState(null);
  const [descExpanded, setDescExpanded] = useState(false);
  const [onWantlist, setOnWantlist] = useState(false);
  const [wantlistLoading, setWantlistLoading] = useState(false);
  const [offerAmount, setOfferAmount] = useState('');
  const [showOfferInput, setShowOfferInput] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  const [pulseData, setPulseData] = useState(null);
  const [rarityData, setRarityData] = useState(null);
  const onCloseRef = React.useRef(onClose);
  onCloseRef.current = onClose;

  // Edit mode state
  const [editing, setEditing] = useState(false);
  const [editPrice, setEditPrice] = useState('');
  const [editShippingCost, setEditShippingCost] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editCondition, setEditCondition] = useState('');
  const [editPressing, setEditPressing] = useState('');
  const [editListingType, setEditListingType] = useState('');
  const [editPhotos, setEditPhotos] = useState([]); // [{url, preview, file?}]
  const [editInsured, setEditInsured] = useState(false);
  const [editIntlShipping, setEditIntlShipping] = useState(false);
  const [editIntlShippingCost, setEditIntlShippingCost] = useState('');
  const [saving, setSaving] = useState(false);
  const [uploadingPhotos, setUploadingPhotos] = useState(false);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchListing = useCallback(async () => {
    if (!listingId) return;
    setLoading(true);
    setEditing(false);
    try {
      const r = await axios.get(`${API}/listings/${listingId}`, { headers });
      setListing(r.data);
      setOnWantlist(r.data.on_wantlist || false);
      setPhotoIdx(0);
      if (r.data.discogs_id) {
        axios.get(`${API}/valuation/pulse/${r.data.discogs_id}`, { headers })
          .then(p => setPulseData(p.data))
          .catch(() => setPulseData(null));
        axios.get(`${API}/vinyl/rarity/${r.data.discogs_id}`)
          .then(r => setRarityData(r.data))
          .catch(() => setRarityData(null));
      } else { setPulseData(null); setRarityData(null); }
    } catch (err) {
      toast.error('listing not found.');
      onClose();
    } finally {
      setLoading(false);
    }
  }, [listingId, API, token]);

  useEffect(() => {
    if (open && listingId) fetchListing();
  }, [open, listingId, fetchListing]);

  // URL management
  const closingRef = React.useRef(false);
  useEffect(() => {
    if (open && listingId) {
      window.history.pushState({ modal: true }, '', `/honeypot/listing/${listingId}`);
      closingRef.current = false;
    }
    const handlePop = () => {
      if (!closingRef.current) onCloseRef.current();
    };
    window.addEventListener('popstate', handlePop);
    return () => window.removeEventListener('popstate', handlePop);
  }, [open, listingId]);

  const handleClose = () => {
    closingRef.current = true;
    if (window.history.state?.modal) {
      window.history.back();
    }
    setEditing(false);
    onClose();
  };

  // Enter edit mode
  const startEditing = () => {
    if (!listing) return;
    setEditPrice(listing.price?.toString() || '');
    setEditShippingCost(listing.shipping_cost?.toString() || '');
    setEditDescription(listing.description || '');
    setEditCondition(listing.condition || '');
    setEditPressing(listing.pressing_notes || '');
    setEditListingType(listing.listing_type || 'BUY_NOW');
    setEditPhotos((listing.photo_urls || []).map(url => ({ url, preview: resolveImageUrl(url), file: null })));
    setEditInsured(listing.insured || false);
    setEditIntlShipping(listing.international_shipping || false);
    setEditIntlShippingCost(listing.international_shipping_cost?.toString() || '');
    setEditing(true);
  };

  // Photo handling for edit
  const handleEditPhotoSelect = (e) => {
    const files = Array.from(e.target.files || []);
    const remaining = 10 - editPhotos.length;
    if (remaining <= 0) { toast.error('maximum 10 photos.'); return; }
    const { validateImageFile } = require('../utils/imageUpload');
    const valid = [];
    for (const file of files.slice(0, remaining)) {
      const err = validateImageFile(file);
      if (err) { toast.error(err); continue; }
      valid.push({ file, preview: URL.createObjectURL(file), url: null });
    }
    if (valid.length) setEditPhotos(prev => [...prev, ...valid]);
  };

  const removeEditPhoto = (idx) => {
    setEditPhotos(prev => {
      const r = prev[idx];
      if (r.file && r.preview) URL.revokeObjectURL(r.preview);
      return prev.filter((_, i) => i !== idx);
    });
  };

  // Save edited listing
  const saveEdits = async () => {
    if (editPhotos.length === 0) { toast.error('at least 1 photo is required.'); return; }
    if (editListingType !== 'TRADE' && !editPrice) { toast.error('price is required.'); return; }
    if (!editCondition) { toast.error('condition is required.'); return; }

    setSaving(true);
    try {
      // Upload any new photos
      setUploadingPhotos(true);
      const photoUrls = [];
      for (const photo of editPhotos) {
        if (photo.url) { photoUrls.push(photo.url); continue; }
        const formData = new FormData();
        formData.append('file', photo.file);
        const resp = await axios.post(`${API}/upload`, formData, { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } });
        photoUrls.push(`${API}/files/serve/${resp.data.path}`);
      }
      setUploadingPhotos(false);

      const updateData = {
        price: editListingType !== 'TRADE' ? parseFloat(editPrice) : null,
        shipping_cost: editShippingCost ? parseFloat(editShippingCost) : null,
        description: editDescription || null,
        condition: editCondition,
        pressing_notes: editPressing || null,
        listing_type: editListingType,
        photo_urls: photoUrls,
        insured: editInsured,
        international_shipping: editIntlShipping,
        international_shipping_cost: editIntlShipping && editIntlShippingCost ? parseFloat(editIntlShippingCost) : null,
      };

      const resp = await axios.put(`${API}/listings/${listingId}`, updateData, { headers: { Authorization: `Bearer ${token}` } });
      setListing(resp.data);
      setEditing(false);
      toast.success('listing updated.');
    } catch (err) {
      setUploadingPhotos(false);
      toast.error(err.response?.data?.detail || 'failed to update listing.');
    } finally {
      setSaving(false);
    }
  };

  const toggleWantlist = async () => {
    if (!listing) return;
    setWantlistLoading(true);
    try {
      if (onWantlist) {
        const isos = await axios.get(`${API}/iso`, { headers: { Authorization: `Bearer ${token}` } });
        const match = isos.data?.find(i =>
          i.artist?.toLowerCase() === listing.artist?.toLowerCase() &&
          i.album?.toLowerCase() === listing.album?.toLowerCase()
        );
        if (match) {
          await axios.delete(`${API}/iso/${match.id}`, { headers: { Authorization: `Bearer ${token}` } });
        }
        setOnWantlist(false);
        toast.success('removed from Dream List.');
      } else {
        await axios.post(`${API}/composer/iso`, {
          artist: listing.artist, album: listing.album,
          discogs_id: listing.discogs_id, cover_url: listing.cover_url,
          year: listing.year,
        }, { headers: { Authorization: `Bearer ${token}` } });
        setOnWantlist(true);
        trackEvent('wantlist_added');
        toast.success('added to Dream List.');
      }
    } catch (err) {
      if (err.response?.status === 409) { setOnWantlist(true); toast.info('already on your Dream List.'); }
      else toast.error('something went wrong.');
    } finally {
      setWantlistLoading(false);
    }
  };

  const handleBuyNowClick = () => {
    if (listing && onBuyNow) { handleClose(); onBuyNow(listing); }
  };

  const handleOfferSubmit = () => {
    if (!offerAmount || !listing) return;
    handleClose();
    if (onMakeOffer) onMakeOffer(listing, parseFloat(offerAmount));
  };

  const handleTradeClick = () => {
    if (listing && onProposeTrade) { handleClose(); onProposeTrade(listing); }
  };

  const photos = listing?.photo_urls || [];
  const isOwn = listing?.user_id === currentUser?.id || listing?.user?.id === currentUser?.id;
  const canEdit = isOwn && listing?.status === 'ACTIVE';
  const isBuyNow = listing?.listing_type === 'BUY_NOW';
  const isMakeOffer = listing?.listing_type === 'MAKE_OFFER';
  const isTrade = listing?.listing_type === 'TRADE';
  const seller = listing?.user;
  const similar = listing?.similar_listings || [];

  return (
    <>
      <Dialog open={open} onOpenChange={(o) => { if (!o) handleClose(); }}>
        <DialogContent
          className="sm:max-w-lg max-h-[92vh] overflow-y-auto p-0 gap-0 rounded-2xl [&>button]:hidden"
          data-testid="listing-detail-modal"
          aria-describedby="listing-detail-desc"
        >
          <span id="listing-detail-desc" className="sr-only">Listing detail</span>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-6 h-6 animate-spin text-amber-500" />
            </div>
          ) : listing ? (
            <div>
              {/* Dynamic SEO metadata for this listing */}
              <SEOHead
                title={`${listing.artist} - ${listing.album}${listing.pressing_notes ? ` (${listing.pressing_notes})` : ''}${listing.listing_type === 'TRADE' ? ' For Trade' : listing.price ? ` $${listing.price}` : ''}`}
                description={`${listing.listing_type === 'TRADE' ? `${listing.artist} - ${listing.album} available for trade` : `Buy ${listing.artist} - ${listing.album} for $${listing.price || 'N/A'}`} on The Honey Groove.${listing.pressing_notes ? ` Pressing: ${listing.pressing_notes}.` : ''}${listing.condition ? ` Condition: ${listing.condition}.` : ''}`}
                url={`/honeypot/listing/${listing.id}`}
                image={listing.photo_urls?.[0] || listing.cover_url}
                type="product"
                vinylMeta={{
                  artist: listing.artist,
                  album: listing.album,
                  variant: listing.pressing_notes || listing.color_variant,
                  year: listing.year,
                  format: 'Vinyl',
                }}
                productMeta={{
                  price: listing.price,
                  currency: 'USD',
                  availability: listing.status === 'ACTIVE' ? 'in stock' : 'out of stock',
                  condition: listing.condition,
                }}
                conditionMeta={{
                  mediaCondition: listing.condition,
                  graded: !!listing.condition,
                }}
                tradeMeta={listing.listing_type === 'TRADE' ? {
                  available: true,
                  tradeType: 'swap',
                  negotiable: true,
                  iso: listing.pressing_notes,
                } : undefined}
                jsonLd={{
                  '@context': 'https://schema.org',
                  '@type': 'Product',
                  name: `${listing.artist} - ${listing.album}${listing.pressing_notes ? ` (${listing.pressing_notes})` : ''}`,
                  image: listing.photo_urls?.[0] || listing.cover_url,
                  category: 'Vinyl Record',
                  brand: { '@type': 'MusicGroup', name: listing.artist },
                  url: `https://thehoneygroove.com/honeypot/listing/${listing.id}`,
                  ...(listing.price ? {
                    offers: {
                      '@type': 'Offer',
                      price: String(listing.price),
                      priceCurrency: 'USD',
                      availability: listing.status === 'ACTIVE' ? 'https://schema.org/InStock' : 'https://schema.org/SoldOut',
                      itemCondition: 'https://schema.org/UsedCondition',
                      ...(listing.user && { seller: { '@type': 'Person', name: listing.user.username } }),
                    },
                  } : {}),
                  additionalProperty: [
                    ...(listing.pressing_notes ? [{ '@type': 'PropertyValue', name: 'Variant', value: listing.pressing_notes }] : []),
                    ...(listing.color_variant ? [{ '@type': 'PropertyValue', name: 'Color', value: listing.color_variant }] : []),
                    ...(listing.condition ? [{ '@type': 'PropertyValue', name: 'Condition', value: listing.condition }] : []),
                    ...(listing.year ? [{ '@type': 'PropertyValue', name: 'Release Year', value: String(listing.year) }] : []),
                  ],
                }}
              />
              {/* Close button */}
              <button onClick={handleClose}
                className="absolute top-3 right-3 z-20 bg-black/40 hover:bg-black/60 text-white rounded-full p-1.5 transition-colors"
                data-testid="listing-modal-close">
                <X className="w-5 h-5" />
              </button>

              {/* ========== EDIT MODE ========== */}
              {editing ? (
                <div className="p-6 space-y-4" data-testid="listing-edit-form">
                  <h2 className="font-heading text-xl text-[#2A1A06]">Edit Listing</h2>
                  <p className="text-sm text-muted-foreground">{listing.artist} — {listing.album}</p>

                  {/* Condition */}
                  <div>
                    <label className="text-sm font-medium mb-1.5 block">Condition</label>
                    <Select value={editCondition} onValueChange={setEditCondition}>
                      <SelectTrigger className="border-honey/50" data-testid="edit-condition-select">
                        <SelectValue placeholder="Condition" />
                      </SelectTrigger>
                      <SelectContent>
                        {GRADE_OPTIONS.map(g => <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Pressing / Variant */}
                  <Input placeholder="Pressing / variant notes" value={editPressing} onChange={e => setEditPressing(e.target.value)} className="border-honey/50" data-testid="edit-pressing-input" />

                  {/* Listing Type */}
                  <div>
                    <label className="text-sm font-medium mb-1.5 block">Listing Type</label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { key: 'BUY_NOW', label: 'Buy Now', icon: DollarSign },
                        { key: 'MAKE_OFFER', label: 'Offer', icon: DollarSign },
                        { key: 'TRADE', label: 'Trade', icon: ArrowRightLeft },
                      ].map(t => (
                        <button key={t.key} onClick={() => setEditListingType(t.key)}
                          className={`px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-1 justify-center transition-all ${editListingType === t.key ? 'bg-amber-100/60 text-[#C8861A] ring-2 ring-offset-1 ring-amber-300 shadow-sm' : 'bg-gray-50 text-muted-foreground hover:bg-gray-100'}`}
                          data-testid={`edit-type-${t.key.toLowerCase()}`}>
                          <t.icon className="w-3 h-3" /> {t.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Price & Shipping */}
                  {editListingType !== 'TRADE' && (
                    <div className="space-y-3">
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input placeholder="Price" type="number" value={editPrice} onChange={e => setEditPrice(e.target.value)} className="pl-9 border-honey/50" data-testid="edit-price-input" />
                      </div>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input placeholder="Shipping cost" type="number" value={editShippingCost} onChange={e => setEditShippingCost(e.target.value)} className="pl-9 border-honey/50" data-testid="edit-shipping-input" />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">shipping</span>
                      </div>
                    </div>
                  )}

                  {/* Description */}
                  <Textarea placeholder="Description (optional)" value={editDescription} onChange={e => setEditDescription(e.target.value)} className="border-honey/50 resize-none" rows={3} data-testid="edit-description-input" />

                  {/* Photos */}
                  <div>
                    <label className="text-sm font-medium mb-1.5 block">Photos <span className="text-muted-foreground font-normal">(1-10)</span></label>
                    <div className="grid grid-cols-4 gap-2">
                      {editPhotos.map((photo, idx) => (
                        <div key={idx} className="relative aspect-square rounded-lg overflow-hidden border border-honey/30 group">
                          <img src={photo.preview || resolveImageUrl(photo.url)} alt={`${listing.artist} ${listing.album} vinyl record photo ${idx + 1}`} className="w-full h-full object-cover" />
                          <button onClick={() => removeEditPhoto(idx)} className="absolute top-1 right-1 bg-black/60 rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity" data-testid={`edit-remove-photo-${idx}`}>
                            <X className="w-3 h-3 text-white" />
                          </button>
                          {idx === 0 && <span className="absolute bottom-1 left-1 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded">Cover</span>}
                        </div>
                      ))}
                      {editPhotos.length < 10 && (
                        <label className="aspect-square rounded-lg border-2 border-dashed border-honey/40 flex flex-col items-center justify-center cursor-pointer hover:border-honey hover:bg-honey/5 transition-all" data-testid="edit-add-photo-btn">
                          <Camera className="w-5 h-5 text-honey mb-1" />
                          <span className="text-[10px] text-muted-foreground">{editPhotos.length}/10</span>
                          <input type="file" accept=".jpg,.jpeg,.png,.webp,.heic,.heif" multiple onChange={handleEditPhotoSelect} className="hidden" />
                        </label>
                      )}
                    </div>
                  </div>

                  {/* Insurance & International Shipping */}
                  <div className="space-y-2">
                    <label className="flex items-center gap-2.5 cursor-pointer" data-testid="edit-insured-checkbox">
                      <input type="checkbox" checked={editInsured} onChange={e => setEditInsured(e.target.checked)} className="w-4 h-4 rounded border-honey/50 accent-[#E8A820]" />
                      <span className="text-sm">Shipping insurance</span>
                    </label>
                    <label className="flex items-center gap-2.5 cursor-pointer" data-testid="edit-intl-shipping-checkbox">
                      <input type="checkbox" checked={editIntlShipping} onChange={e => setEditIntlShipping(e.target.checked)} className="w-4 h-4 rounded border-honey/50 accent-[#E8A820]" />
                      <span className="text-sm">Offer International Shipping</span>
                    </label>
                    {editIntlShipping && (
                      <div className="pl-[26px]">
                        <div className="relative">
                          <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                          <Input placeholder="International shipping cost" type="number" value={editIntlShippingCost} onChange={e => setEditIntlShippingCost(e.target.value)} className="pl-9 border-honey/50" data-testid="edit-intl-shipping-cost-input" />
                          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">intl shipping</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Save / Cancel */}
                  <div className="flex gap-2 pt-2">
                    <Button onClick={saveEdits} disabled={saving}
                      className="flex-1 bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="edit-save-btn">
                      {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                      {uploadingPhotos ? 'Uploading photos...' : 'Save Changes'}
                    </Button>
                    <Button onClick={() => setEditing(false)} variant="outline" className="rounded-full border-honey/50" data-testid="edit-cancel-btn">
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                /* ========== VIEW MODE ========== */
                <div>
                  {/* Album Art */}
                  <div className="flex justify-center bg-stone-50 pt-6 pb-4 px-6">
                    <div className="relative max-w-[480px] w-full">
                      <AlbumArt
                        src={photos[0] || listing.cover_url}
                        alt={`${listing.artist} ${listing.album}${listing.pressing_notes || listing.color_variant ? ` ${listing.pressing_notes || listing.color_variant}` : ''} vinyl record`}
                        className="w-full aspect-square object-cover rounded-2xl shadow-lg"
                        data-testid="listing-modal-art"
                      />
                    </div>
                  </div>

                  {/* Record details */}
                  <div className="text-center px-6 pt-3 pb-1" data-testid="listing-modal-info">
                    <h2 className="text-[32px] leading-tight text-[#2A1A06]" style={{ fontFamily: '"Playfair Display", serif', fontWeight: 700 }}>
                      {listing.artist}
                    </h2>
                    <p className="text-[26px] text-[#C8861A] mt-0.5" style={{ fontFamily: '"Cormorant Garamond", serif', fontStyle: 'italic' }}>
                      {listing.album}
                    </p>
                    {(listing.pressing_notes || listing.year) && (
                      <p className="text-[13px] text-[#8A6B4A]/80 mt-1.5 font-medium tracking-wide">
                        {[listing.pressing_notes, listing.year && `${listing.year} pressing`].filter(Boolean).join(' \u00b7 ')}
                      </p>
                    )}
                    {rarityData?.tier && (
                      <div className="mt-2.5" data-testid="listing-rarity-badge">
                        <RarityPill tier={rarityData.tier} size="sm" />
                      </div>
                    )}
                  </div>

                  {/* Edit button for owner */}
                  {canEdit && (
                    <div className="px-6 pb-2">
                      <Button onClick={startEditing} variant="outline" className="w-full rounded-full border-honey/50 text-[#C8861A] hover:bg-honey/10" data-testid="listing-edit-btn">
                        <Pencil className="w-4 h-4 mr-2" /> Edit Listing
                      </Button>
                    </div>
                  )}

                  {/* Condition + Seller row */}
                  <div className="flex items-center justify-between px-6 py-3 border-t border-stone-100" data-testid="listing-modal-seller-row">
                    {listing.condition && (
                      <GradeLabel condition={listing.condition} variant="pill" />
                    )}
                    {seller && (
                      <Link to={`/profile/${seller.username}`} onClick={handleClose}
                        className="flex items-center gap-2 hover:opacity-80 transition-opacity" data-testid="listing-seller-link">
                        <Avatar className="w-7 h-7 border border-amber-200">
                          <AvatarImage src={resolveImageUrl(seller.avatar_url)} />
                          <AvatarFallback className="bg-amber-50 text-xs">{seller.username?.[0]?.toUpperCase()}</AvatarFallback>
                        </Avatar>
                        <div className="text-left">
                          <p className="text-sm font-medium">@{seller.username}</p>
                          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                            <div className="flex">
                              {[1, 2, 3, 4, 5].map(s => (
                                <Star key={s} className={`w-2.5 h-2.5 ${s <= Math.round(seller.rating || 5) ? 'fill-amber-400 text-amber-400' : 'text-stone-300'}`} />
                              ))}
                            </div>
                            <span>· {seller.completed_sales || 0} sales</span>
                          </div>
                        </div>
                      </Link>
                    )}
                  </div>

                  {/* Seller photos */}
                  {photos.length > 0 && (
                    <div className="px-6 py-3 border-t border-stone-100" data-testid="listing-photos">
                      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
                        {photos.map((url, i) => (
                          <button key={i} onClick={() => setExpandedPhoto(i)}
                            className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border border-stone-200 hover:border-amber-300 transition-colors"
                            data-testid={`listing-photo-thumb-${i}`}>
                            <img src={resolveImageUrl(url)} alt={`${listing.artist} ${listing.album} vinyl record photo ${i + 1}`} className="w-full h-full object-cover" />
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Price */}
                  <div className="px-6 pt-6 pb-3" data-testid="listing-price-section">
                    {listing.price && (
                      <p className="text-[52px] leading-none text-[#996012]" style={{ fontFamily: '"Playfair Display", serif', fontWeight: 700 }} data-testid="listing-price">
                        ${listing.price}
                      </p>
                    )}
                    {isMakeOffer && (
                      <p className="text-xs text-muted-foreground mt-2">or make an offer</p>
                    )}
                    {isTrade && (
                      <p className="text-sm font-medium text-purple-600 mt-2">Open to trades</p>
                    )}
                  </div>

                  {/* Honey Pulse */}
                  {pulseData?.confident && listing.price && (
                    <div className="mx-6 mt-2 mb-1 bg-amber-50/70 border border-amber-200/60 rounded-xl p-3" data-testid="honey-pulse-module">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <Flame className="w-4 h-4 text-orange-500" />
                        <span className="text-xs font-bold text-amber-800">Honey Pulse</span>
                        <span className="text-[10px] text-muted-foreground">90-Day Market Signal</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>Median: <span className="font-semibold text-amber-800">${pulseData.median?.toFixed(2)}</span></span>
                        <span>Hot Range: <span className="font-semibold text-amber-800">${pulseData.hot_low?.toFixed(2)} - ${pulseData.hot_high?.toFixed(2)}</span></span>
                      </div>
                      {listing.price >= pulseData.hot_low && listing.price <= pulseData.hot_high ? (
                        <p className="text-xs font-semibold text-orange-600 mt-1.5 flex items-center gap-1" data-testid="pulse-price-signal">
                          <Flame className="w-3 h-3" /> Priced in the Honey Zone
                        </p>
                      ) : listing.price > pulseData.hot_high ? (
                        <p className="text-xs text-muted-foreground mt-1.5" data-testid="pulse-price-signal">Over Market Range</p>
                      ) : (
                        <p className="text-xs text-muted-foreground mt-1.5" data-testid="pulse-price-signal">Below Market Range</p>
                      )}
                    </div>
                  )}

                  {/* Description */}
                  {listing.description && (
                    <div className="px-6 py-3" data-testid="listing-description">
                      <p className={`text-[18px] text-[#8A6B4A] leading-relaxed ${!descExpanded ? 'line-clamp-3' : ''}`}
                        style={{ fontFamily: '"Cormorant Garamond", serif' }}>
                        {listing.description}
                      </p>
                      {listing.description.length > 120 && (
                        <button onClick={() => setDescExpanded(!descExpanded)}
                          className="text-xs text-amber-600 hover:underline mt-1" data-testid="listing-read-more">
                          {descExpanded ? 'Show less' : 'Read more'}
                        </button>
                      )}
                    </div>
                  )}

                  {/* Off-platform payment warning */}
                  {listing.offplatform_flagged && (
                    <div className="mx-6 my-2 bg-yellow-50 border border-yellow-300 rounded-xl px-4 py-3 flex items-start gap-3" data-testid="offplatform-warning">
                      <AlertTriangle className="w-5 h-5 text-yellow-600 shrink-0 mt-0.5" />
                      <p className="text-sm text-yellow-800">
                        This listing mentions an outside payment method. Never pay outside the Honey Groove. All legitimate transactions happen inside the app through Stripe only.
                      </p>
                    </div>
                  )}

                  {/* Shipping insurance indicator */}
                  {listing.insured !== null && listing.insured !== undefined && (
                    <div className="px-6 py-2" data-testid="listing-insurance-status">
                      {listing.insured ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 px-3 py-1.5 rounded-full">
                          <Package className="w-3.5 h-3.5" /> Seller added shipping insurance
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-full">
                          <Package className="w-3.5 h-3.5" /> No shipping insurance
                        </span>
                      )}
                    </div>
                  )}

                  {/* Shipping costs */}
                  {listing.shipping_cost != null && (
                    <div className="px-6 py-1" data-testid="listing-domestic-shipping">
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-stone-600 bg-stone-50 border border-stone-200 px-3 py-1.5 rounded-full">
                        <Package className="w-3.5 h-3.5" /> Shipping: ${listing.shipping_cost.toFixed(2)}{listing.international_shipping ? ' (Domestic)' : ''}
                      </span>
                    </div>
                  )}

                  {/* International shipping indicator */}
                  {listing.international_shipping ? (
                    <div className="px-6 py-1 space-y-1" data-testid="listing-intl-shipping">
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-full">
                        <Package className="w-3.5 h-3.5" /> International Shipping: {listing.international_shipping_cost ? `$${listing.international_shipping_cost.toFixed(2)}` : 'Available'}
                      </span>
                    </div>
                  ) : (
                    <div className="px-6 py-1" data-testid="listing-no-intl-shipping">
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-stone-500 bg-stone-50 border border-stone-200 px-3 py-1.5 rounded-full">
                        <Package className="w-3.5 h-3.5" /> International Shipping: Not Available
                      </span>
                    </div>
                  )}

                  {/* Shipping info */}
                  {seller && (seller.city || seller.region) && (
                    <div className="px-6 py-2 text-xs text-muted-foreground" data-testid="listing-shipping">
                      Ships from {[seller.city, seller.region].filter(Boolean).join(', ')}
                    </div>
                  )}

                  {/* Domestic-only shipping warning */}
                  {!isOwn && !listing.international_shipping && seller?.country && currentUser?.country && seller.country !== currentUser.country && (
                    <div className="mx-6 mt-2 px-3 py-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-start gap-2" data-testid="domestic-only-warning">
                      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                      <span>This seller only ships domestically ({seller.country}). International shipping is not available for this listing.</span>
                    </div>
                  )}

                  {/* CTA buttons */}
                  {!isOwn && (
                    <div className="px-6 pt-4 pb-3 space-y-2.5" data-testid="listing-cta-section">
                      {isBuyNow && (
                        <Button onClick={handleBuyNowClick}
                          className="w-full h-12 rounded-full bg-[#E8A820] hover:bg-[#d49a1a] text-[#2A1A06] text-base font-semibold shadow-md shadow-amber-200/40 active:scale-[0.97] transition-all duration-150"
                          data-testid="listing-buy-now-btn">
                          buy now · ${listing.price}
                        </Button>
                      )}
                      {isMakeOffer && !showOfferInput && (
                        <>
                          <Button onClick={handleBuyNowClick}
                            className="w-full h-12 rounded-full bg-[#E8A820] hover:bg-[#d49a1a] text-[#2A1A06] text-base font-semibold shadow-md shadow-amber-200/40 active:scale-[0.97] transition-all duration-150"
                            data-testid="listing-buy-asking-btn">
                            buy now · ${listing.price}
                          </Button>
                          <Button onClick={() => setShowOfferInput(true)} variant="outline"
                            className="w-full h-11 rounded-full border-[#E8A820]/60 text-[#996012] hover:bg-amber-50/60 text-sm font-medium active:scale-[0.97] transition-all duration-150"
                            data-testid="listing-make-offer-btn">
                            make an offer
                          </Button>
                        </>
                      )}
                      {isMakeOffer && showOfferInput && (
                        <div className="space-y-2">
                          <div className="flex gap-2">
                            <div className="relative flex-1">
                              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                              <Input type="number" placeholder="Your offer" value={offerAmount}
                                onChange={(e) => setOfferAmount(e.target.value)}
                                className="pl-8 border-amber-300" autoFocus
                                data-testid="listing-offer-input" />
                            </div>
                            <Button onClick={handleOfferSubmit} disabled={!offerAmount}
                              className="bg-[#E8A820] hover:bg-[#d49a1a] text-[#2A1A06] rounded-full px-6"
                              data-testid="listing-submit-offer-btn">
                              send
                            </Button>
                          </div>
                          <button onClick={() => setShowOfferInput(false)} className="text-xs text-muted-foreground hover:text-stone-600">cancel</button>
                        </div>
                      )}
                      {isTrade && (
                        <Button onClick={handleTradeClick}
                          className="w-full h-12 rounded-full bg-[#E8A820] hover:bg-[#d49a1a] text-[#2A1A06] text-base font-semibold shadow-md shadow-amber-200/40 active:scale-[0.97] transition-all duration-150"
                          data-testid="listing-trade-btn">
                          propose a trade
                        </Button>
                      )}
                      {!isTrade && onProposeTrade && (
                        <Button onClick={handleTradeClick} variant="outline"
                          className="w-full h-10 rounded-full border-amber-300/60 text-[#996012] hover:bg-amber-50/60 text-sm active:scale-[0.97] transition-all duration-150"
                          data-testid="listing-trade-instead-btn">
                          <ArrowRightLeft className="w-4 h-4 mr-2" />
                          propose a trade instead
                        </Button>
                      )}
                    </div>
                  )}

                  {/* Secured by Stripe */}
                  {!isOwn && (listing.price || listing.listing_type === 'TRADE') && (
                    <div className="text-center py-2" data-testid="stripe-trust-badge">
                      <span className="text-[11px] text-muted-foreground/60 inline-flex items-center gap-1.5">
                        <svg width="28" height="12" viewBox="0 0 28 12" fill="none" className="opacity-40">
                          <path d="M13.3 3.4c0-.6.5-.8 1.3-.8.9 0 2.1.3 3 .8V.6c-1-.4-2-.6-3-.6C12.4 0 11 1.2 11 3.2c0 3.1 4.3 2.6 4.3 4 0 .7-.6.9-1.4.9-1.2 0-2.7-.5-3.8-1.2v2.8c1.3.6 2.6.8 3.8.8 2.3 0 3.8-1.1 3.8-3.2-.1-3.3-4.4-2.8-4.4-3.9zM7.5 5L6.3 4.5c-.5-.2-.6-.4-.6-.6 0-.3.3-.4.7-.4.6 0 1.2.2 1.8.5l.7-2A5 5 0 007 1.5C5.6 1.5 4.5 2.3 4.5 3.6c0 .8.5 1.5 1.2 1.8l1.1.5c.5.2.6.4.6.7 0 .3-.3.5-.8.5-.7 0-1.4-.3-2.1-.7l-.7 2c.9.5 1.8.7 2.8.7C8 9.1 9 8.2 9 6.9 9 6 8.4 5.4 7.5 5zm11.3-3.5h-2l.01 6.6c0 1.9 1 2.7 2.3 2.7.7 0 1.3-.1 1.8-.4V8.1c-.3.1-.9.3-1.3.3-.6 0-1-.2-1-1V4h1.3V1.6h-1.1zm5 0l-.2 1.2h-.01V1.6h-2.5v8.1h2.6V4.8c.6-.8 1.7-.7 2-.6V1.6c-.4-.2-1.6-.3-2.1.9zm2.8-1.8L24 .5v2.7h-1.3V5.5H24v3.2c0 1.6.8 2.3 2 2.3.6 0 1.1-.1 1.5-.3V8.4c-.3.1-.6.2-1 .2-.4 0-.7-.2-.7-.8V5.5h1.7V3.2h-1.7V-.3z" fill="currentColor"/>
                        </svg>
                        Secured by Stripe
                      </span>
                    </div>
                  )}
                  {!isOwn && (
                    <div className="px-6 py-2 text-center" data-testid="listing-wantlist-section">
                      <button onClick={toggleWantlist} disabled={wantlistLoading}
                        className={`text-xs transition-colors ${onWantlist ? 'text-green-600' : 'text-amber-600 hover:text-amber-700'}`}
                        data-testid="listing-wantlist-toggle">
                        {wantlistLoading ? <Loader2 className="w-3 h-3 animate-spin inline mr-1" /> : null}
                        {onWantlist ? (
                          <span className="flex items-center justify-center gap-1"><Check className="w-3 h-3" /> on your Dream List</span>
                        ) : 'add to Dream List'}
                      </button>
                    </div>
                  )}
                  {!isOwn && (
                    <div className="px-6 py-1 text-center">
                      <button
                        type="button"
                        onClick={() => setReportOpen(true)}
                        className="text-[11px] text-muted-foreground/60 hover:text-red-500 transition-colors inline-flex items-center gap-1"
                        data-testid="report-listing-btn"
                      >
                        <Flag className="w-3 h-3" /> Report Listing
                      </button>
                    </div>
                  )}

                  {/* Similar listings */}
                  {similar.length > 0 && (
                    <div className="px-6 pt-3 pb-5 border-t border-stone-100" data-testid="listing-similar">
                      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-2">more like this</p>
                      <div className="flex gap-3 overflow-x-auto pb-1 -mx-1 px-1">
                        {similar.map(s => (
                          <button key={s.id} onClick={() => { setListing(null); setLoading(true); }}
                            className="flex-shrink-0 w-28 text-left" data-testid={`similar-listing-${s.id}`}>
                            <div className="w-28 h-28 rounded-lg overflow-hidden bg-stone-100 mb-1">
                              <AlbumArt src={s.cover_url} alt={`${s.artist} ${s.album} vinyl record`} className="w-full h-full object-cover" />
                            </div>
                            <p className="text-xs font-medium truncate">{s.album}</p>
                            <p className="text-[10px] text-muted-foreground truncate">{s.price ? `$${s.price}` : 'Trade'}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Photo Lightbox */}
      <PhotoLightbox
        photos={photos}
        initialIndex={typeof expandedPhoto === 'number' ? expandedPhoto : 0}
        open={expandedPhoto !== null}
        onClose={() => setExpandedPhoto(null)}
      />

      {/* Report Modal */}
      <ReportModal
        open={reportOpen}
        onOpenChange={setReportOpen}
        targetType="listing"
        targetId={listingId}
      />
    </>
  );
};

export default ListingDetailModal;
