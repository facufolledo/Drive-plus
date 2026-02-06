import { motion } from "framer-motion";
import { ArrowRight, Trophy, Users2, TrendingUp, Gamepad2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import CursorTrail from "../components/CursorTrail";
import { useAuth } from "../context/AuthContext";

export default function Landing() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: <Trophy className="w-6 h-6 md:w-9 md:h-9" />,
      title: "Torneos",
      description: "Organizá y gestioná torneos profesionales"
    },
    {
      icon: <Users2 className="w-6 h-6 md:w-9 md:h-9" />,
      title: "Jugadores",
      description: "Seguí el rendimiento de cada jugador"
    },
    {
      icon: <TrendingUp className="w-6 h-6 md:w-9 md:h-9" />,
      title: "Estadísticas",
      description: "Análisis detallado en tiempo real"
    },
    {
      icon: <Gamepad2 className="w-6 h-6 md:w-9 md:h-9" />,
      title: "Partidos",
      description: "Control completo de cada encuentro"
    }
  ];

  return (
    <div className="min-h-screen bg-[#0E0F11] text-white relative overflow-hidden">
      <CursorTrail />
      {/* Imagen de fondo de pádel */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `linear-gradient(rgba(14, 15, 17, 0.65), rgba(14, 15, 17, 0.75)), url('https://i.ibb.co/LD3mCF7g/padel.webp')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat"
        }}
      />

      {/* Overlay adicional para mejor contraste */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0E0F11]/30 to-[#0E0F11]/90" />

      {/* Navbar simple */}
      <nav className="relative z-20 backdrop-blur-md bg-[#0E0F11]/80 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <button 
            onClick={() => window.location.reload()}
            className="flex items-center hover:opacity-80 transition-opacity cursor-pointer"
          >
            <img 
              src={`${import.meta.env.BASE_URL}logo-drive.png`}
              alt="Drive+ Logo" 
              className="h-10 md:h-12 w-auto object-contain"
            />
          </button>
          {isAuthenticated ? (
            <motion.button
              onClick={() => navigate("/dashboard")}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative px-8 py-3 bg-gradient-to-r from-cyan-400 to-emerald-400 text-[#0E0F11] font-black text-sm uppercase tracking-wider overflow-hidden group"
              style={{
                clipPath: "polygon(10% 0%, 90% 0%, 100% 50%, 90% 100%, 10% 100%, 0% 50%)"
              }}
            >
              <span className="relative z-10">Ir al Dashboard</span>
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </motion.button>
          ) : (
            <motion.button
              onClick={() => navigate("/register")}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative px-8 py-3 bg-gradient-to-r from-cyan-400 to-emerald-400 text-[#0E0F11] font-black text-sm uppercase tracking-wider overflow-hidden group"
              style={{
                clipPath: "polygon(10% 0%, 90% 0%, 100% 50%, 90% 100%, 10% 100%, 0% 50%)"
              }}
            >
              <span className="relative z-10">Registrarse</span>
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </motion.button>
          )}
        </div>
      </nav>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-6 pt-16 pb-20">
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center max-w-5xl"
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-8"
          >
            <h1 className="text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-bold mb-4 md:mb-6 leading-tight text-white">
              Bienvenido a{" "}
              <span className="text-white">Drive</span><span className="text-primary">+</span>
            </h1>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-base sm:text-lg md:text-2xl lg:text-3xl text-[#9DA3AF] mb-8 md:mb-14 leading-relaxed"
          >
            Gestioná partidos, torneos y evaluá tus rendimientos
            <br />
            <span className="text-[#E8E9EB]">Todo en una plataforma profesional</span>
          </motion.p>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mb-20 flex justify-center"
          >
            <motion.button
              whileHover={{
                scale: 1.05,
                boxShadow: "0px 0px 25px rgba(0, 85, 255, 0.6)",
                y: -2,
              }}
              whileTap={{ scale: 0.98, y: 0 }}
              onClick={() => navigate("/login")}
              className="bg-gradient-to-r from-primary to-blue-600 text-white font-bold text-sm md:text-base lg:text-lg px-6 md:px-10 py-3 md:py-4 rounded-xl flex items-center gap-2 md:gap-3 transition-all shadow-lg shadow-primary/30"
            >
              Comenzar <ArrowRight size={24} />
            </motion.button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-8"
          >
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.5,
                  delay: 0.9 + index * 0.1,
                  type: "spring",
                  stiffness: 100
                }}
                whileHover={{
                  scale: 1.08,
                  y: -8,
                }}
                className="bg-[#0E0F11]/70 backdrop-blur-sm border border-white/10 hover:border-primary/50 rounded-lg md:rounded-xl p-4 md:p-8 text-center transition-all cursor-pointer group"
              >
                <motion.div
                  className="text-primary mb-2 md:mb-4 flex justify-center"
                  whileHover={{ rotate: [0, -10, 10, -10, 0], scale: 1.1 }}
                  transition={{ duration: 0.5 }}
                >
                  {feature.icon}
                </motion.div>
                <h3 className="text-[#E8E9EB] font-semibold text-sm md:text-lg mb-1 md:mb-2 group-hover:text-white transition-colors">
                  {feature.title}
                </h3>
                <p className="text-[#9DA3AF] text-xs md:text-base leading-tight md:leading-normal group-hover:text-[#B5BBC7] transition-colors">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 z-50 backdrop-blur-md bg-[#0E0F11]/80 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center">
          <p className="text-[#9DA3AF] text-sm">
            © 2025 Plataforma Drive<span className="text-primary">+</span> — Todos los derechos reservados
          </p>
        </div>
      </footer>
    </div>
  );
}
