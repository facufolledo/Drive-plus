/**
 * Modal para intercambiar una pareja de un cruce con otra de otro cruce (playoffs).
 */
import { useState } from 'react';
import { X, ArrowRightLeft, AlertCircle } from 'lucide-react';
import torneoService from '../services/torneo.service';

interface Partido {
  id: number;
  fase: string;
  numero_partido?: number;
  pareja1_id?: number;
  pareja2_id?: number;
  pareja1_nombre?: string;
  pareja2_nombre?: string;
  estado: string;
}

interface ModalIntercambiarParejasPlayoffProps {
  isOpen: boolean;
  onClose: () => void;
  torneoId: number;
  partidoOrigen: Partido;
  partidosDestino: Partido[];
  onIntercambiado: () => void;
}

export default function ModalIntercambiarParejasPlayoff({
  isOpen,
  onClose,
  torneoId,
  partidoOrigen,
  partidosDestino,
  onIntercambiado,
}: ModalIntercambiarParejasPlayoffProps) {
  const [slotOrigen, setSlotOrigen] = useState<1 | 2>(1);
  const [partidoDestinoId, setPartidoDestinoId] = useState<number | null>(null);
  const [slotDestino, setSlotDestino] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const partidoDestino = partidosDestino.find((p) => p.id === partidoDestinoId);
  const nombreSlotOrigen = slotOrigen === 1 ? partidoOrigen.pareja1_nombre : partidoOrigen.pareja2_nombre;
  const nombreSlotDestino = partidoDestino
    ? (slotDestino === 1 ? partidoDestino.pareja1_nombre : partidoDestino.pareja2_nombre)
    : '—';

  const handleIntercambiar = async () => {
    if (!partidoDestinoId || partidoDestinoId === partidoOrigen.id) {
      setError('Elegí otro partido.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await torneoService.intercambiarParejasPlayoff(torneoId, {
        partido_id_a: partidoOrigen.id,
        partido_id_b: partidoDestinoId,
        slot_a: slotOrigen,
        slot_b: slotDestino,
      });
      onIntercambiado();
      onClose();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al intercambiar');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const labelFase = (p: Partido) => `${p.fase} · Partido ${p.numero_partido ?? p.id}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-card border border-cardBorder rounded-xl shadow-xl max-w-md w-full">
        <div className="flex items-center justify-between p-4 border-b border-cardBorder">
          <h3 className="text-lg font-bold text-textPrimary flex items-center gap-2">
            <ArrowRightLeft size={20} />
            Intercambiar parejas
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
            Intercambiá una pareja de este cruce con una pareja de otro cruce (solo partidos pendientes).
          </p>

          <div>
            <label className="block text-xs font-bold text-textSecondary mb-1">Pareja de este partido ({labelFase(partidoOrigen)})</label>
            <select
              value={slotOrigen}
              onChange={(e) => setSlotOrigen(Number(e.target.value) as 1 | 2)}
              className="w-full bg-background border border-cardBorder rounded-lg px-3 py-2 text-textPrimary text-sm"
            >
              <option value={1}>{partidoOrigen.pareja1_nombre || 'Pareja 1'}</option>
              <option value={2}>{partidoOrigen.pareja2_nombre || 'Pareja 2'}</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-textSecondary mb-1">Con pareja del partido</label>
            <select
              value={partidoDestinoId ?? ''}
              onChange={(e) => setPartidoDestinoId(Number(e.target.value) || null)}
              className="w-full bg-background border border-cardBorder rounded-lg px-3 py-2 text-textPrimary text-sm"
            >
              <option value="">Elegir partido...</option>
              {partidosDestino
                .filter((p) => p.id !== partidoOrigen.id)
                .map((p) => (
                  <option key={p.id} value={p.id}>
                    {labelFase(p)}
                  </option>
                ))}
            </select>
          </div>

          {partidoDestino && (
            <div>
              <label className="block text-xs font-bold text-textSecondary mb-1">Pareja del otro partido</label>
              <select
                value={slotDestino}
                onChange={(e) => setSlotDestino(Number(e.target.value) as 1 | 2)}
                className="w-full bg-background border border-cardBorder rounded-lg px-3 py-2 text-textPrimary text-sm"
              >
                <option value={1}>{partidoDestino.pareja1_nombre || 'Pareja 1'}</option>
                <option value={2}>{partidoDestino.pareja2_nombre || 'Pareja 2'}</option>
              </select>
            </div>
          )}

          {(nombreSlotOrigen || nombreSlotDestino) && (
            <div className="p-3 bg-primary/10 rounded-lg border border-primary/20 text-sm">
              <span className="font-medium text-textPrimary">{nombreSlotOrigen || 'TBD'}</span>
              <span className="mx-2 text-textSecondary">↔</span>
              <span className="font-medium text-textPrimary">{nombreSlotDestino || 'TBD'}</span>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-500 text-sm">
              <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
              {error}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-cardBorder flex gap-2 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-textSecondary hover:bg-background"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleIntercambiar}
            disabled={loading || !partidoDestinoId}
            className="px-4 py-2 rounded-lg text-sm font-bold bg-accent text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Intercambiando...' : 'Intercambiar'}
          </button>
        </div>
      </div>
    </div>
  );
}
