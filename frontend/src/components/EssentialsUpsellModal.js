import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Button } from './ui/button';
import { Award, ExternalLink, ShieldCheck } from 'lucide-react';

const CORE_ESSENTIALS = [
  {
    id: 'shield',
    honeyLabel: 'The Shield',
    name: 'Outer Sleeves (4mil Clarity)',
    descriptor: 'Crystal-clear outer protection for the records worth showing off.',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/gpztxclu_71NmJBFvbyL._AC_SL1500_.jpg',
  },
  {
    id: 'vault',
    honeyLabel: 'The Vault',
    name: 'Inner Sleeves (Antistatic Rice Paper)',
    descriptor: 'Antistatic inner sleeves that keep your vinyl clean and properly tucked away.',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/6g7drwvn_product2.jpg',
  },
  {
    id: 'polish',
    honeyLabel: 'The Polish',
    name: 'Complete Cleaning Kit',
    descriptor: 'A complete care kit for records that deserve a little extra love.',
    image: 'https://customer-assets.emergentagent.com/job_088a9581-bbfd-42c2-ad31-f5535df4814c/artifacts/obo7sks1_image3.jpg',
  },
];

const EssentialsUpsellModal = ({ open, onClose, onProceed }) => {
  const handleYes = () => {
    window.open('/essentials', '_blank');
    onProceed();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onProceed(); }}>
      <DialogContent className="max-w-md border-amber-200/50 p-0 overflow-hidden" data-testid="essentials-upsell-modal">
        {/* Header */}
        <div className="bg-gradient-to-b from-amber-50/80 to-white px-6 pt-6 pb-4">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg text-stone-900">
              <ShieldCheck className="w-5 h-5 text-amber-600" />
              Protect Your Investment
            </DialogTitle>
            <DialogDescription className="text-sm text-stone-500 mt-1.5 leading-relaxed">
              Vinyl deserves a little protection. Would you like to grab a few essentials to keep your new record safe and sounding sweet?
            </DialogDescription>
          </DialogHeader>
        </div>

        {/* Products */}
        <div className="px-6 pb-2 space-y-3">
          {CORE_ESSENTIALS.map(item => (
            <div key={item.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-stone-50/50 transition-colors" data-testid={`upsell-item-${item.id}`}>
              <img
                src={item.image}
                alt={item.name}
                className="w-14 h-14 rounded-lg object-cover border border-stone-200/60 shrink-0"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Award className="w-3 h-3 text-amber-500 shrink-0" />
                  <span className="text-[10px] font-semibold text-amber-600 uppercase tracking-wide">
                    {item.honeyLabel}
                  </span>
                </div>
                <p className="text-sm font-medium text-stone-800 leading-tight">{item.name}</p>
                <p className="text-xs text-stone-400 leading-snug mt-0.5 line-clamp-1">{item.descriptor}</p>
              </div>
            </div>
          ))}
          <p className="text-[11px] text-stone-400 italic text-center pt-1">
            Sleeves and cleaning tools can extend the life of your collection.
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-2 px-6 pb-6 pt-2">
          <Button
            variant="ghost"
            onClick={onProceed}
            className="flex-1 rounded-full text-sm text-stone-500"
            data-testid="upsell-no-thanks"
          >
            No Thanks
          </Button>
          <Button
            onClick={handleYes}
            className="flex-1 bg-amber-600 text-white hover:bg-amber-700 rounded-full text-sm gap-1.5"
            data-testid="upsell-yes"
          >
            Yes, Show Me
            <ExternalLink className="w-3.5 h-3.5" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default EssentialsUpsellModal;
