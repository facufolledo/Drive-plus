import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import Button from '../components/Button';
import Input from '../components/Input';
import CursorTrail from '../components/CursorTrail';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const navigate = useNavigate();
  const { register, loginWithGoogle, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'El email es requerido';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida';
    } else if (formData.password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      await register('', formData.email, formData.password);
      // Mostrar mensaje de verificación de email
      setEmailSent(true);
    } catch (err: any) {
      setErrors({ general: err.message || 'Error al registrar usuario' });
    }
  };

  const handleGoogleRegister = async () => {
    try {
      await loginWithGoogle();
      // El AuthContext ya maneja la redirección a completar-perfil
      navigate('/completar-perfil');
    } catch (err: any) {
      const errorMessage = err.message || 'Error al registrar con Google';
      // Si el error indica que ya existe, agregar información adicional
      if (errorMessage.includes('ya existe') || errorMessage.includes('already exists')) {
        setErrors({ general: 'Esta cuenta de Google ya está registrada. Serás redirigido al inicio de sesión.' });
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setErrors({ general: errorMessage });
      }
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 relative overflow-hidden">
      <CursorTrail />
      {/* Fondo de pádel */}
      <div className="fixed inset-0 pointer-events-none">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-30"
          style={{
            backgroundImage: 'url(https://i.ibb.co/wN0RJcvS/padel2.webp)',
          }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10 px-4"
      >
        {/* Logo y título */}
        <div className="text-center mb-6 md:mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200 }}
            className="inline-flex flex-col items-center justify-center mb-3 md:mb-4"
          >
            <img 
              src={`${import.meta.env.BASE_URL}logo-drive.png`}
              alt="Drive+ Logo" 
              className="h-24 md:h-32 w-auto object-contain"
            />
          </motion.div>
          <p className="text-textSecondary text-center text-sm md:text-base">Únete a la comunidad</p>
        </div>

        {/* Formulario */}
        <div className="bg-cardBg rounded-xl md:rounded-2xl p-5 md:p-8 border border-cardBorder shadow-2xl">
          <h2 className="text-xl md:text-2xl font-bold text-textPrimary mb-4 md:mb-6">Crear Cuenta</h2>

          {emailSent ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-8"
            >
              <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mail className="text-primary" size={32} />
              </div>
              <h3 className="text-xl font-bold text-textPrimary mb-2">
                ¡Verifica tu email!
              </h3>
              <p className="text-textSecondary mb-4">
                Te enviamos un correo a <span className="text-primary font-bold">{formData.email}</span>
              </p>
              <p className="text-textSecondary text-sm mb-6">
                Haz clic en el enlace del correo para verificar tu cuenta y luego inicia sesión.
              </p>
              <Button
                variant="primary"
                onClick={() => navigate('/login')}
                className="w-full"
              >
                Ir a Iniciar Sesión
              </Button>
            </motion.div>
          ) : (
            <>
              {errors.general && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mb-4"
                >
                  <p className="text-red-500 text-sm font-semibold mb-2">{errors.general}</p>
                  {errors.general.includes('ya está registrado') && (
                    <Link 
                      to="/login" 
                      className="text-primary hover:text-blue-400 text-sm font-bold underline inline-block"
                    >
                      Ir a Iniciar Sesión →
                    </Link>
                  )}
                </motion.div>
              )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-textSecondary text-sm font-medium mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={20} />
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="tu@email.com"
                  className="pl-10"
                />
              </div>
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
            </div>

            <div>
              <label className="block text-textSecondary text-sm font-medium mb-2">
                Contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={20} />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="••••••••"
                  className="pl-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-textSecondary hover:text-textPrimary transition-colors"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password}</p>}
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Creando cuenta...' : 'Crear Cuenta'}
            </Button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-cardBorder"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-cardBg text-textSecondary">O continúa con</span>
            </div>
          </div>

          <motion.button
            type="button"
            onClick={handleGoogleRegister}
            disabled={isLoading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full bg-white hover:bg-gray-50 text-gray-900 font-bold py-3 px-4 rounded-lg border-2 border-gray-300 transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            {isLoading ? 'Registrando...' : 'Continuar con Google'}
          </motion.button>

              <div className="mt-6 text-center space-y-3">
                <p className="text-textSecondary text-sm">
                  ¿Ya tienes cuenta?{' '}
                  <Link to="/login" className="text-primary hover:text-blue-400 font-bold transition-colors">
                    Inicia sesión
                  </Link>
                </p>
                <button
                  onClick={() => navigate('/')}
                  className="text-textSecondary hover:text-textPrimary text-sm transition-colors"
                >
                  ← Volver al inicio
                </button>
              </div>
            </>
          )}
        </div>

      </motion.div>
    </div>
  );
}
