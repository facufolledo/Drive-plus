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

  return (
    <motion.div
      ref={ref}
      initial={shouldReduceMotion ? false : { opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={shouldReduceMotion ? {} : { y: -2 }}
      whileTap={{ scale: 0.98 }}
      className="group cursor-pointer"
      onClick={() => navigate(`/torneos/${torneo.id}`)}
    >
      <div className="relative bg-cardBg/95 backdrop-blur-sm rounded-lg p-2 md:p-4 border border-cardBorder group-hover:border-transparent transition-all duration-200 overflow-hidden h-full">
        {/* Glow effect on hover - solo desktop */}
        <div className={`hidden md:block absolute -inset-[1px] bg-gradient-to-br ${getEstadoColor()} opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-lg -z-10 blur-sm`} />
        
        <div className="relative z-10 flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between mb-1.5 md:mb-3 gap-1.5 md:gap-3">
            <div className="flex items-center gap-1.5 md:gap-3 min-w-0 flex-1">
              <div className={`bg-gradient-to-br ${getEstadoColor()} p-1 md:p-2 rounded flex-shrink-0`}>
                <Trophy className="text-white" size={14} />
                <Trophy className="text-white hidden md:block md:w-6 md:h-6" size={24} />
              </div>
              <h3 className="text-xs md:text-base font-bold text-textPrimary group-hover:text-white transition-colors truncate">
                {torneo.nombre}
              </h3>
            </div>
            
            {/* Estado badge */}
            <div className={`flex items-center gap-0.5 md:gap-1.5 px-1.5 md:px-3 py-0.5 md:py-1 rounded-full bg-gradient-to-r ${getEstadoColor()} text-white flex-shrink-0`}>
              {getEstadoIcon()}
            </div>
          </div>

          {/* Info */}
          <div className="space-y-1 md:space-y-2 mb-1.5 md:mb-3 flex-1">
            <div className="flex items-center gap-1 md:gap-2 text-textSecondary">
              <Calendar size={10} className="flex-shrink-0 md:w-4 md:h-4" />
              <span className="text-[9px] md:text-sm truncate">
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
              <div className="flex items-center gap-1 md:gap-2 text-textSecondary">
                <Users size={10} className="flex-shrink-0 md:w-4 md:h-4" />
                <span className="text-[9px] md:text-sm">
                  {torneo.participantes || 0} parejas
                </span>
              </div>
            )}

            {/* Categoría y Género */}
            <div className="flex items-center gap-1 md:gap-2 flex-wrap">
              <span className="px-1.5 md:px-3 py-0.5 md:py-1 rounded-full bg-primary/10 text-primary text-[8px] md:text-xs font-bold">
                {torneo.total_categorias && torneo.total_categorias > 1 
                  ? 'Categorías Varias' 
                  : torneo.categoria || 'Sin categoría'}
              </span>
              {torneo.genero && GENERO_LABELS[torneo.genero] && (
                <span className={`px-1.5 md:px-3 py-0.5 md:py-1 rounded-full bg-gradient-to-r ${GENERO_LABELS[torneo.genero].color} text-white text-[8px] md:text-xs font-bold`}>
                  {GENERO_LABELS[torneo.genero].icon}
                </span>
              )}
              {torneo.formato && FORMATO_LABELS[torneo.formato] && (
                <span className="text-[8px] md:text-xs text-textSecondary truncate">
                  {FORMATO_LABELS[torneo.formato]}
                </span>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-1.5 md:pt-3 border-t border-cardBorder mt-auto">
            <div className="text-textSecondary text-[9px] md:text-sm">
              {torneo.salasIds?.length || 0} {(torneo.salasIds?.length || 0) === 1 ? 'partido' : 'partidos'}
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/torneos/${torneo.id}`);
              }}
              className="text-[9px] md:text-sm px-1.5 md:px-4 py-0.5 md:py-2"
            >
              Ver
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
