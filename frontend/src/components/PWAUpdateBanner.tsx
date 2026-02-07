/**
 * Banner cuando hay una nueva versión de la app (Service Worker actualizado).
 * Evita que el usuario tenga que hacer Ctrl+Shift+R manualmente.
 */

import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';

export function PWAUpdateBanner() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const onUpdate = () => setShow(true);
    window.addEventListener('pwa-update-available', onUpdate);
    return () => window.removeEventListener('pwa-update-available', onUpdate);
  }, []);

  const handleReload = () => {
    window.location.reload();
  };

  if (!show) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-primary text-white px-4 py-2.5 shadow-md flex items-center justify-center gap-3 flex-wrap">
      <span className="text-sm font-medium">Hay una nueva versión de Drive+</span>
      <button
        onClick={handleReload}
        className="flex items-center gap-1.5 bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
      >
        <RefreshCw size={16} />
        Recargar
      </button>
    </div>
  );
}

export default PWAUpdateBanner;
