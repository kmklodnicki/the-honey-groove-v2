import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { resolveImageUrl } from '../utils/imageUrl';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { UserPlus, UserMinus, Loader2, Disc } from 'lucide-react';
import { toast } from 'sonner';

const UserRow = ({ u, currentUserId, token, API, onFollowChange }) => {
  const [following, setFollowing] = useState(u.is_following);
  const [loading, setLoading] = useState(false);
  const isMe = u.id === currentUserId;

  const toggle = async () => {
    setLoading(true);
    try {
      if (following) {
        await axios.delete(`${API}/follow/${u.username}`, { headers: { Authorization: `Bearer ${token}` }});
      } else {
        await axios.post(`${API}/follow/${u.username}`, {}, { headers: { Authorization: `Bearer ${token}` }});
      }
      setFollowing(!following);
      onFollowChange?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-3 py-3 border-b border-honey/10 last:border-0" data-testid={`user-row-${u.username}`}>
      <Link to={`/profile/${u.username}`} className="flex items-center gap-3 flex-1 min-w-0">
        <Avatar className="h-10 w-10 border-2 border-honey/30">
          {u.avatar_url && <AvatarImage src={resolveImageUrl(u.avatar_url)} />}
          <AvatarFallback className="bg-honey-soft text-vinyl-black text-sm font-heading">
            {u.username?.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <p className="font-medium text-sm truncate">@{u.username}</p>
          {u.bio && <p className="text-xs text-muted-foreground truncate">{u.bio}</p>}
          {!isMe && u.records_in_common > 0 ? (
            <p className="text-xs text-amber-700 flex items-center gap-1" data-testid={`common-records-${u.username}`}>
              <Disc className="w-3 h-3" /> {u.records_in_common} record{u.records_in_common !== 1 ? 's' : ''} in common
            </p>
          ) : u.record_count !== undefined ? (
            <p className="text-xs text-muted-foreground">{u.record_count} records</p>
          ) : null}
        </div>
      </Link>
      {!isMe && token && (
        <Button
          size="sm"
          variant={following ? "outline" : "default"}
          onClick={toggle}
          disabled={loading}
          className={`shrink-0 rounded-full text-xs px-4 ${
            following
              ? 'border-vinyl-black/30 hover:bg-red-50 hover:text-red-600 hover:border-red-200'
              : 'bg-honey text-vinyl-black hover:bg-honey-amber'
          }`}
          data-testid={`follow-toggle-${u.username}`}
        >
          {loading ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : following ? (
            <><UserMinus className="w-3 h-3 mr-1" />Following</>
          ) : (
            <><UserPlus className="w-3 h-3 mr-1" />Follow</>
          )}
        </Button>
      )}
    </div>
  );
};

const FollowListModal = ({ open, onOpenChange, username, listType, onFollowChange }) => {
  const { user, token, API } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && username) {
      setLoading(true);
      const url = listType === 'followers'
        ? `${API}/users/${username}/followers`
        : `${API}/users/${username}/following`;

      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      axios.get(url, { headers })
        .then(res => setUsers(res.data))
        .catch(() => toast.error(`Failed to load ${listType}`))
        .finally(() => setLoading(false));
    }
  }, [open, username, listType, API, token]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="font-heading capitalize">{listType}</DialogTitle>
          <DialogDescription>@{username}'s {listType}</DialogDescription>
        </DialogHeader>
        <div className="overflow-y-auto max-h-[60vh]" data-testid={`${listType}-list`}>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-honey" />
            </div>
          ) : users.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {listType === 'followers' ? 'No followers yet' : 'Not following anyone yet'}
            </p>
          ) : (
            users.map(u => (
              <UserRow
                key={u.id}
                u={u}
                currentUserId={user?.id}
                token={token}
                API={API}
                onFollowChange={onFollowChange}
              />
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export { FollowListModal, UserRow };
