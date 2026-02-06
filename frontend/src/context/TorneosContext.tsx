import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Torneo } from '../utils/types';
import torneoService, { TorneoCreate, ParejaInscripcion, Pareja } from '../services/torneo.service';
import { useAuth } from './AuthContext';

interface MiTorneo {
  id: number;
  nombre: string;
  estado: string;
  estado_inscripcion: string;
  fecha_inicio: string;
  fecha_fin: string;
}

interface TorneosContextType {
  // Estado
  torneos: Torneo[];
  torneoActual: Torneo | null;
  parejas: Pareja[];
  misTorneos: MiTorneo[];
  loading: boolean;
  error: string | null;
  
  // Acciones de torneos
  cargarTorneos: () => Promise<void>;
  cargarTorneo: (id: number) => Promise<void>;
  cargarMisTorneos: () => Promise<void>;
  crearTorneo: (data: TorneoCreate) => Promise<Torneo>;
  actualizarTorneo: (id: number, data: Partial<TorneoCreate>) => Promise<void>;
  eliminarTorneo: (id: number) => Promise<void>;
  cambiarEstadoTorneo: (id: number, estado: string) => Promise<void>;
  
  // Acciones de inscripciones
  cargarParejas: (torneoId: number) => Promise<void>;
  inscribirPareja: (torneoId: number, data: ParejaInscripcion) => Promise<void>;
  confirmarPareja: (torneoId: number, parejaId: number) => Promise<void>;
  rechazarPareja: (torneoId: number, parejaId: number, motivo?: string) => Promise<void>;
  darBajaPareja: (torneoId: number, parejaId: number, motivo?: string) => Promise<void>;
  
  // Permisos
  puedeCrearTorneos: boolean;
  esAdministrador: boolean;
  
  // Utilidades
  limpiarError: () => void;
}

const TorneosContext = createContext<TorneosContextType | undefined>(undefined);

export function TorneosProvider({ children }: { children: ReactNode }) {
  const [torneos, setTorneos] = useState<Torneo[]>([]);
  const [torneoActual, setTorneoActual] = useState<Torneo | null>(null);
  const [parejas, setParejas] = useState<Pareja[]>([]);
  const [misTorneos, setMisTorneos] = useState<MiTorneo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { usuario } = useAuth();
  
  // Permisos
  const puedeCrearTorneos = usuario?.puede_crear_torneos || false;
  const esAdministrador = usuario?.es_administrador || false;

  // ============================================
  // FUNCIONES AUXILIARES
  // ============================================
  
  const adaptarTorneoBackendAFrontend = (torneoBackend: any): Torneo | null => {
    // Validar que el torneo tenga un ID válido
    if (!torneoBackend.id || isNaN(Number(torneoBackend.id))) {
      console.error('Torneo sin ID válido:', torneoBackend);
      return null;
    }
    
    return {
      id: torneoBackend.id?.toString() || '0',
      nombre: torneoBackend.nombre || '',
      descripcion: torneoBackend.descripcion || '',
      categoria: torneoBackend.categoria || '',
      estado: mapearEstadoBackendAFrontend(torneoBackend.estado),
      fechaInicio: torneoBackend.fecha_inicio || '',
      fechaFin: torneoBackend.fecha_fin || '',
      lugar: torneoBackend.lugar || torneoBackend.ubicacion || '',
      genero: torneoBackend.genero || 'masculino',
      formato: torneoBackend.formato || torneoBackend.tipo || 'grupos',
      participantes: torneoBackend.parejas_inscritas || torneoBackend.total_parejas || 0,
      salasIds: torneoBackend.salasIds || [],
      createdAt: torneoBackend.created_at || '',
      // Guardar estado original y creador para verificaciones
      estado_original: torneoBackend.estado,
      creado_por: torneoBackend.creado_por,
      horarios_disponibles: torneoBackend.horarios_disponibles,
    } as Torneo;
  };
  
  const mapearEstadoBackendAFrontend = (estadoBackend: string): 'programado' | 'activo' | 'finalizado' => {
    const estado = estadoBackend?.toLowerCase() || '';
    switch (estado) {
      case 'inscripcion':
      case 'armando_zonas':
        return 'programado';
      case 'fase_grupos':
      case 'fase_eliminacion':
        return 'activo';
      case 'finalizado':
        return 'finalizado';
      default:
        return 'programado';
    }
  };
  
  // ============================================
  // ACCIONES DE TORNEOS
  // ============================================
  
  const cargarTorneos = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const torneosData = await torneoService.listarTorneos();
      const torneosAdaptados = torneosData
        .map(adaptarTorneoBackendAFrontend)
        .filter((t): t is Torneo => t !== null); // Filtrar torneos inválidos
      setTorneos(torneosAdaptados);
    } catch (err: any) {
      console.error('Error al cargar torneos:', err);
      setError(err.response?.data?.detail || 'Error al cargar torneos');
    } finally {
      setLoading(false);
    }
  };
  
  const cargarTorneo = async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      
      const torneo = await torneoService.obtenerTorneo(id);
      const torneoAdaptado = adaptarTorneoBackendAFrontend(torneo);
      setTorneoActual(torneoAdaptado);
    } catch (err: any) {
      console.error('Error al cargar torneo:', err);
      setError(err.response?.data?.detail || 'Error al cargar torneo');
    } finally {
      setLoading(false);
    }
  };

  const cargarMisTorneos = async () => {
    if (!usuario) return;
    
    try {
      const data = await torneoService.obtenerMisTorneos();
      const adaptados = data.torneos.map(t => ({
        id: t.id,
        nombre: t.nombre,
        estado: t.estado,
        estado_inscripcion: t.mi_inscripcion?.estado_inscripcion || 'inscripta',
        fecha_inicio: t.fecha_inicio,
        fecha_fin: t.fecha_fin
      }));
      setMisTorneos(adaptados);
    } catch (err: any) {
      console.error('Error al cargar mis torneos:', err);
    }
  };
  
  const crearTorneo = async (data: TorneoCreate): Promise<Torneo> => {
    try {
      setLoading(true);
      setError(null);
      
      // Validar datos
      const errores = torneoService.validarDatosTorneo(data);
      if (errores.length > 0) {
        throw new Error(errores.join(', '));
      }
      
      const nuevoTorneo = await torneoService.crearTorneo(data);
      const torneoAdaptado = adaptarTorneoBackendAFrontend(nuevoTorneo);
      
      // Actualizar lista local
      setTorneos(prev => [torneoAdaptado, ...prev]);
      
      return torneoAdaptado;
    } catch (err: any) {
      console.error('Error al crear torneo:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Error al crear torneo';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };
  
  const actualizarTorneo = async (id: number, data: Partial<TorneoCreate>) => {
    try {
      setLoading(true);
      setError(null);
      
      const torneoActualizado = await torneoService.actualizarTorneo(id, data);
      const torneoAdaptado = adaptarTorneoBackendAFrontend(torneoActualizado);
      
      // Actualizar lista local
      setTorneos(prev => prev.map(t => 
        parseInt(t.id) === id ? torneoAdaptado : t
      ));
      
      // Actualizar torneo actual si es el mismo
      if (torneoActual && parseInt(torneoActual.id) === id) {
        setTorneoActual(torneoAdaptado);
      }
    } catch (err: any) {
      console.error('Error al actualizar torneo:', err);
      setError(err.response?.data?.detail || 'Error al actualizar torneo');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const eliminarTorneo = async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      
      await torneoService.eliminarTorneo(id);
      
      // Actualizar lista local
      setTorneos(prev => prev.filter(t => parseInt(t.id) !== id));
      
      // Limpiar torneo actual si es el mismo
      if (torneoActual && parseInt(torneoActual.id) === id) {
        setTorneoActual(null);
      }
    } catch (err: any) {
      console.error('Error al eliminar torneo:', err);
      setError(err.response?.data?.detail || 'Error al eliminar torneo');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const cambiarEstadoTorneo = async (id: number, estado: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const torneoActualizado = await torneoService.cambiarEstado(id, estado);
      const torneoAdaptado = adaptarTorneoBackendAFrontend(torneoActualizado);
      
      // Actualizar lista local
      setTorneos(prev => prev.map(t => 
        parseInt(t.id) === id ? torneoAdaptado : t
      ));
      
      // Actualizar torneo actual si es el mismo
      if (torneoActual && parseInt(torneoActual.id) === id) {
        setTorneoActual(torneoAdaptado);
      }
    } catch (err: any) {
      console.error('Error al cambiar estado:', err);
      setError(err.response?.data?.detail || 'Error al cambiar estado');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // ============================================
  // ACCIONES DE INSCRIPCIONES
  // ============================================
  
  const cargarParejas = async (torneoId: number) => {
    try {
      setLoading(true);
      setError(null);
      
      const parejasData = await torneoService.listarParejas(torneoId);
      console.log('🔍 CONTEXT - Guardando parejas en estado (primeras 2):', parejasData.slice(0, 2));
      setParejas(parejasData);
    } catch (err: any) {
      console.error('Error al cargar parejas:', err);
      setError(err.response?.data?.detail || 'Error al cargar parejas');
    } finally {
      setLoading(false);
    }
  };
  
  const inscribirPareja = async (torneoId: number, data: ParejaInscripcion) => {
    try {
      setLoading(true);
      setError(null);
      
      // Validar datos
      const errores = torneoService.validarInscripcionPareja(data);
      if (errores.length > 0) {
        throw new Error(errores.join(', '));
      }
      
      // inscribirPareja ahora devuelve código de confirmación, no la pareja
      await torneoService.inscribirPareja(torneoId, data);
      
      // Recargar parejas para obtener la nueva
      await cargarParejas(torneoId);
      // También recargar mis torneos
      await cargarMisTorneos();
    } catch (err: any) {
      console.error('Error al inscribir pareja:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Error al inscribir pareja';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };
  
  const confirmarPareja = async (torneoId: number, parejaId: number) => {
    try {
      setLoading(true);
      setError(null);
      
      const parejaConfirmada = await torneoService.confirmarPareja(torneoId, parejaId);
      
      // Actualizar lista local
      setParejas(prev => prev.map(p => 
        p.id === parejaId ? parejaConfirmada : p
      ));
    } catch (err: any) {
      console.error('Error al confirmar pareja:', err);
      setError(err.response?.data?.detail || 'Error al confirmar pareja');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const rechazarPareja = async (torneoId: number, parejaId: number, motivo?: string) => {
    try {
      setLoading(true);
      setError(null);
      
      await torneoService.rechazarPareja(torneoId, parejaId, motivo);
      
      // Remover de lista local
      setParejas(prev => prev.filter(p => p.id !== parejaId));
    } catch (err: any) {
      console.error('Error al rechazar pareja:', err);
      setError(err.response?.data?.detail || 'Error al rechazar pareja');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const darBajaPareja = async (torneoId: number, parejaId: number, motivo?: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const parejaBaja = await torneoService.darBajaPareja(torneoId, parejaId, motivo);
      
      // Actualizar lista local
      setParejas(prev => prev.map(p => 
        p.id === parejaId ? parejaBaja : p
      ));
    } catch (err: any) {
      console.error('Error al dar de baja pareja:', err);
      setError(err.response?.data?.detail || 'Error al dar de baja pareja');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // ============================================
  // UTILIDADES
  // ============================================
  
  const limpiarError = () => {
    setError(null);
  };
  
  // Cargar torneos al montar el componente
  useEffect(() => {
    cargarTorneos();
  }, []);

  // Cargar mis torneos cuando hay usuario
  useEffect(() => {
    if (usuario) {
      cargarMisTorneos();
    }
  }, [usuario]);

  return (
    <TorneosContext.Provider value={{
      // Estado
      torneos,
      torneoActual,
      parejas,
      misTorneos,
      loading,
      error,
      
      // Acciones de torneos
      cargarTorneos,
      cargarTorneo,
      cargarMisTorneos,
      crearTorneo,
      actualizarTorneo,
      eliminarTorneo,
      cambiarEstadoTorneo,
      
      // Acciones de inscripciones
      cargarParejas,
      inscribirPareja,
      confirmarPareja,
      rechazarPareja,
      darBajaPareja,
      
      // Permisos
      puedeCrearTorneos,
      esAdministrador,
      
      // Utilidades
      limpiarError
    }}>
      {children}
    </TorneosContext.Provider>
  );
}

export function useTorneos() {
  const context = useContext(TorneosContext);
  if (!context) {
    throw new Error('useTorneos debe usarse dentro de TorneosProvider');
  }
  return context;
}
