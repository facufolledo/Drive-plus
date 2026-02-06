# BUG CRÍTICO: Fixture genera partidos en horarios restringidos

## PROBLEMA
El algoritmo de generación de fixture NO respeta las restricciones horarias de las parejas. Ejemplo:
- **Pareja Bicet/Cejas** tiene restricción: NO puede jugar viernes 09:00-19:00
- **El sistema genera**: Partido viernes 16:10 ❌

## REPRESENTACIÓN DE DATOS

### 1. FECHA
- **Tipo**: String
- **Formato**: `"2026-02-06"` (YYYY-MM-DD)
- **Ejemplo**: `"2026-02-14"`

### 2. HORA
- **Tipo**: String
- **Formato**: `"16:10"` (HH:MM)
- **Conversión a minutos**: `hora_mins = int(hora.split(':')[0]) * 60 + int(hora.split(':')[1])`
- **Ejemplo**: `"16:10"` → `970 minutos`

### 3. DÍA DE LA SEMANA
- **Tipo**: String en español, lowercase
- **Valores**: `"lunes"`, `"martes"`, `"miercoles"`, `"jueves"`, `"viernes"`, `"sabado"`, `"domingo"`
- **Conversión desde datetime**:
```python
dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
dia_semana = dias[fecha.weekday()]
```

### 4. DURACIÓN DE PARTIDO
- **Constante**: `50 minutos`
- **Uso**: Un partido que empieza a las 16:10 (970 mins) termina a las 17:00 (1020 mins)

### 5. ESTRUCTURA DE RESTRICCIONES EN BASE DE DATOS
Campo `disponibilidad_horaria` en tabla `torneos_parejas` (tipo JSONB):

```json
[
  {
    "dias": ["viernes"],
    "horaInicio": "09:00",
    "horaFin": "19:00"
  },
  {
    "dias": ["sabado"],
    "horaInicio": "09:00",
    "horaFin": "10:00"
  }
]
```

**IMPORTANTE**: Estas son **RESTRICCIONES** (horarios cuando NO pueden jugar), no disponibilidad.

### 6. ESTRUCTURA DE HORARIOS DEL TORNEO
Campo `horarios_disponibles` en tabla `torneos` (tipo JSONB):

**Formato actual en DB** (lista):
```json
[
  {
    "dias": ["viernes"],
    "horaInicio": "15:00",
    "horaFin": "23:30"
  },
  {
    "dias": ["sabado", "domingo"],
    "horaInicio": "09:00",
    "horaFin": "23:30"
  }
]
```

**Formato esperado por el algoritmo** (dict):
```json
{
  "viernes": {"inicio": "15:00", "fin": "23:30"},
  "sabado": {"inicio": "09:00", "fin": "23:30"},
  "domingo": {"inicio": "09:00", "fin": "23:30"}
}
```

## BUGS IDENTIFICADOS

### BUG #1: Formato de horarios_torneo (YA CORREGIDO)
**Ubicación**: Línea ~320 en `_generar_slots_torneo()`
**Problema**: El método asume que `horarios_torneo` es dict, pero se guarda como lista
**Fix aplicado**: Normalización al inicio del método

### BUG #2: Ocupación de canchas solo valida hora exacta (PENDIENTE)
**Ubicación**: Línea ~350 en `_asignar_horarios_y_canchas()`
**Problema**: 
```python
ocupacion_canchas[(fecha, hora)].append(cancha_id)
```
Solo detecta choques si la hora es **exactamente** la misma. No valida solapamiento de rangos.

**Ejemplo del problema**:
- Partido A: 16:00-16:50 en Cancha 1
- Partido B: 16:30-17:20 en Cancha 1
- El sistema permite ambos porque `16:00 != 16:30` ❌

**Fix necesario**: Validar solapamiento por rangos (inicio_dt, fin_dt)

### BUG #3: Formato alternativo de restricciones no contemplado (PENDIENTE)
**Ubicación**: Línea ~200 en `_obtener_disponibilidad_parejas()`
**Problema**: Si las restricciones vienen con claves diferentes, se ignoran
**Fix necesario**: Normalizar claves alternativas

## FUNCIÓN QUE ELIGE EL HORARIO

### Método principal: `_asignar_horarios_y_canchas()`
**Ubicación**: Línea ~350 en `backend/src/services/torneo_fixture_global_service.py`

**Lógica actual**:
1. Itera por cada partido sin programar
2. Para cada slot disponible (fecha, dia, hora):
   - Verifica disponibilidad horaria de ambas parejas
   - Verifica tiempo mínimo entre partidos (180 minutos)
   - Verifica cancha disponible
3. Si encuentra slot válido, lo asigna

**Código relevante**:
```python
for fecha, dia, hora in slots_disponibles:
    # 1. VERIFICAR DISPONIBILIDAD HORARIA
    hora_mins = int(hora.split(':')[0]) * 60 + int(hora.split(':')[1])
    
    pareja1_disponible = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
        dia, hora_mins, disp1
    )
    
    pareja2_disponible = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
        dia, hora_mins, disp2
    )
    
    if not (pareja1_disponible and pareja2_disponible):
        continue
    
    # 2. VERIFICAR TIEMPO MÍNIMO ENTRE PARTIDOS (180 MINUTOS)
    # ... código ...
    
    # 3. VERIFICAR CANCHA DISPONIBLE
    canchas_ocupadas = ocupacion_canchas[(fecha, hora)]
    cancha_libre = None
    
    for cancha in canchas:
        if cancha.id not in canchas_ocupadas:
            cancha_libre = cancha
            break
```

### Método de verificación: `_verificar_disponibilidad_pareja()`
**Ubicación**: Línea ~565 en `backend/src/services/torneo_fixture_global_service.py`

**Lógica**:
```python
@staticmethod
def _verificar_disponibilidad_pareja(dia: str, hora_mins: int, disponibilidad: Dict) -> bool:
    """
    Verifica si una pareja está disponible en un día y hora específicos
    
    Returns:
        bool: True si está disponible, False si está restringido
    """
    restricciones = disponibilidad.get('restricciones', {})
    
    # Sin restricciones = disponible siempre
    if not restricciones:
        return True
    
    # Verificar si el día tiene restricciones
    if dia not in restricciones:
        return True  # Día sin restricciones = disponible todo el día
    
    # Verificar si la hora está en alguna restricción
    rangos_restringidos = restricciones[dia]
    for inicio_mins, fin_mins in rangos_restringidos:
        # Verificar solapamiento: partido [hora_mins, hora_mins + 50] vs restricción [inicio_mins, fin_mins]
        if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
            return False  # Hay solapamiento = NO disponible
    
    return True  # No hay solapamiento = disponible
```

## EJEMPLO CONCRETO DEL BUG

### Pareja: Diego Bicet / Juan Cejas (ID #463)
**Restricciones en DB**:
```json
[
  {
    "dias": ["viernes"],
    "horaInicio": "09:00",
    "horaFin": "19:00"
  },
  {
    "dias": ["sabado"],
    "horaInicio": "09:00",
    "horaFin": "10:00"
  },
  {
    "dias": ["sabado"],
    "horaInicio": "13:00",
    "horaFin": "17:00"
  }
]
```

**Interpretación**:
- Viernes: NO pueden 09:00-19:00 (540-1140 mins)
- Sábado: NO pueden 09:00-10:00 (540-600 mins) Y 13:00-17:00 (780-1020 mins)
- Sábado SÍ pueden: 10:00-13:00 Y 17:00-23:30
- Domingo: SÍ pueden todo el día (09:00-23:30)

**Partido generado incorrectamente**:
- Fecha: Viernes 2026-02-14
- Hora: 16:10 (970 minutos)
- Fin: 17:00 (1020 minutos)

**Verificación**:
- Día: `"viernes"`
- Restricción viernes: 09:00-19:00 (540-1140 mins)
- Partido: 16:10-17:00 (970-1020 mins)
- Solapamiento: `970 < 1140 AND 1020 > 540` → **TRUE** ❌
- **Resultado esperado**: `_verificar_disponibilidad_pareja()` debería retornar `False`
- **Resultado actual**: Retorna `True` (por eso se programa el partido)

## TESTS EJECUTADOS

### Test 1: `test_generar_fixture_torneo37.py`
- Genera 7 partidos correctamente
- Bicet/Cejas juegan viernes 19:10 y sábado 10:40 ✅

### Test 2: `test_fixture_torneo37_restricciones.py`
- Verifica 0 violaciones ✅
- Todos los partidos respetan restricciones

### Problema: Backend en producción sigue generando mal
- Cache limpiado (`.pyc`)
- Backend reiniciado múltiples veces
- Sigue generando partido viernes 16:10 ❌

## POSIBLES CAUSAS

1. **Cache de Python no limpiado correctamente**
2. **Backend no está usando el código corregido** (deployment issue)
3. **Bug adicional no identificado** en la lógica de verificación
4. **Datos corruptos en DB** que no coinciden con lo esperado

## ARCHIVOS INVOLUCRADOS

### Archivo principal con el bug:
`backend/src/services/torneo_fixture_global_service.py`

### Métodos críticos:
1. `_generar_slots_torneo()` - Línea ~320
2. `_asignar_horarios_y_canchas()` - Línea ~350
3. `_verificar_disponibilidad_pareja()` - Línea ~565
4. `_obtener_disponibilidad_parejas()` - Línea ~200

### Scripts de test:
- `backend/test_generar_fixture_torneo37.py`
- `backend/test_fixture_torneo37_restricciones.py`
- `backend/verificar_torneo_37.py`
- `backend/debug_restricciones_bicet.py`
- `backend/debug_slots_torneo37.py`

## CONFIGURACIÓN DEL TORNEO 37

- **ID**: 37
- **Fecha inicio**: 2026-02-14 (viernes)
- **Fecha fin**: 2026-02-16 (domingo)
- **Horarios**:
  - Viernes: 15:00-23:30
  - Sábado: 09:00-23:30
  - Domingo: 09:00-23:30
- **Canchas**: 5 (Cancha 1-5)
- **Categorías**: 3 (7ma, Principiante, 5ta)
- **Parejas**: 19 (8 en 7ma, 11 en Principiante, 0 en 5ta)

## REGLAS DEL ALGORITMO

1. **Duración de partido**: 50 minutos
2. **Tiempo mínimo entre partidos del mismo jugador**: 180 minutos (3 horas)
3. **Máximo partidos simultáneos**: Número de canchas disponibles (5)
4. **Restricciones horarias**: DEBEN respetarse estrictamente
5. **Generación por categoría**: Debe considerar partidos ya programados de otras categorías

## SOLICITUD

Por favor, analiza el código de `backend/src/services/torneo_fixture_global_service.py` y:

1. Identifica por qué `_verificar_disponibilidad_pareja()` está retornando `True` cuando debería retornar `False`
2. Verifica si hay algún bug adicional en la lógica de verificación
3. Proporciona el código corregido para los métodos afectados
4. Sugiere cómo agregar logging detallado para debug

**NOTA**: Los tests locales funcionan correctamente, pero el backend en ejecución sigue generando partidos incorrectos. Esto sugiere que puede haber un problema de deployment o cache que no se está limpiando correctamente.
