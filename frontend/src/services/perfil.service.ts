import { api } from './api';

export interface PerfilPublico {
  id_usuario: number;
  nombre: string;
  apellido: string;
  nombre_usuario: string;
  email?: string;
  rating: number;
  categoria_id?: number;
  categoria?: string;
  posicion_preferida?: string;
  mano_dominante?: string;
  ciudad?: string;
  pais?: string;
  fecha_registro: string;
  foto_perfil?: string;
  activo: boolean;
}

export interface EstadisticasJugador {
  partidos_jugados: number;
  partidos_ganados: number;
  partidos_perdidos: number;
  porcentaje_victorias: number;
  racha_actual: { tipo: 'victorias' | 'derrotas'; cantidad: number };
  mejor_rating: number;
  peor_rating: number;
  rating_actual: number;
  torneos_participados: number;
  torneos_ganados: number;
  finales_jugadas: number;
  sets_ganados: number;
  sets_perdidos: number;
  games_ganados: number;
  games_perdidos: number;
  cambio_rating_total: number;
  winrate_torneos: number;
  winrate_amistosos: number;
  mejor_racha: number;
}

export interface PartidoHistorial {
  id_partido: number;
  fecha: string;
  estado: string;
  tipo?: string;
  fase?: string;
  categoria?: string;
  jugadores: Array<{
    id_usuario: number;
    nombre_usuario: string;
    nombre: string;
    apellido: string;
    equipo: number;
    rating: number;
  }>;
  resultado?: {
    sets_eq1: number;
    sets_eq2: number;
    detalle_sets: Array<{ set: number; juegos_eq1: number; juegos_eq2: number; tiebreak_eq1?: number; tiebreak_eq2?: number }>;
    confirmado: boolean;
    desenlace: string;
  };
  historial_rating?: { rating_antes: number; delta: number; rating_despues: number };
}

class PerfilService {
  async getPerfilPublico(username: string): Promise<PerfilPublico> {
    try {
      // Usar axios directamente sin headers de autenticación para perfiles públicos
      const API_URL = import.meta.env.VITE_API_URL || 'https://drive-plus-production.up.railway.app';
      const response = await fetch(`${API_URL}/usuarios/perfil-publico/${username}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`El usuario @${username} no fue encontrado`);
        }
        if (response.status === 500) {
          // Error 500 - probablemente el backend está desplegando cambios
          throw new Error(`El perfil está temporalmente no disponible. Por favor intenta de nuevo en unos segundos.`);
        }
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error: any) {
      console.error('Error obteniendo perfil público:', {
        username,
        message: error.message
      });
      
      if (error.message.includes('no fue encontrado') || error.message.includes('temporalmente no disponible')) {
        throw error;
      }
      throw new Error('Error al cargar el perfil del usuario');
    }
  }

  async getEstadisticas(userId: number): Promise<EstadisticasJugador> {
    try {
      const response = await api.get(`/usuarios/${userId}/estadisticas`);
      return response.data;
    } catch (error) {
      throw new Error('Error al cargar estadísticas');
    }
  }

  async getHistorial(userId: number, limit = 50): Promise<PartidoHistorial[]> {
    try {
      const response = await api.get(`/partidos/usuario/${userId}?limit=${limit}`);
      const partidosUnicos = response.data.filter((partido: PartidoHistorial, index: number, self: PartidoHistorial[]) =>
        index === self.findIndex((p) => p.id_partido === partido.id_partido)
      );
      return partidosUnicos;
    } catch (error: any) {
      if (error.response?.status === 404) return [];
      throw new Error('Error al cargar historial');
    }
  }

  async buscarJugadores(query: string, limit = 20): Promise<PerfilPublico[]> {
    try {
      // Usar el endpoint público de búsqueda sin autenticación
      const API_URL = import.meta.env.VITE_API_URL || 'https://drive-plus-production.up.railway.app';
      const response = await fetch(`${API_URL}/usuarios/buscar-publico?q=${encodeURIComponent(query)}&limit=${limit}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          return []; // No hay resultados, no es un error
        }
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data || [];
    } catch (error: any) {
      console.error('Error buscando jugadores:', error.message);
      if (error.message.includes('404')) {
        return []; // No hay resultados, no es un error
      }
      throw new Error('Servicio de búsqueda no disponible temporalmente');
    }
  }

  async compararJugadores(userId1: number, userId2: number) {
    try {
      const response = await api.get(`/usuarios/comparar/${userId1}/${userId2}`);
      return response.data;
    } catch (error) {
      throw new Error('Error al comparar jugadores');
    }
  }

  async getEvolucionRating(userId: number, dias = 90) {
    try {
      const response = await api.get(`/usuarios/${userId}/evolucion?dias=${dias}`);
      return response.data;
    } catch (error) {
      throw new Error('Error al cargar evolución del rating');
    }
  }

  async getTorneos(userId: number) {
    try {
      const response = await api.get(`/usuarios/${userId}/torneos`);
      return response.data;
    } catch (error) {
      throw new Error('Error al cargar torneos');
    }
  }
}

export const perfilService = new PerfilService();
