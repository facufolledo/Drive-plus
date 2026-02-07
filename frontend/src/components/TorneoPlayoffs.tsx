import { useEffect, useState, useCallback } from 'react';
import { Trophy, Zap, Users, Info, RefreshCw, Filter } from 'lucide-react';
import Card from './Card';
import Button from './Button';
import SkeletonLoader from './SkeletonLoader';
import TorneoBracket from './TorneoBracket';
import torneoService, { Categoria } from '../services/torneo.service';
import { useTorneos } from '../context/TorneosContext';

interface TorneoPlayoffsProps {
  torneoId: number;
  esOrganizador: boolean;
}

interface Partido {
  id: number;
  pareja1_id?: number;
  pareja2_id?: number;
  pareja1_nombre?: string;
  pareja2_nombre?: string;
  ganador_id?: number;
  resultado?: any;
  fase: string;
  estado: string;
}

// Cache de playoffs
const playoffsCache: Record<number, { partidos: Partido[]; timestamp: number }> = {};
const CACHE_TTL = 30000; // 30 segundos - más corto para ver cambios en tiempo real

export default function TorneoPlayoffs({ torneoId, esOrganizador }: TorneoPlayoffsProps) {
  const [partidos, setPartidos] = useState<Partido[]>([]);
  const [loading, setLoading] = useState(true);
  const [generando, setGenerando] = useState(false);
  const [playoffsGenerados, setPlayoffsGenerados] = useState(false);
  const [ultimaActualizacion, setUltimaActualizacion] = useState<Date | null>(null);
  const { parejas } = useTorneos();
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [categoriaFiltro, setCategoriaFiltro] = useState<number | null>(null);

  useEffect(() => {
    // Guard: Solo cargar si torneoId es válido
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      setLoading(false);
      return;
    }
    
    torneoService.listarCategorias(torneoId)
      .then(setCategorias)
      .catch(() => setCategorias([]));
  }, [torneoId]);

  const cargarPlayoffs = useCallback(async (forzar: boolean = false) => {
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) return;
    
    const cached = playoffsCache[torneoId];
    
    if (!forzar && cached && Date.now() - cached.timestamp < CACHE_TTL) {
      // Filtrar por categoría del cache
      const partidosFiltrados = categoriaFiltro 
        ? cached.partidos.filter((p: any) => p.categoria_id === categoriaFiltro)
        : cached.partidos;
      setPartidos(partidosFiltrados);
      setPlayoffsGenerados(partidosFiltrados.length > 0);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      // Lista plana con categoria_id (incluye partidos BYE y todas las fases)
      const res = await torneoService.listarPartidosPlayoffs(torneoId);
      const partidosData = (res?.partidos && Array.isArray(res.partidos)) ? res.partidos : [];
      
      // Guardar en cache
      playoffsCache[torneoId] = {
        partidos: partidosData,
        timestamp: Date.now()
      };
      
      // Filtrar por categoría; si "Todas", mostrar la primera categoría que tenga partidos
      let partidosFiltrados = partidosData;
      if (categoriaFiltro) {
        partidosFiltrados = partidosData.filter((p: any) => p.categoria_id === categoriaFiltro);
      } else if (partidosData.length > 0) {
        const primeraCategoriaId = partidosData[0].categoria_id;
        partidosFiltrados = partidosData.filter((p: any) => p.categoria_id === primeraCategoriaId);
      }
      
      setPartidos(partidosFiltrados);
      setPlayoffsGenerados(partidosFiltrados.length > 0);
      setUltimaActualizacion(new Date());
    } catch (error: any) {
      console.error('Error al cargar playoffs:', error);
      setPartidos([]);
      setPlayoffsGenerados(false);
    } finally {
      setLoading(false);
    }
  }, [torneoId, categoriaFiltro]);

  useEffect(() => {
    cargarPlayoffs();
  }, [cargarPlayoffs, categoriaFiltro]);

  // Auto-refresh cada 30 segundos para ver cambios en tiempo real
  useEffect(() => {
    const interval = setInterval(() => {
      cargarPlayoffs(true);
    }, 30000);
    
    return () => clearInterval(interval);
  }, [cargarPlayoffs]);

  // Función para refrescar manualmente
  const refrescarPlayoffs = () => {
    delete playoffsCache[torneoId];
    cargarPlayoffs(true);
  };

  const [error, setError] = useState<string | null>(null);

  const generarPlayoffs = async () => {
    try {
      setGenerando(true);
      setError(null);
      await torneoService.generarPlayoffs(torneoId);
      await cargarPlayoffs();
    } catch (error: any) {
      console.error('Error al generar playoffs:', error);
      setError(error.response?.data?.detail || 'Error al generar playoffs');
    } finally {
      setGenerando(false);
    }
  };

  const regenerarPlayoffs = async () => {
    if (!confirm('¿Estás seguro de regenerar los playoffs? Se perderán los resultados actuales.')) {
      return;
    }
    delete playoffsCache[torneoId];
    await generarPlayoffs();
  };

  // Invalidar cache cuando se carga un resultado
  const handleResultadoCargado = () => {
    delete playoffsCache[torneoId];
    cargarPlayoffs(true);
  };

  // Calcular información del bracket basado en parejas
  const parejasConfirmadas = parejas.filter(p => p.estado === 'confirmada').length;
  const parejasInscritas = parejas.filter(p => p.estado !== 'baja').length;
  const parejasActivas = parejasConfirmadas > 0 ? parejasConfirmadas : parejasInscritas;
  
  // Determinar tamaño del bracket necesario
  const calcularTamañoBracket = (numParejas: number) => {
    if (numParejas <= 2) return { rondas: 1, nombre: 'Final directa' };
    if (numParejas <= 4) return { rondas: 2, nombre: 'Semifinales + Final' };
    if (numParejas <= 8) return { rondas: 3, nombre: 'Cuartos + Semis + Final' };
    if (numParejas <= 16) return { rondas: 4, nombre: '8vos + Cuartos + Semis + Final' };
    return { rondas: 5, nombre: '16avos + 8vos + Cuartos + Semis + Final' };
  };

  const bracketInfo = calcularTamañoBracket(parejasActivas);

  if (loading) {
    return (
      <div className="space-y-4">
        <SkeletonLoader height="200px" />
      </div>
    );
  }

  // Estado vacío - No hay playoffs generados
  if (!playoffsGenerados || partidos.length === 0) {
    return (
      <Card>
        <div className="p-6 md:p-8 text-center">
          <div className="bg-gradient-to-br from-accent/20 to-primary/20 w-16 h-16 md:w-20 md:h-20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Trophy size={32} className="text-accent md:w-10 md:h-10" />
          </div>
          
          <h3 className="text-xl md:text-2xl font-bold text-textPrimary mb-2">
            Fase de Playoffs
          </h3>
          
          {parejasInscritas === 0 ? (
            <>
              <p className="text-textSecondary mb-4 text-sm md:text-base">
                Aún no hay parejas inscritas en el torneo.
              </p>
              <div className="bg-background rounded-lg p-4 max-w-md mx-auto">
                <div className="flex items-center gap-2 text-textSecondary text-sm">
                  <Info size={16} />
                  <span>Inscribí parejas primero para poder generar los playoffs.</span>
                </div>
              </div>
            </>
          ) : (
            <>
              <p className="text-textSecondary mb-4 text-sm md:text-base max-w-md mx-auto">
                Los playoffs se generan cuando finaliza la fase de grupos. 
                Los mejores de cada zona clasifican a la eliminación directa.
              </p>
              
              {/* Info del bracket estimado */}
              <div className="bg-background rounded-lg p-4 max-w-md mx-auto mb-6">
                <div className="flex items-center justify-center gap-2 mb-3">
                  <Users size={18} className="text-primary" />
                  <span className="font-bold text-textPrimary">
                    {parejasActivas} parejas
                  </span>
                  <span className="text-textSecondary text-sm">
                    (inscritas)
                  </span>
                </div>
                <p className="text-sm text-textSecondary">
                  Formato estimado: <span className="text-primary font-bold">{bracketInfo.nombre}</span>
                </p>
              </div>

              {/* Mensaje de error */}
              {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4 max-w-md mx-auto">
                  <p className="text-red-500 text-sm">{error}</p>
                </div>
              )}

              {esOrganizador && (
                <Button
                  onClick={generarPlayoffs}
                  disabled={generando || parejasActivas < 2}
                  variant="accent"
                  className="gap-2"
                >
                  <Zap size={18} />
                  {generando ? 'Generando...' : 'Generar Playoffs'}
                </Button>
              )}

              {parejasActivas < 2 && (
                <p className="text-xs text-textSecondary mt-4">
                  Se necesitan al menos 2 parejas para generar playoffs.
                </p>
              )}
            </>
          )}
        </div>
      </Card>
    );
  }

  // Mostrar bracket de playoffs usando el nuevo componente
  return (
    <Card>
      <div className="p-4 md:p-6">
        {/* Filtro por categoría */}
        {categorias.length > 0 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-3 mb-4 border-b border-cardBorder">
            <Filter size={14} className="text-textSecondary flex-shrink-0" />
            <button
              onClick={() => setCategoriaFiltro(null)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all ${
                categoriaFiltro === null
                  ? 'bg-accent text-white'
                  : 'bg-cardBorder text-textSecondary hover:bg-accent/20'
              }`}
            >
              Todas
            </button>
            {categorias.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategoriaFiltro(cat.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all ${
                  categoriaFiltro === cat.id
                    ? 'bg-accent text-white'
                    : 'bg-cardBorder text-textSecondary hover:bg-accent/20'
                }`}
              >
                {cat.nombre}
              </button>
            ))}
          </div>
        )}

        {/* Header con botones */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-xs text-textSecondary">
            {ultimaActualizacion && (
              <span>Actualizado: {ultimaActualizacion.toLocaleTimeString()}</span>
            )}
            <button
              onClick={refrescarPlayoffs}
              className="p-1 hover:bg-background rounded transition-colors"
              title="Refrescar"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
          {esOrganizador && (
            <Button
              onClick={regenerarPlayoffs}
              disabled={generando}
              variant="ghost"
              size="sm"
              className="text-xs"
            >
              <Zap size={14} className="mr-1" />
              {generando ? 'Regenerando...' : 'Regenerar Playoffs'}
            </Button>
          )}
        </div>
        
        {/* Mensaje de error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4">
            <p className="text-red-500 text-sm">{error}</p>
          </div>
        )}
        
        <TorneoBracket 
          partidos={partidos} 
          torneoId={torneoId}
          esOrganizador={esOrganizador}
          onResultadoCargado={handleResultadoCargado}
        />
      </div>
    </Card>
  );
}
