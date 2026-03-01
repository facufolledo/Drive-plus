import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Medal, Award, TrendingUp, Users } from 'lucide-react';
import Card from '../components/Card';
import RatingProgressBar from '../components/RatingProgressBar';
import { apiService } from '../services/api';
import { logger } from '../utils/logger';

type Categoria = '8va' | '7ma' | '6ta' | '5ta' | '4ta' | '3ra';
type Genero = 'masculino' | 'femenino' | 'mixto';

interface Jugador {
  posicion: number;
  nombre: string;
  rating: number;
  partidosJugados: number;
  partidosGanados: number;
  winRate: number;
  cambioSemanal: number;
}

export default function RankingsCategorias() {
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState<Categoria>('6ta');
  const [generoSeleccionado, setGeneroSeleccionado] = useState<Genero>('masculino');
  const [mostrarTodos, setMostrarTodos] = useState(false);
  const [jugadores, setJugadores] = useState<Jugador[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const LIMITE_INICIAL = 20;

  // Mapeo de categorías a IDs del backend
  const categoriaIds: Record<Categoria, number> = {
    'Principiante': 7,
    '8va': 1,
    '7ma': 2,
    '6ta': 3,
    '5ta': 4,
    '4ta': 5,
    '3ra': 6,
  };

  // Cargar jugadores cuando cambie categoría o género
  useEffect(() => {
    const cargarJugadores = async () => {
      try {
        setIsLoading(true);
        const categoriaId = categoriaIds[categoriaSeleccionada];
        const sexo = generoSeleccionado === 'masculino' ? 'masculino' : generoSeleccionado === 'femenino' ? 'femenino' : 'masculino';
        
        const response = await apiService.getRankingPorCategoria(categoriaId, sexo as any);
        
        // Transformar datos del backend al formato del componente
        const jugadoresTransformados = (response.jugadores || []).map((j: any, index: number) => ({
          posicion: index + 1,
          nombre: `${j.nombre || ''} ${j.apellido || ''}`.trim() || j.nombre_usuario,
          rating: j.rating || 0,
          partidosJugados: j.partidos_jugados || 0,
          partidosGanados: j.partidos_ganados || 0,
          winRate: j.partidos_jugados > 0 ? Math.round((j.partidos_ganados / j.partidos_jugados) * 100) : 0,
          cambioSemanal: 0, // TODO: Implementar en backend
        }));
        
        setJugadores(jugadoresTransformados);
      } catch (error) {
        logger.error('Error al cargar ranking por categoría:', error);
        setJugadores([]);
      } finally {
        setIsLoading(false);
      }
    };

    cargarJugadores();
  }, [categoriaSeleccionada, generoSeleccionado]);

  const categorias: { id: Categoria; nombre: string; rango: string; color: string; bgColor: string; textColor: string; icon: any }[] = [
    { 
      id: '8va', 
      nombre: '8va', 
      rango: 'Principiante', 
      color: 'from-amber-700/40 to-orange-800/40',
      bgColor: 'bg-amber-900/20',
      textColor: 'text-amber-700',
      icon: Medal 
    },
    { 
      id: '7ma', 
      nombre: '7ma', 
      rango: 'Intermedio Bajo', 
      color: 'from-slate-400/40 to-slate-600/40',
      bgColor: 'bg-slate-500/20',
      textColor: 'text-slate-400',
      icon: Medal 
    },
    { 
      id: '6ta', 
      nombre: '6ta', 
      rango: 'Intermedio', 
      color: 'from-yellow-600/40 to-amber-600/40',
      bgColor: 'bg-yellow-700/20',
      textColor: 'text-yellow-600',
      icon: Trophy 
    },
    { 
      id: '5ta', 
      nombre: '5ta', 
      rango: 'Intermedio Alto', 
      color: 'from-cyan-400/40 to-teal-500/40',
      bgColor: 'bg-cyan-500/20',
      textColor: 'text-cyan-400',
      icon: Award 
    },
    { 
      id: '4ta', 
      nombre: '4ta', 
      rango: 'Avanzado', 
      color: 'from-blue-400/40 to-indigo-500/40',
      bgColor: 'bg-blue-500/20',
      textColor: 'text-blue-400',
      icon: Trophy 
    },
    { 
      id: '3ra', 
      nombre: '3ra', 
      rango: 'Profesional', 
      color: 'from-purple-400/40 to-pink-500/40',
      bgColor: 'bg-purple-500/20',
      textColor: 'text-purple-400',
      icon: Trophy 
    },
  ];

  const jugadoresMostrados = mostrarTodos ? jugadores : jugadores.slice(0, LIMITE_INICIAL);
  const categoriaActual = categorias.find(c => c.id === categoriaSeleccionada)!;
  const hayMasJugadores = jugadores.length > LIMITE_INICIAL;

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 md:gap-4"
      >
        <div>
          <div className="flex items-center gap-2 md:gap-3 mb-1 md:mb-2">
            <div className="h-0.5 md:h-1 w-8 md:w-12 bg-gradient-to-r from-primary to-secondary rounded-full" />
            <h1 className="text-2xl md:text-5xl font-black text-textPrimary tracking-tight">
              Rankings por Categoría
            </h1>
          </div>
          <p className="text-textSecondary text-xs md:text-base ml-10 md:ml-15">
            Mejores jugadores de cada categoría
          </p>
        </div>
      </motion.div>

      {/* Filtro de Género */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex gap-2 md:gap-3"
      >
        {(['masculino', 'femenino', 'mixto'] as Genero[]).map((genero) => (
          <button
            key={genero}
            onClick={() => setGeneroSeleccionado(genero)}
            className={`px-4 md:px-6 py-2 md:py-3 rounded-lg md:rounded-xl text-sm md:text-base font-bold transition-all active:scale-95 ${
              generoSeleccionado === genero
                ? 'bg-primary text-white'
                : 'bg-cardBg text-textSecondary hover:bg-cardBorder'
            }`}
          >
            {genero.charAt(0).toUpperCase() + genero.slice(1)}
          </button>
        ))}
      </motion.div>

      {/* Tabs de Categorías */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-3 md:flex md:flex-wrap gap-2 md:gap-3"
      >
        {categorias.map((categoria, index) => {
          const Icon = categoria.icon;
          return (
            <button
              key={categoria.id}
              onClick={() => setCategoriaSeleccionada(categoria.id)}
              className={`flex flex-col md:flex-row items-center justify-center gap-1 md:gap-3 px-2 md:px-6 py-2 md:py-4 rounded-lg md:rounded-xl text-sm md:text-base font-bold transition-all active:scale-95 ${
                categoriaSeleccionada === categoria.id
                  ? `${categoria.bgColor} ${categoria.textColor} border-2 ${categoria.textColor.replace('text-', 'border-')}`
                  : 'bg-cardBg text-textSecondary hover:bg-cardBorder border-2 border-transparent'
              }`}
            >
              <Icon size={16} className="md:w-5 md:h-5 flex-shrink-0" />
              <div className="text-center md:text-left">
                <p className="text-xs md:text-sm font-bold">{categoria.nombre}</p>
                <p className="text-[9px] md:text-xs opacity-80 hidden md:block">{categoria.rango}</p>
              </div>
            </button>
          );
        })}
      </motion.div>

      {/* Estadísticas de la Categoría */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className={categoriaActual.bgColor}>
          <div className="p-3 md:p-6">
            <div className="flex items-center gap-2 md:gap-4 mb-2 md:mb-4">
              <div className={`w-10 h-10 md:w-16 md:h-16 rounded-full ${categoriaActual.bgColor} border-2 ${categoriaActual.textColor.replace('text-', 'border-')} flex items-center justify-center flex-shrink-0`}>
                <categoriaActual.icon size={20} className={`${categoriaActual.textColor} md:w-8 md:h-8`} />
              </div>
              <div className="min-w-0">
                <h2 className="text-lg md:text-3xl font-black text-textPrimary">{categoriaActual.nombre}</h2>
                <p className="text-textSecondary text-[10px] md:text-base truncate">Rango: {categoriaActual.rango}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 md:gap-6 mt-2 md:mt-6">
              <div className="text-center">
                <p className="text-xl md:text-3xl font-black text-primary">{jugadores.length}</p>
                <p className="text-textSecondary text-[9px] md:text-sm">Jugadores</p>
              </div>
              <div className="text-center">
                <p className="text-xl md:text-3xl font-black text-secondary">{jugadores[0]?.rating || 0}</p>
                <p className="text-textSecondary text-[9px] md:text-sm">Rating Máx</p>
              </div>
              <div className="text-center">
                <p className="text-xl md:text-3xl font-black text-accent">{jugadores.length > 0 ? Math.round(jugadores.reduce((acc, j) => acc + j.rating, 0) / jugadores.length) : 0}</p>
                <p className="text-textSecondary text-[9px] md:text-sm">Rating Prom.</p>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Top 3 Destacado */}
      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-textSecondary">Cargando rankings...</p>
        </div>
      ) : jugadores.length === 0 ? (
        <div className="text-center py-12">
          <Card>
            <div className="p-8">
              <Trophy size={48} className="mx-auto mb-4 text-textSecondary opacity-50" />
              <p className="text-textPrimary font-bold mb-2">No hay jugadores en esta categoría</p>
              <p className="text-textSecondary text-sm">Intenta con otra categoría o género</p>
            </div>
          </Card>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-6">
            {jugadoresMostrados.slice(0, 3).map((jugador, index) => (
          <motion.div
            key={jugador.posicion}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 + index * 0.1 }}
          >
            <Card className={index === 0 ? `border-2 ${categoriaActual.textColor.replace('text-', 'border-')}` : ''}>
              <div className="p-3 md:p-6 text-center">
                <div className="relative inline-block mb-2 md:mb-4">
                  <div className={`w-14 h-14 md:w-20 md:h-20 rounded-full ${categoriaActual.bgColor} border-2 ${categoriaActual.textColor.replace('text-', 'border-')} flex items-center justify-center ${categoriaActual.textColor} text-xl md:text-3xl font-black`}>
                    {jugador.posicion}
                  </div>
                  {index === 0 && (
                    <div className={`absolute -top-1 -right-1 md:-top-2 md:-right-2 w-5 h-5 md:w-8 md:h-8 ${categoriaActual.bgColor} border-2 ${categoriaActual.textColor.replace('text-', 'border-')} rounded-full flex items-center justify-center`}>
                      <Trophy size={10} className={`${categoriaActual.textColor} md:w-4 md:h-4`} />
                    </div>
                  )}
                </div>

                <h3 className="text-sm md:text-xl font-bold text-textPrimary mb-1 md:mb-2 truncate px-1">{jugador.nombre}</h3>
                
                <div className="mb-2 md:mb-4">
                  <p className="text-2xl md:text-4xl font-black text-primary mb-0.5 md:mb-1">{jugador.rating}</p>
                  <div className="flex items-center justify-center gap-1">
                    <TrendingUp size={12} className="text-secondary md:w-4 md:h-4" />
                    <span className="text-secondary font-bold text-xs md:text-base">+{jugador.cambioSemanal}</span>
                  </div>
                </div>

                <div className="px-2">
                  <RatingProgressBar
                    currentRating={jugador.rating}
                    size="sm"
                    showLabel={false}
                  />
                </div>

                <div className="grid grid-cols-2 gap-2 md:gap-4 mt-2 md:mt-4 pt-2 md:pt-4 border-t border-cardBorder">
                  <div>
                    <p className="text-lg md:text-2xl font-bold text-textPrimary">{jugador.partidosGanados}</p>
                    <p className="text-[9px] md:text-xs text-textSecondary">Victorias</p>
                  </div>
                  <div>
                    <p className="text-lg md:text-2xl font-bold text-textPrimary">{jugador.partidosJugados}</p>
                    <p className="text-[9px] md:text-xs text-textSecondary">Partidos</p>
                  </div>
                </div>
              </div>
            </Card>
            </motion.div>
          ))}
        </div>

        {/* Resto del Ranking */}
        {jugadoresMostrados.length > 3 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <Card>
            <div className="p-3 md:p-6">
              <h3 className="text-sm md:text-xl font-bold text-textPrimary mb-3 md:mb-6 flex items-center gap-2">
                <Users size={16} className="md:w-6 md:h-6" />
                Resto del Ranking
              </h3>

              <div className="space-y-2 md:space-y-3">
                {jugadoresMostrados.slice(3).map((jugador, index) => (
                  <motion.div
                    key={jugador.posicion}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.9 + index * 0.02 }}
                    className="flex items-center justify-between p-2 md:p-4 bg-background rounded-lg md:rounded-xl border border-cardBorder hover:border-primary/50 transition-colors active:scale-[0.98]"
                  >
                    <div className="flex items-center gap-2 md:gap-4 flex-1 min-w-0">
                      <div className="w-8 h-8 md:w-12 md:h-12 rounded-full bg-cardBorder flex items-center justify-center text-textPrimary font-bold text-xs md:text-base flex-shrink-0">
                        {jugador.posicion}
                      </div>
                      <div className="min-w-0">
                        <p className="text-textPrimary font-semibold text-xs md:text-base truncate">{jugador.nombre}</p>
                        <p className="text-textSecondary text-[9px] md:text-sm">{jugador.partidosJugados} partidos</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 md:gap-6 flex-shrink-0">
                      <div className="text-right">
                        <p className="text-lg md:text-2xl font-bold text-primary">{jugador.rating}</p>
                        <p className="text-secondary text-[9px] md:text-sm font-bold">+{jugador.cambioSemanal}</p>
                      </div>
                      <div className="text-right hidden md:block">
                        <p className="text-lg font-bold text-textPrimary">{jugador.partidosGanados}</p>
                        <p className="text-textSecondary text-xs">Victorias</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

                {/* Botón Cargar Más */}
                {!mostrarTodos && hayMasJugadores && (
                  <div className="mt-6 text-center">
                    <button
                      onClick={() => setMostrarTodos(true)}
                      className="w-full py-3 bg-cardBorder hover:bg-primary/20 text-textPrimary font-bold rounded-lg transition-colors"
                    >
                      Cargar más jugadores ({jugadores.length - LIMITE_INICIAL} restantes)
                    </button>
                  </div>
                )}

              {mostrarTodos && hayMasJugadores && (
                <div className="mt-6 text-center">
                  <button
                    onClick={() => {
                        setMostrarTodos(false);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                      className="w-full py-3 bg-cardBorder hover:bg-primary/20 text-textPrimary font-bold rounded-lg transition-colors"
                    >
                      Mostrar menos
                    </button>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        )}
      </>
      )}
    </div>
  );
}
