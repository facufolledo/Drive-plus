-- Índices para optimizar el Dashboard
-- Ejecutar en producción para mejorar performance

-- 1. Índice compuesto para últimos partidos del usuario (CRÍTICO)
CREATE INDEX IF NOT EXISTS idx_partido_jugador_usuario_partido 
ON partido_jugador (id_usuario, id_partido DESC);

-- 2. Índice para delta semanal (historial de rating) (CRÍTICO)
CREATE INDEX IF NOT EXISTS idx_historial_rating_usuario_fecha 
ON historial_rating (id_usuario, fecha DESC);

-- 3. Índice compuesto para historial por partido y usuario
CREATE INDEX IF NOT EXISTS idx_historial_rating_partido_usuario 
ON historial_rating (id_partido, id_usuario);

-- 4. Índice para top jugadores por sexo y rating (CRÍTICO)
-- Nota: Asegurarse que sexo esté normalizado (M/F) para máxima performance
CREATE INDEX IF NOT EXISTS idx_usuario_sexo_rating 
ON usuario (sexo, rating DESC);

-- 5. Índice para perfil_usuario (si no existe como FK)
CREATE INDEX IF NOT EXISTS idx_perfil_usuario_id 
ON perfil_usuario (id_usuario);

-- 6. Índice para partidos por fecha (CRÍTICO para ordenar)
CREATE INDEX IF NOT EXISTS idx_partido_fecha 
ON partido (fecha DESC);

-- 7. CONSTRAINTS DE UNICIDAD para evitar duplicados
-- Asegurar que no haya duplicados en partido_jugador
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_partido_jugador_partido_usuario'
    ) THEN
        ALTER TABLE partido_jugador 
        ADD CONSTRAINT uq_partido_jugador_partido_usuario 
        UNIQUE (id_partido, id_usuario);
    END IF;
END $$;

-- Asegurar que no haya duplicados en historial_rating
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_historial_rating_partido_usuario'
    ) THEN
        ALTER TABLE historial_rating 
        ADD CONSTRAINT uq_historial_rating_partido_usuario 
        UNIQUE (id_partido, id_usuario);
    END IF;
END $$;

-- Verificar índices creados
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('partido_jugador', 'historial_rating', 'usuario', 'perfil_usuario', 'partido')
ORDER BY tablename, indexname;

-- Verificar constraints creados
SELECT 
    conname as constraint_name,
    conrelid::regclass as table_name,
    contype as constraint_type
FROM pg_constraint
WHERE conname IN ('uq_partido_jugador_partido_usuario', 'uq_historial_rating_partido_usuario');
