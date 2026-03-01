import { useState, useEffect } from 'react';
import categoriaService, { Categoria } from '../services/categoria.service';

export function useCategorias() {
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCategorias();
  }, []);

  const loadCategorias = async () => {
    try {
      setLoading(true);
      const data = await categoriaService.getCategorias();
      setCategorias(data);
      setError(null);
    } catch (err) {
      setError('Error al cargar categorías');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getCategoriasNombres = (): string[] => {
    return categorias.map(c => c.nombre);
  };

  const getCategoriaByRating = (rating: number): string => {
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
  };

  return {
    categorias,
    loading,
    error,
    getCategoriasNombres,
    getCategoriaByRating,
    refresh: loadCategorias
  };
}
