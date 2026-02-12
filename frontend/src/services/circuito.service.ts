import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Circuito {
  id: number;
  codigo: string;
  nombre: string;
  descripcion?: string;
  logo_url?: string;
  activo: boolean;
  torneos_count: number;
}

export interface RankingCircuitoItem {
  posicion: number;
  id_usuario: number;
  nombre_usuario?: string;
  nombre?: string;
  apellido?: string;
  imagen_url?: string;
  categoria?: string;
  puntos: number;
  partidos_jugados: number;
  partidos_ganados: number;
  winrate: number;
}

export interface CircuitoInfo extends Circuito {
  torneos: Array<{
    id: number;
    nombre: string;
    estado: string;
    fecha_inicio: string;
    fecha_fin: string;
  }>;
}

class CircuitoService {
  private getAuthHeaders() {
    const token = localStorage.getItem('firebase_token') || localStorage.getItem('access_token') || localStorage.getItem('token');
    return {
      headers: { Authorization: `Bearer ${token}` },
    };
  }

  async listarCircuitos(activo?: boolean): Promise<Circuito[]> {
    const params = activo !== undefined ? { activo } : {};
    const response = await axios.get(`${API_URL}/circuitos`, { params });
    return response.data;
  }

  async crearCircuito(data: { codigo: string; nombre: string; descripcion?: string; logo_url?: string }): Promise<Circuito> {
    const response = await axios.post(`${API_URL}/circuitos`, data, this.getAuthHeaders());
    return response.data;
  }

  async actualizarCircuito(id: number, data: { nombre?: string; descripcion?: string; logo_url?: string; activo?: boolean }): Promise<Circuito> {
    const response = await axios.put(`${API_URL}/circuitos/${id}`, data, this.getAuthHeaders());
    return response.data;
  }

  async eliminarCircuito(id: number): Promise<void> {
    await axios.delete(`${API_URL}/circuitos/${id}`, this.getAuthHeaders());
  }

  async obtenerRanking(codigo: string, categoria?: string, limit?: number): Promise<RankingCircuitoItem[]> {
    const params: any = {};
    if (categoria) params.categoria = categoria;
    if (limit) params.limit = limit;
    const response = await axios.get(`${API_URL}/circuitos/${codigo}/ranking`, { params });
    return response.data;
  }

  async obtenerInfo(codigo: string): Promise<CircuitoInfo> {
    const response = await axios.get(`${API_URL}/circuitos/${codigo}/info`);
    return response.data;
  }
}

export const circuitoService = new CircuitoService();
export default circuitoService;
