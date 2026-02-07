// Utilidades para PWA
import { logger } from './logger';

export interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

let deferredPrompt: BeforeInstallPromptEvent | null = null;

// Registrar Service Worker
export const registerServiceWorker = async (): Promise<void> => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });
      
      logger.log('✅ Service Worker registrado:', registration.scope);

      // Verificar actualizaciones al volver a la pestaña (evita cache viejo)
      const checkUpdate = () => registration.update();
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') checkUpdate();
      });
      setInterval(checkUpdate, 30 * 60 * 1000);

      // Escuchar actualizaciones
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              logger.log('🔄 Nueva versión disponible');
              // Aquí puedes mostrar un mensaje al usuario
              showUpdateNotification();
            }
          });
        }
      });

    } catch (error) {
      logger.error('❌ Error registrando Service Worker:', error);
    }
  }
};

// Capturar evento de instalación
export const setupInstallPrompt = (): void => {
  window.addEventListener('beforeinstallprompt', (e: Event) => {
    e.preventDefault();
    deferredPrompt = e as BeforeInstallPromptEvent;
    logger.log('💾 Prompt de instalación capturado');
    
    // Mostrar botón de instalación personalizado
    showInstallButton();
  });

  // Detectar cuando se instala
  window.addEventListener('appinstalled', () => {
    logger.log('✅ PWA instalada exitosamente');
    deferredPrompt = null;
    hideInstallButton();
  });
};

// Mostrar prompt de instalación
export const showInstallPrompt = async (): Promise<boolean> => {
  if (!deferredPrompt) {
    logger.log('⚠️ No hay prompt de instalación disponible');
    return false;
  }

  try {
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    logger.log(`👤 Usuario ${outcome === 'accepted' ? 'aceptó' : 'rechazó'} la instalación`);
    
    deferredPrompt = null;
    return outcome === 'accepted';
  } catch (error) {
    logger.error('❌ Error mostrando prompt:', error);
    return false;
  }
};

// Verificar si está instalada
export const isPWAInstalled = (): boolean => {
  return window.matchMedia('(display-mode: standalone)').matches ||
         (window.navigator as any).standalone === true ||
         document.referrer.includes('android-app://');
};

// Verificar si puede instalarse
export const canInstall = (): boolean => {
  return deferredPrompt !== null;
};

// Detectar si está online
export const isOnline = (): boolean => {
  return navigator.onLine;
};

// Escuchar cambios de conectividad
export const setupConnectivityListeners = (
  onOnline: () => void,
  onOffline: () => void
): void => {
  window.addEventListener('online', () => {
    logger.log('🌐 Conexión restaurada');
    onOnline();
  });

  window.addEventListener('offline', () => {
    logger.log('📡 Sin conexión');
    onOffline();
  });
};

// Solicitar permisos de notificaciones
export const requestNotificationPermission = async (): Promise<boolean> => {
  if (!('Notification' in window)) {
    logger.log('⚠️ Notificaciones no soportadas');
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  return false;
};

// Mostrar notificación local
export const showNotification = async (
  title: string,
  options?: NotificationOptions
): Promise<void> => {
  const hasPermission = await requestNotificationPermission();
  
  if (!hasPermission) {
    logger.log('⚠️ Sin permisos para notificaciones');
    return;
  }

  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    const registration = await navigator.serviceWorker.ready;
    await registration.showNotification(title, {
      icon: '/icons/icon-192x192.png',
      badge: '/icons/icon-72x72.png',
      vibrate: [200, 100, 200],
      ...options
    });
  } else {
    new Notification(title, options);
  }
};

// Funciones auxiliares para UI
function showInstallButton() {
  const event = new CustomEvent('pwa-installable', { detail: { canInstall: true } });
  window.dispatchEvent(event);
}

function hideInstallButton() {
  const event = new CustomEvent('pwa-installable', { detail: { canInstall: false } });
  window.dispatchEvent(event);
}

function showUpdateNotification() {
  const event = new CustomEvent('pwa-update-available');
  window.dispatchEvent(event);
}

// Registrar sincronización en background
export const registerBackgroundSync = async (tag: string): Promise<void> => {
  if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await (registration as any).sync.register(tag);
      logger.log('🔄 Background sync registrado:', tag);
    } catch (error) {
      logger.error('❌ Error registrando background sync:', error);
    }
  }
};
