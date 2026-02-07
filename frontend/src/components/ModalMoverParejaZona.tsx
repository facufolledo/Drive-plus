/**
 * Modal para mover una pareja a otra zona (misma categoría).
 */
import { useState } from 'react';
import { X, ArrowRight, AlertCircle } from 'lucide-react';

interface ZonaOption {
  zona_id: number;
  zona_nombre: string;
  categoria_id?: number;
}

interface ModalMoverParejaZonaProps {
  isOpen: boolean;
  onClose: () => void;
  parejaNombre: string;
  parejaId: number;
  zonaOrigenId: number;
  zonaOrigenNombre: string;
  zonasDestino: ZonaOption[];
  onMover: (parejaId: number, zonaDestinoId: number) => Promise<void>;
}

export default function ModalMoverParejaZona({
  isOpen,
  onClose,
  parejaNombre,
  parejaId,
  zonaOrigenId,
  zonaOrigenNombre,
  zonasDestino,
  onMover,
}: ModalMoverParejaZonaProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleMover = async (zonaDestinoId: number) => {
    setError(null);
    setLoading(true);
    try {
      await onMover(parejaId, zonaDestinoId);
      onClose();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al mover la pareja');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-card border border-cardBorder rounded-xl shadow-xl max-w-md w-full">
        <div className="flex items-center justify-between p-4 border-b border-cardBorder">
          <h3 className="text-lg font-bold text-textPrimary flex items-center gap-2">
            <ArrowRight size={20} />
            Mover pareja a otra zona
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-background text-textSecondary"
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <p className="text-sm text-textSecondary">
            <span className="font-medium text-textPrimary">{parejaNombre}</span>
            <span className="mx-1">está en</span>
            <span className="font-medium text-textPrimary">{zonaOrigenNombre}</span>.
            Elegí la zona de destino (misma categoría):
          </p>

          {zonasDestino.length === 0 ? (
            <p className="text-sm text-textSecondary">
              No hay otras zonas en esta categoría para mover la pareja.
            </p>
          ) : (
            <div className="space-y-2">
              {zonasDestino.map((z) => (
                <button
                  key={z.zona_id}
                  type="button"
                  onClick={() => handleMover(z.zona_id)}
                  disabled={loading}
                  className="w-full flex items-center justify-between p-3 rounded-lg border border-cardBorder hover:border-primary hover:bg-primary/5 transition-colors text-left disabled:opacity-50"
                >
                  <span className="font-medium text-textPrimary">{z.zona_nombre}</span>
                  <ArrowRight size={18} className="text-primary flex-shrink-0" />
                </button>
              ))}
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-500 text-sm">
              <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
              {error}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-cardBorder">
          <button
            type="button"
            onClick={onClose}
            className="w-full px-4 py-2 rounded-lg text-sm font-medium text-textSecondary hover:bg-background"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
