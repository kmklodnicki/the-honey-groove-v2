import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogTitle } from '../components/ui/dialog';
import { Home, Search, User, LogOut, Settings, Library, ShoppingBag, ArrowRightLeft, Bell, Check, MessageCircle, Globe, HelpCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import GlobalSearch from './GlobalSearch';

// Bee icon SVG component
const BeeIcon = ({ className = "w-4 h-4" }) => (
  <svg viewBox="0 0 24 24" className={className} fill="none">
    <ellipse cx="12" cy="14" rx="5" ry="4" fill="#1F1F1F"/>
    <ellipse cx="12" cy="13" rx="3.5" ry="2" fill="#F4B942"/>
    <ellipse cx="12" cy="15" rx="3" ry="1.5" fill="#F4B942"/>
    <circle cx="12" cy="9" r="2.5" fill="#1F1F1F"/>
    <ellipse cx="8" cy="11" rx="2" ry="3" fill="#1F1F1F" opacity="0.3"/>
    <ellipse cx="16" cy="11" rx="2" ry="3" fill="#1F1F1F" opacity="0.3"/>
  </svg>
);

// Avatar with bee fallback
const BeeAvatar = ({ user, className = "h-10 w-10" }) => {
  const firstLetter = user?.username?.charAt(0).toUpperCase() || '?';
  const hasCustomAvatar = user?.avatar_url && !user.avatar_url.includes('dicebear');

  return (
    <Avatar className={`${className} border-2 border-honey`}>
      {hasCustomAvatar && <AvatarImage src={user.avatar_url} alt={user?.username} />}
      <AvatarFallback className="bg-honey-soft text-vinyl-black relative">
        <span className="font-heading">{firstLetter}</span>
        <BeeIcon className="absolute -bottom-0.5 -right-0.5 w-4 h-4" />
      </AvatarFallback>
    </Avatar>
  );
};

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchOpen, setSearchOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <>
    <nav className="hidden md:block fixed top-0 left-0 right-0 z-50 glass border-b border-honey/30">
      <div className="max-w-6xl mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-[88px]">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group" data-testid="nav-logo">
            <img 
              src="/logo-wordmark.png" 
              alt="the Honey Groove" 
              className="h-[104px] group-hover:scale-105 transition-transform"
            />
          </Link>

          {/* Navigation Links */}
          {user && (
            <div className="hidden md:flex items-center gap-1">
              <Link to="/hive" data-testid="nav-hive">
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/hive') ? 'bg-honey/20' : ''}`}
                >
                  <Home className="w-4 h-4" />
                  The Hive
                </Button>
              </Link>
              <Link to="/explore" data-testid="nav-explore">
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/explore') ? 'bg-honey/20' : ''}`}
                >
                  <Globe className="w-4 h-4" />
                  Explore
                </Button>
              </Link>
              <Link to="/collection" data-testid="nav-collection">
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/collection') ? 'bg-honey/20' : ''}`}
                >
                  <Library className="w-4 h-4" />
                  Collection
                </Button>
              </Link>
              <Link to="/honeypot" data-testid="nav-honeypot">
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/honeypot') ? 'bg-honey/20' : ''}`}
                >
                  <ShoppingBag className="w-4 h-4" />
                  The Honeypot
                </Button>
              </Link>
              <Button 
                variant="ghost" 
                className="gap-2"
                onClick={() => setSearchOpen(true)}
                data-testid="nav-search-btn"
              >
                <Search className="w-4 h-4" />
              </Button>
            </div>
          )}

          {/* Right Side */}
          <div className="flex items-center gap-2">
            {user && <DMBadge />}
            {user && <NotificationBell />}
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full" data-testid="user-menu-trigger">
                    <BeeAvatar user={user} className="h-10 w-10" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <div className="flex items-center gap-2 p-2">
                    <BeeAvatar user={user} className="h-8 w-8" />
                    <div className="flex flex-col">
                      <p className="text-sm font-medium">@{user.username}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate(`/profile/${user.username}`)} data-testid="menu-profile">
                    <User className="mr-2 h-4 w-4" />
                    Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/settings')} data-testid="menu-settings">
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => window.open('https://thehoneygroove.com/faq', '_blank')} data-testid="menu-help">
                    <HelpCircle className="mr-2 h-4 w-4" />
                    Help
                  </DropdownMenuItem>
                  {user.is_admin && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => navigate('/admin')} data-testid="menu-admin">
                        <Settings className="mr-2 h-4 w-4" />
                        Admin Panel
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate('/admin/disputes')} data-testid="menu-admin-disputes">
                        <ArrowRightLeft className="mr-2 h-4 w-4" />
                        Disputes
                      </DropdownMenuItem>
                    </>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600" data-testid="menu-logout">
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login">
                  <Button variant="ghost" data-testid="nav-login">Log in</Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

    </nav>

    {/* Mobile Slim Top Bar */}
    {user && (
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 h-[52px] bg-[#FAF6EE] border-b border-[#C8861A]/10" data-testid="mobile-top-bar">
        <div className="flex items-center h-full px-3">
          <Link to="/hive" className="shrink-0 mr-auto overflow-visible">
            <img src="/logo-wordmark.png" alt="the Honey Groove" className="h-[40px] w-auto min-w-[140px] max-w-[160px] object-contain" />
          </Link>
          <div className="flex items-center gap-2 shrink-0">
            <DMBadge />
            <NotificationBell />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full p-0" data-testid="mobile-user-menu">
                  <BeeAvatar user={user} className="h-8 w-8" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <div className="flex items-center gap-2 p-2">
                  <BeeAvatar user={user} className="h-8 w-8" />
                  <div className="flex flex-col">
                    <p className="text-sm font-medium">@{user.username}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate(`/profile/${user.username}`)} data-testid="mobile-menu-profile">
                  <User className="mr-2 h-4 w-4" /> Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/settings')} data-testid="mobile-menu-settings">
                  <Settings className="mr-2 h-4 w-4" /> Settings
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/trades')} data-testid="mobile-menu-trades">
                  <ArrowRightLeft className="mr-2 h-4 w-4" /> Trades
                </DropdownMenuItem>
                {user.is_admin && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => navigate('/admin')} data-testid="mobile-menu-admin">
                      <Settings className="mr-2 h-4 w-4" /> Admin Panel
                    </DropdownMenuItem>
                  </>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600" data-testid="mobile-menu-logout">
                  <LogOut className="mr-2 h-4 w-4" /> Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    )}

    {/* Mobile Bottom Nav */}
    {user && (
      <div
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#FAF6EE] border-t border-[#C8861A]/10"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
        data-testid="mobile-bottom-nav"
      >
        <div className="flex justify-around items-center h-16">
          <Link to="/hive" className="flex items-center justify-center flex-1 h-full" data-testid="mobile-hive">
            <Home className="w-6 h-6" style={{ color: isActive('/hive') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
          </Link>
          <Link to="/explore" className="flex items-center justify-center flex-1 h-full" data-testid="mobile-explore">
            <Globe className="w-6 h-6" style={{ color: isActive('/explore') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
          </Link>
          <button onClick={() => setSearchOpen(true)} className="flex items-center justify-center flex-1 h-full" data-testid="mobile-search">
            <Search className="w-6 h-6" style={{ color: searchOpen ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
          </button>
          <Link to="/collection" className="flex items-center justify-center flex-1 h-full" data-testid="mobile-collection">
            <Library className="w-6 h-6" style={{ color: isActive('/collection') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
          </Link>
          <Link to="/honeypot" className="flex items-center justify-center flex-1 h-full" data-testid="mobile-honeypot">
            <ShoppingBag className="w-6 h-6" style={{ color: isActive('/honeypot') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
          </Link>
        </div>
      </div>
    )}

    {/* Global Search Dialog */}
    <Dialog open={searchOpen} onOpenChange={setSearchOpen}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] p-0 overflow-hidden [&>button:last-child]:hidden" aria-describedby="global-search-desc">
        <DialogTitle className="sr-only">Search</DialogTitle>
        <span id="global-search-desc" className="sr-only">Search records, collectors, and posts</span>
        <GlobalSearch onClose={() => setSearchOpen(false)} />
      </DialogContent>
    </Dialog>
    </>
  );
};

// DM Badge Component
const DMBadge = () => {
  const { token, API } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchCount = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/dm/unread-count`, { headers: { Authorization: `Bearer ${token}` } });
      setUnreadCount(resp.data.count);
    } catch { /* ignore */ }
  }, [API, token]);

  useEffect(() => { fetchCount(); const iv = setInterval(fetchCount, 15000); return () => clearInterval(iv); }, [fetchCount]);

  return (
    <Button variant="ghost" className="relative h-9 w-9 rounded-full" onClick={() => navigate('/messages')} data-testid="dm-badge-btn">
      <MessageCircle className="h-5 w-5 text-vinyl-black" />
      {unreadCount > 0 && (
        <span className="absolute -top-0.5 -right-0.5 bg-honey text-vinyl-black text-[10px] font-bold min-w-[18px] h-[18px] rounded-full flex items-center justify-center" data-testid="dm-unread-badge">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </Button>
  );
};

// Notification Bell Component
const NotificationBell = () => {
  const { token, API } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const prevCountRef = React.useRef(0);
  const hasNotificationAPI = typeof Notification !== 'undefined';
  const [pushEnabled, setPushEnabled] = React.useState(hasNotificationAPI && Notification.permission === 'granted');

  // Request browser notification permission on mount
  useEffect(() => {
    if (hasNotificationAPI && Notification.permission === 'default') {
      Notification.requestPermission().then(p => setPushEnabled(p === 'granted'));
    }
  }, [hasNotificationAPI]);

  const fetchCount = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/notifications/unread-count`, { headers: { Authorization: `Bearer ${token}` } });
      const newCount = resp.data.count;
      // Show browser notification if count increased
      if (hasNotificationAPI && pushEnabled && newCount > prevCountRef.current && prevCountRef.current >= 0) {
        try {
          const latest = await axios.get(`${API}/notifications?limit=1`, { headers: { Authorization: `Bearer ${token}` } });
          if (latest.data.length > 0 && !latest.data[0].read) {
            const n = latest.data[0];
            new Notification('The HoneyGroove', {
              body: n.body || n.title || 'You have a new notification',
              icon: '/favicon.png',
              tag: n.id,
            });
          }
        } catch { /* ignore */ }
      }
      prevCountRef.current = newCount;
      setUnreadCount(newCount);
    } catch { /* ignore */ }
  }, [API, token, pushEnabled]);

  const fetchNotifications = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/notifications?limit=15`, { headers: { Authorization: `Bearer ${token}` } });
      setNotifications(resp.data);
    } catch { /* ignore */ }
  }, [API, token]);

  useEffect(() => {
    fetchCount();
    const interval = setInterval(fetchCount, 15000);
    return () => clearInterval(interval);
  }, [fetchCount]);

  useEffect(() => { if (open) fetchNotifications(); }, [open, fetchNotifications]);

  const markAllRead = async () => {
    try {
      await axios.put(`${API}/notifications/read-all`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch { /* ignore */ }
  };

  const handleClick = async (notif) => {
    if (!notif.read) {
      await axios.put(`${API}/notifications/${notif.id}/read`, {}, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
      setUnreadCount(c => Math.max(0, c - 1));
    }
    setOpen(false);
    const d = notif.data || {};
    if (d.conversation_id) navigate('/messages');
    else if (d.trade_id) navigate('/trades');
    else if (d.follower_username) navigate(`/profile/${d.follower_username}`);
    else if (d.listing_id) navigate('/honeypot');
    else if (d.post_id) navigate('/hive');
  };

  const NOTIF_ICONS = {
    NEW_FOLLOWER: '👤', POST_LIKED: '❤️', NEW_COMMENT: '💬',
    TRADE_PROPOSED: '🤝', TRADE_ACCEPTED: '✅', TRADE_SHIPPED: '📦',
    TRADE_CONFIRMED: '🎉', SALE_COMPLETED: '💰', PURCHASE_COMPLETED: '🛒',
    STRIPE_CONNECTED: '💳', ISO_MATCH: '🔍',
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-9 w-9 rounded-full" data-testid="notification-bell">
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-[#C8861A] text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1" data-testid="notification-badge">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-80 max-h-96 overflow-y-auto" align="end" forceMount>
        <div className="flex items-center justify-between p-2">
          <p className="text-sm font-heading">Notifications</p>
          {unreadCount > 0 && (
            <button onClick={markAllRead} className="text-xs text-honey-amber hover:underline flex items-center gap-1" data-testid="mark-all-read">
              <Check className="w-3 h-3" /> Mark all read
            </button>
          )}
        </div>
        <DropdownMenuSeparator />
        {notifications.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">No notifications yet</div>
        ) : (
          notifications.map(n => (
            <DropdownMenuItem key={n.id} onClick={() => handleClick(n)} className={`flex items-start gap-2 p-2 cursor-pointer ${!n.read ? 'bg-honey/5' : ''}`} data-testid={`notif-${n.id}`}>
              <span className="text-lg mt-0.5 shrink-0">{NOTIF_ICONS[n.type] || '🔔'}</span>
              <div className="flex-1 min-w-0">
                <p className={`text-sm truncate ${!n.read ? 'font-medium' : ''}`}>{n.body}</p>
                <p className="text-[10px] text-muted-foreground">{formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}</p>
              </div>
              {!n.read && <span className="w-2 h-2 rounded-full bg-honey shrink-0 mt-2" />}
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default Navbar;
