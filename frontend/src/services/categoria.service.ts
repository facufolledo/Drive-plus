import api from './api';

export interface Categoria {
  id_categoria: number;
  nombre: string;
  descripcion?: string;
  rating_min?: number;
  rating_max?: number;
  sexo?: string;
}

class CategoriaService {
  private categoriasCache: Categoria[] | null = null;
  private cacheTimestamp: number = 0;
  private CACHE_DURATION = 5 * 60 * 1000; // 5 minutos

  async getCategorias(forceRefresh = false): Promise<Categoria[]> {
    const now = Date.now();
    
    // Usar caché si existe y no ha expirado
    if (!forceRefresh && this.categoriasCache && (now - this.cacheTimestamp) < this.CACHE_DURATION) {
      return this.categoriasCache;
    }

    try {
      const response = await api.get<Categoria[]>('/categorias');
      this.categoriasCache = response.data;
      this.cacheTimestamp = now;
      return response.data;
    } catch (error) {
      console.error('Error al cargar categorías:', error);
      // Si falla, devolver categorías por defecto
      return this.getCategoriasDefault();
    }
  }

  async getCategoriasNombres(): Promise<string[]> {
    const categorias = await this.getCategorias();
    return categorias.map(c => c.nombre);
  }

  async getCategoriaByRating(rating: number): Promise<string> {
    const categorias = await this.getCategorias();
    
    // Ordenar por rating_min descendente para encontrar la categoría correcta
    const categoriasOrdenadas = [...categorias].sort((a, b) => 
      (b.rating_min || 0) - (a.rating_min || 0)
    );

    for (const cat of categoriasOrdenadas) {
      if (cat.rating_min !== undefined && rating >= cat.rating_min) {
        if (cat.rating_max === undefined || rating <= cat.rating_max) {
          return cat.nombre;
        }
      }
    }

    return 'Principiante';
  }

  private getCategoriasDefault(): Categoria[] {
    return [
      { id_categoria: 7, nombre: 'Principiante', rating_min: 0, rating_max: 499 },
      { id_categoria: 1, nombre: '8va', rating_min: 500, rating_max: 999 },
      { id_categoria: 2, nombre: '7ma', rating_min: 1000, rating_max: 1199 },
      { id_categoria: 3, nombre: '6ta', rating_min: 1200, rating_max: 1399 },
      { id_categoria: 4, nombre: '5ta', rating_min: 1400, rating_max: 1599 },
      { id_categoria: 5, nombre: '4ta', rating_min: 1600, rating_max: 1799 },
      { id_categoria: 6, nombre: '3ra', rating_min: 1800, rating_max: 9999 },
    ];
  }

  clearCache() {
    this.categoriasCache = null;
    this.cacheTimestamp = 0;
  }
}

export default new CategoriaService();
