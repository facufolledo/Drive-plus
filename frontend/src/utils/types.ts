export interface Jugador {
  id: string;
  nombre: string;
  nombreUsuario?: string;
  rating?: number;
  esCreador?: boolean;
}

export interface Equipo {
  jugador1: Jugador;
  jugador2: Jugador;
  puntos: number;
  confirmado: boolean;
  confirmadoPor?: string; // ID del jugador que confirmó
  fechaConfirmacion?: string;
}

export interface Sala {
  id: string;
  nombre: string;
  fecha: string;
  estado: 'esperando' | 'activa' | 'en_juego' | 'finalizada' | 'programada';
  codigoInvitacion?: string;
  jugadores?: Jugador[];
  equiposAsignados?: boolean;
  equipoA: Equipo;
  equipoB: Equipo;
  sets?: any[]; // Set[] from padelTypes
  ganador?: 'equipoA' | 'equipoB';
  torneoId?: string;
  creadoPor: string;
  creador_id?: string | number; // ID del creador para comparación
  estadoConfirmacion?: 'sin_resultado' | 'pendiente_confirmacion' | 'confirmado' | 'disputado';
  resultado?: any; // ResultadoPartido from padelTypes
  resultadoFinal?: boolean;
  motivoDisputa?: string;
  formato?: 'best_of_3' | 'best_of_3_supertiebreak';
  cambiosElo?: Array<{
    id_usuario: number;
    rating_antes: number;
    rating_despues: number;
    cambio_elo: number;
  }>;
  eloAplicado?: boolean;
  usuariosConfirmados?: number[];  // IDs de usuarios que ya confirmaron
  createdAt: string;
}

export interface Torneo {
  id: string;
  nombre: string;
  fechaInicio: string;
  fechaFin: string;
  categoria: string;
  formato: 'eliminacion-simple' | 'eliminacion-doble' | 'round-robin' | 'grupos' | 'por-puntos';
  genero: 'masculino' | 'femenino' | 'mixto';
  descripcion: string;
  estado: 'activo' | 'finalizado' | 'programado';
  salasIds: string[];
  participantes: number;
  ganadorId?: string;
  createdAt: string;
  lugar?: string;
  total_categorias?: number;
  categorias?: Array<{
    nombre: string;
    genero: string;
  }>;
}

// Tipos específicos para torneos del backend
export interface TorneoBackend {
  id: number;
  nombre: string;
  descripcion?: string;
  tipo: string;
  categoria: string;
  estado: 'INSCRIPCION' | 'ARMANDO_ZONAS' | 'FASE_GRUPOS' | 'FASE_ELIMINACION' | 'FINALIZADO';
  fecha_inicio: string;
  fecha_fin: string;
  lugar?: string;
  reglas_json?: any;
  creado_por: number;
  created_at: string;
  updated_at: string;
}

export interface ParejaInscripcion {
  jugador1_id: number;
  jugador2_id: number;
  observaciones?: string;
}

export interface Pareja {
  id: number;
  torneo_id: number;
  jugador1: {
    id: number;
    nombre: string;
    apellido: string;
    foto_perfil?: string;
    rating?: number;
    categoria?: string;
  };
  jugador2: {
    id: number;
    nombre: string;
    apellido: string;
    foto_perfil?: string;
    rating?: number;
    categoria?: string;
  };
  estado: 'inscripta' | 'confirmada' | 'baja';
  categoria_asignada?: string;
  observaciones?: string;
  created_at: string;
}

export interface Usuario {
  id: string;
  nombre: string;
  email: string;
  avatar?: string;
  rol: 'jugador' | 'admin';
  puede_crear_torneos?: boolean;
  es_administrador?: boolean;
  estadisticas: {
    partidosJugados: number;
    partidosGanados: number;
    torneosParticipados: number;
    torneosGanados: number;
  };
  createdAt: string;
}

export interface EstadisticasJugador {
  jugadorId: string;
  nombre: string;
  partidosJugados: number;
  partidosGanados: number;
  partidosPerdidos: number;
  puntosAFavor: number;
  puntosEnContra: number;
  porcentajeVictorias: number;
}
