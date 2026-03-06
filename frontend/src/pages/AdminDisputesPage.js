import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { AlertTriangle, ArrowRightLeft, CheckCircle2, XCircle, Loader2, Disc, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { usePageTitle } from '../hooks/usePageTitle';

const AdminDisputesPage = () => {
  usePageTitle('Admin Disputes');
  const { token, API } = useAuth();
  const [disputes, setDisputes] = useState([]);
  const [allDisputes, setAllDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('open');
  const [selected, setSelected] = useState(null);
  const [showResolve, setShowResolve] = useState(false);

  const fetchDisputes = useCallback(async () => {
    try {
      const [open, all] = await Promise.all([
        axios.get(`${API}/admin/disputes`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/disputes/all`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      setDisputes(open.data);
      setAllDisputes(all.data);
    } catch (err) {
      if (err.response?.status === 403) toast.error('admin access required.');
    }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchDisputes(); }, [fetchDisputes]);

  const openDisputes = disputes;
  const resolvedDisputes = allDisputes.filter(t => t.dispute?.resolution);

  if (loading) return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-16 md:pt-24">
      <Skeleton className="h-10 w-64 mb-6" />
      {[1, 2].map(i => <Skeleton key={i} className="h-40 w-full mb-4" />)}
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24" data-testid="admin-disputes-page">
      <div className="mb-6">
        <h1 className="font-heading text-3xl text-vinyl-black flex items-center gap-2">
          <AlertTriangle className="w-7 h-7 text-red-500" /> Dispute Review
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Admin dashboard for trade dispute resolution</p>
      </div>

      <div className="flex gap-2 mb-6">
        <Button variant={tab === 'open' ? 'default' : 'outline'} onClick={() => setTab('open')}
          className={tab === 'open' ? 'bg-red-600 text-white' : ''} data-testid="tab-open-disputes">
          Open ({openDisputes.length})
        </Button>
        <Button variant={tab === 'resolved' ? 'default' : 'outline'} onClick={() => setTab('resolved')}
          className={tab === 'resolved' ? 'bg-green-600 text-white' : ''} data-testid="tab-resolved-disputes">
          Resolved ({resolvedDisputes.length})
        </Button>
      </div>

      {tab === 'open' && (
        openDisputes.length === 0 ? (
          <Card className="p-8 text-center border-honey/30">
            <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-4" />
            <h3 className="font-heading text-xl mb-2">No open disputes</h3>
            <p className="text-muted-foreground text-sm">All disputes have been resolved.</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {openDisputes.map(trade => (
              <DisputeCard key={trade.id} trade={trade} onSelect={() => { setSelected(trade); setShowResolve(true); }} />
            ))}
          </div>
        )
      )}

      {tab === 'resolved' && (
        resolvedDisputes.length === 0 ? (
          <Card className="p-8 text-center border-honey/30">
            <p className="text-muted-foreground text-sm">No resolved disputes yet.</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {resolvedDisputes.map(trade => <DisputeCard key={trade.id} trade={trade} resolved />)}
          </div>
        )
      )}

      {selected && (
        <ResolveModal open={showResolve} onOpenChange={(o) => { if (!o) { setShowResolve(false); setSelected(null); } }}
          trade={selected} token={token} API={API} onResolved={fetchDisputes} />
      )}
    </div>
  );
};

const DisputeCard = ({ trade, onSelect, resolved }) => {
  const d = trade.dispute;
  const opener = d.opened_by === trade.initiator_id ? trade.initiator : trade.responder;
  const other = d.opened_by === trade.initiator_id ? trade.responder : trade.initiator;

  return (
    <Card className={`p-5 border-l-4 ${resolved ? 'border-l-green-400' : 'border-l-red-400'}`} data-testid={`dispute-card-${trade.id}`}>
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="font-heading text-base">Trade #{trade.id.slice(0, 8)}</p>
          <p className="text-xs text-muted-foreground">
            @{trade.initiator?.username} <ArrowRightLeft className="w-3 h-3 inline mx-1" /> @{trade.responder?.username}
            <span className="ml-2">{formatDistanceToNow(new Date(d.opened_at), { addSuffix: true })}</span>
          </p>
        </div>
        {!resolved && onSelect && (
          <Button size="sm" className="bg-red-600 text-white hover:bg-red-700" onClick={onSelect} data-testid={`resolve-dispute-${trade.id}`}>
            Resolve
          </Button>
        )}
        {resolved && d.resolution && (
          <span className={`px-2 py-1 rounded-full text-xs font-bold ${
            d.resolution.outcome === 'COMPLETED' ? 'bg-green-100 text-green-700' :
            d.resolution.outcome === 'CANCELLED' ? 'bg-red-100 text-red-700' :
            'bg-amber-100 text-amber-700'
          }`}>{d.resolution.outcome}</span>
        )}
      </div>

      {/* The exchange */}
      <div className="flex items-center gap-3 bg-gray-50 rounded-lg p-3 mb-3">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {trade.offered_record?.cover_url ? <img src={trade.offered_record.cover_url} alt="" className="w-10 h-10 rounded object-cover" />
            : <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>}
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{trade.offered_record?.title || 'Unknown'}</p>
            <p className="text-xs text-muted-foreground">@{trade.initiator?.username}</p>
          </div>
        </div>
        <ArrowRightLeft className="w-4 h-4 text-honey shrink-0" />
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{trade.listing_record?.album || 'Unknown'}</p>
            <p className="text-xs text-muted-foreground">@{trade.responder?.username}</p>
          </div>
        </div>
      </div>

      {/* Dispute reason */}
      <div className="bg-red-50 rounded-lg p-3 mb-2">
        <p className="text-xs font-medium text-red-700 mb-1">Dispute by @{opener?.username}</p>
        <p className="text-sm">{d.reason}</p>
        {d.photo_urls?.length > 0 && (
          <div className="flex gap-2 mt-2">{d.photo_urls.map((url, i) => <img key={i} src={url} alt="" className="w-16 h-16 rounded object-cover border" />)}</div>
        )}
      </div>

      {/* Response */}
      {d.response && (
        <div className="bg-blue-50 rounded-lg p-3 mb-2">
          <p className="text-xs font-medium text-blue-700 mb-1">Response by @{other?.username}</p>
          <p className="text-sm">{d.response.text}</p>
          {d.response.photo_urls?.length > 0 && (
            <div className="flex gap-2 mt-2">{d.response.photo_urls.map((url, i) => <img key={i} src={url} alt="" className="w-16 h-16 rounded object-cover border" />)}</div>
          )}
        </div>
      )}

      {!d.response && !resolved && (
        <p className="text-xs text-red-500 flex items-center gap-1"><Clock className="w-3 h-3" /> Awaiting response — due {formatDistanceToNow(new Date(d.response_deadline), { addSuffix: true })}</p>
      )}

      {/* Resolution details */}
      {d.resolution && (
        <div className="bg-green-50 rounded-lg p-3 border border-green-200">
          <p className="text-xs font-medium text-green-700">Resolution: {d.resolution.outcome}</p>
          <p className="text-sm text-muted-foreground">{d.resolution.notes}</p>
          {d.resolution.partial_amount && <p className="text-sm font-medium mt-1">${d.resolution.partial_amount} cash difference owed</p>}
        </div>
      )}
    </Card>
  );
};

const ResolveModal = ({ open, onOpenChange, trade, token, API, onResolved }) => {
  const [resolution, setResolution] = useState('');
  const [notes, setNotes] = useState('');
  const [partialAmount, setPartialAmount] = useState('');
  const [loading, setLoading] = useState(false);

  const handleResolve = async () => {
    if (!resolution || !notes.trim()) { toast.error('select a resolution and add notes.'); return; }
    setLoading(true);
    try {
      await axios.put(`${API}/admin/disputes/${trade.id}/resolve`, {
        resolution, notes,
        partial_amount: partialAmount ? parseFloat(partialAmount) : null,
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('dispute resolved.');
      onOpenChange(false);
      onResolved();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-heading flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-red-500" /> Resolve Dispute</DialogTitle>
          <DialogDescription>Trade #{trade.id.slice(0, 8)} — @{trade.initiator?.username} vs @{trade.responder?.username}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div>
            <label className="text-sm font-medium mb-2 block">Resolution</label>
            <Select value={resolution} onValueChange={setResolution}>
              <SelectTrigger data-testid="resolution-select"><SelectValue placeholder="Select outcome..." /></SelectTrigger>
              <SelectContent>
                <SelectItem value="COMPLETED"><CheckCircle2 className="w-4 h-4 inline mr-1 text-green-500" /> Force Complete</SelectItem>
                <SelectItem value="CANCELLED"><XCircle className="w-4 h-4 inline mr-1 text-red-500" /> Full Cancellation</SelectItem>
                <SelectItem value="PARTIAL">Partial — Cash Difference</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {resolution === 'PARTIAL' && (
            <Input placeholder="Cash difference amount ($)" type="number" value={partialAmount} onChange={e => setPartialAmount(e.target.value)}
              className="border-amber-300" data-testid="partial-amount-input" />
          )}
          <Textarea placeholder="Resolution notes (visible to both parties)" value={notes} onChange={e => setNotes(e.target.value)}
            className="resize-none" rows={3} data-testid="resolution-notes-input" />
          <Button onClick={handleResolve} disabled={loading || !resolution || !notes.trim()}
            className="w-full bg-red-600 text-white hover:bg-red-700 rounded-full" data-testid="submit-resolution-btn">
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <AlertTriangle className="w-4 h-4 mr-1" />}
            Resolve Dispute
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AdminDisputesPage;
