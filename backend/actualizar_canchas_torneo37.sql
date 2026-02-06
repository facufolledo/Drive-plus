-- Actualizar canchas del torneo 37 - Solo 2 canchas techadas disponibles
-- Desactivar canchas 3, 4 y 5

UPDATE torneo_canchas
SET activa = false
WHERE torneo_id = 37
AND nombre IN ('Cancha 3', 'Cancha 4', 'Cancha 5');

-- Verificar estado
SELECT id, nombre, activa, torneo_id
FROM torneo_canchas
WHERE torneo_id = 37
ORDER BY nombre;
