import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, Clock, Loader2 } from 'lucide-react';
import Button from './Button';
import { torneoService } from '../services/torneo.service';

interface ModalEditarTorneoProps {
  isOpen: boolean;
  onClose: () => void;
  torneo: any;
  onSuccess: () => void;
}

export default function ModalEditarTorneo({ isOpen, onClose, torneo, onSuccess }: ModalEditarTorneoProps) {
  const [descripcion, setDescripcion] = useState('');
  const [horariosDisponibles, setHorariosDisponibles] = useState<{
    semana: {desde: string, hasta: string}[],
    finDeSemana: {desde: string, hasta: string}[]
  }>({
    semana: [],
    finDeSemana: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && torneo) {
      setDescripcion(torneo.descripcion || '');
      
      // Parsear horarios del torneo
      const horarios = torneo.horarios_disponibles || {};
      const semana: {desde: string, hasta: string}[] = [];
      const finDeSemana: {desde: string, hasta: string}[] = [];
      
      // Extraer horarios de semana (lunes-viernes)
      const diasSemana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'];
      const horarioSemana = diasSemana.map(dia => horarios[dia]).find(h => h);
      if (horarioSemana) {
        semana.push({ desde: horarioSemana.inicio, hasta: horarioSemana.fin });
      }
      
      // Extraer horarios de fin de semana (sábado-domingo)
      const diasFinde = ['sabado', 'domingo'];
      const horarioFinde = diasFinde.map(dia => horarios[dia]).find(h => h);
      if (horarioFinde) {
        finDeSemana.push({ desde: horarioFinde.inicio, hasta: horarioFinde.fin });
      }
      
      setHorariosDisponibles({ semana, finDeSemana });
    }
  }, [isOpen, torneo]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Construir horarios en formato backend
      const horarios: Record<string, {inicio: string, fin: string}> = {};
      
      const horarioSemana = horariosDisponibles.semana.find(h => h.desde && h.hasta);
      if (horarioSemana) {
        ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'].forEach(dia => {
          horarios[dia] = { inicio: horarioSemana.desde, fin: horarioSemana.hasta };
        });
      }
      
      const horarioFinde = horariosDisponibles.finDeSemana.find(h => h.desde && h.hasta);
      if (horarioFinde) {
        ['sabado', 'domingo'].forEach(dia => {
          horarios[dia] = { inicio: horarioFinde.desde, fin: horarioFinde.hasta };
        });
      }

      await torneoService.actualizarTorneo(torneo.id, {
        descripcion: descripcion.trim() || undefined,
        horarios_disponibles: Object.keys(horarios).length > 0 ? horarios : undefined
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al actualizar el torneo');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />
          
          <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="bg-cardBg rounded-xl border border-cardBorder shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            >
              {/* Header */}
              <div className="sticky top-0 bg-cardBg border-b border-cardBorder p-4 flex items-center justify-between z-10">
                <h2 className="text-lg font-bold text-textPrimary">Editar Torneo</h2>
                <button onClick={onClose} className="text-textSecondary hover:text-textPrimary">
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-4 space-y-4">
                {error && (
                  <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-500 text-sm">
                    {error}
                  </div>
                )}

                {/* Descripción */}
                <div>
                  <label className="block text-textSecondary text-sm font-bold mb-2">
                    <FileText size={14} className="inline mr-1" />
                    Descripción
                  </label>
                  <textarea
                    value={descripcion}
                    onChange={(e) => setDescripcion(e.target.value)}
                    placeholder="Premios, reglas especiales..."
                    className="w-full bg-background border border-cardBorder rounded-lg px-3 py-2 text-sm text-textPrimary placeholder-textSecondary focus:outline-none focus:border-primary resize-none"
                    rows={3}
                  />
                </div>

                {/* Horarios disponibles */}
                <div className="bg-cardHover rounded-lg p-4">
                  <label className="block text-textSecondary text-sm font-bold mb-3">
                    <Clock size={14} className="inline mr-1" />
                    Horarios disponibles para jugar
                  </label>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Horarios de Semana */}
                    <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3">
                      <label className="block text-blue-400 text-xs font-bold mb-2">
                        Lunes a Viernes
                      </label>
                      
                      {horariosDisponibles.semana.map((horario, index) => (
                        <div key={index} className="flex gap-2 items-end mb-2">
                          <div className="flex-1">
                            <label className="block text-xs text-textSecondary mb-1">Desde</label>
                            <select
                              value={horario.desde}
                              onChange={(e) => {
                                const nuevos = {...horariosDisponibles};
                                nuevos.semana[index].desde = e.target.value;
                                setHorariosDisponibles(nuevos);
                              }}
                              className="w-full bg-background border border-cardBorder rounded-lg px-2 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-primary"
                            >
                              <option value="">Seleccionar</option>
                              {Array.from({ length: 48 }, (_, i) => {
                                const h = Math.floor(i / 2);
                                const m = i % 2 === 0 ? '00' : '30';
                                return `${h.toString().padStart(2, '0')}:${m}`;
                              }).concat(['23:59']).map(hora => (
                                <option key={hora} value={hora}>{hora}</option>
                              ))}
                            </select>
                          </div>
                          <div className="flex-1">
                            <label className="block text-xs text-textSecondary mb-1">Hasta</label>
                            <select
                              value={horario.hasta}
                              onChange={(e) => {
                                const nuevos = {...horariosDisponibles};
                                nuevos.semana[index].hasta = e.target.value;
                                setHorariosDisponibles(nuevos);
                              }}
                              className="w-full bg-background border border-cardBorder rounded-lg px-2 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-primary"
                              disabled={!horario.desde}
                            >
                              <option value="">Seleccionar</option>
                              {Array.from({ length: 48 }, (_, i) => {
                                const h = Math.floor(i / 2);
                                const m = i % 2 === 0 ? '00' : '30';
                                return `${h.toString().padStart(2, '0')}:${m}`;
                              }).concat(['23:59']).filter(hora => hora > horario.desde).map(hora => (
                                <option key={hora} value={hora}>{hora}</option>
                              ))}
                            </select>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              const nuevos = {...horariosDisponibles};
                              nuevos.semana = nuevos.semana.filter((_, i) => i !== index);
                              setHorariosDisponibles(nuevos);
                            }}
                            className="px-2 py-1.5 text-red-500 hover:bg-red-50 rounded text-xs"
                          >
                            ✕
                          </button>
                        </div>
                      ))}

                      <button
                        type="button"
                        onClick={() => {
                          const nuevos = {...horariosDisponibles};
                          nuevos.semana.push({ desde: '', hasta: '' });
                          setHorariosDisponibles(nuevos);
                        }}
                        className="w-full py-1.5 px-3 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg text-xs font-medium transition-colors"
                      >
                        + Agregar horario
                      </button>
                    </div>

                    {/* Horarios de Fin de Semana */}
                    <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-3">
                      <label className="block text-green-400 text-xs font-bold mb-2">
                        Sábado y Domingo
                      </label>
                      
                      {horariosDisponibles.finDeSemana.map((horario, index) => (
                        <div key={index} className="flex gap-2 items-end mb-2">
                          <div className="flex-1">
                            <label className="block text-xs text-textSecondary mb-1">Desde</label>
                            <select
                              value={horario.desde}
                              onChange={(e) => {
                                const nuevos = {...horariosDisponibles};
                                nuevos.finDeSemana[index].desde = e.target.value;
                                setHorariosDisponibles(nuevos);
                              }}
                              className="w-full bg-background border border-cardBorder rounded-lg px-2 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-primary"
                            >
                              <option value="">Seleccionar</option>
                              {Array.from({ length: 48 }, (_, i) => {
                                const h = Math.floor(i / 2);
                                const m = i % 2 === 0 ? '00' : '30';
                                return `${h.toString().padStart(2, '0')}:${m}`;
                              }).concat(['23:59']).map(hora => (
                                <option key={hora} value={hora}>{hora}</option>
                              ))}
                            </select>
                          </div>
                          <div className="flex-1">
                            <label className="block text-xs text-textSecondary mb-1">Hasta</label>
                            <select
                              value={horario.hasta}
                              onChange={(e) => {
                                const nuevos = {...horariosDisponibles};
                                nuevos.finDeSemana[index].hasta = e.target.value;
                                setHorariosDisponibles(nuevos);
                              }}
                              className="w-full bg-background border border-cardBorder rounded-lg px-2 py-1.5 text-xs text-textPrimary focus:outline-none focus:border-primary"
                              disabled={!horario.desde}
                            >
                              <option value="">Seleccionar</option>
                              {Array.from({ length: 48 }, (_, i) => {
                                const h = Math.floor(i / 2);
                                const m = i % 2 === 0 ? '00' : '30';
                                return `${h.toString().padStart(2, '0')}:${m}`;
                              }).concat(['23:59']).filter(hora => hora > horario.desde).map(hora => (
                                <option key={hora} value={hora}>{hora}</option>
                              ))}
                            </select>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              const nuevos = {...horariosDisponibles};
                              nuevos.finDeSemana = nuevos.finDeSemana.filter((_, i) => i !== index);
                              setHorariosDisponibles(nuevos);
                            }}
                            className="px-2 py-1.5 text-red-500 hover:bg-red-50 rounded text-xs"
                          >
                            ✕
                          </button>
                        </div>
                      ))}

                      <button
                        type="button"
                        onClick={() => {
                          const nuevos = {...horariosDisponibles};
                          nuevos.finDeSemana.push({ desde: '', hasta: '' });
                          setHorariosDisponibles(nuevos);
                        }}
                        className="w-full py-1.5 px-3 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-lg text-xs font-medium transition-colors"
                      >
                        + Agregar horario
                      </button>
                    </div>
                  </div>
                </div>

                {/* Botones */}
                <div className="flex gap-3 pt-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={onClose}
                    className="flex-1"
                    disabled={loading}
                  >
                    Cancelar
                  </Button>
                  <Button
                    type="submit"
                    variant="accent"
                    className="flex-1"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 size={16} className="animate-spin mr-2" />
                        Guardando...
                      </>
                    ) : (
                      'Guardar Cambios'
                    )}
                  </Button>
                </div>
              </form>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
