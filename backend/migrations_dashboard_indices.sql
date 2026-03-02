-- Índices para optimizar el Dashboard
-- Ejecutar en producción para mejorar performance

-- 1. Índice para últimos partidos del usuario
CREATE INDEX IF NOT EXISTS idx_partido_jugador_usuario_partido 
ON partido_jugador (id_usuario, id_partido DESC);

-- 2. Índice para delta semanal (historial de rating)
CREATE INDEX IF NOT EXISTS idx_historial_rating_usuario_fecha 
ON historial_rating (id_usuario, fecha DESC);

-- 3. Índice para top jugadores por sexo y rating
CREATE INDEX IF NOT EXISTS idx_usuario_sexo_rating 
ON usuario (sexo, rating DESC);

-- 4. Índice para perfil_usuario (si no existe como FK)
CREATE INDEX IF NOT EXISTS idx_perfil_usuario_id 
ON perfil_usuario (id_usuario);

-- 5. Índice para partidos por fecha (para ordenar correctamente)
CREATE INDEX IF NOT EXISTS idx_partido_fecha 
ON partido (fecha DESC);

-- Verificar índices creados
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('partido_jugador', 'historial_rating', 'usuario', 'perfil_usuario', 'partido')
ORDER BY tablename, indexname;
