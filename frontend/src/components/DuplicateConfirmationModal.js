import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Copy } from 'lucide-react';

const DuplicateConfirmationModal = ({ open, onConfirm, onCancel, copyCount, recordTitle }) => (
  <Dialog open={open} onOpenChange={(v) => { if (!v) onCancel(); }}>
    <DialogContent className="sm:max-w-md" data-testid="duplicate-detection-modal">
      <DialogHeader>
        <DialogTitle className="font-heading text-lg flex items-center gap-2">
          <Copy className="w-5 h-5 text-[#D4A828]" /> Duplicate Detected
        </DialogTitle>
        <DialogDescription className="text-sm text-muted-foreground pt-1">
          You already have {copyCount === 1 ? 'a copy' : `${copyCount} copies`} of
          {recordTitle ? <strong className="text-[#1E2A3A]"> {recordTitle}</strong> : ' this record'} in your collection. Would you like to add another copy?
        </DialogDescription>
      </DialogHeader>
      <DialogFooter className="flex gap-2 sm:gap-2 pt-2">
        <Button
          variant="outline"
          onClick={onCancel}
          className="flex-1 rounded-xl border-[#E5DBC8] text-[#3A4D63] hover:bg-[#FFFBF2]"
          data-testid="duplicate-cancel-btn"
        >
          No, Cancel
        </Button>
        <Button
          onClick={onConfirm}
          className="flex-1 rounded-xl bg-[#E8A820] text-[#1E2A3A] hover:bg-[#D49A18] border-0 font-medium"
          data-testid="duplicate-confirm-btn"
        >
          Yes, Add Another
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export default DuplicateConfirmationModal;
