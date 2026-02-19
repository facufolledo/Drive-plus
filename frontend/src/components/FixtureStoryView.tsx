import { useEffect, useRef, useState } from 'react';
import { X, Download } from 'lucide-react';

interface Partido {
  id_partido: number;
  pareja1_nombre: string;
  pareja2_nombre: string;
  fecha_hora_inicio?: string;
  fecha_hora_fin?: string;
  fecha_hora?: string;
  cancha_nombre?: string;
  cancha_id?: number;
  zona_id?: number;
  estado: string;
}

interface Zona {
  id: string;
  nombre: string;
  partidos: Partido[];
}

interface FixtureStoryViewProps {
  isOpen: boolean;
  onClose: () => void;
  torneoNombre: string;
  categoriaNombre: string;
  zonasConPartidos: Zona[];
  canchas: any[];
  parseFechaLocal: (fecha: string) => Date;
}

// Colores
const BG = '#0a0a1a';
const ZONA_BG = '#1a1a3a';
const ROW_EVEN = '#111128';
const ROW_ODD = '#151535';
const BORDER = '#2a2a5a';
const TEXT_WHITE = '#ffffff';
const TEXT_MUTED = '#7777aa';
const ACCENT_BLUE = '#5b9cf5';
const ACCENT_PURPLE = '#a855f7';

export default function FixtureStoryView({
  isOpen,
  onClose,
  torneoNombre,
  categoriaNombre,
  zonasConPartidos,
  canchas,
  parseFechaLocal,
}: FixtureStoryViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [descargando, setDescargando] = useState(false);
  const [logoImg, setLogoImg] = useState<HTMLImageElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => setLogoImg(img);
    img.onerror = () => setLogoImg(null);
    img.src = '/logo-drive.png';
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !canvasRef.current) return;
    dibujarCanvas();
  }, [isOpen, logoImg, zonasConPartidos]);

  const getNombreCancha = (canchaId: number | null | undefined) => {
    if (!canchaId) return '';
    const cancha = canchas.find((c: any) => c.id === canchaId);
    return cancha?.nombre || `Cancha ${canchaId}`;
  };

  const formatHora = (fechaStr?: string) => {
    if (!fechaStr) return '--:--';
    const fecha = parseFechaLocal(fechaStr);
    return fecha.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  const formatDia = (fechaStr?: string) => {
    if (!fechaStr) return '';
    const fecha = parseFechaLocal(fechaStr);
    return fecha.toLocaleDateString('es-AR', { weekday: 'short', day: 'numeric', month: 'short' }).toUpperCase();
  };

  const dibujarCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const W = 1080;
    const PAD = 50;
    const INNER = W - PAD * 2;

    // Calcular altura con escalado dinámico
    const totalPartidos = zonasConPartidos.reduce((s, z) => s + z.partidos.length, 0);
    const totalZonas = zonasConPartidos.length;

    // Escalar si hay muchos partidos para que entre en 1920
    const TARGET_H = 1920;
    const BASE_ROW_H = 88;
    const BASE_ZONA_HEAD_H = 52;
    const BASE_COL_HEAD_H = 32;
    const BASE_ZONA_GAP = 28;
    const BASE_HEADER_H = 380;
    const BASE_FOOTER_H = 70;
    const BASE_FONT = 20;

    const baseContentH = totalZonas * (BASE_ZONA_HEAD_H + BASE_COL_HEAD_H + BASE_ZONA_GAP) + totalPartidos * BASE_ROW_H;
    const baseTotal = BASE_HEADER_H + baseContentH + BASE_FOOTER_H + 40;

    // Si excede 1920, escalar todo proporcionalmente
    const scale = baseTotal > TARGET_H ? TARGET_H / baseTotal : 1;
    const ROW_H = Math.round(BASE_ROW_H * scale);
    const ZONA_HEAD_H = Math.round(BASE_ZONA_HEAD_H * scale);
    const COL_HEAD_H = Math.round(BASE_COL_HEAD_H * scale);
    const ZONA_GAP = Math.round(BASE_ZONA_GAP * scale);
    const HEADER_H = Math.round(BASE_HEADER_H * scale);
    const FOOTER_H = Math.round(BASE_FOOTER_H * scale);
    const fontSize = Math.max(14, Math.round(BASE_FONT * scale));
    const fontSizeSmall = Math.max(11, Math.round(13 * scale));
    const fontSizeHora = Math.max(16, Math.round(24 * scale));
    const fontSizeTorneo = Math.max(20, Math.round(30 * scale));
    const fontSizeCat = Math.max(30, Math.round(52 * scale));
    const fontSizeZona = Math.max(16, Math.round(24 * scale));

    const contentH = totalZonas * (ZONA_HEAD_H + COL_HEAD_H + ZONA_GAP) + totalPartidos * ROW_H;
    const H = Math.max(TARGET_H, HEADER_H + contentH + FOOTER_H + 40);

    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d')!;

    // Fondo degradado
    const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
    bgGrad.addColorStop(0, BG);
    bgGrad.addColorStop(0.4, '#0e0e24');
    bgGrad.addColorStop(1, BG);
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, W, H);

    let y = Math.round(55 * scale);

    // === LOGO ===
    if (logoImg) {
      const logoH = Math.round(90 * scale);
      const aspect = logoImg.width / logoImg.height;
      const logoW = logoH * aspect;
      const logoX = (W - logoW) / 2;
      ctx.shadowColor = '#6366f1';
      ctx.shadowBlur = 25;
      ctx.drawImage(logoImg, logoX, y, logoW, logoH);
      ctx.shadowBlur = 0;
      y += logoH + Math.round(35 * scale);
    } else {
      y += Math.round(40 * scale);
    }

    // === TORNEO NOMBRE ===
    ctx.fillStyle = ACCENT_BLUE;
    ctx.font = `600 ${fontSizeTorneo}px "Inter", "Segoe UI", sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText(torneoNombre.toUpperCase(), W / 2, y);
    y += Math.round(55 * scale);

    // === CATEGORÍA ===
    ctx.fillStyle = TEXT_WHITE;
    ctx.font = `bold ${fontSizeCat}px "Inter", "Segoe UI", sans-serif`;
    ctx.fillText(categoriaNombre.toUpperCase(), W / 2, y);
    y += Math.round(40 * scale);

    // Línea decorativa
    const lineGrad = ctx.createLinearGradient(W / 2 - 120, 0, W / 2 + 120, 0);
    lineGrad.addColorStop(0, 'transparent');
    lineGrad.addColorStop(0.5, ACCENT_BLUE);
    lineGrad.addColorStop(1, 'transparent');
    ctx.strokeStyle = lineGrad;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(W / 2 - 120, y);
    ctx.lineTo(W / 2 + 120, y);
    ctx.stroke();
    y += 30;

    // === COLUMNAS ===
    const COL_HORA_X = PAD;
    const COL_HORA_W = 140;
    const COL_CANCHA_W = 150;
    const COL_MATCH_X = COL_HORA_X + COL_HORA_W;
    const COL_MATCH_W = INNER - COL_HORA_W - COL_CANCHA_W;
    const COL_CANCHA_X = COL_MATCH_X + COL_MATCH_W;

    // === ZONAS ===
    ctx.textAlign = 'left';

    zonasConPartidos.forEach((zona) => {
      // Zona header con fondo
      roundRect(ctx, PAD, y, INNER, ZONA_HEAD_H, 6);
      const zGrad = ctx.createLinearGradient(PAD, y, PAD + INNER, y);
      zGrad.addColorStop(0, ZONA_BG);
      zGrad.addColorStop(1, '#141438');
      ctx.fillStyle = zGrad;
      ctx.fill();

      // Borde izquierdo accent
      ctx.fillStyle = ACCENT_BLUE;
      roundRect(ctx, PAD, y, 4, ZONA_HEAD_H, 3);
      ctx.fill();

      // Nombre zona
      ctx.fillStyle = TEXT_WHITE;
      ctx.font = `bold ${fontSizeZona}px "Inter", "Segoe UI", sans-serif`;
      ctx.fillText(zona.nombre.toUpperCase(), PAD + 18, y + ZONA_HEAD_H * 0.65);

      // Cantidad partidos
      ctx.fillStyle = TEXT_MUTED;
      ctx.font = `${fontSizeSmall + 3}px "Inter", "Segoe UI", sans-serif`;
      ctx.textAlign = 'right';
      ctx.fillText(`${zona.partidos.length} partidos`, PAD + INNER - 14, y + ZONA_HEAD_H * 0.65);
      ctx.textAlign = 'left';

      y += ZONA_HEAD_H + 4;

      // Column headers
      ctx.fillStyle = '#0d0d22';
      ctx.fillRect(PAD, y, INNER, COL_HEAD_H);
      ctx.fillStyle = TEXT_MUTED;
      ctx.font = `bold ${fontSizeSmall}px "Inter", "Segoe UI", sans-serif`;
      ctx.fillText('HORARIO', COL_HORA_X + 10, y + COL_HEAD_H * 0.7);
      ctx.fillText('PARTIDO', COL_MATCH_X + 10, y + COL_HEAD_H * 0.7);
      ctx.textAlign = 'right';
      ctx.fillText('CANCHA', COL_CANCHA_X + COL_CANCHA_W - 10, y + COL_HEAD_H * 0.7);
      ctx.textAlign = 'left';
      y += COL_HEAD_H;

      // Partidos ordenados
      const sorted = [...zona.partidos].sort((a, b) => {
        const fa = a.fecha_hora_inicio || a.fecha_hora || '';
        const fb = b.fecha_hora_inicio || b.fecha_hora || '';
        if (!fa || !fb) return 0;
        return new Date(fa).getTime() - new Date(fb).getTime();
      });

      sorted.forEach((partido, pi) => {
        const rowY = y;
        ctx.fillStyle = pi % 2 === 0 ? ROW_EVEN : ROW_ODD;
        ctx.fillRect(PAD, rowY, INNER, ROW_H);

        // Borde inferior sutil
        ctx.strokeStyle = BORDER;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(PAD, rowY + ROW_H);
        ctx.lineTo(PAD + INNER, rowY + ROW_H);
        ctx.stroke();

        const fechaStr = partido.fecha_hora_inicio || partido.fecha_hora;

        // Hora
        ctx.fillStyle = ACCENT_BLUE;
        ctx.font = `bold ${fontSizeHora}px "Inter", "Segoe UI", sans-serif`;
        ctx.fillText(formatHora(fechaStr), COL_HORA_X + 10, rowY + ROW_H * 0.38);

        // Día
        ctx.fillStyle = TEXT_MUTED;
        ctx.font = `${fontSizeSmall}px "Inter", "Segoe UI", sans-serif`;
        ctx.fillText(formatDia(fechaStr), COL_HORA_X + 10, rowY + ROW_H * 0.68);

        // Separador vertical
        ctx.strokeStyle = BORDER;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(COL_MATCH_X, rowY + 12);
        ctx.lineTo(COL_MATCH_X, rowY + ROW_H - 12);
        ctx.stroke();

        // Pareja 1 - blanco, mismo tamaño
        const p1 = partido.pareja1_nombre || 'Por definir';
        const p2 = partido.pareja2_nombre || 'Por definir';
        const maxW = COL_MATCH_W - 20;

        ctx.fillStyle = TEXT_WHITE;
        ctx.font = `bold ${fontSize}px "Inter", "Segoe UI", sans-serif`;
        ctx.fillText(truncText(ctx, p1, maxW), COL_MATCH_X + 10, rowY + ROW_H * 0.35);

        // "vs" en accent
        ctx.font = `bold ${fontSizeSmall}px "Inter", "Segoe UI", sans-serif`;
        ctx.fillStyle = ACCENT_PURPLE;
        ctx.fillText('vs', COL_MATCH_X + 10, rowY + ROW_H * 0.67);
        const vsW = ctx.measureText('vs  ').width;

        // Pareja 2 - blanco, mismo tamaño que pareja 1
        ctx.fillStyle = TEXT_WHITE;
        ctx.font = `bold ${fontSize}px "Inter", "Segoe UI", sans-serif`;
        ctx.fillText(truncText(ctx, p2, maxW - vsW), COL_MATCH_X + 10 + vsW, rowY + ROW_H * 0.67);

        // Separador vertical
        ctx.strokeStyle = BORDER;
        ctx.beginPath();
        ctx.moveTo(COL_CANCHA_X, rowY + 12);
        ctx.lineTo(COL_CANCHA_X, rowY + ROW_H - 12);
        ctx.stroke();

        // Cancha
        const cancha = getNombreCancha(partido.cancha_id);
        if (cancha) {
          ctx.fillStyle = ACCENT_PURPLE;
          ctx.font = `bold ${Math.max(13, Math.round(18 * scale))}px "Inter", "Segoe UI", sans-serif`;
          ctx.textAlign = 'center';
          ctx.fillText(cancha, COL_CANCHA_X + COL_CANCHA_W / 2, rowY + ROW_H / 2 + 6);
          ctx.textAlign = 'left';
        }

        y += ROW_H;
      });

      y += ZONA_GAP;
    });

    // === FOOTER ===
    y = Math.max(y + 10, H - FOOTER_H);
    ctx.strokeStyle = BORDER;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(PAD, y);
    ctx.lineTo(PAD + INNER, y);
    ctx.stroke();

    ctx.fillStyle = TEXT_MUTED;
    ctx.font = `${Math.max(14, Math.round(18 * scale))}px "Inter", "Segoe UI", sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText('drive-plus.com.ar', W / 2, y + 35);
  };

  const descargarImagen = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    setDescargando(true);
    try {
      const link = document.createElement('a');
      link.download = `fixture-${categoriaNombre.replace(/\s/g, '-')}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (err) {
      console.error('Error al descargar:', err);
    } finally {
      setDescargando(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center bg-black/85">
      {/* Canvas scrollable */}
      <div className="flex-1 overflow-y-auto flex justify-center pt-2 pb-2 px-2 w-full" style={{ scrollbarWidth: 'thin' }}>
        <canvas
          ref={canvasRef}
          className="rounded-lg shadow-2xl w-full max-w-[480px]"
          style={{ height: 'auto' }}
        />
      </div>

      {/* Barra inferior fija con botones */}
      <div className="w-full flex items-center justify-center gap-2 sm:gap-3 px-3 py-2.5 bg-black/70 backdrop-blur-sm flex-shrink-0 border-t border-white/10">
        <button
          onClick={descargarImagen}
          disabled={descargando}
          className="flex items-center gap-2 px-4 sm:px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg text-xs sm:text-sm font-bold hover:opacity-90 transition-opacity"
        >
          <Download size={16} />
          {descargando ? 'Generando...' : 'Descargar'}
        </button>
        <button
          onClick={onClose}
          className="flex items-center gap-2 px-4 sm:px-6 py-2.5 bg-white/10 text-white rounded-lg text-xs sm:text-sm font-bold hover:bg-white/20 transition-colors"
        >
          <X size={16} />
          Cerrar
        </button>
      </div>
    </div>
  );
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function truncText(ctx: CanvasRenderingContext2D, text: string, maxW: number): string {
  if (ctx.measureText(text).width <= maxW) return text;
  let t = text;
  while (t.length > 0 && ctx.measureText(t + '…').width > maxW) t = t.slice(0, -1);
  return t + '…';
}
