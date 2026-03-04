import { motion } from 'framer-motion';
import { Crown, Users, Clock, Calendar, ChevronDown } from 'lucide-react';
import Button from '../Button';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

interface MiSala {
  id: number;
  nombre: string;
  estado: 'esperando' | 'en_juego' | 'finalizada';
  jugadores_actuales: number;
  jugadores_maximos: number;
  fecha: string;
  hora: string;
  es_organizador: boolean;
  tiempo_transcurrido?: string;
}

interface MisSalasSectionProps {
  salas: any[];
  onEntrarSala: (salaId: number) => void;
  onVerPartido: (salaId: number) => void;
  loading?: boolean;
}

export default function MisSalasSection({ salas, onEntrarSala, onVerPartido, loading }: MisSalasSectionProps) {
  const { usuario } = useAuth();
  const [expandido, setExpandido] = useState(false);

  // Convertir salas del formato actual al formato esperado
  const misSalasFormateadas: MiSala[] = salas.map(sala => {
    // Mapear estados correctamente
    let estadoMapeado: 'esperando' | 'en_juego' | 'finalizada';
    
    switch (sala.estado) {
      case 'esperando':
      case 'pendiente':
        estadoMapeado = 'esperando';
        break;
      case 'activa':
      case 'en_juego':
      case 'jugando':
        estadoMapeado = 'en_juego';
        break;
      case 'finalizada':
      case 'terminada':
      case 'completada':
        estadoMapeado = 'finalizada';
        break;
      default:
        // Si no reconocemos el estado, usar el estado original o 'esperando' por defecto
        estadoMapeado = sala.estado === 'finalizada' ? 'finalizada' : 'esperando';
    }

    return {
      id: parseInt(sala.id),
      nombre: sala.nombre || `Sala #${sala.id}`,
      estado: estadoMapeado,
      jugadores_actuales: sala.jugadores?.length || 0,
      jugadores_maximos: sala.max_jugadores || 4,
      fecha: new Date(sala.fecha_creacion || Date.now()).toLocaleDateString('es-AR', { 
        day: '2-digit', 
        month: 'short' 
      }),
      hora: new Date(sala.fecha_creacion || Date.now()).toLocaleTimeString('es-AR', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      es_organizador: sala.creador_id === usuario?.id_usuario?.toString() || sala.creador_id === usuario?.id_usuario,
      tiempo_transcurrido: estadoMapeado === 'en_juego' ? 'En curso' : undefined
    };
  });

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'esperando': return 'text-yellow-400 bg-yellow-400/20';
      case 'en_juego': return 'text-green-400 bg-green-400/20';
      case 'finalizada': return 'text-gray-400 bg-gray-400/20';
      default: return 'text-gray-400 bg-gray-400/20';
    }
  };

  const getEstadoTexto = (estado: string) => {
    switch (estado) {
      case 'esperando': return 'ESPERANDO';
      case 'en_juego': return 'EN JUEGO';
      case 'finalizada': return 'FINALIZADA';
      default: return estado.toUpperCase();
    }
  };

  const getAccionButton = (sala: MiSala) => {
    const salaOriginal = salas.find(s => parseInt(s.id) === sala.id);
    
    // Si la sala está finalizada, solo mostrar "Ver"
    if (sala.estado === 'finalizada') {
      return (
        <Button
          variant="ghost"
          onClick={() => onVerPartido(sala.id)}
          className="w-full text-sm"
        >
          Ver Resultado
        </Button>
      );
    }
    
    // Si la sala está en juego, mostrar "Ver Partido"
    if (sala.estado === 'en_juego') {
      return (
        <Button
          variant="secondary"
          onClick={() => onVerPartido(sala.id)}
          className="w-full text-sm"
        >
          Ver Partido
        </Button>
      );
    }
    
    // Si la sala está esperando
    if (sala.estado === 'esperando') {
      // Si soy el organizador o ya estoy en la sala, mostrar "Entrar"
      if (sala.es_organizador || salaOriginal?.jugadores?.some((j: any) => j.id === usuario?.id_usuario?.toString())) {
        return (
          <Button
            variant="primary"
            onClick={() => onEntrarSala(sala.id)}
            className="w-full text-sm"
          >
            Entrar a la Sala
          </Button>
        );
      } else {
        // Si no estoy en la sala, mostrar "Unirse"
        return (
          <Button
            variant="primary"
            onClick={() => onEntrarSala(sala.id)}
            className="w-full text-sm"
          >
            Unirse
          </Button>
        );
      }
    }
    
    // Fallback
    return (
      <Button
        variant="ghost"
        onClick={() => onVerPartido(sala.id)}
        className="w-full text-sm"
      >
        Ver
      </Button>
    );
  };

  if (loading) {
    return (
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-textPrimary flex items-center gap-2">
            <Crown size={20} className="text-primary" />
            Mis Salas
          </h2>
        </div>
        <div className="bg-cardBg border border-cardBorder rounded-lg p-6">
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-cardBorder/30 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (misSalasFormateadas.length === 0) {
    return (
      <div className="mb-8">
        <h2 className="text-xl font-bold text-textPrimary mb-4 flex items-center gap-2">
          <Crown size={20} className="text-primary" />
          Mis Salas (0)
        </h2>
        <div className="bg-cardBg/50 border border-cardBorder rounded-lg p-6 text-center">
          <Users size={32} className="mx-auto mb-3 text-textSecondary opacity-50" />
          <p className="text-textSecondary text-sm mb-3">No tienes salas creadas</p>
          <p className="text-textSecondary text-xs">Crea una sala para comenzar a jugar</p>
        </div>
      </div>
    );
  }

  const salasVisibles = expandido ? misSalasFormateadas : misSalasFormateadas.slice(0, 3);

  return (
    <div className="mb-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-textPrimary flex items-center gap-2">
          <Crown size={20} className="text-primary" />
          Mis Salas ({misSalasFormateadas.length})
        </h2>
        
        {misSalasFormateadas.length > 3 && (
          <button
            onClick={() => setExpandido(!expandido)}
            className="flex items-center gap-2 text-sm text-textSecondary hover:text-primary transition-colors"
          >
            {expandido ? 'Ver menos' : `Ver todas (${misSalasFormateadas.length})`}
            <ChevronDown 
              size={16} 
              className={`transform transition-transform ${expandido ? 'rotate-180' : ''}`} 
            />
          </button>
        )}
      </div>
      
      {/* Grid de cards visuales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {salasVisibles.map((sala, index) => (
          <motion.div
            key={sala.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className={`bg-cardBg border rounded-xl p-4 hover:shadow-lg transition-all ${
              sala.estado === 'en_juego' 
                ? 'border-green-500/50 shadow-green-500/20' 
                : sala.estado === 'esperando'
                ? 'border-yellow-500/50'
                : 'border-cardBorder'
            }`}
          >
            {/* Header de la card */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-textPrimary text-base truncate mb-1">
                  {sala.nombre}
                </h3>
                {sala.es_organizador && (
                  <div className="flex items-center gap-1">
                    <Crown size={12} className="text-yellow-400" />
                    <span className="text-xs text-yellow-400">Organizador</span>
                  </div>
                )}
              </div>
              <span className={`px-2 py-1 rounded-lg text-[10px] font-bold ${getEstadoColor(sala.estado)} flex-shrink-0 ml-2`}>
                {sala.estado === 'en_juego' && '● '}
                {getEstadoTexto(sala.estado)}
              </span>
            </div>

            {/* Info de la sala */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2 text-sm text-textSecondary">
                <Users size={14} />
                <span className="font-medium text-textPrimary">
                  {sala.jugadores_actuales}/{sala.jugadores_maximos}
                </span>
                <span>jugadores</span>
              </div>
              
              <div className="flex items-center gap-2 text-sm text-textSecondary">
                {sala.estado === 'en_juego' && sala.tiempo_transcurrido ? (
                  <>
                    <Clock size={14} />
                    <span>{sala.tiempo_transcurrido}</span>
                  </>
                ) : (
                  <>
                    <Calendar size={14} />
                    <span>{sala.fecha}</span>
                  </>
                )}
              </div>
            </div>

            {/* Botón de acción */}
            <div className="pt-3 border-t border-cardBorder">
              {getAccionButton(sala)}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
