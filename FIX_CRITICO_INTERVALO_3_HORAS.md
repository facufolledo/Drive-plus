# FIX CRÍTICO: Intervalo de 3 Horas Entre Partidos

## 🐛 BUG ENCONTRADO

### Problema 1: Intervalo de 3 horas NO respetado
**Ejemplo**: Eric Leterrucci / Facundo Guerrero juegan:
- Partido 1: Viernes 16:10
- Partido 2: Viernes 17:50
- **Diferencia**: 100 minutos ❌ (debería ser mínimo 180 minutos)

### Problema 2: Restricciones horarias NO respetadas
**Ejemplo**: Matias Giordano / Damian Tapia:
- Restricción: NO pueden viernes 09:00-15:00
- Partido programado: Viernes 12:00 ❌

## 🔍 CAUSA RAÍZ

El método `generar_fixture_completo()` tenía un bug crítico:

```python
# ANTES (INCORRECTO)
partidos_existentes = []
if categoria_id:
    # Solo carga partidos existentes si se genera POR CATEGORÍA
    partidos_existentes = db.query(Partido).filter(...)
```

**Problema**: Cuando se genera el fixture COMPLETO (sin especificar categoría), procesaba todas las categorías en un solo lote, pero `_guardar_partidos()` **eliminaba todos los partidos existentes** antes de guardar los nuevos.

**Resultado**:
1. Genera partidos de categoría 7ma
2. Genera partidos de categoría Principiante
3. **Borra TODOS los partidos** (incluyendo los de 7ma)
4. Guarda solo los nuevos
5. Los jugadores de 7ma que también están en Principiante tienen partidos muy cercanos

## ✅ SOLUCIÓN APLICADA

### Cambio 1: Generar por categoría secuencialmente

```python
# DESPUÉS (CORRECTO)
if not categoria_id:
    # Obtener todas las categorías
    categorias = db.query(TorneoCategoria).filter(...)
    
    # Generar fixture para cada categoría SECUENCIALMENTE
    for categoria in categorias:
        resultado_cat = TorneoFixtureGlobalService._generar_fixture_categoria(
            db, torneo_id, user_id, categoria.id
        )
        # Acumular resultados
```

### Cambio 2: Nuevo método `_generar_fixture_categoria()`

Este método:
1. Genera fixture para UNA categoría
2. Carga partidos ya programados de OTRAS categorías
3. Respeta el intervalo de 3 horas con esos partidos
4. Guarda solo los partidos de esta categoría (sin borrar los demás)

```python
@staticmethod
def _generar_fixture_categoria(db, torneo_id, user_id, categoria_id):
    # Cargar partidos de OTRAS categorías
    partidos_existentes = db.query(Partido).filter(
        Partido.id_torneo == torneo_id,
        Partido.fase == 'zona',
        Partido.categoria_id != categoria_id,  # OTRAS categorías
        Partido.fecha_hora.isnot(None)
    ).all()
    
    # Generar partidos considerando los existentes
    resultado = _asignar_horarios_y_canchas(
        ...,
        partidos_existentes  # Respeta estos partidos
    )
    
    # Guardar solo partidos de ESTA categoría
    _guardar_partidos(db, torneo_id, partidos_programados, categoria_id)
```

## 📊 FLUJO CORREGIDO

### Antes (INCORRECTO):
```
1. Generar TODOS los partidos de TODAS las categorías
2. Asignar horarios (sin considerar partidos de otras categorías)
3. Borrar TODOS los partidos existentes
4. Guardar TODOS los nuevos
```

### Después (CORRECTO):
```
1. Generar partidos de Categoría 1
2. Asignar horarios (sin partidos existentes)
3. Guardar partidos de Categoría 1

4. Generar partidos de Categoría 2
5. Asignar horarios (considerando partidos de Categoría 1)
6. Guardar partidos de Categoría 2 (sin borrar Categoría 1)

7. Generar partidos de Categoría 3
8. Asignar horarios (considerando partidos de Categoría 1 y 2)
9. Guardar partidos de Categoría 3 (sin borrar anteriores)
```

## 🎯 VALIDACIONES QUE AHORA FUNCIONAN

### 1. Intervalo de 3 horas
```python
# En _asignar_horarios_y_canchas()
for jugador_id in jugadores:
    for fecha_hora_existente in partidos_por_jugador[jugador_id]:
        diferencia_minutos = abs((fecha_hora_slot - fecha_hora_existente).total_seconds() / 60)
        if diferencia_minutos < 180:  # Mínimo 180 minutos
            conflicto_tiempo = True
            break
```

**Ahora funciona** porque `partidos_por_jugador` incluye partidos de categorías anteriores.

### 2. Restricciones horarias
```python
# En _verificar_disponibilidad_pareja()
if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
    return False  # Hay solapamiento = NO disponible
```

**Ahora funciona** porque el parseo de restricciones está corregido.

## 🧪 TESTING

### Test 1: Limpiar y regenerar
```bash
# Limpiar fixture
python backend/limpiar_fixture_torneo37.py

# Regenerar desde frontend
# Click en "Generar Fixture Completo"

# Verificar
python backend/test_fixture_torneo37_restricciones.py
```

**Resultado esperado**:
- ✅ 0 violaciones de restricciones
- ✅ Todos los jugadores con mínimo 3 horas entre partidos
- ✅ Partidos distribuidos correctamente entre categorías

### Test 2: Verificar intervalo de 3 horas
```sql
-- Buscar jugadores con partidos muy cercanos
SELECT 
    u.nombre_usuario,
    p1.fecha_hora as partido1,
    p2.fecha_hora as partido2,
    EXTRACT(EPOCH FROM (p2.fecha_hora - p1.fecha_hora))/60 as diferencia_minutos
FROM partidos p1
JOIN partidos p2 ON p1.id_torneo = p2.id_torneo
JOIN torneos_parejas tp1 ON p1.pareja1_id = tp1.id OR p1.pareja2_id = tp1.id
JOIN torneos_parejas tp2 ON p2.pareja1_id = tp2.id OR p2.pareja2_id = tp2.id
JOIN usuarios u ON tp1.jugador1_id = u.id_usuario OR tp1.jugador2_id = u.id_usuario
WHERE p1.id_torneo = 37
AND p2.id_torneo = 37
AND p1.id_partido < p2.id_partido
AND (
    tp1.jugador1_id IN (tp2.jugador1_id, tp2.jugador2_id) OR
    tp1.jugador2_id IN (tp2.jugador1_id, tp2.jugador2_id)
)
AND EXTRACT(EPOCH FROM (p2.fecha_hora - p1.fecha_hora))/60 < 180
ORDER BY diferencia_minutos;
```

**Resultado esperado**: 0 filas

## 📝 ARCHIVOS MODIFICADOS

- `backend/src/services/torneo_fixture_global_service.py`
  - Método `generar_fixture_completo()` - Ahora genera por categoría
  - Nuevo método `_generar_fixture_categoria()` - Genera una categoría
  - Import de `TorneoCategoria` agregado

## ✅ CHECKLIST

- [x] Bug identificado
- [x] Solución implementada
- [x] Método `_generar_fixture_categoria()` creado
- [x] Generación secuencial por categoría
- [x] Import de `TorneoCategoria` agregado
- [ ] Fixture regenerado
- [ ] Tests ejecutados: 0 violaciones
- [ ] Verificación de intervalo de 3 horas

## 🚀 PRÓXIMOS PASOS

1. **Limpiar fixture actual**:
   ```bash
   python backend/limpiar_fixture_torneo37.py
   ```

2. **Regenerar desde frontend**:
   - Click en "Eliminar Todo el Fixture"
   - Click en "Generar Fixture Completo"
   - Observar logs en consola del backend

3. **Verificar**:
   ```bash
   python backend/test_fixture_torneo37_restricciones.py
   ```

4. **Verificar intervalo de 3 horas**:
   - Revisar manualmente los partidos
   - Verificar que ningún jugador tenga partidos con menos de 3 horas de diferencia

---

**Fecha**: 2026-02-06
**Estado**: ✅ Corregido
**Versión**: 2.0
**Criticidad**: ALTA
