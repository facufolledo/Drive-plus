import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { Trophy, MapPin, Calendar, ChevronDown, ChevronUp, Target, Hand, TrendingUp, TrendingDown, Flame, Award, Zap } from 'lucide-react';
import Button from '../components/Button';
import { PartidoCardSkeleton } from '../components/SkeletonLoader';
import { PlayerLink } from '../components/UserLink';
import { AdminBadge, AdminId } from '../components/AdminBadge';
import { apiService } from '../services/api';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DetalleSet {
  set: number;
  juegos_eq1: number;
  juegos_eq2: number;
  tiebreak_eq1?: number;
  tiebreak_eq2?: number;
}

interface ResultadoPartido {
  sets_eq1: number;
  sets_eq2: number;
  detalle_sets: DetalleSet[];
  confirmado: boolean;
  desenlace: string;
}

interface JugadorPartido {
  id_usuario: number;
  nombre_usuario: string;
  nombre: string;
  apellido: string;
  equipo: number;
  rating: number;
}

interface HistorialRating {
  rating_antes: number;
  delta: number;
  rating_despues: number;
}

interface Partido {
  id_partido: number;
  fecha: string;
  estado: string;
  tipo?: string;
  jugadores: JugadorPartido[];
  resultado?: ResultadoPartido;
  historial_rating?: HistorialRating;
}

export default function MiPerfil() {
  const { usuario } = useAuth();
  const [filtro, setFiltro] = useState<'todos' | 'torneos' | 'amistosos'>('todos');
  const [mostrarTodos, setMostrarTodos] = useState(false);
  const [partidos, setPartidos] = useState<Partido[]>([]);
  const [loading, setLoading] = useState(true);
  const [detallesAbiertos, setDetallesAbiertos] = useState<Set<number>>(new Set());
  const [categorias, setCategorias] = useState<any[]>([]);

  useEffect(() => {
    if (usuario?.id_usuario) {
      cargarPartidos();
      cargarCategorias();
    }
  }, [usuario]);

  const cargarCategorias = async () => {
    try {
      const categoriasData = await apiService.getCategorias();
      setCategorias(categoriasData);
    } catch (error) {
      console.error('Error al cargar categorías:', error);
    }
  };

  const obtenerNombreCategoria = (): string | null => {
    // 1. Si el backend ya devuelve el nombre de la categoría, usarlo
    if (usuario?.categoria) return usuario.categoria;
    
    // 2. Buscar por id_categoria en la lista de categorías
    if (usuario?.id_categoria && categorias.length > 0) {
      const cat = categorias.find(c => c.id_categoria === usuario.id_categoria);
      if (cat?.nombre) return cat.nombre;
    }
    
    // 3. Fallback: derivar del rating cuando no tiene categoría asignada
    if (usuario?.rating != null) {
      const r = usuario.rating;
      if (r >= 1800) return 'Libre';
      if (r >= 1600) return '4ta';
      if (r >= 1400) return '5ta';
      if (r >= 1200) return '6ta';
      if (r >= 1000) return '7ma';
      if (r >= 500) return '8va';
      return 'Principiante';
    }
    return null;
  };

  // Función para obtener categoría según rating
  const obtenerCategoriaPorRating = (rating: number): string => {
    if (rating >= 1800) return 'Libre';
    if (rating >= 1600) return '4ta';
    if (rating >= 1400) return '5ta';
    if (rating >= 1200) return '6ta';
    if (rating >= 1000) return '7ma';
    if (rating >= 500) return '8va';
    return 'Principiante';
  };

  // Función para detectar cambio de categoría
  const detectarCambioCategoria = (partido: Partido): { hubo: boolean; tipo: 'ascenso' | 'descenso' | null; categoriaAnterior: string; categoriaNueva: string } | null => {
    if (!partido.historial_rating) return null;
    
    const catAnterior = obtenerCategoriaPorRating(partido.historial_rating.rating_antes);
    const catNueva = obtenerCategoriaPorRating(partido.historial_rating.rating_despues);
    
    if (catAnterior !== catNueva) {
      // Determinar si es ascenso o descenso
      const categorias = ['Principiante', '8va', '7ma', '6ta', '5ta', '4ta', 'Libre'];
      const indexAnterior = categorias.indexOf(catAnterior);
      const indexNueva = categorias.indexOf(catNueva);
      
      return {
        hubo: true,
        tipo: indexNueva > indexAnterior ? 'ascenso' : 'descenso',
        categoriaAnterior: catAnterior,
        categoriaNueva: catNueva
      };
    }
    
    return null;
  };

  const cargarPartidos = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.get(
        `${API_URL}/partidos/usuario/${usuario?.id_usuario}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { limit: 50 }
        }
      );
      
      // Eliminar duplicados por id_partido
      const partidosUnicos = response.data.filter((partido: Partido, index: number, self: Partido[]) =>
        index === self.findIndex((p) => p.id_partido === partido.id_partido)
      );
      
      setPartidos(partidosUnicos);
    } catch (error: any) {
      if (error.response?.status === 404) {
        console.log('No hay partidos disponibles');
      }
      setPartidos([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleDetalles = (partidoId: number) => {
    setDetallesAbiertos(prev => {
      const newSet = new Set(prev);
      if (newSet.has(partidoId)) {
        newSet.delete(partidoId);
      } else {
        newSet.add(partidoId);
      }
      return newSet;
    });
  };

  const obtenerEquipoUsuario = (partido: Partido): JugadorPartido[] => {
    const miEquipo = partido.jugadores.find(j => j.id_usuario === usuario?.id_usuario)?.equipo;
    return partido.jugadores.filter(j => j.equipo === miEquipo);
  };

  const obtenerEquipoRival = (partido: Partido): JugadorPartido[] => {
    const miEquipo = partido.jugadores.find(j => j.id_usuario === usuario?.id_usuario)?.equipo;
    return partido.jugadores.filter(j => j.equipo !== miEquipo);
  };

  const esVictoria = (partido: Partido): boolean => {
    if (!partido.resultado) {
      // Si no hay resultado, usar historial_rating para determinar victoria
      if (partido.historial_rating) {
        return partido.historial_rating.delta > 0;
      }
      return false;
    }
    const miEquipo = partido.jugadores.find(j => j.id_usuario === usuario?.id_usuario)?.equipo;
    if (miEquipo === 1) {
      return partido.resultado.sets_eq1 > partido.resultado.sets_eq2;
    } else {
      return partido.resultado.sets_eq2 > partido.resultado.sets_eq1;
    }
  };

  const formatearSets = (partido: Partido): string => {
    if (!partido.resultado) {
      // Si no hay resultado pero hay historial_rating, mostrar W/L
      if (partido.historial_rating) {
        return partido.historial_rating.delta > 0 ? 'W' : 'L';
      }
      return '-';
    }
    const miEquipo = partido.jugadores.find(j => j.id_usuario === usuario?.id_usuario)?.equipo;
    if (miEquipo === 1) {
      return `${partido.resultado.sets_eq1}-${partido.resultado.sets_eq2}`;
    } else {
      return `${partido.resultado.sets_eq2}-${partido.resultado.sets_eq1}`;
    }
  };

  const formatearDetalleSets = (partido: Partido): string => {
    if (!partido.resultado?.detalle_sets) return '';
    const miEquipo = partido.jugadores.find(j => j.id_usuario === usuario?.id_usuario)?.equipo;
    
    return partido.resultado.detalle_sets.map(set => {
      const misJuegos = miEquipo === 1 ? set.juegos_eq1 : set.juegos_eq2;
      const rivalJuegos = miEquipo === 1 ? set.juegos_eq2 : set.juegos_eq1;
      
      // Solo mostrar tiebreak si existe y no es null
      if (set.tiebreak_eq1 !== undefined && set.tiebreak_eq1 !== null && 
          set.tiebreak_eq2 !== undefined && set.tiebreak_eq2 !== null) {
        const miTiebreak = miEquipo === 1 ? set.tiebreak_eq1 : set.tiebreak_eq2;
        return `${misJuegos}-${rivalJuegos}(${miTiebreak})`;
      }
      return `${misJuegos}-${rivalJuegos}`;
    }).join(' / ');
  };

  const formatearFecha = (fecha: string): string => {
    const fechaPartido = new Date(fecha);
    const ahora = new Date();
    const diffMs = ahora.getTime() - fechaPartido.getTime();
    const diffHoras = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDias = Math.floor(diffHoras / 24);

    if (diffHoras < 1) return 'hace menos de 1 hora';
    if (diffHoras < 24) return `hace ${diffHoras} hora${diffHoras > 1 ? 's' : ''}`;
    if (diffDias < 7) return `hace ${diffDias} día${diffDias > 1 ? 's' : ''}`;
    return fechaPartido.toLocaleDateString();
  };

  // Aplicar filtro según el tipo seleccionado
  const partidosFiltrados = partidos.filter(partido => {
    if (filtro === 'todos') return true;
    if (filtro === 'torneos') return partido.tipo === 'torneo';
    if (filtro === 'amistosos') return partido.tipo === 'amistoso';
    return true;
  });
  
  const partidosMostrados = mostrarTodos ? partidosFiltrados : partidosFiltrados.slice(0, 10);

  // Contar totales por tipo
  const totalPartidos = partidos.filter(p => p.resultado || p.historial_rating).length;
  const partidosTorneos = partidos.filter(p => p.tipo === 'torneo').length;
  const partidosAmistosos = partidos.filter(p => p.tipo === 'amistoso' || !p.tipo).length;
  
  const victorias = partidos.filter(p => (p.resultado || p.historial_rating) && esVictoria(p)).length;
  const derrotas = totalPartidos - victorias;
  const winrate = totalPartidos > 0 ? Math.round((victorias / totalPartidos) * 100) : 0;

  // Estadísticas avanzadas
  const calcularEstadisticasAvanzadas = () => {
    // Victorias/Derrotas por tipo
    const torneos = partidos.filter(p => p.tipo === 'torneo');
    const amistosos = partidos.filter(p => p.tipo === 'amistoso' || !p.tipo);
    
    const victoriasTorneos = torneos.filter(p => (p.resultado || p.historial_rating) && esVictoria(p)).length;
    const victoriaAmistosos = amistosos.filter(p => (p.resultado || p.historial_rating) && esVictoria(p)).length;
    
    const winrateTorneos = torneos.length > 0 ? Math.round((victoriasTorneos / torneos.length) * 100) : 0;
    const winrateAmistosos = amistosos.length > 0 ? Math.round((victoriaAmistosos / amistosos.length) * 100) : 0;

    // Racha actual
    let rachaActual = 0;
    let rachaVictorias = true;
    const partidosOrdenados = [...partidos].sort((a, b) => 
      new Date(b.fecha).getTime() - new Date(a.fecha).getTime()
    );
    
    for (const partido of partidosOrdenados) {
      if (!partido.resultado && !partido.historial_rating) continue;
      const victoria = esVictoria(partido);
      if (rachaActual === 0) {
        rachaVictorias = victoria;
        rachaActual = 1;
      } else if (victoria === rachaVictorias) {
        rachaActual++;
      } else {
        break;
      }
    }

    // Mejor racha de victorias
    let mejorRacha = 0;
    let rachaTemp = 0;
    for (const partido of partidosOrdenados.reverse()) {
      if (!partido.resultado && !partido.historial_rating) continue;
      if (esVictoria(partido)) {
        rachaTemp++;
        mejorRacha = Math.max(mejorRacha, rachaTemp);
      } else {
        rachaTemp = 0;
      }
    }

    // Cambio de rating total
    const cambioRatingTotal = partidos.reduce((acc, p) => {
      return acc + (p.historial_rating?.delta || 0);
    }, 0);

    // Rating máximo y mínimo alcanzado
    let ratingMax = usuario?.rating || 1200;
    let ratingMin = usuario?.rating || 1200;
    let ratingActual = usuario?.rating || 1200;
    
    // Reconstruir historial de rating
    for (const partido of partidosOrdenados.reverse()) {
      if (partido.historial_rating) {
        ratingActual = partido.historial_rating.rating_despues;
        ratingMax = Math.max(ratingMax, ratingActual);
        ratingMin = Math.min(ratingMin, ratingActual);
      }
    }

    // Sets ganados/perdidos
    let setsGanados = 0;
    let setsPerdidos = 0;
    let gamesGanados = 0;
    let gamesPerdidos = 0;

    for (const partido of partidos) {
      if (!partido.resultado) continue;
      const miEquipo = partido.jugadores.find(j => j.id_usuario === usuario?.id_usuario)?.equipo;
      
      if (miEquipo === 1) {
        setsGanados += partido.resultado.sets_eq1;
        setsPerdidos += partido.resultado.sets_eq2;
      } else {
        setsGanados += partido.resultado.sets_eq2;
        setsPerdidos += partido.resultado.sets_eq1;
      }

      // Games
      if (partido.resultado.detalle_sets) {
        for (const set of partido.resultado.detalle_sets) {
          if (miEquipo === 1) {
            gamesGanados += set.juegos_eq1;
            gamesPerdidos += set.juegos_eq2;
          } else {
            gamesGanados += set.juegos_eq2;
            gamesPerdidos += set.juegos_eq1;
          }
        }
      }
    }

    return {
      winrateTorneos,
      winrateAmistosos,
      victoriasTorneos,
      victoriaAmistosos,
      derrotasTorneos: torneos.length - victoriasTorneos,
      derrotasAmistosos: amistosos.length - victoriaAmistosos,
      rachaActual,
      rachaVictorias,
      mejorRacha,
      cambioRatingTotal,
      ratingMax,
      ratingMin,
      setsGanados,
      setsPerdidos,
      gamesGanados,
      gamesPerdidos
    };
  };

  const stats = calcularEstadisticasAvanzadas();

  return (
    <div className="min-h-screen p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6">
          
          {/* Panel Izquierdo - Perfil */}
          <div className="lg:col-span-4 space-y-4">
            
            {/* Card de Perfil */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-cardBg rounded-xl p-3 md:p-6 border border-cardBorder"
            >
              <div className="flex items-center justify-between mb-4 md:mb-6">
                <h2 className="text-lg md:text-xl font-bold text-textPrimary flex items-center gap-2">
                  <div className="h-0.5 md:h-1 w-6 md:w-8 bg-gradient-to-r from-primary to-secondary rounded-full" />
                  Mi Perfil
                </h2>
                <button
                  onClick={() => window.location.href = '/perfil/editar'}
                  className="text-primary hover:text-primary/80 text-sm font-semibold transition-colors"
                >
                  Editar
                </button>
              </div>

              {/* Avatar y Nombre */}
              <div className="flex flex-col items-center mb-3">
                <div className="w-20 h-20 md:w-32 md:h-32 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-2xl md:text-4xl font-black mb-2 overflow-hidden">
                  {usuario?.foto_perfil ? (
                    <img
                      src={usuario.foto_perfil}
                      alt={`${usuario.nombre} ${usuario.apellido}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span>{usuario?.nombre?.charAt(0)}{usuario?.apellido?.charAt(0)}</span>
                  )}
                </div>
                <h3 className="text-lg md:text-2xl font-black text-textPrimary text-center">
                  {usuario?.nombre} {usuario?.apellido}
                </h3>
                <p className="text-textSecondary text-[10px] md:text-sm">@{usuario?.nombre_usuario}</p>
                <p className="text-textSecondary text-[9px] md:text-xs mt-0.5">{usuario?.email}</p>
              </div>

              {/* Rating y Categoría */}
              <div className="text-center mb-3 p-2 md:p-4 bg-primary/10 rounded-lg">
                <p className="text-textSecondary text-[10px] md:text-sm mb-0.5">Rating</p>
                <p className="text-2xl md:text-4xl font-black text-primary">{usuario?.rating || 1200}</p>
                {obtenerNombreCategoria() && (
                  <div className="mt-1 px-2 py-0.5 bg-primary/20 rounded-full inline-block">
                    <p className="text-primary text-[9px] md:text-xs font-semibold">
                      {obtenerNombreCategoria()}
                    </p>
                  </div>
                )}
              </div>

              {/* Info Adicional */}
              <div className="space-y-1.5 text-[10px] md:text-sm">
                {usuario?.posicion_preferida && (
                  <div className="flex items-center gap-1.5 text-textSecondary">
                    <Target size={12} className="text-primary md:w-3.5 md:h-3.5" />
                    <span className="capitalize">{usuario.posicion_preferida}</span>
                  </div>
                )}
                {usuario?.mano_dominante && (
                  <div className="flex items-center gap-1.5 text-textSecondary">
                    <Hand size={12} className="text-secondary md:w-3.5 md:h-3.5" />
                    <span className="capitalize">{usuario.mano_dominante}</span>
                  </div>
                )}
                {usuario?.ciudad && usuario?.pais && (
                  <div className="flex items-center gap-1.5 text-textSecondary">
                    <MapPin size={12} className="text-primary md:w-3.5 md:h-3.5" />
                    <span>{usuario.ciudad}, {usuario.pais}</span>
                  </div>
                )}
                <div className="flex items-center gap-1.5 text-textSecondary">
                  <Calendar size={12} className="text-primary md:w-3.5 md:h-3.5" />
                  <span>Miembro desde {new Date().getFullYear()}</span>
                </div>
              </div>
            </motion.div>

            {/* Card de Estadísticas */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-br from-primary/20 to-secondary/20 rounded-xl p-3 md:p-6 border border-primary/30"
            >
              <h3 className="text-sm md:text-lg font-bold text-textPrimary mb-2 md:mb-4">Estadísticas</h3>
              
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-primary/20 rounded-lg p-2 text-center">
                  <Trophy size={16} className="text-primary mx-auto mb-1 md:w-5 md:h-5" />
                  <p className="text-xl md:text-2xl font-black text-primary">{victorias}</p>
                  <p className="text-[9px] md:text-xs text-textSecondary">Victorias</p>
                </div>
                <div className="bg-red-500/20 rounded-lg p-2 text-center">
                  <Trophy size={16} className="text-red-500 mx-auto mb-1 md:w-5 md:h-5" />
                  <p className="text-xl md:text-2xl font-black text-red-500">{derrotas}</p>
                  <p className="text-[9px] md:text-xs text-textSecondary">Derrotas</p>
                </div>
              </div>

              <div className="mt-2 bg-accent/20 rounded-lg p-2 text-center">
                <p className="text-[9px] md:text-xs text-textSecondary mb-0.5">Winrate General</p>
                <p className="text-2xl md:text-3xl font-black text-accent">{winrate}%</p>
              </div>
            </motion.div>

            {/* Card de Estadísticas Avanzadas */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-cardBg rounded-xl p-3 md:p-6 border border-cardBorder"
            >
              <h3 className="text-sm md:text-lg font-bold text-textPrimary mb-3 md:mb-4 flex items-center gap-2">
                <Zap size={16} className="text-accent" />
                Estadísticas Avanzadas
              </h3>
              
              {/* Winrate por tipo */}
              <div className="space-y-3 mb-4">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[10px] md:text-xs text-textSecondary flex items-center gap-1">
                      <Award size={12} className="text-accent" />
                      Torneos
                    </span>
                    <span className="text-[10px] md:text-xs font-bold text-accent">{stats.winrateTorneos}%</span>
                  </div>
                  <div className="h-2 bg-cardBorder rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-accent to-accent/60 rounded-full transition-all duration-500"
                      style={{ width: `${stats.winrateTorneos}%` }}
                    />
                  </div>
                  <p className="text-[9px] text-textSecondary mt-0.5">{stats.victoriasTorneos}V - {stats.derrotasTorneos}D</p>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[10px] md:text-xs text-textSecondary flex items-center gap-1">
                      <Target size={12} className="text-primary" />
                      Amistosos
                    </span>
                    <span className="text-[10px] md:text-xs font-bold text-primary">{stats.winrateAmistosos}%</span>
                  </div>
                  <div className="h-2 bg-cardBorder rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-primary to-primary/60 rounded-full transition-all duration-500"
                      style={{ width: `${stats.winrateAmistosos}%` }}
                    />
                  </div>
                  <p className="text-[9px] text-textSecondary mt-0.5">{stats.victoriaAmistosos}V - {stats.derrotasAmistosos}D</p>
                </div>
              </div>

              {/* Racha y Rating */}
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className={`rounded-lg p-2 text-center ${stats.rachaVictorias ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                  <Flame size={14} className={`mx-auto mb-1 ${stats.rachaVictorias ? 'text-green-400' : 'text-red-400'}`} />
                  <p className={`text-lg md:text-xl font-black ${stats.rachaVictorias ? 'text-green-400' : 'text-red-400'}`}>
                    {stats.rachaActual}
                  </p>
                  <p className="text-[9px] md:text-xs text-textSecondary">
                    Racha {stats.rachaVictorias ? 'Victorias' : 'Derrotas'}
                  </p>
                </div>
                <div className="bg-yellow-500/20 rounded-lg p-2 text-center">
                  <Trophy size={14} className="text-yellow-400 mx-auto mb-1" />
                  <p className="text-lg md:text-xl font-black text-yellow-400">{stats.mejorRacha}</p>
                  <p className="text-[9px] md:text-xs text-textSecondary">Mejor Racha</p>
                </div>
              </div>

              {/* Rating histórico */}
              <div className="grid grid-cols-3 gap-1.5 mb-3">
                <div className="bg-cardBorder/30 rounded-lg p-1.5 text-center">
                  <TrendingUp size={12} className="text-green-400 mx-auto mb-0.5" />
                  <p className="text-sm md:text-base font-bold text-green-400">{stats.ratingMax}</p>
                  <p className="text-[8px] md:text-[10px] text-textSecondary">Máximo</p>
                </div>
                <div className="bg-cardBorder/30 rounded-lg p-1.5 text-center">
                  <TrendingDown size={12} className="text-red-400 mx-auto mb-0.5" />
                  <p className="text-sm md:text-base font-bold text-red-400">{stats.ratingMin}</p>
                  <p className="text-[8px] md:text-[10px] text-textSecondary">Mínimo</p>
                </div>
                <div className={`rounded-lg p-1.5 text-center ${stats.cambioRatingTotal >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                  {stats.cambioRatingTotal >= 0 ? (
                    <TrendingUp size={12} className="text-green-400 mx-auto mb-0.5" />
                  ) : (
                    <TrendingDown size={12} className="text-red-400 mx-auto mb-0.5" />
                  )}
                  <p className={`text-sm md:text-base font-bold ${stats.cambioRatingTotal >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {stats.cambioRatingTotal >= 0 ? '+' : ''}{stats.cambioRatingTotal}
                  </p>
                  <p className="text-[8px] md:text-[10px] text-textSecondary">Cambio Total</p>
                </div>
              </div>

              {/* Sets y Games */}
              <div className="border-t border-cardBorder pt-3">
                <p className="text-[10px] md:text-xs text-textSecondary mb-2">Rendimiento en Sets/Games</p>
                <div className="grid grid-cols-2 gap-2">
                  <div className="text-center">
                    <p className="text-[9px] text-textSecondary">Sets</p>
                    <p className="text-sm font-bold">
                      <span className="text-green-400">{stats.setsGanados}</span>
                      <span className="text-textSecondary mx-1">-</span>
                      <span className="text-red-400">{stats.setsPerdidos}</span>
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-[9px] text-textSecondary">Games</p>
                    <p className="text-sm font-bold">
                      <span className="text-green-400">{stats.gamesGanados}</span>
                      <span className="text-textSecondary mx-1">-</span>
                      <span className="text-red-400">{stats.gamesPerdidos}</span>
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Panel Derecho - Historial */}
          <div className="lg:col-span-8">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-cardBg rounded-xl p-4 md:p-6 border border-cardBorder"
            >
              {/* Header */}
              <div className="mb-4 md:mb-6">
                <h2 className="text-xl md:text-2xl font-black text-textPrimary mb-3 md:mb-4">Historial de Partidos</h2>
                
                {/* Estadísticas */}
                <div className="grid grid-cols-4 gap-2 md:gap-4 mb-4 md:mb-6">
                  <div>
                    <p className="text-textSecondary text-[10px] md:text-sm">Total</p>
                    <p className="text-xl md:text-2xl font-black text-textPrimary">{totalPartidos}</p>
                  </div>
                  <div>
                    <p className="text-textSecondary text-[10px] md:text-sm">Ganados</p>
                    <p className="text-xl md:text-2xl font-black text-secondary">{victorias}</p>
                  </div>
                  <div>
                    <p className="text-textSecondary text-[10px] md:text-sm">Perdidos</p>
                    <p className="text-xl md:text-2xl font-black text-red-500">{derrotas}</p>
                  </div>
                  <div>
                    <p className="text-textSecondary text-[10px] md:text-sm">Winrate</p>
                    <p className="text-xl md:text-2xl font-black text-accent">{winrate}%</p>
                  </div>
                </div>

                {/* Filtros */}
                <div className="flex gap-1 md:gap-2 flex-wrap">
                  <Button
                    variant={filtro === 'todos' ? 'primary' : 'ghost'}
                    onClick={() => setFiltro('todos')}
                    className="text-[10px] md:text-sm px-2 md:px-4 py-1 md:py-2"
                  >
                    TODOS ({totalPartidos})
                  </Button>
                  <Button
                    variant={filtro === 'torneos' ? 'primary' : 'ghost'}
                    onClick={() => setFiltro('torneos')}
                    className="text-[10px] md:text-sm px-2 md:px-4 py-1 md:py-2"
                  >
                    TORNEOS ({partidosTorneos})
                  </Button>
                  <Button
                    variant={filtro === 'amistosos' ? 'primary' : 'ghost'}
                    onClick={() => setFiltro('amistosos')}
                    className="text-[10px] md:text-sm px-2 md:px-4 py-1 md:py-2"
                  >
                    AMISTOSOS ({partidosAmistosos})
                  </Button>
                </div>
              </div>

              {/* Lista de Partidos */}
              <div className="space-y-3">
                {loading ? (
                  <>
                    <PartidoCardSkeleton />
                    <PartidoCardSkeleton />
                    <PartidoCardSkeleton />
                    <PartidoCardSkeleton />
                    <PartidoCardSkeleton />
                  </>
                ) : partidosMostrados.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="bg-cardBorder/30 rounded-lg p-8">
                      <Trophy size={48} className="mx-auto mb-4 text-textSecondary opacity-50" />
                      <p className="text-textPrimary font-bold mb-2">Sin partidos registrados</p>
                      <p className="text-textSecondary text-sm">
                        Tus partidos aparecerán aquí una vez que juegues
                      </p>
                    </div>
                  </div>
                ) : (
                  partidosMostrados.map((partido, index) => {
                    const victoria = esVictoria(partido);
                    const miEquipo = obtenerEquipoUsuario(partido);
                    const rivalEquipo = obtenerEquipoRival(partido);
                    const detallesVisible = detallesAbiertos.has(partido.id_partido);
                    const cambioCategoria = detectarCambioCategoria(partido);

                    return (
                      <div key={partido.id_partido}>
                        {/* Indicador de Cambio de Categoría */}
                        {cambioCategoria?.hubo && (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className={`mb-2 p-2 md:p-3 rounded-lg border-2 ${
                              cambioCategoria.tipo === 'ascenso'
                                ? 'bg-gradient-to-r from-green-500/10 to-emerald-500/10 border-green-500/50'
                                : 'bg-gradient-to-r from-orange-500/10 to-red-500/10 border-orange-500/50'
                            }`}
                          >
                            <div className="flex items-center gap-2 justify-center">
                              {cambioCategoria.tipo === 'ascenso' ? (
                                <TrendingUp className="text-green-400" size={16} />
                              ) : (
                                <TrendingDown className="text-orange-400" size={16} />
                              )}
                              <span className={`text-xs md:text-sm font-bold ${
                                cambioCategoria.tipo === 'ascenso' ? 'text-green-400' : 'text-orange-400'
                              }`}>
                                {cambioCategoria.tipo === 'ascenso' ? '¡ASCENDISTE!' : 'DESCENDISTE'} {cambioCategoria.categoriaAnterior} → {cambioCategoria.categoriaNueva}
                              </span>
                              {cambioCategoria.tipo === 'ascenso' ? (
                                <Trophy className="text-green-400" size={16} />
                              ) : (
                                <TrendingDown className="text-orange-400" size={16} />
                              )}
                            </div>
                          </motion.div>
                        )}

                        {/* Card del Partido */}
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className={`relative rounded-lg p-3 md:p-4 border-l-4 ${
                            victoria
                              ? 'bg-green-500/20 border-green-500 shadow-green-500/20 shadow-lg'
                              : 'bg-red-500/20 border-red-500 shadow-red-500/20 shadow-lg'
                          }`}
                        >
                        {/* Tipo y Fecha */}
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
                          <div className="flex items-center gap-2 flex-wrap">
                            <AdminBadge id={partido.id_partido} label="Partido" />
                            <span className={`px-2 md:px-3 py-0.5 md:py-1 rounded-full text-[10px] md:text-xs font-bold ${
                              partido.tipo === 'torneo' 
                                ? 'bg-accent/20 text-accent' 
                                : 'bg-primary/20 text-primary'
                            }`}>
                              {partido.tipo === 'torneo' ? 'TORNEO' : 'AMISTOSO'}
                            </span>
                            {partido.fase && (
                              <span className="px-2 md:px-3 py-0.5 md:py-1 rounded-full text-[10px] md:text-xs font-bold bg-purple-500/20 text-purple-400">
                                {partido.fase.toUpperCase()}
                              </span>
                            )}
                            {partido.categoria && (
                              <span className="px-2 md:px-3 py-0.5 md:py-1 rounded-full text-[10px] md:text-xs font-bold bg-blue-500/20 text-blue-400">
                                {partido.categoria}
                              </span>
                            )}
                            <span className="text-textSecondary text-[10px] md:text-xs">
                              {formatearFecha(partido.fecha)}
                            </span>
                          </div>
                          {partido.historial_rating && (
                            <span className={`text-base md:text-lg font-black ${
                              partido.historial_rating.delta > 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {partido.historial_rating.delta > 0 ? '+' : ''}{partido.historial_rating.delta}
                            </span>
                          )}
                        </div>

                        {/* Equipos y Resultado */}
                        <div className="grid grid-cols-12 gap-2 md:gap-4 items-center mb-2">
                          {/* Mi Equipo */}
                          <div className="col-span-5">
                            {miEquipo.map((jugador, i) => (
                              <div key={i} className="truncate flex items-center gap-1">
                                <PlayerLink 
                                  id={jugador.id_usuario} 
                                  nombre={`${jugador.nombre} ${jugador.apellido}`}
                                  nombreUsuario={jugador.nombre_usuario}
                                  size="sm" 
                                />
                                <AdminId id={jugador.id_usuario} prefix="U" />
                              </div>
                            ))}
                          </div>

                          {/* Resultado */}
                          <div className="col-span-2 text-center">
                            <p className={`text-lg md:text-3xl font-black leading-tight ${
                              victoria ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {formatearSets(partido)}
                            </p>
                            <p className="text-textSecondary text-[8px] md:text-xs hidden sm:block">
                              {formatearDetalleSets(partido)}
                            </p>
                          </div>

                          {/* Equipo Rival */}
                          <div className="col-span-5 text-right">
                            {rivalEquipo.map((jugador, i) => (
                              <div key={i} className="truncate flex items-center justify-end gap-1">
                                <AdminId id={jugador.id_usuario} prefix="U" />
                                <PlayerLink 
                                  id={jugador.id_usuario} 
                                  nombre={`${jugador.nombre} ${jugador.apellido}`}
                                  nombreUsuario={jugador.nombre_usuario}
                                  size="sm" 
                                />
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Detalles Expandibles */}
                        <AnimatePresence>
                          {detallesVisible && partido.resultado?.detalle_sets && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.2 }}
                              className="overflow-hidden"
                            >
                              <div className="mt-3 md:mt-4 pt-3 md:pt-4 border-t border-cardBorder">
                                <h4 className="text-[10px] md:text-xs font-bold text-textSecondary mb-2">Detalle por Set</h4>
                                <div className="space-y-1 md:space-y-2">
                                  {partido.resultado.detalle_sets.map((set, idx) => {
                                    const miEquipoNum = partido.jugadores.find(j => j.id_usuario === usuario?.id_usuario)?.equipo;
                                    const misJuegos = miEquipoNum === 1 ? set.juegos_eq1 : set.juegos_eq2;
                                    const rivalJuegos = miEquipoNum === 1 ? set.juegos_eq2 : set.juegos_eq1;
                                    const ganeSet = misJuegos > rivalJuegos;

                                    return (
                                      <div key={idx} className={`flex items-center justify-between p-1.5 md:p-2 rounded ${
                                        ganeSet ? 'bg-green-500/10' : 'bg-red-500/10'
                                      }`}>
                                        <span className="text-textSecondary text-[10px] md:text-xs">Set {set.set}</span>
                                        <span className={`font-bold text-xs md:text-sm ${
                                          ganeSet ? 'text-green-400' : 'text-red-400'
                                        }`}>
                                          {misJuegos} - {rivalJuegos}
                                          {set.tiebreak_eq1 !== undefined && set.tiebreak_eq1 !== null && 
                                           set.tiebreak_eq2 !== undefined && set.tiebreak_eq2 !== null && (
                                            <span className="text-[10px] md:text-xs ml-1">
                                              ({miEquipoNum === 1 ? set.tiebreak_eq1 : set.tiebreak_eq2})
                                            </span>
                                          )}
                                        </span>
                                      </div>
                                    );
                                  })}
                                </div>
                                {partido.historial_rating && (
                                  <div className="mt-2 md:mt-3 text-[10px] md:text-xs text-textSecondary space-y-0.5">
                                    <p>Rating antes: {partido.historial_rating.rating_antes}</p>
                                    <p>Rating después: {partido.historial_rating.rating_despues}</p>
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>

                        {/* Botón Ver Detalles */}
                        {partido.resultado && (
                          <button 
                            onClick={() => toggleDetalles(partido.id_partido)}
                            className="absolute bottom-1 md:bottom-2 right-1 md:right-2 text-textSecondary hover:text-primary text-[10px] md:text-xs flex items-center gap-1 transition-colors"
                          >
                            {detallesVisible ? 'ocultar' : 'detalles'}
                            {detallesVisible ? <ChevronUp size={10} className="md:w-3 md:h-3" /> : <ChevronDown size={10} className="md:w-3 md:h-3" />}
                          </button>
                        )}
                      </motion.div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Botón Cargar Más */}
              {!mostrarTodos && partidosFiltrados.length > 10 && (
                <div className="mt-6 text-center">
                  <Button
                    variant="ghost"
                    onClick={() => setMostrarTodos(true)}
                    className="w-full"
                  >
                    cargar más
                  </Button>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
