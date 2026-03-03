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
  const [filtro, setFiltro] = useState<'todos' | 'activo' | 'programado' | 'finalizado' | 'mis-torneos'>('todos');
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
    : filtro === 'mis-torneos'
    ? misTorneosFiltrados
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
    <div className="w-full min-w-0 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 md:gap-4"
      >
        <div className="relative">
          <div className="flex items-center gap-2 md:gap-3 mb-1 md:mb-2">
            <div className="h-0.5 md:h-1 w-8 md:w-12 bg-gradient-to-r from-accent to-yellow-500 rounded-full" />
            <h1 className="text-2xl md:text-5xl font-black text-textPrimary tracking-tight">
              Torneos
            </h1>
          </div>
          <p className="text-textSecondary text-xs md:text-base ml-10 md:ml-15">Organiza y gestiona competencias</p>
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

      {/* Estadísticas compactas */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        {[
          { label: 'Total', value: torneos.length, color: 'from-cyan-500 to-blue-500', icon: '🏆' },
          { label: 'Mis Torneos', value: misTorneosFiltrados.length, color: 'from-green-500 to-emerald-500', icon: '👤' },
          { label: 'En Curso', value: torneosActivos.length, color: 'from-secondary to-pink-500', icon: '⚡' },
          { label: 'Programados', value: torneosProgramados.length, color: 'from-primary to-blue-500', icon: '📅' },
          { label: 'Finalizados', value: torneosFinalizados.length, color: 'from-accent to-yellow-400', icon: '✅' }
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.03 }}
            className="group relative"
          >
            <div className="bg-cardBg rounded-lg p-2 md:p-2.5 border border-cardBorder group-hover:border-transparent transition-all duration-200 relative overflow-hidden">
              <div className={`absolute -inset-[1px] bg-gradient-to-br ${stat.color} opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-lg -z-10 blur-sm`} />
              
              <div className="flex items-center justify-between mb-0.5 md:mb-1">
                <span className="text-sm md:text-base">{stat.icon}</span>
                <p className="text-xl md:text-2xl font-black text-textPrimary tracking-tight">
                  {stat.value}
                </p>
              </div>
              <p className="text-textSecondary text-[8px] md:text-[9px] font-bold uppercase tracking-wider">{stat.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Filtros compactos */}
      <div className="space-y-2">
        {/* Filtro por Estado */}
        <div className="flex items-center gap-1.5 md:gap-2 flex-wrap">
          <div className="flex items-center gap-1 md:gap-1.5 text-textSecondary">
            <Filter size={12} className="md:w-3.5 md:h-3.5" />
            <span className="text-[10px] md:text-xs font-bold">Estado:</span>
          </div>
          {(['todos', 'mis-torneos', 'activo', 'programado', 'finalizado'] as const).map((f) => (
            <Button
              key={f}
              variant={filtro === f ? 'accent' : 'secondary'}
              onClick={() => setFiltro(f)}
              className={`text-[10px] md:text-xs px-2 md:px-2.5 py-0.5 md:py-1 ${f === 'mis-torneos' ? 'flex items-center gap-1' : ''}`}
            >
              {f === 'mis-torneos' && <User size={12} />}
              {f === 'todos' ? 'Todos' : f === 'mis-torneos' ? 'Mis Torneos' : f === 'activo' ? 'En Curso' : f === 'programado' ? 'Programados' : 'Finalizados'}
            </Button>
          ))}
        </div>

        {/* Filtro por Género */}
        <div className="flex items-center gap-1.5 md:gap-2 flex-wrap">
          <div className="flex items-center gap-1 md:gap-1.5 text-textSecondary">
            <Filter size={12} className="md:w-3.5 md:h-3.5" />
            <span className="text-[10px] md:text-xs font-bold">Género:</span>
          </div>
          {[
            { value: 'todos', label: 'Todos', icon: '🏆' },
            { value: 'masculino', label: 'Masculino', icon: '♂' },
            { value: 'femenino', label: 'Femenino', icon: '♀' },
            { value: 'mixto', label: 'Mixto', icon: '⚥' }
          ].map((g) => (
            <Button
              key={g.value}
              variant={filtroGenero === g.value ? 'accent' : 'secondary'}
              onClick={() => setFiltroGenero(g.value as any)}
              className="text-[10px] md:text-xs px-2 md:px-2.5 py-0.5 md:py-1 flex items-center gap-1"
            >
              <span className="text-xs md:text-sm">{g.icon}</span>
              <span className="hidden sm:inline">{g.label}</span>
            </Button>
          ))}
        </div>
      </div>

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
