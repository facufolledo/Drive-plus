-- Migración: Sistema de puntos por fase para circuitos
-- Reemplaza el sistema de ELO por puntos fijos según la fase alcanzada

-- 1. Tabla de configuración de puntos por fase (configurable por circuito)
CREATE TABLE IF NOT EXISTS circuito_puntos_fase (
    id BIGSERIAL PRIMARY KEY,
    circuito_id BIGINT REFERENCES circuitos(id) ON DELETE CASCADE NOT NULL,
    fase VARCHAR(20) NOT NULL,  -- 'campeon', 'subcampeon', 'semis', 'cuartos', 'zona'
    puntos INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_circuito_puntos_fase_circuito ON circuito_puntos_fase(circuito_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_circuito_puntos_fase_unique ON circuito_puntos_fase(circuito_id, fase);

-- 2. Tabla de puntos ganados por jugador en cada torneo
CREATE TABLE IF NOT EXISTS circuito_puntos_jugador (
    id BIGSERIAL PRIMARY KEY,
    circuito_id BIGINT REFERENCES circuitos(id) ON DELETE CASCADE NOT NULL,
    torneo_id BIGINT REFERENCES torneos(id) ON DELETE CASCADE NOT NULL,
    categoria_id BIGINT REFERENCES torneo_categorias(id) ON DELETE CASCADE NOT NULL,
    usuario_id BIGINT REFERENCES usuarios(id_usuario) ON DELETE CASCADE NOT NULL,
    fase_alcanzada VARCHAR(20) NOT NULL,  -- 'campeon', 'subcampeon', 'semis', 'cuartos', 'zona'
    puntos INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_circuito_puntos_jugador_circuito ON circuito_puntos_jugador(circuito_id);
CREATE INDEX IF NOT EXISTS idx_circuito_puntos_jugador_usuario ON circuito_puntos_jugador(usuario_id);
CREATE INDEX IF NOT EXISTS idx_circuito_puntos_jugador_torneo ON circuito_puntos_jugador(torneo_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_circuito_puntos_jugador_unique 
    ON circuito_puntos_jugador(circuito_id, torneo_id, categoria_id, usuario_id);

-- 3. Insertar puntos por defecto para el circuito "zf" (Zona Fitness)
-- Primero obtener el ID del circuito
INSERT INTO circuito_puntos_fase (circuito_id, fase, puntos)
SELECT c.id, fase.fase, fase.puntos
FROM circuitos c
CROSS JOIN (VALUES 
    ('campeon', 1000),
    ('subcampeon', 800),
    ('semis', 600),
    ('cuartos', 400),
    ('zona', 100)
) AS fase(fase, puntos)
WHERE c.codigo = 'zf'
ON CONFLICT (circuito_id, fase) DO UPDATE SET puntos = EXCLUDED.puntos;
