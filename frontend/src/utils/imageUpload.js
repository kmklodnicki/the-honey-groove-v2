import heic2any from 'heic2any';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'];
const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'];
const MAX_SIZE = 10 * 1024 * 1024; // 10MB (backend will compress)

/**
 * Validate an image file before upload.
 * Returns null if valid, or an error message string.
 */
export function validateImageFile(file) {
  if (!file) return 'no file selected.';

  const ext = file.name?.split('.').pop()?.toLowerCase() || '';
  const typeOk = ALLOWED_TYPES.includes(file.type?.toLowerCase());
  const extOk = ALLOWED_EXTENSIONS.includes(ext);

  // HEIC files on some browsers report empty or generic type
  if (!typeOk && !extOk) {
    return 'please upload a jpg, png, webp, or heic image.';
  }

  if (file.size > MAX_SIZE) {
    return 'image must be less than 10mb.';
  }

  return null;
}

/**
 * Check if a file is HEIC/HEIF format.
 */
function isHeic(file) {
  const ext = file.name?.split('.').pop()?.toLowerCase() || '';
  const type = file.type?.toLowerCase() || '';
  return ext === 'heic' || ext === 'heif' || type === 'image/heic' || type === 'image/heif';
}

/**
 * Convert HEIC/HEIF to JPEG on the client side, returning a new File.
 * For non-HEIC files, returns the original file unchanged.
 */
export async function prepareImageForUpload(file) {
  if (!isHeic(file)) return file;

  const blob = await heic2any({ blob: file, toType: 'image/jpeg', quality: 0.9 });
  const converted = Array.isArray(blob) ? blob[0] : blob;
  const newName = file.name.replace(/\.heic$/i, '.jpg').replace(/\.heif$/i, '.jpg');
  return new File([converted], newName, { type: 'image/jpeg' });
}
