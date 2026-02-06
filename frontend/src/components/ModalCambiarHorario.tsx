import { useState, useEffect } from 'react';
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
  const [conflictos, setConflictos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingCanchas, setLoadingCanchas] = useState(true);
  const [verificandoConflictos, setVerificandoConflictos] = useState(false);

  useEffect(() => {
    if (isOpen) {
      cargarCanchas();
      // Pre-llenar con datos actuales si existen
      if (partidoActual.fecha_hora) {
        // Usar el mismo parseo que en TorneoFixture para evitar problemas de zona horaria
        const fechaStr = partidoActual.fecha_hora;
        const fecha = new Date(fechaStr);
        const year = fecha.getUTCFullYear();
        const month = fecha.getUTCMonth();
        const day = fecha.getUTCDate();
        const hours = fecha.getUTCHours();
        const minutes = fecha.getUTCMinutes();
        const fechaLocal = new Date(year, month, day, hours, minutes);
        
        // Formatear para inputs
        const fechaISO = fechaLocal.toISOString().split('T')[0];
        const horaStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        
        setFecha(fechaISO);
        setHora(horaStr);
      }
      if (partidoActual.cancha_id) {
        setCanchaId(partidoActual.cancha_id);
      }
    }
  }, [isOpen, partidoActual]);

  // Verificar conflictos en tiempo real cuando cambian fecha, hora o cancha
  useEffect(() => {
    if (fecha && hora && canchaId && isOpen) {
      verificarConflictosPreview();
    } else {
      setConflictos([]);
    }
  }, [fecha, hora, canchaId, isOpen]);

  const verificarConflictosPreview = async () => {
    setVerificandoConflictos(true);
    try {
      const url = `${import.meta.env.VITE_API_URL}/torneos/${torneoId}/partidos/${partidoId}/cambiar-horario`;
      const token = localStorage.getItem('firebase_token');
      
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          fecha,
          hora,
          cancha_id: canchaId
        })
      });
      
      const data = await response.json();

      if (data.error === 'SOLAPAMIENTO_DETECTADO') {
        setConflictos(data.conflictos || []);
      } else {
        setConflictos([]);
      }
    } catch (error) {
      // Silenciar errores de preview
      setConflictos([]);
    } finally {
      setVerificandoConflictos(false);
    }
  };

  const cargarCanchas = async () => {
    try {
      setLoadingCanchas(true);
      const canchasData = await torneoService.listarCanchas(torneoId);
      // Filtrar solo canchas activas
      const canchasActivas = canchasData.filter((c: any) => c.activa);
      setCanchas(canchasActivas);
      if (canchasActivas.length > 0 && !canchaId) {
        setCanchaId(canchasActivas[0].id);
      }
    } catch (error) {
      console.error('Error al cargar canchas:', error);
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

    // Si hay conflictos, pedir confirmación
    if (conflictos.length > 0) {
      const confirmar = window.confirm(
        `⚠️ HAY ${conflictos.length} CONFLICTO(S)\n\n` +
        `El horario seleccionado se solapa con otros partidos en la misma cancha.\n\n` +
        `¿Estás seguro de que quieres continuar de todas formas?`
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
        body: JSON.stringify({
          fecha,
          hora,
          cancha_id: canchaId
        })
      });
      
      const data = await response.json();

      if (!response.ok) {
        toast.error(data.detail || `Error ${response.status}`);
        return;
      }

      if (data.success) {
        toast.success('✅ Horario actualizado correctamente');
        onSuccess();
        onClose();
      } else {
        toast.error(data.detail || data.message || 'Error al cambiar horario');
      }
    } catch (error: any) {
      console.error('Error al cambiar horario:', error);
      toast.error(`Error: ${error.message || 'Error de conexión'}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

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
            <button
              onClick={onClose}
              className="p-2 hover:bg-borderColor/50 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-textSecondary" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-4">
            {/* Fecha */}
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">
                Fecha
              </label>
              <input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-borderColor rounded-lg text-textPrimary focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>

            {/* Hora */}
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">
                Hora
              </label>
              <input
                type="time"
                value={hora}
                onChange={(e) => setHora(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-borderColor rounded-lg text-textPrimary focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>

            {/* Cancha */}
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">
                Cancha
              </label>
              {loadingCanchas ? (
                <div className="text-sm text-textSecondary">Cargando canchas...</div>
              ) : (
                <select
                  value={canchaId}
                  onChange={(e) => setCanchaId(Number(e.target.value))}
                  className="w-full px-4 py-2 bg-background border border-borderColor rounded-lg text-textPrimary focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  {canchas.map((cancha) => (
                    <option key={cancha.id} value={cancha.id}>
                      {cancha.nombre}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Conflictos en tiempo real */}
            {verificandoConflictos && (
              <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-blue-500">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  Verificando disponibilidad...
                </div>
              </div>
            )}

            {conflictos.length > 0 && !verificandoConflictos && (
              <div className="p-4 bg-red-500/10 border-2 border-red-500/50 rounded-lg animate-pulse">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-bold text-red-500 mb-2 text-lg">
                      ⚠️ {conflictos.length} Conflicto{conflictos.length > 1 ? 's' : ''} Detectado{conflictos.length > 1 ? 's' : ''}
                    </h3>
                    <p className="text-sm text-red-400 mb-3 font-medium">
                      Este horario se solapa con otros partidos en la misma cancha:
                    </p>
                    <div className="space-y-2">
                      {conflictos.map((conflicto, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-background/80 rounded-lg border border-red-500/30"
                        >
                          <div className="font-medium text-textPrimary text-sm">
                            {conflicto.pareja1} vs {conflicto.pareja2}
                          </div>
                          <div className="text-red-400 text-xs mt-1 font-bold">
                            🕐 {conflicto.fecha_hora} - {conflicto.cancha}
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-red-400 mt-3 font-medium">
                      💡 Selecciona otro horario o cancha para evitar solapamientos
                    </p>
                  </div>
                </div>
              </div>
            )}

            {!verificandoConflictos && conflictos.length === 0 && fecha && hora && (
              <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-500 font-medium">
                    ✓ Horario disponible - Sin conflictos
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex gap-3 p-6 border-t border-borderColor">
            <Button
              variant="secondary"
              onClick={onClose}
              className="flex-1"
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              onClick={handleCambiarHorario}
              className="flex-1"
              disabled={loading || !fecha || !hora}
            >
              {loading ? 'Cambiando...' : 'Cambiar Horario'}
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
