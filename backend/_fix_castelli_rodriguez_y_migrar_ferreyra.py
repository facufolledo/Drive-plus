"""
1. Migrar Álvaro Ferreyra (TEMP 532 -> REAL 243)
2. Corregir rating de Castelli (6) y Rodríguez (12): 
   - Deben tener rating promedio de 8va - lo que perdieron en P445
   - Primero diagnosticar estado actual
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # ============================================================
    # DIAGNÓSTICO
    # ============================================================
    print("=" * 60)
    print("DIAGNÓSTICO")
    print("=" * 60)
    
    # Rating promedio de 8va (cat 89)
    avg = c.execute(text("""
        SELECT AVG(u.rating)::int
        FROM (
            SELECT jugador1_id as uid FROM torneos_parejas WHERE torneo_id = 38 AND categoria_id = 89
            UNION
            SELECT jugador2_id as uid FROM torneos_parejas WHERE torneo_id = 38 AND categoria_id = 89
        ) j
        JOIN usuarios u ON j.uid = u.id_usuario
    """)).fetchone()[0]
    print(f"  Rating promedio 8va: {avg}")
    
    # Estado actual de Castelli y Rodríguez
    for uid, nombre in [(6, "Matías Castelli"), (12, "Santiago Rodríguez")]:
        u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        hr = c.execute(text("""
            SELECT id_historial, id_partido, rating_antes, delta, rating_despues
            FROM historial_rating WHERE id_usuario = :uid ORDER BY creado_en
        """), {"uid": uid}).fetchall()
        print(f"\n  {nombre} (ID {uid}): rating={u[0]}, pj={u[1]}")
        for h in hr:
            print(f"    historial #{h[0]}: P{h[1]} {h[2]} + ({h[3]}) = {h[4]}")
    
    # P445 info
    p445 = c.execute(text("""
        SELECT pareja1_id, pareja2_id, ganador_pareja_id, elo_aplicado
        FROM partidos WHERE id_partido = 445
    """)).fetchone()
    print(f"\n  P445: p1={p445[0]}, p2={p445[1]}, ganador={p445[2]}, elo_aplicado={p445[3]}")
    
    # Álvaro Ferreyra temp y real
    for uid, label in [(532, "TEMP"), (243, "REAL")]:
        u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        p = c.execute(text("SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        print(f"\n  Álvaro Ferreyra {label} (ID {uid}): {p[0]} {p[1]}, rating={u[0]}, pj={u[1]}")
    
    # En qué pareja está el temp 532
    parejas_532 = c.execute(text("""
        SELECT tp.id, tp.categoria_id, tcat.nombre, tp.jugador1_id, tp.jugador2_id
        FROM torneos_parejas tp
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE tp.torneo_id = 38 AND (tp.jugador1_id = 532 OR tp.jugador2_id = 532)
    """)).fetchall()
    for p in parejas_532:
        print(f"    Pareja {p[0]} en {p[2]} (j1={p[3]}, j2={p[4]})")

    print()
    input_continue = True  # cambiar a False para solo diagnosticar

    if input_continue:
        # ============================================================
        # 1. MIGRAR ÁLVARO FERREYRA (532 -> 243)
        # ============================================================
        print("=" * 60)
        print("1. MIGRAR ÁLVARO FERREYRA (532 -> 243)")
        print("=" * 60)
        
        # Actualizar torneos_parejas
        r1 = c.execute(text("UPDATE torneos_parejas SET jugador1_id = 243 WHERE jugador1_id = 532 AND torneo_id = 38"), {}).rowcount
        r2 = c.execute(text("UPDATE torneos_parejas SET jugador2_id = 243 WHERE jugador2_id = 532 AND torneo_id = 38"), {}).rowcount
        print(f"  torneos_parejas: {r1+r2} actualizadas")
        
        # Actualizar historial_rating (si hay)
        r3 = c.execute(text("UPDATE historial_rating SET id_usuario = 243 WHERE id_usuario = 532"), {}).rowcount
        print(f"  historial_rating: {r3} registros migrados")
        
        # NO sobreescribir rating del real (243 tiene 249, temp tiene 1299)
        # El real tiene rating 249 que es bajo, pero el temp tenía 1299 de 8va
        # Dejamos el rating del real como está (249) ya que no ha jugado partidos
        print(f"  Rating de real (243) NO modificado (mantiene su rating actual)")
        
        print("  ✅ Álvaro Ferreyra migrado")

        # ============================================================
        # 2. CORREGIR CASTELLI Y RODRÍGUEZ
        # ============================================================
        print(f"\n{'=' * 60}")
        print("2. CORREGIR CASTELLI Y RODRÍGUEZ (rating 8va)")
        print("=" * 60)
        
        # Calcular rating promedio de 8va EXCLUYENDO a Castelli y Rodríguez
        avg_8va = c.execute(text("""
            SELECT AVG(u.rating)::int
            FROM (
                SELECT jugador1_id as uid FROM torneos_parejas WHERE torneo_id = 38 AND categoria_id = 89
                UNION
                SELECT jugador2_id as uid FROM torneos_parejas WHERE torneo_id = 38 AND categoria_id = 89
            ) j
            JOIN usuarios u ON j.uid = u.id_usuario
            WHERE j.uid NOT IN (6, 12)
        """)).fetchone()[0]
        print(f"  Rating promedio 8va (sin ellos): {avg_8va}")
        
        # Ellos perdieron P445, el delta fue -15
        # Queremos: rating_base = avg_8va, luego aplicar la pérdida
        # rating_antes debería ser avg_8va, rating_despues = avg_8va + delta
        for uid, nombre in [(6, "Matías Castelli"), (12, "Santiago Rodríguez")]:
            hr = c.execute(text("""
                SELECT id_historial, delta FROM historial_rating 
                WHERE id_usuario = :uid AND id_partido = 445
            """), {"uid": uid}).fetchone()
            
            delta = hr[1] if hr else 0
            nuevo_rating = avg_8va + delta
            
            # Actualizar historial
            c.execute(text("""
                UPDATE historial_rating 
                SET rating_antes = :antes, rating_despues = :despues
                WHERE id_usuario = :uid AND id_partido = 445
            """), {"antes": avg_8va, "despues": nuevo_rating, "uid": uid})
            
            # Actualizar rating del usuario
            c.execute(text("UPDATE usuarios SET rating = :r WHERE id_usuario = :uid"), {"r": nuevo_rating, "uid": uid})
            
            print(f"  {nombre} (ID {uid}): rating_antes={avg_8va}, delta={delta}, rating={nuevo_rating}")
        
        c.commit()
        print("\n✅ Todo aplicado")
        
        # Verificación final
        print(f"\n{'=' * 60}")
        print("VERIFICACIÓN FINAL")
        print("=" * 60)
        for uid, nombre in [(6, "Matías Castelli"), (12, "Santiago Rodríguez"), (243, "Álvaro Ferreyra")]:
            u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
            print(f"  {nombre} (ID {uid}): rating={u[0]}, pj={u[1]}")
