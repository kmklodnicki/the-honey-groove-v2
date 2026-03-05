import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { ExternalLink, RefreshCw, CheckCircle2, AlertCircle, Loader2, Unplug, Disc } from 'lucide-react';
import { toast } from 'sonner';

const DiscogsImport = ({ onImportComplete }) => {
  const { token, API } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(null);
  const [showDisconnect, setShowDisconnect] = useState(false);
  const [showConnect, setShowConnect] = useState(false);
  const [discogsUsername, setDiscogsUsername] = useState('');
  const [connecting, setConnecting] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const [statusResp, progressResp] = await Promise.all([
        axios.get(`${API}/discogs/status`, { headers: { Authorization: `Bearer ${token}` }}),
        axios.get(`${API}/discogs/import/progress`, { headers: { Authorization: `Bearer ${token}` }})
      ]);
      setStatus(statusResp.data);
      
      if (statusResp.data.import_status?.status === 'in_progress') {
        setImporting(true);
        setProgress(statusResp.data.import_status);
      } else if (progressResp.data?.status === 'completed' && progressResp.data?.imported > 0) {
        setProgress(progressResp.data);
      }
    } catch (err) {
      console.error('Failed to fetch Discogs status:', err);
    } finally {
      setLoading(false);
    }
  }, [API, token]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Poll for progress when importing
  useEffect(() => {
    if (!importing) return;

    const interval = setInterval(async () => {
      try {
        const resp = await axios.get(`${API}/discogs/import/progress`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setProgress(resp.data);

        if (resp.data.status === 'completed' || resp.data.status === 'error') {
          setImporting(false);
          clearInterval(interval);
          if (resp.data.status === 'completed') {
            toast.success(`Imported ${resp.data.imported} records from Discogs!`);
            onImportComplete?.();
          } else {
            toast.error(resp.data.error_message || 'Import failed');
          }
          fetchStatus();
        }
      } catch (err) {
        console.error('Poll error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [importing, API, token, fetchStatus, onImportComplete]);

  // Check URL params for OAuth callback result
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const discogsParam = params.get('discogs');
    if (discogsParam === 'connected') {
      toast.success(`Discogs account connected! (${params.get('username') || ''})`);
      // Clean up URL
      window.history.replaceState({}, '', window.location.pathname);
      fetchStatus();
    } else if (discogsParam === 'error') {
      toast.error('Failed to connect Discogs: ' + (params.get('message') || 'Unknown error'));
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [fetchStatus]);

  const handleConnect = async () => {
    try {
      const resp = await axios.get(`${API}/discogs/oauth/start`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Redirect to Discogs for authorization
      window.location.href = resp.data.authorization_url;
    } catch (err) {
      // If OAuth isn't configured, show username dialog for token-based connection
      if (err.response?.status === 400) {
        setShowConnect(true);
      } else {
        toast.error(err.response?.data?.detail || 'Failed to start Discogs connection');
      }
    }
  };

  const handleTokenConnect = async (e) => {
    e.preventDefault();
    if (!discogsUsername.trim()) return;
    
    setConnecting(true);
    try {
      await axios.post(`${API}/discogs/connect-token`, 
        { discogs_username: discogsUsername.trim() },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      toast.success(`Connected to Discogs as ${discogsUsername.trim()}`);
      setShowConnect(false);
      setDiscogsUsername('');
      fetchStatus();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to connect');
    } finally {
      setConnecting(false);
    }
  };

  const handleImport = async () => {
    setImporting(true);
    setProgress({ status: 'in_progress', total: 0, imported: 0, skipped: 0 });
    try {
      const resp = await axios.post(`${API}/discogs/import`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProgress(resp.data);
    } catch (err) {
      setImporting(false);
      toast.error(err.response?.data?.detail || 'Failed to start import');
    }
  };

  const handleDisconnect = async () => {
    try {
      await axios.delete(`${API}/discogs/disconnect`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatus({ connected: false });
      setProgress(null);
      setShowDisconnect(false);
      toast.success('Discogs account disconnected');
    } catch (err) {
      toast.error('Failed to disconnect');
    }
  };

  if (loading) {
    return (
      <Card className="border-honey/30">
        <CardContent className="py-6">
          <div className="flex items-center gap-3 text-muted-foreground">
            <Loader2 className="w-4 h-4 animate-spin" />
            Checking Discogs connection...
          </div>
        </CardContent>
      </Card>
    );
  }

  const progressPercent = progress?.total > 0
    ? Math.round(((progress.imported + progress.skipped) / progress.total) * 100)
    : 0;

  return (
    <>
      <Card className="border-honey/30" data-testid="discogs-import-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-vinyl-black rounded-lg flex items-center justify-center">
                <Disc className="w-5 h-5 text-honey" />
              </div>
              <div>
                <CardTitle className="text-base">Import from Discogs</CardTitle>
                <CardDescription>
                  {status?.connected
                    ? `Connected as ${status.discogs_username}`
                    : 'Connect your Discogs account to import your collection'}
                </CardDescription>
              </div>
            </div>
            {status?.connected && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDisconnect(true)}
                className="text-muted-foreground hover:text-red-500"
                data-testid="discogs-disconnect-btn"
              >
                <Unplug className="w-4 h-4" />
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {!status?.connected ? (
            <Button
              onClick={handleConnect}
              className="bg-vinyl-black text-white hover:bg-vinyl-black/80 rounded-full gap-2 w-full sm:w-auto"
              data-testid="discogs-connect-btn"
            >
              <ExternalLink className="w-4 h-4" />
              Connect Discogs Account
            </Button>
          ) : importing && progress ? (
            <div className="space-y-3" data-testid="discogs-import-progress">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-honey-amber" />
                  Importing collection...
                </span>
                <span className="text-muted-foreground">
                  {progress.imported + progress.skipped} / {progress.total || '...'}
                </span>
              </div>
              <Progress value={progressPercent} className="h-2" />
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span className="text-green-600">{progress.imported} imported</span>
                <span>{progress.skipped} skipped</span>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {progress?.status === 'completed' && progress.imported > 0 && (
                <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg" data-testid="import-complete-msg">
                  <CheckCircle2 className="w-4 h-4" />
                  Last import: {progress.imported} records imported
                  {progress.skipped > 0 && `, ${progress.skipped} skipped (duplicates)`}
                </div>
              )}
              {progress?.status === 'error' && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4" />
                  {progress.error_message || 'Import failed'}
                </div>
              )}
              <div className="flex items-center gap-3">
                <Button
                  onClick={handleImport}
                  className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
                  data-testid="discogs-sync-btn"
                >
                  <RefreshCw className="w-4 h-4" />
                  {status?.last_synced ? 'Sync Now' : 'Import Collection'}
                </Button>
                {status?.last_synced && (
                  <span className="text-xs text-muted-foreground">
                    Last synced: {new Date(status.last_synced).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Disconnect Dialog */}
      <Dialog open={showDisconnect} onOpenChange={setShowDisconnect}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading">Disconnect Discogs</DialogTitle>
            <DialogDescription>
              This will remove the connection to your Discogs account. Records already imported will remain in your collection.
            </DialogDescription>
          </DialogHeader>
          <div className="flex gap-3 justify-end pt-4">
            <Button variant="outline" onClick={() => setShowDisconnect(false)}>Cancel</Button>
            <Button
              variant="destructive"
              onClick={handleDisconnect}
              data-testid="confirm-disconnect-btn"
            >
              Disconnect
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Connect with Username Dialog */}
      <Dialog open={showConnect} onOpenChange={setShowConnect}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading">Connect Discogs</DialogTitle>
            <DialogDescription>
              Enter your Discogs username to import your public collection.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleTokenConnect} className="space-y-4 pt-2">
            <Input
              placeholder="Your Discogs username"
              value={discogsUsername}
              onChange={(e) => setDiscogsUsername(e.target.value)}
              className="border-honey/50"
              data-testid="discogs-username-input"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <Button type="button" variant="outline" onClick={() => setShowConnect(false)}>Cancel</Button>
              <Button 
                type="submit"
                className="bg-honey text-vinyl-black hover:bg-honey-amber"
                disabled={!discogsUsername.trim() || connecting}
                data-testid="discogs-username-submit"
              >
                {connecting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Connect
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default DiscogsImport;
