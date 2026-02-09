# Fix: Ranking no muestra partidos ganados ni tendencia

## Problema
En producción, la tabla de rankings mostraba:
- Partidos jugados: 0 (para todos los usuarios)
- Partidos ganados: 0
- % Victoria: 0%
- Tendencia: -- (neutral)

## Causa Raíz
El campo `Usuario.partidos_jugados` NO se estaba actualizando correctamente. Aunque el código en `torneo_resultado_service.py` SÍ actualiza este campo (líneas 655 y 687), los 37 partidos confirmados existentes se guardaron ANTES de que este código existiera o hubo algún problema en el proceso.

## Datos en Producción
- ✅ 37 partidos confirmados
- ✅ 152 registros en historial_rating
- ✅ 46 usuarios tenían partidos_jugados > 0 (desactualizados)
- ❌ El endpoint devolvía `partidos_jugados: 0` para la mayoría

## Solución Aplicada

### 1. Script de Actualización Masiva
**Archivo**: `backend/actualizar_partidos_jugados_usuarios.py`

Actualiza el campo `partidos_jugados` de todos los usuarios basándose en `historial_rating`:

```sql
UPDATE usuarios u
SET partidos_jugados = (
    SELECT COUNT(DISTINCT hr.id_partido)
    FROM historial_rating hr
    JOIN partidos p ON hr.id_partido = p.id_partido
    WHERE hr.id_usuario = u.id_usuario
    AND p.estado IN ('finalizado', 'confirmado')
)
```

**Resultado**:
- ✅ 50 usuarios actualizados
- ✅ Ahora 50 usuarios tienen partidos_jugados > 0 (antes eran 46)

### 2. Fix en el Endpoint de Ranking
**Archivo**: `backend/src/controllers/ranking_controller.py`

Modificado para calcular `partidos_jugados` dinámicamente desde `historial_rating` en lugar de usar el campo de la tabla:

**Cambio 1: Agregar subquery para calcular partidos jugados**
```python
partidos_jugados_subq = (
    db.query(
        HistorialRating.id_usuario,
        func.count(func.distinct(HistorialRating.id_partido)).label("partidos_jugados_real")
    )
    .join(Partido, HistorialRating.id_partido == Partido.id_partido)
    .filter(
        Partido.estado.in_(["finalizado", "confirmado"])
    )
    .group_by(HistorialRating.id_usuario)
    .subquery()
)
```

**Cambio 2: Usar el campo calculado**
```python
# ANTES
Usuario.partidos_jugados,

# DESPUÉS
func.coalesce(partidos_jugados_subq.c.partidos_jugados_real, 0).label("partidos_jugados"),
```

**Cambio 3: Agregar JOIN**
```python
.join(partidos_jugados_subq, Usuario.id_usuario == partidos_jugados_subq.c.id_usuario, isouter=True)
```

## ¿Por qué el campo no se actualizaba?

El código en `torneo_resultado_service.py` SÍ actualiza `usuario.partidos_jugados`:
```python
usuario.partidos_jugados = (usuario.partidos_jugados or 0) + 1
```

Y SÍ hace commit:
```python
db.commit()  # Línea 75
```

**Posibles causas**:
1. Los 37 partidos existentes se guardaron ANTES de que este código existiera
2. Hubo algún error en el proceso que hizo rollback
3. El código se agregó recientemente y los partidos viejos nunca se actualizaron

## Ventajas del Fix Aplicado

### Opción elegida: Cálculo dinámico
- ✅ Siempre sincronizado con `historial_rating`
- ✅ No depende de que el campo se actualice correctamente
- ✅ Funciona incluso si hay errores en el proceso de guardado
- ✅ Más robusto a largo plazo

### Alternativa descartada: Usar campo actualizado
- ❌ Requiere que el campo se actualice siempre correctamente
- ❌ Si falla un commit, el campo queda desactualizado
- ❌ Requiere scripts de sincronización periódicos

## Resultado Esperado

Después del deploy, el endpoint `/ranking/` debería devolver:
```json
{
  "id_usuario": 136,
  "nombre_usuario": "matiasgiordano",
  "rating": 1500,
  "partidos_jugados": 5,       // ← Calculado desde historial_rating
  "partidos_ganados": 5,       // ← Calculado desde historial_rating
  "tendencia": "up"            // ← Calculado desde suma de deltas
}
```

## Pasos para Deploy

1. ✅ Script ejecutado: `actualizar_partidos_jugados_usuarios.py`
2. ✅ Código modificado en `ranking_controller.py`
3. ⏳ Commit y push a Railway
4. ⏳ Verificar en producción: https://drive-plus-production.up.railway.app/ranking/?limit=5
5. ⏳ Limpiar cache del frontend (Ctrl+Shift+R)
6. ⏳ Verificar en https://drive-plus.com.ar/rankings

## Verificación

Ejecutar en producción:
```bash
python backend/test_ranking_produccion.py
```

Debería mostrar usuarios con `partidos_jugados > 0` y `partidos_ganados > 0`.

## Mantenimiento Futuro

El campo `Usuario.partidos_jugados` seguirá actualizándose en cada partido nuevo (el código ya existe), pero el endpoint de ranking NO depende de él. Esto garantiza que:

1. Si el campo se desactualiza, el ranking sigue funcionando
2. No necesitamos scripts de sincronización
3. La fuente de verdad es `historial_rating`
