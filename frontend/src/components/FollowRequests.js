import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Button } from './ui/button';
import { Check, X, UserPlus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { resolveImageUrl } from '../utils/imageUrl';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from './ui/dialog';

export const FollowRequestsBadge = ({ count, onClick }) => {
  if (!count) return null;
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium hover:bg-amber-100 transition-colors"
      data-testid="follow-requests-badge"
    >
      <UserPlus className="w-3.5 h-3.5" />
      {count} follow request{count !== 1 ? 's' : ''}
    </button>
  );
};

export const FollowRequestsModal = ({ open, onOpenChange }) => {
  const { token, API } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState({});

  useEffect(() => {
    if (open) {
      setLoading(true);
      axios.get(`${API}/follow-requests`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => setRequests(r.data))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [open, API, token]);

  const handleAccept = async (id) => {
    setActionLoading(prev => ({ ...prev, [id]: 'accept' }));
    try {
      await axios.post(`${API}/follow-requests/${id}/accept`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setRequests(prev => prev.filter(r => r.id !== id));
      toast.success('Follow request accepted');
    } catch {
      toast.error('Failed to accept');
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: null }));
    }
  };

  const handleDecline = async (id) => {
    setActionLoading(prev => ({ ...prev, [id]: 'decline' }));
    try {
      await axios.post(`${API}/follow-requests/${id}/decline`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setRequests(prev => prev.filter(r => r.id !== id));
      toast.success('Follow request declined');
    } catch {
      toast.error('Failed to decline');
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: null }));
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-amber-600" /> Follow Requests
          </DialogTitle>
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-stone-400" /></div>
        ) : requests.length === 0 ? (
          <p className="text-center text-sm text-stone-500 py-8">No pending follow requests</p>
        ) : (
          <div className="space-y-1">
            {requests.map(req => (
              <div key={req.id} className="flex items-center gap-3 py-3 border-b border-stone-100 last:border-0" data-testid={`follow-request-${req.from_user.username}`}>
                <Link to={`/profile/${req.from_user.username}`} className="flex items-center gap-3 flex-1 min-w-0" onClick={() => onOpenChange(false)}>
                  <Avatar className="h-10 w-10 border-2 border-honey/30">
                    {req.from_user.avatar_url && <AvatarImage src={resolveImageUrl(req.from_user.avatar_url)} />}
                    <AvatarFallback className="bg-honey-soft text-vinyl-black text-sm font-heading">
                      {req.from_user.username?.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">@{req.from_user.username}</p>
                    {req.from_user.bio && <p className="text-xs text-muted-foreground truncate">{req.from_user.bio}</p>}
                  </div>
                </Link>
                <div className="flex gap-1.5 shrink-0">
                  <Button
                    size="sm"
                    onClick={() => handleAccept(req.id)}
                    disabled={!!actionLoading[req.id]}
                    className="rounded-full bg-honey text-vinyl-black hover:bg-honey-amber h-8 w-8 p-0"
                    data-testid={`accept-request-${req.from_user.username}`}
                  >
                    {actionLoading[req.id] === 'accept' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDecline(req.id)}
                    disabled={!!actionLoading[req.id]}
                    className="rounded-full border-stone-300 h-8 w-8 p-0"
                    data-testid={`decline-request-${req.from_user.username}`}
                  >
                    {actionLoading[req.id] === 'decline' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <X className="w-3.5 h-3.5" />}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
