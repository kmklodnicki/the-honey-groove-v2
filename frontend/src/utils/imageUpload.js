import heic2any from 'heic2any';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'];
const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'];
const MAX_SIZE = 15 * 1024 * 1024; // 15MB

/**
 * Validate an image file before upload.
 * Returns null if valid, or an error message string.
 */
export function validateImageFile(file) {
  if (!file) return 'no file selected.';

  const ext = file.name?.split('.').pop()?.toLowerCase() || '';
  const typeOk = ALLOWED_TYPES.includes(file.type?.toLowerCase());
  const extOk = ALLOWED_EXTENSIONS.includes(ext);

  if (!typeOk && !extOk) {
    return 'please upload a jpg, png, webp, or heic image.';
  }

  if (file.size > MAX_SIZE) {
    return 'image must be less than 15mb.';
  }

  return null;
}

function isHeic(file) {
  const ext = file.name?.split('.').pop()?.toLowerCase() || '';
  const type = file.type?.toLowerCase() || '';
  return ext === 'heic' || ext === 'heif' || type === 'image/heic' || type === 'image/heif';
}

/**
 * Try converting via native browser Canvas (works on macOS/iOS Safari & Chrome).
 */
function canvasConvert(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      // If image decoded to 0x0, the browser can't handle this format
      if (img.width === 0 || img.height === 0) { URL.revokeObjectURL(url); reject(new Error('empty')); return; }
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      canvas.toBlob(
        (blob) => {
          URL.revokeObjectURL(url);
          if (blob && blob.size > 100) resolve(blob);
          else reject(new Error('canvas export failed'));
        },
        'image/jpeg',
        0.9
      );
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('native decode failed')); };
    img.src = url;
  });
}

/**
 * Convert HEIC/HEIF to JPEG, trying multiple strategies.
 * For non-HEIC files, returns the original file unchanged.
 */
export async function prepareImageForUpload(file) {
  if (!isHeic(file)) return file;

  const newName = file.name.replace(/\.heic$/i, '.jpg').replace(/\.heif$/i, '.jpg');

  // Strategy 1: Native Canvas (macOS/iOS browsers can decode HEIC natively)
  try {
    const blob = await canvasConvert(file);
    console.log('HEIC converted via native Canvas');
    return new File([blob], newName, { type: 'image/jpeg' });
  } catch (e) {
    console.log('Canvas conversion failed, trying heic2any:', e.message);
  }

  // Strategy 2: heic2any WebAssembly decoder
  try {
    const blob = await heic2any({ blob: file, toType: 'image/jpeg', quality: 0.9 });
    const converted = Array.isArray(blob) ? blob[0] : blob;
    console.log('HEIC converted via heic2any');
    return new File([converted], newName, { type: 'image/jpeg' });
  } catch (e) {
    console.log('heic2any conversion failed, uploading raw:', e.message);
  }

  // Strategy 3: Upload raw file — let the backend handle it
  return file;
}
