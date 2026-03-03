import { useState, useEffect } from 'react';
import { Users, Check, X, Clock, Trophy } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from './Button';
import torneoService from '../services/torneo.service';

interface Invitacion {
  pareja_id: number;
  torneo_id: number;
  torneo_nombre: string;
  companero_id: number;
  companero_nombre: string;
  fecha_expiracion: string;
  codigo: string;
}

export default function InvitacionesPendientes() {
  const navigate = useNavigate();
  const [invitaciones, setInvitaciones] = useState<Invitacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [procesando, setProcesando] = useState<number | null>(null);

  useEffect(() => {
    cargarInvitaciones();
  }, []);

  const cargarInvitaciones = async () => {
    try {
      setLoading(true);
      const data = await torneoService.obtenerMisInvitaciones();
      setInvitaciones(data.invitaciones || []);
    } catch (err) {
      console.error('Error cargando invitaciones:', err);
      setInvitaciones([]);
    } finally {
      setLoading(false);
    }
  };

  const confirmarInvitacion = async (codigo: string) => {
    try {
      setProcesando(invitaciones.find(i => i.codigo === codigo)?.pareja_id || null);
      await torneoService.confirmarParejaPorCodigo(codigo);
      await cargarInvitaciones();
    } catch (err: any) {
      console.error('Error confirmando:', err);
    } finally {
      setProcesando(null);
    }
  };

  const rechazarInvitacion = async (parejaId: number) => {
    try {
      setProcesando(parejaId);
      await torneoService.rechazarInvitacion(parejaId);
      await cargarInvitaciones();
    } catch (err) {
      console.error('Error rechazando:', err);
    } finally {
      setProcesando(null);
    }
  };

  const calcularTiempoRestante = (fechaExpiracion: string) => {
    const ahora = new Date();
    const expira = new Date(fechaExpiracion);
    const diff = expira.getTime() - ahora.getTime();
    
    if (diff <= 0) return 'Expirado';
    
    const horas = Math.floor(diff / (1000 * 60 * 60));
    const minutos = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (horas > 24) {
      return `${Math.floor(horas / 24)}d ${horas % 24}h`;
    }
    return `${horas}h ${minutos}m`;
  };

  if (loading) {
    return (
      <div className="text-center py-4">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full mx-auto animate-spin" />
      </div>
    );
  }

  if (invitaciones.length === 0) {
    return (
      <div className="text-center py-6">
        <div className="mb-3 opacity-50">
          <Trophy size={32} className="mx-auto text-textSecondary" />
        </div>
        <p className="text-sm text-textSecondary mb-3">📭 Sin invitaciones</p>
        <button 
          onClick={() => navigate('/torneos')}
          className="px-4 py-2 rounded-lg bg-accent/20 hover:bg-accent/30 text-accent text-sm font-bold transition-all hover:scale-105 border border-accent/30"
        >
          Explorá torneos disponibles →
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {invitaciones.map((inv) => (
        <div
          key={inv.pareja_id}
          className="bg-background rounded-lg p-3 border border-cardBorder"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="font-bold text-textPrimary text-sm truncate">
                {inv.torneo_nombre}
              </p>
              <p className="text-xs text-textSecondary">
                Compañero: <span className="text-primary">{inv.companero_nombre}</span>
              </p>
              <div className="flex items-center gap-1 mt-1 text-xs text-yellow-500">
                <Clock size={12} />
                <span>Expira en {calcularTiempoRestante(inv.fecha_expiracion)}</span>
              </div>
            </div>
            
            <div className="flex gap-2 flex-shrink-0">
              <button
                onClick={() => rechazarInvitacion(inv.pareja_id)}
                disabled={procesando === inv.pareja_id}
                className="p-2 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors disabled:opacity-50"
                title="Rechazar"
              >
                <X size={16} />
              </button>
              <button
                onClick={() => confirmarInvitacion(inv.codigo)}
                disabled={procesando === inv.pareja_id}
                className="p-2 rounded-lg bg-green-500/10 text-green-500 hover:bg-green-500/20 transition-colors disabled:opacity-50"
                title="Aceptar"
              >
                <Check size={16} />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
