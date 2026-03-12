import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom';
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
import { Home, Search, User, LogOut, Settings, Library, ShoppingBag, ArrowRightLeft, Bell, Check, MessageCircle, Globe, HelpCircle, Package, AlertTriangle, Sparkles, Loader2 } from 'lucide-react';
import VerifiedShield from './VerifiedShield';
const KATIE_ID = '4072aaa7-1171-4cd2-9c8f-20dfca8fdc58';
import { formatDistanceToNow } from 'date-fns';
import ReportModal from './ReportModal';
import { resolveImageUrl } from '../utils/imageUrl';
import { prefetchAPI } from '../hooks/useAPI';

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
      {hasCustomAvatar && <AvatarImage src={resolveImageUrl(user.avatar_url)} alt={user?.username} />}
      <AvatarFallback className="bg-honey-soft text-vinyl-black relative">
        <span className="font-heading">{firstLetter}</span>
        <BeeIcon className="absolute -bottom-0.5 -right-0.5 w-4 h-4" />
      </AvatarFallback>
    </Avatar>
  );
};

const Navbar = () => {
  const { user, logout, API, token } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchOpen, setSearchOpen] = useState(false); // kept for legacy, unused
  const [reportOpen, setReportOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  // BLOCK 450: Prefetch route data on hover for instant navigation
  const prefetchRouteMap = {
    '/nectar': ['/explore/trending?limit=10', '/explore/suggested-collectors?limit=8'],
    '/honeypot': ['/listings?limit=20'],
    '/collection': ['/records'],
  };
  const handlePrefetch = (path) => {
    const routes = prefetchRouteMap[path];
    if (routes) routes.forEach(r => prefetchAPI(API, token, r));
  };

  return (
    <>
    <nav className="hidden md:block sticky top-0 z-[1000] glass border-b border-honey/30" style={{ overflow: 'visible', contain: 'none' }}>
      <div className="max-w-6xl mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-[88px]">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group" data-testid="nav-logo">
            <img 
              src="/logo-wordmark.png" 
              alt="the Honey Groove" 
              style={{width: '140px', minWidth: '140px'}}
              className="group-hover:scale-105 transition-all duration-300 object-contain group-hover:drop-shadow-[0_2px_8px_rgba(244,185,66,0.3)]"
            />
          </Link>

          {/* Navigation Links */}
          {user && (
            <div className="hidden md:flex items-center gap-1">
              <Link to="/hive" data-testid="nav-hive" className={`nav-honey-link ${isActive('/hive') ? 'nav-active' : ''}`}>
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/hive') ? 'bg-honey/20 text-[#C8861A]' : ''}`}
                >
                  <Home className="w-4 h-4" />
                  The Hive
                </Button>
              </Link>
              <Link to="/nectar" data-testid="nav-explore" onMouseEnter={() => handlePrefetch('/nectar')} className={`nav-honey-link ${isActive('/nectar') ? 'nav-active' : ''}`}>
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/nectar') ? 'bg-honey/20 text-[#C8861A]' : ''}`}
                >
                  <Globe className="w-4 h-4" />
                  Nectar
                </Button>
              </Link>
              <Link to="/collection" data-testid="nav-collection" onMouseEnter={() => handlePrefetch('/collection')} className={`nav-honey-link ${isActive('/collection') ? 'nav-active' : ''}`}>
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/collection') ? 'bg-honey/20 text-[#C8861A]' : ''}`}
                >
                  <Library className="w-4 h-4" />
                  Collection
                </Button>
              </Link>
              <Link to="/honeypot" data-testid="nav-honeypot" onMouseEnter={() => handlePrefetch('/honeypot')} className={`nav-honey-link ${isActive('/honeypot') ? 'nav-active' : ''}`}>
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/honeypot') ? 'bg-honey/20 text-[#C8861A]' : ''}`}
                >
                  <ShoppingBag className="w-4 h-4" />
                  The Honeypot
                </Button>
              </Link>
              <Link to="/essentials" data-testid="nav-essentials" className={`nav-honey-link ${isActive('/essentials') ? 'nav-active' : ''}`}>
                <Button 
                  variant="outline" 
                  className={`gap-2 border-[#C8861A]/30 text-[#C8861A] hover:bg-[#C8861A]/10 ${isActive('/essentials') ? 'bg-[#C8861A]/15 border-[#C8861A]/50' : ''}`}
                >
                  <Sparkles className="w-4 h-4" />
                  Essentials
                </Button>
              </Link>
              <Button 
                variant="ghost" 
                className="gap-2"
                onClick={() => navigate('/search')}
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
            {user && (
              <Button
                variant="ghost"
                className="relative h-9 w-9 rounded-full"
                onClick={() => setReportOpen(true)}
                data-testid="nav-report-btn"
                title="Report a Problem"
              >
                <AlertTriangle className="h-5 w-5 text-vinyl-black" />
              </Button>
            )}
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full avatar-honey-ring" data-testid="user-menu-trigger">
                    <BeeAvatar user={user} className="h-10 w-10" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56 shadow-[0_10px_15px_-3px_rgba(0,0,0,0.1),0_4px_6px_-2px_rgba(0,0,0,0.05)] backdrop-blur-sm bg-white/95 border border-honey/20" align="end" forceMount style={{ zIndex: 2147483647, position: 'fixed' }}>
                  <div className="flex items-center gap-2 p-2">
                    <BeeAvatar user={user} className="h-8 w-8" />
                    <div className="flex flex-col">
                      <p className="text-sm font-medium flex items-center gap-1">
                        @{user.username}
                        {(user.golden_hive_verified || user.is_admin || user.id === KATIE_ID) && (
                          <VerifiedShield size={14} isFounder={user.is_admin || user.id === KATIE_ID} />
                        )}
                      </p>
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
                  <DropdownMenuItem onClick={() => navigate('/orders')} data-testid="menu-orders">
                    <Package className="mr-2 h-4 w-4" />
                    Orders
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/essentials')} data-testid="menu-essentials">
                    <Sparkles className="mr-2 h-4 w-4" />
                    Honey Essentials
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
      <div className="md:hidden sticky top-0 z-[1000] h-[52px] bg-[#FAF6EE] border-b border-[#C8861A]/10" data-testid="mobile-top-bar" style={{ overflow: 'visible', contain: 'none' }}>
        <div className="flex items-center h-full px-3">
          <Link to="/hive" className="shrink-0 mr-auto overflow-visible">
            <img src="/logo-wordmark.png" alt="the Honey Groove" style={{minWidth: '120px', width: '120px'}} className="object-contain" />
          </Link>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => navigate('/search')}
              className="relative h-8 w-8 flex items-center justify-center rounded-full"
              data-testid="mobile-search-top"
              title="Search"
            >
              <Search className="h-5 w-5 text-vinyl-black" />
            </button>
            <DMBadge />
            <NotificationBell />
            <Button
              variant="ghost"
              className="relative h-8 w-8 rounded-full p-0"
              onClick={() => setReportOpen(true)}
              data-testid="mobile-report-btn"
              title="Report a Problem"
            >
              <AlertTriangle className="h-5 w-5 text-vinyl-black" />
            </Button>
            <MobileProfileMenu user={user} onLogout={handleLogout} />
          </div>
        </div>
      </div>
    )}

    {/* Mobile Bottom Nav */}
    {user && (
      <div
        className="md:hidden fixed bottom-0 left-0 right-0 z-[100000] bg-[#FAF6EE] border-t border-[#C8861A]/10"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
        data-testid="mobile-bottom-nav"
      >
        <div className="flex justify-around items-center h-16">
          <Link to="/hive" className={`mobile-nav-item flex flex-col items-center justify-center flex-1 h-full gap-0.5 ${isActive('/hive') ? 'nav-active' : ''}`} data-testid="mobile-hive">
            <Home className="w-5 h-5 transition-all duration-200" style={{ color: isActive('/hive') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
            <span className="text-[10px] font-medium transition-colors duration-200" style={{ color: isActive('/hive') ? '#C8861A' : 'rgba(138, 107, 74, 0.5)' }}>Hive</span>
            <span className="mobile-nav-dot" />
          </Link>
          <Link to="/nectar" className={`mobile-nav-item flex flex-col items-center justify-center flex-1 h-full gap-0.5 ${isActive('/nectar') ? 'nav-active' : ''}`} data-testid="mobile-explore">
            <Globe className="w-5 h-5 transition-all duration-200" style={{ color: isActive('/nectar') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
            <span className="text-[10px] font-medium transition-colors duration-200" style={{ color: isActive('/nectar') ? '#C8861A' : 'rgba(138, 107, 74, 0.5)' }}>Nectar</span>
            <span className="mobile-nav-dot" />
          </Link>
          <Link to="/collection" className={`mobile-nav-item flex flex-col items-center justify-center flex-1 h-full gap-0.5 ${isActive('/collection') ? 'nav-active' : ''}`} data-testid="mobile-collection">
            <Library className="w-5 h-5 transition-all duration-200" style={{ color: isActive('/collection') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
            <span className="text-[10px] font-medium transition-colors duration-200" style={{ color: isActive('/collection') ? '#C8861A' : 'rgba(138, 107, 74, 0.5)' }}>Collection</span>
            <span className="mobile-nav-dot" />
          </Link>
          <Link to="/honeypot" className={`mobile-nav-item flex flex-col items-center justify-center flex-1 h-full gap-0.5 ${isActive('/honeypot') ? 'nav-active' : ''}`} data-testid="mobile-honeypot">
            <ShoppingBag className="w-5 h-5 transition-all duration-200" style={{ color: isActive('/honeypot') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
            <span className="text-[10px] font-medium transition-colors duration-200" style={{ color: isActive('/honeypot') ? '#C8861A' : 'rgba(138, 107, 74, 0.5)' }}>Honeypot</span>
            <span className="mobile-nav-dot" />
          </Link>
          <Link to="/essentials" className={`mobile-nav-item flex flex-col items-center justify-center flex-1 h-full gap-0.5 ${isActive('/essentials') ? 'nav-active' : ''}`} data-testid="mobile-essentials">
            <Sparkles className="w-5 h-5 transition-all duration-200" style={{ color: isActive('/essentials') ? '#C8861A' : 'rgba(138, 107, 74, 0.65)' }} />
            <span className="text-[10px] font-medium transition-colors duration-200" style={{ color: isActive('/essentials') ? '#C8861A' : 'rgba(138, 107, 74, 0.5)' }}>Essentials</span>
            <span className="mobile-nav-dot" />
          </Link>
        </div>
      </div>
    )}

    {/* Report a Problem Modal */}
    <ReportModal
      open={reportOpen}
      onOpenChange={setReportOpen}
      targetType="bug"
      targetId={null}
    />
    </>
  );
};


// Mobile Profile Menu — Portal-based, bypasses all stacking contexts
const MobileProfileMenu = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const triggerRef = useRef(null);
  const [pos, setPos] = useState({ top: 0, right: 0 });

  const toggle = useCallback(() => {
    if (!open && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPos({ top: rect.bottom + 6, right: window.innerWidth - rect.right });
    }
    setOpen(prev => !prev);
  }, [open]);

  // Close on route change
  const location = useLocation();
  useEffect(() => { setOpen(false); }, [location.pathname]);

  const go = (path) => { setOpen(false); navigate(path); };

  const menuItems = [
    { icon: User, label: 'Profile', action: () => go(`/profile/${user.username}`), testId: 'mobile-menu-profile' },
    { icon: Settings, label: 'Settings', action: () => go('/settings'), testId: 'mobile-menu-settings' },
    { icon: Package, label: 'Orders', action: () => go('/orders'), testId: 'mobile-menu-orders' },
    { icon: Sparkles, label: 'Honey Essentials', action: () => go('/essentials'), testId: 'mobile-menu-essentials' },
    { icon: ArrowRightLeft, label: 'Trades', action: () => go('/trades'), testId: 'mobile-menu-trades' },
  ];

  if (user.is_admin) {
    menuItems.push({ separator: true });
    menuItems.push({ icon: Settings, label: 'Admin Panel', action: () => go('/admin'), testId: 'mobile-menu-admin' });
  }

  return (
    <>
      <button
        ref={triggerRef}
        onClick={toggle}
        className="relative h-11 w-11 flex items-center justify-center rounded-full -mr-1"
        data-testid="mobile-user-menu"
        style={{ zIndex: 10, WebkitTapHighlightColor: 'transparent' }}
      >
        <BeeAvatar user={user} className="h-8 w-8" />
      </button>
      {open && ReactDOM.createPortal(
        <>
          {/* Backdrop */}
          <div
            onClick={() => setOpen(false)}
            data-testid="mobile-menu-backdrop"
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 2147483646,
              background: 'transparent',
            }}
          />
          {/* Menu */}
          <div
            data-testid="mobile-menu-portal"
            style={{
              position: 'fixed',
              top: pos.top,
              right: pos.right,
              zIndex: 2147483647,
              width: 224,
              borderRadius: 8,
              border: '1px solid rgba(200,134,26,0.2)',
              background: 'rgba(255,255,255,0.97)',
              backdropFilter: 'blur(12px)',
              boxShadow: '0 10px 25px -5px rgba(0,0,0,0.15), 0 8px 10px -6px rgba(0,0,0,0.1)',
              overflow: 'hidden',
              animation: 'mobileMenuIn 150ms ease-out',
            }}
          >
            {/* User header */}
            <div className="flex items-center gap-2 p-3 border-b border-honey/10">
              <BeeAvatar user={user} className="h-8 w-8" />
              <div className="flex flex-col min-w-0">
                <p className="text-sm font-medium truncate flex items-center gap-1">
                  @{user.username}
                  {(user.golden_hive_verified || user.is_admin || user.id === KATIE_ID) && (
                    <VerifiedShield size={14} isFounder={user.is_admin || user.id === KATIE_ID} />
                  )}
                </p>
                <p className="text-xs text-muted-foreground truncate">{user.email}</p>
              </div>
            </div>
            {/* Menu items */}
            <div className="py-1">
              {menuItems.map((item, i) => {
                if (item.separator) return <div key={`sep-${i}`} className="h-px bg-honey/10 my-1" />;
                const Icon = item.icon;
                return (
                  <button
                    key={item.testId}
                    onClick={item.action}
                    data-testid={item.testId}
                    className="flex items-center gap-2 w-full px-3 py-2.5 text-sm text-left hover:bg-honey/5 active:bg-honey/10 transition-colors"
                  >
                    <Icon className="h-4 w-4 shrink-0 text-muted-foreground" /> {item.label}
                  </button>
                );
              })}
            </div>
            {/* Logout */}
            <div className="border-t border-honey/10 py-1">
              <button
                onClick={() => { setOpen(false); onLogout(); }}
                data-testid="mobile-menu-logout"
                className="flex items-center gap-2 w-full px-3 py-2.5 text-sm text-red-600 hover:bg-red-50 active:bg-red-100 transition-colors"
              >
                <LogOut className="h-4 w-4 shrink-0" /> Log out
              </button>
            </div>
          </div>
        </>,
        document.body
      )}
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
        <span className="absolute -top-0.5 -right-0.5 bg-honey text-vinyl-black text-[10px] font-bold min-w-[18px] h-[18px] rounded-full flex items-center justify-center badge-pulse" data-testid="dm-unread-badge">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </Button>
  );
};

// Notification Bell Component
const NotificationBell = () => {
  const { token, API, user } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
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
      const resp = await axios.get(`${API}/notifications?limit=15&skip=0`, { headers: { Authorization: `Bearer ${token}` } });
      setNotifications(resp.data);
      setHasMore(resp.data.length >= 15);
    } catch { /* ignore */ }
  }, [API, token]);

  // BLOCK 575/578: Load next page of notifications
  const fetchMore = async () => {
    setLoadingMore(true);
    try {
      const resp = await axios.get(`${API}/notifications?limit=15&skip=${notifications.length}`, { headers: { Authorization: `Bearer ${token}` } });
      if (resp.data.length === 0) {
        setHasMore(false);
      } else {
        setNotifications(prev => [...prev, ...resp.data]);
        setHasMore(resp.data.length >= 15);
      }
    } catch { /* ignore */ }
    setLoadingMore(false);
  };

  useEffect(() => {
    fetchCount();
    const interval = setInterval(fetchCount, 15000);
    return () => clearInterval(interval);
  }, []);

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
    const t = notif.type;
    // DMs → messages page
    if (d.conversation_id) navigate('/messages');
    // Trades → trades page
    else if (d.trade_id) navigate('/trades');
    // Follower → their profile
    else if (d.follower_username) navigate(`/profile/${d.follower_username}`);
    // Orders (shipped/cancelled) → orders page
    else if (d.order_id) navigate('/orders');
    // Post interactions → specific post with optional comment
    else if (d.post_id) {
      const params = new URLSearchParams({ post: d.post_id });
      if (d.comment_id) params.set('comment', d.comment_id);
      navigate(`/hive?${params.toString()}`);
    }
    // Listings (sale, purchase, wantlist match) → honeypot listing detail
    else if (d.listing_id) navigate(`/honeypot/listing/${d.listing_id}`);
    // Wax report → wax reports page
    else if (t === 'WAX_REPORT') navigate('/wax-reports');
    // Bingo → nectar (explore) where bingo lives
    else if (t === 'BINGO') navigate('/nectar');
    // Mood board → profile mood board tab
    else if (t === 'MOOD_BOARD') navigate(`/profile/${user?.username}`);
    // Streak nudge → hive (daily prompt is at top)
    else if (t === 'streak_nudge' || t === 'streak_nudge_urgent') navigate('/hive');
    // Price alert → honeypot
    else if (t === 'PRICE_ALERT') navigate('/honeypot');
    // Stripe connected → settings
    else if (t === 'STRIPE_CONNECTED') navigate('/settings');
  };

  const NOTIF_ICONS = {
    NEW_FOLLOWER: '👤', POST_LIKED: '❤️', NEW_COMMENT: '💬',
    TRADE_PROPOSED: '🤝', TRADE_ACCEPTED: '✅', TRADE_SHIPPED: '📦',
    TRADE_CONFIRMED: '🎉', SALE_COMPLETED: '💰', PURCHASE_COMPLETED: '🛒',
    STRIPE_CONNECTED: '💳', ISO_MATCH: '🔍', WANTLIST_MATCH: '🔍',
    ORDER_SHIPPED: '📦', ORDER_CANCELLED: '❌', PRICE_ALERT: '💲',
    WAX_REPORT: '📊', BINGO: '🎯', MOOD_BOARD: '🎨',
    streak_nudge: '🐝', streak_nudge_urgent: '🐝', dm: '💬',
    HOLD_DISPUTE: '⚠️', COMMENT_LIKED: '❤️', COMMENT_REPLY: '💬',
    MENTION: '🔔',
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-9 w-9 rounded-full" data-testid="notification-bell">
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-[#C8861A] text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 badge-pulse" data-testid="notification-badge">
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
        {/* BLOCK 575/578: View More button — glassy honey style */}
        {notifications.length > 0 && (
          <div className="p-2 border-t" style={{ borderColor: 'rgba(218,165,32,0.15)' }}>
            {hasMore ? (
              <button
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); fetchMore(); }}
                disabled={loadingMore}
                className="w-full py-2 rounded-lg text-xs font-semibold transition-all hover:scale-[1.01]"
                style={{
                  background: 'rgba(255,255,255,0.4)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid rgba(218,165,32,0.3)',
                  color: '#7A5A1A',
                }}
                data-testid="notif-view-more"
              >
                {loadingMore ? (
                  <Loader2 className="w-4 h-4 animate-spin mx-auto text-[#C8861A]" />
                ) : (
                  'View More'
                )}
              </button>
            ) : (
              <p className="text-center text-[11px] text-muted-foreground py-1" data-testid="notif-caught-up">
                You're all caught up!
              </p>
            )}
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default Navbar;
