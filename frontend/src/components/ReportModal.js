import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Loader2, AlertTriangle, ImagePlus, X, Heart } from 'lucide-react';
import { toast } from 'sonner';

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

const ReportModal = ({ open, onOpenChange, targetType, targetId }) => {
  const { API, token } = useAuth();
  const [mode, setMode] = useState('bug'); // 'bug' | 'feedback'
  const [reasons, setReasons] = useState([]);
  const [selectedReason, setSelectedReason] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [notesError, setNotesError] = useState('');
  const [screenshotFile, setScreenshotFile] = useState(null);
  const [screenshotPreview, setScreenshotPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const isBugMode = mode === 'bug';
  const showToggle = targetType === 'bug';

  useEffect(() => {
    if (open && targetType) {
      if (targetType === 'bug') setMode('bug');
      axios.get(`${API}/reports/reasons/${targetType}`)
        .then(r => setReasons(r.data.reasons || []))
        .catch(() => setReasons([]));
      setSelectedReason('');
      setNotes('');
      setNotesError('');
      setScreenshotFile(null);
      setScreenshotPreview(null);
    }
  }, [open, targetType, API]);

  const switchMode = (m) => {
    setMode(m);
    setSelectedReason('');
    setNotes('');
    setNotesError('');
    removeScreenshot();
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!ALLOWED_TYPES.includes(file.type)) { toast.error('Please select a JPG, PNG, or WebP image.'); return; }
    if (file.size > MAX_FILE_SIZE) { toast.error('File must be under 10MB.'); return; }
    setScreenshotFile(file);
    setScreenshotPreview(URL.createObjectURL(file));
  };

  const removeScreenshot = () => {
    if (screenshotPreview) URL.revokeObjectURL(screenshotPreview);
    setScreenshotFile(null);
    setScreenshotPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async () => {
    if (isBugMode && !selectedReason) { toast.error('Please select a reason'); return; }
    if (!notes.trim()) {
      setNotesError(isBugMode ? 'Please tell us what happened.' : 'Please share your thoughts.');
      return;
    }
    setNotesError('');
    setSubmitting(true);
    try {
      let screenshotUrl = null;
      if (screenshotFile) {
        setUploading(true);
        const formData = new FormData();
        formData.append('file', screenshotFile);
        const uploadResp = await axios.post(`${API}/upload`, formData, {
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
        });
        screenshotUrl = uploadResp.data.url;
        setUploading(false);
      }

      const body = {
        target_type: isBugMode ? targetType : 'feedback',
        target_id: targetId || null,
        reason: isBugMode ? selectedReason : 'General Feedback',
        notes,
        screenshot_url: screenshotUrl,
        page_url: window.location.href,
        browser_info: navigator.userAgent,
      };
      await axios.post(`${API}/reports/submit`, body, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success(isBugMode ? 'Report submitted. Our team will review it.' : 'Thanks for your feedback!');
      onOpenChange(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit');
    } finally {
      setSubmitting(false);
      setUploading(false);
    }
  };

  const titles = { listing: 'Report Listing', seller: 'Report User', order: 'Report Issue', bug: 'Report a Bug' };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md border-honey/30" data-testid="report-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-800">
            {isBugMode ? <AlertTriangle className="w-5 h-5 text-amber-600" /> : <Heart className="w-5 h-5 text-amber-600" />}
            {showToggle ? (isBugMode ? 'Report a Bug' : 'General Feedback') : (titles[targetType] || 'Report')}
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            {isBugMode ? 'Help us keep The HoneyGroove safe. Select a reason below.' : 'We love hearing from you.'}
          </DialogDescription>
        </DialogHeader>

        {/* Toggle — only for bug/feedback entry point */}
        {showToggle && (
          <div className="flex rounded-full bg-stone-100 p-0.5 mt-1" data-testid="report-mode-toggle">
            <button
              type="button"
              onClick={() => switchMode('bug')}
              className={`flex-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                isBugMode ? 'bg-white text-amber-800 shadow-sm' : 'text-stone-500 hover:text-stone-700'
              }`}
              data-testid="toggle-bug"
            >
              Report a Bug
            </button>
            <button
              type="button"
              onClick={() => switchMode('feedback')}
              className={`flex-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                !isBugMode ? 'bg-white text-amber-800 shadow-sm' : 'text-stone-500 hover:text-stone-700'
              }`}
              data-testid="toggle-feedback"
            >
              General Feedback
            </button>
          </div>
        )}

        <div className="space-y-3 mt-2">
          {/* Reason selectors — bug mode only */}
          {isBugMode && (
            <div className="space-y-1.5" data-testid="reason-selectors">
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
          )}

          <div>
            <Textarea
              placeholder={isBugMode ? 'What happened?' : "tell us what you're liking, loving, and any improvements you'd like to see"}
              value={notes}
              onChange={e => { setNotes(e.target.value); if (notesError) setNotesError(''); }}
              className={`border-honey/30 ${isBugMode ? 'min-h-[80px]' : 'min-h-[120px]'} ${notesError ? 'border-red-400' : ''}`}
              data-testid="report-notes"
            />
            {notesError && <p className="text-xs text-red-500 mt-1" data-testid="report-notes-error">{notesError}</p>}
          </div>

          {/* Screenshot upload — bug mode only */}
          {isBugMode && (
            <div data-testid="screenshot-upload-section">
              {!screenshotPreview ? (
                <label className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-amber-300/60 bg-amber-50/30 cursor-pointer hover:bg-amber-50/60 transition-colors">
                  <ImagePlus className="w-4 h-4 text-amber-600" />
                  <span className="text-xs text-amber-700">Attach Screenshot (Optional)</span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".jpg,.jpeg,.png,.webp"
                    onChange={handleFileSelect}
                    className="hidden"
                    data-testid="screenshot-file-input"
                  />
                </label>
              ) : (
                <div className="relative inline-block" data-testid="screenshot-preview">
                  <img src={screenshotPreview} alt="Screenshot preview" className="w-24 h-24 object-cover rounded-lg border border-amber-200" />
                  <button type="button" onClick={removeScreenshot} className="absolute -top-2 -right-2 bg-white border border-gray-200 rounded-full p-0.5 shadow-sm hover:bg-red-50 transition-colors" data-testid="screenshot-remove-btn">
                    <X className="w-3.5 h-3.5 text-red-500" />
                  </button>
                  <p className="text-[10px] text-muted-foreground mt-1">{screenshotFile?.name}</p>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-2 justify-end">
            <Button variant="ghost" onClick={() => onOpenChange(false)} className="rounded-full text-xs" data-testid="report-cancel-btn">Cancel</Button>
            <Button
              onClick={handleSubmit}
              disabled={submitting || uploading || !notes.trim() || (isBugMode && !selectedReason)}
              className="bg-amber-600 text-white hover:bg-amber-700 rounded-full text-xs px-5"
              data-testid="report-submit-btn"
            >
              {(submitting || uploading) && <Loader2 className="w-3 h-3 animate-spin mr-1" />}
              {isBugMode ? 'Submit Report' : 'Send Feedback'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ReportModal;
