import { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import { Trophy, Edit3, Crown, Star, Sparkles, FastForward, ArrowRightLeft, X } from 'lucide-react';
import ModalCargarResultado from './ModalCargarResultado';
import torneoService from '../services/torneo.service';

interface Partido {
  id: number;
  id_partido?: number;
  pareja1_id?: number;
  pareja2_id?: number;
  pareja1_nombre?: string;
  pareja2_nombre?: string;
  ganador_id?: number;
  resultado?: any;
  fase: string;
  estado: string;
  numero_partido?: number;
}

interface TorneoBracketProps {
  partidos: Partido[];
  torneoId: number;
  esOrganizador: boolean;
  onResultadoCargado?: () => void;
}

/** Id numérico del partido (la API a veces devuelve id como string) */
function partidoIdNum(partido: Partido): number {
  const n = Number(partido?.id ?? partido?.id_partido);
  return Number.isFinite(n) ? n : 0;
}

export default function TorneoBracket({ partidos, torneoId, esOrganizador, onResultadoCargado }: TorneoBracketProps) {
  const [partidoSeleccionado, setPartidoSeleccionado] = useState<Partido | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modoIntercambiarActivo, setModoIntercambiarActivo] = useState(false);
  const [primeraSeleccion, setPrimeraSeleccion] = useState<{ partidoId: number; slot: 1 | 2 } | null>(null);
  const [intercambiando, setIntercambiando] = useState(false);
  const [svgSize, setSvgSize] = useState({ width: 0, height: 0 });
  const [lines, setLines] = useState<JSX.Element[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const matchRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Agrupar partidos por fase
  const agruparPorFase = useCallback(() => {
    const fases: Record<string, Partido[]> = {
      '16avos': [],
      '8vos': [],
      '4tos': [],
      semis: [],
      final: [],
    };

    partidos.forEach((p) => {
      let fase = p.fase;
      if (fase === 'cuartos') fase = '4tos';
      if (fase === 'semifinal') fase = 'semis';
      if (fases[fase]) {
        fases[fase].push(p);
      }
    });

    Object.keys(fases).forEach((fase) => {
      fases[fase].sort((a, b) => (a.numero_partido || 0) - (b.numero_partido || 0));
    });

    return fases;
  }, [partidos]);

  const fases = agruparPorFase();
  const fasesActivas = Object.entries(fases).filter(([, p]) => p.length > 0);
  const fasesOrden = fasesActivas.map(([nombre]) => nombre);

  const partidoFinal = fases.final[0];
  const hayCampeon = partidoFinal?.ganador_id && partidoFinal?.estado === 'confirmado';
  const nombreCampeon = hayCampeon
    ? partidoFinal.ganador_id === partidoFinal.pareja1_id
      ? partidoFinal.pareja1_nombre
      : partidoFinal.pareja2_nombre
    : null;

  // Calcular líneas SVG - solo horizontales y verticales
  const calcularLineas = useCallback(() => {
    if (!containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    setSvgSize({ width: containerRect.width, height: containerRect.height });

    const newLines: JSX.Element[] = [];
    const lineColor = 'rgba(99, 102, 241, 0.5)';
    const lineWidth = 2;

    for (let faseIdx = 0; faseIdx < fasesOrden.length - 1; faseIdx++) {
      const faseActual = fasesOrden[faseIdx];
      const faseSiguiente = fasesOrden[faseIdx + 1];
      const partidosFaseActual = fases[faseActual];

      for (let i = 0; i < partidosFaseActual.length; i += 2) {
        const match1Ref = matchRefs.current.get(`${faseActual}-${i}`);
        const match2Ref = matchRefs.current.get(`${faseActual}-${i + 1}`);
        const nextMatchRef = matchRefs.current.get(`${faseSiguiente}-${Math.floor(i / 2)}`);

        if (!match1Ref || !nextMatchRef) continue;

        const rect1 = match1Ref.getBoundingClientRect();
        const rect2 = match2Ref?.getBoundingClientRect();
        const rectNext = nextMatchRef.getBoundingClientRect();

        // Posiciones relativas al container (x2 para que la línea salga del segundo partido/bye)
        const x1 = rect1.right - containerRect.left;
        const x2 = rect2 ? rect2.right - containerRect.left : x1;
        const y1 = rect1.top + rect1.height / 2 - containerRect.top;
        const y2 = rect2 ? rect2.top + rect2.height / 2 - containerRect.top : y1;
        const x3 = rectNext.left - containerRect.left;
        const y3 = rectNext.top + rectNext.height / 2 - containerRect.top;

        // Punto medio horizontal entre las fases
        const xMid = x1 + (x3 - x1) / 2;
        // Punto medio vertical entre los dos partidos
        const yMid = (y1 + y2) / 2;

        // Línea 1: horizontal desde match1 hacia xMid
        newLines.push(
          <path
            key={`l1-${faseActual}-${i}`}
            d={`M ${x1} ${y1} H ${xMid}`}
            stroke={lineColor}
            strokeWidth={lineWidth}
            fill="none"
          />
        );

        // Si hay match2 (o BYE): línea desde el borde derecho del segundo recuadro
        if (rect2) {
          newLines.push(
            <path
              key={`l2-${faseActual}-${i}`}
              d={`M ${x2} ${y2} H ${xMid}`}
              stroke={lineColor}
              strokeWidth={lineWidth}
              fill="none"
            />
          );

          // Línea 3: vertical conectando y1 con y2 en xMid
          newLines.push(
            <path
              key={`l3-${faseActual}-${i}`}
              d={`M ${xMid} ${y1} V ${y2}`}
              stroke={lineColor}
              strokeWidth={lineWidth}
              fill="none"
            />
          );
        }

        // Línea 4: horizontal desde xMid,yMid hacia el siguiente partido
        newLines.push(
          <path
            key={`l4-${faseActual}-${i}`}
            d={`M ${xMid} ${yMid} H ${x3}`}
            stroke={lineColor}
            strokeWidth={lineWidth}
            fill="none"
          />
        );

        // Si el siguiente partido no está centrado, agregar línea vertical
        if (Math.abs(yMid - y3) > 2) {
          newLines.push(
            <path
              key={`l5-${faseActual}-${i}`}
              d={`M ${x3} ${yMid} V ${y3}`}
              stroke={lineColor}
              strokeWidth={lineWidth}
              fill="none"
            />
          );
        }
      }
    }

    setLines(newLines);
  }, [fases, fasesOrden]);

  useEffect(() => {
    const timer = setTimeout(calcularLineas, 150);
    window.addEventListener('resize', calcularLineas);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', calcularLineas);
    };
  }, [calcularLineas]);

  const setMatchRef = (fase: string, index: number) => (el: HTMLDivElement | null) => {
    if (el) {
      matchRefs.current.set(`${fase}-${index}`, el);
    }
  };

  const abrirModalResultado = (partido: Partido) => {
    setPartidoSeleccionado(partido);
    setModalOpen(true);
  };

  const handleResultadoCargado = () => {
    setModalOpen(false);
    setPartidoSeleccionado(null);
    onResultadoCargado?.();
  };

  const handleSeleccionPareja = async (partidoId: number, slot: 1 | 2) => {
    if (!primeraSeleccion) {
      // Primera selección
      setPrimeraSeleccion({ partidoId, slot });
    } else {
      // Segunda selección - ejecutar intercambio
      if (primeraSeleccion.partidoId === partidoId && primeraSeleccion.slot === slot) {
        // Deseleccionar si es la misma
        setPrimeraSeleccion(null);
        return;
      }
      
      setIntercambiando(true);
      try {
        await torneoService.intercambiarParejasPlayoff(torneoId, {
          partido_id_a: primeraSeleccion.partidoId,
          partido_id_b: partidoId,
          slot_a: primeraSeleccion.slot,
          slot_b: slot,
        });
        setPrimeraSeleccion(null);
        setModoIntercambiarActivo(false);
        onResultadoCargado?.();
      } catch (error) {
        console.error('Error al intercambiar:', error);
      } finally {
        setIntercambiando(false);
      }
    }
  };

  const cancelarIntercambio = () => {
    setPrimeraSeleccion(null);
    setModoIntercambiarActivo(false);
  };

  // PartidoBox component
  const PartidoBox = ({ partido, esFinal = false }: { partido: Partido; esFinal?: boolean }) => {
    const esBye = partido.estado === 'bye';
    const ganadorA = partido.ganador_id === partido.pareja1_id && partido.pareja1_id;
    const ganadorB = partido.ganador_id === partido.pareja2_id && partido.pareja2_id;
    const tieneAmbosEquipos = partido.pareja1_id && partido.pareja2_id;
    const puedeCargarResultado =
      esOrganizador && partido.estado === 'pendiente' && partido.id > 0 && tieneAmbosEquipos;
    const partidoFinalizado = partido.estado === 'confirmado';
    const idP = partidoIdNum(partido);
    
    const esSeleccionado = primeraSeleccion != null && idP === primeraSeleccion.partidoId;
    const puedeIntercambiar = modoIntercambiarActivo && partido.estado === 'pendiente' && idP > 0 && (partido.pareja1_id || partido.pareja2_id);

    if (esBye) {
      const nombreGanador = partido.pareja1_nombre || partido.pareja2_nombre || 'TBD';
      return (
        <div className="bg-card border-2 border-green-500/30 rounded-lg overflow-hidden w-[200px]">
          <div className="flex items-center gap-2 px-3 py-2.5 border-b border-cardBorder bg-green-500/10">
            <FastForward size={12} className="text-green-500 flex-shrink-0" />
            <span className="text-xs font-bold text-green-500 truncate">{nombreGanador}</span>
          </div>
          <div className="px-3 py-2.5">
            <span className="text-xs text-textSecondary italic">BYE</span>
          </div>
          <div className="py-1.5 bg-green-500/10 flex items-center justify-center gap-1 border-t border-green-500/20">
            <FastForward size={10} className="text-green-500" />
            <span className="text-[10px] font-bold text-green-500">Pasa directo</span>
          </div>
        </div>
      );
    }

    return (
      <div
        className={`bg-card border-2 rounded-lg overflow-hidden w-[200px] md:w-[220px] transition-all ${
          esSeleccionado
            ? 'border-primary ring-4 ring-primary/50 shadow-lg scale-105'
            : esFinal
              ? 'border-accent shadow-lg shadow-accent/20'
              : partidoFinalizado
                ? 'border-green-500/50'
                : puedeCargarResultado
                  ? 'border-yellow-500/50'
                  : 'border-primary/30'
        }`}
      >
        {/* Fila pareja 1 */}
        <div
          className={`flex items-center gap-1 px-3 py-2.5 border-b border-cardBorder ${ganadorA ? 'bg-green-500/20' : 'bg-card'}`}
        >
          {ganadorA && <Trophy size={12} className="text-green-500 flex-shrink-0" />}
          <span
            className={`flex-1 text-xs font-bold truncate ${ganadorA ? 'text-green-500' : partido.pareja1_nombre ? 'text-textPrimary' : 'text-textSecondary'}`}
          >
            {partido.pareja1_nombre || 'TBD'}
          </span>
          {puedeIntercambiar && partido.pareja1_id && (
            <button
              type="button"
              onClick={() => handleSeleccionPareja(idP, 1)}
              disabled={intercambiando}
              className={`p-2 md:p-1 rounded transition-all disabled:opacity-50 min-h-[44px] md:min-h-0 min-w-[44px] md:min-w-0 flex items-center justify-center ${
                esSeleccionado && primeraSeleccion?.slot === 1
                  ? 'bg-primary text-white ring-2 ring-primary/50'
                  : 'bg-primary/20 hover:bg-primary/40 active:bg-primary/50 text-primary'
              }`}
              title={esSeleccionado && primeraSeleccion?.slot === 1 ? 'Seleccionada' : 'Seleccionar para intercambiar'}
            >
              <ArrowRightLeft size={14} className="md:w-3 md:h-3" />
            </button>
          )}
        </div>
        {/* Fila pareja 2 */}
        <div className={`flex items-center gap-1 px-3 py-2.5 ${ganadorB ? 'bg-green-500/20' : 'bg-card'}`}>
          {ganadorB && <Trophy size={12} className="text-green-500 flex-shrink-0" />}
          <span
            className={`flex-1 text-xs font-bold truncate ${ganadorB ? 'text-green-500' : partido.pareja2_nombre ? 'text-textPrimary' : 'text-textSecondary'}`}
          >
            {partido.pareja2_nombre || 'TBD'}
          </span>
          {puedeIntercambiar && partido.pareja2_id && (
            <button
              type="button"
              onClick={() => handleSeleccionPareja(idP, 2)}
              disabled={intercambiando}
              className={`p-2 md:p-1 rounded transition-all disabled:opacity-50 min-h-[44px] md:min-h-0 min-w-[44px] md:min-w-0 flex items-center justify-center ${
                esSeleccionado && primeraSeleccion?.slot === 2
                  ? 'bg-primary text-white ring-2 ring-primary/50'
                  : 'bg-primary/20 hover:bg-primary/40 active:bg-primary/50 text-primary'
              }`}
              title={esSeleccionado && primeraSeleccion?.slot === 2 ? 'Seleccionada' : 'Seleccionar para intercambiar'}
            >
              <ArrowRightLeft size={14} className="md:w-3 md:h-3" />
            </button>
          )}
        </div>
        
        {puedeCargarResultado && !modoIntercambiarActivo ? (
          <button
            onClick={() => abrirModalResultado(partido)}
            className="w-full py-2 md:py-1.5 bg-gradient-to-r from-accent/30 to-yellow-500/30 hover:from-accent/50 hover:to-yellow-500/50 active:from-accent/60 active:to-yellow-500/60 transition-all flex items-center justify-center gap-1 border-t border-accent/20 min-h-[44px] md:min-h-0"
          >
            <Edit3 size={12} className="text-accent" />
            <span className="text-xs md:text-[10px] font-bold text-accent">Cargar Resultado</span>
          </button>
        ) : partidoFinalizado ? (
          <div className="py-2 md:py-1.5 bg-green-500/10 flex items-center justify-center gap-1 border-t border-green-500/20">
            <Trophy size={10} className="text-green-500" />
            <span className="text-[10px] font-bold text-green-500">Finalizado</span>
          </div>
        ) : !tieneAmbosEquipos && partido.id > 0 ? (
          <div className="py-2 md:py-1.5 bg-gray-500/10 flex items-center justify-center border-t border-gray-500/20">
            <span className="text-[10px] text-textSecondary">Esperando clasificados</span>
          </div>
        ) : null}
      </div>
    );
  };

  if (fasesActivas.length === 0) {
    return (
      <div className="text-center py-8">
        <Trophy size={48} className="mx-auto text-textSecondary mb-4" />
        <p className="text-textSecondary">No hay partidos de playoffs</p>
      </div>
    );
  }


  // Calcular posición vertical para centrar cada fase
  const calcularPaddingTop = (faseIdx: number, _numPartidos: number) => {
    if (faseIdx === 0) return 0;
    // Cada ronda siguiente debe estar centrada entre los partidos de la anterior
    // El primer partido de la ronda N debe estar centrado entre partidos 0 y 1 de ronda N-1
    const alturaPartido = 95; // altura aproximada de cada partido
    const gapBase = 16;
    const multiplicadorAnterior = Math.pow(2, faseIdx - 1);
    const espacioAnterior = (alturaPartido + gapBase) * multiplicadorAnterior;
    // Centrar: mitad del espacio entre dos partidos de la ronda anterior
    return espacioAnterior / 2;
  };

  return (
    <div className="w-full">
      {/* Campeón */}
      {hayCampeon && nombreCampeon && (
        <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="mb-6">
          <div className="relative bg-gradient-to-br from-yellow-500/20 via-accent/20 to-yellow-500/20 rounded-xl p-5 border-2 border-yellow-500/50 shadow-lg overflow-hidden">
            <div className="absolute inset-0 opacity-10">
              <Star size={32} className="absolute top-3 left-3 text-yellow-500" fill="currentColor" />
              <Star size={32} className="absolute top-3 right-3 text-yellow-500" fill="currentColor" />
            </div>
            <div className="relative text-center">
              <div className="flex justify-center mb-3">
                <div className="relative">
                  <div className="absolute -inset-3 bg-yellow-500/30 rounded-full blur-lg" />
                  <div className="relative bg-gradient-to-br from-yellow-400 to-yellow-600 p-3 rounded-full">
                    <Trophy size={32} className="text-white" />
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-center gap-2 mb-2">
                <Crown size={18} className="text-yellow-500" />
                <h2 className="text-xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-yellow-600">
                  ¡CAMPEONES!
                </h2>
                <Crown size={18} className="text-yellow-500" />
              </div>
              <div className="bg-yellow-500/10 rounded-lg p-3 border border-yellow-500/30 inline-block">
                <div className="flex items-center gap-2">
                  <Sparkles size={16} className="text-yellow-500" />
                  <span className="text-base font-bold text-yellow-500">{nombreCampeon}</span>
                  <Sparkles size={16} className="text-yellow-500" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-6">
        <div className="text-center flex-1">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-accent/10 to-primary/10 px-4 md:px-5 py-2 rounded-full">
            <Trophy className="text-accent" size={18} />
            <h2 className="text-base md:text-lg font-bold text-textPrimary">{hayCampeon ? 'Resultados' : 'Fase de Playoffs'}</h2>
            <Trophy className="text-primary" size={18} />
          </div>
          <p className="text-textSecondary mt-1 text-xs md:text-sm">Eliminación directa</p>
        </div>
        
        {/* Botón Intercambiar Parejas */}
        {esOrganizador && !hayCampeon && (
          <div className="flex flex-col md:flex-row items-center gap-2 w-full md:w-auto">
            {modoIntercambiarActivo && primeraSeleccion && (
              <div className="text-xs text-textSecondary bg-primary/10 px-3 py-1.5 rounded-lg text-center">
                Seleccioná la segunda pareja
              </div>
            )}
            <button
              onClick={() => {
                if (modoIntercambiarActivo) {
                  cancelarIntercambio();
                } else {
                  setModoIntercambiarActivo(true);
                }
              }}
              disabled={intercambiando}
              className={`flex items-center justify-center gap-2 px-4 py-2.5 md:py-2 rounded-lg font-bold text-sm transition-all disabled:opacity-50 w-full md:w-auto min-h-[44px] md:min-h-0 ${
                modoIntercambiarActivo
                  ? 'bg-red-500/20 text-red-500 hover:bg-red-500/30 active:bg-red-500/40'
                  : 'bg-primary/20 text-primary hover:bg-primary/30 active:bg-primary/40'
              }`}
            >
              {modoIntercambiarActivo ? (
                <>
                  <X size={18} />
                  Cancelar
                </>
              ) : (
                <>
                  <ArrowRightLeft size={18} />
                  Intercambiar Parejas
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Bracket */}
      <div className="overflow-x-auto pb-4">
        <div ref={containerRef} className="relative min-w-max px-4 py-2 mx-auto w-fit">
          {/* SVG para líneas */}
          <svg
            className="absolute inset-0 pointer-events-none"
            width={svgSize.width || '100%'}
            height={svgSize.height || '100%'}
            style={{ zIndex: 0 }}
          >
            {lines}
          </svg>

          {/* Fases */}
          <div className="relative flex items-start gap-16" style={{ zIndex: 1 }}>
            {fasesActivas.map(([nombre, partidosFase], faseIdx) => {
              const esFinal = nombre === 'final';
              const multiplicador = Math.pow(2, faseIdx);
              const gap = 16 * multiplicador;
              const paddingTop = calcularPaddingTop(faseIdx, partidosFase.length);

              return (
                <div key={nombre} className="flex flex-col items-center">
                  {/* Título */}
                  <div
                    className={`mb-4 px-4 py-1.5 rounded-lg ${esFinal ? 'bg-gradient-to-r from-accent to-primary' : 'bg-primary/10'}`}
                  >
                    <span className={`text-xs font-bold uppercase ${esFinal ? 'text-white' : 'text-primary'}`}>
                      {nombre === 'semis'
                        ? 'Semifinales'
                        : nombre === '4tos'
                          ? 'Cuartos'
                          : nombre === '8vos'
                            ? 'Octavos'
                            : nombre === '16avos'
                              ? '16avos'
                              : 'Final'}
                    </span>
                  </div>

                  {/* Partidos con padding para centrar */}
                  <div className="flex flex-col" style={{ gap: `${gap}px`, paddingTop: `${paddingTop}px` }}>
                    {partidosFase.map((partido, idx) => (
                      <motion.div
                        key={partido.id || `${nombre}-${idx}`}
                        ref={setMatchRef(nombre, idx)}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: faseIdx * 0.08 + idx * 0.03 }}
                      >
                        <PartidoBox partido={partido} esFinal={esFinal} />
                      </motion.div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Leyenda */}
      <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-textSecondary">Ganador</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-yellow-500" />
          <span className="text-textSecondary">Pendiente</span>
        </div>
        <div className="flex items-center gap-1.5">
          <FastForward size={12} className="text-green-500" />
          <span className="text-textSecondary">BYE</span>
        </div>
      </div>

      {/* Modal resultado */}
      {partidoSeleccionado &&
        createPortal(
          <ModalCargarResultado
            isOpen={modalOpen}
            onClose={() => {
              setModalOpen(false);
              setPartidoSeleccionado(null);
            }}
            partido={{ ...partidoSeleccionado, id_partido: partidoSeleccionado.id_partido || partidoSeleccionado.id }}
            torneoId={torneoId}
            onResultadoCargado={handleResultadoCargado}
          />,
          document.body
        )}

      </div>
  );
}
