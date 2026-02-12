import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Configurar axios para evitar cache
axios.defaults.headers.common['Cache-Control'] = 'no-cache, no-store, must-revalidate';
axios.defaults.headers.common['Pragma'] = 'no-cache';
axios.defaults.headers.common['Expires'] = '0';

// Tipos para crear/actualizar torneos
export interface TorneoCreate {
  nombre: string;
  descripcion?: string;
  fecha_inicio: string;
  fecha_fin: string;
  lugar?: string;
  ubicacion?: string; // Alias para compatibilidad
  categoria: string;
  genero?: string;
  max_parejas?: number;
  premio?: string;
  reglas_json?: any;
  // Campos de pago
  requiere_pago?: boolean;
  monto_inscripcion?: number;
  alias_cbu_cvu?: string;
  titular_cuenta?: string;
  banco?: string;
  telefono_contacto?: string;
  // Horarios
  horarios_disponibles?: any;
  // Código de circuito
  codigo?: string;
}

// Tipo del backend
export interface TorneoBackend {
  id: number;
  nombre: string;
  descripcion: string;
  fecha_inicio: string;
  fecha_fin: string;
  lugar: string;
  categoria: string;
  max_parejas: number;
  parejas_inscritas?: number;
  estado: string;
  premio?: string;
  owner_id: number;
  created_at: string;
}

// Tipo para el frontend (compatible con el Context)
export interface Torneo {
  id_torneo: number;
  nombre: string;
  descripcion: string;
  fecha_inicio: string;
  fecha_fin: string;
  ubicacion: string;
  categoria: string;
  max_parejas: number;
  parejas_inscritas: number;
  estado: 'inscripcion' | 'armando_zonas' | 'fase_grupos' | 'fase_eliminacion' | 'finalizado';
  premio?: string;
  owner_id: number;
}

// Tipos para inscripciones
export interface ParejaInscripcion {
  jugador1_id: number;
  jugador2_id: number;
  nombre_pareja: string;
  categoria_id?: number;
}

export interface Pareja {
  id: number;
  id_pareja?: number; // Alias para compatibilidad
  torneo_id: number;
  jugador1_id: number;
  jugador2_id: number;
  nombre_pareja: string;
  estado: 'pendiente' | 'inscripta' | 'confirmada' | 'baja' | 'rechazada' | 'expirada';
  jugador1_nombre?: string;
  jugador2_nombre?: string;
  disponibilidad_horaria?: any; // Restricciones horarias de la pareja
}

export interface EstadisticasTorneo {
  torneo_id: number;
  total_parejas: number;
  total_partidos: number;
  partidos_jugados: number;
  partidos_pendientes: number;
  zonas: number;
  fase_actual: string;
}

// Tipos para categorías
export interface CategoriaCreate {
  nombre: string;
  genero: string;
  max_parejas: number;
  orden?: number;
}

export interface Categoria {
  id: number;
  torneo_id: number;
  nombre: string;
  genero: string;
  max_parejas: number;
  estado: string;
  orden: number;
  parejas_inscritas: number;
}

class TorneoService {
  private getAuthHeaders() {
    const token = localStorage.getItem('firebase_token') || localStorage.getItem('access_token') || localStorage.getItem('token');
    return {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    };
  }

  // CRUD Torneos
  async listarTorneos(params?: {
    skip?: number;
    limit?: number;
    estado?: string;
    categoria?: string;
  }): Promise<Torneo[]> {
    const response = await axios.get(`${API_URL}/torneos`, { params });
    return response.data;
  }

  async obtenerTorneo(torneoId: number): Promise<Torneo> {
    // Agregar timestamp para evitar cache del navegador
    const response = await axios.get(`${API_URL}/torneos/${torneoId}?_t=${Date.now()}`);
    return response.data;
  }

  async crearTorneo(data: TorneoCreate): Promise<Torneo> {
    const response = await axios.post(
      `${API_URL}/torneos`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async actualizarTorneo(torneoId: number, data: Partial<TorneoCreate>): Promise<Torneo> {
    const response = await axios.put(
      `${API_URL}/torneos/${torneoId}`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async eliminarTorneo(torneoId: number): Promise<void> {
    await axios.delete(
      `${API_URL}/torneos/${torneoId}`,
      this.getAuthHeaders()
    );
  }

  // Estado
  async cambiarEstado(torneoId: number, nuevoEstado: string): Promise<Torneo> {
    const response = await axios.patch(
      `${API_URL}/torneos/${torneoId}/estado`,
      { nuevo_estado: nuevoEstado },
      this.getAuthHeaders()
    );
    return response.data;
  }

  // Estadísticas
  async obtenerEstadisticas(torneoId: number): Promise<EstadisticasTorneo> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/estadisticas`);
    return response.data;
  }

  // Inscripciones
  async inscribirPareja(
    torneoId: number,
    data: { 
      jugador1_id: number; 
      jugador2_id: number; 
      nombre_pareja?: string; 
      categoria_id?: number;
      disponibilidad_horaria?: any[];
    }
  ): Promise<{ pareja_id: number; codigo_confirmacion: string; fecha_expiracion: string; mensaje: string }> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/inscribir`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  // Confirmación de pareja
  async confirmarParejaPorCodigo(codigo: string): Promise<{ mensaje: string; pareja_id: number; torneo_id: number }> {
    const response = await axios.post(
      `${API_URL}/torneos/confirmar-pareja/${codigo}`,
      {},
      this.getAuthHeaders()
    );
    return response.data;
  }

  async rechazarInvitacion(parejaId: number, motivo?: string): Promise<{ mensaje: string }> {
    const response = await axios.post(
      `${API_URL}/torneos/rechazar-invitacion/${parejaId}`,
      {},
      { ...this.getAuthHeaders(), params: { motivo } }
    );
    return response.data;
  }

  async obtenerMisInvitaciones(): Promise<{
    invitaciones: Array<{
      pareja_id: number;
      torneo_id: number;
      torneo_nombre: string;
      companero_id: number;
      companero_nombre: string;
      fecha_expiracion: string;
      codigo: string;
    }>;
  }> {
    const response = await axios.get(`${API_URL}/torneos/mis-invitaciones`, this.getAuthHeaders());
    return response.data;
  }

  async obtenerMisTorneos(): Promise<{
    torneos: Array<{
      id: number;
      nombre: string;
      descripcion: string;
      categoria: string;
      genero: string;
      estado: string;
      fecha_inicio: string;
      fecha_fin: string;
      lugar: string;
      mi_inscripcion: {
        pareja_id: number;
        estado_inscripcion: string;
        categoria_id: number | null;
      };
    }>;
  }> {
    // Intentar primero con el endpoint específico, si falla usar el general con filtros
    try {
      const response = await axios.get(`${API_URL}/torneos/mis-torneos`, this.getAuthHeaders());
      return response.data;
    } catch (error: any) {
      // Si el endpoint específico no existe, usar el general y filtrar en el frontend
      console.warn('Endpoint /torneos/mis-torneos no disponible, usando endpoint general');
      const response = await axios.get(`${API_URL}/torneos`, this.getAuthHeaders());
      
      // Retornar en el formato esperado (por ahora vacío hasta que el backend implemente el endpoint)
      return {
        torneos: []
      };
    }
  }

  async listarParejas(torneoId: number, estado?: string, categoriaId?: number): Promise<Pareja[]> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/parejas`, {
      params: { estado, categoria_id: categoriaId },
    });
    return response.data;
  }

  // Categorías
  async listarCategorias(torneoId: number): Promise<Categoria[]> {
    // Validar que torneoId sea un número válido
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      console.warn('listarCategorias: torneoId inválido', torneoId);
      return [];
    }
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/categorias`);
    return response.data;
  }

  async crearCategoria(torneoId: number, data: CategoriaCreate): Promise<Categoria> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/categorias`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async actualizarCategoria(torneoId: number, categoriaId: number, data: CategoriaCreate): Promise<any> {
    const response = await axios.put(
      `${API_URL}/torneos/${torneoId}/categorias/${categoriaId}`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async eliminarCategoria(torneoId: number, categoriaId: number): Promise<void> {
    await axios.delete(
      `${API_URL}/torneos/${torneoId}/categorias/${categoriaId}`,
      this.getAuthHeaders()
    );
  }

  async confirmarPareja(torneoId: number, parejaId: number): Promise<Pareja> {
    const response = await axios.patch(
      `${API_URL}/torneos/${torneoId}/parejas/${parejaId}/confirmar`,
      {},
      this.getAuthHeaders()
    );
    return response.data;
  }

  async rechazarPareja(torneoId: number, parejaId: number, motivo?: string): Promise<void> {
    await axios.delete(
      `${API_URL}/torneos/${torneoId}/parejas/${parejaId}/rechazar`,
      {
        ...this.getAuthHeaders(),
        params: { motivo },
      }
    );
  }

  async darBajaPareja(torneoId: number, parejaId: number, motivo?: string): Promise<Pareja> {
    const response = await axios.patch(
      `${API_URL}/torneos/${torneoId}/parejas/${parejaId}/baja`,
      { motivo },
      this.getAuthHeaders()
    );
    return response.data;
  }

  async cambiarCategoriaPareja(torneoId: number, parejaId: number, categoriaId: number): Promise<Pareja> {
    const response = await axios.put(
      `${API_URL}/torneos/${torneoId}/parejas/${parejaId}`,
      { categoria_id: categoriaId },
      this.getAuthHeaders()
    );
    return response.data;
  }

  // Zonas
  async generarZonas(torneoId: number, parejasConfirmadas: number[], categoriaId?: number): Promise<any> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/zonas/generar`,
      { parejas_confirmadas: parejasConfirmadas },
      {
        ...this.getAuthHeaders(),
        params: categoriaId ? { categoria_id: categoriaId } : {}
      }
    );
    return response.data;
  }

  async eliminarZonas(torneoId: number, categoriaId?: number): Promise<any> {
    const response = await axios.delete(
      `${API_URL}/torneos/${torneoId}/zonas`,
      {
        ...this.getAuthHeaders(),
        params: categoriaId ? { categoria_id: categoriaId } : {}
      }
    );
    return response.data;
  }

  /** Crea una zona de último momento y asigna parejas. Solo antes de playoffs. */
  async crearZonaUltimoMomento(
    torneoId: number,
    data: { categoria_id: number; nombre: string; pareja_ids: number[] }
  ): Promise<{ zona: { id: number; nombre: string }; message: string }> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/zonas`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  /** Genera solo los partidos (round-robin) de una zona. Quedan sin programar. */
  async generarPartidosZona(torneoId: number, zonaId: number): Promise<{ partidos_creados: number; message: string }> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/zonas/${zonaId}/generar-partidos`,
      {},
      this.getAuthHeaders()
    );
    return response.data;
  }

  async eliminarFixture(torneoId: number, categoriaId?: number): Promise<any> {
    const config = this.getAuthHeaders();
    if (categoriaId !== undefined && categoriaId !== null) {
      config.params = { categoria_id: categoriaId };
    }
    const response = await axios.delete(
      `${API_URL}/torneos/${torneoId}/fixture`,
      config
    );
    return response.data;
  }

  async listarZonas(torneoId: number): Promise<any[]> {
    // Validar que torneoId sea un número válido
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      console.warn('listarZonas: torneoId inválido', torneoId);
      return [];
    }
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/zonas`);
    return response.data;
  }

  /** Zonas + tablas. Si categoriaId se pasa, solo esa categoría (más rápido). */
  async listarZonasConTablas(torneoId: number, categoriaId?: number): Promise<{ zonas: any[]; tablas: any[] }> {
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      return { zonas: [], tablas: [] };
    }
    const params = categoriaId != null ? { categoria_id: categoriaId } : {};
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/zonas/tablas`, { params });
    return response.data;
  }

  async obtenerTablaPosiciones(torneoId: number, zonaId: number): Promise<any> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/zonas/${zonaId}/tabla`);
    return response.data;
  }

  /** Mueve una pareja de su zona actual a otra zona (misma categoría). Solo organizadores. */
  async moverParejaEntreZonas(
    torneoId: number,
    parejaId: number,
    zonaDestinoId: number
  ): Promise<{ message: string }> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/zonas/mover-pareja`,
      null,
      {
        ...this.getAuthHeaders(),
        params: { pareja_id: parejaId, zona_destino_id: zonaDestinoId },
      }
    );
    return response.data;
  }

  // Fixture
  async generarFixture(torneoId: number, categoriaId?: number): Promise<any> {
    const config = this.getAuthHeaders();
    if (categoriaId !== undefined && categoriaId !== null) {
      config.params = { categoria_id: categoriaId };
    }
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/generar-fixture`,
      {},
      config
    );
    return response.data;
  }

  async eliminarFixture(torneoId: number, categoriaId?: number): Promise<any> {
    const config = this.getAuthHeaders();
    if (categoriaId !== undefined && categoriaId !== null) {
      config.params = { categoria_id: categoriaId };
    }
    const response = await axios.delete(
      `${API_URL}/torneos/${torneoId}/fixture`,
      config
    );
    return response.data;
  }

  async listarPartidos(torneoId: number, params?: { zona_id?: number; fase?: string }): Promise<any[]> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/partidos`, { params });
    return response.data;
  }

  // Resultados
  async cargarResultado(torneoId: number, partidoId: number, resultado: any): Promise<any> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/partidos/${partidoId}/resultado`,
      resultado,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async obtenerClasificados(zonaId: number, numClasificados: number = 2): Promise<any[]> {
    const response = await axios.get(`${API_URL}/torneos/zonas/${zonaId}/clasificados`, {
      params: { num_clasificados: numClasificados }
    });
    return response.data;
  }

  async verificarZonaCompleta(zonaId: number): Promise<boolean> {
    const response = await axios.get(`${API_URL}/torneos/zonas/${zonaId}/completa`);
    return response.data.completa;
  }

  // Playoffs (categoriaId opcional: genera solo esa categoría, como el fixture)
  async generarPlayoffs(torneoId: number, clasificadosPorZona: number = 2, categoriaId?: number): Promise<any> {
    const params: Record<string, number> = { clasificados_por_zona: clasificadosPorZona };
    if (categoriaId != null) params.categoria_id = categoriaId;
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/generar-playoffs`,
      {},
      { ...this.getAuthHeaders(), params }
    );
    return response.data;
  }

  async eliminarPlayoffs(torneoId: number, categoriaId?: number): Promise<{ message: string; eliminados: number }> {
    const config: any = this.getAuthHeaders();
    if (categoriaId != null) config.params = { categoria_id: categoriaId };
    const response = await axios.delete(
      `${API_URL}/torneos/${torneoId}/playoffs`,
      config
    );
    return response.data;
  }

  async intercambiarParejasPlayoff(
    torneoId: number,
    data: { partido_id_a: number; partido_id_b: number; slot_a: 1 | 2; slot_b: 1 | 2 }
  ): Promise<{ message: string }> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/playoffs/intercambiar-parejas`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  /** Intercambia posiciones de dos partidos (cuadros) en el bracket. */
  async intercambiarPartidosPlayoff(
    torneoId: number,
    data: { partido_id_a: number; partido_id_b: number }
  ): Promise<{ message: string }> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/playoffs/intercambiar-partidos`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async listarPlayoffs(torneoId: number, categoriaId?: number): Promise<any> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/playoffs`, {
      params: categoriaId ? { categoria_id: categoriaId } : {}
    });
    return response.data;
  }

  async listarPartidosPlayoffs(torneoId: number, categoriaId?: number): Promise<any> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/playoffs/partidos`, {
      params: categoriaId ? { categoria_id: categoriaId } : {}
    });
    return response.data;
  }

  async cargarResultadoPlayoff(torneoId: number, partidoId: number, resultado: any): Promise<any> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/partidos/${partidoId}/resultado`,
      resultado,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async corregirResultado(torneoId: number, partidoId: number, resultado: any): Promise<any> {
    const response = await axios.put(
      `${API_URL}/torneos/${torneoId}/partidos/${partidoId}/resultado`,
      resultado,
      this.getAuthHeaders()
    );
    return response.data;
  }

  // Canchas
  async listarCanchas(torneoId: number): Promise<any[]> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/canchas`);
    return response.data;
  }

  async crearCancha(torneoId: number, data: { nombre: string; activa?: boolean }): Promise<any> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/canchas`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async actualizarCancha(torneoId: number, canchaId: number, data: { nombre?: string; activa?: boolean }): Promise<any> {
    const response = await axios.put(
      `${API_URL}/torneos/${torneoId}/canchas/${canchaId}`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async eliminarCancha(torneoId: number, canchaId: number): Promise<void> {
    await axios.delete(
      `${API_URL}/torneos/${torneoId}/canchas/${canchaId}`,
      this.getAuthHeaders()
    );
  }

  // Slots de horarios
  async listarSlots(torneoId: number, params?: { cancha_id?: number; fecha?: string }): Promise<any[]> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/slots`, { params });
    return response.data;
  }

  async crearSlot(torneoId: number, data: {
    cancha_id: number;
    fecha_hora_inicio: string;
    fecha_hora_fin: string;
  }): Promise<any> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/slots`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async eliminarSlot(torneoId: number, slotId: number): Promise<void> {
    await axios.delete(
      `${API_URL}/torneos/${torneoId}/slots/${slotId}`,
      this.getAuthHeaders()
    );
  }

  // Programación automática
  async programarPartidosAutomaticamente(torneoId: number, params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    duracion_partido_minutos?: number;
    hora_inicio_semana?: string;
    hora_fin_semana?: string;
    hora_inicio_finde?: string;
    hora_fin_finde?: string;
  }): Promise<any> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/programar-automatico`,
      params || {},
      this.getAuthHeaders()
    );
    return response.data;
  }

  async limpiarProgramacion(torneoId: number): Promise<any> {
    const response = await axios.delete(
      `${API_URL}/torneos/${torneoId}/limpiar-programacion`,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async obtenerProgramacion(torneoId: number): Promise<any> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/programacion`);
    return response.data;
  }

  // Bloqueos horarios de jugadores
  async listarBloqueosJugador(torneoId: number, jugadorId: number): Promise<any[]> {
    const response = await axios.get(
      `${API_URL}/torneos/${torneoId}/jugadores/${jugadorId}/bloqueos`
    );
    return response.data;
  }

  async crearBloqueoJugador(torneoId: number, jugadorId: number, data: {
    fecha: string;
    hora_desde: string;
    hora_hasta: string;
    motivo?: string;
  }): Promise<any> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/jugadores/${jugadorId}/bloqueos`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async eliminarBloqueoJugador(torneoId: number, jugadorId: number, bloqueoId: number): Promise<void> {
    await axios.delete(
      `${API_URL}/torneos/${torneoId}/jugadores/${jugadorId}/bloqueos/${bloqueoId}`,
      this.getAuthHeaders()
    );
  }

  // Validaciones
  validarDatosTorneo(data: TorneoCreate): string[] {
    const errores: string[] = [];
    
    if (!data.nombre || data.nombre.trim().length < 3) {
      errores.push('El nombre debe tener al menos 3 caracteres');
    }
    
    if (!data.fecha_inicio) {
      errores.push('La fecha de inicio es requerida');
    }
    
    if (!data.fecha_fin) {
      errores.push('La fecha de fin es requerida');
    }
    
    if (data.fecha_inicio && data.fecha_fin && new Date(data.fecha_inicio) > new Date(data.fecha_fin)) {
      errores.push('La fecha de inicio debe ser anterior a la fecha de fin');
    }
    
    return errores;
  }

  validarInscripcionPareja(data: ParejaInscripcion): string[] {
    const errores: string[] = [];
    
    if (!data.jugador1_id) {
      errores.push('Debe seleccionar el jugador 1');
    }
    
    if (!data.jugador2_id) {
      errores.push('Debe seleccionar el jugador 2');
    }
    
    if (data.jugador1_id === data.jugador2_id) {
      errores.push('Los jugadores deben ser diferentes');
    }
    
    if (!data.nombre_pareja || data.nombre_pareja.trim().length < 3) {
      errores.push('El nombre de la pareja debe tener al menos 3 caracteres');
    }
    
    return errores;
  }

  // Organizadores
  async listarOrganizadores(torneoId: number): Promise<any[]> {
    const response = await axios.get(`${API_URL}/torneos/${torneoId}/organizadores`);
    return response.data;
  }

  async agregarOrganizador(torneoId: number, data: { user_id?: number; username?: string }): Promise<any> {
    const response = await axios.post(
      `${API_URL}/torneos/${torneoId}/organizadores`,
      data,
      this.getAuthHeaders()
    );
    return response.data;
  }

  async removerOrganizador(torneoId: number, userId: number): Promise<void> {
    await axios.delete(
      `${API_URL}/torneos/${torneoId}/organizadores/${userId}`,
      this.getAuthHeaders()
    );
  }

  // Categorías del sistema (de la tabla categorias)
  async obtenerCategoriasDelSistema(): Promise<{ id: number; nombre: string; sexo: string }[]> {
    const response = await axios.get(`${API_URL}/categorias`);
    // Mapear id_categoria a id para consistencia
    return response.data.map((cat: any) => ({
      id: cat.id_categoria,
      nombre: cat.nombre,
      sexo: cat.sexo || 'masculino'
    }));
  }

}

// Exportar instancia por defecto para compatibilidad con Context
const torneoServiceInstance = new TorneoService();
export default torneoServiceInstance;

// También exportar como named export
export const torneoService = torneoServiceInstance;
