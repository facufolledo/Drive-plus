import { useAuth } from '../context/AuthContext';

interface AdminBadgeProps {
  id: number | string;
  label?: string;
  className?: string;
}

/**
 * Badge que muestra IDs solo para administradores
 * Útil para debugging y gestión rápida de la base de datos
 */
export function AdminBadge({ id, label = 'ID', className = '' }: AdminBadgeProps) {
  const { usuario } = useAuth();

  // Solo mostrar si es administrador
  if (!usuario?.es_administrador) {
    return null;
  }

  return (
    <span 
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-gray-700/50 text-gray-300 border border-gray-600/50 ${className}`}
      title={`${label}: ${id}`}
    >
      {label}:{id}
    </span>
  );
}

interface AdminIdProps {
  id: number | string;
  prefix?: string;
}

/**
 * Versión inline del ID para administradores (más compacta)
 */
export function AdminId({ id, prefix = '#' }: AdminIdProps) {
  const { usuario } = useAuth();

  if (!usuario?.es_administrador) {
    return null;
  }

  return (
    <span className="text-[9px] font-mono text-gray-400 ml-1">
      {prefix}{id}
    </span>
  );
}
