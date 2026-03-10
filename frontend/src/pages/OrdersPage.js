import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { ShoppingBag, Package, Truck, CheckCircle2, Clock, XCircle, Loader2, MessageCircle, Ban, ChevronDown, ChevronUp, Disc, Flag, Star } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';
import { usePageTitle } from '../hooks/usePageTitle';
import { GradeLabel } from '../components/GradeLabel';
import { formatGradeDisplay } from '../utils/grading';
import ReportModal from '../components/ReportModal';

const STATUS_BADGE = {
  PAID: { label: 'Paid', color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
  PENDING: { label: 'Pending', color: 'bg-amber-100 text-amber-700', icon: Clock },
  FAILED: { label: 'Failed', color: 'bg-red-100 text-red-700', icon: XCircle },
  EXPIRED: { label: 'Expired', color: 'bg-stone-100 text-stone-500', icon: XCircle },
  CANCELLED: { label: 'Cancelled', color: 'bg-red-50 text-red-500', icon: Ban },
};

const SHIPPING_BADGE = {
  NOT_SHIPPED: { label: 'Not Shipped', color: 'bg-stone-100 text-stone-600' },
  SHIPPED: { label: 'Shipped', color: 'bg-blue-100 text-blue-700' },
  DELIVERED: { label: 'Delivered', color: 'bg-green-100 text-green-700' },
};

const PaymentBadge = ({ status }) => {
  const s = STATUS_BADGE[status] || STATUS_BADGE.PENDING;
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`} data-testid={`payment-status-${status}`}>
      <Icon className="w-3 h-3" /> {s.label}
    </span>
  );
};

const ShippingBadge = ({ status }) => {
  const s = SHIPPING_BADGE[status] || SHIPPING_BADGE.NOT_SHIPPED;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`} data-testid={`shipping-status-${status}`}>
      {status === 'SHIPPED' && <Truck className="w-3 h-3" />}
      {status === 'DELIVERED' && <CheckCircle2 className="w-3 h-3" />}
      {status === 'NOT_SHIPPED' && <Package className="w-3 h-3" />}
      {s.label}
    </span>
  );
};

// Inline shipping editor for sellers
const ShippingEditor = ({ order, token, API, onUpdate }) => {
  const [editing, setEditing] = useState(false);
  const [status, setStatus] = useState(order.shipping_status || 'NOT_SHIPPED');
  const [tracking, setTracking] = useState(order.tracking_number || '');
  const [carrier, setCarrier] = useState(order.shipping_carrier || '');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/orders/${order.id}/shipping`, {
        shipping_status: status, tracking_number: tracking || null, shipping_carrier: carrier || null,
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('shipping updated!');
      onUpdate({ ...order, shipping_status: status, tracking_number: tracking, shipping_carrier: carrier });
      setEditing(false);
    } catch { toast.error('could not update shipping.'); }
    finally { setSaving(false); }
  };

  if (!editing) {
    return (
      <div className="flex items-center gap-2 flex-wrap">
        <ShippingBadge status={order.shipping_status || 'NOT_SHIPPED'} />
        {order.tracking_number && <span className="text-xs text-muted-foreground">#{order.tracking_number}</span>}
        {order.payment_status === 'PAID' && order.shipping_status !== 'DELIVERED' && (
          <button onClick={() => setEditing(true)} className="text-xs text-honey-amber hover:underline" data-testid={`edit-shipping-${order.id}`}>
            update
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2 bg-honey/5 rounded-lg p-3" data-testid={`shipping-editor-${order.id}`}>
      <div className="flex gap-2">
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="h-8 text-xs w-36" data-testid="shipping-status-select">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="NOT_SHIPPED">Not Shipped</SelectItem>
            <SelectItem value="SHIPPED">Shipped</SelectItem>
            <SelectItem value="DELIVERED">Delivered</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="flex gap-2 flex-wrap">
        <Input placeholder="carrier (e.g. USPS)" value={carrier} onChange={e => setCarrier(e.target.value)}
          className="h-8 text-xs flex-1 min-w-[100px]" data-testid="shipping-carrier-input" />
        <Input placeholder="tracking #" value={tracking} onChange={e => setTracking(e.target.value)}
          className="h-8 text-xs flex-1 min-w-[100px]" data-testid="shipping-tracking-input" />
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={save} disabled={saving} className="bg-honey text-vinyl-black hover:bg-honey-amber h-7 text-xs rounded-full" data-testid="save-shipping-btn">
          {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Save'}
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setEditing(false)} className="h-7 text-xs">Cancel</Button>
      </div>
    </div>
  );
};

// Countdown helper
const formatRatingCountdown = (deadline) => {
  if (!deadline) return null;
  const diff = new Date(deadline) - new Date();
  if (diff <= 0) return null;
  const hrs = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  return hrs > 0 ? `${hrs}h ${mins}m left to rate` : `${mins}m left to rate`;
};

// Rating section for delivered orders
const RatingSection = ({ order, perspective, token, API, onUpdate }) => {
  const [stars, setStars] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const myRating = perspective === 'buyer' ? order.buyer_rating : order.seller_rating;
  const theirRating = perspective === 'buyer' ? order.seller_rating : order.buyer_rating;
  const countdown = formatRatingCountdown(order.rating_deadline);
  const isExpired = order.rating_deadline && new Date(order.rating_deadline) < new Date();

  if (myRating) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-3 space-y-1" data-testid="my-rating-display">
        <p className="text-xs font-medium text-green-700">Your Rating</p>
        <div className="flex items-center gap-1">
          {[1,2,3,4,5].map(i => (
            <Star key={i} className={`w-4 h-4 ${i <= myRating.stars ? 'text-amber-400 fill-amber-400' : 'text-stone-200'}`} />
          ))}
        </div>
        {myRating.comment && <p className="text-xs text-green-600">{myRating.comment}</p>}
      </div>
    );
  }

  if (isExpired) {
    return (
      <div className="bg-stone-50 border border-stone-200 rounded-xl p-3" data-testid="rating-expired">
        <p className="text-xs text-muted-foreground">Rating window expired. No rating was left.</p>
      </div>
    );
  }

  const submit = async () => {
    if (!stars) { toast.error('Select a star rating'); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/orders/${order.id}/rate`, { stars, comment }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Rating submitted!');
      onUpdate({ ...order, [`${perspective}_rating`]: { stars, comment, rated_at: new Date().toISOString() } });
    } catch (err) { toast.error(err.response?.data?.detail || 'Could not submit rating'); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-2.5" data-testid="rating-form">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-amber-700">
          Rate the {perspective === 'buyer' ? 'seller' : 'buyer'}
        </p>
        {countdown && (
          <span className="text-[10px] text-amber-600 flex items-center gap-1">
            <Clock className="w-3 h-3" /> {countdown}
          </span>
        )}
      </div>
      <div className="flex items-center gap-1" data-testid="star-rating-input">
        {[1,2,3,4,5].map(i => (
          <button key={i} onClick={() => setStars(i)} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(0)}
            className="transition-transform hover:scale-110" data-testid={`star-${i}`}>
            <Star className={`w-6 h-6 ${i <= (hover || stars) ? 'text-amber-400 fill-amber-400' : 'text-stone-200'}`} />
          </button>
        ))}
      </div>
      <Input placeholder="Optional comment..." value={comment} onChange={e => setComment(e.target.value)}
        className="h-8 text-xs border-amber-200" data-testid="rating-comment-input" />
      <Button size="sm" onClick={submit} disabled={submitting || !stars}
        className="bg-honey text-vinyl-black hover:bg-honey-amber h-7 text-xs rounded-full w-full" data-testid="submit-rating-btn">
        {submitting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Star className="w-3 h-3 mr-1" />}
        Submit Rating
      </Button>
      {theirRating && (
        <div className="pt-1 border-t border-amber-200/50">
          <p className="text-[10px] text-amber-600">
            The {perspective === 'buyer' ? 'seller' : 'buyer'} rated you {theirRating.stars} stars
          </p>
        </div>
      )}
    </div>
  );
};

// Order row
const OrderRow = ({ order, perspective, token, API, onUpdate, onCancel }) => {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const [orderReportOpen, setOrderReportOpen] = useState(false);
  const counterparty = order.counterparty || {};
  const timeAgo = order.created_at ? formatDistanceToNow(new Date(order.created_at), { addSuffix: true }) : '';
  const isCancelled = order.payment_status === 'CANCELLED';
  const isSale = perspective === 'seller';
  const photos = order.photo_urls || [];

  return (
    <Card className={`border-honey/20 overflow-hidden ${isCancelled ? 'opacity-60' : ''}`} data-testid={`order-row-${order.id}`}>
      <CardContent className="p-0 overflow-hidden">
        {/* Clickable header */}
        <button
          onClick={() => setExpanded(prev => !prev)}
          className="w-full p-4 text-left hover:bg-honey/5 transition-colors"
          data-testid={`order-toggle-${order.id}`}
        >
          <div className="flex gap-4 items-start min-w-0">
            {/* Album art */}
            <div className="w-16 h-16 rounded-lg overflow-hidden bg-honey/10 shrink-0">
              {order.cover_url ? (
                <AlbumArt src={order.cover_url} alt={`${order.album || 'Album'} by ${order.artist || 'Artist'}`} className="w-full h-full" />
              ) : (
                <div className="w-full h-full flex items-center justify-center"><Package className="w-6 h-6 text-honey/40" /></div>
              )}
            </div>

            {/* Details */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="min-w-0">
                  <p className="font-heading text-sm leading-tight truncate" data-testid="order-album">{order.album || 'Unknown Album'}</p>
                  <p className="text-xs text-muted-foreground truncate">{order.artist}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-sm font-heading text-honey-amber" data-testid="order-amount">${order.amount?.toFixed(2)}</span>
                  {expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
                </div>
              </div>

              {/* Order meta */}
              <div className="flex items-center gap-2 flex-wrap text-xs text-muted-foreground mb-2">
                <span className="font-mono text-[10px] bg-stone-100 px-1.5 py-0.5 rounded" data-testid="order-number">{order.order_number?.startsWith('HONEY-') ? order.order_number : `#${order.order_number}`}</span>
                <span>{timeAgo}</span>
                {counterparty.username && (
                  <span className="text-honey-amber" data-testid="order-counterparty">
                    @{counterparty.username}
                  </span>
                )}
                {order.condition && <span className="text-stone-400">{formatGradeDisplay(order.condition)}</span>}
              </div>

              {/* Status badges */}
              <div className="flex items-center gap-2 flex-wrap">
                <PaymentBadge status={order.payment_status} />
                {!isCancelled && !isSale && (
                  <>
                    <ShippingBadge status={order.shipping_status || 'NOT_SHIPPED'} />
                    {order.tracking_number && (
                      <span className="text-xs text-muted-foreground">
                        {order.shipping_carrier && `${order.shipping_carrier}: `}#{order.tracking_number}
                      </span>
                    )}
                  </>
                )}
                {!isCancelled && isSale && !expanded && (
                  <ShippingBadge status={order.shipping_status || 'NOT_SHIPPED'} />
                )}
              </div>
            </div>
          </div>
        </button>

        {/* Expanded detail */}
        {expanded && (
          <div className="border-t border-honey/10 p-4 pt-3 space-y-4 bg-honey/5 animate-in slide-in-from-top-2 duration-200" data-testid={`order-detail-${order.id}`}>
            {/* Full listing info */}
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
              {order.album && (
                <div>
                  <span className="text-xs text-muted-foreground">Album</span>
                  <p className="font-medium text-vinyl-black">{order.album}</p>
                </div>
              )}
              {order.artist && (
                <div>
                  <span className="text-xs text-muted-foreground">Artist</span>
                  <p className="font-medium text-vinyl-black">{order.artist}</p>
                </div>
              )}
              {order.condition && (
                <div>
                  <span className="text-xs text-muted-foreground">Condition</span>
                  <div className="mt-0.5"><GradeLabel condition={order.condition} variant="pill" /></div>
                </div>
              )}
              {order.pressing_variant && (
                <div>
                  <span className="text-xs text-muted-foreground">Pressing / Variant</span>
                  <p className="font-medium text-vinyl-black">{order.pressing_variant}</p>
                </div>
              )}
              {order.year && (
                <div>
                  <span className="text-xs text-muted-foreground">Year</span>
                  <p className="font-medium text-vinyl-black">{order.year}</p>
                </div>
              )}
              {order.listing_price != null && (
                <div>
                  <span className="text-xs text-muted-foreground">Listed Price</span>
                  <p className="font-medium text-vinyl-black">${Number(order.listing_price).toFixed(2)}</p>
                </div>
              )}
              {order.listing_type && (
                <div>
                  <span className="text-xs text-muted-foreground">Listing Type</span>
                  <p className="font-medium text-vinyl-black capitalize">{order.listing_type.replace('_', ' ')}</p>
                </div>
              )}
              {counterparty.username && (
                <div>
                  <span className="text-xs text-muted-foreground">{isSale ? 'Buyer' : 'Seller'}</span>
                  <Link to={`/profile/${counterparty.username}`} className="font-medium text-honey-amber hover:underline block" data-testid="order-detail-counterparty">
                    @{counterparty.username}
                  </Link>
                </div>
              )}
            </div>

            {/* Payout Status (for sellers) */}
            {isSale && order.payout_status && (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-muted-foreground">Payout:</span>
                <span className={`px-2 py-0.5 rounded-full font-medium ${
                  order.payout_status === 'RELEASED' ? 'bg-emerald-100 text-emerald-700' :
                  order.payout_status === 'PENDING' ? 'bg-amber-100 text-amber-700' :
                  'bg-stone-100 text-stone-600'
                }`} data-testid="payout-status-badge">
                  {order.payout_status === 'RELEASED' ? 'Released' : order.payout_status === 'PENDING' ? 'Pending (auto-release after delivery)' : order.payout_status}
                </span>
              </div>
            )}

            {/* Description */}
            {order.description && (
              <div>
                <span className="text-xs text-muted-foreground">Description</span>
                <p className="text-sm text-vinyl-black mt-0.5">{order.description}</p>
              </div>
            )}

            {/* Photos */}
            {photos.length > 0 && (
              <div>
                <span className="text-xs text-muted-foreground block mb-2">Photos</span>
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {photos.map((url, i) => (
                    <div key={i} className="w-20 h-20 rounded-lg overflow-hidden bg-honey/10 shrink-0">
                      <AlbumArt src={url} alt={`Photo ${i + 1}`} className="w-full h-full object-cover" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Shipping editor for sellers / tracking for buyers */}
            {!isCancelled && isSale && (
              <div>
                <span className="text-xs text-muted-foreground block mb-1">Shipping</span>
                <ShippingEditor order={order} token={token} API={API} onUpdate={onUpdate} />
              </div>
            )}

            {/* Rating section — show for delivered orders */}
            {!isCancelled && order.shipping_status === 'DELIVERED' && (
              <RatingSection order={order} perspective={isSale ? 'seller' : 'buyer'} token={token} API={API} onUpdate={onUpdate} />
            )}

            {/* Completed status */}
            {order.order_status === 'COMPLETED' && (
              <div className="flex items-center gap-2 text-xs text-green-600" data-testid="order-completed-badge">
                <CheckCircle2 className="w-4 h-4" />
                <span className="font-medium">Transaction Complete</span>
              </div>
            )}

            {/* Cancel / DM actions */}
            {!isCancelled && (
              <div className="pt-2 border-t border-honey/10 flex items-center gap-3">
                {isSale && (order.payment_status === 'PAID' || order.payment_status === 'PENDING') && order.shipping_status !== 'DELIVERED' && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onCancel(order); }}
                    className="text-xs text-red-500 hover:text-red-700 hover:underline transition-colors"
                    data-testid={`cancel-order-${order.id}`}
                  >
                    Cancel Order
                  </button>
                )}
                {!isSale && order.payment_status === 'PAID' && (
                  <button
                    onClick={(e) => { e.stopPropagation(); navigate(`/messages?to=${order.seller_id}`); }}
                    className="text-xs text-muted-foreground hover:text-honey-amber transition-colors flex items-center gap-1"
                    data-testid={`dm-seller-${order.id}`}
                  >
                    <MessageCircle className="w-3 h-3" /> Message {isSale ? 'buyer' : 'seller'}
                  </button>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); setOrderReportOpen(true); }}
                  className="text-xs text-muted-foreground/60 hover:text-red-500 transition-colors flex items-center gap-1 ml-auto"
                  data-testid={`report-order-${order.id}`}
                >
                  <Flag className="w-3 h-3" /> Report Issue
                </button>
              </div>
            )}
          </div>
        )}
      </CardContent>
      <ReportModal open={orderReportOpen} onOpenChange={setOrderReportOpen} targetType="order" targetId={order.id} />
    </Card>
  );
};

const OrdersPage = () => {
  usePageTitle('Orders');
  const { user, token, API } = useAuth();
  const [purchases, setPurchases] = useState([]);
  const [sales, setSales] = useState([]);
  const [loadingPurchases, setLoadingPurchases] = useState(true);
  const [loadingSales, setLoadingSales] = useState(true);
  const [cancelTarget, setCancelTarget] = useState(null);
  const [cancelling, setCancelling] = useState(false);
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${API}/orders/purchases`, { headers }).then(r => setPurchases(r.data)).catch(() => {}).finally(() => setLoadingPurchases(false));
    axios.get(`${API}/orders/sales`, { headers }).then(r => setSales(r.data)).catch(() => {}).finally(() => setLoadingSales(false));
  }, [API, token]);

  const updateSale = (updated) => {
    setSales(prev => prev.map(s => s.id === updated.id ? { ...s, ...updated } : s));
  };

  const handleCancelOrder = async () => {
    if (!cancelTarget) return;
    setCancelling(true);
    try {
      await axios.post(`${API}/orders/${cancelTarget.id}/cancel`, {}, { headers });
      setSales(prev => prev.map(s => s.id === cancelTarget.id ? { ...s, payment_status: 'CANCELLED' } : s));
      toast.success('order cancelled. refund initiated.');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'could not cancel order.');
    } finally {
      setCancelling(false);
      setCancelTarget(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8 overflow-x-hidden" data-testid="orders-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-4">Orders</h1>

      <Tabs defaultValue="purchases" className="w-full overflow-hidden">
        <TabsList className="w-full grid grid-cols-2 mb-4">
          <TabsTrigger value="purchases" data-testid="tab-purchases">
            <ShoppingBag className="w-4 h-4 mr-1.5" /> My Orders {purchases.length > 0 && `(${purchases.length})`}
          </TabsTrigger>
          <TabsTrigger value="sales" data-testid="tab-sales">
            <Package className="w-4 h-4 mr-1.5" /> My Sales {sales.length > 0 && `(${sales.length})`}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="purchases">
          {loadingPurchases ? (
            <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-24 w-full rounded-xl" />)}</div>
          ) : purchases.length === 0 ? (
            <div className="text-center py-16">
              <ShoppingBag className="w-12 h-12 mx-auto text-honey/30 mb-3" />
              <p className="text-muted-foreground">no purchases yet.</p>
              <Link to="/honeypot" className="text-sm text-honey-amber hover:underline mt-1 inline-block">browse the Honeypot</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {purchases.map(order => (
                <OrderRow key={order.id} order={order} perspective="buyer" token={token} API={API} onUpdate={() => {}} onCancel={() => {}} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="sales">
          {loadingSales ? (
            <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-24 w-full rounded-xl" />)}</div>
          ) : sales.length === 0 ? (
            <div className="text-center py-16">
              <Package className="w-12 h-12 mx-auto text-honey/30 mb-3" />
              <p className="text-muted-foreground">no sales yet.</p>
              <Link to="/honeypot" className="text-sm text-honey-amber hover:underline mt-1 inline-block">list something on the Honeypot</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {sales.map(order => (
                <OrderRow key={order.id} order={order} perspective="seller" token={token} API={API} onUpdate={updateSale} onCancel={setCancelTarget} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Cancel Order Confirmation */}
      <AlertDialog open={!!cancelTarget} onOpenChange={(open) => { if (!open) setCancelTarget(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Are you sure you want to cancel this order?</AlertDialogTitle>
            <AlertDialogDescription>
              This cannot be undone. A refund will be issued to the buyer automatically.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={cancelling} data-testid="cancel-order-dismiss">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancelOrder}
              disabled={cancelling}
              className="bg-red-600 text-white hover:bg-red-700"
              data-testid="cancel-order-confirm"
            >
              {cancelling ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default OrdersPage;
