"""Revertir resultado de P440 (cargado por error, todavía no se jugó).
P440: Palma/Tapia (657) vs Ocaña/Millicay (647) - 6-3 6-3 ganó 657
ELO aplicado: Palma 749->789, Tapia 749->789, Ocaña 749->729, Millicay 749->729
Luego P442 aplicó sobre Ocaña/Millicay: 729->709 (delta -20)
Así que al revertir P440, Ocaña/Millicay vuelven de 709 a 709+20=729... NO, 
el rating actual ya incluye ambos deltas. Solo resto el delta de P440.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # 1. Revertir ratings de los 4 jugadores (restar delta de P440)
    hist = c.execute(text("""
        SELECT id_historial, id_usuario, delta FROM historial_rating WHERE id_partido = 440
    """)).fetchall()
    
    print("Revirtiendo ratings:")
    for h in hist:
        # Restar el delta que se sumó
        c.execute(text("UPDATE usuarios SET rating = rating - :delta WHERE id_usuario = :uid"),
                 {"delta": h[2], "uid": h[1]})
        # También restar partidos_jugados
        c.execute(text("UPDATE usuarios SET partidos_jugados = GREATEST(partidos_jugados - 1, 0) WHERE id_usuario = :uid"),
                 {"uid": h[1]})
        
        new_r = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :uid"), {"uid": h[1]}).fetchone()
        nombre = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :uid"), {"uid": h[1]}).fetchone()[0]
        print(f"  {nombre} (ID {h[1]}): delta {h[2]} revertido -> rating={new_r[0]}, partidos={new_r[1]}")
    
    # 2. Actualizar historial_rating de P442 para Ocaña/Millicay (rating_antes debe bajar)
    # P442 hist: Ocaña 729->709, Millicay 729->709
    # Ahora sin P440, antes de P442 tenían 749, no 729
    # Entonces P442 hist debe ser: 749->729 (delta -20)
    for uid in [237, 79]:
        h442 = c.execute(text("""
            SELECT id_historial, rating_antes, delta, rating_despues 
            FROM historial_rating WHERE id_partido = 442 AND id_usuario = :uid
        """), {"uid": uid}).fetchone()
        if h442:
            new_antes = h442[1] + 20  # era 729, ahora 749 (sin el delta de P440)
            new_despues = new_antes + h442[2]  # 749 + (-20) = 729
            c.execute(text("""
                UPDATE historial_rating SET rating_antes = :antes, rating_despues = :despues
                WHERE id_historial = :hid
            """), {"antes": new_antes, "despues": new_despues, "hid": h442[0]})
            nombre = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :uid"), {"uid": uid}).fetchone()[0]
            print(f"  Historial P442 de {nombre}: {h442[1]}->{h442[3]} corregido a {new_antes}->{new_despues}")
    
    # 3. Borrar historial de P440
    deleted = c.execute(text("DELETE FROM historial_rating WHERE id_partido = 440")).rowcount
    print(f"\nHistorial P440 eliminado: {deleted} registros")
    
    # 4. Limpiar P440
    c.execute(text("""
        UPDATE partidos SET estado = 'pendiente', ganador_pareja_id = NULL, 
               resultado_padel = NULL, elo_aplicado = false
        WHERE id_partido = 440
    """))
    print("P440 limpiado: estado=pendiente, sin resultado ni ganador")
    
    c.commit()
    
    # Verificar
    print("\n--- VERIFICACIÓN ---")
    for uid in [544, 545, 237, 79]:
        u = c.execute(text("""
            SELECT u.rating, u.partidos_jugados, pu.nombre || ' ' || pu.apellido
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        print(f"  ID {uid}: {u[2]} rating={u[0]} partidos={u[1]}")
    
    p = c.execute(text("SELECT estado, ganador_pareja_id, resultado_padel, elo_aplicado FROM partidos WHERE id_partido = 440")).fetchone()
    print(f"  P440: estado={p[0]} ganador={p[1]} resultado={p[2]} elo={p[3]}")
