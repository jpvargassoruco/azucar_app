// ===== OFFLINE-FIRST CACHE (IndexedDB) =====
const DB_NAME = 'azucar-offline-cache';
const DB_VERSION = 1;
const STORES = ['glucose', 'meals', 'habits', 'medications', 'fasting', 'alarms'];

let db = null;

function openDB() {
  return new Promise((resolve, reject) => {
    if (db) return resolve(db);
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const d = e.target.result;
      STORES.forEach(store => {
        if (!d.objectStoreNames.contains(store)) {
          d.createObjectStore(store, { keyPath: 'cache_key' });
        }
      });
    };
    req.onsuccess = (e) => { db = e.target.result; resolve(db); };
    req.onerror = () => reject(req.error);
  });
}

async function cacheData(storeName, key, data) {
  try {
    const d = await openDB();
    const tx = d.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    store.put({ cache_key: key, data, timestamp: Date.now() });
    return new Promise(resolve => { tx.oncomplete = resolve; });
  } catch (e) {
    console.warn('Offline cache write failed:', e);
  }
}

async function getCachedData(storeName, key, maxAgeMs = 3600000) {
  try {
    const d = await openDB();
    const tx = d.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const result = await new Promise(resolve => {
      const req = store.get(key);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    });
    if (result && (Date.now() - result.timestamp) < maxAgeMs) {
      return result.data;
    }
  } catch (e) {
    console.warn('Offline cache read failed:', e);
  }
  return null;
}

// ===== PERIODIC BACKGROUND SYNC =====
async function registerPeriodicSync() {
  if (!('serviceWorker' in navigator)) return;
  const reg = await navigator.serviceWorker.ready;
  if ('periodicSync' in reg) {
    try {
      await reg.periodicSync.register('sync-health-data', {
        minInterval: 60 * 60 * 1000 // 1 hour minimum
      });
      console.log('Periodic sync registered');
    } catch (e) {
      console.warn('Periodic sync registration failed:', e);
    }
  }
}

// ===== OFFLINE-AWARE API FETCH =====
async function offlineFetch(url, options = {}, cacheKey = null, storeName = 'glucose') {
  // Try network first
  try {
    const token = localStorage.getItem('azucar_token');
    const headers = { ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(url, { ...options, headers });
    if (res.ok) {
      const data = await res.json();
      // Cache successful response
      if (cacheKey) await cacheData(storeName, cacheKey, data);
      return data;
    }
  } catch (e) {
    console.warn('Network fetch failed, trying cache:', e);
  }

  // Fallback to cache
  if (cacheKey) {
    const cached = await getCachedData(storeName, cacheKey);
    if (cached) {
      console.log('Serving from offline cache');
      return cached;
    }
  }

  throw new Error('No network and no cached data available');
}

// Register on load
registerPeriodicSync();

// Export for use in app
window.offlineFetch = offlineFetch;
window.cacheData = cacheData;
window.getCachedData = getCachedData;
