import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  Trophy, 
  MapPin, 
  Calendar, 
  Target, 
  Hand, 
  TrendingUp, 
  TrendingDown, 
  Flame, 
  Award, 
  Zap,
  Users,
  Share2,
  User
} from 'lucide-react';
import Button from '../components/Button';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { PartidoCardSkeleton } from '../components/SkeletonLoader';
import { PlayerLink } from '../components/UserLink';
import { AdminBadge, AdminId } from '../components/AdminBadge';
import { perfilService, PerfilPublico as PerfilPublicoType, EstadisticasJugador, PartidoHistorial } from '../services/perfil.service';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { clientLogger } from '../utils/clientLogger';

export default function PerfilPublico() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const { usuario: usuarioActual } = useAuth();
  
  const [perfil, setPerfil] = useState<PerfilPublicoType | null>(null);
  const [estadisticas, setEstadisticas] = useState<EstadisticasJugador | null>(null);
  const [partidos, setPartidos] = useState<PartidoHistorial[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filtro, setFiltro] = useState<'todos' | 'torneos' | 'amistosos'>('todos');
  const [mostrarTodos, setMostrarTodos] = useState(false);
  const [detallesAbiertos, setDetallesAbiertos] = useState<Set<number>>(new Set());
  const [categorias, setCategorias] = useState<any[]>([]);

  useEffect(() => {
    if (username) {
      cargarPerfil(username);
      cargarCategorias();
    }
  }, [username]);

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
    if (perfil?.categoria) return perfil.categoria;
    
    // 2. Buscar por categoria_id en la lista de categorías
    if (perfil?.categoria_id && categorias.length > 0) {
      const cat = categorias.find(c => c.id_categoria === perfil.categoria_id);
      if (cat?.nombre) return cat.nombre;
    }
    
    // 3. Fallback: derivar del rating cuando el usuario no tiene categoría asignada
    if (perfil?.rating != null) {
      const r = perfil.rating;
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

  const cargarPerfil = async (username: string) => {
    try {
      setLoading(true);
      setError('');
      
      clientLogger.userAction('View public profile', { username });
      
      // Cargar perfil
      const perfilData = await perfilService.getPerfilPublico(username);
      console.log('Perfil data:', perfilData); // Debug
      setPerfil(perfilData);
      
      // Cargar estadísticas y partidos en paralelo
      const [estadisticasData, partidosData] = await Promise.all([
        perfilService.getEstadisticas(perfilData.id_usuario).catch(() => null),
        perfilService.getHistorial(perfilData.id_usuario).catch(() => [])
      ]);
      
      setEstadisticas(estadisticasData);
      setPartidos(partidosData);
      
    } catch (err: any) {
      setError(err.message || 'Error al cargar el perfil');
      clientLogger.error('Error loading public profile', { username, error: err.message });
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

  const obtenerEquipoUsuario = (partido: PartidoHistorial): any[] => {
    const equipoUsuario = partido.jugadores.find(j => j.id_usuario === perfil?.id_usuario)?.equipo;
    return partido.jugadores.filter(j => j.equipo === equipoUsuario);
  };

  const obtenerEquipoRival = (partido: PartidoHistorial): any[] => {
    const equipoUsuario = partido.jugadores.find(j => j.id_usuario === perfil?.id_usuario)?.equipo;
    return partido.jugadores.filter(j => j.equipo !== equipoUsuario);
  };

  const esVictoria = (partido: PartidoHistorial): boolean => {
    if (!partido.resultado) {
      if (partido.historial_rating) {
        return partido.historial_rating.delta > 0;
      }
      return false;
    }
    const equipoUsuario = partido.jugadores.find(j => j.id_usuario === perfil?.id_usuario)?.equipo;
    if (equipoUsuario === 1) {
      return partido.resultado.sets_eq1 > partido.resultado.sets_eq2;
    } else {
      return partido.resultado.sets_eq2 > partido.resultado.sets_eq1;
    }
  };

  const formatearSets = (partido: PartidoHistorial): string => {
    if (!partido.resultado) {
      if (partido.historial_rating) {
        return partido.historial_rating.delta > 0 ? 'W' : 'L';
      }
      return '-';
    }
    const equipoUsuario = partido.jugadores.find(j => j.id_usuario === perfil?.id_usuario)?.equipo;
    if (equipoUsuario === 1) {
      return `${partido.resultado.sets_eq1}-${partido.resultado.sets_eq2}`;
    } else {
      return `${partido.resultado.sets_eq2}-${partido.resultado.sets_eq1}`;
    }
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

  const compartirPerfil = async () => {
    const url = window.location.href;
    const texto = `Mira el perfil de ${perfil?.nombre} ${perfil?.apellido} en Drive+`;
    
    if (navigator.share) {
      try {
        await navigator.share({ title: texto, url });
        clientLogger.userAction('Share profile', { username, method: 'native' });
      } catch (err) {
        // Usuario canceló
      }
    } else {
      // Fallback: copiar al clipboard
      try {
        await navigator.clipboard.writeText(url);
        clientLogger.userAction('Share profile', { username, method: 'clipboard' });
        // Aquí podrías mostrar una notificación de "Copiado al portapapeles"
      } catch (err) {
        console.error('Error al copiar:', err);
      }
    }
  };

  // Aplicar filtros
  const partidosFiltrados = partidos.filter(partido => {
    if (filtro === 'todos') return true;
    if (filtro === 'torneos') return partido.tipo === 'torneo';
    if (filtro === 'amistosos') return partido.tipo === 'amistoso';
    return true;
  });
  
  const partidosMostrados = mostrarTodos ? partidosFiltrados : partidosFiltrados.slice(0, 10);

  // Verificar si es el propio perfil
  const esMiPerfil = usuarioActual?.nombre_usuario === username;

  if (loading) {
    return (
      <div className="min-h-screen p-4 md:p-6">
        <div className="max-w-7xl mx-auto">
          <LoadingSkeleton variant="card" lines={10} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-4 md:p-6 flex items-center justify-center">
        <div className="text-center">
          <User size={64} className="mx-auto mb-4 text-textSecondary opacity-50" />
          <h2 className="text-xl font-bold text-textPrimary mb-2">Jugador no encontrado</h2>
          <p className="text-textSecondary mb-4">{error}</p>
          <Button onClick={() => navigate(-1)}>
            <ArrowLeft size={16} /> Volver
          </Button>
        </div>
      </div>
    );
  }

  if (!perfil) return null;

  // Calcular estadísticas básicas si no tenemos las avanzadas
  const totalPartidos = partidos.filter(p => p.resultado || p.historial_rating).length;
  const victorias = partidos.filter(p => (p.resultado || p.historial_rating) && esVictoria(p)).length;
  const derrotas = totalPartidos - victorias;
  const winrate = totalPartidos > 0 ? Math.round((victorias / totalPartidos) * 100) : 0;

  const partidosTorneos = partidos.filter(p => p.tipo === 'torneo').length;
  const partidosAmistosos = partidos.filter(p => p.tipo === 'amistoso' || !p.tipo).length;

  return (
    <div className="min-h-screen p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header con navegación */}
        <div className="flex items-center justify-between mb-6">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft size={16} /> Volver
          </Button>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={compartirPerfil}>
              <Share2 size={16} /> Compartir
            </Button>
            {!esMiPerfil && (
              <Button variant="primary" onClick={() => navigate(`/comparar/${usuarioActual?.nombre_usuario}/${username}`)}>
                <Users size={16} /> Comparar
              </Button>
            )}
          </div>
        </div>

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
                  {esMiPerfil ? 'Mi Perfil' : 'Perfil'}
                </h2>
                {esMiPerfil && (
                  <button
                    onClick={() => navigate('/perfil/editar')}
                    className="text-primary hover:text-primary/80 text-sm font-semibold transition-colors"
                  >
                    Editar
                  </button>
                )}
              </div>

              {/* Avatar y Nombre */}
              <div className="flex flex-col items-center mb-3">
                <div className="w-20 h-20 md:w-32 md:h-32 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-2xl md:text-4xl font-black mb-2 overflow-hidden">
                  {perfil.foto_perfil ? (
                    <img
                      src={perfil.foto_perfil}
                      alt={`${perfil.nombre} ${perfil.apellido}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span>{perfil.nombre?.charAt(0)}{perfil.apellido?.charAt(0)}</span>
                  )}
                </div>
                <h3 className="text-lg md:text-2xl font-black text-textPrimary text-center">
                  {perfil.nombre} {perfil.apellido}
                </h3>
                <p className="text-textSecondary text-[10px] md:text-sm">@{perfil.nombre_usuario}</p>
                {esMiPerfil && perfil.email && (
                  <p className="text-textSecondary text-[9px] md:text-xs mt-0.5">{perfil.email}</p>
                )}
              </div>

              {/* Rating y Categoría */}
              <div className="text-center mb-3 p-2 md:p-4 bg-primary/10 rounded-lg">
                <p className="text-textSecondary text-[10px] md:text-sm mb-0.5">Rating</p>
                <p className="text-2xl md:text-4xl font-black text-primary">{perfil.rating || 1200}</p>
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
                {perfil.posicion_preferida && (
                  <div className="flex items-center gap-1.5 text-textSecondary">
                    <Target size={12} className="text-primary md:w-3.5 md:h-3.5" />
                    <span className="capitalize">{perfil.posicion_preferida}</span>
                  </div>
                )}
                {perfil.mano_dominante && (
                  <div className="flex items-center gap-1.5 text-textSecondary">
                    <Hand size={12} className="text-secondary md:w-3.5 md:h-3.5" />
                    <span className="capitalize">{perfil.mano_dominante}</span>
                  </div>
                )}
                {perfil.ciudad && perfil.pais && (
                  <div className="flex items-center gap-1.5 text-textSecondary">
                    <MapPin size={12} className="text-primary md:w-3.5 md:h-3.5" />
                    <span>{perfil.ciudad}, {perfil.pais}</span>
                  </div>
                )}
                <div className="flex items-center gap-1.5 text-textSecondary">
                  <Calendar size={12} className="text-primary md:w-3.5 md:h-3.5" />
                  <span>Miembro desde {new Date(perfil.fecha_registro).getFullYear()}</span>
                </div>
              </div>
            </motion.div>

            {/* Card de Estadísticas Básicas */}
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

            {/* Card de Estadísticas Avanzadas (si están disponibles) */}
            {estadisticas && (
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
                      <span className="text-[10px] md:text-xs font-bold text-accent">{estadisticas.winrate_torneos}%</span>
                    </div>
                    <div className="h-2 bg-cardBorder rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-accent to-accent/60 rounded-full transition-all duration-500"
                        style={{ width: `${estadisticas.winrate_torneos}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-[10px] md:text-xs text-textSecondary flex items-center gap-1">
                        <Target size={12} className="text-primary" />
                        Amistosos
                      </span>
                      <span className="text-[10px] md:text-xs font-bold text-primary">{estadisticas.winrate_amistosos}%</span>
                    </div>
                    <div className="h-2 bg-cardBorder rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-primary to-primary/60 rounded-full transition-all duration-500"
                        style={{ width: `${estadisticas.winrate_amistosos}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Racha y Rating */}
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className={`rounded-lg p-2 text-center ${estadisticas?.racha_actual?.tipo === 'victorias' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                    <Flame size={14} className={`mx-auto mb-1 ${estadisticas?.racha_actual?.tipo === 'victorias' ? 'text-green-400' : 'text-red-400'}`} />
                    <p className={`text-lg md:text-xl font-black ${estadisticas?.racha_actual?.tipo === 'victorias' ? 'text-green-400' : 'text-red-400'}`}>
                      {estadisticas?.racha_actual?.cantidad || 0}
                    </p>
                    <p className="text-[9px] md:text-xs text-textSecondary">
                      Racha {estadisticas?.racha_actual?.tipo === 'victorias' ? 'Victorias' : 'Derrotas'}
                    </p>
                  </div>
                  <div className="bg-yellow-500/20 rounded-lg p-2 text-center">
                    <Trophy size={14} className="text-yellow-400 mx-auto mb-1" />
                    <p className="text-lg md:text-xl font-black text-yellow-400">{estadisticas?.mejor_racha || 0}</p>
                    <p className="text-[9px] md:text-xs text-textSecondary">Mejor Racha</p>
                  </div>
                </div>

                {/* Rating histórico */}
                <div className="grid grid-cols-3 gap-1.5 mb-3">
                  <div className="bg-cardBorder/30 rounded-lg p-1.5 text-center">
                    <TrendingUp size={12} className="text-green-400 mx-auto mb-0.5" />
                    <p className="text-sm md:text-base font-bold text-green-400">{estadisticas.mejor_rating}</p>
                    <p className="text-[8px] md:text-[10px] text-textSecondary">Máximo</p>
                  </div>
                  <div className="bg-cardBorder/30 rounded-lg p-1.5 text-center">
                    <TrendingDown size={12} className="text-red-400 mx-auto mb-0.5" />
                    <p className="text-sm md:text-base font-bold text-red-400">{estadisticas.peor_rating}</p>
                    <p className="text-[8px] md:text-[10px] text-textSecondary">Mínimo</p>
                  </div>
                  <div className={`rounded-lg p-1.5 text-center ${estadisticas.cambio_rating_total >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                    {estadisticas.cambio_rating_total >= 0 ? (
                      <TrendingUp size={12} className="text-green-400 mx-auto mb-0.5" />
                    ) : (
                      <TrendingDown size={12} className="text-red-400 mx-auto mb-0.5" />
                    )}
                    <p className={`text-sm md:text-base font-bold ${estadisticas.cambio_rating_total >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {estadisticas.cambio_rating_total >= 0 ? '+' : ''}{estadisticas.cambio_rating_total}
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
                        <span className="text-green-400">{estadisticas.sets_ganados}</span>
                        <span className="text-textSecondary mx-1">-</span>
                        <span className="text-red-400">{estadisticas.sets_perdidos}</span>
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-[9px] text-textSecondary">Games</p>
                      <p className="text-sm font-bold">
                        <span className="text-green-400">{estadisticas.games_ganados}</span>
                        <span className="text-textSecondary mx-1">-</span>
                        <span className="text-red-400">{estadisticas.games_perdidos}</span>
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
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
                {partidosMostrados.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="bg-cardBorder/30 rounded-lg p-8">
                      <Trophy size={48} className="mx-auto mb-4 text-textSecondary opacity-50" />
                      <p className="text-textPrimary font-bold mb-2">Sin partidos registrados</p>
                      <p className="text-textSecondary text-sm">
                        Los partidos de este jugador aparecerán aquí
                      </p>
                    </div>
                  </div>
                ) : (
                  partidosMostrados.map((partido, index) => {
                    const victoria = esVictoria(partido);
                    const miEquipo = obtenerEquipoUsuario(partido);
                    const rivalEquipo = obtenerEquipoRival(partido);

                    return (
                      <motion.div
                        key={partido.id_partido}
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
                        <div className="grid grid-cols-12 gap-2 md:gap-4 items-center">
                          {/* Equipo del jugador */}
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
                            <span className={`text-lg md:text-xl font-black ${
                              victoria ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {formatearSets(partido)}
                            </span>
                          </div>

                          {/* Equipo rival */}
                          <div className="col-span-5">
                            {rivalEquipo.map((jugador, i) => (
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
                        </div>
                      </motion.div>
                    );
                  })
                )}
              </div>

              {/* Botón Cargar Más */}
              {!mostrarTodos && partidosFiltrados.length > 10 && (
                <div className="mt-4 md:mt-6 text-center">
                  <Button
                    variant="primary"
                    onClick={() => setMostrarTodos(true)}
                    className="w-full md:w-auto"
                  >
                    Cargar más ({partidosFiltrados.length - 10} restantes)
                  </Button>
                </div>
              )}

              {mostrarTodos && partidosFiltrados.length > 10 && (
                <div className="mt-4 md:mt-6 text-center">
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setMostrarTodos(false);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    className="w-full md:w-auto"
                  >
                    Mostrar menos
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
