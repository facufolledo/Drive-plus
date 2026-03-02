import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import InvitacionesPendientes from '../components/InvitacionesPendientes';
import {
  Trophy,
  Crown,
  TrendingUp,
  TrendingDown,
  Minus,
  Swords,
  Target,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useSalas } from '../context/SalasContext';
import { apiService } from '../services/api';
import { perfilService } from '../services/perfil.service';
import type { PartidoHistorial } from '../services/perfil.service';

// --- Helpers de categoría y progreso (mismo criterio que MiPerfil) ---
const UMBRALES = [
  { min: 0, max: 500, nombre: 'Principiante' },
  { min: 500, max: 1000, nombre: '8va' },
  { min: 1000, max: 1200, nombre: '7ma' },
  { min: 1200, max: 1400, nombre: '6ta' },
  { min: 1400, max: 1600, nombre: '5ta' },
  { min: 1600, max: 1800, nombre: '4ta' },
  { min: 1800, max: 9999, nombre: '3ra' },
];

function getCategoriaDesdeRating(rating: number): { nombre: string; siguienteUmbral: number | null; ptsParaSubir: number; progresoPct: number } {
  const r = Math.max(0, rating);
  for (let i = 0; i < UMBRALES.length; i++) {
    if (r >= UMBRALES[i].min && r < UMBRALES[i].max) {
      const siguiente = i < UMBRALES.length - 1 ? UMBRALES[i + 1].min : null;
      const ptsParaSubir = siguiente != null ? Math.max(0, siguiente - r) : 0;
      const rango = UMBRALES[i].max - UMBRALES[i].min;
      const progresoPct = rango > 0 ? Math.min(100, ((r - UMBRALES[i].min) / rango) * 100) : 100;
      return {
        nombre: UMBRALES[i].nombre,
        siguienteUmbral: siguiente,
        ptsParaSubir,
        progresoPct,
      };
    }
  }
  return { nombre: '3ra', siguienteUmbral: null, ptsParaSubir: 0, progresoPct: 100 };
}

export default function Dashboard() {
  const { usuario } = useAuth();
  const navigate = useNavigate();
  const { salas, cargarSalas } = useSalas();

  const [loading, setLoading] = useState(true);
  const [ranking, setRanking] = useState<any[]>([]);
  const [partidos, setPartidos] = useState<PartidoHistorial[]>([]);

  const rating = usuario?.rating ?? 1200;
  const nombreCompleto = [usuario?.nombre, usuario?.apellido].filter(Boolean).join(' ') || usuario?.email?.split('@')[0] || 'Jugador';
  const ciudad = (usuario as any)?.ciudad;
  const esFemenino = usuario?.sexo === 'femenino' || usuario?.sexo === 'F';

  const { nombre: categoriaNombre, siguienteUmbral, ptsParaSubir, progresoPct } = getCategoriaDesdeRating(rating);
  const siguienteCategoria = useMemo(() => {
    const idx = UMBRALES.findIndex((u) => u.nombre === categoriaNombre);
    return idx >= 0 && idx < UMBRALES.length - 1 ? UMBRALES[idx + 1].nombre : null;
  }, [categoriaNombre]);

  const miEnRanking = useMemo(() => {
    if (!usuario?.id_usuario || !ranking.length) return null;
    return ranking.find((j: any) => j.id_usuario === usuario.id_usuario) ?? null;
  }, [ranking, usuario?.id_usuario]);

  const posicionRanking = miEnRanking ? (miEnRanking.posicion ?? ranking.findIndex((j: any) => j.id_usuario === usuario?.id_usuario) + 1) : null;
  const tendencia = (miEnRanking?.tendencia as string) || 'neutral';

  const proximaSala = useMemo(() => {
    if (!usuario?.id_usuario || !salas?.length) return null;
    const userId = usuario.id_usuario;
    const activas = salas.filter(
      (s: any) =>
        s.jugadores?.some((j: any) => j.id === userId || j.id === String(userId)) &&
        ['programada', 'activa', 'en_juego'].includes(s.estado)
    );
    if (activas.length === 0) return null;
    const ordenadas = [...activas].sort((a: any, b: any) => (a.fecha || '').localeCompare(b.fecha || ''));
    return ordenadas[0];
  }, [salas, usuario?.id_usuario]);

  const topJugadores = useMemo(() => {
    const masculinos = ranking.filter((j: any) => j.sexo === 'masculino' || j.sexo === 'M').slice(0, 5);
    const femeninos = ranking.filter((j: any) => j.sexo === 'femenino' || j.sexo === 'F').slice(0, 5);
    return { masculino: masculinos, femenino: femeninos };
  }, [ranking]);

  // Misma lógica que Mi Perfil: victorias, winrate y racha desde partidos
  const esVictoria = (p: PartidoHistorial): boolean => {
    if (!p.resultado && p.historial_rating) return p.historial_rating.delta > 0;
    if (!p.resultado) return false;
    const miEquipo = p.jugadores.find((j) => j.id_usuario === usuario?.id_usuario)?.equipo;
    if (miEquipo === 1) return p.resultado.sets_eq1 > p.resultado.sets_eq2;
    return p.resultado.sets_eq2 > p.resultado.sets_eq1;
  };

  const { totalPartidos, winrate, deltaEstaSemana } = useMemo(() => {
    const conResultado = partidos.filter((p) => p.resultado || p.historial_rating);
    const total = conResultado.length;
    const wins = conResultado.filter(esVictoria).length;
    const wr = total > 0 ? Math.round((wins / total) * 100) : 0;
    let racha = 0;
    let rachaW = true;
    const ordenados = [...partidos].sort((a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime());
    for (const p of ordenados) {
      if (!p.resultado && !p.historial_rating) continue;
      const v = esVictoria(p);
      if (racha === 0) {
        rachaW = v;
        racha = 1;
      } else if (v === rachaW) racha++;
      else break;
    }
    const hace7Dias = Date.now() - 7 * 24 * 60 * 60 * 1000;
    const deltaSemana = partidos
      .filter((p) => new Date(p.fecha).getTime() >= hace7Dias && p.historial_rating)
      .reduce((acc, p) => acc + (p.historial_rating?.delta ?? 0), 0);
    return { totalPartidos: total, winrate: wr, deltaEstaSemana: deltaSemana };
  }, [partidos, usuario?.id_usuario]);

  useEffect(() => {
    if (!usuario?.id_usuario) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [rankingRes, partidosRes] = await Promise.all([
          apiService.getRankingGeneral(50, 0), // Reducido de 200 a 50
          perfilService.getHistorial(usuario.id_usuario, 10).catch(() => []), // Reducido de 100 a 10 (solo necesitamos 3)
        ]);
        if (cancelled) return;
        setRanking(Array.isArray(rankingRes) ? rankingRes : []);
        setPartidos(Array.isArray(partidosRes) ? partidosRes : []);
      } catch (e) {
        if (!cancelled) setRanking([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [usuario?.id_usuario]);

  useEffect(() => {
    if (usuario?.id_usuario) cargarSalas();
  }, [usuario?.id_usuario, cargarSalas]);



  // Pts para llegar al Top 10 (diferencia con el 10° del ranking)
  const ptsAlTop10 = useMemo(() => {
    if (!ranking.length || ranking.length < 10) return null;
    const top10 = ranking[9];
    const ratingTop10 = top10?.rating ?? 0;
    const diff = ratingTop10 - rating;
    return diff > 0 ? diff : null;
  }, [ranking, rating]);

  const mensajeDinamico = useMemo(() => {
    if (tendencia === 'up' && (rating >= 1400 || ptsParaSubir < 50)) return { texto: 'Estás en tu mejor momento', icono: '🔥' };
    if (tendencia === 'up') return { texto: 'Seguí así, vas subiendo', icono: '📈' };
    if (tendencia === 'down' && totalPartidos >= 5) return { texto: 'Un partido más y recuperás', icono: '💪' };
    if (tendencia === 'down') return { texto: 'Cada partido suma', icono: '🎯' };
    if (winrate >= 60 && totalPartidos >= 10) return { texto: 'Excelente nivel', icono: '🏆' };
    if (totalPartidos === 0) return { texto: 'Jugá tu primer partido y sumá puntos', icono: '⚔️' };
    if (ptsAlTop10 != null && ptsAlTop10 <= 80) return { texto: `A ${ptsAlTop10} pts del Top 10`, icono: '🎯' };
    return { texto: 'Seguí jugando para subir en el ranking', icono: '🎾' };
  }, [tendencia, rating, ptsParaSubir, totalPartidos, winrate, ptsAlTop10]);

  const TendenciaIcon = tendencia === 'up' ? TrendingUp : tendencia === 'down' ? TrendingDown : Minus;

  return (
    <div className="w-full min-w-0 space-y-5 pb-6">
      {/* Hero Card - Grande y colorido */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <Card gradient className="overflow-hidden border-2 border-primary/30 shadow-2xl shadow-primary/20 bg-gradient-to-br from-primary/20 via-cardBg to-secondary/10 h-full">
            <div className="relative p-6 md:p-8 h-full flex flex-col justify-between">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-secondary/10" />
              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
              <div className="relative z-10 flex-1 flex items-center justify-between gap-6 md:gap-12">
                {loading ? (
                  <div className="flex justify-center py-8 w-full">
                    <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : (
                  <>
                    {/* Columna izquierda: Info del usuario */}
                    <div className="flex-1 flex flex-col justify-center">
                      <div className="mb-2">
                        <p className="text-base md:text-lg text-textSecondary font-medium mb-1">{esFemenino ? 'Bienvenida,' : 'Bienvenido,'}</p>
                        <div className="flex items-center gap-3 mb-2">
                          <h1 className="text-2xl md:text-3xl font-black text-textPrimary">{nombreCompleto}</h1>
                          <span className="px-3 py-1.5 rounded-lg text-xs font-black uppercase bg-gradient-to-r from-primary to-primary/80 text-white border-2 border-primary/60 shadow-lg flex-shrink-0">
                            {categoriaNombre}
                          </span>
                        </div>
                      </div>
                      {posicionRanking && ciudad && (
                        <p className="text-sm font-bold text-accent mb-4">#{posicionRanking} en {ciudad}</p>
                      )}
                    
                    {/* Últimos 3 partidos */}
                    {partidos.length > 0 && (
                      <div className="flex items-center gap-3 mb-4">
                        <span className="text-xs text-textSecondary font-semibold">Últimos 3 partidos:</span>
                        <div className="flex gap-2">
                          {partidos.slice(0, 3).map((partido, idx) => {
                            const victoria = esVictoria(partido);
                            return (
                              <div key={idx} className={`w-7 h-7 rounded-full flex items-center justify-center shadow-lg ${victoria ? 'bg-green-500' : 'bg-red-500'}`}>
                                <span className="text-white text-sm font-black">{victoria ? '✓' : '✗'}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Variación de rating */}
                    {deltaEstaSemana !== 0 && (
                      <div className={`flex items-center gap-2 mb-4 px-3 py-1.5 rounded-lg border-2 inline-flex ${deltaEstaSemana > 0 ? 'bg-green-500/20 border-green-500/40 text-green-400' : 'bg-red-500/20 border-red-500/40 text-red-400'}`}>
                        <TendenciaIcon className="w-4 h-4" />
                        <span className="text-sm font-black">{deltaEstaSemana > 0 ? '+' : ''}{deltaEstaSemana} pts esta semana</span>
                      </div>
                    )}
                    
                      {siguienteCategoria && siguienteUmbral && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm font-bold">
                            <span className="text-textPrimary">Estás a {ptsParaSubir} pts de {siguienteCategoria}</span>
                            <span className="text-accent">{Math.round(progresoPct)}%</span>
                          </div>
                          <div className="h-3 bg-cardBorder/50 rounded-full overflow-hidden shadow-inner">
                            <div className="h-full bg-gradient-to-r from-primary via-blue-400 to-accent rounded-full transition-all duration-500 shadow-lg" style={{ width: `${progresoPct}%` }} />
                          </div>
                          {/* Mensaje motivacional mejorado */}
                          {ptsParaSubir <= 100 && (
                            <p className="text-xs text-accent font-bold">
                              💪 Ganando {Math.ceil(ptsParaSubir / 25)} partidos podrías ascender
                            </p>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Columna derecha: Rating gigante */}
                    <div className="flex flex-col items-end justify-center">
                      <div className="text-right">
                        <span className="block text-[50px] md:text-[80px] leading-none font-black text-primary tabular-nums drop-shadow-[0_0_35px_rgba(0,85,255,0.7)]">{rating}</span>
                        <span className="block text-sm md:text-lg text-textSecondary font-bold -mt-1 md:-mt-2">pts</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* Stats y acciones */}
        <div className="flex flex-col gap-4">
          {/* Mensaje motivacional mejorado */}
          <div className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-accent/20 to-accent/10 border-2 border-accent/30 shadow-lg">
            <span className="text-3xl flex-shrink-0">{mensajeDinamico.icono}</span>
            <div>
              <p className="text-textPrimary font-bold text-sm">{mensajeDinamico.texto}</p>
              {ptsAlTop10 && ptsAlTop10 <= 100 && (
                <p className="text-xs text-accent font-semibold mt-1">🎯 A solo {ptsAlTop10} pts del Top 10</p>
              )}
            </div>
          </div>
          
          <Card className="border-2 border-cardBorder bg-gradient-to-br from-cardBg to-cardBg/50">
            <div className="flex justify-around gap-4 py-3">
              <div className="text-center">
                <div className="text-2xl font-black text-primary">{winrate}%</div>
                <div className="text-[10px] text-textSecondary font-semibold">Winrate</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-black text-secondary">{totalPartidos}</div>
                <div className="text-[10px] text-textSecondary font-semibold">Partidos</div>
              </div>
            </div>
          </Card>
          
          <Card className="flex-1 border-2 border-cardBorder">
            <div className="p-4">
              <h2 className="text-sm font-black text-textPrimary mb-3 flex items-center gap-2">
                <Swords className="w-5 h-5 text-primary" />
                Próximo partido
              </h2>
              {proximaSala ? (
                <div onClick={() => navigate('/salas')} className="p-3 rounded-xl bg-gradient-to-r from-primary/20 to-primary/10 border-2 border-primary/40 hover:border-primary/60 cursor-pointer transition-all hover:scale-[1.02]">
                  <p className="text-textPrimary text-sm font-bold">{proximaSala.nombre || 'Partido'}</p>
                  <p className="text-xs text-textSecondary">{proximaSala.fecha ? new Date(proximaSala.fecha).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' }) : 'Próximamente'}</p>
                </div>
              ) : (
                <div className="rounded-xl bg-gradient-to-br from-primary/30 to-secondary/30 border-2 border-primary/50 p-5 text-center shadow-xl">
                  <p className="text-textPrimary text-base font-black mb-4">Creá una sala y sumá puntos</p>
                  <button onClick={() => navigate('/salas')} className="w-full px-8 py-4 rounded-xl font-black text-lg bg-gradient-to-r from-primary via-blue-600 to-primary text-white hover:scale-105 transition-all shadow-2xl shadow-primary/50 border-2 border-primary/30">
                    <Target className="w-6 h-6 inline mr-2" />
                    Crear sala
                  </button>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Top jugadores + Invitaciones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card className="border-2 border-cardBorder shadow-xl">
          <div className="p-4 md:p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-black text-textPrimary flex items-center gap-2">
                <Crown className="w-5 h-5 text-accent" />
                Top Jugadores
              </h2>
              {ptsAlTop10 && (
                <p className="text-xs font-bold text-accent bg-accent/10 px-2.5 py-1 rounded-lg">A {ptsAlTop10} pts del Top 10</p>
              )}
            </div>
            {loading ? (
              <div className="flex justify-center py-6">
                <div className="w-6 h-6 border-3 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-black text-textSecondary uppercase mb-2">Masculino</p>
                  <div className="space-y-2">
                    {topJugadores.masculino.map((jugador: any, index: number) => (
                      <div key={jugador.id_usuario} onClick={() => jugador.nombre_usuario && navigate(`/perfil/${jugador.nombre_usuario}`)} className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all hover:scale-[1.02] border-2 ${index === 0 ? 'bg-gradient-to-r from-amber-500/20 to-amber-500/10 border-amber-500/40 shadow-lg' : 'bg-cardHover border-transparent hover:border-primary/30'}`}>
                        <span className={`text-xs font-black w-5 text-center ${index === 0 ? 'text-amber-400' : 'text-textSecondary'}`}>#{index + 1}</span>
                        <p className="text-sm font-bold text-textPrimary truncate flex-1">{jugador.nombre} {jugador.apellido}</p>
                        <span className="text-sm font-black text-primary">{jugador.rating}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-black text-textSecondary uppercase mb-2">Femenino</p>
                  <div className="space-y-2">
                    {topJugadores.femenino.map((jugador: any, index: number) => (
                      <div key={jugador.id_usuario} onClick={() => jugador.nombre_usuario && navigate(`/perfil/${jugador.nombre_usuario}`)} className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all hover:scale-[1.02] border-2 ${index === 0 ? 'bg-gradient-to-r from-amber-500/20 to-amber-500/10 border-amber-500/40 shadow-lg' : 'bg-cardBorder/50 border-transparent hover:border-secondary/30'}`}>
                        <span className={`text-xs font-black w-5 text-center ${index === 0 ? 'text-amber-400' : 'text-textSecondary'}`}>#{index + 1}</span>
                        <p className="text-sm font-bold text-textPrimary truncate flex-1">{jugador.nombre} {jugador.apellido}</p>
                        <span className="text-sm font-black text-secondary">{jugador.rating}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>

        <Card className="border-2 border-cardBorder shadow-xl">
          <div className="p-4 md:p-5">
            <h2 className="text-base font-black text-textPrimary mb-3 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-accent" />
              Invitaciones y Torneos
            </h2>
            <InvitacionesPendientes />
          </div>
        </Card>
      </div>
    </div>
  );
}
