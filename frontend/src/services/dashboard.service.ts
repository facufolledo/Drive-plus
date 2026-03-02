import { apiService } from './api';

export interface DashboardData {
  top_jugadores: {
    masculino: Array<{
      id_usuario: number;
      nombre: string;
      apellido: string;
      rating: number;
      nombre_usuario: string;
    }>;
    femenino: Array<{
      id_usuario: number;
      nombre: string;
      apellido: string;
      rating: number;
      nombre_usuario: string;
    }>;
  };
  ultimos_partidos: Array<{
    id_partido: number;
    fecha: string;
    victoria: boolean;
  }>;
  delta_semana: number;
}

class DashboardService {
  async getDashboardData(): Promise<DashboardData> {
    const response = await apiService.get('/dashboard/data');
    return response.data;
  }
}

export const dashboardService = new DashboardService();
