import React, { useEffect } from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import confetti from 'canvas-confetti';

/**
 * BLOCK 500: "Authentication: Pure Gold" success screen.
 * Fires after OAuth callback with discogs=connected.
 * Gold Dust confetti, premium branding, vault CTA.
 */
const PureGoldModal = ({ open, onClose }) => {
  useEffect(() => {
    if (open) {
      // Gold Dust confetti burst
      const end = Date.now() + 1500;
      const goldColors = ['#FFD700', '#B8860B', '#FFA000', '#DAA520'];
      const frame = () => {
        confetti({
          particleCount: 3,
          angle: 60,
          spread: 55,
          origin: { x: 0, y: 0.6 },
          colors: goldColors,
        });
        confetti({
          particleCount: 3,
          angle: 120,
          spread: 55,
          origin: { x: 1, y: 0.6 },
          colors: goldColors,
        });
        if (Date.now() < end) requestAnimationFrame(frame);
      };
      frame();
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="sm:max-w-md p-0 overflow-hidden border-0 rounded-2xl" data-testid="pure-gold-modal">
        {/* Header */}
        <div className="px-6 pt-5 pb-4 text-center" style={{ background: 'linear-gradient(135deg, #1A1A1A 0%, #2A1A06 100%)' }}>
          <p className="text-[10px] font-medium tracking-[0.3em] uppercase mb-3" style={{ color: '#2C2C2C', fontFamily: '"DM Serif Display", Georgia, serif', color: '#B8860B' }} data-testid="pure-gold-brand">
            THE HONEY GROOVE
          </p>
          <h2 className="text-2xl font-bold text-white mb-1" style={{ fontFamily: '"DM Serif Display", Georgia, serif' }} data-testid="pure-gold-headline">
            Authentication: Pure Gold
          </h2>
        </div>

        {/* Body */}
        <div className="px-6 pb-6 pt-5 space-y-4 text-center">
          <p className="text-sm text-stone-600 leading-relaxed">
            Your connection is solid. We've synced your crates, verified your status,
            and polished up your stats. Welcome to the authenticated inner circle of
            The Honey Groove.
          </p>
          <p className="text-sm italic" style={{ color: '#C8861A' }}>
            Everything is looking sweet.
          </p>

          <Button
            onClick={onClose}
            className="w-full h-12 rounded-full text-base font-bold mt-2 transition-transform hover:scale-[1.02]"
            style={{ background: 'linear-gradient(135deg, #FFD700, #B8860B)', color: '#1A1A1A', boxShadow: '0 4px 20px rgba(255,215,0,0.3)' }}
            data-testid="enter-vault-btn"
          >
            Enter the Vault
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PureGoldModal;
