/**
 * Modal para agregar una zona de último momento (2+ parejas que se inscriben tarde).
 * Solo visible antes de generar playoffs.
 */
import { useEffect, useState } from 'react';
import { X, Users, AlertCircle } from 'lucide-react';
import { torneoService } from '../services/torneo.service';

interface Pareja {
  id: number;
  jugador1_id: number;
  jugador2_id: number;
  categoria_id?: number;
  estado?: string;
  nombre_pareja?: string;
  pareja_nombre?: string;
  nombre?: string;
}

interface ModalAgregarZonaUltimoMomentoProps {
  isOpen: boolean;
  onClose: () => void;
  torneoId: number;
  categorias: { id: number; nombre: string }[];
  zonas: { id: number; nombre: string; categoria_id?: number; parejas?: { id: number }[] }[];
  onZonaCreada: () => void;
}

export default function ModalAgregarZonaUltimoMomento({
  isOpen,
  onClose,
  torneoId,
  categorias,
  zonas,
  onZonaCreada,
}: ModalAgregarZonaUltimoMomentoProps) {
  const [categoriaId, setCategoriaId] = useState<number | null>(null);
  const [nombreZona, setNombreZona] = useState('Zona último momento');
  const [parejasTodas, setParejasTodas] = useState<Pareja[]>([]);
  const [loadingParejas, setLoadingParejas] = useState(false);
  const [loadingSubmit, setLoadingSubmit] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [zonaRecienCreada, setZonaRecienCreada] = useState<{ id: number; nombre: string } | null>(null);
  const [generandoPartidos, setGenerandoPartidos] = useState(false);
  const [zonasCompletas, setZonasCompletas] = useState<{ parejas?: { id: number }[] }[]>([]);

  const parejasEnZona = new Set(
    (zonasCompletas.length ? zonasCompletas : zonas).flatMap((z) => (z.parejas || []).map((p: { id: number }) => p.id))
  );
  const parejasOpciones = parejasTodas.filter(
    (p) =>
      p.categoria_id === categoriaId &&
      !parejasEnZona.has(p.id) &&
      p.estado !== 'baja'
  );

  useEffect(() => {
    if (isOpen && torneoId) {
      setError(null);
      setZonaRecienCreada(null);
      setCategoriaId(categorias[0]?.id ?? null);
      setNombreZona('Zona último momento');
      setSelectedIds([]);
      setLoadingParejas(true);
      Promise.all([
        torneoService.listarParejas(torneoId, undefined, undefined),
        torneoService.listarZonas(torneoId),
      ])
        .then(([parejasData, zonasData]) => {
          setParejasTodas(Array.isArray(parejasData) ? parejasData : []);
          setZonasCompletas(Array.isArray(zonasData) ? zonasData : []);
        })
        .catch(() => {
          setParejasTodas([]);
          setZonasCompletas([]);
        })
        .finally(() => setLoadingParejas(false));
    }
  }, [isOpen, torneoId, categorias]);

  const togglePareja = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSubmit = async () => {
    if (!categoriaId || selectedIds.length < 2) {
      setError('Elegí una categoría y al menos 2 parejas.');
      return;
    }
    setLoadingSubmit(true);
    setError(null);
    try {
      const res = await torneoService.crearZonaUltimoMomento(torneoId, {
        categoria_id: categoriaId,
        nombre: nombreZona.trim() || 'Zona último momento',
        pareja_ids: selectedIds,
      });
      onZonaCreada();
      setZonaRecienCreada(res.zona);
      // No cerrar aún: ofrecer generar partidos
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al crear la zona');
    } finally {
      setLoadingSubmit(false);
    }
  };

  if (!isOpen) return null;

  const nombrePareja = (p: Pareja) =>
    p.nombre_pareja || p.pareja_nombre || p.nombre || `Pareja #${p.id}`;

  const generarPartidos = async () => {
    if (!zonaRecienCreada) return;
    setGenerandoPartidos(true);
    setError(null);
    try {
      await torneoService.generarPartidosZona(torneoId, zonaRecienCreada.id);
      onZonaCreada();
      onClose();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al generar partidos');
    } finally {
      setGenerandoPartidos(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-card border border-cardBorder rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-cardBorder">
          <h3 className="text-lg font-bold text-textPrimary flex items-center gap-2">
            <Users size={20} />
            Agregar zona de último momento
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-background text-textSecondary"
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4 overflow-y-auto space-y-4">
          {!zonaRecienCreada ? (
            <>
              <p className="text-sm text-textSecondary">
                Creá una zona nueva con parejas que se inscribieron tarde. Después podés generar los partidos de esta zona desde Programación.
              </p>

              <div>
                <label className="block text-xs font-bold text-textSecondary mb-1">Categoría</label>
                <select
                  value={categoriaId ?? ''}
                  onChange={(e) => {
                    setCategoriaId(Number(e.target.value) || null);
                    setSelectedIds([]);
                  }}
                  className="w-full bg-background border border-cardBorder rounded-lg px-3 py-2 text-textPrimary text-sm"
                >
                  {categorias.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-textSecondary mb-1">Nombre de la zona</label>
                <input
                  type="text"
                  value={nombreZona}
                  onChange={(e) => setNombreZona(e.target.value)}
                  placeholder="Ej: Zona último momento"
                  className="w-full bg-background border border-cardBorder rounded-lg px-3 py-2 text-textPrimary text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-textSecondary mb-2">
                  Parejas (mínimo 2) — se muestran las que aún no están en ninguna zona
                </label>
                {loadingParejas ? (
                  <p className="text-sm text-textSecondary">Cargando parejas...</p>
                ) : parejasOpciones.length === 0 ? (
                  <p className="text-sm text-textSecondary">
                    No hay parejas sin zona en esta categoría. Inscribí parejas primero o movelas desde otra zona.
                  </p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto border border-cardBorder rounded-lg p-2">
                    {parejasOpciones.map((p) => (
                      <label
                        key={p.id}
                        className="flex items-center gap-2 p-2 rounded hover:bg-background cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(p.id)}
                          onChange={() => togglePareja(p.id)}
                          className="rounded border-cardBorder"
                        />
                        <span className="text-sm text-textPrimary">{nombrePareja(p)}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : null}

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-500 text-sm">
              <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          {zonaRecienCreada && (
            <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <p className="text-sm text-green-700 dark:text-green-400 font-medium mb-2">
                Zona &quot;{zonaRecienCreada.nombre}&quot; creada. ¿Generar partidos de esta zona ahora?
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={generarPartidos}
                  disabled={generandoPartidos}
                  className="px-3 py-1.5 rounded-lg text-sm font-bold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
                >
                  {generandoPartidos ? 'Generando...' : 'Sí, generar partidos'}
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-1.5 rounded-lg text-sm font-medium text-textSecondary hover:bg-background"
                >
                  No, cerrar
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-cardBorder flex gap-2 justify-end">
          {!zonaRecienCreada ? (
            <>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg text-sm font-medium text-textSecondary hover:bg-background"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loadingSubmit || selectedIds.length < 2 || loadingParejas}
                className="px-4 py-2 rounded-lg text-sm font-bold bg-accent text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingSubmit ? 'Creando...' : 'Crear zona'}
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-textSecondary hover:bg-background"
            >
              Cerrar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
