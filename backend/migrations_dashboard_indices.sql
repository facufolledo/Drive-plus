-- Índices para optimizar el Dashboard
-- Ejecutar en producción para mejorar performance

-- 1. Índice compuesto para últimos partidos del usuario (CRÍTICO)
CREATE INDEX IF NOT EXISTS idx_partido_jugadores_usuario_partido 
ON partido_jugadores (id_usuario, id_partido DESC);

-- 2. Índice para delta semanal (historial de rating) (CRÍTICO)
-- Nota: La tabla historial_rating usa 'creado_en' no 'fecha'
CREATE INDEX IF NOT EXISTS idx_historial_rating_usuario_fecha 
ON historial_rating (id_usuario, creado_en DESC);

-- 3. Índice compuesto para historial por partido y usuario
CREATE INDEX IF NOT EXISTS idx_historial_rating_partido_usuario 
ON historial_rating (id_partido, id_usuario);

-- 4. Índice para top jugadores por sexo y rating (CRÍTICO)
-- Nota: Asegurarse que sexo esté normalizado (M/F) para máxima performance
CREATE INDEX IF NOT EXISTS idx_usuarios_sexo_rating 
ON usuarios (sexo, rating DESC);

-- 5. Índice para perfil_usuarios (si no existe como FK)
CREATE INDEX IF NOT EXISTS idx_perfil_usuarios_id 
ON perfil_usuarios (id_usuario);

-- 6. Índice para partidos por fecha (CRÍTICO para ordenar)
CREATE INDEX IF NOT EXISTS idx_partidos_fecha 
ON partidos (fecha DESC);

-- 7. CONSTRAINTS DE UNICIDAD para evitar duplicados
-- NOTA: Estos constraints ya existen en la base de datos
-- Si necesitas crearlos en una DB nueva, descomenta las siguientes líneas:

-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (
--         SELECT 1 FROM pg_constraint 
--         WHERE conname = 'uq_historial_rating_partido_usuario'
--     ) THEN
--         ALTER TABLE partido_jugadores 
--         ADD CONSTRAINT uq_historial_rating_partido_usuario 
--         UNIQUE (id_partido, id_usuario);
--     END IF;
-- END $$;

-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (
--         SELECT 1 FROM pg_constraint 
--         WHERE conname = 'uq_historial_rating_partido_usuario_2'
--     ) THEN
--         ALTER TABLE historial_rating 
--         ADD CONSTRAINT uq_historial_rating_partido_usuario_2 
--         UNIQUE (id_partido, id_usuario);
--     END IF;
-- END $$;

-- Verificar índices creados
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('partido_jugadores', 'historial_rating', 'usuarios', 'perfil_usuarios', 'partidos')
ORDER BY tablename, indexname;

-- Verificar constraints creados
SELECT 
    conname as constraint_name,
    conrelid::regclass as table_name,
    contype as constraint_type
FROM pg_constraint
WHERE conname IN ('uq_partido_jugadores_partido_usuario', 'uq_historial_rating_partido_usuario');
