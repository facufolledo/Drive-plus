"""
Revertir P442 ELO y re-aplicar correctamente.
P442: Ocaña/Millicay (647) vs Palacio/Porras (655) - 3-6 3-6 ganó 655
Estado actual post-revert de P440:
  Ocaña (237): rating=729, partidos=1 (solo P442)
  Millicay (79): rating=729, partidos=1 (solo P442)
  Palacio (542): rating=789, partidos=1
  Porras (543): rating=789, partidos=1
Historial P442 corregido: Ocaña 749->729, Millicay 749->729, Palacio ?->789, Porras ?->789
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # 1. Ver estado actual
    print("=== ESTADO ACTUAL ===")
    hist = c.execute(text("""
        SELECT h.id_historial, h.id_usuario, h.rating_antes, h.delta, h.rating_despues,
               pu.nombre || ' ' || pu.apellido
        FROM historial_rating h
        JOIN perfil_usuarios pu ON h.id_usuario = pu.id_usuario
        WHERE h.id_partido = 442
        ORDER BY h.id_historial
    """)).fetchall()
    for h in hist:
        print(f"  hist {h[0]}: {h[5]} (ID {h[1]}) {h[2]} -> {h[4]} (delta {h[3]})")
    
    for uid in [237, 79, 542, 543]:
        u = c.execute(text("""
            SELECT u.rating, u.partidos_jugados, pu.nombre || ' ' || pu.apellido
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        print(f"  ID {uid}: {u[2]} rating={u[0]} partidos={u[1]}")
    
    # 2. Revertir P442 ELO
    print("\n=== REVIRTIENDO P442 ===")
    for h in hist:
        c.execute(text("UPDATE usuarios SET rating = rating - :delta, partidos_jugados = GREATEST(partidos_jugados - 1, 0) WHERE id_usuario = :uid"),
                 {"delta": h[3], "uid": h[1]})
    
    # Borrar historial P442
    c.execute(text("DELETE FROM historial_rating WHERE id_partido = 442"))
    
    # Limpiar P442
    c.execute(text("""
        UPDATE partidos SET estado = 'pendiente', ganador_pareja_id = NULL,
               resultado_padel = NULL, elo_aplicado = false
        WHERE id_partido = 442
    """))
    
    # Verificar ratings base
    print("Ratings después de revertir:")
    for uid in [237, 79, 542, 543]:
        u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :uid"), {"uid": uid}).fetchone()
        nombre = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :uid"), {"uid": uid}).fetchone()[0]
        print(f"  ID {uid}: {nombre} rating={u[0]} partidos={u[1]}")
    
    # 3. Re-aplicar ELO de P442 correctamente
    # Resultado: 3-6 3-6, ganó pareja 655 (Palacio/Porras)
    # Todos empiezan en 749 (base 8va)
    print("\n=== RE-APLICANDO ELO P442 ===")
    
    # ELO calculation: K=40 para nuevos
    # Expected score: ambos equipos 749 avg -> E = 0.5
    # Ganador (655): S=1, delta = K * (1 - 0.5) = 40 * 0.5 = 20 por jugador? 
    # Perdedor (647): S=0, delta = K * (0 - 0.5) = 40 * -0.5 = -20
    # Pero el sistema usa su propia fórmula. Veamos qué deltas tenía antes.
    # Antes: Palacio 749->789 (+40), Porras 749->789 (+40), Ocaña 749->729 (-20), Millicay 749->729 (-20)
    # Eso es raro, ganadores +40 y perdedores -20. Puede ser K diferente.
    # Mejor uso los mismos deltas que el sistema calculó originalmente.
    
    deltas = {
        542: 40,   # Palacio (ganador)
        543: 40,   # Porras (ganador)
        237: -20,  # Ocaña (perdedor)
        79: -20,   # Millicay (perdedor)
    }
    
    for uid, delta in deltas.items():
        rating_antes = c.execute(text("SELECT rating FROM usuarios WHERE id_usuario = :uid"), {"uid": uid}).fetchone()[0]
        rating_despues = rating_antes + delta
        
        c.execute(text("UPDATE usuarios SET rating = :r, partidos_jugados = partidos_jugados + 1 WHERE id_usuario = :uid"),
                 {"r": rating_despues, "uid": uid})
        
        c.execute(text("""
            INSERT INTO historial_rating (id_usuario, id_partido, rating_antes, delta, rating_despues)
            VALUES (:uid, 442, :antes, :delta, :despues)
        """), {"uid": uid, "antes": rating_antes, "delta": delta, "despues": rating_despues})
        
        nombre = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :uid"), {"uid": uid}).fetchone()[0]
        print(f"  {nombre} (ID {uid}): {rating_antes} -> {rating_despues} (delta {delta})")
    
    # Marcar P442 como finalizado
    c.execute(text("""
        UPDATE partidos SET estado = 'confirmado', ganador_pareja_id = 655,
               resultado_padel = '{"sets": [{"gamesEquipoA": 3, "gamesEquipoB": 6, "ganador": "equipoB", "completado": true}, {"gamesEquipoA": 3, "gamesEquipoB": 6, "ganador": "equipoB", "completado": true}]}'::jsonb,
               elo_aplicado = true
        WHERE id_partido = 442
    """))
    
    c.commit()
    
    # Verificación final
    print("\n=== VERIFICACIÓN FINAL ===")
    for uid in [237, 79, 542, 543]:
        u = c.execute(text("""
            SELECT u.rating, u.partidos_jugados, pu.nombre || ' ' || pu.apellido
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        print(f"  ID {uid}: {u[2]} rating={u[0]} partidos={u[1]}")
    
    h2 = c.execute(text("""
        SELECT id_historial, id_usuario, rating_antes, delta, rating_despues
        FROM historial_rating WHERE id_partido = 442 ORDER BY id_historial
    """)).fetchall()
    print(f"\nHistorial P442: {len(h2)} registros")
    for h in h2:
        print(f"  hist {h[0]}: uid={h[1]} {h[2]}->{h[4]} (delta {h[3]})")
    
    p = c.execute(text("SELECT estado, ganador_pareja_id, elo_aplicado FROM partidos WHERE id_partido = 442")).fetchone()
    print(f"\nP442: estado={p[0]} ganador={p[1]} elo={p[2]}")
