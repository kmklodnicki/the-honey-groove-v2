import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Switch } from '../components/ui/switch';
import { ArrowLeft, Save, LogOut, Camera, Loader2, Mail, HelpCircle, ExternalLink, MessageSquare, Flag, Trash2, CreditCard, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '../components/ui/dialog';

const SettingsPage = () => {
  usePageTitle('Settings');
  const { user, token, API, updateUser, logout } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [username, setUsername] = useState(user?.username || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [setup, setSetup] = useState(user?.setup || '');
  const [location, setLocation] = useState(user?.location || '');
  const [favoriteGenre, setFavoriteGenre] = useState(user?.favorite_genre || '');
  const [country, setCountry] = useState(user?.country || '');
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState(user?.avatar_url);
  const [nlSubscribed, setNlSubscribed] = useState(false);
  const [nlLoading, setNlLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [stripeStatus, setStripeStatus] = useState(null); // { stripe_connected, stripe_account_id }
  const [stripeLoading, setStripeLoading] = useState(true);
  const [stripeConnecting, setStripeConnecting] = useState(false);

  useEffect(() => {
    axios.get(`${API}/newsletter/status`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setNlSubscribed(r.data.subscribed))
      .catch(() => {});
    axios.get(`${API}/stripe/status`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setStripeStatus(r.data))
      .catch(() => setStripeStatus({ stripe_connected: false, stripe_account_id: null }))
      .finally(() => setStripeLoading(false));
  }, [API, token]);

  const toggleNewsletter = async () => {
    setNlLoading(true);
    try {
      if (nlSubscribed) {
        await axios.post(`${API}/newsletter/unsubscribe`, { email: user.email }, { headers: { Authorization: `Bearer ${token}` } });
        setNlSubscribed(false);
        toast.success('unsubscribed.');
      } else {
        await axios.post(`${API}/newsletter/subscribe`, { email: user.email, source: 'in_app' }, { headers: { Authorization: `Bearer ${token}` } });
        setNlSubscribed(true);
        toast.success('subscribed.');
      }
    } catch { toast.error('could not update. try again.'); }
    finally { setNlLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await axios.put(`${API}/auth/me`, 
        { 
          username: username !== user.username ? username : undefined,
          bio: bio,
          setup: setup,
          location: location,
          country: country || undefined,
          favorite_genre: favoriteGenre || undefined,
          avatar_url: avatarPreview !== user.avatar_url ? avatarPreview : undefined
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      updateUser(response.data);
      toast.success('profile updated.');
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to update profile';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const handlePhotoClick = () => {
    fileInputRef.current?.click();
  };

  const handlePhotoChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const { validateImageFile } = await import('../utils/imageUpload');
    const err = validateImageFile(file);
    if (err) {
      toast.error(err);
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/upload`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      // Build the URL using the current API base so it works in any environment
      const publicUrl = `${API}/files/serve/${response.data.path}`;
      
      setAvatarPreview(publicUrl);
      toast.success('photo uploaded. click save to apply.');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('could not upload photo. try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleStripeConnect = async () => {
    setStripeConnecting(true);
    try {
      const resp = await axios.post(`${API}/stripe/connect`, {}, { headers: { Authorization: `Bearer ${token}` } });
      if (resp.data.url) {
        window.location.href = resp.data.url;
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'could not start Stripe setup. try again.';
      toast.error(msg);
    } finally {
      setStripeConnecting(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await axios.delete(`${API}/auth/account`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('your account has been deleted.');
      logout();
      navigate('/');
    } catch {
      toast.error('could not delete account. try again.');
    } finally {
      setDeleting(false);
      setShowDeleteModal(false);
    }
  };

  const firstLetter = user?.username?.charAt(0).toUpperCase() || '?';
  const hasCustomAvatar = avatarPreview && !avatarPreview.includes('dicebear');

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 pt-16 md:pt-24 pb-24 md:pb-8">
      <Button 
        variant="ghost" 
        onClick={() => navigate(-1)}
        className="mb-6 gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>

      <h1 className="font-heading text-3xl text-vinyl-black mb-6">Settings</h1>

      <Card className="border-honey/30 mb-6">
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Update your profile information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Avatar with Upload */}
          <div className="flex items-center gap-6">
            <div className="relative group">
              <Avatar className="w-24 h-24 border-4 border-honey">
                {hasCustomAvatar && <AvatarImage src={avatarPreview} alt={user?.username} />}
                <AvatarFallback className="text-3xl bg-honey-soft text-vinyl-black relative">
                  <span className="font-heading">{firstLetter}</span>
                  <svg 
                    viewBox="0 0 24 24" 
                    className="absolute bottom-0 right-0 w-6 h-6"
                    fill="none"
                  >
                    <ellipse cx="12" cy="14" rx="5" ry="4" fill="#1F1F1F"/>
                    <ellipse cx="12" cy="13" rx="3.5" ry="2" fill="#F4B942"/>
                    <ellipse cx="12" cy="15" rx="3" ry="1.5" fill="#F4B942"/>
                    <circle cx="12" cy="9" r="2.5" fill="#1F1F1F"/>
                    <ellipse cx="8" cy="11" rx="2" ry="3" fill="#1F1F1F" opacity="0.3"/>
                    <ellipse cx="16" cy="11" rx="2" ry="3" fill="#1F1F1F" opacity="0.3"/>
                  </svg>
                </AvatarFallback>
              </Avatar>
              
              {/* Upload overlay */}
              <button
                onClick={handlePhotoClick}
                disabled={uploading}
                className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                data-testid="upload-avatar-btn"
              >
                {uploading ? (
                  <Loader2 className="w-6 h-6 text-white animate-spin" />
                ) : (
                  <Camera className="w-6 h-6 text-white" />
                )}
              </button>
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".jpg,.jpeg,.png,.webp,.heic,.heif"
                onChange={handlePhotoChange}
                className="hidden"
                data-testid="avatar-file-input"
              />
            </div>
            
            <div>
              <p className="font-medium">@{user?.username}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
              <button 
                onClick={handlePhotoClick}
                className="text-sm text-honey-amber hover:underline mt-1"
              >
                {uploading ? 'Uploading...' : 'Change photo'}
              </button>
            </div>
          </div>

          {/* Username */}
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
              className="border-honey/50"
              data-testid="settings-username"
            />
          </div>

          {/* Bio */}
          <div className="space-y-2">
            <Label htmlFor="bio">Bio</Label>
            <Textarea
              id="bio"
              placeholder="tell the hive who you are."
              value={bio}
              onChange={(e) => { if (e.target.value.length <= 160) setBio(e.target.value); }}
              className="border-honey/50"
              rows={3}
              data-testid="settings-bio"
            />
            <p className="text-xs text-muted-foreground text-right">{bio.length}/160</p>
          </div>

          {/* Setup */}
          <div className="space-y-2">
            <Label htmlFor="setup">Setup</Label>
            <Input
              id="setup"
              placeholder="your turntable, needle, speakers..."
              value={setup}
              onChange={(e) => { if (e.target.value.length <= 100) setSetup(e.target.value); }}
              className="border-honey/50"
              data-testid="settings-setup"
            />
            <p className="text-xs text-muted-foreground text-right">{setup.length}/100</p>
          </div>

          {/* Location */}
          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              placeholder="city, country"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="border-honey/50"
              data-testid="settings-location"
            />
          </div>

          {/* Country */}
          <div className="space-y-2">
            <Label htmlFor="country">Country</Label>
            <select
              id="country"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="flex h-10 w-full rounded-md border border-honey/50 bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              data-testid="settings-country"
            >
              <option value="">Select country</option>
              {['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'NL', 'SE', 'IT', 'ES', 'BR', 'MX', 'NZ', 'IE', 'NO', 'DK', 'FI', 'BE', 'AT', 'CH', 'PT', 'PL', 'CZ', 'KR', 'TW', 'SG', 'ZA', 'AR', 'CL', 'CO', 'PH', 'IN', 'IL', 'GR', 'HU', 'RO', 'HR', 'SK', 'BG', 'RS', 'UA', 'TH', 'MY', 'ID', 'VN', 'HK', 'AE', 'SA'].map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground">Used for shipping eligibility on marketplace listings.</p>
          </div>

          {/* Favorite Genre */}
          <div className="space-y-2">
            <Label htmlFor="genre">Favorite Genre</Label>
            <select
              id="genre"
              value={favoriteGenre}
              onChange={(e) => setFavoriteGenre(e.target.value)}
              className="flex h-10 w-full rounded-md border border-honey/50 bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              data-testid="settings-genre"
            >
              <option value="">Select a genre</option>
              {['Jazz', 'Soul', 'Funk', 'R&B', 'Pop', 'Hip Hop', 'Rock', 'Indie', 'Alternative', 'Electronic', 'House', 'Techno', 'Ambient', 'Classical', 'Folk', 'Country', 'Reggae', 'Punk', 'Metal', 'Blues', 'Latin', 'World'].map(g => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>

          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
            data-testid="save-settings-btn"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </CardContent>
      </Card>

      {/* Newsletter */}
      <Card className="border-honey/30 mb-6" data-testid="newsletter-settings-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Mail className="w-5 h-5 text-amber-500" /> The Weekly Wax</CardTitle>
          <CardDescription>get the honey groove newsletter in your inbox every week.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">{nlSubscribed ? 'Subscribed' : 'Not subscribed'}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <Switch
              checked={nlSubscribed}
              onCheckedChange={toggleNewsletter}
              disabled={nlLoading}
              data-testid="newsletter-toggle"
            />
          </div>
        </CardContent>
      </Card>

      {/* Payments & Payouts */}
      <Card className="border-honey/30 mb-6" data-testid="payments-settings-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><CreditCard className="w-5 h-5 text-[#635bff]" /> Payments & Payouts</CardTitle>
          <CardDescription>connect Stripe to sell records and receive payouts.</CardDescription>
        </CardHeader>
        <CardContent>
          {stripeLoading ? (
            <div className="flex items-center gap-3 py-2">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
              <span className="text-sm text-muted-foreground">checking connection...</span>
            </div>
          ) : stripeStatus?.stripe_connected ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-green-700">Stripe Connected</p>
                  <p className="text-xs text-muted-foreground">you can list items for sale and receive payouts.</p>
                </div>
              </div>
              <a
                href="https://dashboard.stripe.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-[#635bff] hover:underline flex items-center gap-1"
                data-testid="stripe-dashboard-link"
              >
                Dashboard <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Not connected</p>
                <p className="text-xs text-muted-foreground">connect Stripe to start selling on the Honeypot.</p>
              </div>
              <Button
                onClick={handleStripeConnect}
                disabled={stripeConnecting}
                className="bg-[#635bff] text-white hover:bg-[#5146e0] rounded-full gap-2"
                data-testid="stripe-connect-btn"
              >
                {stripeConnecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
                Connect Stripe
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Help & Support */}
      <Card className="border-honey/30 mb-6" data-testid="help-support-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><HelpCircle className="w-5 h-5 text-honey-amber" /> Help & Support</CardTitle>
          <CardDescription>Get help with your account or the platform</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <a
            href="https://thehoneygroove.com/faq"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-3 rounded-xl border border-honey/20 hover:bg-honey/5 transition-colors group"
            data-testid="help-faq-link"
          >
            <div className="flex items-center gap-3">
              <HelpCircle className="w-4 h-4 text-honey-amber" />
              <span className="text-sm font-medium">FAQ</span>
            </div>
            <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-honey-amber transition-colors" />
          </a>
          <a
            href="mailto:hello@thehoneygroove.com"
            className="flex items-center justify-between p-3 rounded-xl border border-honey/20 hover:bg-honey/5 transition-colors group"
            data-testid="help-contact-link"
          >
            <div className="flex items-center gap-3">
              <MessageSquare className="w-4 h-4 text-honey-amber" />
              <span className="text-sm font-medium">Contact Us</span>
            </div>
            <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-honey-amber transition-colors" />
          </a>
          <button
            onClick={() => navigate('/hive')}
            className="flex items-center justify-between p-3 rounded-xl border border-honey/20 hover:bg-honey/5 transition-colors group w-full text-left"
            data-testid="help-report-link"
          >
            <div className="flex items-center gap-3">
              <Flag className="w-4 h-4 text-honey-amber" />
              <span className="text-sm font-medium">Report a Problem</span>
            </div>
            <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-honey-amber transition-colors" />
          </button>
        </CardContent>
      </Card>

      {/* Account Actions */}
      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">Account</CardTitle>
          <CardDescription>Account actions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            variant="outline"
            onClick={handleLogout}
            className="text-red-600 border-red-300 hover:bg-red-50 gap-2"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
            Log Out
          </Button>

          <div className="border-t border-honey/20 pt-4">
            <button
              onClick={() => setShowDeleteModal(true)}
              className="flex items-center gap-2 text-sm text-[#8A6B4A] hover:text-[#6B5238] transition-colors"
              data-testid="delete-account-btn"
            >
              <Trash2 className="w-4 h-4" />
              Delete Account
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Delete Account Confirmation Modal */}
      <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
        <DialogContent className="sm:max-w-md bg-[#FAF6EE] border-honey/30 rounded-2xl" data-testid="delete-account-modal">
          <DialogHeader>
            <DialogTitle className="font-heading text-2xl text-vinyl-black">Are you sure?</DialogTitle>
            <DialogDescription className="font-serif italic text-base text-vinyl-black/70 leading-relaxed mt-3">
              Deleting your account is permanent and cannot be undone. Your collection, posts, wantlist, and trade history will be removed immediately. This action cannot be reversed and your account cannot be reactivated.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3 mt-4">
            <Button
              variant="outline"
              onClick={handleDeleteAccount}
              disabled={deleting}
              className="w-full border-vinyl-black/30 text-vinyl-black hover:bg-vinyl-black/5 rounded-full"
              data-testid="confirm-delete-btn"
            >
              {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Yes, delete my account
            </Button>
            <Button
              onClick={() => setShowDeleteModal(false)}
              className="w-full bg-[#E8A820] text-vinyl-black hover:bg-[#C8861A] rounded-full font-medium"
              data-testid="cancel-delete-btn"
            >
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SettingsPage;
