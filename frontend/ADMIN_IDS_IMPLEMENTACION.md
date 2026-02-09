# Implementación de IDs para Administradores

## Objetivo
Mostrar IDs de entidades (usuarios, parejas, partidos, torneos, salas) solo para usuarios con `es_administrador=true` en la base de datos.

## Componente Creado

### `AdminBadge.tsx`
Componente reutilizable que muestra IDs solo para administradores:

```typescript
// Badge completo con label
<AdminBadge id={123} label="Partido" />
// Resultado: "Partido:123" (solo visible para admins)

// ID inline compacto
<AdminId id={123} prefix="U" />
// Resultado: "U123" (solo visible para admins)
```

## Componentes Modificados

### ✅ Completados

1. **MiPerfil.tsx**
   - IDs de partidos (prefijo "P")
   - IDs de usuarios en historial (prefijo "U")

2. **PerfilPublico.tsx**
   - IDs de partidos (prefijo "P")
   - IDs de usuarios en historial (prefijo "U")

3. **TorneoFixture.tsx**
   - IDs de partidos (prefijo "P")
   - IDs de parejas (prefijo "PA")

4. **TorneoBracket.tsx**
   - IDs de parejas en playoffs (prefijo "PA")

5. **Rankings.tsx** (Tabla General de Ranking)
   - IDs de usuarios en vista desktop (prefijo "U")
   - IDs de usuarios en vista móvil (prefijo "U")

### ⚠️ Pendientes

- **TorneoZonas.tsx**: Import agregado pero NO implementado en la tabla
- **Salas**: Agregar IDs de sala donde corresponda
- **Torneos**: Agregar IDs de torneo en headers

## Prefijos Usados

- `P` = Partido
- `U` = Usuario
- `PA` = Pareja
- `T` = Torneo (pendiente)
- `S` = Sala (pendiente)

## Problema Detectado: Ranking sin Datos

### Síntoma
La tabla de rankings muestra:
- Partidos ganados: 0
- % Victoria: 0%
- Tendencia: -- (neutral)

### Causa Probable
El backend SÍ devuelve los datos correctamente (`partidos_ganados` y `tendencia`), pero:
1. El backend no está corriendo en local
2. El frontend tiene datos cacheados viejos
3. Los datos en la BD están vacíos (no hay partidos confirmados)

### Solución
1. Iniciar el backend: `cd backend && .\venv\Scripts\Activate.ps1 && uvicorn main:app --reload`
2. Limpiar cache del navegador (Ctrl+Shift+R)
3. Verificar que existan partidos confirmados en la BD

### Endpoint del Backend
El endpoint `/ranking/` devuelve:
```json
{
  "id_usuario": 123,
  "nombre_usuario": "usuario",
  "rating": 1500,
  "partidos_jugados": 10,
  "partidos_ganados": 6,
  "tendencia": "up",
  ...
}
```

## Cómo Probar

1. Asegurarse de que tu usuario tenga `es_administrador=true` en la BD
2. Iniciar sesión en la aplicación
3. Navegar a cualquier página con IDs implementados
4. Los IDs deberían aparecer en gris oscuro junto a los elementos

## Notas Técnicas

- El componente usa `useAuth()` para verificar `usuario?.es_administrador`
- Los IDs son pequeños (9px) y discretos para no interferir con el diseño
- Usan fuente monoespaciada para mejor legibilidad
- Color: `text-gray-400` para que no distraigan

## Scripts de Verificación

- `backend/verificar_datos_ranking.py`: Verifica datos en la BD
- `backend/test_ranking_endpoint.py`: Prueba el endpoint de ranking
