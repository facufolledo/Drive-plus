import { ReactNode, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import CursorTrail from './CursorTrail';
import PWAInstallPrompt from './PWAInstallPrompt';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <CursorTrail />
      
      {/* Imagen de fondo: más blur y blackout para que el contenido sea protagonista */}
      <div className="fixed inset-0 z-0">
        <div
          className="absolute inset-0 backdrop-blur-md"
          style={{
            backgroundImage: `linear-gradient(rgba(15, 18, 28, 0.94), rgba(15, 18, 28, 0.97)), url('https://i.ibb.co/wN0RJcvS/padel2.webp')`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
            backgroundAttachment: "fixed"
          }}
        />
      </div>

      <Navbar onMenuClick={() => setSidebarOpen(true)} />

      <div className="flex pt-16 relative z-10 min-h-screen">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <main className="flex-1 min-w-0 px-4 py-4 md:px-6 md:py-5 lg:px-8 lg:py-6 w-full overflow-x-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, x: -20, scale: 0.98 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 20, scale: 0.98 }}
              transition={{ 
                type: 'tween',
                ease: 'anticipate',
                duration: 0.3
              }}
              className="w-full max-w-[1600px] mx-auto"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* PWA Install Prompt */}
      <PWAInstallPrompt />
    </div>
  );
}
