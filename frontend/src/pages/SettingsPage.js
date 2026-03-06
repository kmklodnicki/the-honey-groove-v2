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
import { ArrowLeft, Save, LogOut, Camera, Loader2, Mail, HelpCircle, ExternalLink, MessageSquare, Flag } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';

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
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState(user?.avatar_url);
  const [nlSubscribed, setNlSubscribed] = useState(false);
  const [nlLoading, setNlLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API}/newsletter/status`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setNlSubscribed(r.data.subscribed))
      .catch(() => {});
  }, [API, token]);

  const toggleNewsletter = async () => {
    setNlLoading(true);
    try {
      if (nlSubscribed) {
        await axios.post(`${API}/newsletter/unsubscribe`, { email: user.email }, { headers: { Authorization: `Bearer ${token}` } });
        setNlSubscribed(false);
        toast.success('Unsubscribed');
      } else {
        await axios.post(`${API}/newsletter/subscribe`, { email: user.email, source: 'in_app' }, { headers: { Authorization: `Bearer ${token}` } });
        setNlSubscribed(true);
        toast.success('Subscribed!');
      }
    } catch { toast.error('Failed to update'); }
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
          favorite_genre: favoriteGenre || undefined,
          avatar_url: avatarPreview !== user.avatar_url ? avatarPreview : undefined
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      updateUser(response.data);
      toast.success('Profile updated!');
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
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB');
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

      // Get the public URL from the response
      const uploadedPath = response.data.path;
      const publicUrl = `https://integrations.emergentagent.com/objstore/api/v1/storage/public/${uploadedPath}`;
      
      setAvatarPreview(publicUrl);
      toast.success('Photo uploaded! Click Save to apply changes.');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload photo. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
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
                accept="image/*"
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
              {['Jazz', 'Soul', 'Funk', 'R&B', 'Hip Hop', 'Rock', 'Indie', 'Electronic', 'House', 'Techno', 'Ambient', 'Classical', 'Folk', 'Country', 'Reggae', 'Punk', 'Metal', 'Blues', 'Latin', 'World'].map(g => (
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
        <CardContent>
          <Button
            variant="outline"
            onClick={handleLogout}
            className="text-red-600 border-red-300 hover:bg-red-50 gap-2"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
            Log Out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;
