import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface DashboardData {
  top_masculino: Array<{
    id_usuario: number;
    nombre_usuario: string;
    nombre: string;
    apellido: string;
    rating: number;
    sexo: string;
  }>;
  top_femenino: Array<{
    id_usuario: number;
    nombre_usuario: string;
    nombre: string;
    apellido: string;
    rating: number;
    sexo: string;
  }>;
  ultimos_partidos: Array<{
    id_partido: number;
    fecha: string | null;
    victoria: boolean;
    delta: number;
  }>;
  delta_semanal: number;
}

export const dashboardService = {
  /**
   * Obtiene todos los datos del dashboard en una sola llamada optimizada
   */
  async getDashboardData(): Promise<DashboardData> {
    const token = localStorage.getItem('firebase_token');
    
    const response = await axios.get<DashboardData>(`${API_URL}/dashboard/data`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    
    return response.data;
  },
};
