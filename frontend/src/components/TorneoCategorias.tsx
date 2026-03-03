import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Trash2, Edit2, Users, ChevronDown, ChevronUp } from 'lucide-react';
import { torneoService, Categoria } from '../services/torneo.service';
import Card from './Card';
import Button from './Button';

interface TorneoCategoriasProps {
  torneoId: number;
  esOrganizador: boolean;
  onCategoriaSeleccionada?: (categoriaId: number | null) => void;
}

const GENEROS = [
  { value: 'masculino', label: 'Masculino' },
  { value: 'femenino', label: 'Femenino' },
  { value: 'mixto', label: 'Mixto' },
];

const CATEGORIAS_SUGERIDAS = ['8va', '7ma', '6ta', '5ta', '4ta', '3ra', '2da', '1ra'];

export default function TorneoCategorias({ torneoId, esOrganizador, onCategoriaSeleccionada }: TorneoCategoriasProps) {
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState<number | null>(null);
  
  // Modal crear/editar
  const [modalOpen, setModalOpen] = useState(false);
  const [editando, setEditando] = useState<Categoria | null>(null);
  const [nombre, setNombre] = useState('');
  const [genero, setGenero] = useState('masculino');
  const [guardando, setGuardando] = useState(false);
  
  // Expandir/colapsar
  const [expandido, setExpandido] = useState(true);

  useEffect(() => {
    // Guard: Solo cargar si torneoId es válido
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      setLoading(false);
      return;
    }
    cargarCategorias();
  }, [torneoId]);

  const cargarCategorias = async () => {
    // Double check por si acaso
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      return;
    }
    
    try {
      setLoading(true);
      const data = await torneoService.listarCategorias(torneoId);
      setCategorias(data);
    } catch (err: any) {
      console.error('Error cargando categorias:', err);
    } finally {
      setLoading(false);
    }
  };

  const abrirModalCrear = () => {
    setEditando(null);
    setNombre('');
    setGenero('masculino');
    setModalOpen(true);
  };

  const abrirModalEditar = (cat: Categoria) => {
    setEditando(cat);
    setNombre(cat.nombre);
    setGenero(cat.genero);
    setModalOpen(true);
  };

  const guardarCategoria = async () => {
    if (!nombre.trim()) {
      setError('El nombre es requerido');
      return;
    }

    try {
      setGuardando(true);
      setError('');
      
      if (editando) {
        await torneoService.actualizarCategoria(torneoId, editando.id, {
          nombre: nombre.trim(),
          genero,
          max_parejas: 999, // Sin límite
          orden: editando.orden
        });
      } else {
        await torneoService.crearCategoria(torneoId, {
          nombre: nombre.trim(),
          genero,
          max_parejas: 999, // Sin límite
          orden: categorias.length
        });
      }
      
      setModalOpen(false);
      await cargarCategorias();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al guardar');
    } finally {
      setGuardando(false);
    }
  };

  const eliminarCategoria = async (cat: Categoria) => {
    if (cat.parejas_inscritas > 0) {
      alert(`No se puede eliminar: hay ${cat.parejas_inscritas} parejas inscritas`);
      return;
    }
    
    if (!confirm(`¿Eliminar la categoría "${cat.nombre}"?`)) return;

    try {
      await torneoService.eliminarCategoria(torneoId, cat.id);
      await cargarCategorias();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al eliminar');
    }
  };

  const seleccionarCategoria = (catId: number | null) => {
    setCategoriaSeleccionada(catId);
    onCategoriaSeleccionada?.(catId);
  };

  if (loading) {
    return (
      <Card>
        <div className="p-4 animate-pulse">
          <div className="h-6 bg-cardBorder rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            <div className="h-10 bg-cardBorder rounded"></div>
            <div className="h-10 bg-cardBorder rounded"></div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <div className="p-4">
          {/* Header */}
          <div 
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setExpandido(!expandido)}
          >
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-textPrimary">Categorías del Torneo</h3>
              <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                {categorias.length}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {esOrganizador && (
                <Button
                  variant="ghost"
                  onClick={(e) => { e.stopPropagation(); abrirModalCrear(); }}
                  className="text-xs"
                >
                  <Plus size={14} className="mr-1" />
                  Agregar
                </Button>
              )}
              {expandido ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </div>
          </div>

          {/* Lista de categorías - REDISEÑADO como cards compactas */}
          {expandido && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              className="mt-4"
            >
              {categorias.length === 0 ? (
                <div className="text-center py-6 text-textSecondary">
                  <p className="text-sm">No hay categorías configuradas</p>
                  {esOrganizador && (
                    <Button variant="primary" onClick={abrirModalCrear} className="mt-3 text-sm">
                      Crear Primera Categoría
                    </Button>
                  )}
                </div>
              ) : (
                <>
                  {/* Filtro "Todas" */}
                  <button
                    onClick={() => seleccionarCategoria(null)}
                    className={`w-full mb-3 p-3 rounded-lg border text-left transition-all ${
                      categoriaSeleccionada === null
                        ? 'border-primary bg-primary/10'
                        : 'border-cardBorder hover:border-primary/50'
                    }`}
                  >
                    <span className="font-bold text-textPrimary">Todas las categorías</span>
                  </button>

                  {/* Grid de categorías como cards compactas */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {categorias.map((cat) => {
                      const colorClasses = cat.genero === 'masculino' 
                        ? 'from-blue-500/20 to-blue-600/10 border-blue-500/40 hover:border-blue-500/70'
                        : cat.genero === 'femenino'
                        ? 'from-pink-500/20 to-pink-600/10 border-pink-500/40 hover:border-pink-500/70'
                        : 'from-purple-500/20 to-purple-600/10 border-purple-500/40 hover:border-purple-500/70';
                      
                      const textColor = cat.genero === 'masculino'
                        ? 'text-blue-400'
                        : cat.genero === 'femenino'
                        ? 'text-pink-400'
                        : 'text-purple-400';
                      
                      return (
                        <motion.div
                          key={cat.id}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          className={`relative p-4 rounded-xl border-2 bg-gradient-to-br transition-all cursor-pointer ${colorClasses} ${
                            categoriaSeleccionada === cat.id
                              ? 'ring-2 ring-primary shadow-lg'
                              : ''
                          }`}
                          onClick={() => seleccionarCategoria(cat.id)}
                        >
                          {/* Nombre y género */}
                          <div className="mb-3">
                            <h4 className={`text-xl font-black ${textColor} mb-1`}>
                              {cat.nombre}
                            </h4>
                            <span className="text-xs uppercase tracking-wider text-textSecondary font-bold">
                              {cat.genero}
                            </span>
                          </div>
                          
                          {/* Número de parejas */}
                          <div className="flex items-center gap-2">
                            <Users size={16} className={textColor} />
                            <span className="text-sm font-bold text-textPrimary">
                              {cat.parejas_inscritas} {cat.parejas_inscritas === 1 ? 'pareja' : 'parejas'}
                            </span>
                          </div>
                          
                          {/* Botones de acción (solo organizador) */}
                          {esOrganizador && (
                            <div className="absolute top-2 right-2 flex items-center gap-1">
                              <button
                                onClick={(e) => { e.stopPropagation(); abrirModalEditar(cat); }}
                                className="p-1.5 bg-cardBg/80 backdrop-blur-sm rounded-lg text-textSecondary hover:text-primary transition-colors"
                              >
                                <Edit2 size={14} />
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); eliminarCategoria(cat); }}
                                className="p-1.5 bg-cardBg/80 backdrop-blur-sm rounded-lg text-textSecondary hover:text-red-500 transition-colors"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          )}
                        </motion.div>
                      );
                    })}
                  </div>
                </>
              )}
            </motion.div>
          )}
        </div>
      </Card>

      {/* Modal Crear/Editar */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-card rounded-xl max-w-md w-full p-6"
          >
            <h3 className="text-xl font-bold text-textPrimary mb-4">
              {editando ? 'Editar Categoría' : 'Nueva Categoría'}
            </h3>

            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-500 text-sm">
                {error}
              </div>
            )}

            {/* Nombre */}
            <div className="mb-4">
              <label className="block text-sm font-bold text-textSecondary mb-2">
                Nombre *
              </label>
              <input
                type="text"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Ej: 8va, 6ta, 3ra"
                className="w-full px-4 py-3 bg-background border border-cardBorder rounded-lg text-textPrimary"
              />
              {/* Sugerencias */}
              <div className="flex flex-wrap gap-1 mt-2">
                {CATEGORIAS_SUGERIDAS.map((sug) => (
                  <button
                    key={sug}
                    type="button"
                    onClick={() => setNombre(sug)}
                    className="text-xs px-2 py-1 bg-cardBorder rounded hover:bg-primary/20 transition-colors"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>

            {/* Género */}
            <div className="mb-4">
              <label className="block text-sm font-bold text-textSecondary mb-2">
                Género
              </label>
              <div className="flex gap-2">
                {GENEROS.map((g) => (
                  <button
                    key={g.value}
                    type="button"
                    onClick={() => setGenero(g.value)}
                    className={`flex-1 py-2 rounded-lg border transition-all ${
                      genero === g.value
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-cardBorder text-textSecondary hover:border-primary/50'
                    }`}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Botones */}
            <div className="flex gap-3">
              <Button
                variant="ghost"
                onClick={() => setModalOpen(false)}
                className="flex-1"
                disabled={guardando}
              >
                Cancelar
              </Button>
              <Button
                variant="accent"
                onClick={guardarCategoria}
                className="flex-1"
                disabled={guardando || !nombre.trim()}
              >
                {guardando ? 'Guardando...' : editando ? 'Guardar' : 'Crear'}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </>
  );
}
