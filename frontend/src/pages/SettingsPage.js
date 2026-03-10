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
import { ArrowLeft, Save, LogOut, Camera, Loader2, Mail, HelpCircle, ExternalLink, MessageSquare, Flag, Trash2, CreditCard, CheckCircle2, Shield, Bug, Lock, Globe, Users, MessageCircleMore } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '../components/ui/dialog';
import ReportModal from '../components/ReportModal';
import CropModal from '../components/CropModal';

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
  const [city, setCity] = useState(user?.city || '');
  const [stateUS, setStateUS] = useState(user?.state || '');
  const [postalCode, setPostalCode] = useState(user?.postal_code || '');
  const [instagramUsername, setInstagramUsername] = useState(user?.instagram_username || '');
  const [tiktokUsername, setTiktokUsername] = useState(user?.tiktok_username || '');
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [cropSrc, setCropSrc] = useState(null);
  const [showCrop, setShowCrop] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState(user?.avatar_url);
  const [nlSubscribed, setNlSubscribed] = useState(false);
  const [nlLoading, setNlLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [stripeStatus, setStripeStatus] = useState(null); // { stripe_connected, stripe_account_id }
  const [stripeLoading, setStripeLoading] = useState(true);
  const [stripeConnecting, setStripeConnecting] = useState(false);
  const [editingEmail, setEditingEmail] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [emailSaving, setEmailSaving] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [verifyUploading, setVerifyUploading] = useState(false);
  const verifyInputRef = useRef(null);
  const [bugReportOpen, setBugReportOpen] = useState(false);
  const [isPrivate, setIsPrivate] = useState(user?.is_private || false);
  const [dmSetting, setDmSetting] = useState(user?.dm_setting || 'everyone');

  useEffect(() => {
    axios.get(`${API}/newsletter/status`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setNlSubscribed(r.data.subscribed))
      .catch(() => {});
    axios.get(`${API}/stripe/status`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setStripeStatus(r.data))
      .catch(() => setStripeStatus({ stripe_connected: false, stripe_account_id: null }))
      .finally(() => setStripeLoading(false));
    axios.get(`${API}/verification/status`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setVerificationStatus(r.data))
      .catch(() => {});
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
    if (!username.trim()) {
      toast.error('username is required.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        username: username !== user.username ? username : undefined,
        bio: bio || '',
        setup: setup || '',
        location: country === 'US' ? [city, stateUS].filter(Boolean).join(', ') : (city || location || ''),
        country: country || undefined,
        city: city || undefined,
        state: country === 'US' ? (stateUS || undefined) : undefined,
        postal_code: postalCode || undefined,
        favorite_genre: favoriteGenre || undefined,
        avatar_url: avatarPreview !== user.avatar_url ? avatarPreview : undefined,
        instagram_username: instagramUsername.replace(/^@/, '').trim() || '',
        tiktok_username: tiktokUsername.replace(/^@/, '').trim() || '',
        is_private: isPrivate,
        dm_setting: dmSetting,
      };
      const response = await axios.put(`${API}/auth/me`, payload,
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
    const { validateImageFile } = await import('../utils/imageUpload');
    const err = validateImageFile(file);
    if (err) { toast.error(err); return; }
    // Open crop modal with the selected image
    const reader = new FileReader();
    reader.onload = () => { setCropSrc(reader.result); setShowCrop(true); };
    reader.readAsDataURL(file);
    // Reset input so the same file can be re-selected
    e.target.value = '';
  };

  const handleCropComplete = async (croppedFile) => {
    setShowCrop(false);
    setCropSrc(null);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', croppedFile);
      const response = await axios.post(`${API}/upload`, formData, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' }
      });
      const publicUrl = `${API}/files/serve/${response.data.path}`;
      setAvatarPreview(publicUrl);
      toast.success('photo cropped & uploaded. click save to apply.');
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

  const handleVerificationUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setVerifyUploading(true);
    try {
      const formData = new FormData();
      formData.append('id_photo', file);
      await axios.post(`${API}/verification/submit`, formData, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
      });
      toast.success('Verification submitted! You\'ll be notified once reviewed.');
      setVerificationStatus({ status: 'PENDING', golden_hive: false });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally { setVerifyUploading(false); }
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

  const handleEmailChange = async () => {
    if (!newEmail.trim() || !newEmail.includes('@')) {
      toast.error('please enter a valid email address.');
      return;
    }
    setEmailSaving(true);
    try {
      const resp = await axios.post(`${API}/auth/change-email`, 
        { new_email: newEmail.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(resp.data.message || 'confirmation email sent to your new address.');
      setEditingEmail(false);
      setNewEmail('');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'could not request email change.');
    } finally {
      setEmailSaving(false);
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
            
            <div className="min-w-0">
              <p className="font-medium">@{user?.username}</p>
              <p className="text-sm text-muted-foreground break-all">{user?.email}</p>
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

          {/* Email */}
          <div className="space-y-2">
            <Label>Email</Label>
            {!editingEmail ? (
              <div className="flex items-center gap-2">
                <p className="text-sm break-all flex-1" data-testid="settings-email-display">{user?.email}</p>
                <button
                  onClick={() => { setEditingEmail(true); setNewEmail(user?.email || ''); }}
                  className="text-sm text-honey-amber hover:underline whitespace-nowrap"
                  data-testid="settings-email-edit-btn"
                >
                  change
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <Input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="new email address"
                  className="border-honey/50"
                  data-testid="settings-email-input"
                />
                <p className="text-xs text-muted-foreground">a confirmation link will be sent to your new email. your current email stays active until you confirm.</p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleEmailChange}
                    disabled={emailSaving || !newEmail.trim()}
                    className="bg-honey text-vinyl-black hover:bg-honey/90"
                    data-testid="settings-email-save-btn"
                  >
                    {emailSaving ? 'sending...' : 'send confirmation'}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => { setEditingEmail(false); setNewEmail(''); }}
                    data-testid="settings-email-cancel-btn"
                  >
                    cancel
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Bio */}
          <div className="space-y-2">
            <Label htmlFor="bio">Bio</Label>
            <Textarea
              id="bio"
              placeholder="tell the hive who you are."
              value={bio}
              onChange={(e) => setBio(e.target.value.slice(0, 160))}
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
              onChange={(e) => setSetup(e.target.value.slice(0, 100))}
              className="border-honey/50"
              data-testid="settings-setup"
            />
            <p className="text-xs text-muted-foreground text-right">{setup.length}/100</p>
          </div>

          {/* Country */}
          <div className="space-y-2">
            <Label htmlFor="country" className="text-sm font-heading tracking-wide">Country</Label>
            <select
              id="country"
              value={country}
              onChange={(e) => { setCountry(e.target.value); if (e.target.value !== 'US') setStateUS(''); }}
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

          {/* City + State (US only) + Postal Code */}
          <div className={`grid gap-4 ${country === 'US' ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2'}`}>
            <div className="space-y-2">
              <Label htmlFor="city" className="text-sm font-heading tracking-wide">City <span className="text-xs font-normal text-muted-foreground/70 italic">(Optional)</span></Label>
              <Input
                id="city"
                placeholder="Your city"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="border-honey/50"
                data-testid="settings-city"
              />
            </div>

            {country === 'US' && (
              <div className="space-y-2">
                <Label htmlFor="stateUS" className="text-sm font-heading tracking-wide">State</Label>
                <select
                  id="stateUS"
                  value={stateUS}
                  onChange={(e) => setStateUS(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-honey/50 bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  data-testid="settings-state"
                >
                  <option value="">Select state</option>
                  {['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'].map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="postalCode" className="text-sm font-heading tracking-wide">{country === 'US' ? 'ZIP Code' : 'Postal Code'} <span className="text-xs font-normal text-muted-foreground/70 italic">(Optional)</span></Label>
              <Input
                id="postalCode"
                placeholder={country === 'US' ? 'ZIP code' : 'Postal code'}
                value={postalCode}
                onChange={(e) => setPostalCode(e.target.value)}
                className="border-honey/50"
                data-testid="settings-postal"
              />
            </div>
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

          {/* Instagram */}
          <div className="space-y-2">
            <Label htmlFor="instagram">Instagram</Label>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">instagram.com/</span>
              <Input
                id="instagram"
                placeholder="username"
                value={instagramUsername}
                onChange={(e) => setInstagramUsername(e.target.value.replace(/^@/, ''))}
                className="border-honey/50 flex-1"
                data-testid="settings-instagram"
              />
            </div>
          </div>

          {/* TikTok */}
          <div className="space-y-2">
            <Label htmlFor="tiktok">TikTok</Label>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">tiktok.com/@</span>
              <Input
                id="tiktok"
                placeholder="username"
                value={tiktokUsername}
                onChange={(e) => setTiktokUsername(e.target.value.replace(/^@/, ''))}
                className="border-honey/50 flex-1"
                data-testid="settings-tiktok"
              />
            </div>
          </div>

          <Button
            onClick={handleSave}
            disabled={saving || !username.trim()}
            className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
            data-testid="save-settings-btn"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </CardContent>
      </Card>

      {/* Newsletter */}
      {/* Privacy & Messaging */}
      <Card className="border-honey/30 mb-6" data-testid="privacy-settings-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Shield className="w-5 h-5 text-amber-600" /> Privacy & Messaging</CardTitle>
          <CardDescription>control who can follow you and send you messages.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Profile Privacy */}
          <div>
            <Label className="text-sm font-medium mb-3 block">Profile Visibility</Label>
            <div className="flex items-center justify-between p-3 rounded-lg bg-stone-50/80 border border-stone-200/50">
              <div className="flex items-center gap-3">
                {isPrivate ? <Lock className="w-4 h-4 text-amber-600" /> : <Globe className="w-4 h-4 text-green-600" />}
                <div>
                  <p className="text-sm font-medium">{isPrivate ? 'Private' : 'Public'}</p>
                  <p className="text-xs text-muted-foreground">
                    {isPrivate ? 'Only approved followers can see your content' : 'Anyone can see your profile and follow you'}
                  </p>
                </div>
              </div>
              <Switch
                checked={isPrivate}
                onCheckedChange={setIsPrivate}
                data-testid="private-account-toggle"
              />
            </div>
          </div>

          {/* DM Settings */}
          <div>
            <Label className="text-sm font-medium mb-3 block">Who can message you?</Label>
            <div className="space-y-2">
              {[
                { value: 'everyone', label: 'Everyone', desc: 'Anyone can send you a direct message', icon: Globe },
                { value: 'following', label: 'People I Follow', desc: 'Only users you follow can message you', icon: Users },
                { value: 'requests', label: 'Allow Message Requests', desc: 'Anyone can send a request — you accept or decline', icon: MessageCircleMore },
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setDmSetting(opt.value)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all text-left ${
                    dmSetting === opt.value
                      ? 'border-amber-400 bg-amber-50/50'
                      : 'border-stone-200/50 bg-stone-50/40 hover:bg-stone-50/80'
                  }`}
                  data-testid={`dm-setting-${opt.value}`}
                >
                  <opt.icon className={`w-4 h-4 shrink-0 ${dmSetting === opt.value ? 'text-amber-600' : 'text-stone-400'}`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${dmSetting === opt.value ? 'text-amber-800' : 'text-stone-700'}`}>{opt.label}</p>
                    <p className="text-xs text-muted-foreground">{opt.desc}</p>
                  </div>
                  {dmSetting === opt.value && <CheckCircle2 className="w-4 h-4 text-amber-600 shrink-0" />}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Newsletter - original */}
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
              <Button
                onClick={async () => {
                  if (!window.confirm('Disconnect Stripe? You will not be able to sell until you reconnect.')) return;
                  try {
                    await axios.post(`${API}/stripe/disconnect`, {}, { headers: { Authorization: `Bearer ${token}` } });
                    setStripeStatus({ stripe_connected: false, stripe_account_id: null });
                    toast.success('Stripe disconnected.');
                  } catch (err) {
                    toast.error(err.response?.data?.detail || 'Could not disconnect.');
                  }
                }}
                variant="outline"
                className="rounded-full border-red-200 text-red-600 hover:bg-red-50 text-xs gap-1.5"
                data-testid="stripe-disconnect-btn"
              >
                <CreditCard className="w-3.5 h-3.5" />
                Disconnect
              </Button>
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

          {/* Golden Hive Verification */}
          <div className="border-t border-honey/20 pt-4">
            <Label className="text-sm font-medium text-amber-800 mb-2 block">Golden Hive Verification</Label>
            {verificationStatus?.golden_hive ? (
              <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2" data-testid="golden-hive-verified">
                <CheckCircle2 className="w-4 h-4" />
                <span className="font-medium">Verified Golden Hive Member</span>
              </div>
            ) : verificationStatus?.status === 'PENDING' ? (
              <div className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2" data-testid="verification-pending">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Verification under review</span>
              </div>
            ) : verificationStatus?.status === 'DENIED' ? (
              <div className="space-y-2">
                <p className="text-sm text-red-600">Your previous verification was not approved. Please resubmit with a clearer photo.</p>
                <Button onClick={() => verifyInputRef.current?.click()} disabled={verifyUploading}
                  variant="outline" className="rounded-full text-xs border-honey/50" data-testid="resubmit-verification-btn">
                  {verifyUploading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Shield className="w-3 h-3 mr-1" />}
                  Resubmit ID Photo
                </Button>
                <input ref={verifyInputRef} type="file" accept="image/*" onChange={handleVerificationUpload} className="hidden" />
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">Upload a government-issued ID to become a verified Golden Hive member. Your ID will be securely processed and reviewed by an admin.</p>
                <Button onClick={() => verifyInputRef.current?.click()} disabled={verifyUploading}
                  variant="outline" className="rounded-full text-xs border-honey/50" data-testid="submit-verification-btn">
                  {verifyUploading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Shield className="w-3 h-3 mr-1" />}
                  Upload ID Photo
                </Button>
                <input ref={verifyInputRef} type="file" accept="image/*" onChange={handleVerificationUpload} className="hidden" />
              </div>
            )}
          </div>

          <div className="border-t border-honey/20 pt-4">
            <button
              type="button"
              onClick={() => setBugReportOpen(true)}
              className="flex items-center gap-2 text-sm text-[#8A6B4A] hover:text-amber-600 transition-colors"
              data-testid="report-bug-btn"
            >
              <Bug className="w-4 h-4" />
              Report a Bug
            </button>
          </div>

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
              Deleting your account is permanent and cannot be undone. Your collection, posts, Dream List, and trade history will be removed immediately. This action cannot be reversed and your account cannot be reactivated.
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

      <ReportModal open={bugReportOpen} onOpenChange={setBugReportOpen} targetType="bug" targetId={null} />

      <CropModal
        open={showCrop}
        onClose={() => { setShowCrop(false); setCropSrc(null); }}
        imageSrc={cropSrc}
        onCropComplete={handleCropComplete}
      />
    </div>
  );
};

export default SettingsPage;
