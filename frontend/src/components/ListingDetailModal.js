import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { X, Star, Loader2, ChevronLeft, ChevronRight, DollarSign, ArrowRightLeft, Disc, Check, Heart, AlertTriangle, Package } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import AlbumArt from './AlbumArt';

const CONDITION_MAP = {
  'Mint': 'bg-emerald-100 text-emerald-800 border-emerald-200',
  'Near Mint': 'bg-green-100 text-green-700 border-green-200',
  'Very Good Plus': 'bg-lime-100 text-lime-700 border-lime-200',
  'Very Good': 'bg-amber-100 text-amber-700 border-amber-200',
  'Good': 'bg-orange-100 text-orange-700 border-orange-200',
};

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

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchListing = useCallback(async () => {
    if (!listingId) return;
    setLoading(true);
    try {
      const r = await axios.get(`${API}/listings/${listingId}`, { headers });
      setListing(r.data);
      setOnWantlist(r.data.on_wantlist || false);
      setPhotoIdx(0);
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
  useEffect(() => {
    if (open && listingId) {
      window.history.pushState({ modal: true }, '', `/honeypot/listing/${listingId}`);
    }
    const handlePop = () => { onClose(); };
    window.addEventListener('popstate', handlePop);
    return () => window.removeEventListener('popstate', handlePop);
  }, [open, listingId, onClose]);

  const handleClose = () => {
    if (window.history.state?.modal) {
      window.history.back();
    } else {
      onClose();
    }
  };

  const toggleWantlist = async () => {
    if (!listing) return;
    setWantlistLoading(true);
    try {
      if (onWantlist) {
        // Find and remove the ISO
        const isos = await axios.get(`${API}/iso`, { headers: { Authorization: `Bearer ${token}` } });
        const match = isos.data?.find(i =>
          i.artist?.toLowerCase() === listing.artist?.toLowerCase() &&
          i.album?.toLowerCase() === listing.album?.toLowerCase()
        );
        if (match) {
          await axios.delete(`${API}/iso/${match.id}`, { headers: { Authorization: `Bearer ${token}` } });
        }
        setOnWantlist(false);
        toast.success('removed from wantlist.');
      } else {
        await axios.post(`${API}/composer/iso`, {
          artist: listing.artist, album: listing.album,
          discogs_id: listing.discogs_id, cover_url: listing.cover_url,
          year: listing.year,
        }, { headers: { Authorization: `Bearer ${token}` } });
        setOnWantlist(true);
        trackEvent('wantlist_added');
        toast.success('added to wantlist.');
      }
    } catch (err) {
      if (err.response?.status === 409) { setOnWantlist(true); toast.info('already on your wantlist.'); }
      else toast.error('something went wrong.');
    } finally {
      setWantlistLoading(false);
    }
  };

  const handleBuyNowClick = () => {
    if (listing && onBuyNow) {
      handleClose();
      onBuyNow(listing);
    }
  };

  const handleOfferSubmit = () => {
    if (!offerAmount || !listing) return;
    handleClose();
    if (onMakeOffer) onMakeOffer(listing, parseFloat(offerAmount));
  };

  const handleTradeClick = () => {
    if (listing && onProposeTrade) {
      handleClose();
      onProposeTrade(listing);
    }
  };

  const photos = listing?.photo_urls || [];
  const isOwn = listing?.user_id === currentUser?.id || listing?.user?.id === currentUser?.id;
  const isBuyNow = listing?.listing_type === 'BUY_NOW';
  const isMakeOffer = listing?.listing_type === 'MAKE_OFFER';
  const isTrade = listing?.listing_type === 'TRADE';
  const condClass = listing?.condition ? (CONDITION_MAP[listing.condition] || 'bg-stone-100 text-stone-600 border-stone-200') : '';
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
              {/* Close button */}
              <button onClick={handleClose}
                className="absolute top-3 right-3 z-20 bg-black/40 hover:bg-black/60 text-white rounded-full p-1.5 transition-colors"
                data-testid="listing-modal-close">
                <X className="w-5 h-5" />
              </button>

              {/* Album Art */}
              <div className="flex justify-center bg-stone-50 pt-6 pb-4 px-6">
                <div className="relative max-w-[480px] w-full">
                  <AlbumArt
                    src={listing.cover_url || photos[0]}
                    alt={listing.album}
                    className="w-full aspect-square object-cover rounded-2xl shadow-lg"
                    data-testid="listing-modal-art"
                  />
                </div>
              </div>

              {/* Record details */}
              <div className="text-center px-6 pt-2 pb-3" data-testid="listing-modal-info">
                <h2 className="text-[32px] leading-tight text-[#2A1A06]" style={{ fontFamily: '"Playfair Display", serif', fontWeight: 700 }}>
                  {listing.artist}
                </h2>
                <p className="text-[26px] text-[#C8861A] mt-0.5" style={{ fontFamily: '"Cormorant Garamond", serif', fontStyle: 'italic' }}>
                  {listing.album}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {[listing.year, listing.pressing_notes].filter(Boolean).join(' · ')}
                </p>
              </div>

              {/* Condition + Seller row */}
              <div className="flex items-center justify-between px-6 py-3 border-t border-stone-100" data-testid="listing-modal-seller-row">
                {listing.condition && (
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${condClass}`} data-testid="listing-condition-pill">
                    {listing.condition}
                  </span>
                )}
                {seller && (
                  <Link to={`/profile/${seller.username}`} onClick={handleClose}
                    className="flex items-center gap-2 hover:opacity-80 transition-opacity" data-testid="listing-seller-link">
                    <Avatar className="w-7 h-7 border border-amber-200">
                      <AvatarImage src={seller.avatar_url} />
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
                      <button key={i} onClick={() => setExpandedPhoto(url)}
                        className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border border-stone-200 hover:border-amber-300 transition-colors"
                        data-testid={`listing-photo-thumb-${i}`}>
                        <img src={url} alt="" className="w-full h-full object-cover" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Price */}
              <div className="px-6 pt-4 pb-1" data-testid="listing-price-section">
                {listing.price && (
                  <p className="text-[52px] leading-none text-[#996012]" style={{ fontFamily: '"Playfair Display", serif', fontWeight: 700 }} data-testid="listing-price">
                    ${listing.price}
                  </p>
                )}
                {isMakeOffer && (
                  <p className="text-xs text-muted-foreground mt-1">or make an offer</p>
                )}
                {isTrade && (
                  <p className="text-sm font-medium text-purple-600 mt-1">Open to trades</p>
                )}
              </div>

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

              {/* Shipping info */}
              {seller && (seller.city || seller.region) && (
                <div className="px-6 py-2 text-xs text-muted-foreground" data-testid="listing-shipping">
                  Ships from {[seller.city, seller.region].filter(Boolean).join(', ')}
                </div>
              )}

              {/* CTA buttons */}
              {!isOwn && (
                <div className="px-6 pt-3 pb-2 space-y-2" data-testid="listing-cta-section">
                  {isBuyNow && (
                    <Button onClick={handleBuyNowClick}
                      className="w-full h-12 rounded-full bg-[#E8A820] hover:bg-[#d49a1a] text-[#2A1A06] text-base font-semibold"
                      data-testid="listing-buy-now-btn">
                      buy now — ${listing.price}
                    </Button>
                  )}
                  {isMakeOffer && !showOfferInput && (
                    <>
                      <Button onClick={() => setShowOfferInput(true)}
                        className="w-full h-12 rounded-full bg-[#E8A820] hover:bg-[#d49a1a] text-[#2A1A06] text-base font-semibold"
                        data-testid="listing-make-offer-btn">
                        make an offer
                      </Button>
                      <Button onClick={handleBuyNowClick} variant="outline"
                        className="w-full h-12 rounded-full border-[#E8A820] text-[#996012] hover:bg-amber-50 text-base"
                        data-testid="listing-buy-asking-btn">
                        buy at asking price — ${listing.price}
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
                      className="w-full h-12 rounded-full bg-[#E8A820] hover:bg-[#d49a1a] text-[#2A1A06] text-base font-semibold"
                      data-testid="listing-trade-btn">
                      propose a trade
                    </Button>
                  )}
                  {/* Trade option for Buy/Offer listings too */}
                  {!isTrade && onProposeTrade && (
                    <Button onClick={handleTradeClick} variant="outline"
                      className="w-full h-11 rounded-full border-amber-300 text-[#996012] hover:bg-amber-50 text-sm"
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
                      <span className="flex items-center justify-center gap-1"><Check className="w-3 h-3" /> on your wantlist</span>
                    ) : 'add to wantlist'}
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
                          <AlbumArt src={s.cover_url} alt="" className="w-full h-full object-cover" />
                        </div>
                        <p className="text-xs font-medium truncate">{s.album}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{s.price ? `$${s.price}` : 'Trade'}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Expanded photo overlay */}
      {expandedPhoto && (
        <div className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center"
          onClick={() => setExpandedPhoto(null)} data-testid="listing-photo-expanded">
          <button onClick={() => setExpandedPhoto(null)}
            className="absolute top-4 right-4 text-white/80 hover:text-white">
            <X className="w-8 h-8" />
          </button>
          <img src={expandedPhoto} alt="" className="max-w-[90vw] max-h-[90vh] object-contain rounded-lg" />
        </div>
      )}
    </>
  );
};

export default ListingDetailModal;
