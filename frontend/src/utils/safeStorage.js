// Safe localStorage wrapper for Safari private browsing compatibility.
// Safari private mode throws QuotaExceededError on setItem.
// Falls back to in-memory storage when localStorage is unavailable.

const memoryStore = {};

function isLocalStorageAvailable() {
  try {
    const testKey = '__honeygroove_storage_test__';
    localStorage.setItem(testKey, '1');
    localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

const canUseLS = isLocalStorageAvailable();

export const safeStorage = {
  getItem(key) {
    try {
      if (canUseLS) return localStorage.getItem(key);
    } catch { /* fall through */ }
    return memoryStore[key] || null;
  },
  setItem(key, value) {
    memoryStore[key] = value;
    try {
      if (canUseLS) localStorage.setItem(key, value);
    } catch { /* Safari private mode — in-memory only */ }
  },
  removeItem(key) {
    delete memoryStore[key];
    try {
      if (canUseLS) localStorage.removeItem(key);
    } catch { /* ignore */ }
  },
};

export default safeStorage;
