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
import { ArrowRightLeft, Check, X, MessageSquare, Disc, Loader2, DollarSign, ChevronRight, Search } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { Link } from 'react-router-dom';

const STATUS_CONFIG = {
  PROPOSED: { label: 'Proposed', color: 'bg-amber-100 text-amber-700', dot: 'bg-amber-400' },
  COUNTERED: { label: 'Countered', color: 'bg-blue-100 text-blue-700', dot: 'bg-blue-400' },
  ACCEPTED: { label: 'Accepted', color: 'bg-green-100 text-green-700', dot: 'bg-green-400' },
  DECLINED: { label: 'Declined', color: 'bg-red-100 text-red-700', dot: 'bg-red-400' },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-100 text-gray-600', dot: 'bg-gray-400' },
  SHIPPING: { label: 'Shipping', color: 'bg-purple-100 text-purple-700', dot: 'bg-purple-400' },
  CONFIRMING: { label: 'Confirming', color: 'bg-cyan-100 text-cyan-700', dot: 'bg-cyan-400' },
  COMPLETED: { label: 'Completed', color: 'bg-green-100 text-green-700', dot: 'bg-green-500' },
  DISPUTED: { label: 'Disputed', color: 'bg-red-100 text-red-700', dot: 'bg-red-500' },
};

const TradesPage = () => {
  const { user, token, API } = useAuth();
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('active');
  const [selectedTrade, setSelectedTrade] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const fetchTrades = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/trades`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrades(resp.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchTrades(); }, [fetchTrades]);

  const activeTrades = trades.filter(t => ['PROPOSED', 'COUNTERED', 'ACCEPTED', 'SHIPPING', 'CONFIRMING'].includes(t.status));
  const completedTrades = trades.filter(t => ['COMPLETED', 'DECLINED', 'CANCELLED'].includes(t.status));

  const openDetail = (trade) => {
    setSelectedTrade(trade);
    setShowDetail(true);
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 pt-24">
        <Skeleton className="h-10 w-48 mb-6" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-28 w-full mb-3" />)}
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8" data-testid="trades-page">
      <div className="mb-6">
        <h1 className="font-heading text-3xl text-vinyl-black">My Trades</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your record trades with other collectors</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-honey/10 mb-6 w-full grid grid-cols-2">
          <TabsTrigger value="active" className="data-[state=active]:bg-honey text-sm" data-testid="tab-active-trades">
            Active ({activeTrades.length})
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-honey text-sm" data-testid="tab-trade-history">
            History ({completedTrades.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active">
          {activeTrades.length === 0 ? (
            <Card className="p-8 text-center border-honey/30">
              <ArrowRightLeft className="w-12 h-12 text-honey mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">No active trades</h3>
              <p className="text-muted-foreground text-sm mb-4">Browse TRADE listings in the Market to propose a trade!</p>
              <Link to="/iso">
                <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full">Go to Market</Button>
              </Link>
            </Card>
          ) : (
            <div className="space-y-3">
              {activeTrades.map(trade => (
                <TradeCard key={trade.id} trade={trade} currentUserId={user?.id} onClick={() => openDetail(trade)} />
              ))}
            </div>
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
            <div className="space-y-3">
              {completedTrades.map(trade => (
                <TradeCard key={trade.id} trade={trade} currentUserId={user?.id} onClick={() => openDetail(trade)} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Trade Detail Modal */}
      {selectedTrade && (
        <TradeDetailModal
          open={showDetail}
          onOpenChange={(open) => { if (!open) { setShowDetail(false); setSelectedTrade(null); } }}
          trade={selectedTrade}
          currentUserId={user?.id}
          token={token}
          API={API}
          onUpdate={fetchTrades}
        />
      )}
    </div>
  );
};

// Trade Card Component
const TradeCard = ({ trade, currentUserId, onClick }) => {
  const isInitiator = trade.initiator_id === currentUserId;
  const otherUser = isInitiator ? trade.responder : trade.initiator;
  const sc = STATUS_CONFIG[trade.status] || STATUS_CONFIG.PROPOSED;
  const needsAction = (trade.status === 'PROPOSED' && !isInitiator) || (trade.status === 'COUNTERED' && isInitiator);

  return (
    <Card
      className={`p-4 border-honey/30 cursor-pointer transition-all hover:shadow-md ${needsAction ? 'ring-2 ring-honey/50' : ''}`}
      onClick={onClick}
      data-testid={`trade-card-${trade.id}`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${sc.dot}`} />
          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${sc.color}`}>{sc.label}</span>
          {needsAction && <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-honey text-vinyl-black">Action needed</span>}
        </div>
        <span className="text-xs text-muted-foreground">{formatDistanceToNow(new Date(trade.updated_at), { addSuffix: true })}</span>
      </div>

      {/* Two records side by side */}
      <div className="flex items-center gap-3">
        <RecordMini record={trade.offered_record} label={isInitiator ? 'You offer' : `@${trade.initiator?.username} offers`} />
        <ArrowRightLeft className="w-5 h-5 text-honey shrink-0" />
        <RecordMini record={trade.listing_record} label={isInitiator ? `@${trade.responder?.username}'s` : 'Your listing'} />
      </div>

      {/* Boot info */}
      {trade.boot_amount > 0 && (
        <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
          <DollarSign className="w-3 h-3" />
          ${trade.boot_amount} boot {trade.boot_direction === 'TO_SELLER' ? `to @${trade.responder?.username}` : `to @${trade.initiator?.username}`}
          <span className="text-honey-amber ml-1">(settled directly between traders)</span>
        </div>
      )}

      {/* Counter indicator */}
      {trade.status === 'COUNTERED' && trade.counter && (
        <div className="mt-2 px-3 py-1.5 bg-blue-50 rounded-lg text-xs text-blue-700">
          Counter: {trade.counter.record_id ? 'Different record requested' : ''} {trade.counter.boot_amount ? `$${trade.counter.boot_amount} boot` : ''}
        </div>
      )}

      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-2">
          <Avatar className="h-5 w-5">
            {otherUser?.avatar_url && <AvatarImage src={otherUser.avatar_url} />}
            <AvatarFallback className="text-[10px] bg-honey/20">{otherUser?.username?.charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>
          <span className="text-xs text-muted-foreground">with @{otherUser?.username}</span>
        </div>
        {trade.messages?.length > 0 && (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <MessageSquare className="w-3 h-3" /> {trade.messages.length}
          </span>
        )}
      </div>
    </Card>
  );
};

// Mini record display
const RecordMini = ({ record, label }) => (
  <div className="flex items-center gap-2 flex-1 min-w-0">
    {record?.cover_url ? (
      <img src={record.cover_url} alt="" className="w-12 h-12 rounded-lg object-cover shadow" />
    ) : (
      <div className="w-12 h-12 rounded-lg bg-honey/20 flex items-center justify-center shrink-0">
        <Disc className="w-5 h-5 text-honey" />
      </div>
    )}
    <div className="min-w-0 flex-1">
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className="text-sm font-medium truncate">{record?.title || record?.album || 'Unknown'}</p>
      <p className="text-xs text-muted-foreground truncate">{record?.artist || ''}</p>
    </div>
  </div>
);

// Trade Detail Modal
const TradeDetailModal = ({ open, onOpenChange, trade, currentUserId, token, API, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [showCounter, setShowCounter] = useState(false);
  const [counterMessage, setCounterMessage] = useState('');
  const [counterBoot, setCounterBoot] = useState('');
  const [counterBootDir, setCounterBootDir] = useState('TO_SELLER');
  const [otherRecords, setOtherRecords] = useState([]);
  const [counterRecordId, setCounterRecordId] = useState('');
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [messageText, setMessageText] = useState('');

  const isInitiator = trade.initiator_id === currentUserId;
  const canAccept = (trade.status === 'PROPOSED' && !isInitiator) || (trade.status === 'COUNTERED' && isInitiator);
  const canCounter = (trade.status === 'PROPOSED' && !isInitiator) || (trade.status === 'COUNTERED' && isInitiator);
  const canDecline = ['PROPOSED', 'COUNTERED'].includes(trade.status);
  const sc = STATUS_CONFIG[trade.status] || STATUS_CONFIG.PROPOSED;

  // Fetch other party's collection for counter
  const fetchOtherRecords = async () => {
    const otherUsername = isInitiator ? trade.responder?.username : trade.initiator?.username;
    if (!otherUsername) return;
    setLoadingRecords(true);
    try {
      const resp = await axios.get(`${API}/users/${otherUsername}/records`);
      setOtherRecords(resp.data);
    } catch { /* ignore */ }
    finally { setLoadingRecords(false); }
  };

  const handleAccept = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/trades/${trade.id}/accept`, {}, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Trade accepted!');
      onOpenChange(false);
      onUpdate();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const handleDecline = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/trades/${trade.id}/decline`, {}, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Trade declined');
      onOpenChange(false);
      onUpdate();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const handleCounter = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/trades/${trade.id}/counter`, {
        requested_record_id: counterRecordId || null,
        boot_amount: counterBoot ? parseFloat(counterBoot) : null,
        boot_direction: counterBoot ? counterBootDir : null,
        message: counterMessage || null,
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Counter sent!');
      setShowCounter(false);
      onOpenChange(false);
      onUpdate();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const handleSendMessage = async () => {
    if (!messageText.trim()) return;
    try {
      await axios.post(`${API}/trades/${trade.id}/message`, { text: messageText }, { headers: { Authorization: `Bearer ${token}` } });
      setMessageText('');
      onUpdate();
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
          {/* The Exchange */}
          <div className="bg-honey/5 rounded-xl p-4">
            <p className="text-xs font-medium text-muted-foreground mb-3">THE EXCHANGE</p>
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <p className="text-[10px] text-muted-foreground mb-1">
                  @{trade.initiator?.username} {isInitiator ? '(you)' : ''} offers
                </p>
                <RecordDetail record={trade.offered_record} />
              </div>
              <div className="flex flex-col items-center pt-6">
                <ArrowRightLeft className="w-5 h-5 text-honey" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] text-muted-foreground mb-1">
                  @{trade.responder?.username} {!isInitiator ? '(you)' : ''} has
                </p>
                <RecordDetail record={trade.listing_record} />
              </div>
            </div>
          </div>

          {/* Boot info */}
          {trade.boot_amount > 0 && (
            <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 rounded-lg text-sm">
              <DollarSign className="w-4 h-4 text-amber-600" />
              <span><strong>${trade.boot_amount}</strong> boot {trade.boot_direction === 'TO_SELLER' ? `to @${trade.responder?.username}` : `to @${trade.initiator?.username}`}</span>
              <span className="text-xs text-amber-600 ml-auto">settled directly</span>
            </div>
          )}

          {/* Counter info */}
          {trade.status === 'COUNTERED' && trade.counter && (
            <div className="px-3 py-2 bg-blue-50 rounded-lg text-sm border border-blue-200">
              <p className="font-medium text-blue-700 text-xs mb-1">Counter Offer</p>
              {trade.counter_record && (
                <p className="text-sm">Wants: <strong>{trade.counter_record.title}</strong> by {trade.counter_record.artist}</p>
              )}
              {trade.counter.boot_amount > 0 && (
                <p className="text-sm">${trade.counter.boot_amount} boot {trade.counter.boot_direction === 'TO_SELLER' ? 'to seller' : 'to buyer'}</p>
              )}
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
          {['PROPOSED', 'COUNTERED', 'ACCEPTED'].includes(trade.status) && (
            <div className="flex gap-2">
              <Input
                placeholder="Send a message..."
                value={messageText}
                onChange={e => setMessageText(e.target.value)}
                className="border-honey/50 text-sm"
                onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                data-testid="trade-message-input"
              />
              <Button size="sm" onClick={handleSendMessage} className="bg-honey text-vinyl-black hover:bg-honey-amber" data-testid="trade-send-msg-btn">
                <MessageSquare className="w-4 h-4" />
              </Button>
            </div>
          )}

          {/* Counter Form */}
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
                    <SelectTrigger className="text-sm border-blue-200">
                      <SelectValue placeholder="Pick a different record..." />
                    </SelectTrigger>
                    <SelectContent>
                      {otherRecords.map(r => (
                        <SelectItem key={r.id} value={r.id}>{r.artist} — {r.title}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Input placeholder="Boot amount ($)" type="number" value={counterBoot} onChange={e => setCounterBoot(e.target.value)} className="text-sm border-blue-200" />
                <Select value={counterBootDir} onValueChange={setCounterBootDir}>
                  <SelectTrigger className="text-sm border-blue-200">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="TO_SELLER">Boot to seller</SelectItem>
                    <SelectItem value="TO_BUYER">Boot to buyer</SelectItem>
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

          {/* Action Buttons */}
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

          {/* Accepted state */}
          {trade.status === 'ACCEPTED' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
              <Check className="w-6 h-6 text-green-600 mx-auto mb-1" />
              <p className="text-sm font-medium text-green-700">Trade Accepted!</p>
              <p className="text-xs text-green-600 mt-1">Both parties have agreed. Shipping details coming in Phase 2.</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Record detail card
const RecordDetail = ({ record }) => (
  <div className="bg-white rounded-lg p-2 border border-honey/20">
    {record?.cover_url ? (
      <img src={record.cover_url} alt="" className="w-full aspect-square rounded-lg object-cover mb-2" />
    ) : (
      <div className="w-full aspect-square rounded-lg bg-honey/10 flex items-center justify-center mb-2">
        <Disc className="w-8 h-8 text-honey" />
      </div>
    )}
    <p className="text-sm font-heading truncate">{record?.title || record?.album || 'Unknown'}</p>
    <p className="text-xs text-muted-foreground truncate">{record?.artist || ''}</p>
  </div>
);

// Propose Trade Modal (exported for use in ISOPage)
export const ProposeTradeModal = ({ open, onOpenChange, listing, token, API, onSuccess }) => {
  const { user: currentUser } = useAuth();
  const [records, setRecords] = useState([]);
  const [selectedRecordId, setSelectedRecordId] = useState('');
  const [bootAmount, setBootAmount] = useState('');
  const [bootDirection, setBootDirection] = useState('TO_SELLER');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingRecords, setLoadingRecords] = useState(true);

  useEffect(() => {
    if (open && token && currentUser?.username) {
      setLoadingRecords(true);
      axios.get(`${API}/users/${currentUser.username}/records`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => setRecords(r.data))
        .catch(() => {})
        .finally(() => setLoadingRecords(false));
    }
  }, [open, API, token, currentUser?.username]);

  const handlePropose = async () => {
    if (!selectedRecordId) { toast.error('Select a record to offer'); return; }
    setLoading(true);
    try {
      await axios.post(`${API}/trades`, {
        listing_id: listing.id,
        offered_record_id: selectedRecordId,
        boot_amount: bootAmount ? parseFloat(bootAmount) : null,
        boot_direction: bootAmount ? bootDirection : null,
        message: message || null,
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Trade proposed!');
      onOpenChange(false);
      onSuccess?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to propose'); }
    finally { setLoading(false); }
  };

  const reset = () => {
    setSelectedRecordId('');
    setBootAmount('');
    setBootDirection('TO_SELLER');
    setMessage('');
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) reset(); onOpenChange(o); }}>
      <DialogContent className="sm:max-w-md max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-heading flex items-center gap-2">
            <ArrowRightLeft className="w-5 h-5 text-honey" /> Propose a Trade
          </DialogTitle>
          <DialogDescription>Offer a record from your collection</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* What they have */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">THEY HAVE</p>
            <div className="flex items-center gap-3 bg-honey/10 rounded-lg p-3">
              {listing?.cover_url ? (
                <img src={listing.cover_url} alt="" className="w-14 h-14 rounded-lg object-cover shadow" />
              ) : listing?.photo_urls?.[0] ? (
                <img src={listing.photo_urls[0]} alt="" className="w-14 h-14 rounded-lg object-cover shadow" />
              ) : (
                <div className="w-14 h-14 rounded-lg bg-honey/20 flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>
              )}
              <div>
                <p className="font-heading text-base">{listing?.album}</p>
                <p className="text-sm text-muted-foreground">{listing?.artist}</p>
                {listing?.condition && <p className="text-xs text-honey-amber">{listing.condition}</p>}
              </div>
            </div>
          </div>

          {/* What you offer */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">YOU OFFER</p>
            {loadingRecords ? (
              <Skeleton className="h-10 w-full" />
            ) : records.length === 0 ? (
              <p className="text-sm text-muted-foreground">No records in your collection to offer.</p>
            ) : (
              <Select value={selectedRecordId} onValueChange={setSelectedRecordId}>
                <SelectTrigger className="border-honey/50" data-testid="trade-offer-select">
                  <SelectValue placeholder="Choose a record from your collection" />
                </SelectTrigger>
                <SelectContent>
                  {records.map(r => (
                    <SelectItem key={r.id} value={r.id}>{r.artist} — {r.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Boot (cash on top) */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">BOOT <span className="font-normal">(cash on top, optional)</span></p>
            <div className="grid grid-cols-2 gap-2">
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input placeholder="Amount" type="number" value={bootAmount} onChange={e => setBootAmount(e.target.value)} className="pl-9 border-honey/50" data-testid="trade-boot-amount" />
              </div>
              <Select value={bootDirection} onValueChange={setBootDirection}>
                <SelectTrigger className="border-honey/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="TO_SELLER">You pay boot</SelectItem>
                  <SelectItem value="TO_BUYER">They pay boot</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <p className="text-[10px] text-muted-foreground mt-1">Boot is settled directly between traders</p>
          </div>

          <Textarea placeholder="Message to seller (optional)" value={message} onChange={e => setMessage(e.target.value)} className="border-honey/50 resize-none" rows={2} data-testid="trade-message-input" />

          <Button
            onClick={handlePropose}
            disabled={loading || !selectedRecordId}
            className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full"
            data-testid="trade-propose-btn"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <ArrowRightLeft className="w-4 h-4 mr-2" />}
            Propose Trade
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TradesPage;
