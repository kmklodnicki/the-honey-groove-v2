import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { CreditCard } from 'lucide-react';

const StripeGateModal = ({ open, onClose }) => {
  const navigate = useNavigate();

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm text-center p-8" data-testid="stripe-gate-modal">
        <div className="flex flex-col items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-[#F0E6C8] flex items-center justify-center">
            <CreditCard className="w-7 h-7 text-[#D4A828]" />
          </div>
          <h3 className="font-heading text-xl text-vinyl-black">connect stripe to list</h3>
          <p className="text-sm text-muted-foreground">
            you need to connect your Stripe account before you can list items for sale or trade. it only takes a minute.
          </p>
          <Button
            onClick={() => { onClose(); navigate('/settings'); }}
            className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
            data-testid="stripe-gate-connect-btn"
          >
            <CreditCard className="w-4 h-4" /> go to settings
          </Button>
          <button onClick={onClose} className="text-xs text-muted-foreground hover:underline" data-testid="stripe-gate-dismiss">
            maybe later
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default StripeGateModal;
