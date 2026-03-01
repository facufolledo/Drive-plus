import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { User, Calendar, Hash, MapPin, Phone, Trophy } from 'lucide-react';
import Button from '../components/Button';
import Input from '../components/Input';
import Card from '../components/Card';
import { PerfilCompleto } from '../services/auth.service';
import { useAuth } from '../context/AuthContext';
import { useCategorias } from '../hooks/useCategorias';

export default function CompletarPerfil() {
  const navigate = useNavigate();
  const { firebaseUser, completeProfile, logout } = useAuth();
  const { getCategoriasNombres } = useCategorias();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  // Polling para verificar si el email fue verificado
  useEffect(() => {
    if (!firebaseUser || firebaseUser.emailVerified) return;

    const checkEmailVerification = async () => {
      try {
        await firebaseUser.reload();
        if (firebaseUser.emailVerified) {
          // Forzar refresh del token
          await firebaseUser.getIdToken(true);
        }
      } catch (err) {
        console.error('Error checking email verification:', err);
      }
    };

    // Verificar cada 3 segundos
    const interval = setInterval(checkEmailVerification, 3000);
    return () => clearInterval(interval);
  }, [firebaseUser]);
  
  const [formData, setFormData] = useState<PerfilCompleto>({
    nombre: '',
    apellido: '',
    dni: '',
    fecha_nacimiento: '',
    genero: 'masculino',
    categoria_inicial: 'Principiante',
    mano_habil: 'derecha',
    posicion_preferida: 'indiferente',
    telefono: '',
    ciudad: ''
  });

  const handleCancel = async () => {
    // Confirmar antes de cancelar
    const confirmar = window.confirm(
      '¿Estás seguro que querés cancelar el registro?\n\n' +
      'Se perderán todos los datos ingresados y tendrás que volver a crear una cuenta.'
    );
    
    if (!confirmar) return;

    try {
      setLoading(true);
      // Hacer logout completo para limpiar Firebase y estado local
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Error al cancelar:', error);
      // Si falla el logout, al menos navegar al inicio
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await completeProfile(formData);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Error al completar el perfil');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-3 md:p-4 py-4 md:py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-3xl"
      >
        <Card>
          <div className="mb-4 md:mb-6">
            <h1 className="text-xl md:text-3xl font-black text-textPrimary mb-1 md:mb-2">
              Completá tu Perfil
            </h1>
            <p className="text-textSecondary text-sm md:text-base">
              Necesitamos algunos datos para crear tu cuenta
            </p>
            {firebaseUser && (
              <p className="text-primary text-xs md:text-sm mt-2">
                Registrado como: {firebaseUser.email}
              </p>
            )}
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 mb-4"
            >
              <p className="text-red-500 text-sm">{error}</p>
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 md:space-y-6">
            {/* Datos Personales */}
            <div>
              <h3 className="text-base md:text-lg font-bold text-textPrimary mb-3 md:mb-4 flex items-center gap-2">
                <User size={18} className="text-primary md:w-5 md:h-5" />
                Datos Personales
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                <div>
                  <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                    Nombre *
                  </label>
                  <Input
                    value={formData.nombre}
                    onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                    placeholder="Juan"
                    required
                    className="text-sm md:text-base"
                  />
                </div>
                <div>
                  <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                    Apellido *
                  </label>
                  <Input
                    value={formData.apellido}
                    onChange={(e) => setFormData({ ...formData, apellido: e.target.value })}
                    placeholder="Pérez"
                    required
                    className="text-sm md:text-base"
                  />
                </div>
                <div>
                  <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                    <div className="flex items-center gap-1.5 md:gap-2">
                      <Hash size={14} className="md:w-4 md:h-4" />
                      DNI *
                    </div>
                  </label>
                  <Input
                    value={formData.dni}
                    onChange={(e) => setFormData({ ...formData, dni: e.target.value })}
                    placeholder="12345678"
                    required
                    className="text-sm md:text-base"
                  />
                </div>
                <div>
                  <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                    <div className="flex items-center gap-1.5 md:gap-2">
                      <Calendar size={14} className="md:w-4 md:h-4" />
                      Fecha de Nacimiento *
                    </div>
                  </label>
                  <Input
                    type="date"
                    value={formData.fecha_nacimiento}
                    onChange={(e) => setFormData({ ...formData, fecha_nacimiento: e.target.value })}
                    required
                    className="text-sm md:text-base"
                  />
                </div>
              </div>
            </div>

            {/* Género */}
            <div>
              <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                Género *
              </label>
              <div className="grid grid-cols-2 gap-2 md:gap-3">
                {[
                  { value: 'masculino', label: 'Masculino', icon: '♂' },
                  { value: 'femenino', label: 'Femenino', icon: '♀' }
                ].map((gen) => (
                  <motion.button
                    key={gen.value}
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setFormData({ ...formData, genero: gen.value as any })}
                    className={`py-2.5 md:py-3 px-3 md:px-4 rounded-lg font-bold transition-all flex items-center justify-center gap-1.5 md:gap-2 text-sm md:text-base ${
                      formData.genero === gen.value
                        ? 'bg-gradient-to-r from-primary to-blue-600 text-white'
                        : 'bg-cardBorder text-textSecondary hover:text-textPrimary'
                    }`}
                  >
                    <span className="text-lg md:text-xl">{gen.icon}</span>
                    <span>{gen.label}</span>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Datos Deportivos */}
            <div>
              <h3 className="text-base md:text-lg font-bold text-textPrimary mb-3 md:mb-4 flex items-center gap-2">
                <Trophy size={18} className="text-accent md:w-5 md:h-5" />
                Datos Deportivos
              </h3>
              
              {/* Categoría Inicial */}
              <div className="mb-3 md:mb-4">
                <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                  Categoría Inicial *
                </label>
                <div className="grid grid-cols-3 md:grid-cols-6 gap-1.5 md:gap-2">
                  {getCategoriasNombres().map((cat) => (
                    <motion.button
                      key={cat}
                      type="button"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setFormData({ ...formData, categoria_inicial: cat })}
                      className={`py-1.5 md:py-2 px-2 md:px-3 rounded-lg font-bold transition-all text-sm md:text-base ${
                        formData.categoria_inicial === cat
                          ? 'bg-gradient-to-r from-accent to-yellow-500 text-white'
                          : 'bg-cardBorder text-textSecondary hover:text-textPrimary'
                      }`}
                    >
                      {cat}
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Mano Hábil y Posición */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                <div>
                  <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                    Mano Hábil
                  </label>
                  <select
                    value={formData.mano_habil}
                    onChange={(e) => setFormData({ ...formData, mano_habil: e.target.value as any })}
                    className="w-full bg-background border border-cardBorder rounded-lg px-3 md:px-4 py-2.5 md:py-3 text-textPrimary text-sm md:text-base focus:outline-none focus:border-primary transition-colors"
                  >
                    <option value="derecha">Derecha</option>
                    <option value="zurda">Zurda</option>
                  </select>
                </div>
                <div>
                  <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                    Posición Preferida
                  </label>
                  <select
                    value={formData.posicion_preferida}
                    onChange={(e) => setFormData({ ...formData, posicion_preferida: e.target.value as any })}
                    className="w-full bg-background border border-cardBorder rounded-lg px-3 md:px-4 py-2.5 md:py-3 text-textPrimary text-sm md:text-base focus:outline-none focus:border-primary transition-colors"
                  >
                    <option value="drive">Drive</option>
                    <option value="reves">Revés</option>
                    <option value="indiferente">Indiferente</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Datos Opcionales */}
            <div>
              <h3 className="text-base md:text-lg font-bold text-textPrimary mb-3 md:mb-4">
                Datos Opcionales
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                <div>
                  <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                    <div className="flex items-center gap-1.5 md:gap-2">
                      <Phone size={14} className="md:w-4 md:h-4" />
                      Teléfono
                    </div>
                  </label>
                  <Input
                    value={formData.telefono}
                    onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
                    placeholder="+54 9 11 1234-5678"
                    className="text-sm md:text-base"
                  />
                </div>
                <div>
                  <label className="block text-textSecondary text-xs md:text-sm font-medium mb-1.5 md:mb-2">
                    <div className="flex items-center gap-1.5 md:gap-2">
                      <MapPin size={14} className="md:w-4 md:h-4" />
                      Ciudad
                    </div>
                  </label>
                  <Input
                    value={formData.ciudad}
                    onChange={(e) => setFormData({ ...formData, ciudad: e.target.value })}
                    placeholder="Buenos Aires"
                    className="text-sm md:text-base"
                  />
                </div>
              </div>
            </div>

            {/* Botones */}
            <div className="flex flex-col md:flex-row gap-2 md:gap-3 pt-2 md:pt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={handleCancel}
                className="flex-1 text-sm md:text-base py-2.5 md:py-3"
                disabled={loading}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="accent"
                className="flex-1 text-sm md:text-base py-2.5 md:py-3"
                disabled={loading}
              >
                {loading ? 'Guardando...' : 'Completar Registro'}
              </Button>
            </div>
          </form>
        </Card>
      </motion.div>
    </div>
  );
}
