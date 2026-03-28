-- Asignar horarios finales a los 4 partidos conflictivos
-- Torneo 46 - Categoria 7ma

-- Partido 1044: Sabado 16:00
UPDATE partidos 
SET fecha_hora = '2026-03-29 16:00:00'
WHERE id_partido = 1044;

-- Partido 1045: Sabado 17:00
UPDATE partidos 
SET fecha_hora = '2026-03-29 17:00:00'
WHERE id_partido = 1045;

-- Partido 1046: Viernes 23:59
UPDATE partidos 
SET fecha_hora = '2026-03-28 23:59:00'
WHERE id_partido = 1046;

-- Partido 1052: Viernes 22:30
UPDATE partidos 
SET fecha_hora = '2026-03-28 22:30:00'
WHERE id_partido = 1052;

-- Verificar
SELECT 
    id_partido,
    fecha_hora,
    'Actualizado' as estado
FROM partidos
WHERE id_partido IN (1044, 1045, 1046, 1052)
ORDER BY fecha_hora;
