# Sistema de Categorías Dinámico

## Descripción

El sistema ahora obtiene las categorías directamente de la base de datos, permitiendo agregar, modificar o eliminar categorías sin tocar el código.

## Cómo funciona

### Backend
- **Endpoint**: `GET /categorias`
- **Controller**: `backend/src/controllers/categoria_controller.py`
- Devuelve todas las categorías de la tabla `categorias`

### Frontend
- **Servicio**: `frontend/src/services/categoria.service.ts`
  - Obtiene categorías del backend
  - Implementa caché de 5 minutos
  - Fallback a categorías por defecto si falla la API

- **Hook**: `frontend/src/hooks/useCategorias.ts`
  - Hook React para usar en componentes
  - Funciones útiles:
    - `categorias`: Array de categorías
    - `getCategoriasNombres()`: Array de nombres
    - `getCategoriaByRating(rating)`: Obtiene categoría según rating
    - `refresh()`: Refresca las categorías

## Uso en componentes

```typescript
import { useCategorias } from '../hooks/useCategorias';

function MiComponente() {
  const { categorias, getCategoriasNombres, getCategoriaByRating } = useCategorias();
  
  // Obtener nombres para un select
  const nombres = getCategoriasNombres();
  
  // Obtener categoría por rating
  const categoria = getCategoriaByRating(1500); // "5ta"
  
  return (
    <select>
      {nombres.map(nombre => (
        <option key={nombre} value={nombre}>{nombre}</option>
      ))}
    </select>
  );
}
```

## Componentes actualizados

- ✅ `CompletarPerfil.tsx` - Usa `useCategorias()`
- ⏳ Pendientes de actualizar:
  - `TorneosNuevo.tsx`
  - `RankingCircuito.tsx`
  - `PerfilPublico.tsx`
  - `MiPerfil.tsx`
  - Mobile screens

## Cómo agregar/modificar categorías

### 1. Agregar nueva categoría

```sql
-- Ejemplo: Agregar "2da" categoría
INSERT INTO categorias (nombre, descripcion, rating_min, rating_max, sexo)
VALUES ('2da', 'Segunda categoría élite', 2000, 2199, 'masculino');

-- Ejemplo: Agregar "1ra" categoría
INSERT INTO categorias (nombre, descripcion, rating_min, rating_max, sexo)
VALUES ('1ra', 'Primera categoría profesional', 2200, 9999, 'masculino');
```

### 2. Modificar nombre de categoría existente

```sql
-- Cambiar nombre
UPDATE categorias 
SET nombre = '3ra' 
WHERE id_categoria = 6;

-- Cambiar rangos de rating
UPDATE categorias 
SET rating_min = 1800, rating_max = 1999
WHERE id_categoria = 6;
```

### 3. Eliminar categoría

```sql
-- CUIDADO: Asegúrate de que no haya usuarios con esta categoría
DELETE FROM categorias WHERE id_categoria = 10;
```

## El frontend se actualizará automáticamente

- El caché se refresca cada 5 minutos
- O al recargar la página
- O llamando a `refresh()` del hook
- **No necesitas tocar código**, el sistema detecta las nuevas categorías

## Ejemplo completo: Agregar categorías profesionales

```sql
-- Agregar 2da categoría
INSERT INTO categorias (nombre, descripcion, rating_min, rating_max, sexo)
VALUES 
  ('2da', 'Segunda categoría', 2000, 2199, 'masculino'),
  ('1ra', 'Primera categoría', 2200, 9999, 'masculino');

-- Verificar
SELECT * FROM categorias ORDER BY rating_min;
```

Después de ejecutar esto:
1. El endpoint `/categorias` devolverá las nuevas categorías
2. Los filtros en el frontend mostrarán "2da" y "1ra" automáticamente
3. Los usuarios con rating 2000+ se clasificarán en las nuevas categorías

## Ventajas

1. **Flexibilidad**: Cambiar nombres sin tocar código
2. **Escalabilidad**: Agregar categorías fácilmente
3. **Consistencia**: Una sola fuente de verdad (BD)
4. **Mantenibilidad**: Menos código hardcodeado

## Notas importantes

- El sistema mantiene un fallback a categorías por defecto si falla la API
- El caché evita llamadas innecesarias al backend
- Las categorías se ordenan por `rating_min` automáticamente
