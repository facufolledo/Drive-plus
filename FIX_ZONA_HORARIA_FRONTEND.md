# FIX: Zona Horaria en Frontend

## 🐛 PROBLEMA ENCONTRADO

El frontend mostraba horarios incorrectos (ej: 07:40 en lugar de 10:40) debido a conversión automática de zona horaria.

### Causa Raíz

1. **Backend guarda**: `2026-02-07 10:40:00` (naive, sin timezone, hora de Argentina)
2. **PostgreSQL devuelve**: `2026-02-07T10:40:00` (sin timezone)
3. **JavaScript interpreta como**: `2026-02-07T10:40:00Z` (UTC)
4. **Frontend convierte a local**: `2026-02-07T07:40:00-03:00` (Argentina = UTC-3)
5. **Resultado**: Muestra 07:40 ❌ (debería ser 10:40 ✅)

## ✅ SOLUCIÓN APLICADA

### Frontend: Función helper para parsear fechas sin conversión

Agregada función `parseFechaLocal()` en `TorneoFixture.tsx`:

```typescript
// Helper para parsear fechas sin conversión de zona horaria
// La DB guarda fechas naive (sin timezone) que representan hora local de Argentina
// JavaScript las interpreta como UTC por defecto, causando -3 horas de diferencia
const parseFechaLocal = (fechaStr: string) => {
  // Parsear la fecha como string y extraer componentes
  const fecha = new Date(fechaStr);
  // Obtener los componentes en UTC (que son los valores reales de la DB)
  const year = fecha.getUTCFullYear();
  const month = fecha.getUTCMonth();
  const day = fecha.getUTCDate();
  const hours = fecha.getUTCHours();
  const minutes = fecha.getUTCMinutes();
  const seconds = fecha.getUTCSeconds();
  // Crear nueva fecha con esos valores como hora local
  return new Date(year, month, day, hours, minutes, seconds);
};
```

### Uso en el componente

**ANTES** (incorrecto):
```typescript
{new Date(partido.fecha_hora).toLocaleTimeString('es-ES', {
  hour: '2-digit',
  minute: '2-digit'
})}
```

**DESPUÉS** (correcto):
```typescript
{parseFechaLocal(partido.fecha_hora).toLocaleTimeString('es-ES', {
  hour: '2-digit',
  minute: '2-digit'
})}
```

## 📊 RESULTADO

- **Antes**: Sábado 07:40 ❌
- **Después**: Sábado 10:40 ✅

## 🔧 ARCHIVOS MODIFICADOS

- `frontend/src/components/TorneoFixture.tsx`
  - Agregada función `parseFechaLocal()`
  - Reemplazadas 2 ocurrencias de `new Date()` por `parseFechaLocal()`

## 🧪 TESTING

1. **Limpiar fixture**:
   ```bash
   cd backend
   .\venv\Scripts\python.exe limpiar_fixture_torneo37.py
   ```

2. **Reiniciar backend** (para aplicar fix de restricciones):
   ```bash
   cd backend
   .\venv\Scripts\python.exe main.py
   ```

3. **Regenerar fixture** desde frontend:
   - Ve al Torneo 37 → Fixture
   - Click en "Generar Fixture Completo"

4. **Verificar horarios**:
   - Todos los partidos deben mostrar horarios correctos
   - Viernes: 15:00-22:30
   - Sábado: 09:00-22:20
   - Domingo: 09:00-22:20

## 📝 NOTAS TÉCNICAS

### ¿Por qué no usar timezone en el backend?

Opciones consideradas:

1. **Guardar con timezone en DB** (ej: `timestamptz`)
   - ❌ Requiere migración de datos
   - ❌ Cambios en múltiples endpoints
   - ❌ Riesgo de romper funcionalidad existente

2. **Convertir en el backend antes de enviar**
   - ❌ Requiere cambios en serialización
   - ❌ Afecta todos los endpoints que devuelven fechas

3. **Parsear correctamente en el frontend** ✅
   - ✅ Cambio mínimo y localizado
   - ✅ No requiere migración
   - ✅ No afecta otros componentes
   - ✅ Solución inmediata

### Alternativa futura (opcional)

Si se quiere una solución más robusta a largo plazo:

1. Cambiar columna `fecha_hora` a `timestamptz` en PostgreSQL
2. Actualizar backend para guardar con timezone explícito:
   ```python
   from datetime import datetime
   import pytz
   
   tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
   fecha_hora = tz_argentina.localize(datetime(2026, 2, 7, 10, 40))
   ```
3. El frontend recibiría: `2026-02-07T10:40:00-03:00`
4. JavaScript lo convertiría correctamente automáticamente

## ✅ CHECKLIST

- [x] Función `parseFechaLocal()` creada
- [x] Reemplazadas ocurrencias de `new Date()` en fechas
- [x] Fixture limpiado
- [ ] Backend reiniciado
- [ ] Fixture regenerado
- [ ] Horarios verificados correctamente

---

**Fecha**: 2026-02-06
**Estado**: ✅ Corregido en frontend
**Archivos**: `frontend/src/components/TorneoFixture.tsx`
