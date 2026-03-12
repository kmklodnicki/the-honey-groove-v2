import React, { useState } from 'react';
import { Shield, ExternalLink } from 'lucide-react';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

/**
 * BLOCK 587: Discogs Security / Import Intent Modal
 * 3-option modal:
 *   Connect Now  → intent = CONNECTED, launches OAuth
 *   Maybe Later  → intent = LATER, shows banner
 *   Proceed Without → intent = DECLINED, kills banner permanently
 */
const DiscogsSecurityModal = ({ open, onClose }) => {
  const { token, API, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);

  const setIntent = async (intent) => {
    try {
      await axios.post(`${API}/discogs/update-import-intent`, { intent }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch { /* ignore */ }
  };

  const handleConnect = async () => {
    setLoading(true);
    await setIntent('CONNECTED');
    try {
      const origin = encodeURIComponent(window.location.origin);
      localStorage.setItem('honeygroove_oauth_pending', JSON.stringify({ user_id: null, ts: Date.now() }));
      const resp = await axios.get(`${API}/discogs/oauth/start?frontend_origin=${origin}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      window.location.href = resp.data.authorization_url || resp.data.auth_url;
    } catch {
      setLoading(false);
      onClose();
    }
  };

  const handleLater = async () => {
    await setIntent('LATER');
    updateUser({ discogs_import_intent: 'LATER', discogs_migration_dismissed: true });
    onClose();
  };

  const handleDecline = async () => {
    await setIntent('DECLINED');
    updateUser({ discogs_import_intent: 'DECLINED', discogs_migration_dismissed: true });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleLater(); }}>
      <DialogContent className="sm:max-w-md p-0 overflow-hidden border-0" data-testid="discogs-migration-modal">
        <div className="px-6 pt-6 pb-4" style={{ background: 'linear-gradient(135deg, #1A1A1A 0%, #2A1A06 100%)' }}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center"
              style={{ background: 'rgba(200,134,26,0.2)', border: '1px solid rgba(200,134,26,0.4)' }}>
              <Shield className="w-5 h-5 text-amber-400" />
            </div>
            <h2 className="text-xl font-bold text-white" style={{ fontFamily: '"DM Serif Display", serif' }}>
              Secure Library Import
            </h2>
          </div>
        </div>

        <div className="px-6 pb-6 space-y-5">
          <p className="text-sm text-stone-600 leading-relaxed">
            To protect your library, we implemented a new secure safety feature to verify your identity.
            Connect your Discogs account via official OAuth to ensure your collection data remains private and uniquely yours.
          </p>

          <div className="rounded-xl p-4" style={{ background: '#FFFDF5', border: '1px solid rgba(200,134,26,0.2)' }}>
            <p className="text-xs text-stone-500 mb-1">What you get</p>
            <ul className="text-xs text-stone-600 space-y-1">
              <li className="flex items-start gap-2">
                <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                Your full Discogs collection imported in seconds
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                Verified identity — no one can impersonate your collection
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                Automatic collection value tracking
              </li>
            </ul>
          </div>

          <div className="flex flex-col gap-2.5 pt-1">
            <Button
              onClick={handleConnect}
              disabled={loading}
              className="w-full h-11 rounded-full text-sm font-bold gap-2 transition-all hover:shadow-lg disabled:opacity-60"
              style={{ background: '#FFBF00', color: '#1A1A1A', border: '1.5px solid #DAA520' }}
              onMouseEnter={e => { e.currentTarget.style.background = '#E5AB00'; }}
              onMouseLeave={e => { e.currentTarget.style.background = '#FFBF00'; }}
              data-testid="reconnect-now-btn"
            >
              <ExternalLink className="w-4 h-4" />
              {loading ? 'Connecting...' : 'Connect Discogs'}
            </Button>
            <Button
              variant="ghost"
              className="w-full h-10 rounded-full text-sm text-stone-500 hover:text-stone-700"
              onClick={async () => {
                await handleLater();
                onClose();
              }}
              data-testid="connect-later-btn"
            >
              Connect Later
            </Button>
          </div>
        </div>
        </DialogContent>
      </Dialog>
    );
  };

export default DiscogsSecurityModal;
