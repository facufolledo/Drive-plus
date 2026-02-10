# Optimización Endpoint Zonas/Tablas

## Problema
El endpoint `/torneos/{torneo_id}/zonas/tablas` tardaba mucho en cargar, especialmente en torneos con múltiples categorías y zonas (como el torneo 37).

## Causa
**Problema de N+1 queries**: El endpoint hacía un loop por cada zona llamando a `obtener_tabla_posiciones`, y cada llamada ejecutaba múltiples queries a la base de datos.

Para un torneo con 3 categorías y múltiples zonas, esto resultaba en decenas de queries individuales.

## Solución Implementada

### Batch Loading
Reescrito el endpoint completo para cargar todos los datos en batch:

1. **Una query** para todas las asignaciones de parejas a zonas
2. **Una query** para todas las parejas involucradas
3. **Una query** para todos los partidos confirmados de las zonas
4. **Una query** para todos los usuarios y perfiles
5. **Procesamiento en memoria** de estadísticas y ordenamiento

### Código Optimizado
```python
# Antes: Loop con N queries
for zona in zonas:
    tabla = TorneoZonaService.obtener_tabla_posiciones(db, zona.id)  # Query por zona
    # Más queries dentro de obtener_tabla_posiciones

# Después: Batch loading
asignaciones = db.query(TorneoZonaPareja).filter(
    TorneoZonaPareja.zona_id.in_(zonas_ids)
).all()  # UNA query para todas las zonas

parejas = db.query(TorneoPareja).filter(
    TorneoPareja.id.in_(parejas_ids)
).all()  # UNA query para todas las parejas

partidos = db.query(Partido).filter(
    Partido.id_torneo == torneo_id,
    Partido.zona_id.in_(zonas_ids),
    Partido.estado == 'confirmado'
).all()  # UNA query para todos los partidos

# Procesamiento en memoria
```

## Resultado
- **Reducción drástica** de queries a la base de datos
- **Carga mucho más rápida** del tab "Zonas" en torneos
- **Escalable** para torneos con muchas categorías y zonas

## Archivo Modificado
- `backend/src/controllers/torneo_controller.py` (líneas 1357-1580)

## Deploy
- Commit: `dfb3ee9`
- Push a Railway: Completado
- Deploy automático en progreso
