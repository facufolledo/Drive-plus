import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import Button from '../components/Button';
import ModalCrearSala from '../components/ModalCrearSala';
import ModalUnirseSala from '../components/ModalUnirseSala';
import SalaEspera from '../components/SalaEspera';
import MarcadorPadel from '../components/MarcadorPadel';
import ModalConfirmarResultado from '../components/ModalConfirmarResultado';
import MisSalasSection from '../components/salas/MisSalasSection';
import SalasEnJuegoSection from '../components/salas/SalasEnJuegoSection';
import ExplorarSalasTable from '../components/salas/ExplorarSalasTable';
import { SalasDebug } from '../components/SalasDebug';
import { Plus, Settings, AlertCircle, RefreshCw } from 'lucide-react';
import { useSalas } from '../context/SalasContext';
import { useAuth } from '../context/AuthContext';
import { Sala } from '../utils/types';

export default function Salas() {
  const { salas, getSalasPendientesConfirmacion, cargarSalas, loading } = useSalas();
  const { usuario } = useAuth();
  const [codigoUrl, setCodigoUrl] = useState<string | null>(null);
  const [modalCrearOpen, setModalCrearOpen] = useState(false);
  const [modalUnirseOpen, setModalUnirseOpen] = useState(false);
  const [modalEsperaOpen, setModalEsperaOpen] = useState(false);
  const [modalMarcadorOpen, setModalMarcadorOpen] = useState(false);
  const [modalConfirmarOpen, setModalConfirmarOpen] = useState(false);
  const [salaSeleccionada, setSalaSeleccionada] = useState<Sala | null>(null);
  const [busqueda, setBusqueda] = useState('');
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [historialColapsado, setHistorialColapsado] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // OPTIMIZACIÓN: Cargar salas con debounce
  const cargarSalasOptimizado = useCallback(async (forceRefresh: boolean = false) => {
    if (usuario && !loading) {
      try {
        setRefreshing(forceRefresh);
        await cargarSalas(forceRefresh);
        setLastRefresh(new Date());
      } catch (error) {
        console.error('Error al cargar salas:', error);
      } finally {
        setRefreshing(false);
      }
    }
  }, [usuario, loading, cargarSalas]);

  // Cargar salas inicial y verificar código en URL
  useEffect(() => {
    // Verificar código en URL
    const params = new URLSearchParams(window.location.search);
    const codigo = params.get('codigo');
    if (codigo) {
      setCodigoUrl(codigo);
      setModalUnirseOpen(true);
      window.history.replaceState({}, '', '/salas');
    }

    // Cargar salas inicial
    if (usuario) {
      cargarSalas(false);
      setLastRefresh(new Date());
    }
  }, [usuario, cargarSalas]);

  // Auto-refresh cada 30 segundos solo si la página está visible
  useEffect(() => {
    if (!usuario) return;

    let intervalId: NodeJS.Timeout;
    
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // Configurar auto-refresh
        intervalId = setInterval(() => {
          cargarSalas(false);
          setLastRefresh(new Date());
        }, 30000); // 30 segundos
      } else {
        // Limpiar interval cuando la página no es visible
        if (intervalId) {
          clearInterval(intervalId);
        }
      }
    };

    // Configurar listener
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Iniciar interval si la página ya es visible
    if (document.visibilityState === 'visible') {
      intervalId = setInterval(() => {
        cargarSalas(false);
        setLastRefresh(new Date());
      }, 30000);
    }

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [usuario, cargarSalas]);

  // OPTIMIZACIÓN: Memoizar cálculos pesados
  const salasPendientes = useMemo(() => {
    return usuario ? getSalasPendientesConfirmacion(usuario.id_usuario?.toString() || '') : [];
  }, [usuario, getSalasPendientesConfirmacion]);

  // OPTIMIZACIÓN: Memoizar separación de salas
  const { misSalas, salasEnJuego } = useMemo(() => {
    const userId = usuario?.id_usuario?.toString();
    const mis = salas.filter(s => s.jugadores?.some(j => j.id === userId));
    const enJuego = salas.filter(s => 
      (s.estado === 'activa' || s.estado === 'en_juego') && 
      !mis.some(m => m.id_sala === s.id_sala)
    );
    
    return { misSalas: mis, salasEnJuego: enJuego };
  }, [salas, usuario]);

  // OPTIMIZACIÓN: Función de refresh manual
  const handleRefresh = useCallback(async () => {
    await cargarSalasOptimizado(true);
  }, [cargarSalasOptimizado]);
  const salasExplorar = salas.filter(s => !misSalas.includes(s) && !salasEnJuego.includes(s));
  const salasHistorial = salas.filter(s => s.estado === 'finalizada');

  const salasActivas = salas.filter(s => s.estado === 'activa' || s.estado === 'en_juego');
  const salasProgramadas = salas.filter(s => s.estado === 'programada');
  const salasFinalizadas = salas.filter(s => s.estado === 'finalizada');

  const handleOpenMarcador = (sala: Sala) => {
    setSalaSeleccionada(sala);
    
    console.log('🔍 Abriendo sala:', {
      id: sala.id,
      estado: sala.estado,
      nombre: sala.nombre,
      jugadores: sala.jugadores?.length || 0
    });
    
    // Lógica mejorada basada en el estado real de la sala
    if (sala.estado === 'finalizada' || sala.estado === 'terminada' || sala.estado === 'completada') {
      // Sala finalizada - solo mostrar resultados
      setModalMarcadorOpen(true);
    } else if (sala.estado === 'en_juego' || sala.estado === 'activa' || sala.estado === 'jugando') {
      // Sala en juego - abrir marcador
      setModalMarcadorOpen(true);
    } else if (sala.estado === 'esperando' || sala.estado === 'pendiente') {
      // Sala esperando - abrir sala de espera
      setModalEsperaOpen(true);
    } else {
      // Estado desconocido - abrir sala de espera por defecto
      console.warn('⚠️ Estado de sala desconocido:', sala.estado);
      setModalEsperaOpen(true);
    }
  };

  const handleIniciarPartido = () => {
    setModalEsperaOpen(false);
    setModalMarcadorOpen(true);
  };

  return (
    <div className="w-full min-w-0 space-y-6">
      {/* HEADER - Optimizado para móvil */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col gap-4"
      >
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="h-1 w-8 md:w-12 bg-gradient-to-r from-primary to-secondary rounded-full" />
            <h1 className="text-2xl md:text-4xl font-black text-textPrimary tracking-tight">
              Salas
            </h1>
          </div>
          <p className="text-textSecondary text-sm md:text-base ml-11 md:ml-15">Gestioná tus partidos de pádel</p>
        </div>
        
        {/* Botones reorganizados para móvil */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <Button 
            variant="primary" 
            onClick={() => setModalCrearOpen(true)}
            className="flex items-center justify-center gap-2 px-4 py-3 text-sm font-bold"
          >
            <Plus size={16} />
            Nueva Sala
          </Button>
          
          <div className="flex gap-2">
            <div className="flex-1 sm:flex-none">
              <input
                type="text"
                placeholder="🔍 Buscar"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                className="w-full sm:w-48 bg-cardBg border border-cardBorder rounded-lg px-3 py-2.5 text-sm text-textPrimary placeholder-textSecondary focus:border-primary focus:outline-none"
              />
            </div>
            
            <Button 
              variant="secondary"
              onClick={() => setMostrarFiltros(!mostrarFiltros)}
              className="flex items-center gap-2 px-3 py-2.5 text-sm"
            >
              <Settings size={16} />
              <span className="hidden sm:inline">Filtros</span>
            </Button>

            {/* OPTIMIZACIÓN: Botón de refresh */}
            <Button 
              variant="outline" 
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-3 py-2.5 text-sm"
            >
              <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">{refreshing ? 'Actualizando...' : 'Actualizar'}</span>
            </Button>
          </div>
        </div>

        {/* OPTIMIZACIÓN: Indicador de estado */}
        <div className="flex items-center gap-2 text-xs text-textSecondary">
          <div className={`w-2 h-2 rounded-full ${loading || refreshing ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`} />
          <span>
            {loading || refreshing 
              ? 'Actualizando salas...' 
              : `Última actualización: ${lastRefresh.toLocaleTimeString()}`
            }
          </span>
        </div>
      </motion.div>

      {/* KPIs - Optimizados para móvil */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
        {[
          { label: 'TOTAL', value: salas.length, color: 'from-cyan-500 to-blue-500' },
          { label: 'EN JUEGO', value: salasActivas.length, color: 'from-green-500 to-emerald-500' },
          { label: 'PROGRAMADAS', value: salasProgramadas.length, color: 'from-primary to-blue-500' },
          { label: 'FINALIZADAS', value: salasFinalizadas.length, color: 'from-gray-500 to-gray-400' }
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className="bg-cardBg rounded-lg p-3 md:p-4 border border-cardBorder text-center"
          >
            <p className="text-xl md:text-2xl font-black text-textPrimary mb-1">{stat.value}</p>
            <p className="text-textSecondary text-[10px] md:text-xs font-bold uppercase tracking-wider leading-tight">
              {stat.label}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Alerta de confirmaciones pendientes - Optimizada para móvil */}
      {salasPendientes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-accent/10 border border-accent/30 rounded-lg p-3 md:p-4"
        >
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <AlertCircle size={18} className="text-accent flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-accent font-bold text-sm md:text-base">
                Tienes {salasPendientes.length} {salasPendientes.length === 1 ? 'partido pendiente' : 'partidos pendientes'} de confirmación
              </p>
              <p className="text-textSecondary text-xs md:text-sm">
                Confirma los resultados para que sean oficiales
              </p>
            </div>
            <Button
              variant="accent"
              onClick={() => {
                setSalaSeleccionada(salasPendientes[0]);
                setModalMarcadorOpen(true);
              }}
              className="text-xs md:text-sm px-3 md:px-4 py-2 w-full sm:w-auto"
            >
              Confirmar Ahora
            </Button>
          </div>
        </motion.div>
      )}

      {/* Debug Component - Solo en desarrollo */}
      <SalasDebug salas={salas} usuario={usuario} />

      {/* SECCIÓN 1 - MIS SALAS (PRIORIDAD MÁXIMA) */}
      <MisSalasSection 
        salas={misSalas}
        onEntrarSala={(salaId) => {
          const sala = salas.find(s => s.id === salaId.toString());
          if (sala) handleOpenMarcador(sala);
        }}
        onVerPartido={(salaId) => {
          const sala = salas.find(s => s.id === salaId.toString());
          if (sala) handleOpenMarcador(sala);
        }}
        loading={loading}
      />

      {/* SECCIÓN 2 - SALAS EN JUEGO / HOY */}
      <SalasEnJuegoSection 
        salas={salasEnJuego}
        onVerSala={(salaId) => {
          const sala = salas.find(s => s.id === salaId.toString());
          if (sala) handleOpenMarcador(sala);
        }}
        loading={loading}
      />

      {/* SECCIÓN 3 - EXPLORAR SALAS (TABLA ESCALABLE) */}
      <ExplorarSalasTable 
        salas={salasExplorar}
        onUnirseSala={(salaId) => {
          const sala = salas.find(s => s.id === salaId.toString());
          if (sala) handleOpenMarcador(sala);
        }}
        onVerSala={(salaId) => {
          const sala = salas.find(s => s.id === salaId.toString());
          if (sala) handleOpenMarcador(sala);
        }}
        busqueda={busqueda}
        loading={loading}
      />

      {/* SECCIÓN 4 - HISTORIAL (COLAPSADO) */}
      <div className="space-y-3">
        <button
          onClick={() => setHistorialColapsado(!historialColapsado)}
          className="flex items-center gap-2 text-textPrimary hover:text-primary transition-colors"
        >
          <span className={`transform transition-transform ${historialColapsado ? 'rotate-0' : 'rotate-90'}`}>
            ▸
          </span>
          <span className="font-bold">Historial de Salas ({salasHistorial.length})</span>
        </button>
        
        {!historialColapsado && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <ExplorarSalasTable 
              salas={salasHistorial}
              onUnirseSala={() => {}}
              onVerSala={(salaId) => {
                const sala = salas.find(s => s.id === salaId.toString());
                if (sala) handleOpenMarcador(sala);
              }}
              busqueda={busqueda}
              loading={loading}
              soloLectura={true}
            />
          </motion.div>
        )}
      </div>

      {/* Modales */}
      <ModalCrearSala isOpen={modalCrearOpen} onClose={() => setModalCrearOpen(false)} />
      <ModalUnirseSala 
        isOpen={modalUnirseOpen} 
        onClose={() => {
          setModalUnirseOpen(false);
          setCodigoUrl(null);
        }} 
        codigoInicial={codigoUrl || undefined}
      />
      <SalaEspera
        isOpen={modalEsperaOpen}
        onClose={() => {
          setModalEsperaOpen(false);
          setSalaSeleccionada(null);
        }}
        sala={salaSeleccionada}
        onIniciarPartido={handleIniciarPartido}
      />
      <MarcadorPadel
        isOpen={modalMarcadorOpen}
        onClose={() => {
          setModalMarcadorOpen(false);
          setSalaSeleccionada(null);
        }}
        sala={salaSeleccionada}
      />
      <ModalConfirmarResultado
        isOpen={modalConfirmarOpen}
        onClose={() => {
          setModalConfirmarOpen(false);
          setSalaSeleccionada(null);
        }}
        sala={salaSeleccionada}
      />
    </div>
  );
}
