import { useState, useEffect, useRef } from 'react';
import { X, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from './Button';
import { torneoService } from '../services/torneo.service';
import { toast } from 'react-hot-toast';

interface ModalCambiarHorarioProps {
  isOpen: boolean;
  onClose: () => void;
  torneoId: number;
  partidoId: number;
  partidoActual: any;
  onSuccess: () => void;
}

export default function ModalCambiarHorario({
  isOpen,
  onClose,
  torneoId,
  partidoId,
  partidoActual,
  onSuccess
}: ModalCambiarHorarioProps) {
  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [canchaId, setCanchaId] = useState<number>(1);
  const [canchas, setCanchas] = useState<any[]>([]);
  const [conflictos, setConflictos] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingCanchas, setLoadingCanchas] = useState(true);
  const [verificandoConflictos, setVerificandoConflictos] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (isOpen) {
      cargarCanchas();
      setConflictos(null);
      if (partidoActual.fecha_hora) {
        const fechaObj = new Date(partidoActual.fecha_hora);
        const year = fechaObj.getUTCFullYear();
        const month = fechaObj.getUTCMonth();
        const day = fechaObj.getUTCDate();
        const hours = fechaObj.getUTCHours();
        const minutes = fechaObj.getUTCMinutes();
        const fechaLocal = new Date(year, month, day, hours, minutes);
        setFecha(fechaLocal.toISOString().split('T')[0]);
        setHora(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`);
      }
      if (partidoActual.cancha_id) {
        setCanchaId(partidoActual.cancha_id);
      }
    }
  }, [isOpen, partidoActual]);

  // Debounced conflict check using GET endpoint
  useEffect(() => {
    if (fecha && hora && canchaId && isOpen) {
      // Reset to loading state immediately
      setConflictos(null);
      setVerificandoConflictos(true);

      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        verificarConflictosPreview();
      }, 400);
    } else {
      setConflictos(null);
      setVerificandoConflictos(false);
    }
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [fecha, hora, canchaId, isOpen]);

  const verificarConflictosPreview = async () => {
    try {
      const token = localStorage.getItem('firebase_token');
      const params = new URLSearchParams({ fecha, hora, cancha_id: String(canchaId) });
      const url = `${import.meta.env.VITE_API_URL}/torneos/${torneoId}/partidos/${partidoId}/verificar-horario?${params}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setConflictos(data.conflictos || []);
      } else {
        setConflictos([]);
      }
    } catch {
      setConflictos([]);
    } finally {
      setVerificandoConflictos(false);
    }
  };

  const cargarCanchas = async () => {
    try {
      setLoadingCanchas(true);
      const canchasData = await torneoService.listarCanchas(torneoId);
      const canchasActivas = canchasData.filter((c: any) => c.activa);
      setCanchas(canchasActivas);
      if (canchasActivas.length > 0 && !canchaId) {
        setCanchaId(canchasActivas[0].id);
      }
    } catch {
      toast.error('Error al cargar canchas');
    } finally {
      setLoadingCanchas(false);
    }
  };

  const handleCambiarHorario = async () => {
    if (!fecha || !hora) {
      toast.error('Debes seleccionar fecha y hora');
      return;
    }

    if (conflictos && conflictos.length > 0) {
      const confirmar = window.confirm(
        `⚠️ HAY ${conflictos.length} CONFLICTO(S)\n\n` +
        conflictos.map(c => `• ${c.mensaje || 'Solapamiento'}: ${c.pareja1} vs ${c.pareja2} (${c.fecha_hora})`).join('\n') +
        `\n\n¿Estás seguro de que quieres continuar?`
      );
      if (!confirmar) return;
    }

    setLoading(true);
    try {
      const url = `${import.meta.env.VITE_API_URL}/torneos/${torneoId}/partidos/${partidoId}/cambiar-horario`;
      const token = localStorage.getItem('firebase_token');

      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ fecha, hora, cancha_id: canchaId })
      });

      const data = await response.json();

      if (data.error === 'SOLAPAMIENTO_DETECTADO') {
        setConflictos(data.conflictos || []);
        toast.error(`${data.conflictos?.length || 0} conflicto(s) detectado(s)`);
        return;
      }

      if (!response.ok) {
        toast.error(data.detail || `Error ${response.status}`);
        return;
      }

      if (data.success) {
        toast.success('✅ Horario actualizado');
        onSuccess();
        onClose();
      } else {
        toast.error(data.detail || data.message || 'Error al cambiar horario');
      }
    } catch (error: any) {
      toast.error(`Error: ${error.message || 'Error de conexión'}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const conflictosCancha = conflictos?.filter(c => c.tipo === 'cancha') || [];
  const conflictosDescanso = conflictos?.filter(c => c.tipo === 'descanso') || [];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-cardBg border border-borderColor rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-borderColor">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-accent/10 rounded-lg">
                <Clock className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-textPrimary">Cambiar Horario</h2>
                <p className="text-sm text-textSecondary">
                  {partidoActual.pareja1_nombre} vs {partidoActual.pareja2_nombre}
                </p>
              </div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-borderColor/50 rounded-lg transition-colors">
              <X className="w-5 h-5 text-textSecondary" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">Fecha</label>
              <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-borderColor rounded-lg text-textPrimary focus:outline-none focus:ring-2 focus:ring-accent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">Hora</label>
              <input type="time" value={hora} onChange={(e) => setHora(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-borderColor rounded-lg text-textPrimary focus:outline-none focus:ring-2 focus:ring-accent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">Cancha</label>
              {loadingCanchas ? (
                <div className="text-sm text-textSecondary">Cargando canchas...</div>
              ) : (
                <select value={canchaId} onChange={(e) => setCanchaId(Number(e.target.value))}
                  className="w-full px-4 py-2 bg-background border border-borderColor rounded-lg text-textPrimary focus:outline-none focus:ring-2 focus:ring-accent">
                  {canchas.map((cancha) => (
                    <option key={cancha.id} value={cancha.id}>{cancha.nombre}</option>
                  ))}
                </select>
              )}
            </div>

            {/* Estado de verificación */}
            {verificandoConflictos && (
              <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-blue-500">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  Verificando disponibilidad...
                </div>
              </div>
            )}

            {/* Conflictos de cancha */}
            {!verificandoConflictos && conflictosCancha.length > 0 && (
              <div className="p-4 bg-red-500/10 border-2 border-red-500/50 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-bold text-red-500 mb-2">
                      ⚠️ {conflictosCancha.length} Solapamiento{conflictosCancha.length > 1 ? 's' : ''} de cancha
                    </h3>
                    <div className="space-y-2">
                      {conflictosCancha.map((c, idx) => (
                        <div key={idx} className="p-3 bg-background/80 rounded-lg border border-red-500/30">
                          <div className="font-medium text-textPrimary text-sm">{c.pareja1} vs {c.pareja2}</div>
                          <div className="text-red-400 text-xs mt-1 font-bold">
                            🕐 {c.fecha_hora} - {c.cancha} {c.categoria ? `(${c.categoria})` : ''}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Conflictos de descanso */}
            {!verificandoConflictos && conflictosDescanso.length > 0 && (
              <div className="p-4 bg-orange-500/10 border-2 border-orange-500/50 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-bold text-orange-500 mb-2">
                      ⏱️ {conflictosDescanso.length} Conflicto{conflictosDescanso.length > 1 ? 's' : ''} de descanso (&lt;3h)
                    </h3>
                    <div className="space-y-2">
                      {conflictosDescanso.map((c, idx) => (
                        <div key={idx} className="p-3 bg-background/80 rounded-lg border border-orange-500/30">
                          <div className="font-medium text-textPrimary text-sm">{c.pareja1} vs {c.pareja2}</div>
                          <div className="text-orange-400 text-xs mt-1 font-bold">
                            🕐 {c.fecha_hora} - {c.cancha} {c.categoria ? `(${c.categoria})` : ''}
                          </div>
                          <div className="text-orange-400 text-xs mt-0.5">{c.mensaje}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Sin conflictos */}
            {!verificandoConflictos && conflictos !== null && conflictos.length === 0 && fecha && hora && (
              <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-500 font-medium">✓ Horario disponible - Sin conflictos</span>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex gap-3 p-6 border-t border-borderColor">
            <Button variant="secondary" onClick={onClose} className="flex-1" disabled={loading}>
              Cancelar
            </Button>
            <Button variant="primary" onClick={handleCambiarHorario} className="flex-1"
              disabled={loading || !fecha || !hora || verificandoConflictos}>
              {loading ? 'Cambiando...' : 'Cambiar Horario'}
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
