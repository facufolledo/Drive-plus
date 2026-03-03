import { forwardRef, memo } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Trophy, Calendar, Users, Play, CheckCircle, Clock } from 'lucide-react';
import { Torneo } from '../utils/types';
import Button from './Button';
import { useAuth } from '../context/AuthContext';

interface TorneoCardProps {
  torneo: Torneo;
}

const FORMATO_LABELS: Record<string, string> = {
  'eliminacion-simple': 'Eliminación Simple',
  'eliminacion-doble': 'Eliminación Doble',
  'round-robin': 'Round Robin',
  'grupos': 'Por Grupos',
  'por-puntos': 'Por Puntos',
};

const GENERO_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  'masculino': { label: 'Masculino', icon: '♂', color: 'from-blue-500 to-blue-600' },
  'femenino': { label: 'Femenino', icon: '♀', color: 'from-pink-500 to-pink-600' },
  'mixto': { label: 'Mixto', icon: '⚥', color: 'from-purple-500 to-purple-600' },
};

const TorneoCard = forwardRef<HTMLDivElement, TorneoCardProps>(({ torneo }, ref) => {
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();
  const { usuario } = useAuth();
  
  // Verificar si el usuario es administrador
  const esAdmin = usuario?.es_administrador === true;
  
  // Helper para parsear fechas sin problemas de zona horaria
  const parseFechaSinZonaHoraria = (fechaISO: string): Date => {
    const [year, month, day] = fechaISO.split('-').map(Number);
    return new Date(year, month - 1, day);
  };
  
  const getEstadoColor = () => {
    switch (torneo.estado) {
      case 'activo':
        return 'from-secondary to-pink-600';
      case 'finalizado':
        return 'from-accent to-yellow-500';
      case 'programado':
        return 'from-primary to-blue-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  const getEstadoIcon = () => {
    switch (torneo.estado) {
      case 'activo':
        return <Play size={12} className="md:w-4 md:h-4" />;
      case 'finalizado':
        return <CheckCircle size={12} className="md:w-4 md:h-4" />;
      case 'programado':
        return <Clock size={12} className="md:w-4 md:h-4" />;
    }
  };

  const getEstadoLabel = () => {
    switch (torneo.estado) {
      case 'activo':
        return 'En Curso';
      case 'finalizado':
        return 'Finalizado';
      case 'programado':
        return 'Próximo';
      default:
        return '';
    }
  };

  return (
    <motion.div
      ref={ref}
      initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={shouldReduceMotion ? {} : { y: -4, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
      className="group cursor-pointer"
      onClick={() => navigate(`/torneos/${torneo.id}`)}
    >
      <div className={`relative bg-cardBg/95 backdrop-blur-sm rounded-xl p-3 md:p-5 border border-cardBorder group-hover:border-transparent transition-all duration-300 overflow-hidden h-full ${
        torneo.estado === 'finalizado' ? 'opacity-90' : ''
      }`}>
        {/* Overlay gris sutil para finalizados */}
        {torneo.estado === 'finalizado' && (
          <div className="absolute inset-0 bg-gray-900/10 pointer-events-none" />
        )}
        
        {/* Glow effect on hover */}
        <div className={`hidden md:block absolute -inset-[1px] bg-gradient-to-br ${getEstadoColor()} opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl -z-10 blur-md`} />
        
        <div className="relative z-10 flex flex-col h-full">
          {/* Header */}
          <div className="flex items-start gap-2 md:gap-4 mb-2 md:mb-4">
            <div className={`bg-gradient-to-br ${getEstadoColor()} p-1.5 md:p-3 rounded-lg flex-shrink-0 shadow-lg`}>
              <Trophy className="text-white" size={18} />
              <Trophy className="text-white hidden md:block md:w-8 md:h-8" size={32} />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-sm md:text-xl font-black text-textPrimary group-hover:text-white transition-colors mb-1 leading-tight bg-gradient-to-r from-textPrimary to-textPrimary/80 bg-clip-text group-hover:from-white group-hover:to-white/90" style={{ textShadow: '0 0 20px rgba(255,255,255,0.1)' }}>
                {torneo.nombre}
              </h3>
              {/* Estado label pequeño */}
              <div className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[8px] md:text-[10px] font-bold ${
                torneo.estado === 'activo' 
                  ? 'bg-secondary/10 text-secondary' 
                  : torneo.estado === 'finalizado'
                  ? 'bg-accent/10 text-accent'
                  : 'bg-primary/10 text-primary'
              }`}>
                {getEstadoIcon()}
                <span>{getEstadoLabel()}</span>
              </div>
            </div>
          </div>

          {/* Info */}
          <div className="space-y-2 md:space-y-2.5 mb-2 md:mb-4 flex-1">
            <div className="flex items-center gap-1.5 md:gap-2 text-textSecondary">
              <Calendar size={12} className="flex-shrink-0 md:w-4 md:h-4" />
              <span className="text-[10px] md:text-sm truncate">
                {parseFechaSinZonaHoraria(torneo.fechaInicio).toLocaleDateString('es-ES', { 
                  day: 'numeric', 
                  month: 'short' 
                })} - {parseFechaSinZonaHoraria(torneo.fechaFin).toLocaleDateString('es-ES', { 
                  day: 'numeric', 
                  month: 'short'
                })}
              </span>
            </div>
            
            {/* Parejas inscriptas - Solo visible para administradores */}
            {esAdmin && (
              <div className="flex items-center gap-1.5 md:gap-2 text-textSecondary">
                <Users size={12} className="flex-shrink-0 md:w-4 md:h-4" />
                <span className="text-[10px] md:text-sm">
                  {torneo.participantes || 0} parejas
                </span>
              </div>
            )}

            {/* Categoría y Género */}
            <div className="flex flex-col gap-1.5">
              {/* Si tiene categorías, mostrarlas separadas por género */}
              {torneo.categorias && torneo.categorias.length > 0 ? (
                <>
                  {/* Categorías Masculinas */}
                  {torneo.categorias.filter(c => c.genero === 'masculino').length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className="text-[9px] md:text-xs text-blue-400 font-bold">♂</span>
                      {torneo.categorias
                        .filter(c => c.genero === 'masculino')
                        .map((cat, idx) => (
                          <span
                            key={`masc-${idx}`}
                            className="px-1.5 md:px-2 py-0.5 md:py-1 rounded-full bg-blue-500/10 text-blue-400 text-[8px] md:text-[10px] font-bold"
                          >
                            {cat.nombre}
                          </span>
                        ))}
                    </div>
                  )}
                  
                  {/* Categorías Femeninas */}
                  {torneo.categorias.filter(c => c.genero === 'femenino').length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className="text-[9px] md:text-xs text-pink-400 font-bold">♀</span>
                      {torneo.categorias
                        .filter(c => c.genero === 'femenino')
                        .map((cat, idx) => (
                          <span
                            key={`fem-${idx}`}
                            className="px-1.5 md:px-2 py-0.5 md:py-1 rounded-full bg-pink-500/10 text-pink-400 text-[8px] md:text-[10px] font-bold"
                          >
                            {cat.nombre}
                          </span>
                        ))}
                    </div>
                  )}
                  
                  {/* Categorías Mixtas */}
                  {torneo.categorias.filter(c => c.genero === 'mixto').length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className="text-[9px] md:text-xs text-purple-400 font-bold">⚥</span>
                      {torneo.categorias
                        .filter(c => c.genero === 'mixto')
                        .map((cat, idx) => (
                          <span
                            key={`mixto-${idx}`}
                            className="px-1.5 md:px-2 py-0.5 md:py-1 rounded-full bg-purple-500/10 text-purple-400 text-[8px] md:text-[10px] font-bold"
                          >
                            {cat.nombre}
                          </span>
                        ))}
                    </div>
                  )}
                </>
              ) : (
                /* Fallback: mostrar categoría única si no hay array de categorías */
                <div className="flex items-center gap-1.5 md:gap-2 flex-wrap">
                  <span className="px-2 md:px-3 py-1 md:py-1.5 rounded-full bg-primary/10 text-primary text-[9px] md:text-xs font-bold">
                    {torneo.categoria || 'Sin categoría'}
                  </span>
                  {torneo.genero && GENERO_LABELS[torneo.genero] && (
                    <span className={`px-2 md:px-3 py-1 md:py-1.5 rounded-full bg-gradient-to-r ${GENERO_LABELS[torneo.genero].color} text-white text-[9px] md:text-xs font-bold`}>
                      {GENERO_LABELS[torneo.genero].icon}
                    </span>
                  )}
                </div>
              )}
              
              {/* Formato */}
              {torneo.formato && FORMATO_LABELS[torneo.formato] && (
                <span className="text-[9px] md:text-xs text-textSecondary">
                  {FORMATO_LABELS[torneo.formato]}
                </span>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end pt-2 md:pt-3 border-t border-cardBorder/50 mt-auto" style={{ borderImage: 'linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent) 1' }}>
            <Button
              variant="primary"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/torneos/${torneo.id}`);
              }}
              className="text-[10px] md:text-sm px-2 md:px-5 py-1 md:py-2.5 font-bold"
            >
              Ver Detalles
            </Button>
          </div>
        </div>
      </div>
    </motion.div>
  );
});

TorneoCard.displayName = 'TorneoCard';

// OPTIMIZACIÓN MOBILE: Memoizar para evitar re-renders innecesarios
export default memo(TorneoCard);
