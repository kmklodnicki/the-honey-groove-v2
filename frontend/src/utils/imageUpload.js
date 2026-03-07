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
    return 'please upload a jpg, png, or webp image.';
  }

  if (file.size > MAX_SIZE) {
    return 'image must be less than 10mb.';
  }

  return null;
}
