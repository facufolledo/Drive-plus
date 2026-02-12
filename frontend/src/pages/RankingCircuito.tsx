import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Medal, Filter, Search, Plus, Trash2, Loader2, ArrowLeft, Image, ChevronRight, Upload } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import { useAuth } from '../context/AuthContext';
import { useDebounce } from '../hooks/useDebounce';
import circuitoService, { Circuito, RankingCircuitoItem, CircuitoInfo } from '../services/circuito.service';
import { storage } from '../config/firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';

const CATEGORIAS_FILTRO = ['Todas', 'Principiante', '8va', '7ma', '6ta', '5ta', '4ta', 'Libre'];

// Colores de gradiente para las cards
const CARD_GRADIENTS = [
  'from-blue-600 to-indigo-800',
  'from-purple-600 to-violet-800',
  'from-emerald-600 to-teal-800',
  'from-orange-500 to-red-700',
  'from-pink-500 to-rose-700',
  'from-cyan-500 to-blue-700',
  'from-amber-500 to-orange-700',
  'from-fuchsia-500 to-purple-700',
];

export default function RankingCircuito() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { codigo: codigoRuta } = useParams<{ codigo: string }>();
  
  // useAuth puede no estar disponible si la ruta es pública (fuera de AuthProvider)
  let usuario: any = null;
  try {
    const auth = useAuth();
    usuario = auth?.usuario;
  } catch {
    // Ruta pública, sin auth
  }

  // El código puede venir de la URL (/circuito/zf) o del query param (?c=zf)
  const codigoParam = codigoRuta || searchParams.get('c');
  // Si venimos de /circuito/:codigo, es modo público (sin grid de circuitos)
  const isPublicRoute = !!codigoRuta;

  const [circuitos, setCircuitos] = useState<Circuito[]>([]);
  const [circuitoInfo, setCircuitoInfo] = useState<CircuitoInfo | null>(null);
  const [ranking, setRanking] = useState<RankingCircuitoItem[]>([]);
  const [filtroCategoria, setFiltroCategoria] = useState('Todas');
  const [busqueda, setBusqueda] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [loadingRanking, setLoadingRanking] = useState(false);

  // Modal crear circuito
  const [showCrear, setShowCrear] = useState(false);
  const [nuevoCircuito, setNuevoCircuito] = useState({ codigo: '', nombre: '', descripcion: '', logo_url: '' });
  const [creando, setCreando] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const logoInputRef = useRef<HTMLInputElement>(null);
  const editLogoInputRef = useRef<HTMLInputElement>(null);
  const [editingCircuitoId, setEditingCircuitoId] = useState<number | null>(null);

  const debouncedBusqueda = useDebounce(busqueda, 300);

  useEffect(() => { if (!isPublicRoute) cargarCircuitos(); }, []);

  useEffect(() => {
    if (codigoParam) {
      cargarRanking(codigoParam);
      cargarInfoCircuito(codigoParam);
    }
  }, [codigoParam, filtroCategoria]);

  const cargarCircuitos = async () => {
    try {
      setIsLoading(true);
      const data = await circuitoService.listarCircuitos(true);
      setCircuitos(data);
    } catch (err) {
      console.error('Error cargando circuitos:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const cargarRanking = async (codigo: string) => {
    try {
      setLoadingRanking(true);
      const cat = filtroCategoria === 'Todas' ? undefined : filtroCategoria;
      const data = await circuitoService.obtenerRanking(codigo, cat);
      setRanking(data);
    } catch (err) {
      console.error('Error cargando ranking:', err);
      setRanking([]);
    } finally {
      setLoadingRanking(false);
    }
  };

  const cargarInfoCircuito = async (codigo: string) => {
    try {
      const data = await circuitoService.obtenerInfo(codigo);
      setCircuitoInfo(data);
    } catch (err) {
      console.error('Error cargando info:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCrearCircuito = async () => {
    if (!nuevoCircuito.codigo || !nuevoCircuito.nombre) return;
    try {
      setCreando(true);
      await circuitoService.crearCircuito({
        codigo: nuevoCircuito.codigo,
        nombre: nuevoCircuito.nombre,
        descripcion: nuevoCircuito.descripcion || undefined,
        logo_url: nuevoCircuito.logo_url || undefined,
      });
      setShowCrear(false);
      setNuevoCircuito({ codigo: '', nombre: '', descripcion: '', logo_url: '' });
      setLogoPreview(null);
      await cargarCircuitos();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al crear circuito');
    } finally {
      setCreando(false);
    }
  };

  const handleEliminarCircuito = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm('¿Eliminar este circuito?')) return;
    try {
      await circuitoService.eliminarCircuito(id);
      await cargarCircuitos();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al eliminar');
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { alert('La imagen no puede superar 5MB'); return; }
    if (!file.type.startsWith('image/')) { alert('Solo se permiten imágenes'); return; }
    try {
      setUploadingLogo(true);
      const reader = new FileReader();
      reader.onloadend = () => setLogoPreview(reader.result as string);
      reader.readAsDataURL(file);
      const storageRef = ref(storage, `circuitos/${nuevoCircuito.codigo || 'temp'}_${Date.now()}`);
      await uploadBytes(storageRef, file);
      const url = await getDownloadURL(storageRef);
      setNuevoCircuito(prev => ({ ...prev, logo_url: url }));
    } catch (err) {
      console.error('Error subiendo logo:', err);
      alert('Error al subir la imagen');
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleEditLogoClick = (e: React.MouseEvent, circuitoId: number) => {
    e.stopPropagation();
    setEditingCircuitoId(circuitoId);
    editLogoInputRef.current?.click();
  };

  const handleEditLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !editingCircuitoId) return;
    if (file.size > 5 * 1024 * 1024) { alert('La imagen no puede superar 5MB'); return; }
    if (!file.type.startsWith('image/')) { alert('Solo se permiten imágenes'); return; }
    try {
      setUploadingLogo(true);
      const storageRef = ref(storage, `circuitos/${editingCircuitoId}_${Date.now()}`);
      await uploadBytes(storageRef, file);
      const url = await getDownloadURL(storageRef);
      await circuitoService.actualizarCircuito(editingCircuitoId, { logo_url: url });
      await cargarCircuitos();
      // Si estamos viendo el ranking de este circuito, recargar info
      if (codigoParam) await cargarInfoCircuito(codigoParam);
    } catch (err) {
      console.error('Error subiendo logo:', err);
      alert('Error al subir la imagen');
    } finally {
      setUploadingLogo(false);
      setEditingCircuitoId(null);
      if (editLogoInputRef.current) editLogoInputRef.current.value = '';
    }
  };

  const verRanking = (codigo: string) => {
    setSearchParams({ c: codigo });
  };

  const volverAGrid = () => {
    setSearchParams({});
    setCircuitoInfo(null);
    setRanking([]);
    setFiltroCategoria('Todas');
    setBusqueda('');
  };

  // Filtrar ranking por búsqueda
  const rankingFiltrado = ranking.filter(j => {
    if (!debouncedBusqueda) return true;
    const nombre = `${j.nombre || ''} ${j.apellido || ''}`.toLowerCase();
    return nombre.includes(debouncedBusqueda.toLowerCase()) ||
           (j.nombre_usuario || '').toLowerCase().includes(debouncedBusqueda.toLowerCase());
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  // ========== VISTA RANKING DE UN CIRCUITO ==========
  if (codigoParam) {
    return (
      <div className="space-y-6">
        {/* Input oculto para editar logo */}
        <input type="file" ref={editLogoInputRef} accept="image/*" onChange={handleEditLogoUpload} className="hidden" />
        
        {/* Header con botón volver */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          {!isPublicRoute && (
            <button onClick={volverAGrid} className="flex items-center gap-1.5 text-textSecondary hover:text-primary transition-colors mb-3 text-sm">
              <ArrowLeft size={16} /> Volver a circuitos
            </button>
          )}

          {/* Banner del circuito */}
          {circuitoInfo && (
            <div className={`relative rounded-xl overflow-hidden bg-gradient-to-r ${CARD_GRADIENTS[Math.abs(codigoParam.charCodeAt(0)) % CARD_GRADIENTS.length]}`}>
              {circuitoInfo.logo_url && (
                <div className="absolute inset-0">
                  <img src={circuitoInfo.logo_url} alt="" className="w-full h-full object-cover opacity-20" />
                </div>
              )}
              {/* Admin: botón editar imagen del banner */}
              {usuario?.es_administrador && (
                <button
                  onClick={() => { setEditingCircuitoId(circuitoInfo.id); editLogoInputRef.current?.click(); }}
                  className="absolute top-3 right-3 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white rounded-lg px-2.5 py-1.5 text-xs font-bold flex items-center gap-1.5 transition-colors z-10"
                >
                  {uploadingLogo && editingCircuitoId === circuitoInfo.id ? <Loader2 size={12} className="animate-spin" /> : <Image size={12} />}
                  {circuitoInfo.logo_url ? 'Cambiar imagen' : 'Agregar imagen'}
                </button>
              )}
              <div className="relative p-4 md:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-2xl md:text-4xl font-black text-white">{circuitoInfo.nombre}</h1>
                    {circuitoInfo.descripcion && (
                      <p className="text-white/70 text-sm mt-1">{circuitoInfo.descripcion}</p>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <div className="bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2 text-center">
                      <p className="text-white font-black text-xl">{circuitoInfo.torneos?.length || 0}</p>
                      <p className="text-white/60 text-[10px]">Torneos</p>
                    </div>
                    <div className="bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2 text-center">
                      <p className="text-white font-black text-xl">{ranking.length}</p>
                      <p className="text-white/60 text-[10px]">Jugadores</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </motion.div>

        {/* Filtros */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-2 md:left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={16} />
            <Input type="text" placeholder="Buscar jugador..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} className="pl-8 md:pl-10 text-sm" />
          </div>
          <div className="flex items-center gap-1.5 md:gap-2 flex-wrap">
            <div className="flex items-center gap-1 text-textSecondary">
              <Filter size={14} />
              <span className="text-xs md:text-sm font-bold">Categoría:</span>
            </div>
            {CATEGORIAS_FILTRO.map(cat => (
              <Button key={cat} variant={filtroCategoria === cat ? 'primary' : 'secondary'} onClick={() => setFiltroCategoria(cat)} className="text-[10px] md:text-sm px-2 md:px-3 py-1 md:py-1.5">
                {cat}
              </Button>
            ))}
          </div>
        </div>

        {/* Tabla ranking */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg md:text-2xl font-bold text-textPrimary flex items-center gap-2">
              <Trophy className="text-accent w-5 h-5 md:w-7 md:h-7" />
              Ranking
            </h2>
          </div>

          {/* Desktop */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-cardBorder">
                  <th className="text-left py-3 px-4 text-textSecondary text-sm font-bold uppercase tracking-wider">Pos</th>
                  <th className="text-left py-3 px-4 text-textSecondary text-sm font-bold uppercase tracking-wider">Jugador</th>
                  <th className="text-center py-3 px-4 text-textSecondary text-sm font-bold uppercase tracking-wider">Puntos</th>
                  <th className="text-center py-3 px-4 text-textSecondary text-sm font-bold uppercase tracking-wider">Categoría</th>
                  <th className="text-center py-3 px-4 text-textSecondary text-sm font-bold uppercase tracking-wider">Partidos</th>
                  <th className="text-center py-3 px-4 text-textSecondary text-sm font-bold uppercase tracking-wider">Victorias</th>
                  <th className="text-center py-3 px-4 text-textSecondary text-sm font-bold uppercase tracking-wider">% Win</th>
                </tr>
              </thead>
              <tbody>
                {loadingRanking ? (
                  <tr><td colSpan={7} className="py-8 text-center text-textSecondary">Cargando ranking...</td></tr>
                ) : rankingFiltrado.length === 0 ? (
                  <tr><td colSpan={7} className="py-8 text-center text-textSecondary">No hay jugadores en este circuito</td></tr>
                ) : (
                  rankingFiltrado.map((j, index) => {
                    const nombreCompleto = `${j.nombre || ''} ${j.apellido || ''}`.trim() || j.nombre_usuario || 'Sin nombre';
                    return (
                      <motion.tr key={`${j.id_usuario}-${j.categoria}`} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.02 }} className="border-b border-cardBorder hover:bg-cardBorder/50 transition-colors">
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            {index === 0 && <Medal className="text-accent" size={16} />}
                            {index === 1 && <Medal className="text-gray-400" size={16} />}
                            {index === 2 && <Medal className="text-orange-400" size={16} />}
                            <span className="text-textPrimary font-bold text-lg">#{j.posicion}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <button onClick={() => {
                            if (isPublicRoute) {
                              navigate('/login');
                            } else {
                              j.nombre_usuario ? navigate(`/jugador/${j.nombre_usuario}`) : navigate(`/perfil/${j.id_usuario}`);
                            }
                          }} className="text-left hover:opacity-80 cursor-pointer">
                            <p className="text-textPrimary font-bold text-base hover:text-primary transition-colors">{nombreCompleto}</p>
                            <p className="text-textSecondary text-xs">@{j.nombre_usuario || 'sin-usuario'}</p>
                          </button>
                        </td>
                        <td className="py-4 px-4 text-center"><span className="text-2xl font-black text-accent">{j.puntos}</span></td>
                        <td className="py-4 px-4 text-center">
                          <span className="inline-block px-3 py-1 rounded-full text-white font-bold text-sm bg-gradient-to-r from-blue-500 to-blue-600">{j.categoria || '-'}</span>
                        </td>
                        <td className="py-4 px-4 text-center text-textPrimary font-semibold">{j.partidos_jugados}</td>
                        <td className="py-4 px-4 text-center text-secondary font-semibold">{j.partidos_ganados}</td>
                        <td className="py-4 px-4 text-center text-textPrimary font-semibold">{j.winrate}%</td>
                      </motion.tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Mobile */}
          <div className="md:hidden space-y-2">
            {loadingRanking ? (
              <div className="py-8 text-center text-textSecondary text-sm">
                <Loader2 className="animate-spin inline-block mb-2" size={20} />
                <p>Cargando ranking...</p>
              </div>
            ) : rankingFiltrado.length === 0 ? (
              <div className="py-8 text-center text-textSecondary text-sm">No hay jugadores en este circuito</div>
            ) : (
              rankingFiltrado.map((j, index) => {
                const nombreCompleto = `${j.nombre || ''} ${j.apellido || ''}`.trim() || j.nombre_usuario || 'Sin nombre';
                return (
                  <motion.div key={`${j.id_usuario}-${j.categoria}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.04 }}
                    onClick={() => {
                      if (isPublicRoute) {
                        navigate('/login');
                      } else {
                        j.nombre_usuario ? navigate(`/jugador/${j.nombre_usuario}`) : navigate(`/perfil/${j.id_usuario}`);
                      }
                    }}
                    className="bg-cardBg/50 rounded-lg p-2 border border-cardBorder hover:border-primary/30 transition-colors cursor-pointer">
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {index === 0 && <Medal className="text-accent" size={14} />}
                        {index === 1 && <Medal className="text-gray-400" size={14} />}
                        {index === 2 && <Medal className="text-orange-400" size={14} />}
                        <span className="text-textPrimary font-bold text-sm">#{j.posicion}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-textPrimary font-bold text-xs truncate">{nombreCompleto}</p>
                        <p className="text-textSecondary text-[9px] truncate">@{j.nombre_usuario}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-xl font-black text-accent">{j.puntos}</p>
                        <span className="inline-block px-1.5 py-0.5 rounded-full text-white font-bold text-[8px] bg-gradient-to-r from-blue-500 to-blue-600">{j.categoria || '-'}</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-[9px] pt-1.5 border-t border-cardBorder/50">
                      <div className="text-center"><p className="text-textSecondary">Partidos</p><p className="text-textPrimary font-bold text-xs">{j.partidos_jugados}</p></div>
                      <div className="text-center"><p className="text-textSecondary">Victorias</p><p className="text-secondary font-bold text-xs">{j.partidos_ganados}</p></div>
                      <div className="text-center"><p className="text-textSecondary">% Win</p><p className="text-accent font-bold text-xs">{j.winrate}%</p></div>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>
        </Card>
      </div>
    );
  }

  // ========== VISTA GRID DE CIRCUITOS ==========
  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="h-0.5 md:h-1 w-8 md:w-12 bg-gradient-to-r from-accent to-secondary rounded-full" />
              <h1 className="text-2xl md:text-5xl font-black text-textPrimary tracking-tight">Rankings por Torneo</h1>
            </div>
            <p className="text-textSecondary text-xs md:text-base ml-10 md:ml-15">Seleccioná un circuito para ver el ranking completo</p>
          </div>
          {usuario?.es_administrador && (
            <Button variant="primary" onClick={() => setShowCrear(true)} className="text-xs md:text-sm px-3 md:px-4 py-2">
              <Plus size={16} className="mr-1" /> Nuevo Circuito
            </Button>
          )}
        </div>
      </motion.div>

      {/* Input oculto para editar logo de circuito existente */}
      <input type="file" ref={editLogoInputRef} accept="image/*" onChange={handleEditLogoUpload} className="hidden" />

      {/* Grid de circuitos */}
      {circuitos.length === 0 ? (
        <Card>
          <div className="py-12 text-center">
            <Trophy className="mx-auto text-textSecondary mb-3" size={48} />
            <p className="text-textSecondary text-sm">No hay circuitos creados todavía</p>
            {usuario?.es_administrador && (
              <Button variant="primary" onClick={() => setShowCrear(true)} className="mt-4 text-sm">
                <Plus size={14} className="mr-1" /> Crear primer circuito
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {circuitos.map((c, index) => {
            const gradient = CARD_GRADIENTS[index % CARD_GRADIENTS.length];
            return (
              <motion.div
                key={c.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -4, scale: 1.02 }}
                className="group cursor-pointer"
                onClick={() => verRanking(c.codigo)}
              >
                <div className="bg-cardBg rounded-xl border border-cardBorder overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:border-primary/30">
                  {/* Header con gradiente o imagen */}
                  <div className={`relative h-32 md:h-36 bg-gradient-to-br ${gradient}`}>
                    {c.logo_url && (
                      <img src={c.logo_url} alt={c.nombre} className="absolute inset-0 w-full h-full object-cover opacity-30 group-hover:opacity-40 transition-opacity" />
                    )}
                    <div className="absolute inset-0 p-4 flex flex-col justify-end">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-xl md:text-2xl font-black text-white drop-shadow-lg">{c.nombre}</h3>
                          {c.descripcion && (
                            <p className="text-white/70 text-xs mt-0.5 line-clamp-2">{c.descripcion}</p>
                          )}
                        </div>
                        <Trophy className="text-white/40 flex-shrink-0" size={24} />
                      </div>
                    </div>
                    {/* Admin buttons */}
                    {usuario?.es_administrador && (
                      <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => handleEditLogoClick(e, c.id)}
                          className="bg-primary/80 hover:bg-primary text-white rounded-full p-1.5"
                        >
                          {uploadingLogo && editingCircuitoId === c.id ? <Loader2 size={12} className="animate-spin" /> : <Image size={12} />}
                        </button>
                        <button
                          onClick={(e) => handleEliminarCircuito(e, c.id)}
                          className="bg-red-500/80 hover:bg-red-500 text-white rounded-full p-1.5"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Stats */}
                  <div className="p-4 space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2 text-textSecondary">
                        <Trophy size={14} />
                        <span>Torneos</span>
                      </div>
                      <span className="text-textPrimary font-bold">{c.torneos_count}</span>
                    </div>

                    {/* Botón ver ranking */}
                    <button className="w-full py-2.5 px-4 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 group-hover:bg-primary group-hover:text-white">
                      Ver Ranking Completo <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Modal crear circuito */}
      <AnimatePresence>
        {showCrear && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={() => setShowCrear(false)} />
            <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
              <motion.div initial={{ opacity: 0, scale: 0.9, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="bg-cardBg rounded-xl border border-cardBorder shadow-2xl w-full max-w-md p-4 space-y-3">
                <h3 className="text-lg font-bold text-textPrimary">Nuevo Circuito</h3>
                <div>
                  <label className="block text-textSecondary text-xs font-bold mb-1">Código (corto, sin espacios)</label>
                  <Input value={nuevoCircuito.codigo} onChange={(e) => setNuevoCircuito({ ...nuevoCircuito, codigo: e.target.value.toLowerCase().replace(/\s/g, '') })} placeholder="Ej: zf" />
                </div>
                <div>
                  <label className="block text-textSecondary text-xs font-bold mb-1">Nombre</label>
                  <Input value={nuevoCircuito.nombre} onChange={(e) => setNuevoCircuito({ ...nuevoCircuito, nombre: e.target.value })} placeholder="Ej: Zona Fitness" />
                </div>
                <div>
                  <label className="block text-textSecondary text-xs font-bold mb-1">Descripción (opcional)</label>
                  <textarea value={nuevoCircuito.descripcion} onChange={(e) => setNuevoCircuito({ ...nuevoCircuito, descripcion: e.target.value })} placeholder="Descripción del circuito..."
                    className="w-full bg-background border border-cardBorder rounded-lg px-2 py-1.5 text-xs text-textPrimary placeholder-textSecondary focus:outline-none focus:border-primary resize-none" rows={2} />
                </div>
                <div>
                  <label className="block text-textSecondary text-xs font-bold mb-1">
                    <Image size={12} className="inline mr-1" />Imagen del circuito (opcional)
                  </label>
                  <input type="file" ref={logoInputRef} accept="image/*" onChange={handleLogoUpload} className="hidden" />
                  {logoPreview || nuevoCircuito.logo_url ? (
                    <div className="relative rounded-lg overflow-hidden h-28 mb-2">
                      <img src={logoPreview || nuevoCircuito.logo_url} alt="Preview" className="w-full h-full object-cover" />
                      <button type="button" onClick={() => { setLogoPreview(null); setNuevoCircuito(prev => ({ ...prev, logo_url: '' })); }} className="absolute top-1 right-1 bg-red-500/80 text-white rounded-full p-1 hover:bg-red-500">
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ) : null}
                  <button type="button" onClick={() => logoInputRef.current?.click()} disabled={uploadingLogo}
                    className="w-full py-2 px-3 border border-dashed border-cardBorder rounded-lg text-xs text-textSecondary hover:border-primary hover:text-primary transition-colors flex items-center justify-center gap-2">
                    {uploadingLogo ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
                    {uploadingLogo ? 'Subiendo...' : 'Subir imagen'}
                  </button>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button variant="secondary" onClick={() => setShowCrear(false)} className="flex-1">Cancelar</Button>
                  <Button variant="primary" onClick={handleCrearCircuito} disabled={creando || !nuevoCircuito.codigo || !nuevoCircuito.nombre} className="flex-1">
                    {creando ? <Loader2 size={14} className="animate-spin mr-1" /> : null}
                    Crear
                  </Button>
                </div>
              </motion.div>
            </div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
