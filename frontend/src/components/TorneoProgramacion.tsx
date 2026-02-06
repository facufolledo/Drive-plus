import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Clock, MapPin, Plus, Trash2, Zap, AlertCircle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { torneoService } from '../services/torneo.service';
import Card from './Card';
import Button from './Button';
import SkeletonLoader from './SkeletonLoader';

interface TorneoProgramacionProps {
  torneoId: number;
  esOrganizador: boolean;
}

interface PartidoSinSlot {
  partido_id: number;
  pareja1_nombre?: string;
  pareja2_nombre?: string;
  razon?: string;
}

interface ResultadoProgramacion {
  programados: number;
  sin_programar: number;
  playoffs_pendientes?: number;
  partidos_sin_slot: PartidoSinSlot[];
  message: string;
}

interface Cancha {
  id: number;
  nombre: string;
  activa: boolean;
}

interface Slot {
  id: number;
  cancha_id: number;
  cancha_nombre?: string;
  fecha_hora_inicio: string;
  fecha_hora_fin: string;
  ocupado: boolean;
  partido_id?: number;
}

export default function TorneoProgramacion({ torneoId, esOrganizador }: TorneoProgramacionProps) {
  const [canchas, setCanchas] = useState<Cancha[]>([]);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);
  const [programando, setProgramando] = useState(false);
  const [error, setError] = useState('');
  
  // Modal crear cancha
  const [modalCanchaOpen, setModalCanchaOpen] = useState(false);
  const [nombreCancha, setNombreCancha] = useState('');
  
  // Programación automática
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [duracionPartido, setDuracionPartido] = useState(70);
  
  // Horarios por tipo de día
  const [horaInicioSemana, setHoraInicioSemana] = useState('17:00'); // Lun-Vie desde las 17
  const [horaFinSemana, setHoraFinSemana] = useState('22:00');
  const [horaInicioFinDeSemana, setHoraInicioFinDeSemana] = useState('09:00'); // Sab-Dom desde las 9
  const [horaFinFinDeSemana, setHoraFinFinDeSemana] = useState('21:00');
  
  // Modal resultado programación
  const [modalResultadoOpen, setModalResultadoOpen] = useState(false);
  const [resultadoProgramacion, setResultadoProgramacion] = useState<ResultadoProgramacion | null>(null);
  const [limpiando, setLimpiando] = useState(false);

  useEffect(() => {
    cargarDatos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [torneoId]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      setError('');
      const [canchasData, slotsData] = await Promise.all([
        torneoService.listarCanchas(torneoId),
        torneoService.listarSlots(torneoId)
      ]);
      
      // Asegurar que siempre sean arrays
      setCanchas(Array.isArray(canchasData) ? canchasData : []);
      setSlots(Array.isArray(slotsData) ? slotsData : []);
    } catch (error: any) {
      console.error('Error al cargar datos:', error);
      // Si es 404, probablemente no hay canchas aún
      if (error.response?.status === 404) {
        setCanchas([]);
        setSlots([]);
      } else {
        setError(error.response?.data?.detail || 'Error al cargar la programación');
      }
    } finally {
      setLoading(false);
    }
  };

  const crearCancha = async () => {
    if (!nombreCancha.trim()) {
      setError('El nombre de la cancha es requerido');
      return;
    }

    try {
      setError('');
      await torneoService.crearCancha(torneoId, { nombre: nombreCancha.trim(), activa: true });
      setNombreCancha('');
      setModalCanchaOpen(false);
      setError('');
      await cargarDatos();
    } catch (error: any) {
      console.error('Error al crear cancha:', error);
      setError(error.response?.data?.detail || error.message || 'Error al crear cancha');
    }
  };

  const eliminarCancha = async (canchaId: number) => {
    if (!confirm('¿Estás seguro de eliminar esta cancha? Se eliminarán todos los horarios asociados.')) return;

    try {
      setError('');
      await torneoService.eliminarCancha(torneoId, canchaId);
      await cargarDatos();
    } catch (error: any) {
      console.error('Error al eliminar cancha:', error);
      setError(error.response?.data?.detail || error.message || 'Error al eliminar cancha');
    }
  };

  const programarAutomaticamente = async () => {
    if (!fechaInicio || !fechaFin) {
      setError('Debes seleccionar las fechas de inicio y fin');
      return;
    }

    if (new Date(fechaInicio) > new Date(fechaFin)) {
      setError('La fecha de inicio debe ser anterior a la fecha de fin');
      return;
    }

    if (canchas.length === 0) {
      setError('Debes crear al menos una cancha antes de programar');
      return;
    }

    try {
      setProgramando(true);
      setError('');
      const resultado = await torneoService.programarPartidosAutomaticamente(torneoId, {
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        duracion_partido_minutos: duracionPartido,
        hora_inicio_semana: horaInicioSemana,
        hora_fin_semana: horaFinSemana,
        hora_inicio_finde: horaInicioFinDeSemana,
        hora_fin_finde: horaFinFinDeSemana
      });
      await cargarDatos();
      
      // Mostrar resultado en modal bonito
      setResultadoProgramacion({
        programados: resultado.programados || 0,
        sin_programar: resultado.sin_programar || 0,
        playoffs_pendientes: resultado.playoffs_pendientes || 0,
        partidos_sin_slot: resultado.partidos_sin_slot_detalle || [],
        message: resultado.message || 'Programación completada'
      });
      setModalResultadoOpen(true);
    } catch (error: any) {
      console.error('Error al programar:', error);
      setError(error.response?.data?.detail || error.message || 'Error al programar partidos');
    } finally {
      setProgramando(false);
    }
  };

  const limpiarProgramacion = async () => {
    if (!confirm('¿Estás seguro de limpiar toda la programación? Se eliminarán todos los horarios y los partidos quedarán sin fecha asignada.')) {
      return;
    }

    try {
      setLimpiando(true);
      setError('');
      const resultado = await torneoService.limpiarProgramacion(torneoId);
      await cargarDatos();
      alert(`✅ ${resultado.message}\n\nSlots eliminados: ${resultado.slots_eliminados}\nPartidos desprogramados: ${resultado.partidos_desprogramados}`);
    } catch (error: any) {
      console.error('Error al limpiar:', error);
      setError(error.response?.data?.detail || error.message || 'Error al limpiar programación');
    } finally {
      setLimpiando(false);
    }
  };

  const agruparSlotsPorFecha = () => {
    const grupos: { [fecha: string]: Slot[] } = {};
    slots.forEach(slot => {
      const fechaObj = new Date(slot.fecha_hora_inicio);
      const nombreDia = fechaObj.toLocaleDateString('es-ES', { weekday: 'long' });
      const fechaFormateada = fechaObj.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
      // Capitalizar primera letra del día
      const diaCapitalizado = nombreDia.charAt(0).toUpperCase() + nombreDia.slice(1);
      const fechaConDia = `${diaCapitalizado} ${fechaFormateada}`;
      if (!grupos[fechaConDia]) grupos[fechaConDia] = [];
      grupos[fechaConDia].push(slot);
    });
    return grupos;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <SkeletonLoader height="200px" />
        <SkeletonLoader height="400px" />
      </div>
    );
  }

  const slotsPorFecha = agruparSlotsPorFecha();

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-textPrimary">Programación de Partidos</h2>
          <p className="text-xs md:text-sm text-textSecondary">Gestiona canchas y horarios</p>
        </div>
        {esOrganizador && (
          <Button
            variant="accent"
            onClick={() => setModalCanchaOpen(true)}
            className="text-sm md:text-base"
          >
            <Plus size={16} className="mr-1.5 md:mr-2" />
            Nueva Cancha
          </Button>
        )}
      </div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg"
        >
          <AlertCircle size={18} className="text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-500">{error}</p>
        </motion.div>
      )}

      {/* Canchas */}
      <Card>
        <div className="p-4 md:p-6">
          <h3 className="text-lg md:text-xl font-bold text-textPrimary mb-3 md:mb-4 flex items-center gap-2">
            <MapPin size={20} className="text-primary" />
            Canchas Disponibles
          </h3>

          {canchas.length === 0 ? (
            <div className="text-center py-8 text-textSecondary">
              <MapPin size={40} className="mx-auto mb-3 opacity-50" />
              <p className="text-sm md:text-base">No hay canchas configuradas</p>
              {esOrganizador && (
                <Button
                  variant="primary"
                  onClick={() => setModalCanchaOpen(true)}
                  className="mt-4 text-sm"
                >
                  Crear Primera Cancha
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 md:gap-3">
              {canchas.map((cancha, idx) => (
                <motion.div
                  key={cancha.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="p-3 md:p-4 bg-background rounded-lg border border-cardBorder flex items-center justify-between"
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <div className={`w-2 h-2 rounded-full ${cancha.activa ? 'bg-green-500' : 'bg-gray-500'}`} />
                    <span className="font-bold text-textPrimary text-sm md:text-base truncate">{cancha.nombre}</span>
                  </div>
                  {esOrganizador && (
                    <button
                      onClick={() => eliminarCancha(cancha.id)}
                      className="text-textSecondary hover:text-red-500 transition-colors p-1"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </Card>

      {/* Programación Automática */}
      {esOrganizador && canchas.length > 0 && (
        <Card>
          <div className="p-4 md:p-6">
            <h3 className="text-lg md:text-xl font-bold text-textPrimary mb-3 md:mb-4 flex items-center gap-2">
              <Zap size={20} className="text-accent" />
              Programación Automática
            </h3>

            {/* Fechas y duración */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
              <div>
                <label className="block text-xs md:text-sm font-bold text-textSecondary mb-2">
                  Fecha Inicio
                </label>
                <input
                  type="date"
                  value={fechaInicio}
                  onChange={(e) => setFechaInicio(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-cardBorder rounded-lg text-textPrimary text-sm"
                />
              </div>

              <div>
                <label className="block text-xs md:text-sm font-bold text-textSecondary mb-2">
                  Fecha Fin
                </label>
                <input
                  type="date"
                  value={fechaFin}
                  onChange={(e) => setFechaFin(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-cardBorder rounded-lg text-textPrimary text-sm"
                />
              </div>

              <div>
                <label className="block text-xs md:text-sm font-bold text-textSecondary mb-2">
                  Duración partido (min)
                </label>
                <input
                  type="number"
                  value={duracionPartido}
                  onChange={(e) => setDuracionPartido(parseInt(e.target.value) || 90)}
                  min="30"
                  max="180"
                  step="15"
                  className="w-full px-3 py-2 bg-background border border-cardBorder rounded-lg text-textPrimary text-sm"
                />
              </div>
            </div>

            {/* Horarios Lunes a Viernes */}
            <div className="mb-4">
              <p className="text-xs md:text-sm font-bold text-textSecondary mb-2">
                🗓️ Horarios Lunes a Viernes
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-textSecondary mb-1">Desde</label>
                  <input
                    type="time"
                    value={horaInicioSemana}
                    onChange={(e) => setHoraInicioSemana(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-cardBorder rounded-lg text-textPrimary text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-textSecondary mb-1">Hasta</label>
                  <input
                    type="time"
                    value={horaFinSemana}
                    onChange={(e) => setHoraFinSemana(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-cardBorder rounded-lg text-textPrimary text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Horarios Sábado y Domingo */}
            <div className="mb-4">
              <p className="text-xs md:text-sm font-bold text-textSecondary mb-2">
                🌞 Horarios Sábado y Domingo
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-textSecondary mb-1">Desde</label>
                  <input
                    type="time"
                    value={horaInicioFinDeSemana}
                    onChange={(e) => setHoraInicioFinDeSemana(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-cardBorder rounded-lg text-textPrimary text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-textSecondary mb-1">Hasta</label>
                  <input
                    type="time"
                    value={horaFinFinDeSemana}
                    onChange={(e) => setHoraFinFinDeSemana(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-cardBorder rounded-lg text-textPrimary text-sm"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-2">
              <Button
                variant="accent"
                onClick={programarAutomaticamente}
                disabled={programando || limpiando || !fechaInicio || !fechaFin}
                className="flex-1 sm:flex-none text-sm md:text-base"
              >
                {programando ? (
                  <span className="flex items-center gap-2">
                    <Loader2 size={16} className="animate-spin" />
                    Programando...
                  </span>
                ) : (
                  <>
                    <Zap size={16} className="mr-1.5" />
                    Programar Automáticamente
                  </>
                )}
              </Button>
              
              {slots.length > 0 && (
                <Button
                  variant="ghost"
                  onClick={limpiarProgramacion}
                  disabled={programando || limpiando}
                  className="flex-1 sm:flex-none text-sm md:text-base text-red-500 hover:bg-red-500/10"
                >
                  {limpiando ? (
                    <span className="flex items-center gap-2">
                      <Loader2 size={16} className="animate-spin" />
                      Limpiando...
                    </span>
                  ) : (
                    <>
                      <Trash2 size={16} className="mr-1.5" />
                      Limpiar Programación
                    </>
                  )}
                </Button>
              )}
            </div>
            
            {programando && (
              <p className="text-xs text-textSecondary mt-2">
                Este proceso puede tardar algunos minutos dependiendo de la cantidad de partidos...
              </p>
            )}
          </div>
        </Card>
      )}

      {/* Programación por Fecha */}
      {Object.keys(slotsPorFecha).length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg md:text-xl font-bold text-textPrimary flex items-center gap-2">
            <Calendar size={20} className="text-primary" />
            Horarios Programados
          </h3>

          {Object.entries(slotsPorFecha).map(([fecha, slotsDelDia]) => (
            <Card key={fecha}>
              <div className="p-4 md:p-6">
                <h4 className="font-bold text-textPrimary mb-3 text-sm md:text-base">{fecha}</h4>
                <div className="space-y-2">
                  {slotsDelDia.map((slot, idx) => (
                    <motion.div
                      key={slot.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.03 }}
                      className={`p-2 md:p-3 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                        slot.ocupado
                          ? 'bg-green-500/10 border-green-500/30'
                          : 'bg-background border-cardBorder'
                      }`}
                    >
                      <div className="flex items-center gap-2 md:gap-3 flex-1 min-w-0">
                        <Clock size={14} className="text-textSecondary flex-shrink-0 md:w-4 md:h-4" />
                        <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 flex-1 min-w-0">
                          <span className="text-xs md:text-sm text-textPrimary font-medium whitespace-nowrap">
                            {new Date(slot.fecha_hora_inicio).toLocaleTimeString('es-ES', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                            {' - '}
                            {new Date(slot.fecha_hora_fin).toLocaleTimeString('es-ES', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                          <span className="text-xs md:text-sm text-textSecondary truncate">
                            {slot.cancha_nombre || `Cancha ${slot.cancha_id}`}
                          </span>
                        </div>
                      </div>
                      <span
                        className={`text-xs font-bold px-2 py-1 rounded-full whitespace-nowrap self-start sm:self-auto ${
                          slot.ocupado
                            ? 'bg-green-500/20 text-green-500'
                            : 'bg-gray-500/20 text-gray-500'
                        }`}
                      >
                        {slot.ocupado ? 'Ocupado' : 'Libre'}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Modal Crear Cancha */}
      {modalCanchaOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-3 md:p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-card rounded-xl max-w-md w-full p-4 md:p-6"
          >
            <h3 className="text-lg md:text-xl font-bold text-textPrimary mb-3 md:mb-4">Nueva Cancha</h3>

            <div className="mb-4">
              <label className="block text-xs md:text-sm font-bold text-textSecondary mb-2">
                Nombre de la Cancha *
              </label>
              <input
                type="text"
                value={nombreCancha}
                onChange={(e) => setNombreCancha(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    crearCancha();
                  }
                }}
                placeholder="Ej: Cancha 1"
                className="w-full px-3 md:px-4 py-2 md:py-3 bg-background border border-cardBorder rounded-lg text-textPrimary text-sm md:text-base focus:outline-none focus:border-primary"
                autoFocus
                maxLength={50}
              />
              <p className="text-xs text-textSecondary mt-1">
                {nombreCancha.length}/50 caracteres
              </p>
            </div>

            <div className="flex gap-2 md:gap-3">
              <Button
                variant="ghost"
                onClick={() => {
                  setModalCanchaOpen(false);
                  setNombreCancha('');
                  setError('');
                }}
                className="flex-1 text-sm md:text-base"
              >
                Cancelar
              </Button>
              <Button 
                variant="accent" 
                onClick={crearCancha} 
                className="flex-1 text-sm md:text-base"
                disabled={!nombreCancha.trim()}
              >
                Crear
              </Button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Modal Resultado Programación */}
      <AnimatePresence>
        {modalResultadoOpen && resultadoProgramacion && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-3 md:p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-card rounded-xl max-w-lg w-full p-4 md:p-6 max-h-[80vh] overflow-y-auto"
            >
              {/* Header con icono */}
              <div className="flex items-center gap-3 mb-4">
                {resultadoProgramacion.sin_programar === 0 ? (
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle size={24} className="text-green-500" />
                  </div>
                ) : (
                  <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center">
                    <AlertCircle size={24} className="text-yellow-500" />
                  </div>
                )}
                <div>
                  <h3 className="text-lg md:text-xl font-bold text-textPrimary">
                    Programación Completada
                  </h3>
                  <p className="text-sm text-textSecondary">
                    {resultadoProgramacion.message}
                  </p>
                </div>
              </div>

              {/* Estadísticas */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-center">
                  <p className="text-2xl font-bold text-green-500">
                    {resultadoProgramacion.programados}
                  </p>
                  <p className="text-xs text-textSecondary">Partidos programados</p>
                </div>
                <div className={`p-3 rounded-lg text-center ${
                  resultadoProgramacion.sin_programar > 0 
                    ? 'bg-yellow-500/10 border border-yellow-500/30' 
                    : 'bg-gray-500/10 border border-gray-500/30'
                }`}>
                  <p className={`text-2xl font-bold ${
                    resultadoProgramacion.sin_programar > 0 ? 'text-yellow-500' : 'text-gray-500'
                  }`}>
                    {resultadoProgramacion.sin_programar}
                  </p>
                  <p className="text-xs text-textSecondary">Sin slot disponible</p>
                </div>
              </div>

              {/* Info de playoffs pendientes */}
              {resultadoProgramacion.playoffs_pendientes && resultadoProgramacion.playoffs_pendientes > 0 && (
                <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <p className="text-sm text-blue-400">
                    ℹ️ {resultadoProgramacion.playoffs_pendientes} partidos de playoffs esperan que se definan los clasificados de cada zona
                  </p>
                </div>
              )}

              {/* Detalle de partidos sin slot */}
              {resultadoProgramacion.sin_programar > 0 && resultadoProgramacion.partidos_sin_slot.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-bold text-textPrimary mb-2 flex items-center gap-2">
                    <XCircle size={16} className="text-yellow-500" />
                    Partidos sin programar
                  </h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {resultadoProgramacion.partidos_sin_slot.map((partido, idx) => (
                      <div 
                        key={partido.partido_id || idx}
                        className="p-2 bg-yellow-500/5 border border-yellow-500/20 rounded-lg text-sm"
                      >
                        <p className="font-medium text-textPrimary">
                          {partido.pareja1_nombre || 'Pareja 1'} vs {partido.pareja2_nombre || 'Pareja 2'}
                        </p>
                        {partido.razon && (
                          <p className="text-xs text-yellow-500 mt-1">
                            {partido.razon}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-textSecondary mt-2">
                    💡 Tip: Agrega más slots de horarios o revisa los bloqueos de los jugadores
                  </p>
                </div>
              )}

              {/* Botón cerrar */}
              <Button
                variant="primary"
                onClick={() => setModalResultadoOpen(false)}
                className="w-full"
              >
                Entendido
              </Button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
