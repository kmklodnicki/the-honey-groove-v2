import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ShoppingBag, Package, Truck, CheckCircle2, Clock, XCircle, Loader2, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';
import { usePageTitle } from '../hooks/usePageTitle';

const STATUS_BADGE = {
  PAID: { label: 'Paid', color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
  PENDING: { label: 'Pending', color: 'bg-amber-100 text-amber-700', icon: Clock },
  FAILED: { label: 'Failed', color: 'bg-red-100 text-red-700', icon: XCircle },
  EXPIRED: { label: 'Expired', color: 'bg-stone-100 text-stone-500', icon: XCircle },
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
      <div className="flex gap-2">
        <Input placeholder="carrier (e.g. USPS)" value={carrier} onChange={e => setCarrier(e.target.value)}
          className="h-8 text-xs flex-1" data-testid="shipping-carrier-input" />
        <Input placeholder="tracking #" value={tracking} onChange={e => setTracking(e.target.value)}
          className="h-8 text-xs flex-1" data-testid="shipping-tracking-input" />
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

// Order row
const OrderRow = ({ order, perspective, token, API, onUpdate }) => {
  const counterparty = order.counterparty || {};
  const timeAgo = order.created_at ? formatDistanceToNow(new Date(order.created_at), { addSuffix: true }) : '';

  return (
    <Card className="border-honey/20" data-testid={`order-row-${order.id}`}>
      <CardContent className="p-4">
        <div className="flex gap-4 items-start">
          {/* Album art */}
          <div className="w-16 h-16 rounded-lg overflow-hidden bg-honey/10 shrink-0">
            {order.cover_url ? (
              <AlbumArt src={order.cover_url} alt="" className="w-full h-full" />
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
              <span className="text-sm font-heading text-honey-amber shrink-0" data-testid="order-amount">${order.amount?.toFixed(2)}</span>
            </div>

            {/* Order meta */}
            <div className="flex items-center gap-2 flex-wrap text-xs text-muted-foreground mb-2">
              <span className="font-mono text-[10px] bg-stone-100 px-1.5 py-0.5 rounded" data-testid="order-number">#{order.order_number}</span>
              <span>{timeAgo}</span>
              {counterparty.username && (
                <Link to={`/profile/${counterparty.username}`} className="text-honey-amber hover:underline" data-testid="order-counterparty">
                  @{counterparty.username}
                </Link>
              )}
              {order.condition && <span className="text-stone-400">{order.condition}</span>}
            </div>

            {/* Status badges */}
            <div className="flex items-center gap-2 flex-wrap">
              <PaymentBadge status={order.payment_status} />
              {perspective === 'seller' ? (
                <ShippingEditor order={order} token={token} API={API} onUpdate={onUpdate} />
              ) : (
                <>
                  <ShippingBadge status={order.shipping_status || 'NOT_SHIPPED'} />
                  {order.tracking_number && (
                    <span className="text-xs text-muted-foreground">
                      {order.shipping_carrier && `${order.shipping_carrier}: `}#{order.tracking_number}
                    </span>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </CardContent>
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
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${API}/orders/purchases`, { headers }).then(r => setPurchases(r.data)).catch(() => {}).finally(() => setLoadingPurchases(false));
    axios.get(`${API}/orders/sales`, { headers }).then(r => setSales(r.data)).catch(() => {}).finally(() => setLoadingSales(false));
  }, [API, token]);

  const updateSale = (updated) => {
    setSales(prev => prev.map(s => s.id === updated.id ? { ...s, ...updated } : s));
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6" data-testid="orders-page">
      <h1 className="font-heading text-3xl text-vinyl-black mb-4">Orders</h1>

      <Tabs defaultValue="purchases" className="w-full">
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
                <OrderRow key={order.id} order={order} perspective="buyer" token={token} API={API} onUpdate={() => {}} />
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
                <OrderRow key={order.id} order={order} perspective="seller" token={token} API={API} onUpdate={updateSale} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default OrdersPage;
