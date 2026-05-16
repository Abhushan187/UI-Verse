/* Service Worker: handles background sync for collections
   - listens for 'sync' event with tag 'collections-sync'
   - reads queued actions from IndexedDB and posts to /api/collections/sync
*/

const DB_NAME = 'ui-verse-db';
const STORE_QUEUE = 'sync-queue';
const SYNC_ENDPOINT = '/api/collections/sync';

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function getAllQueueFromSW() {
  return openDB().then(db => new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_QUEUE, 'readonly');
    const store = tx.objectStore(STORE_QUEUE);
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  }));
}

function clearQueueFromSW(ids) {
  return openDB().then(db => new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_QUEUE, 'readwrite');
    const store = tx.objectStore(STORE_QUEUE);
    ids.forEach(id => store.delete(id));
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  }));
}

self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('sync', event => {
  if (event.tag === 'collections-sync') {
    event.waitUntil((async () => {
      try {
        const queue = await getAllQueueFromSW();
        if (!queue || queue.length === 0) return;
        const res = await fetch(SYNC_ENDPOINT, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({actions: queue}),
          credentials: 'include'
        });
        if (res.ok) {
          const ids = queue.map(q => q.id).filter(Boolean);
          await clearQueueFromSW(ids);
          // notify clients
          const clients = await self.clients.matchAll();
          for (const c of clients) c.postMessage({type:'collections:sync:ok', synced: ids.length});
        }
      } catch (err) {
        // nothing: will retry next sync
      }
    })());
  }
});

self.addEventListener('message', event => {
  if (!event.data) return;
  if (event.data === 'trigger-sync') {
    self.registration.sync && self.registration.sync.register('collections-sync').catch(()=>{});
  }
});
// UI-Verse Service Worker — basic offline-first caching
const CACHE_NAME = 'ui-verse-v1';
const RUNTIME = 'runtime-cache';
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/compare.html',
  '/style.css',
  '/css/main.css',
  '/script.js'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME && k !== RUNTIME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

function cacheFirst(request) {
  return caches.match(request).then(cached => cached || fetch(request).then(resp => {
    return caches.open(RUNTIME).then(cache => { cache.put(request, resp.clone()); return resp; });
  })).catch(() => caches.match('/offline.html'));
}

function staleWhileRevalidate(request) {
  return caches.open(RUNTIME).then(cache =>
    cache.match(request).then(cached => {
      const network = fetch(request).then(resp => { cache.put(request, resp.clone()); return resp; }).catch(() => null);
      return cached || network;
    })
  );
}

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // navigation requests -> cache-first (serve offline page fallback)
  if (req.mode === 'navigate' || (req.method === 'GET' && req.headers.get('accept')?.includes('text/html'))) {
    event.respondWith(cacheFirst(req));
    return;
  }

  // CSS/JS: stale-while-revalidate
  if (req.destination === 'style' || req.destination === 'script') {
    event.respondWith(staleWhileRevalidate(req));
    return;
  }

  // images: cache-first
  if (req.destination === 'image') {
    event.respondWith(
      caches.match(req).then(cached => cached || fetch(req).then(resp => { caches.open(RUNTIME).then(c => c.put(req, resp.clone())); return resp; })).catch(() => caches.match('/offline.html'))
    );
    return;
  }

  // default: try cache, then network
  event.respondWith(caches.match(req).then(cached => cached || fetch(req)));
});
