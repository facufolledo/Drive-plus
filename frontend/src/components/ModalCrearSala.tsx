import { useState } from 'react';
import { X, Copy, Share2, MessageCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import Modal from './Modal';
import Input from './Input';
import Button from './Button';
import { useSalas } from '../context/SalasContext';
import { useAuth } from '../context/AuthContext';

interface ModalCrearSalaProps {
  isOpen: boolean;
  onClose: () => void;
  onSalaCreada?: (salaId: string, codigo: string) => void;
}

export default function ModalCrearSala({ isOpen, onClose, onSalaCreada }: ModalCrearSalaProps) {
  const { addSala } = useSalas();
  const { usuario } = useAuth();
  const [formData, setFormData] = useState({
    nombre: '',
    fecha: '',
    hora: '',
    formato: 'best_of_3' as 'best_of_3' | 'best_of_3_supertiebreak',
  });
  const [salaCreada, setSalaCreada] = useState<{ id: string; codigo: string } | null>(null);
  const [copiado, setCopiado] = useState(false);
  const [creando, setCreando] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.nombre || !formData.fecha || !formData.hora) {
      alert('Por favor completa todos los campos');
      return;
    }

    if (!usuario) {
      alert('Debes iniciar sesión para crear una sala');
      return;
    }

    try {
      setCreando(true);
      
      // Combinar fecha y hora
      const fechaHora = `${formData.fecha}T${formData.hora}`;
      
      // Crear sala en el backend con timeout
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('La creación está tardando más de lo esperado. Por favor, verifica tu conexión.')), 15000)
      );
      
      const createPromise = addSala({
        nombre: formData.nombre,
        fecha: fechaHora,
        estado: 'esperando',
        creadoPor: usuario.id_usuario?.toString() || '',
        estadoConfirmacion: 'sin_resultado',
        resultadoFinal: false,
        equipoA: {
          jugador1: { id: '', nombre: '' },
          jugador2: { id: '', nombre: '' },
          puntos: 0,
          confirmado: false
        },
        equipoB: {
          jugador1: { id: '', nombre: '' },
          jugador2: { id: '', nombre: '' },
          puntos: 0,
          confirmado: false
        }
      });

      const codigo = await Promise.race([createPromise, timeoutPromise]) as string;

      const salaId = crypto.randomUUID(); // Temporal, el backend devuelve el ID real
      setSalaCreada({ id: salaId, codigo });
      
      if (onSalaCreada) {
        onSalaCreada(salaId, codigo);
      }
    } catch (error: any) {
      console.error('Error al crear sala:', error);
      alert(error.message || 'Error al crear la sala. Por favor, intenta nuevamente.');
    } finally {
      setCreando(false);
    }
  };

  const handleCerrar = () => {
    setFormData({
      nombre: '',
      fecha: '',
      hora: '',
      formato: 'best_of_3',
    });
    setSalaCreada(null);
    setCopiado(false);
    onClose();
  };

  const copiarCodigo = () => {
    if (salaCreada) {
      navigator.clipboard.writeText(salaCreada.codigo);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    }
  };

  const compartirWhatsApp = () => {
    if (salaCreada) {
      const appUrl = `${window.location.origin}/salas?codigo=${salaCreada.codigo}`;
      const mensaje = `¡Únete a mi partido de pádel!\n\nPartido: ${formData.nombre}\nFecha: ${new Date(formData.fecha).toLocaleDateString('es-ES')}\nHora: ${formData.hora}\n\nCódigo: ${salaCreada.codigo}\n\nEntra aquí: ${appUrl}`;
      window.open(`https://wa.me/?text=${encodeURIComponent(mensaje)}`, '_blank');
    }
  };

  const [linkCopiado, setLinkCopiado] = useState(false);

  const copiarLink = () => {
    if (salaCreada && salaCreada.codigo) {
      const link = `${window.location.origin}/salas?codigo=${salaCreada.codigo}`;
      navigator.clipboard.writeText(link);
      setLinkCopiado(true);
      setTimeout(() => setLinkCopiado(false), 2000);
    } else {
      alert('Error: No hay código disponible');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCerrar}>
      <div className="bg-cardBg rounded-xl md:rounded-2xl p-4 md:p-8 w-full max-w-lg border border-cardBorder">
        <div className="flex items-center justify-between mb-4 md:mb-6">
          <h2 className="text-xl md:text-2xl font-bold text-textPrimary">
            {salaCreada ? '¡Sala Creada!' : 'Nueva Sala'}
          </h2>
          <button
            onClick={handleCerrar}
            disabled={creando}
            className="text-textSecondary hover:text-textPrimary transition-colors disabled:opacity-50 p-2"
          >
            <X size={20} className="md:w-6 md:h-6" />
          </button>
        </div>

        {!salaCreada ? (
          <form onSubmit={handleSubmit} className="space-y-4 md:space-y-6">
            <div>
              <label className="block text-textSecondary text-xs md:text-sm font-medium mb-2">
                Nombre de la Sala *
              </label>
              <Input
                value={formData.nombre}
                onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                placeholder="Ej: Partido del Viernes"
                autoFocus
                disabled={creando}
                maxLength={50}
                className="text-sm md:text-base"
              />
            </div>

            <div className="grid grid-cols-2 gap-2 sm:gap-4">
              <div>
                <label className="block text-textSecondary text-xs md:text-sm font-medium mb-2">
                  Fecha *
                </label>
                <input
                  type="date"
                  value={formData.fecha}
                  onChange={(e) => setFormData({ ...formData, fecha: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                  disabled={creando}
                  className="w-full px-2 py-2 text-xs md:text-base bg-background border border-cardBorder rounded-lg text-textPrimary focus:outline-none focus:border-primary transition-colors disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-textSecondary text-xs md:text-sm font-medium mb-2">
                  Hora *
                </label>
                <input
                  type="time"
                  value={formData.hora}
                  onChange={(e) => setFormData({ ...formData, hora: e.target.value })}
                  disabled={creando}
                  className="w-full px-2 py-2 text-xs md:text-base bg-background border border-cardBorder rounded-lg text-textPrimary focus:outline-none focus:border-primary transition-colors disabled:opacity-50"
                />
              </div>
            </div>

            <div>
              <label className="block text-textSecondary text-xs md:text-sm font-medium mb-2">
                Formato del Partido
              </label>
              <div className="grid grid-cols-1 gap-2">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, formato: 'best_of_3' })}
                  disabled={creando}
                  className={`p-2 md:p-3 rounded-lg border-2 transition-all text-left disabled:opacity-50 ${
                    formData.formato === 'best_of_3'
                      ? 'border-primary bg-primary/10 text-textPrimary'
                      : 'border-cardBorder bg-background text-textSecondary hover:border-primary/50'
                  }`}
                >
                  <div className="font-bold text-xs md:text-sm">Best of 3 (Clásico)</div>
                  <div className="text-[10px] md:text-xs mt-1 text-textSecondary">Sets a 6 games • Tercer set normal si es necesario</div>
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, formato: 'best_of_3_supertiebreak' })}
                  disabled={creando}
                  className={`p-2 md:p-3 rounded-lg border-2 transition-all text-left disabled:opacity-50 ${
                    formData.formato === 'best_of_3_supertiebreak'
                      ? 'border-secondary bg-secondary/10 text-textPrimary'
                      : 'border-cardBorder bg-background text-textSecondary hover:border-secondary/50'
                  }`}
                >
                  <div className="font-bold text-xs md:text-sm">Best of 3 con SuperTiebreak</div>
                  <div className="text-[10px] md:text-xs mt-1 text-textSecondary">Sets a 6 games • SuperTiebreak a 10 en el tercero</div>
                </button>
              </div>
            </div>

            <div className="bg-primary/10 border border-primary/30 rounded-lg md:rounded-xl p-3 md:p-4">
              <p className="text-textSecondary text-xs md:text-sm">
                💡 <strong>Tip:</strong> Después de crear la sala, recibirás un código 
                de invitación para compartir con los demás jugadores.
              </p>
            </div>

            {creando && (
              <div className="bg-primary/10 border border-primary/30 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <div className="flex-1">
                    <p className="text-textPrimary text-sm font-medium">Creando sala...</p>
                    <p className="text-textSecondary text-xs">Esto puede tardar unos segundos</p>
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <Button type="button" variant="secondary" onClick={handleCerrar} className="flex-1" disabled={creando}>
                Cancelar
              </Button>
              <Button type="submit" variant="primary" className="flex-1" disabled={creando}>
                {creando ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Creando...
                  </span>
                ) : (
                  'Crear Sala'
                )}
              </Button>
            </div>
          </form>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-6"
          >
            <div className="text-center">
              <div className="bg-secondary/20 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl">✓</span>
              </div>
              <p className="text-textSecondary mb-2">Tu código de invitación es:</p>
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="text-5xl font-black text-primary tracking-widest cursor-pointer"
                onClick={copiarCodigo}
              >
                {salaCreada.codigo}
              </motion.div>
              {copiado && (
                <motion.p
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-secondary text-sm mt-2"
                >
                  ✓ Copiado al portapapeles
                </motion.p>
              )}
            </div>

            <div className="bg-background rounded-xl p-4 space-y-2">
              <p className="text-textPrimary font-semibold">📍 {formData.nombre}</p>
              <p className="text-textSecondary text-sm">
                📅 {new Date(formData.fecha).toLocaleDateString('es-ES', { 
                  weekday: 'long', 
                  day: 'numeric', 
                  month: 'long' 
                })}
              </p>
              <p className="text-textSecondary text-sm">⏰ {formData.hora}</p>
            </div>

            <div className="space-y-2">
              <p className="text-textSecondary text-sm font-medium">Compartir invitación:</p>
              <div className="grid grid-cols-3 gap-2">
                <Button
                  variant="ghost"
                  onClick={copiarCodigo}
                  className="flex flex-col items-center gap-1 py-3 relative"
                >
                  <Copy size={20} />
                  <span className="text-xs">{copiado ? '✓ Copiado' : 'Copiar'}</span>
                </Button>
                <Button
                  variant="ghost"
                  onClick={compartirWhatsApp}
                  className="flex flex-col items-center gap-1 py-3 bg-[#25D366]/20 hover:bg-[#25D366]/30 text-[#25D366]"
                >
                  <MessageCircle size={20} />
                  <span className="text-xs">WhatsApp</span>
                </Button>
                <Button
                  variant="ghost"
                  onClick={copiarLink}
                  className="flex flex-col items-center gap-1 py-3 relative"
                >
                  <Share2 size={20} />
                  <span className="text-xs">{linkCopiado ? '✓ Copiado' : 'Link'}</span>
                </Button>
              </div>
            </div>

            <Button variant="primary" onClick={handleCerrar} className="w-full">
              Ir a la Sala
            </Button>
          </motion.div>
        )}
      </div>
    </Modal>
  );
}
