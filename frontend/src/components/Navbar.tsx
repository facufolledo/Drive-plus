import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, LogOut, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface NavbarProps {
  onMenuClick: () => void;
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);
  const [categorias, setCategorias] = useState<any[]>([]);

  useEffect(() => {
    if (usuario) {
      cargarCategorias();
    }
  }, [usuario]);

  const cargarCategorias = async () => {
    try {
      const categoriasData = await apiService.getCategorias();
      setCategorias(categoriasData);
    } catch (error) {
      console.error('Error al cargar categorías:', error);
    }
  };

  const obtenerNombreCategoria = () => {
    // Si el backend ya devuelve el nombre de la categoría, usarlo directamente
    if (usuario?.categoria) return usuario.categoria;
    
    // Si no, buscar por id_categoria
    if (!usuario?.id_categoria || !categorias.length) return null;
    const categoria = categorias.find(cat => cat.id_categoria === usuario.id_categoria);
    return categoria?.nombre || null;
  };

  const getInitials = (nombre: string) => {
    return nombre
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
      className="fixed top-0 left-0 right-0 h-16 bg-cardBg/95 backdrop-blur-xl border-b border-cardBorder z-30 px-4 lg:px-6"
    >
      <div className="flex items-center justify-between h-full relative z-10">
        <div className="flex items-center gap-4">
          <motion.button
            onClick={onMenuClick}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="lg:hidden text-textPrimary hover:text-primary transition-colors"
          >
            <Menu size={24} />
          </motion.button>
          <motion.button 
            onClick={() => window.location.reload()}
            className="flex items-center hover:opacity-80 transition-opacity cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <img 
              src={`${import.meta.env.BASE_URL}logo-drive.png`}
              alt="Drive+ Logo" 
              className="h-14 w-auto object-contain"
            />
          </motion.button>
        </div>

        <div className="flex items-center gap-4">
          {/* Nombre del usuario en desktop */}
          <div className="hidden md:block text-right">
            <p className="text-textPrimary text-sm font-bold">
              {usuario?.nombre} {usuario?.apellido}
            </p>
            <p className="text-textSecondary text-xs">{usuario?.email}</p>
          </div>

          {/* Avatar con menú */}
          <div className="relative">
            <motion.button
              onClick={() => setShowMenu(!showMenu)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative group cursor-pointer"
            >
              <div className="absolute inset-0 bg-primary blur-md opacity-0 group-hover:opacity-50 transition-opacity duration-300 rounded-full" />
              <div className="relative h-10 w-10 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center text-white font-black shadow-lg">
                {usuario && `${usuario.nombre[0]}${usuario.apellido[0]}`.toUpperCase()}
              </div>
            </motion.button>

            {/* Menú desplegable */}
            <AnimatePresence>
              {showMenu && (
                <>
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-40"
                    onClick={() => setShowMenu(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, y: -10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -10, scale: 0.95 }}
                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    className="absolute right-0 top-full mt-2 w-64 bg-cardBg border border-cardBorder rounded-xl shadow-2xl overflow-hidden z-50"
                  >
                    {/* Info del usuario */}
                    <div className="p-4 border-b border-cardBorder">
                      <p className="text-textPrimary font-bold">
                        {usuario?.nombre} {usuario?.apellido}
                      </p>
                      <p className="text-textSecondary text-sm">@{usuario?.nombre_usuario}</p>
                      <p className="text-textSecondary text-xs mt-1">{usuario?.email}</p>
                      <div className="mt-2 flex gap-2 flex-wrap">
                        <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full font-bold">
                          Rating: {usuario?.rating}
                        </span>
                        {obtenerNombreCategoria() && (
                          <span className="text-xs bg-secondary/10 text-secondary px-2 py-1 rounded-full font-bold">
                            {obtenerNombreCategoria()}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Estadísticas rápidas */}
                    <div className="p-4 border-b border-cardBorder">
                      <div className="grid grid-cols-2 gap-2 text-center">
                        <div>
                          <p className="text-2xl font-bold text-textPrimary">{usuario?.partidos_jugados || 0}</p>
                          <p className="text-xs text-textSecondary">Partidos</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-secondary">{usuario?.rating || 0}</p>
                          <p className="text-xs text-textSecondary">Rating</p>
                          {obtenerNombreCategoria() && (
                            <p className="text-[10px] text-primary font-semibold mt-0.5">
                              {obtenerNombreCategoria()}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Opciones */}
                    <div className="p-2">
                      <button
                        onClick={() => {
                          navigate('/perfil');
                          setShowMenu(false);
                        }}
                        className="w-full flex items-center gap-3 px-4 py-3 text-textSecondary hover:text-textPrimary hover:bg-cardBorder rounded-lg transition-colors"
                      >
                        <User size={18} />
                        <span className="font-medium">Mi Perfil</span>
                      </button>
                      <button
                        onClick={() => {
                          logout();
                          setShowMenu(false);
                          navigate('/');
                        }}
                        className="w-full flex items-center gap-3 px-4 py-3 text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                      >
                        <LogOut size={18} />
                        <span className="font-medium">Cerrar Sesión</span>
                      </button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.nav>
  );
}
