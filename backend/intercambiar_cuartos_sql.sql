-- ============================================================
-- Script para intercambiar cuartos de final de 7ma en torneo 37
-- Folledo/Barrera (último) va arriba, Giordano/Tapia (primero) va abajo
-- ============================================================

-- PASO 1: Ver los partidos actuales (ANTES del cambio)
SELECT 
    p.id_partido, 
    p.numero_partido, 
    p.fase, 
    p.pareja1_id, 
    p.pareja2_id,
    p.resultado_pareja1,
    p.resultado_pareja2
FROM partidos p
WHERE p.id_torneo = 37
AND p.fase = 'cuartos'
ORDER BY p.numero_partido;

-- PASO 2: Intercambiar los numero_partido
-- Partido 1 (primero) <-> Partido 4 (último)

BEGIN;

-- Temporal: poner partido 1 en -1
UPDATE partidos
SET numero_partido = -1
WHERE id_torneo = 37
AND fase = 'cuartos'
AND numero_partido = 1;

-- Partido 4 -> Partido 1
UPDATE partidos
SET numero_partido = 1
WHERE id_torneo = 37
AND fase = 'cuartos'
AND numero_partido = 4;

-- Temporal (-1) -> Partido 4
UPDATE partidos
SET numero_partido = 4
WHERE id_torneo = 37
AND fase = 'cuartos'
AND numero_partido = -1;

COMMIT;

-- PASO 3: Verificar el resultado (DESPUÉS del cambio)
SELECT 
    p.id_partido, 
    p.numero_partido, 
    p.fase, 
    p.pareja1_id, 
    p.pareja2_id,
    p.resultado_pareja1,
    p.resultado_pareja2
FROM partidos p
WHERE p.id_torneo = 37
AND p.fase = 'cuartos'
ORDER BY p.numero_partido;
