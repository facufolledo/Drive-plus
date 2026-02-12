import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, Trophy, BarChart3, X, Gamepad2, Target, Award, User, Shield, Search, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const { usuario } = useAuth();

  // Crear secciones dinámicamente basadas en permisos
  const menuSections = [
    {
      title: 'Mis Salas',
      items: [
        { icon: Gamepad2, label: 'Todas las Salas', path: '/salas' },
      ]
    },
    {
      title: 'Principal',
      items: [
        { icon: Home, label: 'Dashboard', path: '/dashboard' },
      ]
    },
    {
      title: 'Competición',
      items: [
        { icon: Trophy, label: 'Torneos', path: '/torneos' },
        { icon: Award, label: 'Mis Torneos', path: '/torneos/mis-torneos' },
      ]
    },
    {
      title: 'Rankings',
      items: [
        { icon: Target, label: 'Tabla General', path: '/rankings' },
        { icon: Zap, label: 'Ranking por Torneo', path: '/rankings/circuito' },
        { icon: BarChart3, label: 'Tops', path: '/rankings/categorias' },
        { icon: Search, label: 'Buscar Jugadores', path: '/jugadores' },
      ]
    },
    {
      title: 'Cuenta',
      items: [
        { icon: User, label: 'Mi Perfil', path: '/perfil' },
        // { icon: Settings, label: 'Configuración', path: '/configuracion' },
      ]
    },
    // Sección de administración solo para administradores
    ...(usuario?.es_administrador ? [{
      title: 'Administración',
      items: [
        { icon: Shield, label: 'Panel de Admin', path: '/admin' },
      ]
    }] : [])
  ];

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      <aside className="hidden lg:block lg:static lg:w-64 bg-cardBg/95 backdrop-blur-xl border-r border-cardBorder shadow-2xl">
        <nav className="p-4 space-y-6 sticky top-20">
          {menuSections.map((section, sectionIndex) => (
            <div key={section.title}>
              <motion.p 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: sectionIndex * 0.1 }}
                className="text-textSecondary text-xs font-bold uppercase tracking-wider mb-3 px-4"
              >
                {section.title}
              </motion.p>
              <div className="space-y-1">
                {section.items.map((item, index) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className="block"
                    >
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: (sectionIndex * 0.1) + (index * 0.05) }}
                        whileHover={{ x: 6 }}
                        whileTap={{ scale: 0.98 }}
                        className={`relative flex items-center gap-3 px-4 py-3 rounded-lg transition-all overflow-hidden ${
                          isActive
                            ? 'text-white'
                            : 'text-textSecondary hover:text-textPrimary hover:bg-cardBorder'
                        }`}
                      >
                        {isActive && (
                          <>
                            <motion.div
                              layoutId="activeTab"
                              className="absolute inset-0 bg-gradient-to-r from-primary to-blue-600"
                              transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            />
                            {/* Glow effect */}
                            <div className="absolute -inset-[1px] bg-gradient-to-r from-primary to-blue-600 blur-sm opacity-50 -z-10" />
                          </>
                        )}
                        <div className="relative z-10 flex items-center gap-3">
                          <Icon size={20} strokeWidth={2.5} />
                          <span className="font-bold">{item.label}</span>
                        </div>
                      </motion.div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      {/* Sidebar móvil */}
      <motion.aside
        initial={false}
        animate={{ x: isOpen ? 0 : -280 }}
        transition={{ type: 'tween', duration: 0.2, ease: 'easeOut' }}
        className="fixed top-16 left-0 bottom-0 w-64 bg-cardBg/95 backdrop-blur-xl border-r border-cardBorder shadow-2xl z-40 lg:hidden overflow-y-auto"
      >
        <div className="flex items-center justify-between p-4 relative z-10">
          <h2 className="text-lg font-bold text-textPrimary">Menú</h2>
          <motion.button 
            onClick={onClose} 
            whileHover={{ scale: 1.1, rotate: 90 }}
            whileTap={{ scale: 0.9 }}
            className="text-textSecondary hover:text-textPrimary"
          >
            <X size={24} />
          </motion.button>
        </div>

        <nav className="p-4 space-y-6 relative z-10">
          {menuSections.map((section, sectionIndex) => (
            <div key={section.title}>
              <motion.p 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: sectionIndex * 0.1 }}
                className="text-textSecondary text-xs font-bold uppercase tracking-wider mb-3 px-4"
              >
                {section.title}
              </motion.p>
              <div className="space-y-1">
                {section.items.map((item, index) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className="block"
                    >
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: (sectionIndex * 0.1) + (index * 0.05) }}
                        whileHover={{ x: 6 }}
                        whileTap={{ scale: 0.98 }}
                        className={`relative flex items-center gap-3 px-4 py-3 rounded-lg transition-all overflow-hidden ${
                          isActive
                            ? 'text-white'
                            : 'text-textSecondary hover:text-textPrimary hover:bg-cardBorder'
                        }`}
                      >
                        {isActive && (
                          <div className="absolute inset-0 bg-gradient-to-r from-primary to-blue-600" />
                        )}
                        <div className="relative z-10 flex items-center gap-3">
                          <Icon size={20} strokeWidth={2.5} />
                          <span className="font-bold">{item.label}</span>
                        </div>
                      </motion.div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </motion.aside>
    </>
  );
}
