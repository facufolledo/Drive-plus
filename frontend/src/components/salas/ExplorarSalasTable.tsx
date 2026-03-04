import { motion } from 'framer-motion';
import { Search, Users, Calendar, Eye, UserPlus } from 'lucide-react';
import Button from '../Button';
import { useState, useMemo } from 'react';

interface SalaExplorar {
  id: string;
  nombre: string;
  jugadores_actuales: number;
  jugadores_maximos: number;
  estado: string;
  fecha: string;
  creador?: string;
}

interface ExplorarSalasTableProps {
  salas: any[];
  onUnirseSala: (salaId: number) => void;
  onVerSala: (salaId: number) => void;
  busqueda: string;
  loading?: boolean;
  soloLectura?: boolean;
  onCrearSala?: () => void;
}

export default function ExplorarSalasTable({ 
  salas, 
  onUnirseSala, 
  onVerSala, 
  busqueda, 
  loading, 
  soloLectura = false,
  onCrearSala
}: ExplorarSalasTableProps) {
  const [paginaActual, setPaginaActual] = useState(1);
  const ITEMS_POR_PAGINA = 10;

  // Convertir salas al formato esperado y filtrar por búsqueda
  const salasFormateadas: SalaExplorar[] = useMemo(() => {
    return salas
      .map(sala => ({
        id: sala.id,
        nombre: sala.nombre || `Sala #${sala.id}`,
        jugadores_actuales: sala.jugadores?.length || 0,
        jugadores_maximos: 4,
        estado: sala.estado === 'esperando' ? 'Esperando' : 
                sala.estado === 'activa' || sala.estado === 'en_juego' ? 'En juego' : 
                sala.estado === 'finalizada' ? 'Finalizada' : 'Programada',
        fecha: new Date(sala.fecha_creacion || Date.now()).toLocaleDateString('es-AR', { 
          day: '2-digit', 
          month: 'short',
          year: sala.estado === 'finalizada' ? 'numeric' : undefined
        }),
        creador: sala.creador_nombre || 'Usuario'
      }))
      .filter(sala => 
        !busqueda || 
        sala.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
        sala.creador?.toLowerCase().includes(busqueda.toLowerCase())
      );
  }, [salas, busqueda]);

  const totalPaginas = Math.ceil(salasFormateadas.length / ITEMS_POR_PAGINA);
  const salasVisibles = salasFormateadas.slice(
    (paginaActual - 1) * ITEMS_POR_PAGINA,
    paginaActual * ITEMS_POR_PAGINA
  );

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'Esperando': return 'text-yellow-400 bg-yellow-400/20';
      case 'En juego': return 'text-green-400 bg-green-400/20';
      case 'Finalizada': return 'text-gray-400 bg-gray-400/20';
      default: return 'text-blue-400 bg-blue-400/20';
    }
  };

  const getAccionButton = (sala: SalaExplorar) => {
    if (soloLectura || sala.estado === 'Finalizada') {
      return (
        <Button
          variant="ghost"
          onClick={() => onVerSala(parseInt(sala.id))}
          className="text-xs px-3 py-1.5 flex items-center gap-1"
        >
          <Eye size={12} />
          Ver
        </Button>
      );
    } else if (sala.estado === 'En juego') {
      return (
        <Button
          variant="secondary"
          onClick={() => onVerSala(parseInt(sala.id))}
          className="text-xs px-3 py-1.5 flex items-center gap-1"
        >
          <Eye size={12} />
          Ver
        </Button>
      );
    } else {
      return (
        <Button
          variant="primary"
          onClick={() => onUnirseSala(parseInt(sala.id))}
          className="text-xs px-3 py-1.5 flex items-center gap-1"
        >
          <UserPlus size={12} />
          Unirse
        </Button>
      );
    }
  };

  if (loading) {
    return (
      <div className="mb-8">
        <h2 className="text-xl font-bold text-textPrimary mb-4 flex items-center gap-2">
          <Search size={20} className="text-primary" />
          {soloLectura ? 'Historial de Salas' : 'Explorar salas'}
        </h2>
        <div className="bg-cardBg border border-cardBorder rounded-lg overflow-hidden">
          <div className="p-6">
            <div className="animate-pulse space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-12 bg-cardBorder/30 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <h2 className="text-xl font-bold text-textPrimary mb-4 flex items-center gap-2">
        <Search size={20} className="text-primary" />
        {soloLectura ? 'Historial de Salas' : 'Explorar salas'}
        {salasFormateadas.length > 0 && (
          <span className="text-textSecondary text-sm font-normal">
            ({salasFormateadas.length} {salasFormateadas.length === 1 ? 'sala' : 'salas'})
          </span>
        )}
      </h2>
      
      {salasFormateadas.length === 0 ? (
        <div className="bg-cardBg/50 border border-cardBorder rounded-lg p-8 text-center">
          <Search size={32} className="mx-auto mb-3 text-textSecondary opacity-50" />
          <p className="text-textSecondary text-sm mb-2">
            {busqueda ? `No se encontraron salas con "${busqueda}"` : 'No hay salas disponibles'}
          </p>
          {busqueda ? (
            <p className="text-textSecondary text-xs">
              Intenta con otros términos de búsqueda
            </p>
          ) : !soloLectura && onCrearSala ? (
            <div className="mt-4">
              <Button
                variant="primary"
                onClick={onCrearSala}
                className="flex items-center gap-2 mx-auto"
              >
                <UserPlus size={16} />
                Crear una sala
              </Button>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="bg-cardBg border border-cardBorder rounded-lg overflow-hidden">
          {/* Header de la tabla */}
          <div className="bg-cardBorder/20 px-6 py-4 border-b border-cardBorder">
            <div className="grid grid-cols-12 gap-4 text-xs font-bold text-textSecondary uppercase tracking-wider">
              <div className="col-span-4">Nombre</div>
              <div className="col-span-2">Jugadores</div>
              <div className="col-span-2">Estado</div>
              <div className="col-span-2">Fecha</div>
              <div className="col-span-2 text-right">Acción</div>
            </div>
          </div>

          {/* Filas de la tabla */}
          <div className="divide-y divide-cardBorder">
            {salasVisibles.map((sala, index) => (
              <motion.div
                key={sala.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="px-6 py-4 hover:bg-cardBorder/10 transition-colors"
              >
                <div className="grid grid-cols-12 gap-4 items-center">
                  {/* Nombre */}
                  <div className="col-span-4">
                    <div>
                      <p className="font-semibold text-textPrimary text-sm">{sala.nombre}</p>
                      <p className="text-xs text-textSecondary">por {sala.creador}</p>
                    </div>
                  </div>

                  {/* Jugadores */}
                  <div className="col-span-2">
                    <div className="flex items-center gap-1 text-sm text-textSecondary">
                      <Users size={14} />
                      <span>{sala.jugadores_actuales} / {sala.jugadores_maximos}</span>
                    </div>
                  </div>

                  {/* Estado */}
                  <div className="col-span-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-bold ${getEstadoColor(sala.estado)}`}>
                        {sala.estado === 'En juego' && '●'} {sala.estado}
                      </span>
                      {sala.estado === 'En juego' && (
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      )}
                    </div>
                  </div>

                  {/* Fecha */}
                  <div className="col-span-2">
                    <div className="flex items-center gap-1 text-sm text-textSecondary">
                      <Calendar size={12} />
                      <span>{sala.fecha}</span>
                    </div>
                  </div>

                  {/* Acción */}
                  <div className="col-span-2 text-right">
                    {getAccionButton(sala)}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Paginación */}
          {totalPaginas > 1 && (
            <div className="bg-cardBorder/10 px-6 py-4 border-t border-cardBorder">
              <div className="flex items-center justify-between">
                <p className="text-sm text-textSecondary">
                  Mostrando {((paginaActual - 1) * ITEMS_POR_PAGINA) + 1} a {Math.min(paginaActual * ITEMS_POR_PAGINA, salasFormateadas.length)} de {salasFormateadas.length} salas
                </p>
                
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => setPaginaActual(Math.max(1, paginaActual - 1))}
                    disabled={paginaActual === 1}
                    className="text-xs px-3 py-1.5"
                  >
                    Anterior
                  </Button>
                  
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(5, totalPaginas) }, (_, i) => {
                      const pagina = i + 1;
                      return (
                        <Button
                          key={pagina}
                          variant={paginaActual === pagina ? 'primary' : 'ghost'}
                          onClick={() => setPaginaActual(pagina)}
                          className="text-xs px-2 py-1.5 min-w-[32px]"
                        >
                          {pagina}
                        </Button>
                      );
                    })}
                  </div>
                  
                  <Button
                    variant="ghost"
                    onClick={() => setPaginaActual(Math.min(totalPaginas, paginaActual + 1))}
                    disabled={paginaActual === totalPaginas}
                    className="text-xs px-3 py-1.5"
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
