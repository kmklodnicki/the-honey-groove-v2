/**
 * CoverUploadModal — lets a user upload or replace the cover photo for a record they own.
 *
 * Props:
 *   open         {boolean}
 *   onClose      {function}
 *   recordId     {string}
 *   albumTitle   {string}
 *   artistName   {string}
 *   onSuccess    {function(updatedRecord)} called after successful upload
 */
import React, { useState, useRef, useCallback } from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { Camera, X, Check, Loader2, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { API } from '../utils/apiBase';
import { validateImageFile, prepareImageForUpload } from '../utils/imageUpload';
import safeStorage from '../utils/safeStorage';

export default function CoverUploadModal({ open, onClose, recordId, albumTitle, artistName, onSuccess }) {
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const reset = useCallback(() => {
    setPreview(null);
    setFile(null);
    setUploading(false);
  }, []);

  const handleClose = useCallback(() => {
    reset();
    onClose();
  }, [reset, onClose]);

  const handleFileChange = async (e) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    console.log('CoverUpload: selected file', selected.name, selected.type, selected.size);

    const err = validateImageFile(selected);
    if (err) { toast.error(err); return; }

    try {
      const converted = await prepareImageForUpload(selected);
      console.log('CoverUpload: prepared file', converted.name, converted.type, converted.size);
      setFile(converted);
      const url = URL.createObjectURL(converted);
      setPreview(url);
    } catch (e) {
      console.error('CoverUpload: prepareImageForUpload failed', e);
      toast.error('Could not read image. Please try a different file.');
    }
  };

  const handleUpload = async () => {
    if (!file) { toast.error('No file selected — please pick a photo first.'); return; }
    if (!recordId) { toast.error('Missing record ID — please close and try again.'); return; }
    setUploading(true);
    try {
      const token = safeStorage.getItem('honeygroove_token');
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API}/records/${recordId}/cover`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Upload failed');
      }
      const updated = await res.json();
      toast.success('Cover photo updated!');
      onSuccess?.(updated);
      handleClose();
    } catch (e) {
      toast.error(e.message || `Upload failed. Please try again.`);
      console.error('CoverUpload error:', e);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleClose(); }}>
      <DialogContent className="max-w-sm w-full p-0 overflow-hidden rounded-2xl">
        <div className="flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-5 pt-5 pb-3">
            <div>
              <h2 className="font-serif text-base font-semibold">Add Cover Photo</h2>
              {(albumTitle || artistName) && (
                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                  {albumTitle}{artistName ? ` · ${artistName}` : ''}
                </p>
              )}
            </div>
            <button onClick={handleClose} className="text-muted-foreground hover:text-foreground transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Preview area */}
          <div className="mx-5 mb-4">
            {preview ? (
              <div className="relative aspect-square rounded-xl overflow-hidden bg-muted">
                <img src={preview} alt="Preview" className="w-full h-full object-cover" />
                <button
                  onClick={() => { setPreview(null); setFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                  className="absolute top-2 right-2 rounded-full p-1"
                  style={{ background: 'rgba(0,0,0,0.55)' }}
                >
                  <X className="w-3.5 h-3.5 text-white" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full aspect-square rounded-xl border-2 border-dashed border-honey/40 flex flex-col items-center justify-center gap-2 hover:border-honey/70 hover:bg-honey/5 transition-colors"
              >
                <div className="rounded-full p-3 bg-honey/10">
                  <Camera className="w-6 h-6 text-honey-amber" />
                </div>
                <div className="text-center px-4">
                  <p className="text-sm font-medium">Choose a photo</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Snap a clean photo of your album cover</p>
                </div>
              </button>
            )}
          </div>

          {/* Guidance */}
          {!preview && (
            <div className="mx-5 mb-4 rounded-lg bg-cream/60 px-3 py-2 text-xs text-muted-foreground space-y-1">
              <p className="font-medium text-foreground/80">Tips for a great photo:</p>
              <p>• Lay the record flat under good light</p>
              <p>• Keep the cover filling the frame</p>
              <p>• JPEG, PNG, WebP, or HEIC — max 10MB</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 px-5 pb-5">
            <Button variant="outline" size="sm" className="flex-1" onClick={handleClose} disabled={uploading}>
              Cancel
            </Button>
            {!preview ? (
              <Button
                size="sm"
                className="flex-1 bg-honey text-vinyl-black hover:bg-honey/90"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-3.5 h-3.5 mr-1.5" />
                Select Photo
              </Button>
            ) : (
              <Button
                size="sm"
                className="flex-1 bg-honey text-vinyl-black hover:bg-honey/90"
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? (
                  <><Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />Uploading…</>
                ) : (
                  <><Check className="w-3.5 h-3.5 mr-1.5" />Upload</>
                )}
              </Button>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.webp,.heic,.heif"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}
