-- Migración: Sistema de Circuitos / Ranking por Torneo
-- Fecha: 2026-02-12

-- 1. Agregar columna codigo a torneos (si no existe)
ALTER TABLE torneos ADD COLUMN IF NOT EXISTS codigo VARCHAR(20);
CREATE INDEX IF NOT EXISTS idx_torneos_codigo ON torneos(codigo);

-- 2. Crear tabla de circuitos
CREATE TABLE IF NOT EXISTS circuitos (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    logo_url TEXT,
    activo BOOLEAN DEFAULT TRUE,
    creado_por BIGINT REFERENCES usuarios(id_usuario),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_circuitos_codigo ON circuitos(codigo);
CREATE INDEX IF NOT EXISTS idx_circuitos_activo ON circuitos(activo);
