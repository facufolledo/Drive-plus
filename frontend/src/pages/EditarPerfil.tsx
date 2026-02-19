import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Camera, Save, X, MapPin, User, Award, Pencil, Lock, Eye, EyeOff } from 'lucide-react';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { storage, auth as firebaseAuth } from '../config/firebase';
import { updatePassword, reauthenticateWithCredential, EmailAuthProvider } from 'firebase/auth';
import { useAuth } from '../context/AuthContext';
import Button from '../components/Button';
import Input from '../components/Input';
import axios from 'axios';
import { parseError } from '../utils/errorHandler';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function EditarPerfil() {
  const { usuario, updateProfile, reloadUser } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [loading, setLoading] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [error, setError] = useState('');
  const [photoPreview, setPhotoPreview] = useState<string | null>(
    usuario?.foto_perfil || null
  );

  // Estado para cambio de contraseña
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // Detectar si el usuario se registró con Google (no puede cambiar password)
  const isGoogleUser = firebaseAuth.currentUser?.providerData?.some(
    (p) => p.providerId === 'google.com'
  );

  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    ciudad: '',
    pais: 'Argentina',
    posicion_preferida: 'drive',
    mano_dominante: 'derecha',
    dni: '',
    fecha_nacimiento: '',
    telefono: '',
  });

  // Actualizar formData cuando cambie el usuario
  useEffect(() => {
    if (usuario) {
      console.log('🔍 Usuario cargado en EditarPerfil:', {
        posicion_preferida: usuario.posicion_preferida,
        mano_dominante: usuario.mano_dominante,
        usuario_completo: usuario
      });
      
      setFormData({
        nombre: usuario.nombre || '',
        apellido: usuario.apellido || '',
        ciudad: usuario.ciudad || '',
        pais: usuario.pais || 'Argentina',
        // Usar los valores del usuario, o valores por defecto si no existen
        posicion_preferida: usuario.posicion_preferida || 'drive',
        mano_dominante: usuario.mano_dominante || 'derecha',
        dni: usuario.dni || '',
        fecha_nacimiento: usuario.fecha_nacimiento || '',
        telefono: usuario.telefono || '',
      });
      setPhotoPreview(usuario.foto_perfil || null);
      
      console.log('✅ FormData actualizado:', {
        posicion_preferida: usuario.posicion_preferida || 'drive',
        mano_dominante: usuario.mano_dominante || 'derecha'
      });
    }
  }, [usuario]);

  const handlePhotoClick = () => {
    fileInputRef.current?.click();
  };

  // Comprimir imagen antes de subir
  const compressImage = (file: File, maxWidth = 800, quality = 0.8): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let { width, height } = img;
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) return reject(new Error('No canvas context'));
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => blob ? resolve(blob) : reject(new Error('Error al comprimir')),
          'image/jpeg',
          quality
        );
      };
      img.onerror = () => reject(new Error('Error al cargar imagen'));
      img.src = URL.createObjectURL(file);
    });
  };

  const handlePhotoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validar tamaño (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('La imagen no puede superar los 5MB');
      return;
    }

    // Validar tipo
    if (!file.type.startsWith('image/')) {
      setError('Solo se permiten imágenes');
      return;
    }

    try {
      setUploadingPhoto(true);
      setError('');

      // Comprimir imagen
      const compressedBlob = await compressImage(file);

      // Crear preview local
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result as string);
      };
      reader.readAsDataURL(compressedBlob);

      // Subir a Firebase Storage con timeout
      const storageRef = ref(storage, `profile-photos/${usuario?.id_usuario}_${Date.now()}`);
      
      const uploadPromise = uploadBytes(storageRef, compressedBlob);
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('TIMEOUT')), 30000)
      );

      await Promise.race([uploadPromise, timeoutPromise]);
      const photoURL = await getDownloadURL(storageRef);

      // Actualizar en el backend
      const token = localStorage.getItem('firebase_token');
      await axios.put(
        `${API_URL}/usuarios/perfil`,
        { foto_perfil: photoURL },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Actualizar contexto local
      updateProfile({ foto_perfil: photoURL });

    } catch (error: any) {
      console.error('Error al subir foto:', error);
      if (error?.message === 'TIMEOUT') {
        setError('La subida tardó demasiado. Verificá tu conexión o las reglas de Firebase Storage.');
      } else if (error?.code === 'storage/unauthorized') {
        setError('No tenés permisos para subir fotos. Contactá al administrador.');
      } else {
        setError(`Error al subir la foto: ${error?.message || 'Intenta nuevamente'}`);
      }
      setPhotoPreview(usuario?.foto_perfil || null);
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleChangePassword = async () => {
    setPasswordError('');
    setPasswordSuccess('');

    if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      setPasswordError('Completá todos los campos');
      return;
    }
    if (passwordData.newPassword.length < 6) {
      setPasswordError('La nueva contraseña debe tener al menos 6 caracteres');
      return;
    }
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('Las contraseñas no coinciden');
      return;
    }

    setPasswordLoading(true);
    try {
      const user = firebaseAuth.currentUser;
      if (!user || !user.email) throw new Error('No hay sesión activa');

      // Re-autenticar con contraseña actual
      const credential = EmailAuthProvider.credential(user.email, passwordData.currentPassword);
      await reauthenticateWithCredential(user, credential);

      // Cambiar contraseña
      await updatePassword(user, passwordData.newPassword);

      setPasswordSuccess('Contraseña actualizada correctamente');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err: any) {
      if (err.code === 'auth/wrong-password' || err.code === 'auth/invalid-credential') {
        setPasswordError('La contraseña actual es incorrecta');
      } else if (err.code === 'auth/weak-password') {
        setPasswordError('La contraseña es muy débil');
      } else {
        setPasswordError(err.message || 'Error al cambiar la contraseña');
      }
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const token = localStorage.getItem('firebase_token');
      
      if (!token) {
        setError('No se encontró token de autenticación. Por favor, inicia sesión nuevamente.');
        setLoading(false);
        return;
      }

      // Filtrar campos vacíos para no sobrescribir con valores vacíos
      const datosAEnviar = Object.fromEntries(
        Object.entries(formData).filter(([_, value]) => value !== '' && value !== null && value !== undefined)
      );
      
      console.log('📤 Enviando al backend:', datosAEnviar);
      
      const response = await axios.put(
        `${API_URL}/usuarios/perfil`,
        datosAEnviar,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      console.log('✅ Respuesta del backend:', response.data);
      
      // Recargar usuario desde el backend para asegurar datos frescos
      await reloadUser();
      
      console.log('✅ Usuario recargado, navegando a perfil...');

      navigate('/perfil');
    } catch (error: any) {
      console.error('Error al actualizar perfil:', error);
      const errorInfo = parseError(error);
      setError(errorInfo.message);
    } finally {
      setLoading(false);
    }
  };

  // Solo bloquear si la foto actual viene de Google (no solo por tener email de Gmail)
  const fotoDeGoogle = usuario?.foto_perfil?.includes('googleusercontent.com');

  return (
    <div className="min-h-screen p-4 md:p-6">
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-cardBg rounded-xl p-6 md:p-8 border border-cardBorder"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl md:text-3xl font-black text-textPrimary">
                Editar Perfil
              </h1>
              <p className="text-textSecondary text-sm mt-1">
                Personaliza tu información
              </p>
            </div>
            <button
              onClick={() => navigate('/perfil')}
              className="text-textSecondary hover:text-textPrimary transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Foto de perfil */}
            <div className="flex flex-col items-center mb-2">
              <button
                type="button"
                onClick={handlePhotoClick}
                disabled={uploadingPhoto}
                className="relative group cursor-pointer disabled:cursor-not-allowed"
              >
                <div className="w-32 h-32 rounded-full overflow-hidden bg-gradient-to-br from-primary to-secondary flex items-center justify-center ring-4 ring-cardBorder group-hover:ring-primary transition-all">
                  {photoPreview ? (
                    <img
                      src={photoPreview}
                      alt="Perfil"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-white text-4xl font-black">
                      {usuario?.nombre?.charAt(0)}{usuario?.apellido?.charAt(0)}
                    </span>
                  )}
                </div>

                {/* Overlay con ícono de editar al hacer hover */}
                <div className="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
                  <Pencil size={32} className="text-white" />
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoChange}
                  className="hidden"
                />
              </button>

              <p className="text-xs text-textSecondary mt-3 text-center">
                {uploadingPhoto ? (
                  <span className="text-primary animate-pulse">Subiendo foto...</span>
                ) : fotoDeGoogle ? (
                  'Haz clic para reemplazar tu foto de Google'
                ) : (
                  'Haz clic para cambiar tu foto'
                )}
              </p>
            </div>

            {/* Nombre y Apellido */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-textSecondary text-sm font-medium mb-2">
                  Nombre
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
                  <Input
                    type="text"
                    value={formData.nombre}
                    onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                    placeholder="Tu nombre"
                    required
                    className="pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-textSecondary text-sm font-medium mb-2">
                  Apellido
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
                  <Input
                    type="text"
                    value={formData.apellido}
                    onChange={(e) => setFormData({ ...formData, apellido: e.target.value })}
                    placeholder="Tu apellido"
                    required
                    className="pl-10"
                  />
                </div>
              </div>
            </div>

            {/* Ciudad y País */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-textSecondary text-sm font-medium mb-2">
                  Ciudad
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
                  <Input
                    type="text"
                    value={formData.ciudad}
                    onChange={(e) => setFormData({ ...formData, ciudad: e.target.value })}
                    placeholder="Tu ciudad"
                    className="pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-textSecondary text-sm font-medium mb-2">
                  País
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
                  <Input
                    type="text"
                    value={formData.pais}
                    onChange={(e) => setFormData({ ...formData, pais: e.target.value })}
                    placeholder="Tu país"
                    className="pl-10"
                  />
                </div>
              </div>
            </div>

            {/* Posición Preferida */}
            <div>
              <label className="block text-textSecondary text-sm font-medium mb-2">
                Posición Preferida
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, posicion_preferida: 'drive' })}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    formData.posicion_preferida === 'drive'
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-cardBorder bg-background text-textSecondary hover:border-primary/50'
                  }`}
                >
                  <Award size={24} className="mx-auto mb-2" />
                  <p className="font-bold">Drive</p>
                  <p className="text-xs mt-1">Lado derecho</p>
                </button>

                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, posicion_preferida: 'reves' })}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    formData.posicion_preferida === 'reves'
                      ? 'border-secondary bg-secondary/10 text-secondary'
                      : 'border-cardBorder bg-background text-textSecondary hover:border-secondary/50'
                  }`}
                >
                  <Award size={24} className="mx-auto mb-2" />
                  <p className="font-bold">Revés</p>
                  <p className="text-xs mt-1">Lado izquierdo</p>
                </button>
              </div>
            </div>

            {/* Mano Dominante */}
            <div>
              <label className="block text-textSecondary text-sm font-medium mb-2">
                Mano Dominante
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, mano_dominante: 'derecha' })}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    formData.mano_dominante === 'derecha'
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-cardBorder bg-background text-textSecondary hover:border-accent/50'
                  }`}
                >
                  <span className="text-3xl mb-2 block">👉</span>
                  <p className="font-bold">Derecha</p>
                </button>

                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, mano_dominante: 'zurda' })}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    formData.mano_dominante === 'zurda'
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-cardBorder bg-background text-textSecondary hover:border-accent/50'
                  }`}
                >
                  <span className="text-3xl mb-2 block">👈</span>
                  <p className="font-bold">Zurda</p>
                </button>
              </div>
            </div>

            {/* Información Adicional */}
            <div>
              <h3 className="text-lg font-bold text-textPrimary mb-4">Información Adicional (Opcional)</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-textSecondary text-sm font-medium mb-2">
                    DNI
                  </label>
                  <Input
                    type="text"
                    value={formData.dni || ''}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '');
                      if (value.length <= 8) {
                        setFormData({ ...formData, dni: value });
                      }
                    }}
                    placeholder="12345678"
                    maxLength={8}
                  />
                </div>

                <div>
                  <label className="block text-textSecondary text-sm font-medium mb-2">
                    Teléfono
                  </label>
                  <Input
                    type="tel"
                    value={formData.telefono || ''}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '');
                      if (value.length <= 15) {
                        setFormData({ ...formData, telefono: value });
                      }
                    }}
                    placeholder="3804565969"
                    maxLength={15}
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-textSecondary text-sm font-medium mb-2">
                    Fecha de Nacimiento
                  </label>
                  <Input
                    type="date"
                    value={formData.fecha_nacimiento || ''}
                    onChange={(e) => setFormData({ ...formData, fecha_nacimiento: e.target.value })}
                  />
                </div>
              </div>
            </div>

            {/* Cambiar Contraseña */}
            {!isGoogleUser && (
              <div>
                <h3 className="text-lg font-bold text-textPrimary mb-4">Cambiar Contraseña</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-textSecondary text-sm font-medium mb-2">
                      Contraseña Actual
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
                      <Input
                        type={showCurrentPassword ? 'text' : 'password'}
                        value={passwordData.currentPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                        placeholder="••••••••"
                        className="pl-10 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-textSecondary hover:text-textPrimary"
                      >
                        {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-textSecondary text-sm font-medium mb-2">
                      Nueva Contraseña
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
                      <Input
                        type={showNewPassword ? 'text' : 'password'}
                        value={passwordData.newPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                        placeholder="Mínimo 6 caracteres"
                        className="pl-10 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-textSecondary hover:text-textPrimary"
                      >
                        {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-textSecondary text-sm font-medium mb-2">
                      Confirmar Nueva Contraseña
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
                      <Input
                        type={showNewPassword ? 'text' : 'password'}
                        value={passwordData.confirmPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                        placeholder="Repetí la nueva contraseña"
                        className="pl-10"
                      />
                    </div>
                  </div>

                  {passwordError && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-red-500/10 border border-red-500/30 rounded-lg p-3"
                    >
                      <p className="text-red-500 text-sm">{passwordError}</p>
                    </motion.div>
                  )}

                  {passwordSuccess && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-green-500/10 border border-green-500/30 rounded-lg p-3"
                    >
                      <p className="text-green-500 text-sm">{passwordSuccess}</p>
                    </motion.div>
                  )}

                  <Button
                    type="button"
                    variant="ghost"
                    onClick={handleChangePassword}
                    disabled={passwordLoading || !passwordData.currentPassword || !passwordData.newPassword}
                    className="w-full"
                  >
                    {passwordLoading ? 'Cambiando...' : 'Cambiar Contraseña'}
                  </Button>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-500/10 border border-red-500/30 rounded-lg p-3"
              >
                <p className="text-red-500 text-sm">{error}</p>
              </motion.div>
            )}

            {/* Botones */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate('/perfil')}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2"
              >
                <Save size={18} />
                {loading ? 'Guardando...' : 'Guardar Cambios'}
              </Button>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
