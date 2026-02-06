import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Users, Target, AlertCircle, X, RefreshCw, Calendar, Filter, Clock } from 'lucide-react';
import { torneoService, Categoria } from '../services/torneo.service';
import Card from './Card';
import Button from './Button';
import SkeletonLoader from './SkeletonLoader';
import { PlayerLink } from './UserLink';
import ModalHorariosPareja from './ModalHorariosPareja';

interface TorneoZonasProps {
  torneoId: number;
  esOrganizador: boolean;
}

interface TablaZona {
  zona_id: number;
  zona_nombre: string;
  categoria_id?: number;
  tabla: any[];
}

// Cache simple para evitar recargas innecesarias
const zonasCache: Record<number, { zonas: any[]; tablas: TablaZona[]; timestamp: number }> = {};
const CACHE_TTL = 60000; // 1 minuto

export default function TorneoZonas({ torneoId, esOrganizador }: TorneoZonasProps) {
  const [zonas, setZonas] = useState<any[]>([]);
  const [tablas, setTablas] = useState<TablaZona[]>([]);
  const [loading, setLoading] = useState(true);
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [categoriaFiltro, setCategoriaFiltro] = useState<number | null>(null);
  const [parejaHorarios, setParejaHorarios] = useState<any>(null);
  const [modalHorariosOpen, setModalHorariosOpen] = useState(false);

  useEffect(() => {
    // Guard: Solo cargar si torneoId es válido
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      setLoading(false);
      return;
    }
    cargarDatos();
    cargarCategorias();
  }, [torneoId]);

  // Seleccionar automáticamente la primera categoría cuando se cargan
  useEffect(() => {
    if (categorias.length > 0 && categoriaFiltro === null) {
      setCategoriaFiltro(categorias[0].id);
    }
  }, [categorias]);

  const cargarCategorias = async () => {
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) return;
    
    try {
      const cats = await torneoService.listarCategorias(torneoId);
      setCategorias(cats);
    } catch (err) {
      console.error('Error cargando categorías:', err);
    }
  };

  const cargarDatos = async (forzar: boolean = false) => {
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) return;
    
    // Verificar cache
    const cached = zonasCache[torneoId];
    if (!forzar && cached && Date.now() - cached.timestamp < CACHE_TTL) {
      setZonas(cached.zonas);
      setTablas(cached.tablas);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const zonasData = await torneoService.listarZonas(torneoId);
      setZonas(zonasData);

      // Cargar tablas de posiciones de todas las zonas
      let tablasData: TablaZona[] = [];
      if (zonasData.length > 0) {
        const tablasPromises = zonasData.map((zona: any) =>
          torneoService.obtenerTablaPosiciones(torneoId, zona.id)
        );
        tablasData = await Promise.all(tablasPromises);
        setTablas(tablasData);
      }

      // Guardar en cache
      zonasCache[torneoId] = {
        zonas: zonasData,
        tablas: tablasData,
        timestamp: Date.now()
      };
    } catch (error) {
      console.error('Error al cargar datos:', error);
    } finally {
      setLoading(false);
    }
  };

  // Función para invalidar cache y recargar
  const refrescarDatos = () => {
    delete zonasCache[torneoId];
    cargarDatos(true);
  };

  const generarZonas = async (categoriaId?: number) => {
    try {
      setGenerando(true);
      setError(null);
      const parejas = await torneoService.listarParejas(torneoId);
      // Filtrar por categoría si se especificó
      const parejasFiltradas = categoriaId 
        ? parejas.filter((p: any) => p.categoria_id === categoriaId && p.estado !== 'baja')
        : parejas.filter((p) => p.estado !== 'baja');
      const parejasIds = parejasFiltradas.map((p) => p.id);

      await torneoService.generarZonas(torneoId, parejasIds, categoriaId);
      // Invalidar cache y recargar
      refrescarDatos();
      await cargarCategorias();
    } catch (error: any) {
      console.error('Error al generar zonas:', error);
      setError(error.response?.data?.detail || 'Error al generar zonas');
    } finally {
      setGenerando(false);
    }
  };

  const eliminarZonas = async (categoriaId?: number) => {
    if (!confirm(`¿Estás seguro de eliminar las zonas${categoriaId ? ' de esta categoría' : ''}? Se perderán todos los partidos y resultados.`)) {
      return;
    }
    
    try {
      setGenerando(true);
      setError(null);
      await torneoService.eliminarZonas(torneoId, categoriaId);
      // Invalidar cache y recargar
      refrescarDatos();
      await cargarCategorias();
    } catch (error: any) {
      console.error('Error al eliminar zonas:', error);
      setError(error.response?.data?.detail || 'Error al eliminar zonas');
    } finally {
      setGenerando(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <SkeletonLoader height="300px" />
        <SkeletonLoader height="300px" />
      </div>
    );
  }

  // Verificar qué categorías ya tienen zonas
  const categoriasConZonas = new Set(zonas.map((z: any) => z.categoria_id).filter(Boolean));
  const categoriasSinZonas = categorias.filter(c => !categoriasConZonas.has(c.id));

  if (zonas.length === 0) {
    return (
      <Card>
        <div className="p-6 text-center">
          <Users size={48} className="mx-auto text-textSecondary mb-4" />
          <h3 className="text-xl font-bold text-textPrimary mb-2">
            Aún no se generaron las zonas
          </h3>
          <p className="text-textSecondary mb-6">
            {categorias.length > 0 
              ? 'Generá las zonas para cada categoría del torneo. Cada categoría tendrá sus propias zonas.'
              : 'Las zonas se generan automáticamente cuando hay suficientes parejas inscritas'
            }
          </p>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3"
            >
              <AlertCircle size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-left">
                <p className="text-red-500 font-medium text-sm">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-500/70 hover:text-red-500 transition-colors"
              >
                <X size={18} />
              </button>
            </motion.div>
          )}

          {esOrganizador && (
            <div className="space-y-3">
              {categorias.length > 0 ? (
                // Botones por categoría con iconos de género
                <div className="flex flex-wrap gap-2 justify-center">
                  {categorias.map((cat) => {
                    const esF = cat.genero === 'femenino';
                    const esMixto = cat.genero === 'mixto';
                    const colorClasses = esMixto 
                      ? 'bg-gradient-to-r from-blue-500 to-pink-500 hover:from-blue-600 hover:to-pink-600'
                      : esF
                      ? 'bg-gradient-to-r from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700'
                      : 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700';
                    
                    return (
                      <button
                        key={cat.id}
                        onClick={() => generarZonas(cat.id)}
                        disabled={generando}
                        className={`${colorClasses} text-white px-4 py-2 rounded-lg text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg hover:shadow-xl`}
                      >
                        <span className="text-base">
                          {esMixto ? '⚥' : esF ? '♀' : '♂'}
                        </span>
                        {generando ? 'Generando...' : `Generar ${cat.nombre}`}
                      </button>
                    );
                  })}
                </div>
              ) : (
                // Botón general si no hay categorías
                <Button onClick={() => generarZonas()} disabled={generando} variant="accent">
                  {generando ? 'Generando...' : 'Generar Zonas'}
                </Button>
              )}
            </div>
          )}
        </div>
      </Card>
    );
  }

  // Función para ir al tab de Fixture
  const irAlFixture = (zonaId?: number, categoriaId?: number) => {
    // Emitir evento para cambiar de tab con filtros opcionales
    window.dispatchEvent(new CustomEvent('cambiarTab', { 
      detail: 'partidos',
      // Pasar filtros adicionales si se proporcionan
      ...(zonaId && { zonaId }),
      ...(categoriaId && { categoriaId })
    }));
  };

  // Función para abrir modal de horarios
  const verHorariosPareja = (pareja: any) => {
    // Pasar el objeto completo de la pareja al modal
    setParejaHorarios(pareja);
    setModalHorariosOpen(true);
  };

  // Filtrar tablas por categoría (SIEMPRE filtrar, nunca mostrar todas)
  const tablasFiltradas = categoriaFiltro
    ? tablas.filter((t: any) => {
        const zona = zonas.find(z => z.id === t.zona_id);
        return zona?.categoria_id === categoriaFiltro;
      })
    : [];

  return (
    <div className="space-y-6">
      {/* Header con botones */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {/* Botón ir al fixture (solo organizador) */}
          {esOrganizador && (
            <Button
              onClick={irAlFixture}
              variant="accent"
              size="sm"
              className="flex items-center gap-2 text-xs"
            >
              <Calendar size={14} />
              Cargar Resultados
            </Button>
          )}
          
          {/* Botón eliminar zonas de categoría actual (solo organizador) */}
          {esOrganizador && categoriaFiltro && tablasFiltradas.length > 0 && (
            <Button
              onClick={() => {
                const cat = categorias.find(c => c.id === categoriaFiltro);
                if (confirm(`⚠️ ¿Estás seguro de eliminar las zonas de ${cat?.nombre}?\n\nSe eliminarán:\n- Todas las zonas\n- Todos los partidos\n- Todas las tablas de posiciones\n\nEsta acción NO se puede deshacer.`)) {
                  eliminarZonas(categoriaFiltro);
                }
              }}
              disabled={generando}
              variant="ghost"
              size="sm"
              className="flex items-center gap-1.5 text-xs text-red-500 hover:text-red-600 hover:bg-red-500/10 border border-red-500/30"
            >
              <X size={14} />
              Eliminar Zonas
            </Button>
          )}
        </div>
        
        {/* Botón refrescar */}
        <button
          onClick={refrescarDatos}
          disabled={loading}
          className="flex items-center gap-1.5 text-xs text-textSecondary hover:text-primary transition-colors px-2 py-1 rounded hover:bg-background self-end sm:self-auto"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Actualizar
        </button>
      </div>

      {/* Filtro por categoría */}
      {categorias.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          <Filter size={14} className="text-textSecondary flex-shrink-0" />
          {categorias.map((cat) => {
            const esF = cat.genero === 'femenino';
            const esMixto = cat.genero === 'mixto';
            const icon = esMixto ? '⚥' : esF ? '♀' : '♂';
            const colorClasses = categoriaFiltro === cat.id
              ? esMixto
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white'
                : esF
                ? 'bg-gradient-to-r from-pink-500 to-pink-600 text-white'
                : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
              : 'bg-cardBorder text-textSecondary hover:bg-primary/20';
            
            return (
              <button
                key={cat.id}
                onClick={() => setCategoriaFiltro(cat.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${colorClasses}`}
              >
                <span>{icon}</span>
                {cat.nombre}
              </button>
            );
          })}
        </div>
      )}

      {/* Botones para generar zonas de categorías faltantes */}
      {esOrganizador && categoriasSinZonas.length > 0 && (
        <div className="bg-accent/5 border border-accent/20 rounded-lg p-3">
          <p className="text-xs text-textSecondary mb-2">Categorías sin zonas:</p>
          <div className="flex flex-wrap gap-2">
            {categoriasSinZonas.map((cat) => {
              const esF = cat.genero === 'femenino';
              const esMixto = cat.genero === 'mixto';
              const colorClasses = esMixto 
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700'
                : esF
                ? 'bg-gradient-to-r from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700'
                : 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700';
              
              return (
                <button
                  key={cat.id}
                  onClick={() => generarZonas(cat.id)}
                  disabled={generando}
                  className={`${colorClasses} text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5`}
                >
                  <span>{esMixto ? '⚥' : esF ? '♀' : '♂'}</span>
                  {generando ? '...' : `Generar ${cat.nombre}`}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Tablas de posiciones de cada zona */}
      {tablasFiltradas.length === 0 && categoriaFiltro && zonas.length > 0 ? (
        // Mensaje cuando la categoría seleccionada no tiene zonas
        <Card>
          <div className="p-6 text-center">
            <Users size={48} className="mx-auto text-textSecondary mb-4" />
            <h3 className="text-xl font-bold text-textPrimary mb-2">
              Esta categoría aún no tiene zonas generadas
            </h3>
            <p className="text-textSecondary mb-6">
              {esOrganizador 
                ? 'Generá las zonas para esta categoría usando el botón de abajo'
                : 'El organizador aún no generó las zonas para esta categoría'
              }
            </p>
            {esOrganizador && (() => {
              const cat = categorias.find(c => c.id === categoriaFiltro);
              if (!cat) return null;
              const esF = cat.genero === 'femenino';
              const esMixto = cat.genero === 'mixto';
              const colorClasses = esMixto 
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700'
                : esF
                ? 'bg-gradient-to-r from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700'
                : 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700';
              
              return (
                <button
                  onClick={() => generarZonas(cat.id)}
                  disabled={generando}
                  className={`${colorClasses} text-white px-4 py-2 rounded-lg text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg hover:shadow-xl mx-auto`}
                >
                  <span className="text-base">
                    {esMixto ? '⚥' : esF ? '♀' : '♂'}
                  </span>
                  {generando ? 'Generando...' : `Generar ${cat.nombre}`}
                </button>
              );
            })()}
          </div>
        </Card>
      ) : (
        tablasFiltradas.map((tabla, index) => (
        <motion.div
          key={tabla.zona_id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Card>
            <div className="p-4 md:p-6">
              {/* Header de la zona */}
              <div className="flex items-center gap-3 mb-4 pb-3 border-b border-cardBorder">
                <div className="bg-gradient-to-br from-primary to-accent p-2 rounded-lg">
                  <Target size={20} className="text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-lg md:text-xl font-bold text-textPrimary">
                      {tabla.zona_nombre}
                    </h3>
                    {/* Badge de categoría con género */}
                    {tabla.categoria_id && (() => {
                      const cat = categorias.find(c => c.id === tabla.categoria_id);
                      if (!cat) return null;
                      const esF = cat.genero === 'femenino';
                      const esMixto = cat.genero === 'mixto';
                      const colorClasses = esMixto
                        ? 'bg-gradient-to-r from-purple-500 to-purple-600'
                        : esF
                        ? 'bg-gradient-to-r from-pink-500 to-pink-600'
                        : 'bg-gradient-to-r from-blue-500 to-blue-600';
                      
                      return (
                        <span className={`${colorClasses} text-white px-2 py-1 rounded-full text-xs font-bold flex items-center gap-1`}>
                          <span>{esMixto ? '⚥' : esF ? '♀' : '♂'}</span>
                          {cat.nombre}
                        </span>
                      );
                    })()}
                  </div>
                  <p className="text-xs text-textSecondary">Tabla de Posiciones</p>
                </div>
                <div className="bg-primary/10 px-3 py-1 rounded-full">
                  <span className="text-primary font-bold text-sm">
                    {tabla.tabla?.length || 0} parejas
                  </span>
                </div>
              </div>

              {/* Tabla de posiciones */}
              <div className="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0">
                <table className="w-full min-w-[600px]">
                  <thead>
                    <tr className="border-b-2 border-primary/20">
                      <th className="text-left py-2 md:py-3 px-2 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        Pos
                      </th>
                      <th className="text-left py-2 md:py-3 px-2 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        Pareja
                      </th>
                      <th className="text-center py-2 md:py-3 px-1 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        PJ
                      </th>
                      <th className="text-center py-2 md:py-3 px-1 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        PG
                      </th>
                      <th className="text-center py-2 md:py-3 px-1 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        PP
                      </th>
                      <th className="text-center py-2 md:py-3 px-1 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        SG
                      </th>
                      <th className="text-center py-2 md:py-3 px-1 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        SP
                      </th>
                      <th className="text-center py-2 md:py-3 px-1 text-textSecondary text-[10px] md:text-xs font-bold uppercase hidden md:table-cell">
                        GG
                      </th>
                      <th className="text-center py-2 md:py-3 px-1 text-textSecondary text-[10px] md:text-xs font-bold uppercase hidden md:table-cell">
                        GP
                      </th>
                      <th className="text-center py-2 md:py-3 px-2 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        Pts
                      </th>
                      <th className="text-center py-2 md:py-3 px-2 text-textSecondary text-[10px] md:text-xs font-bold uppercase">
                        
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {tabla.tabla?.map((item: any, idx: number) => (
                      <tr
                        key={item.pareja_id}
                        className={`border-b border-cardBorder/50 transition-colors hover:bg-background/50 ${
                          item.eliminada 
                            ? 'bg-red-500/5 opacity-60' 
                            : idx < 2 
                            ? 'bg-green-500/5' 
                            : ''
                        }`}
                      >
                        <td className="py-2 md:py-3 px-2">
                          <div className="flex items-center gap-1">
                            {!item.eliminada && idx < 2 && (
                              <Trophy size={12} className="text-green-500" />
                            )}
                            {item.eliminada && (
                              <span className="text-red-500 text-xs">❌</span>
                            )}
                            <span
                              className={`font-bold text-xs md:text-sm ${
                                item.eliminada
                                  ? 'text-red-500/70 line-through'
                                  : idx < 2 
                                  ? 'text-green-500' 
                                  : 'text-textPrimary'
                              }`}
                            >
                              {item.posicion}
                            </span>
                          </div>
                        </td>
                        <td className="py-2 md:py-3 px-2">
                          <div className="flex items-center gap-2">
                            {item.eliminada ? (
                              <span className="text-red-500/70 font-medium text-xs md:text-sm line-through flex items-center gap-1">
                                <span className="text-red-500">❌</span>
                                Pareja Eliminada
                              </span>
                            ) : item.jugador1_id && item.jugador2_id ? (
                              <span className="text-textPrimary font-medium text-xs md:text-sm truncate max-w-[100px] md:max-w-none flex items-center gap-1">
                                <PlayerLink 
                                  id={item.jugador1_id} 
                                  nombre={item.jugador1_nombre || 'J1'} 
                                  nombreUsuario={item.jugador1_username}
                                  size="sm" 
                                />
                                <span>/</span>
                                <PlayerLink 
                                  id={item.jugador2_id} 
                                  nombre={item.jugador2_nombre || 'J2'}
                                  nombreUsuario={item.jugador2_username}
                                  size="sm" 
                                />
                              </span>
                            ) : (
                              <span className="text-textPrimary font-medium text-xs md:text-sm truncate max-w-[100px] md:max-w-none">
                                {item.pareja_nombre || 'Pareja'}
                              </span>
                            )}
                            {!item.eliminada && idx < 2 && (
                              <span className="hidden md:inline-flex px-1.5 py-0.5 bg-green-500/20 text-green-500 text-[9px] font-bold rounded uppercase">
                                Clasifica
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-2 md:py-3 px-1 text-center">
                          <span className={`text-xs md:text-sm ${item.eliminada ? 'text-red-500/50 line-through' : 'text-textSecondary'}`}>
                            {item.partidos_jugados}
                          </span>
                        </td>
                        <td className="py-2 md:py-3 px-1 text-center">
                          <span className={`font-bold text-xs md:text-sm ${item.eliminada ? 'text-red-500/50 line-through' : 'text-green-500'}`}>
                            {item.partidos_ganados}
                          </span>
                        </td>
                        <td className="py-2 md:py-3 px-1 text-center">
                          <span className={`font-bold text-xs md:text-sm ${item.eliminada ? 'text-red-500/50 line-through' : 'text-red-500'}`}>
                            {item.partidos_perdidos}
                          </span>
                        </td>
                        <td className="py-2 md:py-3 px-1 text-center">
                          <span className={`text-xs md:text-sm ${item.eliminada ? 'text-red-500/50 line-through' : 'text-textSecondary'}`}>
                            {item.sets_ganados}
                          </span>
                        </td>
                        <td className="py-2 md:py-3 px-1 text-center">
                          <span className={`text-xs md:text-sm ${item.eliminada ? 'text-red-500/50 line-through' : 'text-textSecondary'}`}>
                            {item.sets_perdidos}
                          </span>
                        </td>
                        <td className="py-2 md:py-3 px-1 text-center hidden md:table-cell">
                          <span className={`text-xs md:text-sm ${item.eliminada ? 'text-red-500/50 line-through' : 'text-green-500/70'}`}>
                            {item.games_ganados}
                          </span>
                        </td>
                        <td className="py-2 md:py-3 px-1 text-center hidden md:table-cell">
                          <span className={`text-xs md:text-sm ${item.eliminada ? 'text-red-500/50 line-through' : 'text-red-500/70'}`}>
                            {item.games_perdidos}
                          </span>
                        </td>
                        <td className="py-2 md:py-3 px-2 text-center">
                          <span className={`font-bold text-sm md:text-base px-2 py-0.5 rounded-full ${
                            item.eliminada 
                              ? 'text-red-500/50 bg-red-500/5 line-through' 
                              : 'text-primary bg-primary/10'
                          }`}>
                            {item.puntos}
                          </span>
                        </td>
                        <td className="py-2 md:py-3 px-2 text-center">
                          <button
                            onClick={() => verHorariosPareja(item)}
                            className="p-1.5 hover:bg-primary/10 rounded-lg transition-colors text-primary hover:text-accent"
                            title="Ver horarios disponibles"
                          >
                            <Clock size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Botón Cargar Resultados para esta zona */}
              {esOrganizador && (
                <div className="mt-4 pt-4 border-t border-cardBorder">
                  <Button
                    onClick={() => irAlFixture(tabla.zona_id, tabla.categoria_id)}
                    variant="accent"
                    size="sm"
                    className="w-full flex items-center justify-center gap-2"
                  >
                    <Calendar size={16} />
                    Cargar Resultados de {tabla.zona_nombre}
                  </Button>
                </div>
              )}
            </div>
          </Card>
        </motion.div>
      )))}

      {/* Info de clasificación */}
      <div className="flex flex-wrap gap-3 justify-center">
        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 rounded-full border border-green-500/20">
          <Trophy size={14} className="text-green-500" />
          <span className="text-xs text-green-500 font-medium">
            Los primeros 2 de cada zona clasifican a Playoffs
          </span>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full border border-primary/20">
          <Target size={14} className="text-primary" />
          <span className="text-xs text-primary font-medium">
            Desempate: Puntos → Sets → Games
          </span>
        </div>
      </div>

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
    </div>
  );
}
