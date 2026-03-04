-- Verificar Dario Barrionuevo
SELECT 
    u.id_usuario,
    p.nombre,
    p.apellido,
    u.rating as rating_actual,
    c.nombre as categoria,
    (SELECT SUM(delta) FROM historial_rating WHERE id_usuario = u.id_usuario) as suma_deltas,
    (SELECT rating_antes FROM historial_rating h 
     JOIN partidos pt ON h.id_partido = pt.id_partido 
     WHERE h.id_usuario = u.id_usuario 
     ORDER BY pt.fecha ASC LIMIT 1) as primer_rating_historial
FROM usuarios u
JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
LEFT JOIN categorias c ON u.id_categoria = c.id_categoria
WHERE p.nombre ILIKE 'Dario' AND p.apellido ILIKE 'Barrionuevo';

-- Ver historial completo
SELECT 
    h.id_partido,
    h.delta,
    h.rating_antes,
    h.rating_despues,
    p.fecha
FROM historial_rating h
JOIN partidos p ON h.id_partido = p.id_partido
JOIN usuarios u ON h.id_usuario = u.id_usuario
JOIN perfil_usuarios pf ON u.id_usuario = pf.id_usuario
WHERE pf.nombre ILIKE 'Dario' AND pf.apellido ILIKE 'Barrionuevo'
ORDER BY p.fecha ASC;
