// Service Worker per PWA - Portale SLA
// Versione: 1.0.0

const CACHE_NAME = 'portale-sla-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// Install Event - Cache statico
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('[Service Worker] Installed successfully');
        return self.skipWaiting(); // Attiva immediatamente
      })
      .catch((error) => {
        console.error('[Service Worker] Install failed:', error);
      })
  );
});

// Activate Event - Pulizia cache vecchi
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[Service Worker] Activated');
      return self.clients.claim(); // Prendi controllo subito
    })
  );
});

// Fetch Event - Strategia Network First con Cache Fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  
  // Skip cross-origin requests
  if (!request.url.startsWith(self.location.origin)) {
    return;
  }
  
  // Skip API requests (sempre network)
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .catch((error) => {
          console.error('[Service Worker] API fetch failed:', error);
          // Ritorna risposta offline per API
          return new Response(
            JSON.stringify({ 
              error: 'Offline', 
              message: 'Sei offline. Alcune funzionalità potrebbero non essere disponibili.' 
            }),
            {
              headers: { 'Content-Type': 'application/json' },
              status: 503
            }
          );
        })
    );
    return;
  }
  
  // Per tutto il resto: Network First, poi Cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Clona la risposta per metterla in cache
        const responseToCache = response.clone();
        
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(request, responseToCache);
        });
        
        return response;
      })
      .catch(() => {
        // Se network fallisce, prova cache
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) {
            console.log('[Service Worker] Serving from cache:', request.url);
            return cachedResponse;
          }
          
          // Se non c'è nemmeno in cache, ritorna pagina offline
          if (request.destination === 'document') {
            return caches.match('/');
          }
          
          return new Response('Risorsa non disponibile offline', {
            status: 503,
            statusText: 'Service Unavailable'
          });
        });
      })
  );
});

// Push Notification Event (per future notifiche)
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received');
  
  const options = {
    body: event.data ? event.data.text() : 'Nuova notifica dal Portale SLA',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    tag: 'portale-sla-notification',
    requireInteraction: false
  };
  
  event.waitUntil(
    self.registration.showNotification('Portale SLA', options)
  );
});

// Notification Click Event
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked');
  
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});

// Background Sync Event (per sincronizzazione offline)
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);
  
  if (event.tag === 'sync-rimborsi') {
    event.waitUntil(syncRimborsi());
  }
});

// Funzione sync rimborsi (esempio per future implementazioni)
async function syncRimborsi() {
  try {
    // Qui andrebbe la logica per sincronizzare rimborsi creati offline
    console.log('[Service Worker] Syncing rimborsi...');
    // TODO: Implementare sync logic
  } catch (error) {
    console.error('[Service Worker] Sync failed:', error);
  }
}

console.log('[Service Worker] Loaded');
