import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Calendar, MapPin, Trophy, Users, Settings, Clock } from 'lucide-react';
import { useTorneos } from '../context/TorneosContext';
import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';
import Button from '../components/Button';
import { TorneoDetalleSkeleton } from '../components/SkeletonLoader';
import ModalInscribirTorneo from '../components/ModalInscribirTorneo';
import TorneoZonas from '../components/TorneoZonas';
import TorneoFixture from '../components/TorneoFixture';
import TorneoPlayoffs from '../components/TorneoPlayoffs';
import TorneoProgramacion from '../components/TorneoProgramacion';
import TorneoParejas from '../components/TorneoParejas';
import TorneoCategorias from '../components/TorneoCategorias';
import GestionOrganizadores from '../components/GestionOrganizadores';
import ModalEditarTorneo from '../components/ModalEditarTorneo';

export default function TorneoDetalle() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { torneoActual, cargarTorneo, cargarParejas, parejas, loading } = useTorneos();
  const { usuario } = useAuth();
  const [tab, setTab] = useState<'info' | 'parejas' | 'zonas' | 'partidos' | 'playoffs' | 'programacion'>('info');
  const [modalInscripcionOpen, setModalInscripcionOpen] = useState(false);
  const [modalOrganizadoresOpen, setModalOrganizadoresOpen] = useState(false);
  const [modalEditarOpen, setModalEditarOpen] = useState(false);

  // Helper para parsear fechas sin problemas de zona horaria
  const parseFechaSinZonaHoraria = (fechaISO: string): Date => {
    const [year, month, day] = fechaISO.split('-').map(Number);
    return new Date(year, month - 1, day);
  };

  useEffect(() => {
    if (id) {
      cargarTorneo(parseInt(id));
      cargarParejas(parseInt(id));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // Verificar si el usuario ya está inscripto en el torneo
  const miInscripcion = parejas.find(p => 
    usuario && (p.jugador1_id === usuario.id_usuario || p.jugador2_id === usuario.id_usuario)
  );
  const estaInscripto = !!miInscripcion;
  const estadoInscripcion = miInscripcion?.estado;

  // Escuchar evento para cambiar tab
  useEffect(() => {
    const handleCambiarTab = (event: any) => {
      const detail = event.detail;
      // Soporta ambos formatos:
      // - detail: "partidos"
      // - detail: { tab: "partidos", categoriaId, zonaId }
      const tabTarget = typeof detail === 'string' ? detail : detail?.tab;
      if (tabTarget) setTab(tabTarget);
    };
    window.addEventListener('cambiarTab', handleCambiarTab);
    return () => window.removeEventListener('cambiarTab', handleCambiarTab);
  }, []);

  if (loading && !torneoActual) {
    return <TorneoDetalleSkeleton />;
  }

  if (!torneoActual) {
    return (
      <Card>
        <div className="text-center py-12">
          <Trophy size={48} className="mx-auto text-textSecondary mb-4" />
          <h2 className="text-xl font-bold text-textPrimary mb-2">Torneo no encontrado</h2>
          <p className="text-textSecondary mb-4">El torneo que buscas no existe o fue eliminado</p>
          <Button onClick={() => navigate('/torneos')}>
            Volver a Torneos
          </Button>
        </div>
      </Card>
    );
  }

  // Verificar si el usuario es el creador del torneo
  const esCreadorTorneo = usuario?.id_usuario === (torneoActual as any).creado_por;
  // El organizador puede ser el creador O estar en la tabla de organizadores O ser administrador
  const esOrganizador = (torneoActual as any).es_organizador || esCreadorTorneo || usuario?.es_administrador;
  
  // Permitir inscripción:
  // - Usuarios normales: solo cuando está en inscripción
  // - Creador del torneo: siempre (puede agregar parejas en cualquier momento)
  const torneoEnInscripcion = torneoActual.estado === 'programado' || 
                              (torneoActual as any).estado_original === 'inscripcion';
  const puedeInscribirse = torneoEnInscripcion || esCreadorTorneo;

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4"
      >
        <Button
          variant="ghost"
          onClick={() => navigate('/torneos')}
          className="flex items-center gap-2"
        >
          <ArrowLeft size={20} />
          Volver
        </Button>
      </motion.div>

      {/* Información del Torneo */}
      <Card>
        <div className="p-6">
          <div className="flex items-start justify-between gap-4 mb-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-accent/10 p-3 rounded-lg">
                  <Trophy className="text-accent" size={32} />
                </div>
                <div>
                  <h1 className="text-2xl md:text-3xl font-bold text-textPrimary">{torneoActual.nombre}</h1>
                  <p className="text-textSecondary">Categoría {torneoActual.categoria}</p>
                </div>
              </div>
            </div>
            
            {/* Estado PROTAGONISTA - Badge grande */}
            <div className="flex flex-col items-end gap-3">
              <div className={`inline-flex items-center gap-2 px-5 py-3 rounded-xl font-black text-sm uppercase tracking-wider shadow-lg ${
                torneoActual.estado === 'programado' 
                  ? 'bg-gradient-to-r from-emerald-600/80 to-emerald-700/80 text-white border-2 border-emerald-500/50'
                  : torneoActual.estado === 'activo'
                  ? 'bg-gradient-to-r from-primary to-blue-600 text-white border-2 border-primary'
                  : 'bg-gradient-to-r from-gray-500 to-gray-600 text-white border-2 border-gray-400'
              }`}>
                <span className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" />
                {torneoActual.estado === 'programado' && 'Inscripciones Abiertas'}
                {torneoActual.estado === 'activo' && 'En Curso'}
                {torneoActual.estado === 'finalizado' && 'Finalizado'}
              </div>
              
              {esOrganizador && (
                <Button variant="ghost" className="flex items-center gap-2 text-xs" onClick={() => setModalEditarOpen(true)}>
                  <Settings size={16} />
                  Gestionar
                </Button>
              )}
            </div>
          </div>

          {/* Información básica */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="flex items-center gap-3 p-4 bg-background rounded-lg">
              <Calendar className="text-primary" size={24} />
              <div>
                <p className="text-xs text-textSecondary">Fechas</p>
                <p className="font-bold text-textPrimary">
                  {parseFechaSinZonaHoraria(torneoActual.fechaInicio).toLocaleDateString('es-ES', { 
                    day: 'numeric', 
                    month: 'short' 
                  })} - {parseFechaSinZonaHoraria(torneoActual.fechaFin).toLocaleDateString('es-ES', { 
                    day: 'numeric', 
                    month: 'short',
                    year: 'numeric'
                  })}
                </p>
              </div>
            </div>

            {torneoActual.lugar && (
              <div className="flex items-center gap-3 p-4 bg-background rounded-lg">
                <MapPin className="text-primary" size={24} />
                <div>
                  <p className="text-xs text-textSecondary">Lugar</p>
                  <p className="font-bold text-textPrimary">{torneoActual.lugar}</p>
                </div>
              </div>
            )}

            <div className="flex items-center gap-3 p-4 bg-background rounded-lg">
              <Users className="text-primary" size={24} />
              <div>
                <p className="text-xs text-textSecondary">Parejas Inscritas</p>
                <p className="font-bold text-textPrimary">{parejas.length}</p>
              </div>
            </div>
          </div>

          {/* Horarios del torneo - MEJORADO */}
          {(() => {
            const horarios = (torneoActual as any).horarios_disponibles;
            if (!horarios) return null;
            
            // Formato nuevo: por día específico
            const diasConHorarios = Object.entries(horarios).filter(([key]) => 
              !['semana', 'finDeSemana'].includes(key)
            );
            
            // Formato antiguo: semana y finDeSemana
            const tieneFormatoAntiguo = horarios.semana || horarios.finDeSemana;
            
            if (diasConHorarios.length === 0 && !tieneFormatoAntiguo) return null;
            
            const nombresDias: Record<string, string> = {
              'lunes': 'Lunes',
              'martes': 'Martes',
              'miercoles': 'Miércoles',
              'jueves': 'Jueves',
              'viernes': 'Viernes',
              'sabado': 'Sábado',
              'domingo': 'Domingo'
            };
            
            return (
              <div className="mb-6 p-5 bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl border-2 border-primary/30">
                <h3 className="font-black text-textPrimary mb-4 flex items-center gap-2 text-lg">
                  <Clock className="text-primary" size={22} />
                  Horarios del Torneo
                </h3>
                <div className="space-y-2">
                  {/* Formato nuevo: por día */}
                  {diasConHorarios.map(([dia, horario]: [string, any]) => (
                    <div key={dia} className="flex items-center justify-between bg-cardBg px-4 py-3 rounded-lg border border-cardBorder hover:border-primary/50 transition-colors">
                      <span className="text-sm font-black text-textPrimary capitalize min-w-[100px]">
                        {nombresDias[dia] || dia}
                      </span>
                      <span className="text-sm text-textSecondary font-bold">
                        {horario.inicio} – {horario.fin}
                      </span>
                    </div>
                  ))}
                  
                  {/* Formato antiguo: semana y fin de semana */}
                  {horarios.semana && horarios.semana.length > 0 && (
                    <div className="flex items-center justify-between bg-cardBg px-4 py-3 rounded-lg border border-cardBorder">
                      <span className="text-sm font-black text-textPrimary min-w-[100px]">Lun-Vie</span>
                      <span className="text-sm text-textSecondary font-bold">
                        {horarios.semana.map((franja: any, idx: number) => (
                          <span key={idx}>
                            {franja.desde} – {franja.hasta}
                            {idx < horarios.semana.length - 1 && ' | '}
                          </span>
                        ))}
                      </span>
                    </div>
                  )}
                  {horarios.finDeSemana && horarios.finDeSemana.length > 0 && (
                    <div className="flex items-center justify-between bg-cardBg px-4 py-3 rounded-lg border border-cardBorder">
                      <span className="text-sm font-black text-textPrimary min-w-[100px]">Sáb-Dom</span>
                      <span className="text-sm text-textSecondary font-bold">
                        {horarios.finDeSemana.map((franja: any, idx: number) => (
                          <span key={idx}>
                            {franja.desde} – {franja.hasta}
                            {idx < horarios.finDeSemana.length - 1 && ' | '}
                          </span>
                        ))}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })()}

          {/* Descripción */}
          <div className="mb-6">
            <h3 className="font-bold text-textPrimary mb-2">Descripción</h3>
            <p className="text-textSecondary">{torneoActual.descripcion || 'Sin descripción'}</p>
          </div>

          {/* Estado de inscripción o botón para inscribirse */}
          <div className="border-t border-cardBorder pt-6">
            {estaInscripto ? (
              <div className="flex items-center gap-3">
                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
                  estadoInscripcion === 'confirmada'
                    ? 'bg-green-500/10 text-green-500'
                    : estadoInscripcion === 'inscripta'
                    ? 'bg-yellow-500/10 text-yellow-500'
                    : estadoInscripcion === 'pendiente'
                    ? 'bg-yellow-500/10 text-yellow-500'
                    : 'bg-gray-500/10 text-gray-500'
                }`}>
                  <span className="w-2 h-2 rounded-full bg-current" />
                  <span className="font-bold text-sm">
                    {estadoInscripcion === 'inscripta' && '⏳ Pendiente de confirmación'}
                    {estadoInscripcion === 'confirmada' && '✓ Confirmado'}
                    {estadoInscripcion === 'pendiente' && '⏳ Esperando confirmación de compañero'}
                    {!['inscripta', 'confirmada', 'pendiente'].includes(estadoInscripcion || '') && 'Participando'}
                  </span>
                </div>
                {/* El organizador puede seguir inscribiendo otras parejas */}
                {esOrganizador && puedeInscribirse && (
                  <Button
                    variant="ghost"
                    onClick={() => setModalInscripcionOpen(true)}
                    className="text-sm"
                  >
                    + Inscribir otra pareja
                  </Button>
                )}
              </div>
            ) : puedeInscribirse ? (
              <Button
                variant="accent"
                onClick={() => setModalInscripcionOpen(true)}
                className="w-full md:w-auto"
              >
                Inscribir Pareja
              </Button>
            ) : null}
          </div>
        </div>
      </Card>

      {/* Tabs - MEJORADOS con línea más fuerte y animación */}
      <div className="relative border-b-2 border-cardBorder/50 overflow-x-auto">
        <div className="flex gap-1">
          <button
            onClick={() => setTab('info')}
            className={`relative px-5 py-3 font-black transition-all whitespace-nowrap ${
              tab === 'info'
                ? 'text-primary'
                : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            Información
            {tab === 'info' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-accent rounded-t-full shadow-lg shadow-primary/50"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
          </button>
          {/* Parejas solo visible para organizador */}
          {esOrganizador && (
            <button
              onClick={() => setTab('parejas')}
              className={`relative px-5 py-3 font-black transition-all whitespace-nowrap ${
                tab === 'parejas'
                  ? 'text-primary'
                  : 'text-textSecondary hover:text-textPrimary'
              }`}
            >
              Parejas ({parejas.length})
              {tab === 'parejas' && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-accent rounded-t-full shadow-lg shadow-primary/50"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
            </button>
          )}
          <button
            onClick={() => setTab('zonas')}
            className={`relative px-5 py-3 font-black transition-all whitespace-nowrap ${
              tab === 'zonas'
                ? 'text-primary'
                : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            Zonas
            {tab === 'zonas' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-accent rounded-t-full shadow-lg shadow-primary/50"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
          </button>
          <button
            onClick={() => setTab('partidos')}
            className={`relative px-5 py-3 font-black transition-all whitespace-nowrap ${
              tab === 'partidos'
                ? 'text-primary'
                : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            Fixture
            {tab === 'partidos' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-accent rounded-t-full shadow-lg shadow-primary/50"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
          </button>
          <button
            onClick={() => setTab('playoffs')}
            className={`relative px-5 py-3 font-black transition-all whitespace-nowrap flex items-center gap-2 ${
              tab === 'playoffs'
                ? 'text-accent'
                : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            <Trophy size={16} />
            Playoffs
            {tab === 'playoffs' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-accent to-yellow-500 rounded-t-full shadow-lg shadow-accent/50"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
          </button>
          {/* Programación solo visible para organizador */}
          {esOrganizador && (
            <button
              onClick={() => setTab('programacion')}
              className={`relative px-5 py-3 font-black transition-all whitespace-nowrap flex items-center gap-2 ${
                tab === 'programacion'
                  ? 'text-primary'
                  : 'text-textSecondary hover:text-textPrimary'
              }`}
            >
              <Settings size={16} />
              Programación
              {tab === 'programacion' && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-accent rounded-t-full shadow-lg shadow-primary/50"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Contenido de tabs */}
      {tab === 'info' && (
        <div className="space-y-4">
          {/* Categorías del torneo */}
          <TorneoCategorias 
            torneoId={parseInt(id!)} 
            esOrganizador={esOrganizador}
          />
          
          <Card>
            <div className="p-6">
              <h3 className="font-bold text-textPrimary mb-4">Información del Torneo</h3>
              <div className="space-y-2 text-textSecondary">
                <p>• Formato: {torneoActual.formato || 'Eliminación simple'}</p>
                <p>• Género: {torneoActual.genero || 'Mixto'}</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {tab === 'parejas' && (
        <TorneoParejas 
          torneoId={parseInt(id!)} 
          parejas={parejas} 
          esOrganizador={esOrganizador}
          onUpdate={() => cargarParejas(parseInt(id!))}
        />
      )}

      {tab === 'zonas' && (
        <TorneoZonas torneoId={parseInt(id!)} esOrganizador={esOrganizador} />
      )}

      {tab === 'partidos' && (
        <TorneoFixture torneoId={parseInt(id!)} esOrganizador={esOrganizador} />
      )}

      {tab === 'playoffs' && (
        <TorneoPlayoffs torneoId={parseInt(id!)} esOrganizador={esOrganizador} />
      )}

      {tab === 'programacion' && esOrganizador && (
        <TorneoProgramacion torneoId={parseInt(id!)} esOrganizador={esOrganizador} />
      )}

      {/* Modal de Inscripción */}
      <ModalInscribirTorneo
        isOpen={modalInscripcionOpen}
        onClose={() => setModalInscripcionOpen(false)}
        torneoId={parseInt(id!)}
        torneoNombre={torneoActual?.nombre || ''}
        esOrganizador={esOrganizador}
        fechaInicio={torneoActual?.fecha_inicio}
        fechaFin={torneoActual?.fecha_fin}
        onInscripcionExitosa={() => {
          // Recargar datos del torneo y parejas después de inscripción exitosa
          cargarTorneo(parseInt(id!));
          cargarParejas(parseInt(id!));
        }}
      />

      <GestionOrganizadores
        isOpen={modalOrganizadoresOpen}
        onClose={() => setModalOrganizadoresOpen(false)}
        torneoId={parseInt(id!)}
        esOwner={esCreadorTorneo}
      />

      <ModalEditarTorneo
        isOpen={modalEditarOpen}
        onClose={() => setModalEditarOpen(false)}
        torneo={torneoActual}
        onSuccess={() => {
          cargarTorneo(parseInt(id!));
        }}
      />
    </div>
  );
}
