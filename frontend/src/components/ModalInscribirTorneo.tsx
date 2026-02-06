import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Users, AlertCircle, Search, Loader2 } from 'lucide-react';
import Button from './Button';
import { useTorneos } from '../context/TorneosContext';
import { useAuth } from '../context/AuthContext';
import { torneoService, Categoria } from '../services/torneo.service';
import { useDebounce } from '../hooks/useDebounce';
import axios from 'axios';
import { parseError } from '../utils/errorHandler';
import ModalPagoInscripcion from './ModalPagoInscripcion';
import SelectorDisponibilidad from './SelectorDisponibilidad';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface FranjaHoraria {
  dias: string[];
  horaInicio: string;
  horaFin: string;
}

interface ModalInscribirTorneoProps {
  isOpen: boolean;
  onClose: () => void;
  torneoId: number;
  torneoNombre: string;
  esOrganizador?: boolean;
  fechaInicio?: string;
  fechaFin?: string;
}

export default function ModalInscribirTorneo({
  isOpen,
  onClose,
  torneoId,
  torneoNombre,
  esOrganizador = false,
  fechaInicio,
  fechaFin,
}: ModalInscribirTorneoProps) {
  const { loading } = useTorneos();
  const { usuario } = useAuth();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [codigoConfirmacion, setCodigoConfirmacion] = useState('');
  
  // Estados para pago
  const [mostrarModalPago, setMostrarModalPago] = useState(false);
  const [pagoInfo, setPagoInfo] = useState<any>(null);
  const [parejaId, setParejaId] = useState<number | null>(null);
  
  // Datos del torneo (si no se pasan como props)
  const [torneoData, setTorneoData] = useState<any>(null);
  
  // Disponibilidad horaria
  const [disponibilidadHoraria, setDisponibilidadHoraria] = useState<FranjaHoraria[]>([]);
  
  // Categorías del torneo
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState<number | null>(null);
  const [loadingCategorias, setLoadingCategorias] = useState(false);
  
  // Para búsqueda de jugador 1 (solo organizador)
  const [searchQuery1, setSearchQuery1] = useState('');
  const [searchResults1, setSearchResults1] = useState<any[]>([]);
  const [searching1, setSearching1] = useState(false);
  const [selectedJugador1, setSelectedJugador1] = useState<any>(null);
  
  // Para búsqueda de jugador 2
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedCompanero, setSelectedCompanero] = useState<any>(null);
  
  // Debounce para las búsquedas
  const debouncedSearchQuery1 = useDebounce(searchQuery1, 300);
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  
  const [formData, setFormData] = useState({
    jugador1_id: '',
    jugador2_id: '',
    nombre_pareja: '',
  });

  // Cargar categorías al abrir
  useEffect(() => {
    if (isOpen && torneoId) {
      cargarCategorias();
      // Si no tenemos las fechas, cargar datos del torneo
      if (!fechaInicio || !fechaFin) {
        cargarDatosTorneo();
      }
    }
  }, [isOpen, torneoId]);

  const cargarDatosTorneo = async () => {
    try {
      const response = await axios.get(`${API_URL}/torneos/${torneoId}`);
      setTorneoData(response.data);
    } catch (err) {
      console.error('Error cargando datos del torneo:', err);
    }
  };

  const cargarCategorias = async () => {
    if (!torneoId || isNaN(torneoId) || torneoId <= 0) {
      setLoadingCategorias(false);
      return;
    }
    
    try {
      setLoadingCategorias(true);
      const cats = await torneoService.listarCategorias(torneoId);
      setCategorias(cats);
      // Si solo hay una categoría, seleccionarla automáticamente
      if (cats.length === 1) {
        setCategoriaSeleccionada(cats[0].id);
      }
    } catch (err) {
      console.error('Error cargando categorías:', err);
    } finally {
      setLoadingCategorias(false);
    }
  };

  // Buscar usuarios para jugador 1 (solo organizador) con debounce
  useEffect(() => {
    if (!esOrganizador) return;
    
    if (debouncedSearchQuery1.length >= 2) {
      buscarUsuarios1(debouncedSearchQuery1);
    } else {
      setSearchResults1([]);
      setSearching1(false);
    }
  }, [debouncedSearchQuery1, esOrganizador, selectedCompanero]);

  // Mostrar indicador de búsqueda inmediatamente para jugador 1
  useEffect(() => {
    if (searchQuery1.length >= 2 && searchQuery1 !== debouncedSearchQuery1) {
      setSearching1(true);
    }
  }, [searchQuery1, debouncedSearchQuery1]);

  const buscarUsuarios1 = async (query: string) => {
    try {
      setSearching1(true);
      const response = await axios.get(`${API_URL}/usuarios/buscar`, {
        params: { q: query, limit: 5 }
      });
      
      // Filtrar para no mostrar al jugador 2 si ya está seleccionado
      const resultados = response.data.filter((u: any) => 
        u.id_usuario !== selectedCompanero?.id_usuario
      );
      setSearchResults1(resultados);
    } catch (err) {
      console.error('Error buscando usuarios:', err);
      setSearchResults1([]);
    } finally {
      setSearching1(false);
    }
  };

  // Buscar usuarios para jugador 2 con debounce
  useEffect(() => {
    if (debouncedSearchQuery.length >= 2) {
      buscarUsuarios(debouncedSearchQuery);
    } else {
      setSearchResults([]);
      setSearching(false);
    }
  }, [debouncedSearchQuery, usuario, esOrganizador, selectedJugador1]);

  // Mostrar indicador de búsqueda inmediatamente para jugador 2
  useEffect(() => {
    if (searchQuery.length >= 2 && searchQuery !== debouncedSearchQuery) {
      setSearching(true);
    }
  }, [searchQuery, debouncedSearchQuery]);

  const buscarUsuarios = async (query: string) => {
    try {
      setSearching(true);
      const response = await axios.get(`${API_URL}/usuarios/buscar`, {
        params: { q: query, limit: 5 }
      });
      
      // Filtrar para no mostrar al usuario actual ni al jugador 1 seleccionado
      const jugador1Id = esOrganizador ? selectedJugador1?.id_usuario : usuario?.id_usuario;
      const resultados = response.data.filter((u: any) => u.id_usuario !== jugador1Id);
      setSearchResults(resultados);
    } catch (err) {
      console.error('Error buscando usuarios:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!usuario) {
      setError('Debes iniciar sesión para inscribirte');
      return;
    }

    // Validaciones según si es organizador o no
    if (esOrganizador) {
      if (!selectedJugador1) {
        setError('Debes seleccionar el jugador 1');
        return;
      }
      if (!selectedCompanero) {
        setError('Debes seleccionar el jugador 2');
        return;
      }
    } else {
      if (!formData.jugador2_id) {
        setError('Debes seleccionar tu compañero');
        return;
      }
    }

    // Determinar jugadores
    const jugador1 = esOrganizador ? selectedJugador1 : usuario;
    const jugador2 = selectedCompanero;

    // Generar nombre de pareja automáticamente
    const nombrePareja = jugador2 
      ? `${jugador1.apellido || jugador1.nombre} / ${jugador2.apellido || jugador2.nombre}`
      : '';

    // Validar categoría si hay categorías disponibles
    if (categorias.length > 0 && !categoriaSeleccionada) {
      setError('Debes seleccionar una categoría');
      return;
    }

    try {
      console.log('🔍 DEBUG - INSCRIPCIÓN FRONTEND');
      console.log('Disponibilidad horaria:', disponibilidadHoraria);
      console.log('Longitud:', disponibilidadHoraria.length);
      console.log('Tipo:', typeof disponibilidadHoraria);
      console.log('Es array:', Array.isArray(disponibilidadHoraria));
      
      const dataToSend = {
        jugador1_id: jugador1.id_usuario,
        jugador2_id: jugador2.id_usuario,
        nombre_pareja: nombrePareja,
        categoria_id: categoriaSeleccionada || undefined,
        disponibilidad_horaria: disponibilidadHoraria.length > 0 ? disponibilidadHoraria : undefined,
      };
      
      console.log('📤 Datos a enviar:', dataToSend);
      console.log('📤 disponibilidad_horaria en data:', dataToSend.disponibilidad_horaria);
      
      const resultado = await torneoService.inscribirPareja(torneoId, dataToSend);
      
      console.log('✅ Resultado inscripción:', resultado);

      setCodigoConfirmacion(resultado.codigo_confirmacion);
      setParejaId(resultado.pareja_id);
      
      // Si requiere pago, mostrar modal de pago
      if (resultado.requiere_pago) {
        setPagoInfo({
          monto: resultado.monto_inscripcion,
          alias_cbu_cvu: resultado.alias_cbu_cvu,
          titular: resultado.titular_cuenta,
          banco: resultado.banco,
          telefono_contacto: resultado.telefono_contacto
        });
        setMostrarModalPago(true);
      } else {
        setSuccess(true);
      }
    } catch (err: any) {
      console.error('Error al inscribir:', err);
      const errorInfo = parseError(err);
      setError(errorInfo.message);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
      setError('');
      setSuccess(false);
      setFormData({ jugador1_id: '', jugador2_id: '', nombre_pareja: '' });
      setSelectedJugador1(null);
      setSelectedCompanero(null);
      setSearchQuery('');
      setSearchQuery1('');
      setCategoriaSeleccionada(null);
    }
  };

  const handleSubirComprobante = async (file: File) => {
    if (!parejaId) return;
    
    // Por ahora solo cerramos el modal, la subida real se implementará después
    console.log('Subiendo comprobante para pareja:', parejaId, file);
    setSuccess(true);
    setMostrarModalPago(false);
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleClose}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            />

            {/* Modal */}
            <div className="fixed inset-0 flex items-center justify-center z-50 p-2 sm:p-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-cardBg rounded-lg sm:rounded-xl border border-cardBorder w-full max-w-md max-h-[95vh] sm:max-h-[90vh] overflow-y-auto"
            >
              {success ? (
                <div className="p-4 sm:p-6 text-center">
                  <div className="w-12 h-12 sm:w-16 sm:h-16 bg-yellow-500/20 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
                    <Users size={24} className="text-yellow-500 sm:w-8 sm:h-8" />
                  </div>
                  <h3 className="text-base sm:text-xl font-bold text-textPrimary mb-1 sm:mb-2">
                    ¡Invitación Enviada!
                  </h3>
                  <p className="text-textSecondary text-xs sm:text-sm mb-4">
                    Tu compañero debe confirmar la inscripción
                  </p>
                  
                  {/* Código de confirmación */}
                  <div className="bg-accent/10 border-2 border-accent/30 rounded-xl p-4 mb-4">
                    <p className="text-xs text-textSecondary mb-2">Código de confirmación:</p>
                    <p className="text-3xl font-black text-accent tracking-widest">{codigoConfirmacion}</p>
                  </div>
                  
                  <p className="text-xs text-textSecondary mb-4">
                    Comparte este código con tu compañero para que confirme.<br/>
                    También le enviamos una notificación.
                  </p>
                  
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      onClick={() => {
                        navigator.clipboard.writeText(codigoConfirmacion);
                      }}
                      className="flex-1 text-xs"
                    >
                      Copiar código
                    </Button>
                    <Button
                      variant="accent"
                      onClick={handleClose}
                      className="flex-1 text-xs"
                    >
                      Entendido
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Header */}
                  <div className="flex items-center justify-between p-3 sm:p-6 border-b border-cardBorder">
                    <div className="flex-1 min-w-0 pr-2">
                      <h2 className="text-base sm:text-xl font-bold text-textPrimary">
                        Inscribirse al Torneo
                      </h2>
                      <p className="text-xs sm:text-sm text-textSecondary mt-0.5 sm:mt-1 truncate">
                        {torneoNombre}
                      </p>
                    </div>
                    <button
                      onClick={handleClose}
                      disabled={loading}
                      className="text-textSecondary hover:text-textPrimary transition-colors disabled:opacity-50 flex-shrink-0"
                    >
                      <X size={20} className="sm:w-6 sm:h-6" />
                    </button>
                  </div>

                  {/* Form */}
                  <form onSubmit={handleSubmit} className="p-3 sm:p-6 space-y-3 sm:space-y-4">
                    {/* Selector de Categoría */}
                    {categorias.length > 0 && (
                      <div>
                        <label className="block text-xs sm:text-sm font-bold text-textSecondary mb-1.5 sm:mb-2">
                          Categoría *
                        </label>
                        {loadingCategorias ? (
                          <div className="h-10 bg-cardBorder animate-pulse rounded-lg"></div>
                        ) : (
                          <div className="grid grid-cols-2 gap-2">
                            {categorias.map((cat) => (
                              <button
                                key={cat.id}
                                type="button"
                                onClick={() => setCategoriaSeleccionada(cat.id)}
                                className={`p-2 rounded-lg border text-left transition-all ${
                                  categoriaSeleccionada === cat.id
                                    ? 'border-primary bg-primary/10'
                                    : 'border-cardBorder hover:border-primary/50'
                                }`}
                              >
                                <span className="font-bold text-textPrimary text-sm">{cat.nombre}</span>
                                <span className={`ml-1 text-xs ${
                                  cat.genero === 'masculino' ? 'text-blue-400' :
                                  cat.genero === 'femenino' ? 'text-pink-400' : 'text-purple-400'
                                }`}>
                                  ({cat.genero.charAt(0).toUpperCase()})
                                </span>
                                <p className="text-xs text-textSecondary">
                                  {cat.parejas_inscritas} parejas inscritas
                                </p>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Jugador 1 - Si es organizador puede elegir, si no es el usuario actual */}
                    {esOrganizador ? (
                      <div>
                        <label className="block text-xs sm:text-sm font-bold text-textSecondary mb-1.5 sm:mb-2">
                          Jugador 1 *
                        </label>
                        
                        {selectedJugador1 ? (
                          <div className="bg-primary/10 rounded-lg p-2 sm:p-4 flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="font-bold text-textPrimary text-sm sm:text-base truncate">
                                {selectedJugador1.nombre} {selectedJugador1.apellido}
                              </p>
                              <p className="text-[10px] sm:text-xs text-textSecondary">
                                Rating: {selectedJugador1.rating || 1200}
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedJugador1(null);
                                setFormData({ ...formData, jugador1_id: '' });
                              }}
                              className="text-textSecondary hover:text-red-500 transition-colors flex-shrink-0 ml-2"
                            >
                              <X size={16} className="sm:w-5 sm:h-5" />
                            </button>
                          </div>
                        ) : (
                          <div className="relative">
                            <div className="relative">
                              <Search size={14} className="absolute left-2 sm:left-3 top-1/2 -translate-y-1/2 text-textSecondary sm:w-[18px] sm:h-[18px]" />
                              <input
                                type="text"
                                value={searchQuery1}
                                onChange={(e) => setSearchQuery1(e.target.value)}
                                placeholder="Busca por nombre o apellido..."
                                disabled={loading}
                                className="w-full pl-8 sm:pl-10 pr-3 sm:pr-4 py-2 sm:py-3 bg-background border border-cardBorder rounded-lg text-sm sm:text-base text-textPrimary placeholder-textSecondary focus:outline-none focus:border-primary transition-colors disabled:opacity-50"
                              />
                            </div>
                            
                            {/* Resultados de búsqueda jugador 1 */}
                            {searchQuery1.length >= 2 && (
                              <div className="absolute z-10 w-full mt-1 sm:mt-2 bg-card border border-cardBorder rounded-lg shadow-lg max-h-48 sm:max-h-60 overflow-y-auto">
                                {searching1 ? (
                                  <div className="p-3 sm:p-4 text-center text-textSecondary text-xs sm:text-sm">
                                    Buscando...
                                  </div>
                                ) : searchResults1.length > 0 ? (
                                  searchResults1.map((user) => (
                                    <button
                                      key={user.id_usuario}
                                      type="button"
                                      onClick={() => {
                                        setSelectedJugador1(user);
                                        setFormData({ ...formData, jugador1_id: user.id_usuario.toString() });
                                        setSearchQuery1('');
                                        setSearchResults1([]);
                                      }}
                                      className="w-full p-2 sm:p-3 text-left hover:bg-background transition-colors border-b border-cardBorder last:border-b-0"
                                    >
                                      <p className="font-bold text-textPrimary text-sm sm:text-base truncate">
                                        {user.nombre} {user.apellido}
                                      </p>
                                      <p className="text-[10px] sm:text-xs text-textSecondary">
                                        Rating: {user.rating || 1200}
                                      </p>
                                    </button>
                                  ))
                                ) : (
                                  <div className="p-3 sm:p-4 text-center text-textSecondary text-xs sm:text-sm">
                                    No se encontraron usuarios
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      /* Info del usuario actual (no organizador) */
                      <div className="bg-primary/10 rounded-lg p-2 sm:p-4">
                        <p className="text-[10px] sm:text-xs text-textSecondary mb-0.5 sm:mb-1">Jugador 1 (Tú)</p>
                        <p className="font-bold text-textPrimary text-sm sm:text-base">
                          {usuario?.nombre} {usuario?.apellido}
                        </p>
                        <p className="text-[10px] sm:text-xs text-textSecondary">
                          Rating: {usuario?.rating || 1200}
                        </p>
                      </div>
                    )}

                    {/* Buscar compañero (Jugador 2) */}
                    <div>
                      <label className="block text-xs sm:text-sm font-bold text-textSecondary mb-1.5 sm:mb-2">
                        {esOrganizador ? 'Jugador 2 *' : 'Buscar Compañero *'}
                      </label>
                      
                      {selectedCompanero ? (
                        <div className="bg-primary/10 rounded-lg p-2 sm:p-4 flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="font-bold text-textPrimary text-sm sm:text-base truncate">
                              {selectedCompanero.nombre} {selectedCompanero.apellido}
                            </p>
                            <p className="text-[10px] sm:text-xs text-textSecondary">
                              Rating: {selectedCompanero.rating || 1200}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedCompanero(null);
                              setFormData({ ...formData, jugador2_id: '' });
                            }}
                            className="text-textSecondary hover:text-red-500 transition-colors flex-shrink-0 ml-2"
                          >
                            <X size={16} className="sm:w-5 sm:h-5" />
                          </button>
                        </div>
                      ) : (
                        <div className="relative">
                          <div className="relative">
                            <Search size={14} className="absolute left-2 sm:left-3 top-1/2 -translate-y-1/2 text-textSecondary sm:w-[18px] sm:h-[18px]" />
                            <input
                              type="text"
                              value={searchQuery}
                              onChange={(e) => setSearchQuery(e.target.value)}
                              placeholder="Busca por nombre o apellido..."
                              disabled={loading}
                              className="w-full pl-8 sm:pl-10 pr-3 sm:pr-4 py-2 sm:py-3 bg-background border border-cardBorder rounded-lg text-sm sm:text-base text-textPrimary placeholder-textSecondary focus:outline-none focus:border-primary transition-colors disabled:opacity-50"
                            />
                          </div>
                          
                          {/* Resultados de búsqueda */}
                          {searchQuery.length >= 2 && (
                            <div className="absolute z-10 w-full mt-1 sm:mt-2 bg-card border border-cardBorder rounded-lg shadow-lg max-h-48 sm:max-h-60 overflow-y-auto">
                              {searching ? (
                                <div className="p-3 sm:p-4 text-center text-textSecondary text-xs sm:text-sm">
                                  Buscando...
                                </div>
                              ) : searchResults.length > 0 ? (
                                searchResults.map((user) => (
                                  <button
                                    key={user.id_usuario}
                                    type="button"
                                    onClick={() => {
                                      setSelectedCompanero(user);
                                      setFormData({ ...formData, jugador2_id: user.id_usuario.toString() });
                                      setSearchQuery('');
                                      setSearchResults([]);
                                    }}
                                    className="w-full p-2 sm:p-3 text-left hover:bg-background transition-colors border-b border-cardBorder last:border-b-0"
                                  >
                                    <p className="font-bold text-textPrimary text-sm sm:text-base truncate">
                                      {user.nombre} {user.apellido}
                                    </p>
                                    <p className="text-[10px] sm:text-xs text-textSecondary">
                                      Rating: {user.rating || 1200} • ID: {user.id_usuario}
                                    </p>
                                  </button>
                                ))
                              ) : (
                                <div className="p-3 sm:p-4 text-center text-textSecondary text-xs sm:text-sm">
                                  No se encontraron usuarios
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                      
                      <p className="text-[10px] sm:text-xs text-textSecondary mt-1">
                        {selectedCompanero 
                          ? 'Compañero seleccionado' 
                          : 'Escribe al menos 2 caracteres para buscar'}
                      </p>
                    </div>

                    {/* Nombre de la pareja - generado automáticamente */}
                    {selectedCompanero && (esOrganizador ? selectedJugador1 : usuario) && (
                      <div className="bg-accent/10 rounded-lg p-2 sm:p-4">
                        <p className="text-[10px] sm:text-xs text-textSecondary mb-0.5 sm:mb-1">Nombre de la Pareja</p>
                        <p className="font-bold text-textPrimary text-sm sm:text-base">
                          {esOrganizador 
                            ? `${selectedJugador1?.apellido || selectedJugador1?.nombre} / ${selectedCompanero.apellido || selectedCompanero.nombre}`
                            : `${usuario?.apellido} / ${selectedCompanero.apellido}`
                          }
                        </p>
                      </div>
                    )}

                    {/* Selector de disponibilidad horaria */}
                    {selectedCompanero && (esOrganizador ? selectedJugador1 : usuario) && (
                      <div className="bg-cardHover rounded-lg p-3 sm:p-4">
                        <SelectorDisponibilidad
                          value={disponibilidadHoraria}
                          onChange={setDisponibilidadHoraria}
                          fechaInicio={fechaInicio || torneoData?.fecha_inicio || ''}
                          fechaFin={fechaFin || torneoData?.fecha_fin || ''}
                          horariosDisponibles={torneoData?.horarios_disponibles}
                        />
                      </div>
                    )}

                    {/* Error */}
                    {error && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-start gap-1.5 sm:gap-2 p-2 sm:p-3 bg-red-500/10 border border-red-500/30 rounded-lg"
                      >
                        <AlertCircle size={14} className="text-red-500 flex-shrink-0 mt-0.5 sm:w-[18px] sm:h-[18px]" />
                        <p className="text-xs sm:text-sm text-red-500">{error}</p>
                      </motion.div>
                    )}

                    {/* Botones */}
                    <div className="flex gap-2 sm:gap-3 pt-2 sm:pt-4">
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={handleClose}
                        disabled={loading}
                        className="flex-1 text-xs sm:text-sm py-2 sm:py-2.5"
                      >
                        Cancelar
                      </Button>
                      <Button
                        type="submit"
                        variant="accent"
                        disabled={loading}
                        className="flex-1 text-xs sm:text-sm py-2 sm:py-2.5 flex items-center justify-center gap-2"
                      >
                        {loading ? (
                          <>
                            <Loader2 size={14} className="animate-spin" />
                            Inscribiendo...
                          </>
                        ) : (
                          'Inscribir Pareja'
                        )}
                      </Button>
                    </div>
                  </form>
                </>
              )}
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
    
    {/* Modal de pago */}
    {pagoInfo && (
      <ModalPagoInscripcion
        isOpen={mostrarModalPago}
        onClose={() => {
          setMostrarModalPago(false);
          setSuccess(true);
        }}
        pagoInfo={pagoInfo}
      />
    )}
  </>
  );
}
