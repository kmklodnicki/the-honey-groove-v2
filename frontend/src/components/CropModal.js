import React, { useState, useCallback } from 'react';
import Cropper from 'react-easy-crop';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { ZoomIn, ZoomOut, RotateCw, Check, X } from 'lucide-react';

/**
 * Utility: create a cropped image from canvas.
 */
function getCroppedImg(imageSrc, pixelCrop) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.crossOrigin = 'anonymous';
    image.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = pixelCrop.width;
      canvas.height = pixelCrop.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(
        image,
        pixelCrop.x, pixelCrop.y, pixelCrop.width, pixelCrop.height,
        0, 0, pixelCrop.width, pixelCrop.height
      );
      canvas.toBlob(
        (blob) => blob ? resolve(blob) : reject(new Error('Canvas empty')),
        'image/jpeg',
        0.92
      );
    };
    image.onerror = reject;
    image.src = imageSrc;
  });
}

const CropModal = ({ open, onClose, imageSrc, onCropComplete }) => {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState(null);

  const onCropChange = useCallback((location) => setCrop(location), []);
  const onZoomChange = useCallback((z) => setZoom(z), []);

  const handleCropComplete = useCallback((_, croppedPixels) => {
    setCroppedAreaPixels(croppedPixels);
  }, []);

  const handleSave = async () => {
    if (!croppedAreaPixels || !imageSrc) return;
    try {
      const blob = await getCroppedImg(imageSrc, croppedAreaPixels);
      const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' });
      onCropComplete(file);
    } catch (err) {
      console.error('Crop error:', err);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="sm:max-w-md p-0 gap-0 rounded-2xl overflow-hidden [&>button]:hidden" data-testid="crop-modal">
        <div className="relative w-full h-[360px] bg-black">
          {imageSrc && (
            <Cropper
              image={imageSrc}
              crop={crop}
              zoom={zoom}
              rotation={rotation}
              aspect={1}
              cropShape="round"
              showGrid={false}
              onCropChange={onCropChange}
              onZoomChange={onZoomChange}
              onCropComplete={handleCropComplete}
            />
          )}
        </div>

        {/* Controls */}
        <div className="p-4 space-y-3 bg-white">
          {/* Zoom slider */}
          <div className="flex items-center gap-3">
            <ZoomOut className="w-4 h-4 text-muted-foreground shrink-0" />
            <input
              type="range"
              min={1}
              max={3}
              step={0.05}
              value={zoom}
              onChange={(e) => setZoom(Number(e.target.value))}
              className="flex-1 h-1.5 rounded-full appearance-none cursor-pointer accent-[#C8861A]"
              style={{ background: `linear-gradient(to right, #C8861A ${((zoom - 1) / 2) * 100}%, #e5e7eb ${((zoom - 1) / 2) * 100}%)` }}
              data-testid="crop-zoom-slider"
            />
            <ZoomIn className="w-4 h-4 text-muted-foreground shrink-0" />
          </div>

          {/* Rotate button */}
          <div className="flex justify-center">
            <button
              onClick={() => setRotation((r) => (r + 90) % 360)}
              className="text-xs text-muted-foreground hover:text-stone-700 flex items-center gap-1.5 transition-colors"
              data-testid="crop-rotate-btn"
            >
              <RotateCw className="w-3.5 h-3.5" /> Rotate
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex gap-2">
            <Button
              onClick={handleSave}
              className="flex-1 bg-honey text-vinyl-black hover:bg-honey-amber rounded-full"
              data-testid="crop-save-btn"
            >
              <Check className="w-4 h-4 mr-2" /> Apply
            </Button>
            <Button
              onClick={onClose}
              variant="outline"
              className="rounded-full border-honey/50"
              data-testid="crop-cancel-btn"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CropModal;
