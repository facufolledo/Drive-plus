import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, UserPlus, Crown, Shield, Trash2, Search, Loader2 } from 'lucide-react';
import Button from './Button';
import Input from './Input';
import { torneoService } from '../services/torneo.service';

interface Organizador {
  id: number;
  user_id: number;
  rol: string;
  nombre: string;
  apellido: string;
  nombre_usuario: string;
  imagen_url?: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  torneoId: number;
  esOwner: boolean;
}

export default function GestionOrganizadores({ isOpen, onClose, torneoId, esOwner }: Props) {
  const [organizadores, setOrganizadores] = useState<Organizador[]>([]);
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState('');
  const [agregando, setAgregando] = useState(false);
  const [error, setError] = useState('');
  const [exito, setExito] = useState('');

  useEffect(() => {
    if (isOpen) cargarOrganizadores();
  }, [isOpen, torneoId]);

  const cargarOrganizadores = async () => {
    try {
      setLoading(true);
      const data = await torneoService.listarOrganizadores(torneoId);
      setOrganizadores(data);
    } catch (err) {
      console.error('Error cargando organizadores:', err);
    } finally {
      setLoading(false);
    }
  };

  const agregarOrganizador = async () => {
    if (!username.trim()) return;
    try {
      setAgregando(true);
      setError('');
      setExito('');
      await torneoService.agregarOrganizador(torneoId, { username: username.trim() });
      setExito(`@${username.trim()} agregado como organizador`);
      setUsername('');
      await cargarOrganizadores();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al agregar organizador');
    } finally {
      setAgregando(false);
    }
  };

  const removerOrganizador = async (userId: number, nombreUsuario: string) => {
    if (!confirm(`¿Remover a @${nombreUsuario} como organizador?`)) return;
    try {
      setError('');
      await torneoService.removerOrganizador(torneoId, userId);
      setExito(`@${nombreUsuario} removido`);
      await cargarOrganizadores();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al remover organizador');
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
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-cardBg rounded-xl border border-cardBorder shadow-2xl w-full max-w-md max-h-[80vh] overflow-y-auto"
            >
              {/* Header */}
              <div className="sticky top-0 bg-cardBg border-b border-cardBorder p-4 flex items-center justify-between z-10">
                <div className="flex items-center gap-2">
                  <Shield className="text-accent" size={20} />
                  <h2 className="text-base font-bold text-textPrimary">Organizadores</h2>
                </div>
                <button onClick={onClose} className="text-textSecondary hover:text-textPrimary">
                  <X size={18} />
                </button>
              </div>

              <div className="p-4 space-y-4">
                {/* Mensajes */}
                {error && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-2 text-red-400 text-xs">
                    {error}
                  </div>
                )}
                {exito && (
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-2 text-green-400 text-xs">
                    {exito}
                  </div>
                )}

                {/* Agregar organizador (solo owner) */}
                {esOwner && (
                  <div className="bg-cardHover rounded-lg p-3">
                    <label className="block text-textSecondary text-xs font-bold mb-2">
                      <UserPlus size={12} className="inline mr-1" />
                      Agregar organizador
                    </label>
                    <div className="flex gap-2">
                      <div className="flex-1 relative">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-textSecondary" size={14} />
                        <Input
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                          placeholder="Username del usuario"
                          className="pl-8 text-sm"
                          onKeyDown={(e) => e.key === 'Enter' && agregarOrganizador()}
                        />
                      </div>
                      <Button
                        variant="accent"
                        onClick={agregarOrganizador}
                        disabled={agregando || !username.trim()}
                        className="text-xs px-3"
                      >
                        {agregando ? <Loader2 size={14} className="animate-spin" /> : 'Agregar'}
                      </Button>
                    </div>
                  </div>
                )}

                {/* Lista de organizadores */}
                <div className="space-y-2">
                  {loading ? (
                    <div className="text-center py-4 text-textSecondary text-sm">
                      <Loader2 size={20} className="animate-spin mx-auto mb-2" />
                      Cargando...
                    </div>
                  ) : organizadores.length === 0 ? (
                    <p className="text-center py-4 text-textSecondary text-sm">Sin organizadores</p>
                  ) : (
                    organizadores.map((org) => (
                      <div
                        key={org.id}
                        className="flex items-center justify-between bg-cardHover rounded-lg p-3"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold ${
                            org.rol === 'owner' ? 'bg-gradient-to-br from-yellow-500 to-orange-500' : 'bg-gradient-to-br from-blue-500 to-blue-600'
                          }`}>
                            {org.rol === 'owner' ? <Crown size={14} /> : <Shield size={14} />}
                          </div>
                          <div>
                            <p className="text-textPrimary text-sm font-bold">
                              {org.nombre} {org.apellido}
                            </p>
                            <p className="text-textSecondary text-xs">
                              @{org.nombre_usuario} · {org.rol === 'owner' ? 'Creador' : 'Colaborador'}
                            </p>
                          </div>
                        </div>
                        {esOwner && org.rol !== 'owner' && (
                          <button
                            onClick={() => removerOrganizador(org.user_id, org.nombre_usuario)}
                            className="text-red-400 hover:text-red-300 p-1"
                            title="Remover organizador"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
