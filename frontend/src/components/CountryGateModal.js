import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { MapPin } from 'lucide-react';

const CountryGateModal = ({ open, onClose }) => {
  const navigate = useNavigate();

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm text-center p-8" data-testid="country-gate-modal">
        <div className="flex flex-col items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center">
            <MapPin className="w-7 h-7 text-blue-600" />
          </div>
          <h3 className="font-heading text-xl text-vinyl-black">set your country first</h3>
          <p className="text-sm text-muted-foreground">
            Before you continue, please set your country in Settings so we can match you with the right listings.
          </p>
          <Button
            onClick={() => { onClose(); navigate('/settings'); }}
            className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
            data-testid="country-gate-settings-btn"
          >
            <MapPin className="w-4 h-4" /> go to settings
          </Button>
          <button onClick={onClose} className="text-xs text-muted-foreground hover:underline" data-testid="country-gate-dismiss">
            maybe later
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CountryGateModal;
