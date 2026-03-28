-- Migración: Permitir torneo_id NULL para torneos externos
-- Esto permite registrar puntos de torneos jugados fuera de la app

-- 1. Eliminar la constraint NOT NULL de torneo_id
ALTER TABLE circuito_puntos_jugador 
    ALTER COLUMN torneo_id DROP NOT NULL;

-- 2. Modificar el índice único para manejar NULL
-- Primero eliminar el índice existente
DROP INDEX IF EXISTS idx_circuito_puntos_jugador_unique;

-- Crear nuevo índice que maneje NULL correctamente
-- En PostgreSQL, NULL != NULL, así que necesitamos un índice parcial
CREATE UNIQUE INDEX idx_circuito_puntos_jugador_unique_con_torneo
    ON circuito_puntos_jugador(circuito_id, torneo_id, categoria_id, usuario_id)
    WHERE torneo_id IS NOT NULL;

-- Para torneos externos (torneo_id NULL), necesitamos identificarlos de otra forma
-- Usaremos un campo adicional para el nombre del torneo externo
ALTER TABLE circuito_puntos_jugador 
    ADD COLUMN IF NOT EXISTS torneo_externo VARCHAR(100);

-- Índice único para torneos externos
CREATE UNIQUE INDEX idx_circuito_puntos_jugador_unique_externo
    ON circuito_puntos_jugador(circuito_id, torneo_externo, categoria_id, usuario_id)
    WHERE torneo_id IS NULL AND torneo_externo IS NOT NULL;
