import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Loader2, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const ReportModal = ({ open, onOpenChange, targetType, targetId }) => {
  const { API, token } = useAuth();
  const [reasons, setReasons] = useState([]);
  const [selectedReason, setSelectedReason] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open && targetType) {
      axios.get(`${API}/reports/reasons/${targetType}`)
        .then(r => setReasons(r.data.reasons || []))
        .catch(() => setReasons([]));
      setSelectedReason('');
      setNotes('');
    }
  }, [open, targetType, API]);

  const handleSubmit = async () => {
    if (!selectedReason) { toast.error('Please select a reason'); return; }
    setSubmitting(true);
    try {
      const body = {
        target_type: targetType,
        target_id: targetId || null,
        reason: selectedReason,
        notes,
        page_url: window.location.href,
        browser_info: navigator.userAgent,
      };
      await axios.post(`${API}/reports/submit`, body, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Report submitted. Our team will review it.');
      onOpenChange(false);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to submit report';
      toast.error(msg);
    } finally { setSubmitting(false); }
  };

  const titles = {
    listing: 'Report Listing',
    seller: 'Report Seller',
    order: 'Report Issue',
    bug: 'Report a Bug',
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md border-honey/30" data-testid="report-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-800">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            {titles[targetType] || 'Report'}
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Help us keep The HoneyGroove safe. Select a reason below.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 mt-2">
          <div className="space-y-1.5">
            {reasons.map(reason => (
              <button
                key={reason}
                type="button"
                onClick={() => setSelectedReason(reason)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all border ${
                  selectedReason === reason
                    ? 'bg-amber-100 border-amber-300 text-amber-800 font-medium'
                    : 'border-gray-200 hover:border-amber-200 hover:bg-amber-50/50 text-gray-700'
                }`}
                data-testid={`report-reason-${reason.toLowerCase().replace(/\s+/g, '-')}`}
              >
                {reason}
              </button>
            ))}
          </div>

          <Textarea
            placeholder="Additional details (optional)"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            className="border-honey/30 min-h-[80px]"
            data-testid="report-notes"
          />

          <div className="flex gap-2 justify-end">
            <Button variant="ghost" onClick={() => onOpenChange(false)} className="rounded-full text-xs" data-testid="report-cancel-btn">
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!selectedReason || submitting}
              className="bg-amber-600 text-white hover:bg-amber-700 rounded-full text-xs px-5"
              data-testid="report-submit-btn"
            >
              {submitting && <Loader2 className="w-3 h-3 animate-spin mr-1" />}
              Submit Report
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ReportModal;
