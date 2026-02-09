# Fix: Ranking no muestra partidos ganados ni tendencia

## Problema
En producción, la tabla de rankings muestra:
- Partidos jugados: 0 (para todos los usuarios)
- Partidos ganados: 0
- % Victoria: 0%
- Tendencia: -- (neutral)

## Causa
El endpoint `/ranking/` estaba consultando `Usuario.partidos_jugados` directamente, pero ese campo no se actualiza automáticamente. Debería calcular los partidos desde la tabla `historial_rating`.

## Datos en Producción
- ✅ 37 partidos confirmados
- ✅ 152 registros en historial_rating
- ✅ 46 usuarios con partidos jugados
- ❌ El endpoint devolvía `partidos_jugados: 0` para todos

## Solución Aplicada

### Archivo modificado: `backend/src/controllers/ranking_controller.py`

**Cambio 1: Agregar subquery para calcular partidos jugados**
```python
# ANTES: No calculaba partidos jugados
partidos_ganados_subq = (...)

# DESPUÉS: Calcula partidos jugados desde historial_rating
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

**Cambio 2: Usar el campo calculado en lugar del campo de la tabla**
```python
# ANTES: Usaba Usuario.partidos_jugados (siempre 0)
Usuario.partidos_jugados,

# DESPUÉS: Usa el campo calculado desde historial_rating
func.coalesce(partidos_jugados_subq.c.partidos_jugados_real, 0).label("partidos_jugados"),
```

**Cambio 3: Agregar JOIN a la nueva subquery**
```python
.join(partidos_jugados_subq, Usuario.id_usuario == partidos_jugados_subq.c.id_usuario, isouter=True)
```

## Resultado Esperado

Después del deploy, el endpoint `/ranking/` debería devolver:
```json
{
  "id_usuario": 136,
  "nombre_usuario": "matiasgiordano",
  "rating": 1500,
  "partidos_jugados": 6,      // ← Ahora calculado correctamente
  "partidos_ganados": 5,       // ← Ya funcionaba
  "tendencia": "up"            // ← Ya funcionaba
}
```

## Pasos para Deploy

1. ✅ Código modificado en `ranking_controller.py`
2. ⏳ Commit y push a Railway
3. ⏳ Verificar en producción: https://drive-plus-production.up.railway.app/ranking/?limit=5
4. ⏳ Limpiar cache del frontend (Ctrl+Shift+R)
5. ⏳ Verificar en https://drive-plus.com.ar/rankings

## Verificación

Ejecutar en producción:
```bash
python backend/test_ranking_produccion.py
```

Debería mostrar usuarios con `partidos_jugados > 0` y `partidos_ganados > 0`.

## Notas

- El campo `Usuario.partidos_jugados` en la tabla sigue existiendo pero no se usa
- Podríamos actualizarlo con un script batch si queremos mantenerlo sincronizado
- La tendencia ya funcionaba correctamente (se calcula desde `suma_deltas`)
