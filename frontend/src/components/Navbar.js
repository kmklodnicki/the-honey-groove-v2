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
import { Disc, Home, Search, PlusCircle, User, LogOut, Settings, Library } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  // Bee SVG Icon
  const BeeIcon = () => (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor">
      <ellipse cx="12" cy="12" rx="6" ry="5" fill="#1F1F1F"/>
      <ellipse cx="12" cy="12" rx="4" ry="3" fill="#F4B942"/>
      <line x1="8" y1="12" x2="16" y2="12" stroke="#1F1F1F" strokeWidth="1"/>
      <ellipse cx="8" cy="9" rx="2" ry="3" fill="#1F1F1F" opacity="0.3"/>
      <ellipse cx="16" cy="9" rx="2" ry="3" fill="#1F1F1F" opacity="0.3"/>
    </svg>
  );

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-honey/30">
      <div className="max-w-6xl mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group" data-testid="nav-logo">
            <img 
              src="https://customer-assets.emergentagent.com/job_vinyl-social-2/artifacts/x2y55r8k_honey-groove-bee2.png" 
              alt="the Honey Groove" 
              className="h-10 group-hover:scale-105 transition-transform"
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
                    <Avatar className="h-10 w-10 border-2 border-honey">
                      <AvatarImage src={user.avatar_url} alt={user.username} />
                      <AvatarFallback className="bg-honey text-vinyl-black">
                        {user.username?.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <div className="flex items-center gap-2 p-2">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={user.avatar_url} />
                      <AvatarFallback>{user.username?.charAt(0).toUpperCase()}</AvatarFallback>
                    </Avatar>
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
