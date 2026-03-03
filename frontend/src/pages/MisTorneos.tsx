import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Calendar, Users, MapPin, Clock, Award, TrendingUp, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';
import TorneoCard from '../components/TorneoCard';
import { useAuth } from '../context/AuthContext';

interface Torneo {
  id: number;
  nombre: string;
  descripcion: string;
  fecha_inicio: string;
  fecha_fin: string;
  ubicacion: string;
  categoria: string;
  tipo: 'eliminacion_simple' | 'eliminacion_doble' | 'round_robin';
  max_equipos: number;
  equipos_inscritos: number;
  estado: 'inscripcion' | 'en_curso' | 'finalizado';
  premio?: string;
  imagen?: string;
  mi_estado?: 'inscrito' | 'en_progreso' | 'eliminado' | 'finalista' | 'campeon';
  mi_posicion?: number;
  proxima_fecha?: string;
}

export default function MisTorneos() {
  const navigate = useNavigate();
  const { usuario } = useAuth();
  const [torneosCreados, setTorneosCreados] = useState<Torneo[]>([]);
  const [torneosInscrito, setTorneosInscrito] = useState<Torneo[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activos' | 'finalizados'>('activos');
  const [mostrarTodosCreados, setMostrarTodosCreados] = useState(false);
  const [mostrarTodosInscrito, setMostrarTodosInscrito] = useState(false);
  const ITEMS_POR_PAGINA = 6;

  // Helper para parsear fechas sin problemas de zona horaria
  const parseFechaSinZonaHoraria = (fechaISO: string): Date => {
    const [year, month, day] = fechaISO.split('-').map(Number);
    return new Date(year, month - 1, day);
  };

  useEffect(() => {
    cargarMisTorneos();
  }, []);

  const cargarMisTorneos = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('firebase_token');
      if (!token) {
        setTorneosCreados([]);
        setTorneosInscrito([]);
        return;
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/torneos/mis-torneos`, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar torneos');
      }
      
      const data = await response.json();
      // Manejar nueva estructura con dos arrays separados
      setTorneosCreados(Array.isArray(data.torneos_creados) ? data.torneos_creados : []);
      setTorneosInscrito(Array.isArray(data.torneos_inscrito) ? data.torneos_inscrito : []);
    } catch (error) {
      console.error('Error al cargar torneos:', error);
      setTorneosCreados([]);
      setTorneosInscrito([]);
    } finally {
      setLoading(false);
    }
  };

  // Combinar ambos arrays para filtros y estadísticas
  const todosLosTorneos = [...torneosCreados, ...torneosInscrito];

  const torneosCreadosFiltrados = torneosCreados.filter(t => {
    if (filtroEstado === 'activos') return t.estado !== 'finalizado';
    if (filtroEstado === 'finalizados') return t.estado === 'finalizado';
    return true;
  });

  const torneosInscritoFiltrados = torneosInscrito.filter(t => {
    if (filtroEstado === 'activos') return t.estado !== 'finalizado';
    if (filtroEstado === 'finalizados') return t.estado === 'finalizado';
    return true;
  });

  const torneosCreadosMostrados = mostrarTodosCreados ? torneosCreadosFiltrados : torneosCreadosFiltrados.slice(0, ITEMS_POR_PAGINA);
  const torneosInscritoMostrados = mostrarTodosInscrito ? torneosInscritoFiltrados : torneosInscritoFiltrados.slice(0, ITEMS_POR_PAGINA);

  const estadisticas = {
    total: todosLosTorneos.length,
    activos: todosLosTorneos.filter(t => t.estado !== 'finalizado').length,
    finalizados: todosLosTorneos.filter(t => t.estado === 'finalizado').length,
    campeonatos: todosLosTorneos.filter(t => t.mi_estado === 'campeon').length
  };

  const getEstadoBadge = (torneo: Torneo) => {
    const badges = {
      inscrito: { text: 'Inscrito', color: 'bg-blue-500/20 text-blue-400 border-blue-500/50' },
      en_progreso: { text: 'En Progreso', color: 'bg-accent/20 text-accent border-accent/50' },
      eliminado: { text: 'Eliminado', color: 'bg-red-500/20 text-red-400 border-red-500/50' },
      finalista: { text: 'Finalista', color: 'bg-secondary/20 text-secondary border-secondary/50' },
      campeon: { text: '🏆 Campeón', color: 'bg-primary/20 text-primary border-primary/50' }
    };

    const badge = badges[torneo.mi_estado || 'inscrito'];
    return (
      <span className={`px-2 md:px-3 py-1 rounded-full text-xs md:text-sm font-bold border ${badge.color}`}>
        {badge.text}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-textSecondary">Cargando tus torneos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-w-0 space-y-6 md:space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="flex items-center gap-2 md:gap-3 mb-1 md:mb-2">
          <div className="h-0.5 md:h-1 w-8 md:w-12 bg-gradient-to-r from-accent to-yellow-500 rounded-full" />
          <h1 className="text-2xl md:text-5xl font-black text-textPrimary tracking-tight">
            Mis Torneos
          </h1>
        </div>
        <p className="text-textSecondary text-xs md:text-base ml-10 md:ml-15">
          Torneos en los que estás participando
        </p>
      </motion.div>

      {/* Estadísticas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
        {[
          { label: 'Total', value: estadisticas.total, color: 'from-primary to-blue-600', icon: Trophy },
          { label: 'Activos', value: estadisticas.activos, color: 'from-accent to-yellow-500', icon: Clock },
          { label: 'Finalizados', value: estadisticas.finalizados, color: 'from-secondary to-pink-500', icon: CheckCircle },
          { label: 'Campeonatos', value: estadisticas.campeonatos, color: 'from-purple-500 to-pink-500', icon: Award }
        ].map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ y: -4, scale: 1.02 }}
              className="group cursor-pointer relative"
            >
              <div className="bg-cardBg rounded-lg md:rounded-xl p-3 md:p-4 border border-cardBorder group-hover:border-transparent transition-all duration-200 relative overflow-hidden">
                <div className={`hidden md:block absolute -inset-[1px] bg-gradient-to-br ${stat.color} opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-xl -z-10 blur-sm`} />

                <div className="flex items-center justify-between mb-1 md:mb-2">
                  <div className={`bg-gradient-to-br ${stat.color} p-1.5 md:p-2 rounded-md md:rounded-lg`}>
                    <Icon size={16} className="text-white md:w-5 md:h-5" />
                  </div>
                  <p className="text-2xl md:text-4xl font-black text-textPrimary tracking-tight">
                    {stat.value}
                  </p>
                </div>
                <p className="text-textSecondary text-[10px] md:text-xs font-bold uppercase tracking-wider">{stat.label}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Filtros */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex gap-2 md:gap-3"
      >
        {[
          { id: 'todos', label: 'Todos' },
          { id: 'activos', label: 'Activos' },
          { id: 'finalizados', label: 'Finalizados' }
        ].map((filtro) => (
          <button
            key={filtro.id}
            onClick={() => setFiltroEstado(filtro.id as any)}
            className={`px-3 md:px-6 py-2 md:py-3 rounded-lg md:rounded-xl text-sm md:text-base font-bold transition-all active:scale-95 ${
              filtroEstado === filtro.id
                ? 'bg-primary text-white'
                : 'bg-cardBg text-textSecondary hover:bg-cardBorder'
            }`}
          >
            {filtro.label}
          </button>
        ))}
      </motion.div>

      {/* Lista de Torneos */}
      {todosLosTorneos.length === 0 ? (
        <Card>
          <div className="text-center py-12 md:py-16 px-4">
            <div className="bg-accent/10 rounded-full w-16 h-16 md:w-20 md:h-20 flex items-center justify-center mx-auto mb-4">
              <Trophy size={32} className="text-accent md:w-10 md:h-10" />
            </div>
            <h3 className="text-lg md:text-xl font-bold text-textPrimary mb-2">
              No tienes torneos {filtroEstado !== 'todos' ? filtroEstado : ''}
            </h3>
            <p className="text-textSecondary text-sm md:text-base mb-6">
              Inscríbete en un torneo para comenzar a competir
            </p>
            <Button
              variant="primary"
              onClick={() => navigate('/torneos')}
              className="text-sm md:text-base"
            >
              Ver Torneos Disponibles
            </Button>
          </div>
        </Card>
      ) : (
        <>
          {/* Torneos que creé */}
          {torneosCreadosFiltrados.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-1 w-12 bg-gradient-to-r from-primary to-blue-600 rounded-full" />
                <h2 className="text-xl md:text-3xl font-black text-textPrimary">
                  Torneos que creé
                  <span className="ml-3 text-sm md:text-base font-bold text-textSecondary">
                    ({torneosCreadosFiltrados.length})
                  </span>
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                <AnimatePresence mode="popLayout">
                  {torneosCreadosMostrados.map((torneo, index) => (
                    <motion.div
                      key={`creado-${torneo.id}`}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ delay: index * 0.05 }}
                      whileHover={{ y: -8, scale: 1.02 }}
                      onClick={() => navigate(`/torneos/${torneo.id}`)}
                      className="cursor-pointer"
                    >
                      <Card hoverable className="h-full relative">
                        {/* Badge de creador */}
                        <div className="absolute top-3 right-3 z-10">
                          <span className="px-2 py-1 bg-primary/20 text-primary border border-primary/50 rounded-full text-xs font-bold">
                            👑 Creador
                          </span>
                        </div>
                        
                        <div className="p-4 md:p-6">
                          {/* Header con estado */}
                          <div className="flex items-start justify-between mb-3 md:mb-4">
                            <div className="flex-1 min-w-0 pr-20">
                              <h3 className="text-base md:text-xl font-bold text-textPrimary mb-1 truncate">
                                {torneo.nombre}
                              </h3>
                              <p className="text-textSecondary text-xs md:text-sm line-clamp-2">
                                {torneo.descripcion}
                              </p>
                            </div>
                          </div>

                          {/* Badge de estado */}
                          <div className="mb-3 md:mb-4">
                            {getEstadoBadge(torneo)}
                          </div>

                          {/* Información del torneo */}
                          <div className="space-y-2 mb-3 md:mb-4">
                            <div className="flex items-center gap-2 text-textSecondary text-xs md:text-sm">
                              <Calendar size={14} className="flex-shrink-0 md:w-4 md:h-4" />
                              <span className="truncate">
                                {parseFechaSinZonaHoraria(torneo.fecha_inicio).toLocaleDateString('es-ES', { 
                                  day: 'numeric', 
                                  month: 'short' 
                                })}
                                {torneo.fecha_inicio !== torneo.fecha_fin && 
                                  ` - ${parseFechaSinZonaHoraria(torneo.fecha_fin).toLocaleDateString('es-ES', { 
                                    day: 'numeric', 
                                    month: 'short' 
                                  })}`
                                }
                              </span>
                            </div>

                            <div className="flex items-center gap-2 text-textSecondary text-xs md:text-sm">
                              <MapPin size={14} className="flex-shrink-0 md:w-4 md:h-4" />
                              <span className="truncate">{torneo.ubicacion}</span>
                            </div>

                            <div className="flex items-center gap-2 text-textSecondary text-xs md:text-sm">
                              <Trophy size={14} className="flex-shrink-0 md:w-4 md:h-4" />
                              <span>Categoría {torneo.categoria}</span>
                            </div>
                          </div>

                          {/* Footer */}
                          <div className="pt-3 md:pt-4 border-t border-cardBorder flex items-center justify-between">
                            <div className="flex items-center gap-1.5 md:gap-2 text-textSecondary text-xs md:text-sm">
                              <Users size={14} className="md:w-4 md:h-4" />
                              <span>{torneo.equipos_inscritos}/{torneo.max_equipos}</span>
                            </div>
                            {torneo.premio && (
                              <span className="text-accent font-bold text-xs md:text-sm">{torneo.premio}</span>
                            )}
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Botón Cargar Más - Creados */}
              {!mostrarTodosCreados && torneosCreadosFiltrados.length > ITEMS_POR_PAGINA && (
                <div className="text-center mt-6">
                  <Button
                    variant="accent"
                    onClick={() => setMostrarTodosCreados(true)}
                    className="w-full md:w-auto"
                  >
                    Cargar más ({torneosCreadosFiltrados.length - ITEMS_POR_PAGINA} restantes)
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Torneos donde estoy inscrito */}
          {torneosInscritoFiltrados.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-1 w-12 bg-gradient-to-r from-accent to-yellow-500 rounded-full" />
                <h2 className="text-xl md:text-3xl font-black text-textPrimary">
                  Torneos donde estoy inscrito
                  <span className="ml-3 text-sm md:text-base font-bold text-textSecondary">
                    ({torneosInscritoFiltrados.length})
                  </span>
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                <AnimatePresence mode="popLayout">
                  {torneosInscritoMostrados.map((torneo, index) => (
                    <motion.div
                      key={`inscrito-${torneo.id}`}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ delay: index * 0.05 }}
                      whileHover={{ y: -8, scale: 1.02 }}
                      onClick={() => navigate(`/torneos/${torneo.id}`)}
                      className="cursor-pointer"
                    >
                      <Card hoverable className="h-full">
                        <div className="p-4 md:p-6">
                          {/* Header con estado */}
                          <div className="flex items-start justify-between mb-3 md:mb-4">
                            <div className="flex-1 min-w-0">
                              <h3 className="text-base md:text-xl font-bold text-textPrimary mb-1 truncate">
                                {torneo.nombre}
                              </h3>
                              <p className="text-textSecondary text-xs md:text-sm line-clamp-2">
                                {torneo.descripcion}
                              </p>
                            </div>
                          </div>

                          {/* Badge de estado */}
                          <div className="mb-3 md:mb-4">
                            {getEstadoBadge(torneo)}
                          </div>

                          {/* Posición si está disponible */}
                          {torneo.mi_posicion && (
                            <div className="mb-3 md:mb-4 p-2 md:p-3 bg-primary/10 rounded-lg border border-primary/30">
                              <div className="flex items-center justify-between">
                                <span className="text-textSecondary text-xs md:text-sm">Tu posición:</span>
                                <span className="text-primary font-black text-xl md:text-2xl">#{torneo.mi_posicion}</span>
                              </div>
                            </div>
                          )}

                          {/* Información del torneo */}
                          <div className="space-y-2 mb-3 md:mb-4">
                            <div className="flex items-center gap-2 text-textSecondary text-xs md:text-sm">
                              <Calendar size={14} className="flex-shrink-0 md:w-4 md:h-4" />
                              <span className="truncate">
                                {parseFechaSinZonaHoraria(torneo.fecha_inicio).toLocaleDateString('es-ES', { 
                                  day: 'numeric', 
                                  month: 'short' 
                                })}
                                {torneo.fecha_inicio !== torneo.fecha_fin && 
                                  ` - ${parseFechaSinZonaHoraria(torneo.fecha_fin).toLocaleDateString('es-ES', { 
                                    day: 'numeric', 
                                    month: 'short' 
                                  })}`
                                }
                              </span>
                            </div>

                            <div className="flex items-center gap-2 text-textSecondary text-xs md:text-sm">
                              <MapPin size={14} className="flex-shrink-0 md:w-4 md:h-4" />
                              <span className="truncate">{torneo.ubicacion}</span>
                            </div>

                            <div className="flex items-center gap-2 text-textSecondary text-xs md:text-sm">
                              <Trophy size={14} className="flex-shrink-0 md:w-4 md:h-4" />
                              <span>Categoría {torneo.categoria}</span>
                            </div>

                            {torneo.proxima_fecha && (
                              <div className="flex items-center gap-2 text-accent text-xs md:text-sm font-bold">
                                <Clock size={14} className="flex-shrink-0 md:w-4 md:h-4" />
                                <span>
                                  Próximo partido: {parseFechaSinZonaHoraria(torneo.proxima_fecha).toLocaleDateString('es-ES', {
                                    day: 'numeric',
                                    month: 'short',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Footer */}
                          <div className="pt-3 md:pt-4 border-t border-cardBorder flex items-center justify-between">
                            <div className="flex items-center gap-1.5 md:gap-2 text-textSecondary text-xs md:text-sm">
                              <Users size={14} className="md:w-4 md:h-4" />
                              <span>{torneo.equipos_inscritos}/{torneo.max_equipos}</span>
                            </div>
                            {torneo.premio && (
                              <span className="text-accent font-bold text-xs md:text-sm">{torneo.premio}</span>
                            )}
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Botón Cargar Más - Inscrito */}
              {!mostrarTodosInscrito && torneosInscritoFiltrados.length > ITEMS_POR_PAGINA && (
                <div className="text-center mt-6">
                  <Button
                    variant="accent"
                    onClick={() => setMostrarTodosInscrito(true)}
                    className="w-full md:w-auto"
                  >
                    Cargar más ({torneosInscritoFiltrados.length - ITEMS_POR_PAGINA} restantes)
                  </Button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
