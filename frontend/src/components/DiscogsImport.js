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
import { ExternalLink, Plus, CheckCircle2, AlertCircle, Loader2, Unplug, Disc, ChevronDown, ChevronUp, Ban, Copy, AlertTriangle, Info } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import AlbumArt from './AlbumArt';
import PureGoldModal from './PureGoldModal';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';

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
      toast.success(`Discogs connected. Ready to import.`);
      window.history.replaceState({}, '', window.location.pathname);
      fetchStatus();
      // BLOCK 500: Show the "Pure Gold" success screen
      setShowPureGold(true);
      // BLOCK 573: Re-check verification status after OAuth — triggers Gold Shield
      axios.get(`${API}/user/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then((resp) => {
        if (resp.data?.golden_hive_verified) {
          toast.success('Golden Hive verified!');
        }
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
      toast.error(err.response?.data?.detail || 'Import failed. Please try again.');
    }
  };

  const handleCheckNew = async () => {
    // "Check for New Additions" — requires a fresh Discogs OAuth if no active token
    if (!status?.connected || !status?.oauth_verified) {
      // Re-initiate OAuth; after callback the user can run check-new
      handleConnect();
      return;
    }
    setImporting(true);
    setProgress({ status: 'in_progress', total: 0, imported: 0, skipped: 0 });
    try {
      const resp = await axios.post(`${API}/discogs/import/check-new`, {}, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 30000,
      });
      setProgress(resp.data);
    } catch (err) {
      setImporting(false);
      if (err.response?.status === 400 && err.response?.data?.detail?.includes('not connected')) {
        // Token was already discarded — re-auth required
        toast.info('Please reconnect to Discogs to check for new additions.');
        handleConnect();
      } else {
        toast.error(err.response?.data?.detail || 'Could not check for new additions.');
      }
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
    if (status?.migration_complete) return null; // Temporarily ignore the dismissal flag
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
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="w-8 h-8 bg-vinyl-black rounded-lg flex items-center justify-center shrink-0">
            <Disc className="w-4 h-4 text-honey" />
          </div>
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="text-sm font-semibold whitespace-nowrap">Import from Discogs</span>
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="w-3.5 h-3.5 text-muted-foreground cursor-help shrink-0" />
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-[260px] text-xs leading-relaxed">
                  <p>One-way import from your Discogs collection into The Honey Groove Vault.</p>
                  <p className="mt-1 text-muted-foreground">Use "Check for New Additions" anytime you add records to your Discogs.</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            {status?.needs_migration && (
              <span className="text-[10px] font-semibold text-[#D4A828] bg-[#F0E6C8] px-1.5 py-0.5 rounded-full border border-[#E5DBC8] shrink-0" data-testid="needs-migration-badge">
                Re-verify
              </span>
            )}
            {status?.has_imported && status?.last_synced && (
              <span className="text-xs text-muted-foreground truncate hidden sm:inline">
                Last import: {new Date(status.last_synced).toLocaleDateString()}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {status?.connected && !status?.needs_migration && !importing && (
              <>
                {status?.has_imported ? (
                  <Button onClick={handleCheckNew} size="sm"
                    className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-1.5 h-8 text-xs px-3"
                    data-testid="discogs-check-new-btn">
                    <Plus className="w-3.5 h-3.5" />
                    Check for New Additions
                  </Button>
                ) : (
                  <Button onClick={handleImport} size="sm"
                    className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-1.5 h-8 text-xs px-3"
                    data-testid="discogs-sync-btn">
                    Import
                  </Button>
                )}
              </>
            )}
            {status?.has_imported && (
              <Button variant="ghost" size="sm" onClick={() => setShowDisconnect(true)}
                className="text-muted-foreground hover:text-red-500 h-8 w-8 p-0" data-testid="discogs-disconnect-btn">
                <Unplug className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </div>

        {/* Expandable content: connect, progress, errors, post-import summary */}
        {(!status?.connected || status?.needs_migration || importing || (progress?.status === 'completed' && progress.imported > 0) || progress?.status === 'error') && (
        <CardContent className="pt-0 pb-3">
          {!status?.connected ? (
            <Button onClick={handleConnect}
              className="rounded-full gap-2 w-full sm:w-auto font-bold text-sm transition-all hover:shadow-lg animate-pulse-subtle"
              style={{ background: 'linear-gradient(135deg, #FFD700, #F4B521)', color: '#1A1A1A', border: '1.5px solid #DAA520', boxShadow: '0 0 20px rgba(255,215,0,0.3)' }}
              onMouseEnter={e => { e.currentTarget.style.background = '#E5AB00'; e.currentTarget.style.boxShadow = '0 0 28px rgba(255,215,0,0.5)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'linear-gradient(135deg, #FFD700, #F4B521)'; e.currentTarget.style.boxShadow = '0 0 20px rgba(255,215,0,0.3)'; }}
              data-testid="discogs-connect-btn">
              <ExternalLink className="w-4 h-4" />
              Connect to Discogs
            </Button>
          ) : status?.needs_migration ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-[#D4A828] bg-[#F0E6C8] px-3 py-1.5 rounded-lg" data-testid="migration-needed-msg">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>Re-verification needed via secure OAuth.</span>
              </div>
              <Button onClick={handleConnect}
                className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2 h-8 text-xs"
                data-testid="discogs-reconnect-btn">
                <ExternalLink className="w-4 h-4" />
                Reconnect
              </Button>
            </div>
          ) : importing && progress ? (
            <div className="space-y-2" data-testid="discogs-import-progress">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-honey-amber" />
                  {progress.total > 0
                    ? `Building your Vault...`
                    : 'Connecting to Discogs...'}
                </span>
                <span className="text-muted-foreground text-xs">
                  {progress.total > 0
                    ? `${progress.imported + progress.skipped} of ${progress.total}`
                    : ''}
                </span>
              </div>
              {progress.total > 0 && (
                <>
                  <Progress value={progressPercent} className="h-1.5" />
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    <span className="text-green-600">{progress.imported} added</span>
                    {progress.skipped > 0 && <span>{progress.skipped} skipped</span>}
                    {progress.newReleasesCreated > 0 && (
                      <span className="text-honey-amber">{progress.newReleasesCreated} new releases fetched</span>
                    )}
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {progress?.status === 'completed' && progress.imported > 0 && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 px-2.5 py-1.5 rounded-lg flex-1" data-testid="import-complete-msg">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                      <span>
                        Import complete! {progress.imported} records added
                        {progress.errors > 0 ? `. ${progress.errors} could not be matched.` : '.'}
                      </span>
                    </div>
                    <Button variant="ghost" size="sm" onClick={fetchSummary} className="text-xs text-honey-amber ml-2 h-7" data-testid="view-summary-btn">
                      Summary
                    </Button>
                  </div>
                  {/* Post-import summary card */}
                  <div className="text-[10px] text-muted-foreground px-1">
                    Imported via Discogs · album art loading in background
                    {progress.spotifyPending > 0 && ` (${progress.spotifyPending} pending)`}
                  </div>
                </div>
              )}
              {progress?.status === 'error' && (
                <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 px-2.5 py-1.5 rounded-lg">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{progress.error_message || 'Import failed'}</span>
                </div>
              )}
            </div>
          )}
        </CardContent>
        )}
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
                <div className="bg-[#FFFBF2] rounded-xl p-3 text-center">
                  <p className="font-heading text-2xl text-[#3A4D63]" data-testid="summary-skipped">{summary.skipped}</p>
                  <p className="text-xs text-muted-foreground">duplicates skipped</p>
                </div>
                {summary.errors > 0 ? (
                  <div className="bg-red-50 rounded-xl p-3 text-center">
                    <p className="font-heading text-2xl text-red-600">{summary.errors}</p>
                    <p className="text-xs text-red-500">errors</p>
                  </div>
                ) : (
                  <div className="bg-[#F0E6C8] rounded-xl p-3 text-center">
                    <p className="font-heading text-2xl text-[#D4A828]" data-testid="summary-total">{summary.total}</p>
                    <p className="text-xs text-[#D4A828]">total in Discogs</p>
                  </div>
                )}
              </div>

              {/* Sample covers */}
              {summary.sample_covers?.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wide">Recently Imported</p>
                  <div className="grid grid-cols-6 gap-1.5" data-testid="import-sample-covers">
                    {summary.sample_covers.slice(0, 12).map((c, i) => (
                      <div key={i} className="aspect-square rounded-lg overflow-hidden bg-[#F3EBE0]" title={`${c.artist} · ${c.title}`}>
                        {c.cover_url ? (
                          <AlbumArt src={c.cover_url} alt={c.title} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center"><Disc className="w-5 h-5 text-[#7A8694]" /></div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Collection stats */}
              {summary.collection_stats && (
                <div className="bg-gradient-to-r from-honey/10 to-honey/20 rounded-xl p-4" data-testid="import-summary-value">
                  <p className="text-xs text-muted-foreground mb-1">Your Vault</p>
                  <div className="flex items-baseline gap-3">
                    <p className="font-heading text-2xl text-vinyl-black">{summary.collection_stats.total_records} records</p>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">
                    Album art is loading in the background via Spotify matching.
                  </p>
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
  duplicate: { label: 'Already in Collection', icon: Copy, color: 'text-[#3A4D63]', bg: 'bg-[#FFFBF2]' },
  missing_data: { label: 'Missing Data', icon: Ban, color: 'text-[#D4A828]', bg: 'bg-[#F0E6C8]' },
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
    <div className="border border-[#E5DBC8]/60 rounded-xl overflow-hidden" data-testid="skipped-records-section">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-sm font-medium text-[#3A4D63] hover:bg-[#FFFBF2]/50 transition-colors"
        data-testid="skipped-records-toggle"
      >
        <span className="flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-[#7A8694]" />
          {records.length} record{records.length !== 1 ? 's' : ''} skipped
        </span>
        {expanded ? <ChevronUp className="w-4 h-4 text-[#7A8694]" /> : <ChevronDown className="w-4 h-4 text-[#7A8694]" />}
      </button>
      {expanded && (
        <div className="border-t border-[#E5DBC8] max-h-[280px] overflow-y-auto">
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
                    <div key={i} className="flex items-center gap-2 text-xs text-[#3A4D63] py-0.5 px-1" data-testid={`skipped-item-${reason}-${i}`}>
                      <span className="truncate font-medium text-[#3A4D63]">{item.artist}</span>
                      <span className="text-[#7A8694]">-</span>
                      <span className="truncate">{item.title}</span>
                      {item.discogs_id && (
                        <span className="shrink-0 text-[10px] text-[#7A8694] ml-auto">
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
