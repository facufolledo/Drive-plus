import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Trophy, Minus, Medal, Filter, Search, TrendingUp, TrendingDown } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import Pagination from '../components/Pagination';
import LazyComponent from '../components/LazyComponent';
import { AdminId } from '../components/AdminBadge';
import { useDebounce } from '../hooks/useDebounce';

import { apiService } from '../services/api';
import { logger } from '../utils/logger';

// Categorías según la base de datos (masculino)
const CATEGORIAS = [
  { id: 7, nombre: 'Principiante', descripcion: 'Categoría para principiantes', ratingMin: 0, ratingMax: 499, color: 'from-slate-500 to-slate-600' },
  { id: 1, nombre: '8va', descripcion: 'Principiante / Princ. avanzado', ratingMin: 500, ratingMax: 999, color: 'from-gray-500 to-gray-600' },
  { id: 2, nombre: '7ma', descripcion: 'Golpes más sólidos', ratingMin: 1000, ratingMax: 1199, color: 'from-blue-500 to-blue-600' },
  { id: 3, nombre: '6ta', descripcion: 'Mejor dominio y estrategia', ratingMin: 1200, ratingMax: 1399, color: 'from-green-500 to-green-600' },
  { id: 4, nombre: '5ta', descripción: 'Buenos jugadores, constancia', ratingMin: 1400, ratingMax: 1599, color: 'from-yellow-500 to-yellow-600' },
  { id: 5, nombre: '4ta', descripcion: 'Muy buenos, técnica + estrategia', ratingMin: 1600, ratingMax: 1799, color: 'from-orange-500 to-orange-600' },
  { id: 6, nombre: 'Libre', descripcion: 'Élite local (top provincia)', ratingMin: 1800, ratingMax: 9999, color: 'from-purple-500 to-pink-500' },
];

function getCategoriaInfo(rating: number) {
  return CATEGORIAS.find(cat => rating >= cat.ratingMin && rating <= cat.ratingMax) || CATEGORIAS[0];
}

export default function Rankings() {
  const [filtroCategoria, setFiltroCategoria] = useState<string>('todas');
  const [filtroGenero, setFiltroGenero] = useState<string>('todos');
  const [busqueda, setBusqueda] = useState('');
  const [paginaActual, setPaginaActual] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);

  const [jugadores, setJugadores] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const ITEMS_POR_PAGINA = 20;
  const navigate = useNavigate();

  // Debounce para la búsqueda
  const debouncedBusqueda = useDebounce(busqueda, 300);



  // Recargar cuando cambien los filtros o la búsqueda
  useEffect(() => {
    const cargarRanking = async () => {
      try {
        setIsLoading(true);
        
        if (filtroCategoria === 'todas') {
          // Cargar ranking general con filtro de género
          const sexoParam = filtroGenero === 'masculino' ? 'masculino' : filtroGenero === 'femenino' ? 'femenino' : undefined;
          const rankingData = await apiService.getRankingGeneral(100, 0, sexoParam as any);
          setJugadores(rankingData);
        } else {
          // Buscar la categoría por nombre
          const categoria = CATEGORIAS.find(c => c.nombre === filtroCategoria);
          if (categoria) {
            const sexoParam = filtroGenero === 'masculino' ? 'masculino' : filtroGenero === 'femenino' ? 'femenino' : 'masculino';
            const categoriaData = await apiService.getRankingPorCategoria(categoria.id || 1, sexoParam as any);
            setJugadores(categoriaData.jugadores || []);
          }
        }
      } catch (error) {
        logger.error('Error al cargar ranking:', error);
        setJugadores([]);
      } finally {
        setIsLoading(false);
      }
    };

    cargarRanking();
    // Resetear página al cambiar filtros
    setPaginaActual(1);
  }, [filtroCategoria, filtroGenero, debouncedBusqueda]);

  // Filtrar jugadores localmente por búsqueda
  const jugadoresFiltrados = jugadores.filter(jugador => {
    const nombreCompleto = `${jugador.nombre || ''} ${jugador.apellido || ''}`.toLowerCase();
    const cumpleBusqueda = debouncedBusqueda === '' || 
                          nombreCompleto.includes(debouncedBusqueda.toLowerCase()) || 
                          (jugador.nombre_usuario || '').toLowerCase().includes(debouncedBusqueda.toLowerCase());
    
    return cumpleBusqueda;
  });

  // Calcular paginación
  const totalItems = jugadoresFiltrados.length;
  const totalPaginasCalculadas = Math.ceil(totalItems / ITEMS_POR_PAGINA);
  const indiceInicio = (paginaActual - 1) * ITEMS_POR_PAGINA;
  const indiceFin = indiceInicio + ITEMS_POR_PAGINA;
  const jugadoresPaginados = jugadoresFiltrados.slice(indiceInicio, indiceFin);

  // Actualizar total de páginas cuando cambien los filtros
  useEffect(() => {
    setTotalPaginas(totalPaginasCalculadas);
    if (paginaActual > totalPaginasCalculadas && totalPaginasCalculadas > 0) {
      setPaginaActual(1);
    }
  }, [totalPaginasCalculadas, paginaActual]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative"
      >
        <div className="flex items-center gap-2 md:gap-3 mb-1 md:mb-2">
          <div className="h-0.5 md:h-1 w-8 md:w-12 bg-gradient-to-r from-primary to-secondary rounded-full" />
          <h1 className="text-2xl md:text-5xl font-black text-textPrimary tracking-tight">
            Rankings
          </h1>
        </div>
        <p className="text-textSecondary text-xs md:text-base ml-10 md:ml-15">Tabla general de jugadores</p>
      </motion.div>

      {/* Información del sistema de categorías */}
      <Card gradient>
        <div className="mb-2 md:mb-4">
          <h2 className="text-sm md:text-xl font-bold text-textPrimary mb-1 md:mb-2">Sistema de Categorías</h2>
          <p className="text-textSecondary text-[10px] md:text-sm">
            El rating se calcula con el algoritmo ELO adaptado para pádel 2vs2. 
            Tu categoría se actualiza automáticamente según tu rating.
          </p>
        </div>
        <div className="grid grid-cols-4 md:grid-cols-4 lg:grid-cols-7 gap-1 md:gap-3">
          {CATEGORIAS.map((cat, index) => (
            <motion.div
              key={cat.nombre}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`bg-gradient-to-br ${cat.color} p-1.5 md:p-3 rounded-lg text-center`}
            >
              <p className="text-white font-black text-[10px] md:text-lg">{cat.nombre}</p>
              <p className="text-white/80 text-[8px] md:text-xs mt-0.5 md:mt-1">{cat.ratingMin}+</p>
            </motion.div>
          ))}
        </div>
      </Card>

      {/* Filtros y Búsqueda */}
      <div className="space-y-3">
        {/* Búsqueda */}
        <div className="relative">
          <Search className="absolute left-2 md:left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={16} />
          <Input
            type="text"
            placeholder="Buscar jugador..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="pl-8 md:pl-10 text-sm"
          />
        </div>

        {/* Filtro por Categoría */}
        <div className="flex items-center gap-1.5 md:gap-2 flex-wrap">
          <div className="flex items-center gap-1 md:gap-2 text-textSecondary">
            <Filter size={14} className="md:w-[18px] md:h-[18px]" />
            <span className="text-xs md:text-sm font-bold">Categoría:</span>
          </div>
          {['todas', ...CATEGORIAS.map(c => c.nombre)].map((cat) => (
            <Button
              key={cat}
              variant={filtroCategoria === cat ? 'primary' : 'secondary'}
              onClick={() => setFiltroCategoria(cat)}
              className="text-[10px] md:text-sm px-2 md:px-3 py-1 md:py-1.5"
            >
              {cat === 'todas' ? 'Todas' : cat}
            </Button>
          ))}
        </div>

        {/* Filtro por Género */}
        <div className="flex items-center gap-1.5 md:gap-2 flex-wrap">
          <div className="flex items-center gap-1 md:gap-2 text-textSecondary">
            <Filter size={14} className="md:w-[18px] md:h-[18px]" />
            <span className="text-xs md:text-sm font-bold">Género:</span>
          </div>
          {[
            { value: 'todos', label: 'Todos', icon: '🏆', color: 'from-purple-500 to-purple-600' },
            { value: 'masculino', label: 'Masculino', icon: '♂', color: 'from-blue-500 to-blue-600' },
            { value: 'femenino', label: 'Femenino', icon: '♀', color: 'from-pink-500 to-pink-600' }
          ].map((g, index) => (
            <motion.div
              key={g.value}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                variant={filtroGenero === g.value ? 'primary' : 'secondary'}
                onClick={() => setFiltroGenero(g.value)}
                className={`flex items-center gap-1 text-[10px] md:text-sm px-2 md:px-3 py-1 md:py-1.5 transition-all duration-300 ${
                  filtroGenero === g.value 
                    ? `bg-gradient-to-r ${g.color} text-white shadow-lg transform` 
                    : 'hover:shadow-md'
                }`}
              >
                <motion.span 
                  className="text-xs md:text-base"
                  animate={{ 
                    scale: filtroGenero === g.value ? 1.2 : 1,
                    rotate: filtroGenero === g.value ? [0, 10, -10, 0] : 0
                  }}
                  transition={{ duration: 0.3 }}
                >
                  {g.icon}
                </motion.span>
                <span className="hidden sm:inline">{g.label}</span>
              </Button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Tabla de Rankings */}
      <Card>
        <div className="flex items-center justify-between mb-4 md:mb-6">
          <h2 className="text-lg md:text-2xl font-bold text-textPrimary flex items-center gap-2">
            <Trophy className="text-accent w-5 h-5 md:w-7 md:h-7" />
            Top Jugadores
          </h2>
        </div>

        {/* Vista de tabla para desktop */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-cardBorder">
                <th className="text-left py-2 md:py-3 px-2 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider">Pos</th>
                <th className="text-left py-2 md:py-3 px-2 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider">Jugador</th>
                <th className="text-center py-2 md:py-3 px-1 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider hidden md:table-cell">Género</th>
                <th className="text-center py-2 md:py-3 px-2 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider">Rating</th>
                <th className="text-center py-2 md:py-3 px-1 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider hidden lg:table-cell">Categoría</th>
                <th className="text-center py-2 md:py-3 px-1 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider hidden md:table-cell">Partidos</th>
                <th className="text-center py-2 md:py-3 px-1 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider hidden lg:table-cell">Victorias</th>
                <th className="text-center py-2 md:py-3 px-1 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider hidden lg:table-cell">% Victoria</th>
                <th className="text-center py-2 md:py-3 px-1 md:px-4 text-textSecondary text-[10px] md:text-sm font-bold uppercase tracking-wider hidden xl:table-cell">Tendencia</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-textSecondary">
                    Cargando rankings...
                  </td>
                </tr>
              ) : jugadoresFiltrados.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-textSecondary">
                    No se encontraron jugadores
                  </td>
                </tr>
              ) : (
                jugadoresPaginados.map((jugador, index) => {
                  const catInfo = getCategoriaInfo(jugador.rating);
                  const nombreCompleto = `${jugador.nombre || ''} ${jugador.apellido || ''}`.trim() || jugador.nombre_usuario;
                  const partidosJugados = jugador.partidos_jugados || 0;
                  const partidosGanados = jugador.partidos_ganados || 0;
                  const porcentaje = partidosJugados > 0 ? Math.round((partidosGanados / partidosJugados) * 100) : 0;
                  
                  return (
                    <motion.tr
                      key={jugador.id_usuario || jugador.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.02 }}
                      className="border-b border-cardBorder hover:bg-cardBorder transition-colors"
                    >
                      <td className="py-2 md:py-4 px-2 md:px-4">
                        <div className="flex items-center gap-1 md:gap-2">
                          {(indiceInicio + index) === 0 && <Medal className="text-accent" size={14} />}
                          {(indiceInicio + index) === 1 && <Medal className="text-gray-400" size={14} />}
                          {(indiceInicio + index) === 2 && <Medal className="text-orange-400" size={14} />}
                          <span className="text-textPrimary font-bold text-sm md:text-lg">#{indiceInicio + index + 1}</span>
                        </div>
                      </td>
                      <td className="py-2 md:py-4 px-2 md:px-4">
                        <button 
                          onClick={() => {
                            // Navegar por username si existe, sino por ID
                            if (jugador.nombre_usuario && jugador.nombre_usuario.trim() !== '') {
                              navigate(`/jugador/${jugador.nombre_usuario}`);
                            } else if (jugador.id_usuario || jugador.id) {
                              navigate(`/perfil/${jugador.id_usuario || jugador.id}`);
                            }
                          }}
                          className="text-left hover:opacity-80 transition-opacity"
                        >
                          <div className="flex items-center gap-1">
                            <p className="text-textPrimary font-bold text-xs md:text-base truncate max-w-[120px] md:max-w-none hover:text-primary transition-colors">{nombreCompleto}</p>
                            <AdminId id={jugador.id_usuario || jugador.id} prefix="U" />
                          </div>
                          <p className="text-textSecondary text-[10px] md:text-xs truncate max-w-[120px] md:max-w-none">@{jugador.nombre_usuario || 'sin-usuario'}</p>
                        </button>
                      </td>
                      <td className="py-2 md:py-4 px-1 md:px-4 text-center hidden md:table-cell">
                        <span className={`inline-block px-2 md:px-3 py-0.5 md:py-1 rounded-full text-white font-bold text-xs md:text-sm ${
                          jugador.sexo === 'M' 
                            ? 'bg-gradient-to-r from-blue-500 to-blue-600' 
                            : 'bg-gradient-to-r from-pink-500 to-pink-600'
                        }`}>
                          {jugador.sexo === 'M' ? '♂' : '♀'}
                        </span>
                      </td>
                      <td className="py-2 md:py-4 px-2 md:px-4 text-center">
                        <span className="text-lg md:text-2xl font-black text-primary">{jugador.rating}</span>
                      </td>
                      <td className="py-2 md:py-4 px-1 md:px-4 text-center hidden lg:table-cell">
                        <span className={`inline-block px-2 md:px-3 py-0.5 md:py-1 rounded-full text-white font-bold text-xs md:text-sm bg-gradient-to-r ${catInfo.color}`}>
                          {catInfo.nombre}
                        </span>
                      </td>
                      <td className="py-2 md:py-4 px-1 md:px-4 text-center hidden md:table-cell">
                        <span className="text-textPrimary font-semibold text-xs md:text-base">{partidosJugados}</span>
                      </td>
                      <td className="py-2 md:py-4 px-1 md:px-4 text-center hidden lg:table-cell">
                        <span className="text-secondary font-semibold text-xs md:text-base">{partidosGanados}</span>
                      </td>
                      <td className="py-2 md:py-4 px-1 md:px-4 text-center hidden lg:table-cell">
                        <span className="text-textPrimary font-semibold text-xs md:text-base">{porcentaje}%</span>
                      </td>
                      <td className="py-2 md:py-4 px-1 md:px-4 text-center hidden xl:table-cell">
                        <div className="flex items-center justify-center gap-1">
                          {jugador.tendencia === 'up' && (
                            <>
                              <TrendingUp className="text-green-500" size={16} />
                              <span className="text-green-500 font-bold text-xs">↑</span>
                            </>
                          )}
                          {jugador.tendencia === 'down' && (
                            <>
                              <TrendingDown className="text-red-500" size={16} />
                              <span className="text-red-500 font-bold text-xs">↓</span>
                            </>
                          )}
                          {(jugador.tendencia === 'stable' || jugador.tendencia === 'neutral' || !jugador.tendencia) && (
                            <>
                              <Minus className="text-textSecondary" size={16} />
                              <span className="text-textSecondary font-bold text-xs">→</span>
                            </>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Vista de cards para móvil */}
        <motion.div 
          className="md:hidden space-y-2"
          key={filtroGenero + filtroCategoria} // Re-animar cuando cambien los filtros
        >
          {isLoading ? (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="py-8 text-center text-textSecondary text-sm"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full mb-2"
              />
              <p>Cargando rankings...</p>
            </motion.div>
          ) : jugadoresFiltrados.length === 0 ? (
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="py-8 text-center text-textSecondary text-sm"
            >
              No se encontraron jugadores
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ staggerChildren: 0.05 }}
            >
              {jugadoresPaginados.map((jugador, index) => {
              const catInfo = getCategoriaInfo(jugador.rating);
              const nombreCompleto = `${jugador.nombre || ''} ${jugador.apellido || ''}`.trim() || jugador.nombre_usuario;
              const partidosJugados = jugador.partidos_jugados || 0;
              const partidosGanados = jugador.partidos_ganados || 0;
              const porcentaje = partidosJugados > 0 ? Math.round((partidosGanados / partidosJugados) * 100) : 0;
              
              return (
                <motion.div
                  key={jugador.id_usuario || jugador.id}
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ 
                    delay: index * 0.05,
                    type: "spring",
                    stiffness: 100,
                    damping: 15
                  }}
                  whileHover={{ 
                    scale: 1.02,
                    boxShadow: "0 8px 25px rgba(0,0,0,0.15)"
                  }}
                  className="bg-cardBg/50 rounded-lg p-2 border border-cardBorder hover:border-primary/30 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    {/* Posición y medalla */}
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {(indiceInicio + index) === 0 && <Medal className="text-accent" size={14} />}
                      {(indiceInicio + index) === 1 && <Medal className="text-gray-400" size={14} />}
                      {(indiceInicio + index) === 2 && <Medal className="text-orange-400" size={14} />}
                      <span className="text-textPrimary font-bold text-sm">#{indiceInicio + index + 1}</span>
                    </div>

                    {/* Nombre y usuario */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1">
                        <p className="text-textPrimary font-bold text-xs truncate">{nombreCompleto}</p>
                        <AdminId id={jugador.id_usuario || jugador.id} prefix="U" />
                      </div>
                      <p className="text-textSecondary text-[9px] truncate">@{jugador.nombre_usuario}</p>
                    </div>

                    {/* Rating destacado */}
                    <div className="text-right flex-shrink-0">
                      <p className="text-xl font-black text-primary">{jugador.rating}</p>
                      <span className={`inline-block px-1.5 py-0.5 rounded-full text-white font-bold text-[8px] bg-gradient-to-r ${catInfo.color}`}>
                        {catInfo.nombre}
                      </span>
                    </div>
                  </div>

                  {/* Estadísticas en fila */}
                  <div className="flex items-center justify-between text-[9px] pt-1.5 border-t border-cardBorder/50">
                    <div className="text-center">
                      <p className="text-textSecondary mb-0.5">Género</p>
                      <span className={`inline-block px-1.5 py-0.5 rounded-full text-white font-bold text-[9px] ${
                        jugador.sexo === 'M' 
                          ? 'bg-gradient-to-r from-blue-500 to-blue-600' 
                          : 'bg-gradient-to-r from-pink-500 to-pink-600'
                      }`}>
                        {jugador.sexo === 'M' ? '♂' : '♀'}
                      </span>
                    </div>
                    <div className="text-center">
                      <p className="text-textSecondary mb-0.5">Partidos</p>
                      <p className="text-textPrimary font-bold text-xs">{partidosJugados}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-textSecondary mb-0.5">Victorias</p>
                      <p className="text-secondary font-bold text-xs">{partidosGanados}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-textSecondary mb-0.5">% Win</p>
                      <p className="text-accent font-bold text-xs">{porcentaje}%</p>
                    </div>
                  </div>
                </motion.div>
              );
              })}
            </motion.div>
          )}
        </motion.div>

        {/* Paginación */}
        <Pagination
          currentPage={paginaActual}
          totalPages={totalPaginas}
          onPageChange={setPaginaActual}
          totalItems={totalItems}
          itemsPerPage={ITEMS_POR_PAGINA}
        />
      </Card>

      {/* Información adicional */}
      <LazyComponent delay={200}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-6">
          <Card>
            <h3 className="text-sm md:text-lg font-bold text-textPrimary mb-1.5 md:mb-3">¿Cómo funciona?</h3>
            <ul className="space-y-0.5 md:space-y-2 text-textSecondary text-[10px] md:text-sm">
              <li>• El rating inicial depende de tu categoría declarada</li>
              <li>• Ganas puntos al vencer rivales de mayor nivel</li>
              <li>• El margen de victoria afecta los puntos ganados</li>
              <li>• Tu categoría se actualiza automáticamente</li>
            </ul>
          </Card>

          <Card>
            <h3 className="text-sm md:text-lg font-bold text-textPrimary mb-1.5 md:mb-3">Factor K</h3>
            <ul className="space-y-0.5 md:space-y-2 text-textSecondary text-[10px] md:text-sm">
              <li>• Nuevo (&lt;15 partidos): K = 32</li>
              <li>• Intermedio (15-59): K = 24</li>
              <li>• Experto (≥60): K = 18</li>
              <li>• Más partidos = cambios más estables</li>
            </ul>
          </Card>

          <Card>
            <h3 className="text-sm md:text-lg font-bold text-textPrimary mb-1.5 md:mb-3">Caps de Rating</h3>
            <ul className="space-y-0.5 md:space-y-2 text-textSecondary text-[10px] md:text-sm">
              <li>• Ganador favorito: +22 máx</li>
              <li>• Ganador no favorito: +40 máx</li>
              <li>• Perdedor favorito: -40 mín</li>
              <li>• Perdedor no favorito: -18 mín</li>
            </ul>
          </Card>
        </div>
      </LazyComponent>


    </div>
  );
}
