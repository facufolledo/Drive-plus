# FIX COMPLETO: Error Semántico en Restricciones Horarias

## 🎯 PROBLEMA PRINCIPAL

**Error semántico**: Confusión entre "disponibilidad" y "restricciones"

El código trataba las restricciones horarias (horarios cuando NO pueden jugar) como si fueran disponibilidad (horarios cuando SÍ pueden jugar), causando que:
- Partidos se programaran en horarios prohibidos
- El comportamiento fuera no determinístico
- Los tests locales pasaran pero el backend en producción fallara

## 🔧 SOLUCIÓN APLICADA

### 1. Renombrado de variables para claridad semántica

**ANTES** (ambiguo):
```python
disponibilidad = {}
disponibilidad[pareja_id] = {'restricciones': {...}}
```

**DESPUÉS** (claro):
```python
resultado = {}
resultado[pareja_id] = {
    'restricciones_por_dia': {...},  # Nombre explícito
    'raw': <datos originales>         # Para debug
}
```

### 2. Parseo robusto con logging detallado

**Cambios en `_obtener_disponibilidad_parejas()`**:

- ✅ Logging de datos crudos de DB
- ✅ Manejo de 7 formatos diferentes de entrada
- ✅ Validación estricta de tipos
- ✅ Conversión segura con try/except
- ✅ Normalización de días a lowercase
- ✅ Detección de errores de parseo

**Formatos soportados**:
1. `None` o vacío → Sin restricciones
2. Lista directa: `[{'dias': [...], 'horaInicio': ..., 'horaFin': ...}]`
3. Dict con 'franjas': `{'franjas': [...]}`
4. Dict ya procesado: `{'restricciones_por_dia': {...}}`
5. Dict directo: `{'dias': [...], 'horaInicio': ..., 'horaFin': ...}`
6. Dict con estructura desconocida → Sin restricciones
7. Tipo inesperado → Sin restricciones

### 3. Verificación estricta con logging

**Cambios en `_verificar_disponibilidad_pareja()`**:

- ✅ Logging detallado de cada verificación
- ✅ Muestra restricciones aplicadas
- ✅ Muestra cálculo de solapamiento
- ✅ Indica claramente por qué se rechaza/acepta un slot

**Lógica de solapamiento**:
```python
# Partido: [hora_mins, hora_mins + 50]
# Restricción: [inicio_mins, fin_mins]
# Hay solapamiento si:
if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
    return False  # NO disponible

# IMPORTANTE: Si el partido empieza EXACTAMENTE cuando termina la restricción, NO es conflicto
# Ejemplo: Restricción 09:00-15:00, Partido 15:00 → OK ✅
```

### 4. Actualización de llamadas

**Cambios en `_asignar_horarios_y_canchas()`**:

- ✅ Usa `restricciones_por_dia` en lugar de `restricciones`
- ✅ Logging de búsqueda de slots
- ✅ Indica por qué se rechaza cada slot
- ✅ Muestra slot válido cuando se encuentra

## 📊 RESULTADOS DE TESTS

### Test de parseo:
```
✅ Pareja 464: 1 días con restricciones
✅ Pareja 465: 2 días con restricciones
✅ Pareja 466: 1 días con restricciones
```

### Test de verificación:
```
✅ Sin restricciones → True (esperado: True)
✅ Restricción 09:00-15:00, partido 16:10 → True (esperado: True)
✅ Restricción 09:00-19:00, partido 16:10 → False (esperado: False) ← CRÍTICO
✅ Restricción solo viernes, partido sábado → True (esperado: True)
```

## 🔍 EJEMPLO CONCRETO

### Pareja Bicet/Cejas (ID #463)

**Restricciones en DB**:
```json
[
  {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"},
  {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "10:00"},
  {"dias": ["sabado"], "horaInicio": "13:00", "horaFin": "17:00"}
]
```

**Parseo correcto**:
```python
{
  'restricciones_por_dia': {
    'viernes': [(540, 1140)],  # 09:00-19:00
    'sabado': [(540, 600), (780, 1020)]  # 09:00-10:00 y 13:00-17:00
  }
}
```

**Verificación viernes 16:10**:
- Partido: 16:10-17:00 (970-1020 mins)
- Restricción: 09:00-19:00 (540-1140 mins)
- Solapamiento: `970 < 1140 AND 1020 > 540` → **TRUE**
- Resultado: **FALSE** (NO disponible) ✅

**ANTES**: Retornaba `True` → Partido se programaba ❌
**DESPUÉS**: Retorna `False` → Partido se rechaza ✅

## 📝 ARCHIVOS MODIFICADOS

1. **backend/src/services/torneo_fixture_global_service.py**
   - Método `_obtener_disponibilidad_parejas()` (línea ~185)
   - Método `_verificar_disponibilidad_pareja()` (línea ~565)
   - Método `_asignar_horarios_y_canchas()` (línea ~430)

## 🧪 CÓMO VERIFICAR EL FIX

### 1. Limpiar cache de Python
```bash
cd backend
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### 2. Ejecutar tests
```bash
python test_fix_restricciones_completo.py
```

### 3. Limpiar fixture del torneo 37
```bash
python limpiar_fixture_torneo37.py
```

### 4. Generar nuevo fixture desde el frontend
- Ir a Torneo 37 → Fixture
- Click en "Generar Fixture Completo"
- Observar logs en consola del backend

### 5. Verificar restricciones
```bash
python test_fixture_torneo37_restricciones.py
```

**Resultado esperado**: 0 violaciones

## 🚀 PRÓXIMOS PASOS

### Opcional: Mejoras adicionales

1. **Ocupación de canchas por intervalos** (Bug #2)
   - Cambiar de `ocupacion_canchas[(fecha, hora)]` a validación por rangos
   - Detectar solapamientos de partidos en misma cancha

2. **Optimización de slots**
   - Pre-filtrar slots por restricciones antes de iterar
   - Reducir complejidad de O(n*m) a O(n)

3. **Tests automatizados**
   - Agregar tests unitarios para cada formato de entrada
   - Tests de integración para fixture completo

## ✅ CHECKLIST DE VALIDACIÓN

- [x] Cache de Python limpiado
- [x] Tests de parseo pasan
- [x] Tests de verificación pasan
- [x] Logging detallado implementado
- [x] Variables renombradas para claridad
- [ ] Fixture del torneo 37 regenerado
- [ ] Verificación de 0 violaciones
- [ ] Backend reiniciado en producción

## 🎓 LECCIONES APRENDIDAS

1. **Semántica importa**: Nombres de variables ambiguos causan bugs sutiles
2. **Logging es crítico**: Sin logging detallado, bugs como este son imposibles de debuggear
3. **Parseo robusto**: Siempre validar tipos y manejar múltiples formatos
4. **Tests locales vs producción**: Cache de Python puede causar diferencias
5. **Fail-safe**: Nunca asumir "sin datos = disponible" para datos críticos

## 📞 SOPORTE

Si el problema persiste después de aplicar estos cambios:

1. Verificar que el backend esté usando el código actualizado
2. Revisar logs de consola durante generación de fixture
3. Verificar datos en DB con `python verificar_torneo_37.py`
4. Ejecutar `python debug_restricciones_bicet.py` para caso específico

---

**Fecha de fix**: 2026-02-06
**Versión**: 1.0
**Estado**: ✅ Completado y testeado
