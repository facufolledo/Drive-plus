import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Trophy, AlertCircle, X, MapPin, Clock, Camera, Filter } from 'lucide-react';
import { torneoService, Categoria } from '../services/torneo.service';
import Card from './Card';
import Button from './Button';
import SkeletonLoader from './SkeletonLoader';
import ModalCargarResultado from './ModalCargarResultado';
import ModalHorariosPareja from './ModalHorariosPareja';
import ModalCambiarHorario from './ModalCambiarHorario';
import html2canvas from 'html2canvas';

interface TorneoFixtureProps {
  torneoId: number;
  esOrganizador: boolean;
}

export default function TorneoFixture({ torneoId, esOrganizador }: TorneoFixtureProps) {
  const [partidos, setPartidos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generando, setGenerando] = useState(false);
  const [partidoSeleccionado, setPartidoSeleccionado] = useState<any>(null);
  const [modalResultadoOpen, setModalResultadoOpen] = useState(false);
  const [filtroZona, setFiltroZona] = useState<string | null>(null);
  const [zonas, setZonas] = useState<any[]>([]);
  const [canchas, setCanchas] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [capturando, setCapturando] = useState(false);
  const fixtureRef = useRef<HTMLDivElement>(null);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [categoriaFiltro, setCategoriaFiltro] = useState<number | null>(null);
  const [partidosNoProgramados, setPartidosNoProgramados] = useState<any[]>([]);
  const [parejaHorarios, setParejaHorarios] = useState<any>(null);
  const [modalHorariosOpen, setModalHorariosOpen] = useState(false);
  const [partidoEditando, setPartidoEditando] = useState<any>(null);
  const [modalCambiarHorarioOpen, setModalCambiarHorarioOpen] = useState(false);

  // Helper para parsear fechas sin conversión de zona horaria
  const parseFechaLocal = (fechaStr: string) => {
    const fecha = new Date(fechaStr);
    const year = fecha.getUTCFullYear();
    const month = fecha.getUTCMonth();
    const day = fecha.getUTCDate();
    const hours = fecha.getUTCHours();
    const minutes = fecha.getUTCMinutes();
    const seconds = fecha.getUTCSeconds();
    return new Date(year, month, day, hours, minutes, seconds);
  };

  useEffect(() => {
    // Guard: Solo cargar si torneoId es válido
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      setLoading(false);
      return;
    }
    cargarDatos();
  }, [torneoId]);

  // Seleccionar automáticamente la primera categoría cuando se cargan
  useEffect(() => {
    if (categorias.length > 0 && categoriaFiltro === null) {
      setCategoriaFiltro(categorias[0].id);
    }
  }, [categorias]);

  // Escuchar evento de cambio de tab con filtros
  useEffect(() => {
    const handleCambiarTabConFiltros = (event: any) => {
      if (event.detail.zonaId) {
        setFiltroZona(event.detail.zonaId.toString());
      }
      if (event.detail.categoriaId) {
        setCategoriaFiltro(event.detail.categoriaId);
      }
    };
    window.addEventListener('cambiarTab', handleCambiarTabConFiltros);
    return () => window.removeEventListener('cambiarTab', handleCambiarTabConFiltros);
  }, []);

  const cargarDatos = async () => {
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) return;
    
    try {
      setLoading(true);
      const [partidosResponse, zonasData, canchasData, categoriasData] = await Promise.all([
        torneoService.listarPartidos(torneoId),
        torneoService.listarZonas(torneoId),
        torneoService.listarCanchas(torneoId).catch(() => []),
        torneoService.listarCategorias(torneoId).catch(() => [])
      ]);
      // El endpoint retorna { total, partidos }, necesitamos solo el array
      const partidosArray = Array.isArray(partidosResponse) 
        ? partidosResponse 
        : (partidosResponse as any).partidos || [];
      setPartidos(partidosArray);
      setZonas(zonasData);
      setCanchas(canchasData);
      setCategorias(categoriasData);
    } catch (error) {
      console.error('Error al cargar datos:', error);
    } finally {
      setLoading(false);
    }
  };

  // Función para capturar el fixture como imagen
  const capturarFixture = async () => {
    if (!fixtureRef.current) return;
    
    try {
      setCapturando(true);
      const canvas = await html2canvas(fixtureRef.current, {
        backgroundColor: '#1a1a2e',
        scale: 2,
        useCORS: true,
      });
      
      // Crear link de descarga
      const link = document.createElement('a');
      link.download = `fixture-torneo-${torneoId}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Error al capturar fixture:', error);
    } finally {
      setCapturando(false);
    }
  };

  // Obtener nombre de cancha por ID
  const getNombreCancha = (canchaId: number | null) => {
    if (!canchaId) return null;
    const cancha = canchas.find(c => c.id === canchaId);
    return cancha?.nombre || `Cancha ${canchaId}`;
  };

  const generarFixture = async (categoriaId?: number) => {
    try {
      setGenerando(true);
      setError(null);
      setPartidosNoProgramados([]);
      const resultado = await torneoService.generarFixture(torneoId, categoriaId);
      
      // Si hay partidos no programados, guardarlos para mostrar alerta
      if (resultado.partidos_sin_programar && resultado.partidos_sin_programar.length > 0) {
        setPartidosNoProgramados(resultado.partidos_sin_programar);
      }
      
      await cargarDatos();
    } catch (error: any) {
      console.error('Error al generar fixture:', error);
      console.error('Error response data:', error.response?.data);
      
      // Manejar correctamente el error 422 de FastAPI
      let errorMsg = 'Error al generar fixture';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        // Si detail es un array (error de validación 422)
        if (Array.isArray(detail)) {
          errorMsg = detail.map((err: any) => {
            if (typeof err === 'string') return err;
            return err.msg || err.message || 'Error de validación';
          }).join(', ');
        } else if (typeof detail === 'string') {
          errorMsg = detail;
        } else {
          // Si detail es un objeto, convertir a string seguro
          errorMsg = JSON.stringify(detail);
        }
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      setError(errorMsg);
    } finally {
      setGenerando(false);
    }
  };

  const eliminarFixture = async (categoriaId?: number) => {
    const categoriaTexto = categoriaId 
      ? categorias.find(c => c.id === categoriaId)?.nombre || `categoría ${categoriaId}`
      : 'todo el torneo';
    
    const confirmacion = window.confirm(
      `⚠️ ELIMINAR FIXTURE\n\n` +
      `¿Estás seguro de que quieres eliminar el fixture de ${categoriaTexto}?\n\n` +
      '• Esta acción no se puede deshacer\n' +
      '• Se eliminarán todos los partidos programados\n' +
      '• Los resultados ya cargados se mantendrán\n\n' +
      'Presiona OK para confirmar o Cancelar para abortar.'
    );
    
    if (!confirmacion) return;
    
    try {
      setGenerando(true);
      setError(null);
      
      await torneoService.eliminarFixture(torneoId, categoriaId);
      await cargarDatos();
      
      // Mostrar mensaje de éxito temporal
      const mensajeExito = `✅ Fixture de ${categoriaTexto} eliminado exitosamente`;
      setError(mensajeExito);
      setTimeout(() => setError(null), 4000);
      
    } catch (error: any) {
      console.error('Error al eliminar fixture:', error);
      
      let errorMsg = 'Error al eliminar fixture';
      if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      setError(`❌ ${errorMsg}`);
    } finally {
      setGenerando(false);
    }
  };

  const abrirModalResultado = (partido: any) => {
    setPartidoSeleccionado(partido);
    setModalResultadoOpen(true);
  };

  const verHorariosPareja = (partido: any, pareja: 'pareja1' | 'pareja2') => {
    const nombre_pareja = pareja === 'pareja1' ? partido.pareja1_nombre : partido.pareja2_nombre;
    const disponibilidad = pareja === 'pareja1' ? partido.pareja1_disponibilidad : partido.pareja2_disponibilidad;
    
    setParejaHorarios({
      nombre_pareja: nombre_pareja || 'Pareja',
      disponibilidad_horaria: disponibilidad
    });
    setModalHorariosOpen(true);
  };

  const handleResultadoCargado = (partidoActualizado?: any) => {
    setModalResultadoOpen(false);
    
    // Actualizar solo el partido modificado en lugar de recargar todo
    if (partidoActualizado) {
      setPartidos(prev => prev.map(p => 
        p.id_partido === partidoActualizado.id_partido ? partidoActualizado : p
      ));
    } else {
      // Si no tenemos el partido actualizado, recargar todo
      cargarDatos();
    }
    
    setPartidoSeleccionado(null);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <SkeletonLoader height="60px" />
        <SkeletonLoader height="300px" />
        <SkeletonLoader height="300px" />
      </div>
    );
  }

  if (partidos.length === 0) {
    return (
      <Card>
        <div className="p-6 text-center">
          <Calendar size={48} className="mx-auto text-textSecondary mb-4" />
          <h3 className="text-xl font-bold text-textPrimary mb-2">
            Aún no se generó el fixture
          </h3>
          <p className="text-textSecondary mb-6">
            El fixture se genera después de crear las zonas
          </p>
          
          {/* Mensaje de error/éxito */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`mb-4 p-4 rounded-lg flex items-start gap-3 ${
                error.startsWith('✅') 
                  ? 'bg-green-500/10 border border-green-500/30' 
                  : 'bg-red-500/10 border border-red-500/30'
              }`}
            >
              <AlertCircle 
                size={20} 
                className={`flex-shrink-0 mt-0.5 ${
                  error.startsWith('✅') ? 'text-green-500' : 'text-red-500'
                }`} 
              />
              <div className="flex-1 text-left">
                <p className={`font-medium text-sm ${
                  error.startsWith('✅') ? 'text-green-500' : 'text-red-500'
                }`}>
                  {typeof error === 'string' ? error : 'Error inesperado'}
                </p>
              </div>
              <button
                onClick={() => setError(null)}
                className={`transition-colors ${
                  error.startsWith('✅') 
                    ? 'text-green-500/70 hover:text-green-500' 
                    : 'text-red-500/70 hover:text-red-500'
                }`}
              >
                <X size={18} />
              </button>
            </motion.div>
          )}
          
          {esOrganizador && (
            <div className="space-y-3">
              {/* Botones de generar */}
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => generarFixture()}
                  disabled={generando}
                  variant="accent"
                  className="flex-1 min-w-[200px]"
                >
                  {generando ? 'Generando...' : 'Generar Fixture Completo'}
                </Button>
              </div>
              
              {/* Botones por categoría - SIEMPRE MOSTRAR si hay categorías */}
              {categorias.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm text-textSecondary font-medium">
                  {partidos.length > 0 ? 'Generar/Regenerar por categoría:' : 'O generar por categoría:'}
                </p>
                <div className="flex flex-wrap gap-2">
                  {categorias.map(cat => {
                    const esF = cat.genero === 'femenino';
                    const esMixto = cat.genero === 'mixto';
                    const icon = esMixto ? '⚥' : esF ? '♀' : '♂';
                    const colorClass = esMixto 
                      ? 'from-purple-500 to-purple-600' 
                      : esF 
                        ? 'from-pink-500 to-pink-600' 
                        : 'from-blue-500 to-blue-600';
                    
                    return (
                      <Button
                        key={cat.id}
                        onClick={() => generarFixture(cat.id)}
                        disabled={generando}
                        variant="secondary"
                        className={`flex items-center gap-2 bg-gradient-to-r ${colorClass} text-white hover:opacity-90`}
                      >
                        <span>{icon}</span>
                        <span>{cat.nombre}</span>
                      </Button>
                    );
                  })}
                </div>
              </div>
            )}
            
            {/* Botones de eliminar (solo si hay partidos) */}
            {partidos.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2 border-t border-cardBorder/50">
                <Button
                  onClick={() => eliminarFixture()}
                  disabled={generando}
                  variant="danger"
                  size="sm"
                  className="flex-1 min-w-[180px]"
                >
                  {generando ? 'Eliminando...' : 'Eliminar Todo el Fixture'}
                </Button>
                
                {categoriaFiltro && (
                  <Button
                    onClick={() => eliminarFixture(categoriaFiltro)}
                    disabled={generando}
                    variant="danger"
                    size="sm"
                    className="flex-1 min-w-[180px]"
                  >
                    {generando ? 'Eliminando...' : 'Eliminar Esta Categoría'}
                  </Button>
                )}
              </div>
            )}
            </div>
          )}
        </div>
      </Card>
    );
  }

  // Filtrar zonas por categoría seleccionada
  const zonasFiltradasPorCategoria = categoriaFiltro
    ? zonas.filter((z: any) => z.categoria_id === categoriaFiltro)
    : zonas;

  // Filtrar partidos por categoría
  const partidosFiltrados = categoriaFiltro
    ? partidos.filter((p: any) => p.categoria_id === categoriaFiltro)
    : partidos;

  // Agrupar partidos por zona
  const partidosPorZona = partidosFiltrados.reduce((acc: any, partido: any) => {
    const zonaId = partido.zona_id || 'sin_zona';
    if (!acc[zonaId]) {
      acc[zonaId] = [];
    }
    acc[zonaId].push(partido);
    return acc;
  }, {});

  const zonasConPartidos = Object.keys(partidosPorZona).map(zonaId => {
    const zona = zonas.find(z => z.id === parseInt(zonaId));
    // Si no hay zona, mostrar la fase del partido (playoffs)
    let nombre = zona?.nombre || 'Sin zona';
    if (!zona && partidosPorZona[zonaId]?.length > 0) {
      const fase = partidosPorZona[zonaId][0]?.fase;
      if (fase) {
        const fasesNombres: Record<string, string> = {
          'semifinal': 'Semifinales',
          'semis': 'Semifinales',
          'final': 'Final',
          'cuartos': 'Cuartos de Final',
          '4tos': 'Cuartos de Final',
          '8vos': 'Octavos de Final',
          '16avos': 'Dieciseisavos de Final'
        };
        nombre = fasesNombres[fase] || fase.charAt(0).toUpperCase() + fase.slice(1);
      }
    }
    return {
      id: zonaId,
      nombre,
      partidos: partidosPorZona[zonaId]
    };
  });

  return (
    <div className="space-y-6">
      {/* Alerta de partidos no programados */}
      {partidosNoProgramados.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
        >
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-yellow-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-yellow-500 font-bold text-sm mb-2">
                ⚠️ Partidos sin programar por incompatibilidad horaria
              </h4>
              <p className="text-yellow-500/80 text-xs mb-3">
                {partidosNoProgramados.length} partido{partidosNoProgramados.length > 1 ? 's' : ''} no pudo{partidosNoProgramados.length > 1 ? 'ieron' : ''} programarse porque las parejas no tienen horarios compatibles.
              </p>
              <div className="space-y-2">
                {partidosNoProgramados.map((partido: any, idx: number) => (
                  <div key={idx} className="p-3 bg-background/50 rounded border border-yellow-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-yellow-500">{partido.zona_nombre}</span>
                        {partido.categoria_nombre && (
                          <span className="text-[10px] px-2 py-0.5 bg-yellow-500/20 text-yellow-500 rounded-full font-bold">
                            {partido.categoria_nombre}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-yellow-500/60">{partido.motivo}</span>
                    </div>
                    <div className="space-y-1 text-xs text-textSecondary">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-textPrimary min-w-0 flex-1">{partido.pareja1_nombre}</span>
                        </div>
                        <div className="text-[10px] text-yellow-500/80 ml-2">
                          📅 {partido.disponibilidad_pareja1 && typeof partido.disponibilidad_pareja1 === 'string' 
                            ? partido.disponibilidad_pareja1
                            : 'Sin restricciones horarias'}
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-textPrimary min-w-0 flex-1">{partido.pareja2_nombre}</span>
                        </div>
                        <div className="text-[10px] text-yellow-500/80 ml-2">
                          📅 {partido.disponibilidad_pareja2 && typeof partido.disponibilidad_pareja2 === 'string'
                            ? partido.disponibilidad_pareja2
                            : 'Sin restricciones horarias'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-yellow-500/70 text-[10px] mt-3">
                💡 Sugerencia: Contacta a las parejas para ajustar su disponibilidad horaria o considera generar las zonas con el sistema inteligente que agrupa parejas con horarios compatibles.
              </p>
            </div>
            <button
              onClick={() => setPartidosNoProgramados([])}
              className="text-yellow-500/70 hover:text-yellow-500 transition-colors"
            >
              <X size={18} />
            </button>
          </div>
        </motion.div>
      )}

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
                onClick={() => {
                  setCategoriaFiltro(cat.id);
                  setFiltroZona(null);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${colorClasses}`}
              >
                <span>{icon}</span>
                {cat.nombre}
              </button>
            );
          })}
        </div>
      )}

      {/* BOTONES DE GENERAR Y ELIMINAR FIXTURE */}
      {esOrganizador && (
        <Card>
          <div className="p-4 space-y-3">
            {/* Botones de generar */}
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => generarFixture()}
                disabled={generando}
                variant="accent"
                size="sm"
                className="flex-1 min-w-[180px]"
              >
                {generando ? 'Generando...' : 'Regenerar Fixture Completo'}
              </Button>
            </div>
            
            {/* Botones por categoría */}
            {categorias.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm text-textSecondary font-medium">Generar/Regenerar por categoría:</p>
                <div className="flex flex-wrap gap-2">
                  {categorias.map(cat => {
                    const esF = cat.genero === 'femenino';
                    const esMixto = cat.genero === 'mixto';
                    const icon = esMixto ? '⚥' : esF ? '♀' : '♂';
                    const colorClass = esMixto 
                      ? 'from-purple-500 to-purple-600' 
                      : esF 
                        ? 'from-pink-500 to-pink-600' 
                        : 'from-blue-500 to-blue-600';
                    
                    return (
                      <Button
                        key={cat.id}
                        onClick={() => generarFixture(cat.id)}
                        disabled={generando}
                        variant="secondary"
                        size="sm"
                        className={`flex items-center gap-2 bg-gradient-to-r ${colorClass} text-white hover:opacity-90`}
                      >
                        <span>{icon}</span>
                        <span>{cat.nombre}</span>
                      </Button>
                    );
                  })}
                </div>
              </div>
            )}
            
            {/* Botones de eliminar */}
            <div className="flex flex-wrap gap-2 pt-2 border-t border-cardBorder/50">
              <Button
                onClick={() => eliminarFixture()}
                disabled={generando}
                variant="danger"
                size="sm"
                className="flex-1 min-w-[180px]"
              >
                {generando ? 'Eliminando...' : 'Eliminar Todo el Fixture'}
              </Button>
              
              {categoriaFiltro && (
                <Button
                  onClick={() => eliminarFixture(categoriaFiltro)}
                  disabled={generando}
                  variant="danger"
                  size="sm"
                  className="flex-1 min-w-[180px]"
                >
                  {generando ? 'Eliminando...' : `Eliminar ${categorias.find(c => c.id === categoriaFiltro)?.nombre || 'Categoría'}`}
                </Button>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Header con filtros de zona y botón de captura */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 overflow-x-auto">
          {/* Filtros por zona (de la categoría seleccionada) */}
          {zonasFiltradasPorCategoria.length > 1 && (
            <div className="flex gap-2 pb-2 sm:pb-0">
              {zonasFiltradasPorCategoria.map(zona => (
                <Button
                  key={zona.id}
                  variant={filtroZona === zona.id.toString() ? 'primary' : 'ghost'}
                  onClick={() => setFiltroZona(zona.id.toString())}
                  size="sm"
                  className="whitespace-nowrap text-xs"
                >
                  {zona.nombre}
                </Button>
              ))}
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2 self-end sm:self-auto">
          {/* Botón capturar para Instagram */}
          <Button
            variant="ghost"
            size="sm"
            onClick={capturarFixture}
            disabled={capturando}
            className="flex items-center gap-2 text-xs"
          >
            <Camera size={14} />
            {capturando ? 'Capturando...' : 'Capturar'}
          </Button>
        </div>
      </div>

      {/* Partidos por zona */}
      <div ref={fixtureRef} className="space-y-6">
      {zonasConPartidos
        .filter(zona => !filtroZona || filtroZona === zona.id)
        .map((zona, index) => (
          <motion.div
            key={zona.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card>
              <div className="p-4 md:p-6">
                <h3 className="text-lg md:text-xl font-bold text-textPrimary mb-3 md:mb-4 flex items-center gap-2">
                  <Trophy size={18} className="text-primary md:w-5 md:h-5" />
                  {zona.nombre}
                </h3>

                <div className="space-y-2 md:space-y-3">
                  {zona.partidos.map((partido: any, idx: number) => {
                    const setsEquipoA = partido.resultado_padel?.sets.filter((s: any) => s.ganador === 'equipoA').length || 0;
                    const setsEquipoB = partido.resultado_padel?.sets.filter((s: any) => s.ganador === 'equipoB').length || 0;
                    const ganadorA = setsEquipoA > setsEquipoB;
                    const ganadorB = setsEquipoB > setsEquipoA;
                    
                    return (
                      <motion.div
                        key={partido.id_partido}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        className="p-3 md:p-4 bg-background rounded-lg border border-cardBorder hover:border-primary/50 transition-all hover:shadow-md"
                      >
                        {/* Header del partido con fecha, hora y cancha */}
                        <div className="flex flex-wrap items-center justify-between gap-2 mb-3 md:mb-4">
                          <div className="flex flex-wrap items-center gap-2 md:gap-3 text-xs md:text-sm text-textSecondary">
                            {/* Fecha y hora */}
                            <div className="flex items-center gap-1.5">
                              <div className="bg-primary/10 p-1 md:p-1.5 rounded">
                                <Calendar size={12} className="text-primary md:w-[14px] md:h-[14px]" />
                              </div>
                              <span className="font-medium">
                                {partido.fecha_hora ? parseFechaLocal(partido.fecha_hora).toLocaleDateString('es-ES', {
                                  weekday: 'short',
                                  day: 'numeric',
                                  month: 'short'
                                }).toUpperCase() : 'Sin fecha'}
                              </span>
                            </div>
                            {/* Hora */}
                            {partido.fecha_hora && (
                              <div className="flex items-center gap-1.5">
                                <Clock size={12} className="text-accent md:w-[14px] md:h-[14px]" />
                                <span className="font-bold text-accent">
                                  {parseFechaLocal(partido.fecha_hora).toLocaleTimeString('es-ES', {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                                {/* Botón cambiar horario (solo organizadores) */}
                                {esOrganizador && partido.estado === 'pendiente' && (
                                  <button
                                    onClick={() => {
                                      setPartidoEditando(partido);
                                      setModalCambiarHorarioOpen(true);
                                    }}
                                    className="p-1 hover:bg-accent/10 rounded transition-colors text-accent/60 hover:text-accent"
                                    title="Cambiar horario"
                                  >
                                    <Clock size={12} className="md:w-3 md:h-3" />
                                  </button>
                                )}
                              </div>
                            )}
                            {/* Cancha */}
                            {partido.cancha_id && (
                              <div className="flex items-center gap-1 bg-accent/10 px-2 py-0.5 rounded">
                                <MapPin size={12} className="text-accent md:w-[14px] md:h-[14px]" />
                                <span className="font-bold text-accent text-[10px] md:text-xs">
                                  {getNombreCancha(partido.cancha_id)}
                                </span>
                              </div>
                            )}
                          </div>
                          <div
                            className={`px-2 md:px-3 py-0.5 md:py-1 rounded-full text-[10px] md:text-xs font-bold flex items-center gap-1 md:gap-1.5 ${
                              partido.estado === 'confirmado'
                                ? 'bg-green-500/10 text-green-500'
                                : partido.estado === 'reportado'
                                ? 'bg-yellow-500/10 text-yellow-500'
                                : 'bg-gray-500/10 text-gray-500'
                            }`}
                          >
                            <span className={`w-1 h-1 md:w-1.5 md:h-1.5 rounded-full ${
                              partido.estado === 'confirmado' ? 'bg-green-500' :
                              partido.estado === 'reportado' ? 'bg-yellow-500' : 'bg-gray-500'
                            }`} />
                            {partido.estado === 'confirmado' && 'Finalizado'}
                            {partido.estado === 'reportado' && 'Reportado'}
                            {partido.estado === 'pendiente' && 'Pendiente'}
                          </div>
                        </div>

                        {/* Parejas con resultado */}
                        <div className="space-y-2 md:space-y-3 mb-2 md:mb-3">
                          {/* Pareja 1 */}
                          <div className={`flex items-center justify-between p-2 md:p-3 rounded-lg transition-colors ${
                            ganadorA ? 'bg-green-500/10 border border-green-500/20' : 'bg-card'
                          }`}>
                            <div className="flex items-center gap-1.5 md:gap-2 flex-1 min-w-0">
                              {ganadorA && <Trophy size={12} className="text-green-500 flex-shrink-0 md:w-4 md:h-4" />}
                              <span className={`font-bold text-xs md:text-base truncate ${ganadorA ? 'text-green-500' : 'text-textPrimary'}`}>
                                {partido.pareja1_nombre || `Pareja ${partido.pareja1_id}`}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              {partido.resultado_padel && (
                                <span className={`text-xl md:text-2xl font-bold ${ganadorA ? 'text-green-500' : 'text-textSecondary'}`}>
                                  {setsEquipoA}
                                </span>
                              )}
                              <button
                                onClick={() => verHorariosPareja(partido, 'pareja1')}
                                className="p-1 hover:bg-primary/10 rounded transition-colors text-primary hover:text-accent flex-shrink-0"
                                title="Ver horarios disponibles"
                              >
                                <Clock size={14} className="md:w-4 md:h-4" />
                              </button>
                            </div>
                          </div>

                          {/* Pareja 2 */}
                          <div className={`flex items-center justify-between p-2 md:p-3 rounded-lg transition-colors ${
                            ganadorB ? 'bg-green-500/10 border border-green-500/20' : 'bg-card'
                          }`}>
                            <div className="flex items-center gap-1.5 md:gap-2 flex-1 min-w-0">
                              {ganadorB && <Trophy size={12} className="text-green-500 flex-shrink-0 md:w-4 md:h-4" />}
                              <span className={`font-bold text-xs md:text-base truncate ${ganadorB ? 'text-green-500' : 'text-textPrimary'}`}>
                                {partido.pareja2_nombre || `Pareja ${partido.pareja2_id}`}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              {partido.resultado_padel && (
                                <span className={`text-xl md:text-2xl font-bold ${ganadorB ? 'text-green-500' : 'text-textSecondary'}`}>
                                  {setsEquipoB}
                                </span>
                              )}
                              <button
                                onClick={() => verHorariosPareja(partido, 'pareja2')}
                                className="p-1 hover:bg-primary/10 rounded transition-colors text-primary hover:text-accent flex-shrink-0"
                                title="Ver horarios disponibles"
                              >
                                <Clock size={14} className="md:w-4 md:h-4" />
                              </button>
                            </div>
                          </div>
                        </div>

                        {/* Detalle de sets */}
                        {partido.resultado_padel && (
                          <div className="flex gap-1.5 md:gap-2 mb-2 md:mb-3 justify-center">
                            {partido.resultado_padel.sets.map((set: any, idx: number) => (
                              <div
                                key={idx}
                                className="px-2 md:px-3 py-1 md:py-2 bg-card rounded-lg border border-cardBorder"
                              >
                                <span className="text-xs md:text-sm font-bold text-textPrimary">
                                  {set.gamesEquipoA}
                                </span>
                                <span className="text-[10px] md:text-xs text-textSecondary mx-0.5 md:mx-1">-</span>
                                <span className="text-xs md:text-sm font-bold text-textPrimary">
                                  {set.gamesEquipoB}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Acciones */}
                        {esOrganizador && partido.estado === 'pendiente' && (
                          <Button
                            variant="accent"
                            size="sm"
                            onClick={() => abrirModalResultado(partido)}
                            className="w-full text-xs md:text-sm py-2"
                          >
                            Cargar Resultado
                          </Button>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Modal Cargar Resultado */}
      {partidoSeleccionado && (
        <ModalCargarResultado
          isOpen={modalResultadoOpen}
          onClose={() => {
            setModalResultadoOpen(false);
            setPartidoSeleccionado(null);
          }}
          partido={partidoSeleccionado}
          torneoId={torneoId}
          onResultadoCargado={handleResultadoCargado}
        />
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

      {/* Modal Cambiar Horario */}
      {partidoEditando && (
        <ModalCambiarHorario
          isOpen={modalCambiarHorarioOpen}
          onClose={() => {
            setModalCambiarHorarioOpen(false);
            setPartidoEditando(null);
          }}
          torneoId={torneoId}
          partidoId={partidoEditando.id_partido}
          partidoActual={partidoEditando}
          onSuccess={() => {
            cargarDatos();
            setModalCambiarHorarioOpen(false);
            setPartidoEditando(null);
          }}
        />
      )}
    </div>
  );
}
