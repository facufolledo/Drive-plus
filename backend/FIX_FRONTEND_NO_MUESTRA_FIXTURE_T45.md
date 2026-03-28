# Fix: Frontend no muestra fixture del Torneo 45

## Problema
El frontend mostraba "Aún no se generó el fixture" aunque los 65 partidos estaban correctamente en la base de datos. Después de arreglar el primer problema, mostraba que el fixture estaba generado pero no listaba ningún partido.

## Causa Raíz (Doble problema)

### Problema 1: Faltaba id_torneo
Los partidos creados manualmente por scripts no tenían el campo `id_torneo` establecido. El endpoint del backend (`GET /torneos/{torneo_id}/partidos`) filtra por `Partido.id_torneo == torneo_id`, por lo que no encontraba ningún partido.

### Problema 2: Faltaba categoria_id
Después de arreglar `id_torneo`, el frontend filtraba por categoría pero los partidos no tenían `categoria_id` establecido, por lo que seguía sin mostrar nada.

```python
# Línea problemática en torneo_controller.py
query = db.query(Partido).filter(Partido.id_torneo == torneo_id)
```

## Diagnóstico

### Paso 1: Verificar id_torneo
```bash
python backend/verificar_id_torneo_partidos_t45.py

# Resultado:
# ❌ 65 partidos SIN id_torneo
# ✅ 0 partidos CON id_torneo
```

### Paso 2: Verificar categoria_id (después de arreglar id_torneo)
```bash
python backend/debug_frontend_partidos_t45.py

# Resultado:
# ✅ 65 partidos CON id_torneo = 45
# ❌ 65 partidos SIN categoria_id
# Frontend filtra por categoría → 0 partidos encontrados
```

## Solución

### Fix 1: Actualizar id_torneo
```sql
UPDATE partidos
SET id_torneo = 45
WHERE id_partido IN (
    SELECT p.id_partido
    FROM partidos p
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    WHERE tp1.torneo_id = 45
    AND p.id_torneo IS NULL
)
```

```bash
python backend/fix_id_torneo_partidos_t45.py
# ✅ Actualizados 65 partidos con id_torneo = 45
```

### Fix 2: Actualizar categoria_id desde las zonas
```sql
UPDATE partidos p
SET categoria_id = tz.categoria_id
FROM torneo_zonas tz
WHERE p.zona_id = tz.id
AND p.id_torneo = 45
AND p.categoria_id IS NULL
```

```bash
python backend/fix_categoria_id_partidos_t45.py
# ✅ Actualizados 65 partidos con categoria_id
# 📊 4ta: 21 partidos
# 📊 6ta: 27 partidos
# 📊 8va: 17 partidos
```

## Estado Final
✅ 65 partidos con `id_torneo = 45`
✅ 65 partidos con `categoria_id` correcto (desde sus zonas)
✅ Endpoint del backend devuelve los 65 partidos
✅ Frontend debería mostrar el fixture completo por categoría

## Lección Aprendida
Al crear partidos manualmente por scripts, SIEMPRE incluir estos campos en el INSERT:

```python
# ❌ MAL - Sin id_torneo ni categoria_id
INSERT INTO partidos (pareja1_id, pareja2_id, zona_id, fecha_hora, ...)

# ✅ BIEN - Con id_torneo y categoria_id
INSERT INTO partidos (
    id_torneo, 
    categoria_id,  -- Obtener desde la zona
    pareja1_id, 
    pareja2_id, 
    zona_id, 
    fecha_hora, 
    ...
)
```

O mejor aún, obtener categoria_id automáticamente:
```python
INSERT INTO partidos (id_torneo, pareja1_id, pareja2_id, zona_id, fecha_hora, ...)
VALUES (
    45,
    pareja1_id,
    pareja2_id,
    zona_id,
    fecha_hora,
    ...
);

-- Luego actualizar categoria_id desde las zonas
UPDATE partidos p
SET categoria_id = tz.categoria_id
FROM torneo_zonas tz
WHERE p.zona_id = tz.id
AND p.categoria_id IS NULL;
```

## Archivos Relacionados
- `backend/verificar_id_torneo_partidos_t45.py` - Diagnóstico id_torneo
- `backend/debug_frontend_partidos_t45.py` - Diagnóstico categoria_id
- `backend/fix_id_torneo_partidos_t45.py` - Fix id_torneo
- `backend/fix_categoria_id_partidos_t45.py` - Fix categoria_id
- `backend/test_endpoint_partidos_t45.py` - Verificación endpoint
- `backend/src/controllers/torneo_controller.py` - Endpoint que filtra por id_torneo
- `frontend/src/components/TorneoFixture.tsx` - Componente que muestra el fixture
