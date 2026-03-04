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
import { Plus, Settings, AlertCircle, RefreshCw, UserPlus } from 'lucide-react';
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

  // OPTIMIZACIÓN: Cargar salas con debounce
  const cargarSalasOptimizado = useCallback(async (forceRefresh: boolean = false) => {
    if (usuario && !loading) {
      try {
        setRefreshing(forceRefresh);
        await cargarSalas(forceRefresh);
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
      !mis.some(m => m.id === s.id)
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
    if (sala.estado === 'finalizada') {
      // Sala finalizada - solo mostrar resultados
      setModalMarcadorOpen(true);
    } else if (sala.estado === 'en_juego' || sala.estado === 'activa') {
      // Sala en juego - abrir marcador
      setModalMarcadorOpen(true);
    } else if (sala.estado === 'esperando' || sala.estado === 'programada') {
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
      {/* HEADER - Compacto y moderno */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col gap-3"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="h-1 w-8 md:w-12 bg-gradient-to-r from-primary to-secondary rounded-full" />
              <h1 className="text-2xl md:text-4xl font-black text-textPrimary tracking-tight">
                Salas
              </h1>
            </div>
            <p className="text-textSecondary text-sm ml-11 md:ml-15">Gestioná tus partidos de pádel</p>
          </div>
          
          {/* Botones principales destacados */}
          <div className="flex gap-2">
            <Button 
              variant="ghost" 
              onClick={() => setModalUnirseOpen(true)}
              className="flex items-center gap-2 px-4 md:px-6 py-3 text-sm md:text-base font-bold border-2 border-cardBorder hover:bg-primary/10 hover:border-primary transition-all"
            >
              <UserPlus size={18} />
              <span className="hidden sm:inline">Unirse por código</span>
              <span className="sm:hidden">Unirse</span>
            </Button>
            
            <Button 
              variant="primary" 
              onClick={() => setModalCrearOpen(true)}
              className="flex items-center gap-2 px-4 md:px-6 py-3 text-sm md:text-base font-bold shadow-lg shadow-primary/30 hover:shadow-xl hover:shadow-primary/40 transition-all"
            >
              <Plus size={20} />
              <span className="hidden sm:inline">Nueva Sala</span>
              <span className="sm:hidden">Crear</span>
            </Button>
          </div>
        </div>
        
        {/* Botones de acción - chips neutros */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="🔍 Buscar sala..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="w-full bg-cardBg border border-cardBorder rounded-lg px-3 py-2 text-sm text-textPrimary placeholder-textSecondary focus:border-primary focus:outline-none transition-colors"
            />
          </div>

          <button
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
            className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-all ${
              mostrarFiltros 
                ? 'bg-primary/10 border-primary text-primary' 
                : 'bg-transparent border-cardBorder text-textSecondary hover:border-primary hover:text-primary'
            }`}
          >
            <Settings size={16} />
            <span>Filtros</span>
          </button>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-cardBorder text-textSecondary hover:border-primary hover:text-primary transition-all disabled:opacity-50"
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            <span>Actualizar</span>
          </button>

          {/* Stats inline compactas */}
          <div className="hidden md:flex items-center gap-3 ml-auto text-xs text-textSecondary">
            <span className="flex items-center gap-1.5">
              <span className="font-bold text-textPrimary">{salas.length}</span> total
            </span>
            <span className="text-cardBorder">•</span>
            <span className="flex items-center gap-1.5">
              <span className="font-bold text-green-500">{salasActivas.length}</span> en juego
            </span>
            <span className="text-cardBorder">•</span>
            <span className="flex items-center gap-1.5">
              <span className="font-bold text-primary">{salasProgramadas.length}</span> programadas
            </span>
            <span className="text-cardBorder">•</span>
            <span className="flex items-center gap-1.5">
              <span className="font-bold text-textSecondary">{salasFinalizadas.length}</span> finalizadas
            </span>
          </div>
        </div>

        {/* Stats mobile - compactas */}
        <div className="grid grid-cols-4 gap-2 md:hidden">
          {[
            { label: 'Total', value: salas.length },
            { label: 'En juego', value: salasActivas.length },
            { label: 'Programadas', value: salasProgramadas.length },
            { label: 'Finalizadas', value: salasFinalizadas.length }
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-lg font-black text-textPrimary">{stat.value}</p>
              <p className="text-[10px] text-textSecondary uppercase">{stat.label}</p>
            </div>
          ))}
        </div>
      </motion.div>

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
        onCrearSala={() => setModalCrearOpen(true)}
      />

      {/* SECCIÓN 4 - HISTORIAL (ACORDEÓN VISIBLE) */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-cardBg rounded-xl border border-cardBorder overflow-hidden"
      >
        <button
          onClick={() => setHistorialColapsado(!historialColapsado)}
          className="w-full flex items-center justify-between p-4 hover:bg-cardBorder/30 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <span className={`transform transition-transform text-primary ${historialColapsado ? 'rotate-0' : 'rotate-90'}`}>
              ▸
            </span>
            <span className="font-bold text-lg text-textPrimary group-hover:text-primary transition-colors">
              Historial de Salas
            </span>
            <span className="px-2 py-0.5 bg-cardBorder rounded-full text-xs font-bold text-textSecondary">
              {salasHistorial.length}
            </span>
          </div>
          <span className="text-xs text-textSecondary">
            {historialColapsado ? 'Mostrar' : 'Ocultar'}
          </span>
        </button>
        
        {!historialColapsado && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-cardBorder"
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
      </motion.div>

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
