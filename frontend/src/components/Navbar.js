import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Home, Search, PlusCircle, User, LogOut, Settings, Library } from 'lucide-react';

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

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-honey/30">
      <div className="max-w-6xl mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group" data-testid="nav-logo">
            <img 
              src="https://customer-assets.emergentagent.com/job_vinyl-social-2/artifacts/n8vjxmsv_honey-groove-transparent.png" 
              alt="the Honey Groove" 
              className="h-12 group-hover:scale-105 transition-transform"
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
                  <Search className="w-4 h-4" />
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
              <Link to="/add-record" data-testid="nav-add-record">
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/add-record') ? 'bg-honey/20' : ''}`}
                >
                  <PlusCircle className="w-4 h-4" />
                  Add
                </Button>
              </Link>
            </div>
          )}

          {/* Right Side */}
          <div className="flex items-center gap-3">
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
                  <DropdownMenuItem onClick={() => navigate('/collection')} data-testid="menu-collection">
                    <Library className="mr-2 h-4 w-4" />
                    My Collection
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/settings')} data-testid="menu-settings">
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </DropdownMenuItem>
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
                <Link to="/signup">
                  <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full" data-testid="nav-signup">
                    Sign up
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {user && (
        <div className="md:hidden fixed bottom-0 left-0 right-0 glass border-t border-honey/30 px-4 py-2">
          <div className="flex justify-around items-center">
            <Link to="/hive" className={`p-2 rounded-lg ${isActive('/hive') ? 'bg-honey/20' : ''}`} data-testid="mobile-hive">
              <Home className="w-6 h-6" />
            </Link>
            <Link to="/explore" className={`p-2 rounded-lg ${isActive('/explore') ? 'bg-honey/20' : ''}`} data-testid="mobile-explore">
              <Search className="w-6 h-6" />
            </Link>
            <Link to="/add-record" className={`p-2 rounded-lg ${isActive('/add-record') ? 'bg-honey/20' : ''}`} data-testid="mobile-add">
              <PlusCircle className="w-6 h-6" />
            </Link>
            <Link to="/collection" className={`p-2 rounded-lg ${isActive('/collection') ? 'bg-honey/20' : ''}`} data-testid="mobile-collection">
              <Library className="w-6 h-6" />
            </Link>
            <Link to={`/profile/${user.username}`} className={`p-2 rounded-lg ${isActive(`/profile/${user.username}`) ? 'bg-honey/20' : ''}`} data-testid="mobile-profile">
              <User className="w-6 h-6" />
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
