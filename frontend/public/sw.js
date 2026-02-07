/**
 * Service Worker para Drive+
 * Maneja cache de assets, offline fallback y background sync
 * IMPORTANTE: No cachear index.html ni / para evitar pantalla en blanco y logo viejo.
 */

const CACHE_VERSION = 'drive-plus-v2';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const IMAGE_CACHE = `${CACHE_VERSION}-images`;

// Solo assets que no cambian con cada deploy (index.html y / NUNCA aquí)
const STATIC_ASSETS = [
  '/offline.html'
];

// Límites de cache
const CACHE_LIMITS = {
  dynamic: 50,
  images: 100
};

// ============================================
// INSTALACIÓN
// ============================================
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('📦 Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// ============================================
// ACTIVACIÓN
// ============================================
self.addEventListener('activate', (event) => {
  console.log('✅ Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then(keys => {
        // Eliminar TODOS los caches antiguos (incl. v1) para forzar contenido nuevo
        return Promise.all(
          keys
            .filter(key => key.startsWith('drive-plus-'))
            .map(key => {
              console.log('🗑️ Service Worker: Deleting old cache:', key);
              return caches.delete(key);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// ============================================
// FETCH (Estrategia de Cache)
// ============================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Solo cachear peticiones GET
  if (request.method !== 'GET') return;

  // Ignorar peticiones a otros dominios (excepto APIs conocidas)
  if (url.origin !== location.origin && !url.origin.includes('railway.app')) {
    return;
  }

  // CRÍTICO: Navegación/documento (/, index.html) → siempre red, NUNCA cache
  // Evita pantalla en blanco y logo viejo tras un deploy
  if (request.mode === 'navigate' || request.destination === 'document') {
    event.respondWith(
      fetch(request).catch(() => caches.match('/offline.html') || new Response('Sin conexión', { status: 503 }))
    );
    return;
  }

  // manifest.json y logo: network-first para que se actualicen sin hard refresh
  if (url.pathname === '/manifest.json' || url.pathname === '/logo-drive.png') {
    event.respondWith(networkFirstStrategy(request, DYNAMIC_CACHE));
    return;
  }

  // Estrategia según tipo de recurso
  if (isImageRequest(request)) {
    event.respondWith(cacheFirstStrategy(request, IMAGE_CACHE));
  } else if (isStaticAsset(request)) {
    event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
  } else if (isAPIRequest(request)) {
    event.respondWith(networkFirstStrategy(request, DYNAMIC_CACHE));
  } else {
    event.respondWith(staleWhileRevalidateStrategy(request, DYNAMIC_CACHE));
  }
});

// ============================================
// ESTRATEGIAS DE CACHE
// ============================================

/**
 * Cache First: Intenta cache primero, luego red
 * Ideal para: Imágenes, assets estáticos
 */
async function cacheFirstStrategy(request, cacheName) {
  try {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
      return cached;
    }
    
    const response = await fetch(request);
    
    if (response.ok) {
      cache.put(request, response.clone());
      limitCacheSize(cacheName, CACHE_LIMITS[cacheName === IMAGE_CACHE ? 'images' : 'dynamic']);
    }
    
    return response;
  } catch (error) {
    console.error('Cache First failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

/**
 * Network First: Intenta red primero, luego cache
 * Ideal para: APIs, datos dinámicos
 */
async function networkFirstStrategy(request, cacheName) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
      limitCacheSize(cacheName, CACHE_LIMITS.dynamic);
    }
    
    return response;
  } catch (error) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
      return cached;
    }
    
    // Fallback offline
    return new Response(JSON.stringify({ 
      error: 'Offline',
      message: 'No hay conexión a internet'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * Stale While Revalidate: Devuelve cache y actualiza en background
 * Ideal para: Páginas HTML, datos que pueden estar desactualizados
 */
async function staleWhileRevalidateStrategy(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  const fetchPromise = fetch(request)
    .then(response => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached);
  
  return cached || fetchPromise;
}

// ============================================
// BACKGROUND SYNC
// ============================================
self.addEventListener('sync', (event) => {
  console.log('🔄 Background Sync:', event.tag);
  
  if (event.tag === 'sync-torneos') {
    event.waitUntil(syncTorneos());
  } else if (event.tag === 'sync-inscripciones') {
    event.waitUntil(syncInscripciones());
  } else if (event.tag === 'sync-resultados') {
    event.waitUntil(syncResultados());
  }
});

/**
 * Sincronizar torneos pendientes
 */
async function syncTorneos() {
  try {
    // Obtener torneos pendientes de IndexedDB
    const pendingTorneos = await getPendingData('torneos');
    
    for (const torneo of pendingTorneos) {
      try {
        const response = await fetch('/api/torneos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(torneo.data)
        });
        
        if (response.ok) {
          await removePendingData('torneos', torneo.id);
          await notifyClient('Torneo creado exitosamente', torneo.data.nombre);
        }
      } catch (error) {
        console.error('Error syncing torneo:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
    throw error; // Reintentar más tarde
  }
}

/**
 * Sincronizar inscripciones pendientes
 */
async function syncInscripciones() {
  try {
    const pendingInscripciones = await getPendingData('inscripciones');
    
    for (const inscripcion of pendingInscripciones) {
      try {
        const response = await fetch(`/api/torneos/${inscripcion.torneoId}/inscribir`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(inscripcion.data)
        });
        
        if (response.ok) {
          await removePendingData('inscripciones', inscripcion.id);
          await notifyClient('Inscripción completada', 'Te has inscrito al torneo');
        }
      } catch (error) {
        console.error('Error syncing inscripcion:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
    throw error;
  }
}

/**
 * Sincronizar resultados pendientes
 */
async function syncResultados() {
  try {
    const pendingResultados = await getPendingData('resultados');
    
    for (const resultado of pendingResultados) {
      try {
        const response = await fetch(`/api/salas/${resultado.salaId}/resultado`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(resultado.data)
        });
        
        if (response.ok) {
          await removePendingData('resultados', resultado.id);
          await notifyClient('Resultado guardado', 'El resultado se ha sincronizado');
        }
      } catch (error) {
        console.error('Error syncing resultado:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
    throw error;
  }
}

// ============================================
// PUSH NOTIFICATIONS (DESACTIVADO - Endpoint no creado aún)
// ============================================
// TODO: Habilitar cuando se cree el endpoint de push notifications en el backend
/*
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'Nueva notificación de Drive+',
    icon: '/logo-drive.png',
    badge: '/logo-drive.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: data.actions || []
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Drive+', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(windowClients => {
        // Si ya hay una ventana abierta, enfocarla
        for (const client of windowClients) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // Si no, abrir nueva ventana
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});
*/

// ============================================
// UTILIDADES
// ============================================

function isImageRequest(request) {
  return request.destination === 'image' || 
         /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(request.url);
}

function isStaticAsset(request) {
  return request.destination === 'style' ||
         request.destination === 'script' ||
         request.destination === 'font' ||
         /\.(css|js|woff|woff2|ttf|eot)$/i.test(request.url);
}

function isAPIRequest(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/api/') || 
         url.origin.includes('railway.app');
}

async function limitCacheSize(cacheName, maxItems) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  
  if (keys.length > maxItems) {
    // Eliminar los más antiguos
    await cache.delete(keys[0]);
    await limitCacheSize(cacheName, maxItems);
  }
}

async function notifyClient(title, body) {
  const clients = await self.clients.matchAll();
  clients.forEach(client => {
    client.postMessage({
      type: 'NOTIFICATION',
      title,
      body
    });
  });
}

// Helpers para IndexedDB (simplificados)
async function getPendingData(_storeName) {
  // En producción, usar IndexedDB real
  return [];
}

async function removePendingData(_storeName, _id) {
  // En producción, usar IndexedDB real
  return true;
}

console.log('🚀 Service Worker loaded');
