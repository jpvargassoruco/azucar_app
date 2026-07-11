const CACHE_NAME = 'azucar-cache-v4';
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/css/app.css',
  '/js/app.js',
  '/js/theme.js',
  '/js/offline.js',
  '/js/help.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Network-first for HTML/CSS/JS (always get latest), cache-first for others
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // Always fetch API routes directly from network
  if (url.pathname.startsWith('/api')) {
    e.respondWith(fetch(e.request));
    return;
  }

  // Network-first for core app files (HTML, CSS, JS, manifest)
  const isAppFile = /\.(html|css|js|json)$/.test(url.pathname) || url.pathname === '/';
  if (isAppFile) {
    e.respondWith(
      fetch(e.request)
        .then((response) => {
          // Update cache with fresh response
          const cloned = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, cloned));
          return response;
        })
        .catch(() => {
          // Offline: serve from cache
          return caches.match(e.request);
        })
    );
  } else {
    // Cache-first for fonts, icons, images
    e.respondWith(
      caches.match(e.request).then((cached) => {
        if (cached) return cached;
        return fetch(e.request).then((response) => {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          const cloned = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, cloned));
          return response;
        });
      })
    );
  }
});

// Push notifications receiver
self.addEventListener('push', (e) => {
  let data = {
    title: 'Azúcar Control',
    body: 'Alerta de salud o recordatorio de hábito.',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-192x192.png',
    url: '/'
  };

  if (e.data) {
    try {
      data = e.data.json();
    } catch (err) {
      data.body = e.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/icons/icon-192x192.png',
    badge: data.badge || '/icons/icon-192x192.png',
    data: { url: data.url || '/' },
    vibrate: [100, 50, 100],
    actions: [{ action: 'open', title: 'Abrir' }]
  };

  e.waitUntil(self.registration.showNotification(data.title, options));
});

// Handle notification click event
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const targetUrl = e.notification.data.url || '/';
  e.waitUntil(
    clients.matchAll({ type: 'window' }).then((windowClients) => {
      for (let i = 0; i < windowClients.length; i++) {
        const client = windowClients[i];
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          return client.navigate(targetUrl).then((c) => c.focus());
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});

// Periodic Background Sync handler
self.addEventListener('periodicsync', (e) => {
  if (e.tag === 'sync-health-data') {
    e.waitUntil(syncHealthData());
  }
});

async function syncHealthData() {
  try {
    const clients = await self.clients.matchAll({ type: 'window' });
    if (clients.length > 0) {
      clients[0].postMessage({ type: 'SYNC_DATA' });
    }
  } catch (err) {
    console.warn('Periodic sync failed:', err);
  }
}

// Message handler for SW communication
self.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (e.data && e.data.type === 'FORCE_UPDATE') {
    self.skipWaiting();
    // Clear all caches except current
    caches.keys().then((keys) => {
      return Promise.all(keys.map((key) => caches.delete(key)));
    }).then(() => {
      // Notify all clients to reload
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => client.postMessage({ type: 'RELOAD_APP' }));
      });
    });
  }
});
