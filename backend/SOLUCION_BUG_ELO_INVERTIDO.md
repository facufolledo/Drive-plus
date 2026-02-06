# 🚨 BUG CRÍTICO: ELO INVERTIDO EN TORNEO 37

## Problema Detectado

**TODOS los cambios de ELO están invertidos:**
- ❌ Los GANADORES pierden puntos
- ❌ Los PERDEDORES ganan puntos

## Evidencia

### Partido 210: Pareja 462 (GANÓ) vs Pareja 494 (PERDIÓ)
- **leandroruarte** (PERDIÓ): +20 puntos ❌
- **bautistaoliva** (PERDIÓ): +16 puntos ❌
- **juanpabloromerojr** (GANÓ): -12 puntos ❌
- **juanromero** (GANÓ): -12 puntos ❌

### Partido 167: Pareja 474 (GANÓ) vs Pareja 477 (PERDIÓ)
- **santinomolina** (GANÓ): -12 puntos ❌
- **agustinmartinez** (GANÓ): -12 puntos ❌
- **dariobarrionuevo** (PERDIÓ): +72 puntos ❌
- **matias.vega25** (PERDIÓ): +116 puntos ❌

## Estadísticas

- **Total de cambios analizados**: 20
- **Correctos**: 0
- **Invertidos**: 20 (100%)
- **Partidos afectados**: 5

## Causa Raíz

El problema estaba en `backend/src/services/torneo_resultado_service.py` en el mapeo de parejas a equipos.

### El Bug Original

```python
# ❌ CÓDIGO INCORRECTO (antes de la corrección)
pareja1_es_equipoA = False  # Valor por defecto INCORRECTO

if jugadores_equipoA:  # Esta condición NUNCA se cumplía
    ids_pareja1 = {pareja1.jugador1_id, pareja1.jugador2_id}
    ids_equipoA = {j.get('id') for j in jugadores_equipoA if j.get('id')}
    pareja1_es_equipoA = bool(ids_pareja1.intersection(ids_equipoA))
```

**Problema**: 
- El frontend **nunca envía jugadores** en el resultado, solo `sets` con `gamesEquipoA/gamesEquipoB`
- La condición `if jugadores_equipoA:` nunca se cumplía
- Siempre usaba el valor por defecto `pareja1_es_equipoA = False`
- Esto invertía el mapeo: trataba `pareja1` como `equipoB` y `pareja2` como `equipoA`

**Consecuencia**:
- Si `pareja1` ganaba 2-0, el sistema creía que había ganado `pareja2`
- Los sets se asignaban al revés en el cálculo de ELO
- El ganador recibía el delta del perdedor (negativo) y viceversa

## Solución

### Corrección Aplicada

El código en `backend/src/services/torneo_resultado_service.py` fue corregido:

```python
# ✅ CÓDIGO CORREGIDO
pareja1_es_equipoA = True  # DEFAULT: frontend usa pareja1=equipoA, pareja2=equipoB

if jugadores_equipoA:  # Solo verificar si hay jugadores (caso raro)
    ids_pareja1 = {pareja1.jugador1_id, pareja1.jugador2_id}
    ids_equipoA = {j.get('id') for j in jugadores_equipoA if j.get('id')}
    pareja1_es_equipoA = bool(ids_pareja1.intersection(ids_equipoA))

# Asignar sets correctamente según la correspondencia
if pareja1_es_equipoA:
    sets_pareja1 = sets_a  # sets de equipoA
    sets_pareja2 = sets_b  # sets de equipoB
else:
    sets_pareja1 = sets_b  # sets de equipoB (invertido)
    sets_pareja2 = sets_a  # sets de equipoA (invertido)
```

**Cambios clave**:
1. ✅ Valor por defecto correcto: `pareja1_es_equipoA = True`
2. ✅ Respeta la convención del frontend: `pareja1 = equipoA`, `pareja2 = equipoB`
3. ✅ `sets_detail` coherente: cuando se invierte el mapeo, `games_a/games_b` se ajustan para coincidir con `pareja1/pareja2`

## Scripts Disponibles

1. **verificar_elo_simple.py**: Detecta el problema (ejecutado - confirmó 20/20 errores)
2. **CORREGIR_ELO_TORNEO37_COMPLETO.py**: Revierte y reapl ica ELO (ejecutado - 100% exitoso)
3. **SOLUCION_BUG_ELO_INVERTIDO.md**: Documentación completa del bug

## Archivos Modificados

- `backend/src/services/torneo_resultado_service.py` - Corregido el valor por defecto de `pareja1_es_equipoA`

## Impacto

- **5 partidos** con ELO mal aplicado
- **20 jugadores** afectados
- **Todos los ratings** del torneo 37 están incorrectos

## Prioridad

🚨 **CRÍTICA** - Debe corregirse inmediatamente antes de que se jueguen más partidos.
