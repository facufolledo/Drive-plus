import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../components/Card';
import Button from '../components/Button';
import ModalCrearTorneo from '../components/ModalCrearTorneo';
import TorneoCard from '../components/TorneoCard';
import SkeletonLoader from '../components/SkeletonLoader';
import InvitacionesPendientes from '../components/InvitacionesPendientes';
import { Plus, Filter, Trophy, User } from 'lucide-react';
import { useTorneos } from '../context/TorneosContext';
import { useAuth } from '../context/AuthContext';

export default function Torneos() {
  const { torneos, misTorneos, puedeCrearTorneos, esAdministrador, loading } = useTorneos();
  const { usuario } = useAuth();
  const [modalCrearOpen, setModalCrearOpen] = useState(false);
  const [filtro, setFiltro] = useState<'todos' | 'activo' | 'programado' | 'finalizado'>('todos');
  const [filtroGenero, setFiltroGenero] = useState<'todos' | 'masculino' | 'femenino' | 'mixto'>('todos');
  const [mostrarTodos, setMostrarTodos] = useState(false);
  const ITEMS_POR_PAGINA = 20;
  
  const puedeCrear = puedeCrearTorneos || esAdministrador;
  
  // IDs de mis torneos para filtrar
  const misTorneosIds = new Set(misTorneos.map(t => t.id));
  const misTorneosFiltrados = torneos.filter(t => misTorneosIds.has(parseInt(t.id)));

  const torneosActivos = torneos.filter(t => t.estado === 'activo');
  const torneosProgramados = torneos.filter(t => t.estado === 'programado');
  const torneosFinalizados = torneos.filter(t => t.estado === 'finalizado');

  // Filtrar por estado
  let torneosFiltrados = filtro === 'todos' 
    ? torneos 
    : torneos.filter(t => t.estado === filtro);

  // Filtrar por género
  if (filtroGenero !== 'todos') {
    torneosFiltrados = torneosFiltrados.filter(t => t.genero === filtroGenero);
  }

  // Separar torneos activos/programados de finalizados
  const torneosActivos_Programados = torneosFiltrados.filter(t => t.estado === 'activo' || t.estado === 'programado');
  const torneosFinalizadosFiltrados = torneosFiltrados.filter(t => t.estado === 'finalizado');

  const torneosActivosMostrados = mostrarTodos ? torneosActivos_Programados : torneosActivos_Programados.slice(0, ITEMS_POR_PAGINA);
  const torneosFinalizadosMostrados = mostrarTodos ? torneosFinalizadosFiltrados : torneosFinalizadosFiltrados.slice(0, ITEMS_POR_PAGINA);

  return (
    <div className="w-full min-w-0 space-y-6">
      {/* Header compacto */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3"
      >
        <div>
          <div className="flex items-center gap-2 md:gap-3 mb-1">
            <div className="h-0.5 md:h-1 w-8 md:w-10 bg-gradient-to-r from-accent to-yellow-500 rounded-full" />
            <h1 className="text-2xl md:text-4xl font-black text-textPrimary tracking-tight">
              Torneos
            </h1>
          </div>
          <p className="text-textSecondary text-xs md:text-sm ml-10 md:ml-13">Organiza y gestiona competencias</p>
        </div>
        {puedeCrear && (
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Button variant="accent" onClick={() => setModalCrearOpen(true)} className="text-sm md:text-base">
              <div className="flex items-center gap-1.5 md:gap-2">
                <Plus size={18} className="md:w-5 md:h-5" />
                <span className="hidden sm:inline">Nuevo Torneo</span>
                <span className="sm:hidden">Nuevo</span>
              </div>
            </Button>
          </motion.div>
        )}
      </motion.div>

      {/* Invitaciones pendientes */}
      <InvitacionesPendientes />

      {/* Hero Stats + Filtros - Todo en un bloque premium */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="relative overflow-hidden rounded-2xl p-5 md:p-7"
        style={{
          background: 'rgba(20, 25, 40, 0.6)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
        }}
      >
        {/* Gradiente sutil de fondo */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5 pointer-events-none" />
        
        <div className="relative space-y-5">
          {/* Stats en línea */}
          <div className="flex flex-wrap items-center gap-4 md:gap-8 text-sm md:text-base">
            <div className="flex items-center gap-2">
              <span className="text-textSecondary/80 text-xs md:text-sm">Total:</span>
              <span className="font-black text-textPrimary text-xl md:text-2xl">{torneos.length}</span>
            </div>
            <div className="h-5 w-px bg-white/10 hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="text-textSecondary/80 text-xs md:text-sm">Mis Torneos:</span>
              <span className="font-black text-green-400 text-xl md:text-2xl">{misTorneosFiltrados.length}</span>
            </div>
            <div className="h-5 w-px bg-white/10 hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="text-textSecondary/80 text-xs md:text-sm">En Curso:</span>
              <span className="font-black text-secondary text-xl md:text-2xl">{torneosActivos.length}</span>
              {torneosActivos.length > 0 && <span className="text-secondary">🔥</span>}
            </div>
            <div className="h-5 w-px bg-white/10 hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="text-textSecondary/80 text-xs md:text-sm">Programados:</span>
              <span className="font-black text-primary text-xl md:text-2xl">{torneosProgramados.length}</span>
            </div>
            <div className="h-5 w-px bg-white/10 hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="text-textSecondary/80 text-xs md:text-sm">Finalizados:</span>
              <span className="font-black text-accent text-xl md:text-2xl">{torneosFinalizados.length}</span>
            </div>
          </div>

          {/* Línea divisoria sutil */}
          <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

          {/* Filtros más sutiles y compactos */}
          <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-6">
            {/* Filtro por Estado */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-textSecondary/60 text-xs font-medium uppercase tracking-wider">Estado:</span>
              <div className="flex gap-1.5">
                {(['todos', 'activo', 'programado', 'finalizado'] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFiltro(f)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                      filtro === f
                        ? 'bg-accent/90 text-black shadow-md'
                        : 'bg-white/5 text-textSecondary/70 hover:bg-white/10 hover:text-textSecondary border border-white/5'
                    }`}
                  >
                    {f === 'todos' ? 'Todos' : f === 'activo' ? 'En Curso' : f === 'programado' ? 'Programados' : 'Finalizados'}
                  </button>
                ))}
              </div>
            </div>

            {/* Filtro por Género */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-textSecondary/60 text-xs font-medium uppercase tracking-wider">Género:</span>
              <div className="flex gap-1.5">
                {[
                  { value: 'todos', label: 'Todos', icon: '🏆' },
                  { value: 'masculino', label: 'Masculino', icon: '♂' },
                  { value: 'femenino', label: 'Femenino', icon: '♀' },
                  { value: 'mixto', label: 'Mixto', icon: '⚥' }
                ].map((g) => (
                  <button
                    key={g.value}
                    onClick={() => setFiltroGenero(g.value as any)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                      filtroGenero === g.value
                        ? 'bg-primary/90 text-white shadow-md'
                        : 'bg-white/5 text-textSecondary/70 hover:bg-white/10 hover:text-textSecondary border border-white/5'
                    }`}
                  >
                    <span className="text-xs">{g.icon}</span>
                    <span className="hidden sm:inline">{g.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Lista de torneos */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 md:gap-4">
          {[...Array(6)].map((_, i) => (
            <SkeletonLoader key={i} height="280px" />
          ))}
        </div>
      ) : torneosFiltrados.length === 0 ? (
        <Card>
          <div className="text-center py-8 md:py-12 text-textSecondary px-4">
            <div className="bg-accent/10 rounded-full w-16 h-16 md:w-20 md:h-20 flex items-center justify-center mx-auto mb-3 md:mb-4">
              <Trophy size={32} className="text-accent md:w-10 md:h-10" />
            </div>
            <p className="text-base md:text-lg mb-2 md:mb-4">
              {filtro === 'todos' 
                ? 'No hay torneos creados' 
                : `No hay torneos ${filtro === 'activo' ? 'en curso' : filtro === 'programado' ? 'programados' : 'finalizados'}`}
            </p>
            <p className="text-xs md:text-sm mb-3 md:mb-4">
              {filtro === 'todos' && puedeCrear && 'Crea tu primer torneo para comenzar a organizar competencias'}
              {filtro === 'todos' && !puedeCrear && 'Aún no hay torneos disponibles'}
            </p>
            {filtro === 'todos' && puedeCrear && (
              <Button variant="accent" onClick={() => setModalCrearOpen(true)} className="text-sm md:text-base">
                <div className="flex items-center gap-1.5 md:gap-2">
                  <Plus size={18} className="md:w-5 md:h-5" />
                  <span className="hidden sm:inline">Crear Primer Torneo</span>
                  <span className="sm:hidden">Crear Torneo</span>
                </div>
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="space-y-8">
          {/* Torneos Activos y Programados */}
          {torneosActivos_Programados.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="h-1 w-12 bg-gradient-to-r from-primary to-secondary rounded-full" />
                <h2 className="text-xl md:text-2xl font-black text-textPrimary">
                  Torneos Activos
                </h2>
                <span className="px-2 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold">
                  {torneosActivos_Programados.length}
                </span>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 md:gap-4">
                <AnimatePresence mode="popLayout">
                  {torneosActivosMostrados.map((torneo) => (
                    <TorneoCard
                      key={torneo.id}
                      torneo={torneo}
                    />
                  ))}
                </AnimatePresence>
              </div>

              {!mostrarTodos && torneosActivos_Programados.length > ITEMS_POR_PAGINA && (
                <div className="mt-4 text-center">
                  <Button
                    variant="accent"
                    onClick={() => setMostrarTodos(true)}
                    className="w-full md:w-auto"
                  >
                    Ver más ({torneosActivos_Programados.length - ITEMS_POR_PAGINA} restantes)
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Torneos Finalizados */}
          {torneosFinalizadosFiltrados.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="h-1 w-12 bg-gradient-to-r from-accent to-yellow-500 rounded-full" />
                <h2 className="text-xl md:text-2xl font-black text-textPrimary">
                  Torneos Finalizados
                </h2>
                <span className="px-2 py-1 rounded-full bg-accent/10 text-accent text-xs font-bold">
                  {torneosFinalizadosFiltrados.length}
                </span>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 md:gap-4">
                <AnimatePresence mode="popLayout">
                  {torneosFinalizadosMostrados.map((torneo) => (
                    <TorneoCard
                      key={torneo.id}
                      torneo={torneo}
                    />
                  ))}
                </AnimatePresence>
              </div>

              {!mostrarTodos && torneosFinalizadosFiltrados.length > ITEMS_POR_PAGINA && (
                <div className="mt-4 text-center">
                  <Button
                    variant="ghost"
                    onClick={() => setMostrarTodos(true)}
                    className="w-full md:w-auto"
                  >
                    Ver más ({torneosFinalizadosFiltrados.length - ITEMS_POR_PAGINA} restantes)
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Botón Mostrar Menos */}
          {mostrarTodos && (torneosActivos_Programados.length > ITEMS_POR_PAGINA || torneosFinalizadosFiltrados.length > ITEMS_POR_PAGINA) && (
            <div className="text-center">
              <Button
                variant="ghost"
                onClick={() => {
                  setMostrarTodos(false);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                className="w-full md:w-auto"
              >
                Mostrar menos
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Modal */}
      <ModalCrearTorneo isOpen={modalCrearOpen} onClose={() => setModalCrearOpen(false)} />
    </div>
  );
}
