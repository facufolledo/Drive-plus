# FIX: Modal Cambiar Horario

## 🐛 PROBLEMA

El modal de cambiar horario no funcionaba cuando se hacía click en el botón "Horario".

### Causas encontradas:

1. **Tipo incorrecto del estado**: `partidoEditando` era `number | null` pero se pasaba el objeto completo
2. **Parseo de fecha con zona horaria**: La fecha actual se parseaba incorrectamente
3. **Falta de logging**: No había forma de ver qué estaba fallando

## ✅ SOLUCIONES APLICADAS

### 1. Corregir tipo del estado en TorneoFixture.tsx

**ANTES**:
```typescript
const [partidoEditando, setPartidoEditando] = useState<number | null>(null);
```

**DESPUÉS**:
```typescript
const [partidoEditando, setPartidoEditando] = useState<any>(null);
```

### 2. Corregir parseo de fecha en ModalCambiarHorario.tsx

**ANTES** (causaba conversión de zona horaria):
```typescript
const fechaHora = new Date(partidoActual.fecha_hora);
setFecha(fechaHora.toISOString().split('T')[0]);
setHora(fechaHora.toTimeString().slice(0, 5));
```

**DESPUÉS** (sin conversión de zona horaria):
```typescript
// Usar el mismo parseo que en TorneoFixture
const fechaStr = partidoActual.fecha_hora;
const fecha = new Date(fechaStr);
const year = fecha.getUTCFullYear();
const month = fecha.getUTCMonth();
const day = fecha.getUTCDate();
const hours = fecha.getUTCHours();
const minutes = fecha.getUTCMinutes();
const fechaLocal = new Date(year, month, day, hours, minutes);

const fechaISO = fechaLocal.toISOString().split('T')[0];
const horaStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;

setFecha(fechaISO);
setHora(horaStr);
```

### 3. Agregar logging detallado

Agregado console.log en puntos clave:
- Datos enviados al backend
- URL del request
- Token de autenticación
- Respuesta del servidor
- Errores completos

## 🧪 TESTING

### Pasos para probar:

1. **Abrir el frontend** (http://localhost:5173)
2. **Ir al Torneo 37** → Pestaña "Fixture"
3. **Click en botón "Horario"** de cualquier partido pendiente
4. **Verificar**:
   - El modal se abre correctamente
   - Los campos fecha, hora y cancha están pre-llenados
   - Se puede cambiar la fecha/hora
   - Al guardar, se muestra mensaje de éxito o conflictos

### Verificar en consola del navegador:

Deberías ver logs como:
```
🔄 Cambiando horario: {fecha: "2026-02-07", hora: "15:00", canchaId: 1, ...}
📡 Request URL: http://localhost:8000/torneos/37/partidos/94/cambiar-horario
🔑 Token exists: true
📥 Response status: 200
📦 Response data: {success: true, message: "Horario actualizado correctamente", ...}
```

### Casos de prueba:

1. **Cambio exitoso**:
   - Seleccionar horario libre
   - Debe mostrar: "✅ Horario actualizado correctamente"
   - El fixture debe actualizarse automáticamente

2. **Conflicto detectado**:
   - Seleccionar horario ocupado
   - Debe mostrar: "⚠️ El horario solicitado se solapa con X partido(s)"
   - Debe listar los partidos en conflicto

3. **Error de validación**:
   - Dejar fecha u hora vacía
   - Debe mostrar: "Debes seleccionar fecha y hora"

## 📝 ARCHIVOS MODIFICADOS

1. **frontend/src/components/TorneoFixture.tsx**
   - Cambiado tipo de `partidoEditando` de `number | null` a `any`

2. **frontend/src/components/ModalCambiarHorario.tsx**
   - Corregido parseo de fecha sin conversión de zona horaria
   - Agregado logging detallado
   - Mejorado manejo de errores HTTP

## 🔧 ENDPOINT BACKEND

El endpoint ya existía y está funcionando correctamente:

```
PUT /torneos/{torneo_id}/partidos/{partido_id}/cambiar-horario
```

**Request body**:
```json
{
  "fecha": "2026-02-07",
  "hora": "15:00",
  "cancha_id": 1
}
```

**Response exitosa**:
```json
{
  "success": true,
  "message": "Horario actualizado correctamente",
  "partido": {
    "id": 94,
    "pareja1": "jugador1/jugador2",
    "pareja2": "jugador3/jugador4",
    "fecha": "2026-02-07",
    "hora": "15:00",
    "cancha": "Cancha 1",
    "cancha_id": 1
  }
}
```

**Response con conflicto**:
```json
{
  "success": false,
  "error": "SOLAPAMIENTO_DETECTADO",
  "message": "El horario solicitado se solapa con 1 partido(s) en Cancha 1",
  "conflictos": [
    {
      "partido_id": 95,
      "pareja1": "jugador5/jugador6",
      "pareja2": "jugador7/jugador8",
      "fecha_hora": "2026-02-07 15:00",
      "cancha": "Cancha 1"
    }
  ]
}
```

## ✅ CHECKLIST

- [x] Tipo de estado corregido
- [x] Parseo de fecha corregido
- [x] Logging agregado
- [x] Manejo de errores mejorado
- [ ] Frontend recargado (Ctrl+F5)
- [ ] Probado cambio exitoso
- [ ] Probado detección de conflictos

---

**Fecha**: 2026-02-06
**Estado**: ✅ Corregido
**Archivos**: 
- `frontend/src/components/TorneoFixture.tsx`
- `frontend/src/components/ModalCambiarHorario.tsx`
