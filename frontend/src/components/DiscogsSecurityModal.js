import React from 'react';
import { Shield, ExternalLink } from 'lucide-react';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

/**
 * BLOCK 455: Discogs Security Migration Modal
 * Shows on first login when user has old token-based Discogs connection
 * but no OAuth verification.
 */
const DiscogsSecurityModal = ({ open, onClose }) => {
  const { token, API } = useAuth();

  const handleReconnect = async () => {
    try {
      const resp = await axios.get(`${API}/discogs/oauth/start`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      window.location.href = resp.data.authorization_url;
    } catch {
      // Fallback: redirect to collection page
      window.location.href = '/collection';
    }
  };

  const handleDismiss = async () => {
    try {
      await axios.post(`${API}/discogs/dismiss-migration`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch { /* ignore */ }
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleDismiss(); }}>
      <DialogContent className="sm:max-w-md p-0 overflow-hidden border-0" data-testid="discogs-migration-modal">
        {/* Header band */}
        <div className="px-6 pt-6 pb-4" style={{ background: 'linear-gradient(135deg, #1A1A1A 0%, #2A1A06 100%)' }}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center"
              style={{ background: 'rgba(200,134,26,0.2)', border: '1px solid rgba(200,134,26,0.4)' }}>
              <Shield className="w-5 h-5 text-amber-400" />
            </div>
            <h2 className="text-xl font-bold text-white" style={{ fontFamily: '"DM Serif Display", serif' }}>
              Security Update
            </h2>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 pb-6 space-y-5">
          <p className="text-sm text-stone-600 leading-relaxed">
            We've made some security updates to keep the honey groove safe. To connect your collection, 
            you must now sign in through our secure Discogs flow. If you previously connected, your 
            account has been safely disconnected for verification.
          </p>

          <div className="rounded-xl p-4" style={{ background: '#FFFDF5', border: '1px solid rgba(200,134,26,0.2)' }}>
            <p className="text-xs text-stone-500 mb-1">What changed?</p>
            <ul className="text-xs text-stone-600 space-y-1">
              <li className="flex items-start gap-2">
                <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                Your Discogs identity is now verified via official OAuth login
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                No one can impersonate your collection
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                Your imported records remain safe
              </li>
            </ul>
          </div>

          <div className="flex flex-col gap-2.5 pt-1">
            <Button
              onClick={handleReconnect}
              className="w-full h-11 rounded-full text-sm font-semibold gap-2"
              style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)', color: '#1A1A1A' }}
              data-testid="reconnect-now-btn"
            >
              <ExternalLink className="w-4 h-4" />
              Reconnect Now
            </Button>
            <Button
              variant="ghost"
              onClick={handleDismiss}
              className="w-full h-10 rounded-full text-sm text-stone-400 hover:text-stone-600"
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
