import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, Check, X, Trash2, AlertCircle, Filter, RefreshCw, Clock } from 'lucide-react';
import { torneoService, Pareja, Categoria } from '../services/torneo.service';
import Card from './Card';
import Button from './Button';
import { PlayerLink } from './UserLink';
import ModalHorariosPareja from './ModalHorariosPareja';

interface TorneoParejaProps {
  torneoId: number;
  parejas: Pareja[];
  esOrganizador: boolean;
  onUpdate: () => void;
}

export default function TorneoParejas({
  torneoId,
  parejas,
  esOrganizador,
  onUpdate,
}: TorneoParejaProps) {
  console.log('🔍 COMPONENT - TorneoParejas recibió parejas:', parejas.slice(0, 2));
  
  const [loading, setLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [categoriaFiltro, setCategoriaFiltro] = useState<number | null>(null);
  
  // Modal cambiar categoría
  const [parejaEditando, setParejaEditando] = useState<Pareja | null>(null);
  const [nuevaCategoriaId, setNuevaCategoriaId] = useState<number | null>(null);
  
  // Modal horarios
  const [parejaHorarios, setParejaHorarios] = useState<any>(null);
  const [modalHorariosOpen, setModalHorariosOpen] = useState(false);

  useEffect(() => {
    // Guard: Solo cargar si torneoId es válido
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      return;
    }
    cargarCategorias();
  }, [torneoId]);

  const cargarCategorias = async () => {
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) return;
    
    try {
      const cats = await torneoService.listarCategorias(torneoId);
      setCategorias(cats);
    } catch (err) {
      console.error('Error cargando categorías:', err);
    }
  };

  const confirmarPareja = async (parejaId: number) => {
    try {
      setLoading(parejaId);
      setError(null);
      await torneoService.confirmarPareja(torneoId, parejaId);
      onUpdate();
    } catch (err: any) {
      console.error('Error al confirmar pareja:', err);
      setError(err.response?.data?.detail || 'Error al confirmar pareja');
    } finally {
      setLoading(null);
    }
  };

  const rechazarPareja = async (parejaId: number) => {
    if (!confirm('¿Estás seguro de eliminar esta pareja del torneo?')) return;

    try {
      setLoading(parejaId);
      setError(null);
      await torneoService.rechazarPareja(torneoId, parejaId);
      onUpdate();
    } catch (err: any) {
      console.error('Error al rechazar pareja:', err);
      setError(err.response?.data?.detail || 'Error al eliminar pareja');
    } finally {
      setLoading(null);
    }
  };

  const darBajaPareja = async (parejaId: number) => {
    if (!confirm('¿Estás seguro de dar de baja esta pareja?')) return;

    try {
      setLoading(parejaId);
      setError(null);
      await torneoService.darBajaPareja(torneoId, parejaId, 'Baja por organizador');
      onUpdate();
    } catch (err: any) {
      console.error('Error al dar de baja:', err);
      setError(err.response?.data?.detail || 'Error al dar de baja');
    } finally {
      setLoading(null);
    }
  };

  const cambiarCategoria = async () => {
    if (!parejaEditando || !nuevaCategoriaId) return;
    
    try {
      setLoading(parejaEditando.id);
      setError(null);
      await torneoService.cambiarCategoriaPareja(torneoId, parejaEditando.id, nuevaCategoriaId);
      setParejaEditando(null);
      setNuevaCategoriaId(null);
      await cargarCategorias(); // Recargar para actualizar conteos
      onUpdate();
    } catch (err: any) {
      console.error('Error al cambiar categoría:', err);
      setError(err.response?.data?.detail || 'Error al cambiar categoría');
    } finally {
      setLoading(null);
    }
  };

  const abrirModalCategoria = async (pareja: Pareja) => {
    setParejaEditando(pareja);
    setNuevaCategoriaId((pareja as any).categoria_id || null);
    // Recargar categorías para tener el conteo actualizado
    await cargarCategorias();
  };

  const verHorariosPareja = (pareja: any) => {
    // Pasar el objeto completo de la pareja al modal
    setParejaHorarios(pareja);
    setModalHorariosOpen(true);
  };

  // Filtrar por categoría
  const parejasFiltradas = categoriaFiltro 
    ? parejas.filter((p: any) => p.categoria_id === categoriaFiltro)
    : parejas;
  
  const parejasActivas = parejasFiltradas.filter((p) => p.estado !== 'baja');
  const parejasBaja = parejasFiltradas.filter((p) => p.estado === 'baja');
  
  // Obtener nombre de categoría
  const getNombreCategoria = (categoriaId: number | null) => {
    if (!categoriaId) return null;
    const cat = categorias.find(c => c.id === categoriaId);
    return cat?.nombre;
  };

  if (parejas.length === 0) {
    return (
      <Card>
        <div className="p-6 text-center py-12">
          <Users size={48} className="mx-auto text-textSecondary mb-4" />
          <p className="text-textSecondary">Aún no hay parejas inscritas</p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-4 md:p-6">
        {/* Error message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3"
          >
            <AlertCircle size={18} className="text-red-500 flex-shrink-0" />
            <p className="text-red-500 text-sm flex-1">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-500/70 hover:text-red-500"
            >
              <X size={16} />
            </button>
          </motion.div>
        )}

        {/* Header con contador */}
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-cardBorder">
          <h3 className="font-bold text-textPrimary flex items-center gap-2">
            <Users size={20} className="text-primary" />
            Parejas Inscritas
          </h3>
          <div className="flex gap-2">
            <span className="px-3 py-1 bg-green-500/10 text-green-500 rounded-full text-xs font-bold">
              {parejasFiltradas.filter((p) => p.estado === 'confirmada').length} confirmadas
            </span>
            <span className="px-3 py-1 bg-yellow-500/10 text-yellow-500 rounded-full text-xs font-bold">
              {parejasFiltradas.filter((p) => p.estado === 'inscripta').length} pendientes
            </span>
          </div>
        </div>

        {/* Filtro por categoría */}
        {categorias.length > 0 && (
          <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
            <Filter size={14} className="text-textSecondary flex-shrink-0" />
            <button
              onClick={() => setCategoriaFiltro(null)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all ${
                categoriaFiltro === null
                  ? 'bg-primary text-white'
                  : 'bg-cardBorder text-textSecondary hover:bg-primary/20'
              }`}
            >
              Todas ({parejas.length})
            </button>
            {categorias.map((cat) => {
              const count = parejas.filter((p: any) => p.categoria_id === cat.id).length;
              return (
                <button
                  key={cat.id}
                  onClick={() => setCategoriaFiltro(cat.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all ${
                    categoriaFiltro === cat.id
                      ? 'bg-primary text-white'
                      : 'bg-cardBorder text-textSecondary hover:bg-primary/20'
                  }`}
                >
                  {cat.nombre} ({count})
                </button>
              );
            })}
          </div>
        )}

        {/* Lista de parejas activas */}
        <div className="space-y-2">
          {parejasActivas.map((pareja, index) => (
            <motion.div
              key={pareja.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.03 }}
              className="flex items-center justify-between p-3 md:p-4 bg-background rounded-lg hover:bg-background/80 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold flex-shrink-0">
                  {index + 1}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-bold text-textPrimary text-sm md:text-base truncate">
                      {pareja.nombre_pareja}
                    </p>
                    {getNombreCategoria((pareja as any).categoria_id) && (
                      <span className="px-1.5 py-0.5 bg-accent/10 text-accent text-[10px] font-bold rounded">
                        {getNombreCategoria((pareja as any).categoria_id)}
                      </span>
                    )}
                  </div>
                  {pareja.jugador1_nombre && pareja.jugador2_nombre && (
                    <div className="text-xs text-textSecondary flex items-center gap-1 flex-wrap">
                      <PlayerLink 
                        id={(pareja as any).jugador1_id} 
                        nombre={pareja.jugador1_nombre} 
                        nombreUsuario={(pareja as any).jugador1_username}
                        size="sm" 
                      />
                      <span>&</span>
                      <PlayerLink 
                        id={(pareja as any).jugador2_id} 
                        nombre={pareja.jugador2_nombre}
                        nombreUsuario={(pareja as any).jugador2_username}
                        size="sm" 
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {/* Estado badge */}
                <span
                  className={`px-2 md:px-3 py-1 rounded-full text-[10px] md:text-xs font-bold ${
                    pareja.estado === 'confirmada'
                      ? 'bg-green-500/10 text-green-500'
                      : 'bg-yellow-500/10 text-yellow-500'
                  }`}
                >
                  {pareja.estado === 'confirmada' ? 'Confirmada' : 'Pendiente'}
                </span>

                {/* Botones de acción para organizador */}
                {esOrganizador && (
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => verHorariosPareja(pareja)}
                      className="p-2 hover:bg-primary/10 hover:text-primary"
                      title="Ver horarios disponibles"
                    >
                      <Clock size={16} />
                    </Button>
                    {categorias.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => abrirModalCategoria(pareja)}
                        disabled={loading === pareja.id}
                        className="p-2 hover:bg-accent/10 hover:text-accent"
                        title="Cambiar categoría"
                      >
                        <RefreshCw size={16} />
                      </Button>
                    )}
                    {pareja.estado === 'inscripta' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => confirmarPareja(pareja.id)}
                        disabled={loading === pareja.id}
                        className="p-2 hover:bg-green-500/10 hover:text-green-500"
                        title="Confirmar pareja"
                      >
                        <Check size={16} />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        pareja.estado === 'inscripta'
                          ? rechazarPareja(pareja.id)
                          : darBajaPareja(pareja.id)
                      }
                      disabled={loading === pareja.id}
                      className="p-2 hover:bg-red-500/10 hover:text-red-500"
                      title="Eliminar pareja"
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Parejas dadas de baja */}
        {parejasBaja.length > 0 && (
          <div className="mt-6 pt-4 border-t border-cardBorder">
            <h4 className="text-sm font-bold text-textSecondary mb-3">
              Parejas dadas de baja ({parejasBaja.length})
            </h4>
            <div className="space-y-2 opacity-60">
              {parejasBaja.map((pareja) => (
                <div
                  key={pareja.id}
                  className="flex items-center justify-between p-3 bg-background/50 rounded-lg"
                >
                  <p className="text-textSecondary text-sm line-through">
                    {pareja.nombre_pareja}
                  </p>
                  <span className="px-2 py-1 bg-red-500/10 text-red-500 rounded-full text-xs font-bold">
                    Baja
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Acciones masivas para organizador */}
        {esOrganizador && parejas.filter((p) => p.estado === 'inscripta').length > 0 && (
          <div className="mt-6 pt-4 border-t border-cardBorder">
            <Button
              variant="accent"
              onClick={async () => {
                const pendientes = parejas.filter((p) => p.estado === 'inscripta');
                for (const pareja of pendientes) {
                  await confirmarPareja(pareja.id);
                }
              }}
              className="w-full"
            >
              <Check size={18} className="mr-2" />
              Confirmar todas las parejas pendientes
            </Button>
          </div>
        )}
      </div>

      {/* Modal cambiar categoría */}
      {parejaEditando && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-card rounded-xl max-w-sm w-full p-4"
          >
            <h3 className="text-lg font-bold text-textPrimary mb-2">
              Cambiar Categoría
            </h3>
            <p className="text-sm text-textSecondary mb-4">
              {parejaEditando.nombre_pareja}
            </p>

            <div className="space-y-2 mb-4">
              {categorias.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setNuevaCategoriaId(cat.id)}
                  className={`w-full p-3 rounded-lg border text-left transition-all ${
                    nuevaCategoriaId === cat.id
                      ? 'border-primary bg-primary/10'
                      : 'border-cardBorder hover:border-primary/50'
                  }`}
                >
                  <span className="font-bold text-textPrimary">{cat.nombre}</span>
                  <span className={`ml-2 text-xs ${
                    cat.genero === 'masculino' ? 'text-blue-400' : 'text-pink-400'
                  }`}>
                    {cat.genero === 'masculino' ? '♂' : '♀'}
                  </span>
                  <p className="text-xs text-textSecondary">
                    {cat.parejas_inscritas} parejas inscritas
                  </p>
                </button>
              ))}
            </div>

            <div className="flex gap-2">
              <Button
                variant="ghost"
                onClick={() => {
                  setParejaEditando(null);
                  setNuevaCategoriaId(null);
                }}
                className="flex-1"
                disabled={loading === parejaEditando.id}
              >
                Cancelar
              </Button>
              <Button
                variant="accent"
                onClick={cambiarCategoria}
                className="flex-1"
                disabled={loading === parejaEditando.id || !nuevaCategoriaId || nuevaCategoriaId === (parejaEditando as any).categoria_id}
              >
                {loading === parejaEditando.id ? 'Guardando...' : 'Guardar'}
              </Button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Modal Horarios */}
      {parejaHorarios && (
        <ModalHorariosPareja
          isOpen={modalHorariosOpen}
          onClose={() => {
            setModalHorariosOpen(false);
            setParejaHorarios(null);
          }}
          pareja={parejaHorarios}
        />
      )}
    </Card>
  );
}
