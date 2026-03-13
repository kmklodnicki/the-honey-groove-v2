import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { ArrowRightLeft, Check, X, MessageSquare, Disc, Loader2, DollarSign, Search, Package, AlertTriangle, Star, Camera, Truck, Clock, CheckCircle2, XCircle, Shield, HelpCircle, MapPin } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../components/ui/tooltip';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { formatDistanceToNow } from 'date-fns';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import AlbumArt from '../components/AlbumArt';
import { resolveImageUrl } from '../utils/imageUrl';

const STATUS_CONFIG = {
  PROPOSED: { label: 'Proposed', color: 'bg-amber-100 text-amber-700', dot: 'bg-amber-400' },
  COUNTERED: { label: 'Countered', color: 'bg-blue-100 text-blue-700', dot: 'bg-blue-400' },
  ACCEPTED: { label: 'Accepted', color: 'bg-green-100 text-green-700', dot: 'bg-green-400' },
  DECLINED: { label: 'Declined', color: 'bg-red-100 text-red-700', dot: 'bg-red-400' },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-100 text-gray-600', dot: 'bg-gray-400' },
  HOLD_PENDING: { label: 'Hold Pending', color: 'bg-amber-100 text-amber-700', dot: 'bg-amber-500' },
  SHIPPING: { label: 'Shipping', color: 'bg-purple-100 text-purple-700', dot: 'bg-purple-400' },
  CONFIRMING: { label: 'Confirming', color: 'bg-cyan-100 text-cyan-700', dot: 'bg-cyan-400' },
  COMPLETED: { label: 'Completed', color: 'bg-green-100 text-green-700', dot: 'bg-green-500' },
  DISPUTED: { label: 'Disputed', color: 'bg-red-100 text-red-700', dot: 'bg-red-500' },
  EXPIRED: { label: 'Expired', color: 'bg-orange-100 text-orange-700', dot: 'bg-orange-500' },
};

// Countdown helper - returns human-readable time left
const formatCountdown = (deadline) => {
  if (!deadline) return null;
  const diff = new Date(deadline) - new Date();
  if (diff <= 0) return 'Overdue';
  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  if (days > 0) return `${days}d ${hours}h remaining`;
  const mins = Math.floor((diff % 3600000) / 60000);
  return hours > 0 ? `${hours}h ${mins}m remaining` : `${mins}m remaining`;
};

const DISPUTE_REASON_LABELS = {
  record_not_as_described: 'Record not as described',
  damaged_during_shipping: 'Damaged during shipping',
  wrong_record_sent: 'Wrong record sent',
  missing_item: 'Missing item',
  counterfeit_fake_pressing: 'Counterfeit / fake pressing',
};

// Trade Timeline
const TIMELINE_STEPS = [
  { key: 'ACCEPTED', label: 'Accepted' },
  { key: 'SHIPPING', label: 'Awaiting Shipment' },
  { key: 'IN_TRANSIT', label: 'In Transit' },
  { key: 'CONFIRMING', label: 'Awaiting Confirmation' },
  { key: 'COMPLETED', label: 'Completed' },
];

const getActiveStep = (trade) => {
  const s = trade.status;
  if (s === 'COMPLETED') return 4;
  if (s === 'CONFIRMING') return 3;
  if (s === 'SHIPPING') {
    const shipping = trade.shipping || {};
    const bothShipped = shipping.initiator && shipping.responder;
    return bothShipped ? 2 : 1;
  }
  if (s === 'HOLD_PENDING' || s === 'ACCEPTED') return 0;
  return -1; // EXPIRED, DISPUTED, etc
};

const TradeTimeline = ({ trade }) => {
  const active = getActiveStep(trade);
  if (active < 0) return null; // Don't show for expired/disputed

  return (
    <div className="py-3" data-testid="trade-timeline">
      <div className="flex items-center justify-between">
        {TIMELINE_STEPS.map((step, i) => (
          <React.Fragment key={step.key}>
            <div className="flex flex-col items-center gap-1" style={{ flex: '0 0 auto' }}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                i < active ? 'bg-green-500 text-white'
                : i === active ? 'bg-honey text-vinyl-black ring-2 ring-honey/30'
                : 'bg-stone-200 text-stone-400'
              }`}>
                {i < active ? <Check className="w-3 h-3" /> : i + 1}
              </div>
              <span className={`text-[9px] text-center leading-tight max-w-[60px] ${
                i <= active ? 'text-foreground font-medium' : 'text-muted-foreground'
              }`}>{step.label}</span>
            </div>
            {i < TIMELINE_STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mx-1 ${i < active ? 'bg-green-400' : 'bg-stone-200'}`} />
            )}
          </React.Fragment>
        ))}
      </div>
      {/* Countdown */}
      {trade.status === 'SHIPPING' && trade.shipping_deadline && (
        <p className="text-xs text-purple-600 text-center mt-2 font-medium" data-testid="shipping-countdown">
          <Clock className="w-3 h-3 inline mr-1" />
          Ship within {formatCountdown(trade.shipping_deadline)}
        </p>
      )}
      {trade.status === 'CONFIRMING' && trade.confirmation_deadline && (
        <p className="text-xs text-cyan-600 text-center mt-2 font-medium" data-testid="confirmation-countdown">
          <Clock className="w-3 h-3 inline mr-1" />
          Confirm within {formatCountdown(trade.confirmation_deadline)}
        </p>
      )}
    </div>
  );
};

// Shipping Address Exchange component for trade parties
const ShippingAddressSection = ({ tradeId, token, API }) => {
  const [myAddress, setMyAddress] = useState('');
  const [otherAddress, setOtherAddress] = useState('');
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const fetchAddresses = async () => {
      try {
        const resp = await axios.get(`${API}/trades/${tradeId}/shipping-address`, { headers: { Authorization: `Bearer ${token}` } });
        setMyAddress(resp.data.my_address || '');
        setOtherAddress(resp.data.other_address || '');
      } catch {}
      setLoaded(true);
    };
    fetchAddresses();
  }, [tradeId, token, API]);

  const handleSave = async () => {
    if (!myAddress.trim()) return;
    setSaving(true);
    try {
      await axios.put(`${API}/trades/${tradeId}/shipping-address`, { address: myAddress }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Shipping address saved');
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to save address'); }
    finally { setSaving(false); }
  };

  if (!loaded) return null;

  return (
    <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-200" data-testid="shipping-address-section">
      <p className="text-xs font-medium text-indigo-700 mb-3 flex items-center gap-1"><MapPin className="w-3 h-3" /> SHIPPING ADDRESSES</p>
      <div className="space-y-3">
        <div>
          <label className="text-xs text-indigo-600 font-medium mb-1 block">Your shipping address</label>
          <Textarea
            placeholder="Enter your full shipping address..."
            value={myAddress}
            onChange={e => setMyAddress(e.target.value)}
            className="text-sm border-indigo-200 min-h-[60px] resize-none"
            data-testid="my-shipping-address"
          />
          <Button onClick={handleSave} disabled={saving || !myAddress.trim()} size="sm" className="mt-2 bg-indigo-600 text-white hover:bg-indigo-700 rounded-full text-xs" data-testid="save-shipping-address-btn">
            {saving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Check className="w-3 h-3 mr-1" />}
            Save Address
          </Button>
        </div>
        {otherAddress ? (
          <div>
            <label className="text-xs text-indigo-600 font-medium mb-1 block">Ship to (other party)</label>
            <div className="bg-white rounded-lg p-3 text-sm border border-indigo-100 whitespace-pre-wrap" data-testid="other-shipping-address">{otherAddress}</div>
          </div>
        ) : (
          <p className="text-xs text-indigo-400 italic" data-testid="waiting-other-address">Waiting for the other party to share their address...</p>
        )}
      </div>
    </div>
  );
};

const TradesPage = () => {
  usePageTitle('Trades');
  const { user, token, API } = useAuth();
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('active');
  const [selectedTrade, setSelectedTrade] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [platformFee, setPlatformFee] = useState(6);

  const fetchTrades = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/trades`, { headers: { Authorization: `Bearer ${token}` } });
      setTrades(resp.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchTrades(); }, [fetchTrades]);
  useEffect(() => {
    axios.get(`${API}/platform-fee`).then(r => setPlatformFee(r.data.platform_fee_percent)).catch(() => {});
  }, [API]);

  const activeTrades = trades.filter(t => ['PROPOSED', 'COUNTERED', 'HOLD_PENDING', 'SHIPPING', 'CONFIRMING', 'DISPUTED'].includes(t.status));
  const completedTrades = trades.filter(t => ['COMPLETED', 'DECLINED', 'CANCELLED'].includes(t.status));

  const openDetail = (trade) => { setSelectedTrade(trade); setShowDetail(true); };

  if (loading) return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-3 md:pt-2">
      <Skeleton className="h-10 w-48 mb-6" />
      {[1, 2, 3].map(i => <Skeleton key={i} className="h-28 w-full mb-3" />)}
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-3 md:pt-2 pb-24 md:pb-8" data-testid="trades-page">
      <div className="mb-6">
        <h1 className="font-heading text-3xl text-vinyl-black">My Trades</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your record trades with other collectors</p>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-2">
          <TabsTrigger value="active" className="data-[state=active]:bg-honey text-sm" data-testid="tab-active-trades">Active ({activeTrades.length})</TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-honey text-sm" data-testid="tab-trade-history">History ({completedTrades.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="active">
          {activeTrades.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <ArrowRightLeft className="w-12 h-12 text-honey mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">No active trades</h3>
              <p className="text-muted-foreground text-sm mb-4">Browse TRADE listings in The Honeypot to propose a trade!</p>
              <Link to="/honeypot"><Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full">Go to The Honeypot</Button></Link>
            </Card>
          ) : (
            <div className="space-y-3">{activeTrades.map(t => <TradeCard key={t.id} trade={t} currentUserId={user?.id} onClick={() => openDetail(t)} feePct={platformFee} />)}</div>
          )}
        </TabsContent>
        <TabsContent value="history">
          {completedTrades.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <ArrowRightLeft className="w-12 h-12 text-honey/40 mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">No trade history</h3>
              <p className="text-muted-foreground text-sm">Completed and declined trades will appear here.</p>
            </Card>
          ) : (
            <div className="space-y-3">{completedTrades.map(t => <TradeCard key={t.id} trade={t} currentUserId={user?.id} onClick={() => openDetail(t)} feePct={platformFee} />)}</div>
          )}
        </TabsContent>
      </Tabs>
      {selectedTrade && (
        <TradeDetailModal open={showDetail} onOpenChange={(o) => { if (!o) { setShowDetail(false); setSelectedTrade(null); } }}
          trade={selectedTrade} currentUserId={user?.id} token={token} API={API} feePct={platformFee} onUpdate={() => { fetchTrades(); setShowDetail(false); setSelectedTrade(null); }} />
      )}
    </div>
  );
};

// ======= Trade Card =======
const TradeCard = ({ trade, currentUserId, onClick, feePct = 6 }) => {
  const isInitiator = trade.initiator_id === currentUserId;
  const otherUser = isInitiator ? trade.responder : trade.initiator;
  const sc = STATUS_CONFIG[trade.status] || STATUS_CONFIG.PROPOSED;
  const role = isInitiator ? 'initiator' : 'responder';
  const holdNeedsPay = trade.status === 'HOLD_PENDING' && !(trade.hold_charges?.[role]?.status === 'paid');
  const needsAction = (trade.status === 'PROPOSED' && !isInitiator) || (trade.status === 'COUNTERED' && isInitiator)
    || holdNeedsPay
    || (trade.status === 'SHIPPING' && !hasShipped(trade, currentUserId))
    || (trade.status === 'CONFIRMING' && !hasConfirmed(trade, currentUserId))
    || (trade.status === 'COMPLETED' && !hasRated(trade, currentUserId));

  return (
    <Card className={`p-4 border-honey/30 cursor-pointer transition-all hover:shadow-md ${needsAction ? 'ring-2 ring-honey/50' : ''}`}
      onClick={onClick} data-testid={`trade-card-${trade.id}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${sc.dot}`} />
          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${sc.color}`}>{sc.label}</span>
          {trade.hold_enabled && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="flex items-center" data-testid="hold-shield-icon">
                    <Shield className="w-3.5 h-3.5 text-honey-amber" />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top" className="bg-vinyl-black text-white text-xs max-w-[200px]">
                  <p>Mutual hold trade · both parties have skin in the game.</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          {needsAction && <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-honey text-vinyl-black">{holdNeedsPay ? 'Pay hold' : 'Action needed'}</span>}
        </div>
        <span className="text-xs text-muted-foreground">{formatDistanceToNow(new Date(trade.updated_at), { addSuffix: true })}</span>
      </div>
      <div className="flex items-center gap-3">
        <RecordMini record={trade.offered_record} label={isInitiator ? 'You offer' : `@${trade.initiator?.username} offers`} />
        <ArrowRightLeft className="w-5 h-5 text-honey shrink-0" />
        <RecordMini record={trade.listing_record} label={isInitiator ? `@${trade.responder?.username}'s` : 'Your listing'} />
      </div>
      {trade.boot_amount > 0 && (
        <div className="mt-2.5 flex items-center gap-2 px-3 py-2 rounded-lg bg-honey/8 border border-honey/15" data-testid="trade-sweetener-badge">
          <DollarSign className="w-4 h-4 text-honey-amber shrink-0" />
          <span className="text-sm font-medium text-vinyl-black">${trade.boot_amount} sweetener</span>
          <span className="text-xs text-muted-foreground">
            {trade.boot_direction === 'TO_SELLER'
              ? `${trade.initiator_id === currentUserId ? 'you pay' : 'they pay'}`
              : `${trade.responder_id === currentUserId ? 'you pay' : 'they pay'}`
            }
          </span>
          <span className="ml-auto text-[10px] text-muted-foreground" title={`${feePct}% platform fee on sweetener amount only`}>{feePct}% fee</span>
        </div>
      )}
      {/* Mutual Hold indicator */}
      {trade.hold_enabled && trade.hold_amount > 0 && (
        <div className="mt-2.5 flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200/50" data-testid="trade-hold-badge">
          <Shield className="w-4 h-4 text-honey-amber shrink-0" />
          <span className="text-sm font-medium text-vinyl-black">
            {trade.hold_status === 'active' ? `Hold active · $${trade.hold_amount} held from each party`
              : trade.hold_status === 'frozen' ? `Hold frozen · $${trade.hold_amount}`
              : trade.hold_status === 'refunded' ? `Hold reversed · $${trade.hold_amount} refunded`
              : `$${trade.hold_amount} mutual hold`}
          </span>
        </div>
      )}
      {/* Shipping status summary */}
      {trade.status === 'SHIPPING' && trade.shipping && (
        <ShippingSummary trade={trade} currentUserId={currentUserId} />
      )}
      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-2">
          <Avatar className="h-5 w-5">
            {otherUser?.avatar_url && <AvatarImage src={resolveImageUrl(otherUser.avatar_url)} />}
            <AvatarFallback className="text-[10px] bg-honey/20">{otherUser?.username?.charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>
          <span className="text-xs text-muted-foreground">with @{otherUser?.username}</span>
        </div>
        {trade.messages?.length > 0 && (
          <span className="text-xs text-muted-foreground flex items-center gap-1"><MessageSquare className="w-3 h-3" /> {trade.messages.length}</span>
        )}
      </div>
    </Card>
  );
};

// ======= Helpers =======
const hasShipped = (trade, userId) => {
  const role = trade.initiator_id === userId ? 'initiator' : 'responder';
  return trade.shipping?.[role] != null;
};
const hasConfirmed = (trade, userId) => trade.confirmations?.[userId] === true;
const hasRated = (trade, userId) => trade.ratings?.[userId] != null;

const ShippingSummary = ({ trade, currentUserId }) => {
  const iShipped = hasShipped(trade, currentUserId);
  const otherShipped = trade.initiator_id === currentUserId
    ? trade.shipping?.responder != null
    : trade.shipping?.initiator != null;
  const otherName = trade.initiator_id === currentUserId ? trade.responder?.username : trade.initiator?.username;
  return (
    <div className="mt-2 flex items-center gap-2 text-xs">
      {iShipped ? <CheckCircle2 className="w-3 h-3 text-green-500" /> : <Clock className="w-3 h-3 text-amber-500" />}
      <span>{iShipped ? 'You shipped' : 'You need to ship'}</span>
      <span className="text-muted-foreground">|</span>
      {otherShipped ? <CheckCircle2 className="w-3 h-3 text-green-500" /> : <Clock className="w-3 h-3 text-amber-500" />}
      <span>{otherShipped ? `@${otherName} shipped` : `Waiting on @${otherName}`}</span>
    </div>
  );
};

const RecordMini = ({ record, label }) => (
  <div className="flex items-center gap-2 flex-1 min-w-0">
    {record?.cover_url ? (
      <AlbumArt src={record.cover_url} alt={`${record.artist} ${record.title} vinyl record`} className="w-12 h-12 rounded-lg object-cover shadow" isUnofficial={record.is_unofficial} />
    ) : (
      <div className="w-12 h-12 rounded-lg bg-honey/20 flex items-center justify-center shrink-0"><Disc className="w-5 h-5 text-honey" /></div>
    )}
    <div className="min-w-0 flex-1">
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className="text-sm font-medium truncate">{record?.title || record?.album || 'Unknown'}</p>
      <p className="text-xs text-muted-foreground truncate">{record?.artist || ''}</p>
    </div>
  </div>
);

// ======= Trade Detail Modal =======
const TradeDetailModal = ({ open, onOpenChange, trade, currentUserId, token, API, feePct = 6, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [showCounter, setShowCounter] = useState(false);
  const [counterMessage, setCounterMessage] = useState('');
  const [counterBoot, setCounterBoot] = useState('');
  const [counterBootDir, setCounterBootDir] = useState('TO_SELLER');
  const [otherRecords, setOtherRecords] = useState([]);
  const [counterRecordId, setCounterRecordId] = useState('');
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [messageText, setMessageText] = useState('');
  // Shipping
  const [trackingNumber, setTrackingNumber] = useState('');
  const [carrier, setCarrier] = useState('');
  // Dispute
  const [showDispute, setShowDispute] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');
  const [disputePhotos, setDisputePhotos] = useState([]);
  const [disputeResponse, setDisputeResponse] = useState('');
  const [disputeResponsePhotos, setDisputeResponsePhotos] = useState([]);
  // Rating
  const [showRating, setShowRating] = useState(false);
  const [ratingValue, setRatingValue] = useState(0);
  const [ratingReview, setRatingReview] = useState('');

  const isInitiator = trade.initiator_id === currentUserId;
  const canAccept = (trade.status === 'PROPOSED' && !isInitiator) || (trade.status === 'COUNTERED' && isInitiator);
  const canCounter = (trade.status === 'PROPOSED' && !isInitiator) || (trade.status === 'COUNTERED' && isInitiator);
  const canDecline = ['PROPOSED', 'COUNTERED'].includes(trade.status);
  const role = isInitiator ? 'initiator' : 'responder';
  const holdPaid = trade.hold_charges?.[role]?.status === 'paid';
  const canPayHold = trade.status === 'HOLD_PENDING' && !holdPaid;
  const canShip = trade.status === 'SHIPPING' && !hasShipped(trade, currentUserId);
  const canConfirm = trade.status === 'CONFIRMING' && !hasConfirmed(trade, currentUserId);
  const canDispute = ['CONFIRMING', 'SHIPPING'].includes(trade.status) && !trade.dispute;
  const canRespondDispute = trade.status === 'DISPUTED' && trade.dispute && !trade.dispute.response && trade.dispute.opened_by !== currentUserId;
  const needsRating = trade.status === 'COMPLETED' && !hasRated(trade, currentUserId);
  const sc = STATUS_CONFIG[trade.status] || STATUS_CONFIG.PROPOSED;
  const otherUser = isInitiator ? trade.responder : trade.initiator;

  const fetchOtherRecords = async () => {
    const otherUsername = isInitiator ? trade.responder?.username : trade.initiator?.username;
    if (!otherUsername) return;
    setLoadingRecords(true);
    try { const resp = await axios.get(`${API}/users/${otherUsername}/records`); setOtherRecords(resp.data); }
    catch { /* ignore */ }
    finally { setLoadingRecords(false); }
  };

  const apiCall = async (method, url, body) => {
    setLoading(true);
    try {
      const config = { headers: { Authorization: `Bearer ${token}` } };
      if (method === 'put') await axios.put(url, body || {}, config);
      else await axios.post(url, body || {}, config);
      return true;
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); return false; }
    finally { setLoading(false); }
  };

  const handleAccept = async () => {
    const confirmed = window.confirm(
      `By accepting, both parties will be charged a mutual hold of $${trade.hold_amount || 0}. This is fully refunded on confirmed delivery. Proceed?`
    );
    if (!confirmed) return;
    if (await apiCall('put', `${API}/trades/${trade.id}/accept`)) {
      toast.success('Trade accepted! Pay your hold to start shipping.');
      trackEvent('trade_completed');
      onUpdate();
    }
  };

  const handlePayHold = async () => {
    setLoading(true);
    try {
      const resp = await axios.post(`${API}/trades/${trade.id}/hold/checkout`,
        { origin_url: window.location.origin },
        { headers: { Authorization: `Bearer ${token}` } });
      if (resp.data.url) {
        window.location.href = resp.data.url;
      }
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to create hold checkout'); }
    finally { setLoading(false); }
  };

  const handleDecline = async () => { if (await apiCall('put', `${API}/trades/${trade.id}/decline`)) { toast.success('trade declined.'); onUpdate(); } };

  const handleCounter = async () => {
    if (await apiCall('put', `${API}/trades/${trade.id}/counter`, {
      requested_record_id: counterRecordId || null,
      boot_amount: counterBoot ? parseFloat(counterBoot) : null,
      boot_direction: counterBoot ? counterBootDir : null,
      message: counterMessage || null,
    })) { toast.success('Counter sent!'); onUpdate(); }
  };

  const handleShip = async () => {
    if (!trackingNumber.trim()) { toast.error('Enter a tracking number'); return; }
    if (trackingNumber.trim().length < 6) { toast.error('Tracking number must be at least 6 characters'); return; }
    if (!carrier.trim()) { toast.error('Enter a carrier (e.g. USPS, UPS, FedEx)'); return; }
    if (await apiCall('put', `${API}/trades/${trade.id}/ship`, { tracking_number: trackingNumber.trim(), carrier: carrier.trim() })) {
      toast.success('Tracking added!'); onUpdate();
    }
  };

  const handleConfirm = async () => {
    if (await apiCall('put', `${API}/trades/${trade.id}/confirm-receipt`)) { toast.success('receipt confirmed.'); onUpdate(); }
  };

  const handleCancelShipping = async () => {
    if (await apiCall('put', `${API}/trades/${trade.id}/cancel-shipping`)) { toast.success('Trade cancelled'); onUpdate(); }
  };

  const handleOpenDispute = async () => {
    // Upload photos first
    const photoUrls = [];
    for (const photo of disputePhotos) {
      const fd = new FormData(); fd.append('file', photo.file);
      try {
        const r = await axios.post(`${API}/upload`, fd, { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } });
        photoUrls.push(r.data.path);
      } catch { /* skip */ }
    }
    if (await apiCall('post', `${API}/trades/${trade.id}/dispute`, { reason: disputeReason, photo_urls: photoUrls })) {
      toast.success('Dispute opened'); onUpdate();
    }
  };

  const handleDisputeRespond = async () => {
    const photoUrls = [];
    for (const photo of disputeResponsePhotos) {
      const fd = new FormData(); fd.append('file', photo.file);
      try {
        const r = await axios.post(`${API}/upload`, fd, { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } });
        photoUrls.push(r.data.path);
      } catch { /* skip */ }
    }
    if (await apiCall('put', `${API}/trades/${trade.id}/dispute/respond`, { response_text: disputeResponse, photo_urls: photoUrls })) {
      toast.success('Response submitted'); onUpdate();
    }
  };

  const handleRate = async () => {
    if (ratingValue === 0) { toast.error('Select a rating'); return; }
    if (await apiCall('post', `${API}/trades/${trade.id}/rate`, { rating: ratingValue, review: ratingReview || null })) {
      toast.success('Rating submitted!'); onUpdate();
    }
  };

  const handleSendMessage = async () => {
    if (!messageText.trim()) return;
    try {
      await axios.post(`${API}/trades/${trade.id}/message`, { text: messageText }, { headers: { Authorization: `Bearer ${token}` } });
      setMessageText(''); onUpdate();
    } catch { toast.error('Failed to send'); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-heading flex items-center gap-2">
            <ArrowRightLeft className="w-5 h-5 text-honey" /> Trade Details
          </DialogTitle>
          <DialogDescription className="flex items-center gap-2">
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${sc.color}`}>{sc.label}</span>
            <span className="text-xs">{formatDistanceToNow(new Date(trade.created_at), { addSuffix: true })}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* Trade Timeline */}
          {['ACCEPTED','HOLD_PENDING','SHIPPING','CONFIRMING','COMPLETED'].includes(trade.status) && (
            <TradeTimeline trade={trade} />
          )}

          {/* Expired notice */}
          {trade.status === 'EXPIRED' && (
            <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 text-center" data-testid="trade-expired-notice">
              <XCircle className="w-6 h-6 text-orange-500 mx-auto mb-1" />
              <p className="text-sm font-medium text-orange-700">Trade Expired</p>
              <p className="text-xs text-orange-600 mt-1">
                {trade.expired_reason === 'shipping_deadline'
                  ? 'This trade expired because one or both parties did not ship within the 3-day deadline. Mutual holds have been released.'
                  : 'This trade has expired.'}
              </p>
            </div>
          )}

          {/* THE EXCHANGE */}
          <div className="bg-honey/5 rounded-xl p-4">
            <p className="text-xs font-medium text-muted-foreground mb-3">THE EXCHANGE</p>
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <p className="text-[10px] text-muted-foreground mb-1">@{trade.initiator?.username} {isInitiator ? '(you)' : ''} offers</p>
                <RecordDetail record={trade.offered_record} condition={trade.offered_condition} photoUrls={trade.offered_photo_urls} />
              </div>
              <div className="flex flex-col items-center pt-6"><ArrowRightLeft className="w-5 h-5 text-honey" /></div>
              <div className="flex-1">
                <p className="text-[10px] text-muted-foreground mb-1">@{trade.responder?.username} {!isInitiator ? '(you)' : ''} has</p>
                <RecordDetail record={trade.listing_record} condition={trade.listing_record?.condition} photoUrls={trade.listing_record?.photo_urls} />
              </div>
            </div>
          </div>

          {/* Boot info */}
          {trade.boot_amount > 0 && (
            <div className="bg-honey/8 border border-honey/20 rounded-xl p-4" data-testid="trade-sweetener-detail">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-5 h-5 text-honey-amber" />
                <span className="font-heading text-lg">${trade.boot_amount} Sweetener</span>
              </div>
              <p className="text-sm text-muted-foreground mb-1">
                {trade.boot_direction === 'TO_SELLER'
                  ? <><strong>@{trade.initiator?.username}</strong> pays <strong>@{trade.responder?.username}</strong></>
                  : <><strong>@{trade.responder?.username}</strong> pays <strong>@{trade.initiator?.username}</strong></>
                }
              </p>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span>{feePct}% platform fee (${(trade.boot_amount * feePct / 100).toFixed(2)})</span>
                <span>&middot;</span>
                <span>Recipient gets ${(trade.boot_amount * (100 - feePct) / 100).toFixed(2)}</span>
              </div>
              <p className="text-[10px] text-muted-foreground mt-2 italic">
                A sweetener is cash added to one side of a trade to balance value. Charged via Stripe when both parties accept. {feePct}% platform fee applies.
              </p>
            </div>
          )}

          {/* === MUTUAL HOLD STATUS === */}
          {trade.hold_enabled && trade.hold_amount > 0 && (
            <div className={`rounded-xl p-4 border ${
              trade.hold_status === 'active' ? 'bg-amber-50 border-amber-200'
                : trade.hold_status === 'frozen' ? 'bg-red-50 border-red-200'
                : trade.hold_status === 'refunded' ? 'bg-green-50 border-green-200'
                : 'bg-amber-50/50 border-amber-200/50'
            }`} data-testid="hold-status-section">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-honey-amber" />
                <span className="text-xs font-medium text-honey-amber">MUTUAL HOLD</span>
              </div>
              {trade.hold_status === 'active' && (
                <p className="text-sm font-medium text-amber-800">Hold active · ${trade.hold_amount} held from each party</p>
              )}
              {trade.hold_status === 'frozen' && (
                <p className="text-sm font-medium text-red-700">Hold frozen · ${trade.hold_amount} per party. Dispute in progress.</p>
              )}
              {trade.hold_status === 'refunded' && (
                <p className="text-sm font-medium text-green-700">Hold reversed · ${trade.hold_amount} refunded to both parties</p>
              )}
              {trade.hold_status === 'awaiting_payment' && (
                <div>
                  <p className="text-sm text-amber-700 mb-2">Both parties must pay the ${trade.hold_amount} hold to start shipping.</p>
                  <div className="flex items-center gap-2 text-xs mb-1">
                    {trade.hold_charges?.initiator?.status === 'paid' ? <CheckCircle2 className="w-3 h-3 text-green-500" /> : <Clock className="w-3 h-3 text-amber-500" />}
                    <span>@{trade.initiator?.username} {isInitiator ? '(you)' : ''} · {trade.hold_charges?.initiator?.status === 'paid' ? 'Paid' : 'Waiting'}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    {trade.hold_charges?.responder?.status === 'paid' ? <CheckCircle2 className="w-3 h-3 text-green-500" /> : <Clock className="w-3 h-3 text-amber-500" />}
                    <span>@{trade.responder?.username} {!isInitiator ? '(you)' : ''} · {trade.hold_charges?.responder?.status === 'paid' ? 'Paid' : 'Waiting'}</span>
                  </div>
                </div>
              )}
              {!trade.hold_status && (
                <p className="text-sm text-amber-700">${trade.hold_amount} mutual hold · charged when both parties accept.</p>
              )}
              <p className="text-[10px] text-muted-foreground mt-2 italic">
                Fully reversed within 48 hours of confirmed delivery. The hold is not subject to platform fees.
              </p>
            </div>
          )}

          {/* Pay Hold Button */}
          {canPayHold && (
            <div>
              <Button onClick={handlePayHold} disabled={loading} className="w-full bg-amber-600 text-white hover:bg-amber-700 rounded-full" data-testid="pay-hold-btn">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Shield className="w-4 h-4 mr-2" />}
                Pay ${trade.hold_amount} Hold
              </Button>
              <div className="text-center mt-2" data-testid="stripe-trust-badge-hold">
                <span className="text-[11px] text-muted-foreground/60 inline-flex items-center gap-1.5">
                  <svg width="28" height="12" viewBox="0 0 28 12" fill="none" className="opacity-40">
                    <path d="M13.3 3.4c0-.6.5-.8 1.3-.8.9 0 2.1.3 3 .8V.6c-1-.4-2-.6-3-.6C12.4 0 11 1.2 11 3.2c0 3.1 4.3 2.6 4.3 4 0 .7-.6.9-1.4.9-1.2 0-2.7-.5-3.8-1.2v2.8c1.3.6 2.6.8 3.8.8 2.3 0 3.8-1.1 3.8-3.2-.1-3.3-4.4-2.8-4.4-3.9zM7.5 5L6.3 4.5c-.5-.2-.6-.4-.6-.6 0-.3.3-.4.7-.4.6 0 1.2.2 1.8.5l.7-2A5 5 0 007 1.5C5.6 1.5 4.5 2.3 4.5 3.6c0 .8.5 1.5 1.2 1.8l1.1.5c.5.2.6.4.6.7 0 .3-.3.5-.8.5-.7 0-1.4-.3-2.1-.7l-.7 2c.9.5 1.8.7 2.8.7C8 9.1 9 8.2 9 6.9 9 6 8.4 5.4 7.5 5zm11.3-3.5h-2l.01 6.6c0 1.9 1 2.7 2.3 2.7.7 0 1.3-.1 1.8-.4V8.1c-.3.1-.9.3-1.3.3-.6 0-1-.2-1-1V4h1.3V1.6h-1.1zm5 0l-.2 1.2h-.01V1.6h-2.5v8.1h2.6V4.8c.6-.8 1.7-.7 2-.6V1.6c-.4-.2-1.6-.3-2.1.9zm2.8-1.8L24 .5v2.7h-1.3V5.5H24v3.2c0 1.6.8 2.3 2 2.3.6 0 1.1-.1 1.5-.3V8.4c-.3.1-.6.2-1 .2-.4 0-.7-.2-.7-.8V5.5h1.7V3.2h-1.7V-.3z" fill="currentColor"/>
                  </svg>
                  Secured by Stripe
                </span>
              </div>
            </div>
          )}

          {/* === SHIPPING STATUS === */}
          {(trade.status === 'SHIPPING' || trade.status === 'CONFIRMING') && trade.shipping && (
            <div className="bg-purple-50 rounded-xl p-4 border border-purple-200">
              <p className="text-xs font-medium text-purple-700 mb-3 flex items-center gap-1"><Truck className="w-3 h-3" /> SHIPPING STATUS</p>
              {['initiator', 'responder'].map(role => {
                const s = trade.shipping?.[role];
                const name = role === 'initiator' ? trade.initiator?.username : trade.responder?.username;
                const isMe = (role === 'initiator' && isInitiator) || (role === 'responder' && !isInitiator);
                return (
                  <div key={role} className={`flex items-center gap-2 py-2 ${role === 'responder' ? 'border-t border-purple-200' : ''}`}>
                    {s ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <Clock className="w-4 h-4 text-amber-500" />}
                    <span className="text-sm flex-1">
                      <strong>@{name}</strong> {isMe ? '(you)' : ''} · {s ? `Shipped via ${s.carrier || 'carrier'}` : 'Waiting to ship'}
                    </span>
                    {s && <span className="text-xs text-purple-600 font-mono">{s.tracking_number}</span>}
                  </div>
                );
              })}
              {trade.shipping_deadline && (
                <p className="text-xs text-purple-600 mt-2 font-medium">
                  <Clock className="w-3 h-3 inline mr-1" />
                  {formatCountdown(trade.shipping_deadline) === 'Overdue'
                    ? <span className="text-red-600 font-bold">OVERDUE — Shipping deadline passed</span>
                    : <>Ship by {new Date(trade.shipping_deadline).toLocaleDateString()} · {formatCountdown(trade.shipping_deadline)}</>
                  }
                </p>
              )}
            </div>
          )}

          {/* Shipping Address Exchange */}
          {(trade.status === 'HOLD_PENDING' || trade.status === 'SHIPPING' || trade.status === 'CONFIRMING') && (
            <ShippingAddressSection tradeId={trade.id} token={token} API={API} />
          )}

          {/* Ship form */}
          {canShip && (
            <div className="border border-purple-200 rounded-lg p-3 space-y-3 bg-purple-50/50">
              <p className="text-sm font-medium text-purple-700 flex items-center gap-1"><Package className="w-4 h-4" /> Add Tracking Info</p>
              <div className="grid grid-cols-2 gap-2">
                <Input placeholder="Tracking number" value={trackingNumber} onChange={e => setTrackingNumber(e.target.value)} className="text-sm border-purple-200" data-testid="tracking-number-input" />
                <Input placeholder="Carrier (USPS, UPS...)" value={carrier} onChange={e => setCarrier(e.target.value)} className="text-sm border-purple-200" data-testid="carrier-input" />
              </div>
              <Button onClick={handleShip} disabled={loading || !trackingNumber.trim()} className="w-full bg-purple-600 text-white hover:bg-purple-700 rounded-full text-sm" data-testid="submit-tracking-btn">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Truck className="w-4 h-4 mr-1" />}
                Submit Tracking
              </Button>
            </div>
          )}

          {/* Late Shipping Alert Banner */}
          {trade.status === 'SHIPPING' && trade.shipping_overdue && (
            <div className="bg-red-50 rounded-xl p-3 border border-red-200">
              <p className="text-xs font-semibold text-red-700 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Late Shipping Alert
              </p>
              <p className="text-xs text-red-600 mt-1">
                The 3-day shipping window has passed. {hasShipped(trade, currentUserId)
                  ? 'Your trade partner has not shipped yet. You may request cancellation.'
                  : 'Please ship immediately to avoid cancellation.'}
              </p>
            </div>
          )}

          {/* Cancel shipping (if overdue and user has shipped) */}
          {trade.status === 'SHIPPING' && trade.shipping_overdue && hasShipped(trade, currentUserId) && (
            <Button onClick={handleCancelShipping} disabled={loading} variant="outline" className="w-full rounded-full text-red-600 border-red-200 hover:bg-red-50" data-testid="cancel-shipping-btn">
              <XCircle className="w-4 h-4 mr-1" /> Request Cancellation
            </Button>
          )}

          {/* === CONFIRMATION === */}
          {trade.status === 'CONFIRMING' && (
            <div className="bg-cyan-50 rounded-xl p-4 border border-cyan-200">
              <p className="text-xs font-medium text-cyan-700 mb-2">CONFIRMATION WINDOW</p>
              <p className="text-sm text-cyan-700 font-medium mb-1">Did you receive the record as described?</p>
              {trade.hold_enabled && (
                <p className="text-xs text-cyan-600 mb-2">Your ${trade.hold_amount} hold will be fully reversed once both parties confirm.</p>
              )}
              {trade.confirmation_deadline && (
                <p className="text-xs text-cyan-600 mb-2"><Clock className="w-3 h-3 inline mr-1" />
                  Auto-confirms {formatDistanceToNow(new Date(trade.confirmation_deadline), { addSuffix: true })}
                </p>
              )}
              {hasConfirmed(trade, currentUserId) ? (
                <p className="text-sm text-green-600 font-medium flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> You confirmed. Waiting on @{otherUser?.username}</p>
              ) : (
                <div className="flex gap-2">
                  <Button onClick={handleConfirm} disabled={loading} className="flex-1 bg-cyan-600 text-white hover:bg-cyan-700 rounded-full text-sm" data-testid="confirm-receipt-btn">
                    {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Check className="w-4 h-4 mr-1" />}
                    Yes, everything looks good
                  </Button>
                  {canDispute && (
                    <Button onClick={() => setShowDispute(true)} variant="outline" className="rounded-full text-red-600 border-red-200 hover:bg-red-50 text-sm" data-testid="open-dispute-btn">
                      <AlertTriangle className="w-4 h-4 mr-1" /> There's an issue
                    </Button>
                  )}
                </div>
              )}
            </div>
          )}

          {/* === DISPUTE SECTION === */}
          {trade.dispute && (
            <div className="bg-red-50 rounded-xl p-4 border border-red-200">
              <p className="text-xs font-medium text-red-700 mb-2 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> DISPUTE</p>
              <p className="text-sm mb-1"><strong>Opened by:</strong> @{trade.dispute.opened_by === trade.initiator_id ? trade.initiator?.username : trade.responder?.username}</p>
              <p className="text-sm mb-2">{DISPUTE_REASON_LABELS[trade.dispute.reason] || trade.dispute.reason}</p>
              {trade.dispute.photo_urls?.length > 0 && (
                <div className="flex gap-2 mb-2 overflow-x-auto">{trade.dispute.photo_urls.map((url, i) => <img key={i} src={url} alt="" className="w-16 h-16 rounded object-cover border" />)}</div>
              )}
              {trade.dispute.response && (
                <div className="mt-3 pl-3 border-l-2 border-red-300">
                  <p className="text-xs font-medium text-red-600">Response:</p>
                  <p className="text-sm">{trade.dispute.response.text}</p>
                  {trade.dispute.response.photo_urls?.length > 0 && (
                    <div className="flex gap-2 mt-1 overflow-x-auto">{trade.dispute.response.photo_urls.map((url, i) => <img key={i} src={url} alt="" className="w-16 h-16 rounded object-cover border" />)}</div>
                  )}
                </div>
              )}
              {trade.dispute.resolution && (
                <div className="mt-3 bg-white rounded-lg p-2 border border-red-200">
                  <p className="text-xs font-medium text-green-700">Resolution: {trade.dispute.resolution.outcome}</p>
                  <p className="text-sm text-muted-foreground">{trade.dispute.resolution.notes}</p>
                </div>
              )}
              {!trade.dispute.response && !trade.dispute.resolution && (
                <p className="text-xs text-red-500 mt-2"><Clock className="w-3 h-3 inline mr-1" />
                  Response due {formatDistanceToNow(new Date(trade.dispute.response_deadline), { addSuffix: true })}
                </p>
              )}
            </div>
          )}

          {/* Dispute response form */}
          {canRespondDispute && (
            <div className="border border-red-200 rounded-lg p-3 space-y-3 bg-red-50/50">
              <p className="text-sm font-medium text-red-700">Respond to Dispute</p>
              <Textarea placeholder="Describe your side..." value={disputeResponse} onChange={e => setDisputeResponse(e.target.value)} className="text-sm border-red-200 resize-none" rows={3} data-testid="dispute-response-input" />
              <PhotoUploadMini photos={disputeResponsePhotos} setPhotos={setDisputeResponsePhotos} label="Evidence photos" />
              <Button onClick={handleDisputeRespond} disabled={loading || !disputeResponse.trim()} className="w-full bg-red-600 text-white hover:bg-red-700 rounded-full text-sm" data-testid="submit-dispute-response-btn">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
                Submit Response
              </Button>
            </div>
          )}

          {/* Open dispute form */}
          {showDispute && !trade.dispute && (
            <div className="border border-red-200 rounded-lg p-3 space-y-3 bg-red-50/50">
              <p className="text-sm font-medium text-red-700">Open a Dispute</p>
              <Select value={disputeReason} onValueChange={setDisputeReason}>
                <SelectTrigger className="text-sm border-red-200" data-testid="dispute-reason-select">
                  <SelectValue placeholder="Select a reason..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="record_not_as_described">Record not as described</SelectItem>
                  <SelectItem value="damaged_during_shipping">Damaged during shipping</SelectItem>
                  <SelectItem value="wrong_record_sent">Wrong record sent</SelectItem>
                  <SelectItem value="missing_item">Missing item</SelectItem>
                  <SelectItem value="counterfeit_fake_pressing">Counterfeit / fake pressing</SelectItem>
                </SelectContent>
              </Select>
              <PhotoUploadMini photos={disputePhotos} setPhotos={setDisputePhotos} label="Upload photo evidence (required)" />
              <div className="flex gap-2">
                <Button onClick={handleOpenDispute} disabled={loading || !disputeReason || disputePhotos.length === 0} className="flex-1 bg-red-600 text-white hover:bg-red-700 rounded-full text-sm" data-testid="submit-dispute-btn">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <AlertTriangle className="w-4 h-4 mr-1" />}
                  Open Dispute
                </Button>
                <Button variant="outline" onClick={() => setShowDispute(false)} className="rounded-full text-sm">Cancel</Button>
              </div>
              <p className="text-[10px] text-red-400">Funds will be frozen immediately while we review your case.</p>
            </div>
          )}

          {/* === COMPLETED + RATING === */}
          {trade.status === 'COMPLETED' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
              <CheckCircle2 className="w-6 h-6 text-green-600 mx-auto mb-1" />
              <p className="text-sm font-medium text-green-700">Trade Completed!</p>
              <p className="text-xs text-green-600 mt-1">Records have been transferred to both collections.</p>
            </div>
          )}

          {/* Rating prompt */}
          {needsRating && !showRating && (
            <Button onClick={() => setShowRating(true)} className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="rate-trade-btn">
              <Star className="w-4 h-4 mr-1" /> Rate @{otherUser?.username}
            </Button>
          )}

          {showRating && (
            <div className="border border-honey/30 rounded-lg p-3 space-y-3 bg-honey/5">
              <p className="text-sm font-medium">Rate your trade with @{otherUser?.username}</p>
              <div className="flex gap-1 justify-center">
                {[1, 2, 3, 4, 5].map(v => (
                  <button key={v} onClick={() => setRatingValue(v)} className="p-1 transition-transform hover:scale-110" data-testid={`rating-star-${v}`}>
                    <Star className={`w-8 h-8 ${v <= ratingValue ? 'fill-honey text-honey' : 'text-gray-300'}`} />
                  </button>
                ))}
              </div>
              <Textarea placeholder="How was the experience? (optional)" value={ratingReview} onChange={e => setRatingReview(e.target.value)} className="text-sm border-honey/50 resize-none" rows={2} data-testid="rating-review-input" />
              <Button onClick={handleRate} disabled={loading || ratingValue === 0} className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full text-sm" data-testid="submit-rating-btn">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Star className="w-4 h-4 mr-1" />}
                Submit Rating ({ratingValue}/5)
              </Button>
            </div>
          )}

          {/* Existing ratings display */}
          {trade.ratings && Object.keys(trade.ratings).length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">RATINGS</p>
              {Object.entries(trade.ratings).map(([uid, r]) => {
                const rater = uid === trade.initiator_id ? trade.initiator : trade.responder;
                return (
                  <div key={uid} className="flex items-center gap-2 text-sm py-1">
                    <span className="text-xs text-muted-foreground">@{rater?.username}:</span>
                    <div className="flex gap-0.5">{[1,2,3,4,5].map(v => <Star key={v} className={`w-3 h-3 ${v <= r.rating ? 'fill-honey text-honey' : 'text-gray-300'}`} />)}</div>
                    {r.review && <span className="text-xs text-muted-foreground ml-1">"{r.review}"</span>}
                  </div>
                );
              })}
            </div>
          )}

          {/* Messages */}
          {trade.messages?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">MESSAGES</p>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {trade.messages.map((msg, i) => {
                  const isMine = msg.user_id === currentUserId;
                  const sender = msg.user_id === trade.initiator_id ? trade.initiator : trade.responder;
                  return (
                    <div key={i} className={`text-sm p-2 rounded-lg ${isMine ? 'bg-honey/10 ml-6' : 'bg-gray-50 mr-6'}`}>
                      <span className="text-xs font-medium">@{sender?.username}</span>
                      <p className="text-sm mt-0.5">{msg.text}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Message input */}
          {['PROPOSED', 'COUNTERED', 'HOLD_PENDING', 'SHIPPING', 'CONFIRMING'].includes(trade.status) && (
            <div className="flex gap-2">
              <Input placeholder="Send a message..." value={messageText} onChange={e => setMessageText(e.target.value)} className="border-honey/50 text-sm"
                onKeyDown={e => e.key === 'Enter' && handleSendMessage()} data-testid="trade-message-input" />
              <Button size="sm" onClick={handleSendMessage} className="bg-honey text-vinyl-black hover:bg-honey-amber" data-testid="trade-send-msg-btn">
                <MessageSquare className="w-4 h-4" />
              </Button>
            </div>
          )}

          {/* Counter form */}
          {showCounter && (
            <div className="border border-blue-200 rounded-lg p-3 space-y-3 bg-blue-50/50">
              <p className="text-sm font-medium text-blue-700">Counter Offer</p>
              <div>
                <label className="text-xs font-medium mb-1 block">Request different record (optional)</label>
                <Button size="sm" variant="outline" onClick={fetchOtherRecords} className="text-xs w-full mb-2">
                  {loadingRecords ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Search className="w-3 h-3 mr-1" />}
                  Browse @{isInitiator ? trade.responder?.username : trade.initiator?.username}'s collection
                </Button>
                {otherRecords.length > 0 && (
                  <Select value={counterRecordId} onValueChange={setCounterRecordId}>
                    <SelectTrigger className="text-sm border-blue-200"><SelectValue placeholder="Pick a different record..." /></SelectTrigger>
                    <SelectContent>{otherRecords.map(r => <SelectItem key={r.id} value={r.id}>{r.artist} · {r.title}</SelectItem>)}</SelectContent>
                  </Select>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Input placeholder="Sweetener amount ($)" type="number" value={counterBoot} onChange={e => setCounterBoot(e.target.value)} className="text-sm border-blue-200" />
                <Select value={counterBootDir} onValueChange={setCounterBootDir}>
                  <SelectTrigger className="text-sm border-blue-200"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="TO_SELLER">Sweetener to seller</SelectItem>
                    <SelectItem value="TO_BUYER">Sweetener to buyer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Textarea placeholder="Message (optional)" value={counterMessage} onChange={e => setCounterMessage(e.target.value)} className="text-sm border-blue-200 resize-none" rows={2} />
              <div className="flex gap-2">
                <Button onClick={handleCounter} disabled={loading} className="flex-1 bg-blue-600 text-white hover:bg-blue-700 rounded-full text-sm" data-testid="counter-submit-btn">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <ArrowRightLeft className="w-4 h-4 mr-1" />}
                  Send Counter
                </Button>
                <Button variant="outline" onClick={() => setShowCounter(false)} className="rounded-full text-sm">Cancel</Button>
              </div>
            </div>
          )}

          {/* Phase 1 action buttons */}
          {(canAccept || canDecline) && !showCounter && (
            <div className="flex gap-2 pt-2">
              {canAccept && (
                <Button onClick={handleAccept} disabled={loading} className="flex-1 bg-green-600 text-white hover:bg-green-700 rounded-full" data-testid="trade-accept-btn">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Check className="w-4 h-4 mr-1" />}
                  Accept Trade
                </Button>
              )}
              {canCounter && (
                <Button onClick={() => setShowCounter(true)} variant="outline" className="flex-1 rounded-full border-blue-300 text-blue-700 hover:bg-blue-50" data-testid="trade-counter-btn">
                  <ArrowRightLeft className="w-4 h-4 mr-1" /> Counter
                </Button>
              )}
              {canDecline && (
                <Button onClick={handleDecline} disabled={loading} variant="outline" className="rounded-full border-red-200 text-red-600 hover:bg-red-50 px-4" data-testid="trade-decline-btn">
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ======= Mini photo upload =======
const PhotoUploadMini = ({ photos, setPhotos, label }) => {
  const handleSelect = (e) => {
    const files = Array.from(e.target.files || []);
    const { validateImageFile } = require('../utils/imageUpload');
    const valid = [];
    for (const f of files.slice(0, 5 - photos.length)) {
      const err = validateImageFile(f);
      if (err) { toast.error(err); continue; }
      valid.push({ file: f, preview: URL.createObjectURL(f) });
    }
    if (valid.length) setPhotos(prev => [...prev, ...valid]);
  };
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <div className="flex gap-2 items-center">
        {photos.map((p, i) => (
          <div key={i} className="relative w-12 h-12">
            <img src={p.preview} alt="" className="w-12 h-12 rounded object-cover border" />
            <button onClick={() => setPhotos(prev => prev.filter((_, j) => j !== i))} className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-[8px]">x</button>
          </div>
        ))}
        {photos.length < 5 && (
          <label className="w-12 h-12 border-2 border-dashed border-gray-300 rounded flex items-center justify-center cursor-pointer hover:border-gray-400">
            <Camera className="w-4 h-4 text-gray-400" />
            <input type="file" accept=".jpg,.jpeg,.png,.webp,.heic,.heif" multiple onChange={handleSelect} className="hidden" />
          </label>
        )}
      </div>
    </div>
  );
};

const RecordDetail = ({ record, condition, photoUrls }) => (
  <div className="bg-white rounded-lg p-2 border border-honey/20">
    {photoUrls?.length > 0 ? (
      <div className="relative">
        <img src={photoUrls[0]} alt="" className="w-full aspect-square rounded-lg object-cover mb-2" />
        {photoUrls.length > 1 && (
          <div className="flex gap-1 mt-1 overflow-x-auto pb-1">
            {photoUrls.slice(1).map((url, i) => (
              <img key={i} src={url} alt="" className="w-10 h-10 rounded object-cover border border-honey/20 shrink-0" />
            ))}
          </div>
        )}
      </div>
    ) : record?.cover_url ? (
      <AlbumArt src={record.cover_url} alt={`${record.artist} ${record.title} vinyl record`} className="w-full aspect-square rounded-lg object-cover mb-2" isUnofficial={record.is_unofficial} />
    ) : (
      <div className="w-full aspect-square rounded-lg bg-honey/10 flex items-center justify-center mb-2"><Disc className="w-8 h-8 text-honey" /></div>
    )}
    <p className="text-sm font-heading truncate">{record?.title || record?.album || 'Unknown'}</p>
    <p className="text-xs text-muted-foreground truncate">{record?.artist || ''}</p>
    {condition && <GradeLabel condition={condition} variant="compact" />}
  </div>
);

import { GRADE_OPTIONS } from '../utils/grading';
import { GradeLabel } from '../components/GradeLabel';

// ======= Propose Trade Modal (exported for ISOPage) =======

// Hold Explainer Link Component
const HoldExplainerLink = () => {
  const [showExplainer, setShowExplainer] = useState(false);
  return (
    <>
      <button
        onClick={() => setShowExplainer(true)}
        className="text-[11px] text-amber-600 hover:text-amber-700 hover:underline flex items-center gap-1"
        data-testid="hold-explainer-trigger"
      >
        <HelpCircle className="w-3 h-3" /> How does this work?
      </button>
      <Dialog open={showExplainer} onOpenChange={setShowExplainer}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2"><Shield className="w-5 h-5 text-honey-amber" /> How Mutual Hold Works</DialogTitle>
            <DialogDescription>Protecting both parties in every trade</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2 text-sm text-muted-foreground" data-testid="hold-explainer-modal">
            <div className="space-y-3">
              <div className="flex gap-3 items-start">
                <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold shrink-0">1</span>
                <p><strong className="text-vinyl-black">Both parties are charged.</strong> When a trade is accepted, both the proposer and the seller are charged the hold amount. This ensures both parties have skin in the game.</p>
              </div>
              <div className="flex gap-3 items-start">
                <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold shrink-0">2</span>
                <p><strong className="text-vinyl-black">Ship your records.</strong> Once both holds are paid, both parties ship their records and enter tracking info.</p>
              </div>
              <div className="flex gap-3 items-start">
                <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold shrink-0">3</span>
                <p><strong className="text-vinyl-black">Confirm delivery.</strong> When both parties confirm they received their records, the hold is fully refunded to both parties.</p>
              </div>
              <div className="flex gap-3 items-start">
                <span className="w-6 h-6 rounded-full bg-red-100 text-red-600 flex items-center justify-center text-xs font-bold shrink-0">!</span>
                <p><strong className="text-vinyl-black">Disputes.</strong> If something goes wrong, either party can open a dispute. An admin will review and decide how to resolve it · including potentially releasing funds to the affected party.</p>
              </div>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs text-amber-800">The hold amount should reflect the approximate value of the records being traded. Higher holds = more protection for both parties.</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export const ProposeTradeModal = ({ open, onOpenChange, listing, token, API, onSuccess, feePct = 6 }) => {
  const { user: currentUser } = useAuth();
  const [records, setRecords] = useState([]);
  const [selectedRecordId, setSelectedRecordId] = useState('');
  const [offeredCondition, setOfferedCondition] = useState('');
  const [offeredPhotos, setOfferedPhotos] = useState([]);
  const [uploadingPhotos, setUploadingPhotos] = useState(false);
  const [bootAmount, setBootAmount] = useState('');
  const [bootDirection, setBootDirection] = useState('TO_SELLER');
  const [holdAmount, setHoldAmount] = useState('');
  const [holdSuggestion, setHoldSuggestion] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingRecords, setLoadingRecords] = useState(true);

  useEffect(() => {
    if (open && token && currentUser?.username) {
      setLoadingRecords(true);
      axios.get(`${API}/users/${currentUser.username}/records`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => setRecords(r.data)).catch(() => {}).finally(() => setLoadingRecords(false));
    }
  }, [open, API, token, currentUser?.username]);

  const handlePhotoSelect = (e) => {
    const files = Array.from(e.target.files || []);
    const remaining = 5 - offeredPhotos.length;
    if (remaining <= 0) { toast.error('Maximum 5 photos'); return; }
    const { validateImageFile } = require('../utils/imageUpload');
    const valid = [];
    for (const f of files.slice(0, remaining)) {
      const err = validateImageFile(f);
      if (err) { toast.error(err); continue; }
      valid.push({ file: f, preview: URL.createObjectURL(f) });
    }
    if (valid.length) setOfferedPhotos(prev => [...prev, ...valid]);
  };

  const removePhoto = (idx) => {
    setOfferedPhotos(prev => { const r = prev[idx]; if (r.preview) URL.revokeObjectURL(r.preview); return prev.filter((_, i) => i !== idx); });
  };

  const handlePropose = async () => {
    if (!selectedRecordId) { toast.error('Select a record to offer'); return; }
    if (!offeredCondition) { toast.error('Select the condition of your record'); return; }
    if (offeredPhotos.length === 0) { toast.error('Add at least 1 photo of your record'); return; }
    const holdVal = parseFloat(holdAmount) || (holdSuggestion?.suggested_hold || 50);
    if (holdVal < 10) { toast.error('Hold amount must be at least $10'); return; }
    setLoading(true);
    try {
      // Upload photos first
      setUploadingPhotos(true);
      const photoUrls = [];
      for (const photo of offeredPhotos) {
        const fd = new FormData(); fd.append('file', photo.file);
        const r = await axios.post(`${API}/upload`, fd, { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } });
        photoUrls.push(r.data.path);
      }
      setUploadingPhotos(false);

      await axios.post(`${API}/trades`, {
        listing_id: listing.id, offered_record_id: selectedRecordId,
        offered_condition: offeredCondition,
        offered_photo_urls: photoUrls,
        boot_amount: bootAmount ? parseFloat(bootAmount) : null,
        boot_direction: bootAmount ? bootDirection : null,
        hold_amount: holdVal,
        message: message || null,
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('trade proposal sent.'); trackEvent('trade_proposed'); onOpenChange(false); onSuccess?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); setUploadingPhotos(false); }
    finally { setLoading(false); }
  };

  const reset = () => {
    setSelectedRecordId(''); setOfferedCondition(''); setBootAmount(''); setBootDirection('TO_SELLER'); setMessage('');
    setHoldAmount(''); setHoldSuggestion(null);
    offeredPhotos.forEach(p => p.preview && URL.revokeObjectURL(p.preview));
    setOfferedPhotos([]);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) reset(); onOpenChange(o); }}>
      <DialogContent className="sm:max-w-md max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-heading flex items-center gap-2"><ArrowRightLeft className="w-5 h-5 text-honey" /> Propose a Trade</DialogTitle>
          <DialogDescription>Offer a record from your vault</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">THEY HAVE</p>
            <div className="flex items-center gap-3 bg-honey/10 rounded-lg p-3">
              {listing?.cover_url ? <AlbumArt src={listing.cover_url} alt={`${listing.artist} ${listing.album} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow" isUnofficial={listing.is_unofficial} />
                : listing?.photo_urls?.[0] ? <AlbumArt src={listing.photo_urls[0]} alt={`${listing.artist} ${listing.album} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow" isUnofficial={listing.is_unofficial} />
                : <div className="w-14 h-14 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
              <div>
                <p className="font-heading text-base">{listing?.album}</p>
                <p className="text-sm text-muted-foreground">{listing?.artist}</p>
                {listing?.condition && <GradeLabel condition={listing.condition} variant="compact" />}
              </div>
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">YOU OFFER</p>
            {loadingRecords ? <Skeleton className="h-10 w-full" /> : records.length === 0 ? (
              <p className="text-sm text-muted-foreground">No records in your vault to offer.</p>
            ) : (
              <Select value={selectedRecordId} onValueChange={setSelectedRecordId}>
                <SelectTrigger className="border-honey/50" data-testid="trade-offer-select"><SelectValue placeholder="Choose a record from your collection" /></SelectTrigger>
                <SelectContent>{records.map(r => <SelectItem key={r.id} value={r.id}>{r.artist} · {r.title}</SelectItem>)}</SelectContent>
              </Select>
            )}
          </div>

          {/* Condition selection */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">CONDITION <span className="text-red-400">*</span></p>
            <div className="flex flex-wrap gap-1.5">
              {GRADE_OPTIONS.map(g => (
                <button key={g.value} onClick={() => setOfferedCondition(g.value)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${offeredCondition === g.value ? 'bg-honey text-vinyl-black shadow-sm ring-2 ring-honey/50' : 'bg-honey/10 text-muted-foreground hover:bg-honey/20'}`}
                  data-testid={`offer-condition-${g.value.toLowerCase().replace(/\+/g, 'plus')}`}>{g.label}</button>
              ))}
            </div>
          </div>

          {/* Photo upload */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">PHOTOS <span className="text-red-400">*</span> <span className="font-normal">(1-5 of your record)</span></p>
            <div className="flex gap-2 flex-wrap">
              {offeredPhotos.map((p, i) => (
                <div key={i} className="relative w-16 h-16 rounded-lg overflow-hidden border border-honey/30 group">
                  <img src={p.preview} alt="" className="w-full h-full object-cover" />
                  <button onClick={() => removePhoto(i)} className="absolute top-0.5 right-0.5 bg-black/60 rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity" data-testid={`remove-offer-photo-${i}`}>
                    <X className="w-3 h-3 text-white" />
                  </button>
                </div>
              ))}
              {offeredPhotos.length < 5 && (
                <label className="w-16 h-16 rounded-lg border-2 border-dashed border-honey/40 flex flex-col items-center justify-center cursor-pointer hover:border-honey hover:bg-honey/5 transition-all" data-testid="add-offer-photo-btn">
                  <Camera className="w-4 h-4 text-honey mb-0.5" />
                  <span className="text-[9px] text-muted-foreground">{offeredPhotos.length}/5</span>
                  <input type="file" accept=".jpg,.jpeg,.png,.webp,.heic,.heif" multiple onChange={handlePhotoSelect} className="hidden" />
                </label>
              )}
            </div>
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">SWEETENER <span className="font-normal">(cash on top, optional)</span></p>
            <p className="text-[10px] text-muted-foreground mb-2 italic">A sweetener balances value between records. {feePct}% platform fee applies to the sweetener amount only.</p>
            <div className="grid grid-cols-2 gap-2">
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input placeholder="Amount" type="number" value={bootAmount} onChange={e => setBootAmount(e.target.value)} className="pl-9 border-honey/50" data-testid="trade-sweetener-amount" />
              </div>
              <Select value={bootDirection} onValueChange={setBootDirection}>
                <SelectTrigger className="border-honey/50"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="TO_SELLER">You pay sweetener</SelectItem>
                  <SelectItem value="TO_BUYER">They pay sweetener</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {bootAmount && parseFloat(bootAmount) > 0 && (
              <p className="text-xs text-muted-foreground mt-1.5">
                Fee: ${(parseFloat(bootAmount) * feePct / 100).toFixed(2)} &middot; Recipient gets ${(parseFloat(bootAmount) * (100 - feePct) / 100).toFixed(2)}
              </p>
            )}
          </div>

          {/* Hold Amount (always required) */}
          <div className="bg-amber-50/50 border border-amber-200/50 rounded-xl p-4" data-testid="hold-amount-section">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-honey-amber" />
                <span className="text-xs font-medium text-honey-amber">HOLD AMOUNT</span>
              </div>
              <HoldExplainerLink />
            </div>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-amber-600" />
              <Input
                type="number"
                min="10"
                placeholder={holdSuggestion ? holdSuggestion.suggested_hold.toFixed(2) : '50.00'}
                value={holdAmount}
                onChange={e => setHoldAmount(e.target.value)}
                className="pl-9 border-amber-300 bg-white"
                data-testid="hold-amount-input"
              />
            </div>
            {holdSuggestion && (
              <p className="text-xs text-amber-700 mt-2">{holdSuggestion.label}</p>
            )}
            {!holdSuggestion && (
              <p className="text-xs text-amber-600/70 mt-2">Suggested based on estimated record values. Both parties will be charged this amount and fully refunded on confirmed delivery.</p>
            )}
            {holdAmount && parseFloat(holdAmount) < 10 && (
              <p className="text-xs text-red-500 mt-1">Minimum hold amount is $10</p>
            )}
          </div>

          <Textarea placeholder="Message to seller (optional)" value={message} onChange={e => setMessage(e.target.value)} className="border-honey/50 resize-none" rows={2} data-testid="trade-message-input" />
          <Button onClick={handlePropose} disabled={loading || !selectedRecordId || !offeredCondition || offeredPhotos.length === 0} className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="trade-propose-btn">
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <ArrowRightLeft className="w-4 h-4 mr-2" />}
            {uploadingPhotos ? 'Uploading photos...' : 'Propose Trade'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TradesPage;
