import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import { ExternalLink, RefreshCw, CheckCircle2, AlertCircle, Loader2, Unplug, Disc, ArrowRight, XCircle, ChevronDown, ChevronUp, Ban, Copy, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import AlbumArt from './AlbumArt';
import PureGoldModal from './PureGoldModal';

const DiscogsImport = ({ onImportComplete, compact = false }) => {
  const { token, API } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(null);
  const [showDisconnect, setShowDisconnect] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState(null);
  const [showPureGold, setShowPureGold] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const [statusResp, progressResp] = await Promise.all([
        axios.get(`${API}/discogs/status`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/discogs/import/progress`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setStatus(statusResp.data);
      if (statusResp.data.import_status?.status === 'in_progress') {
        setImporting(true);
        setProgress(statusResp.data.import_status);
      } else if (progressResp.data?.status === 'completed' && (progressResp.data?.imported > 0 || progressResp.data?.skipped > 0)) {
        setProgress(progressResp.data);
      }
    } catch (err) {
      console.error('Failed to fetch Discogs status:', err);
    } finally {
      setLoading(false);
    }
  }, [API, token]);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

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
            toast.success('collection imported successfully.');
            trackEvent('discogs_import_completed', { records_imported: resp.data.imported });
            if (resp.data.imported > 0) {
              navigate('/onboarding/welcome-to-the-hive');
            } else {
              fetchSummary();
            }
            onImportComplete?.();
          } else {
            toast.error(resp.data.error_message || 'Import failed. Please try again.');
          }
          fetchStatus();
        }
      } catch (err) { console.error('Poll error:', err); }
    }, 2000);
    return () => clearInterval(interval);
  }, [importing, API, token, fetchStatus, onImportComplete]);

  // Check URL params for OAuth callback result
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const discogsParam = params.get('discogs');
    if (discogsParam === 'connected') {
      toast.success(`discogs connected as ${params.get('username') || ''}.`);
      window.history.replaceState({}, '', window.location.pathname);
      fetchStatus();
      // BLOCK 500: Show the "Pure Gold" success screen
      setShowPureGold(true);
      // BLOCK 484: Trigger priority price re-link for first 50 records
      axios.post(`${API}/valuation/priority-relink`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      }).catch(() => {});
    } else if (discogsParam === 'error') {
      toast.error('Failed to connect Discogs: ' + (params.get('message') || 'Unknown error'));
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [fetchStatus, API, token]);

  const fetchSummary = async () => {
    try {
      const resp = await axios.get(`${API}/discogs/import/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resp.data.has_import) {
        setSummary(resp.data);
        setShowSummary(true);
      }
    } catch { /* ignore */ }
  };

  const handleConnect = async () => {
    try {
      // BLOCK 480: Pass window.location.origin so backend can build the correct callback URL
      const origin = encodeURIComponent(window.location.origin);
      const resp = await axios.get(`${API}/discogs/oauth/start?frontend_origin=${origin}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      window.location.href = resp.data.authorization_url;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start Discogs connection');
    }
  };

  const handleImport = async () => {
    setImporting(true);
    setProgress({ status: 'in_progress', total: 0, imported: 0, skipped: 0 });
    try {
      const resp = await axios.post(`${API}/discogs/import`, {}, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 30000,
      });
      setProgress(resp.data);
    } catch (err) {
      setImporting(false);
      toast.error(err.response?.data?.detail || 'could not find that Discogs username. double check and try again.');
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
      toast.success('discogs account disconnected.');
    } catch { toast.error('could not disconnect. try again.'); }
  };

  if (loading) {
    return compact ? null : (
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
                <div className="flex items-center gap-2">
                  <CardTitle className="text-base">Import from Discogs</CardTitle>
                  {status?.oauth_verified && (
                    <span className="text-[10px] font-semibold text-green-700 bg-green-50 px-1.5 py-0.5 rounded-full border border-green-200" data-testid="oauth-verified-badge">
                      Verified
                    </span>
                  )}
                  {status?.needs_migration && (
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded-full border border-amber-200" data-testid="needs-migration-badge">
                      Re-verify
                    </span>
                  )}
                </div>
                <CardDescription>
                  {status?.connected
                    ? `Connected as @${status.discogs_username}`
                    : 'Connect your Discogs account securely via OAuth'}
                </CardDescription>
              </div>
            </div>
            {status?.connected && (
              <Button variant="ghost" size="sm" onClick={() => setShowDisconnect(true)}
                className="text-muted-foreground hover:text-red-500" data-testid="discogs-disconnect-btn">
                <Unplug className="w-4 h-4" />
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {!status?.connected ? (
            <Button onClick={handleConnect}
              className="bg-vinyl-black text-white hover:bg-vinyl-black/80 rounded-full gap-2 w-full sm:w-auto"
              data-testid="discogs-connect-btn">
              <ExternalLink className="w-4 h-4" />
              Connect to Discogs
            </Button>
          ) : status?.needs_migration ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 px-3 py-2 rounded-lg" data-testid="migration-needed-msg">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>Your connection needs re-verification via secure OAuth login.</span>
              </div>
              <Button onClick={handleConnect}
                className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
                data-testid="discogs-reconnect-btn">
                <ExternalLink className="w-4 h-4" />
                Reconnect via OAuth
              </Button>
            </div>
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
              {progress?.status === 'completed' && (progress.imported > 0 || progress.skipped > 0) && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg flex-1" data-testid="import-complete-msg">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>
                      {progress.imported > 0
                        ? `Last import: ${progress.imported} records imported${progress.skipped > 0 ? `, ${progress.skipped} skipped (duplicates)` : ''}`
                        : `Collection in sync · ${progress.skipped} records already imported`}
                    </span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={fetchSummary} className="text-xs text-honey-amber ml-2" data-testid="view-summary-btn">
                    View Summary
                  </Button>
                </div>
              )}
              {progress?.status === 'error' && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{progress.error_message || 'Import failed'}</span>
                </div>
              )}
              <div className="flex items-center gap-3">
                <Button onClick={handleImport}
                  className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
                  data-testid="discogs-sync-btn">
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

      {/* Import Summary Modal */}
      <Dialog open={showSummary} onOpenChange={setShowSummary}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              Import Complete
            </DialogTitle>
            <DialogDescription>
              Your Discogs collection has been imported successfully.
            </DialogDescription>
          </DialogHeader>
          {summary && (
            <div className="space-y-5 pt-2">
              {/* Stats row */}
              <div className="grid grid-cols-3 gap-3" data-testid="import-summary-stats">
                <div className="bg-green-50 rounded-xl p-3 text-center">
                  <p className="font-heading text-2xl text-green-700" data-testid="summary-imported">{summary.imported}</p>
                  <p className="text-xs text-green-600">imported</p>
                </div>
                <div className="bg-stone-50 rounded-xl p-3 text-center">
                  <p className="font-heading text-2xl text-stone-600" data-testid="summary-skipped">{summary.skipped}</p>
                  <p className="text-xs text-muted-foreground">duplicates skipped</p>
                </div>
                {summary.errors > 0 ? (
                  <div className="bg-red-50 rounded-xl p-3 text-center">
                    <p className="font-heading text-2xl text-red-600">{summary.errors}</p>
                    <p className="text-xs text-red-500">errors</p>
                  </div>
                ) : (
                  <div className="bg-amber-50 rounded-xl p-3 text-center">
                    <p className="font-heading text-2xl text-amber-700" data-testid="summary-total">{summary.total}</p>
                    <p className="text-xs text-amber-600">total in Discogs</p>
                  </div>
                )}
              </div>

              {/* Sample covers */}
              {summary.sample_covers?.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wide">Recently Imported</p>
                  <div className="grid grid-cols-6 gap-1.5" data-testid="import-sample-covers">
                    {summary.sample_covers.slice(0, 12).map((c, i) => (
                      <div key={i} className="aspect-square rounded-lg overflow-hidden bg-stone-100" title={`${c.artist} · ${c.title}`}>
                        {c.cover_url ? (
                          <AlbumArt src={c.cover_url} alt={c.title} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center"><Disc className="w-5 h-5 text-stone-300" /></div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Collection value */}
              {summary.collection_stats && (
                <div className="bg-gradient-to-r from-honey/10 to-honey/20 rounded-xl p-4" data-testid="import-summary-value">
                  <p className="text-xs text-muted-foreground mb-1">Your Collection</p>
                  <div className="flex items-baseline gap-3">
                    <p className="font-heading text-2xl text-vinyl-black">{summary.collection_stats.total_records} records</p>
                    {summary.collection_stats.total_value > 0 && (
                      <p className="text-sm text-honey-amber font-medium">
                        ~${summary.collection_stats.total_value.toLocaleString(undefined, { maximumFractionDigits: 0 })} estimated
                      </p>
                    )}
                  </div>
                  {summary.collection_stats.valued_count > 0 && (
                    <p className="text-[10px] text-muted-foreground mt-1">
                      {summary.collection_stats.valued_count} records valued via Discogs market data
                      {summary.collection_stats.valued_count < summary.collection_stats.total_records && ' (more values loading in background)'}
                    </p>
                  )}
                  {summary.collection_stats.valued_count === 0 && summary.imported > 0 && (
                    <p className="text-[10px] text-muted-foreground mt-1">
                      Market values are being fetched in the background. Check back in a few minutes.
                    </p>
                  )}
                </div>
              )}

              {/* Skipped Records Log */}
              {summary.skipped_records?.length > 0 && (
                <SkippedRecordsLog records={summary.skipped_records} />
              )}

              <Button onClick={() => setShowSummary(false)}
                className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full"
                data-testid="close-summary-btn">
                Got it
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

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
            <Button variant="destructive" onClick={handleDisconnect} data-testid="confirm-disconnect-btn">
              Disconnect
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* BLOCK 500: Pure Gold success screen */}
      <PureGoldModal open={showPureGold} onClose={() => setShowPureGold(false)} />
    </>
  );
};

const REASON_CONFIG = {
  duplicate: { label: 'Already in Collection', icon: Copy, color: 'text-stone-500', bg: 'bg-stone-50' },
  missing_data: { label: 'Missing Data', icon: Ban, color: 'text-amber-600', bg: 'bg-amber-50' },
  error: { label: 'Import Error', icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-50' },
};

const SkippedRecordsLog = ({ records }) => {
  const [expanded, setExpanded] = useState(false);

  // Group by reason
  const grouped = records.reduce((acc, r) => {
    const key = r.reason || 'unknown';
    if (!acc[key]) acc[key] = [];
    acc[key].push(r);
    return acc;
  }, {});

  const reasonOrder = ['duplicate', 'missing_data', 'error'];

  return (
    <div className="border border-stone-200/60 rounded-xl overflow-hidden" data-testid="skipped-records-section">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-sm font-medium text-stone-600 hover:bg-stone-50/50 transition-colors"
        data-testid="skipped-records-toggle"
      >
        <span className="flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-stone-400" />
          {records.length} record{records.length !== 1 ? 's' : ''} skipped
        </span>
        {expanded ? <ChevronUp className="w-4 h-4 text-stone-400" /> : <ChevronDown className="w-4 h-4 text-stone-400" />}
      </button>
      {expanded && (
        <div className="border-t border-stone-100 max-h-[280px] overflow-y-auto">
          {reasonOrder.filter(r => grouped[r]).map(reason => {
            const cfg = REASON_CONFIG[reason] || REASON_CONFIG.error;
            const Icon = cfg.icon;
            const items = grouped[reason];
            return (
              <div key={reason} className="px-3 py-2" data-testid={`skipped-group-${reason}`}>
                <div className={`flex items-center gap-1.5 mb-1.5 px-2 py-1 rounded-md ${cfg.bg} w-fit`}>
                  <Icon className={`w-3 h-3 ${cfg.color}`} />
                  <span className={`text-[11px] font-semibold uppercase tracking-wide ${cfg.color}`}>
                    {cfg.label} ({items.length})
                  </span>
                </div>
                <div className="space-y-0.5">
                  {items.map((item, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-stone-500 py-0.5 px-1" data-testid={`skipped-item-${reason}-${i}`}>
                      <span className="truncate font-medium text-stone-700">{item.artist}</span>
                      <span className="text-stone-300">-</span>
                      <span className="truncate">{item.title}</span>
                      {item.discogs_id && (
                        <span className="shrink-0 text-[10px] text-stone-400 ml-auto">
                          #{item.discogs_id}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DiscogsImport;
