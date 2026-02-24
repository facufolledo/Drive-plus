"""
Fix completo de migraciones. Para cada usuario migrado:
1. Transferir circuito_puntos_jugador del temp al real
2. Transferir historial_rating del temp al real  
3. Recalcular partidos_jugados del real
4. El rating del real ya tiene los puntos del temp (se copió antes)
5. Los temps 502, 534 ya fueron borrados. 511, 542 también.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# Mapeo: real_id -> temp_id (los temps ya fueron borrados como usuarios,
# pero pueden quedar datos en circuito_puntos_jugador y historial_rating)
MIGRACIONES = [
    (568, 502, "Benjamin Hrellac"),
    (562, 511, "Juan Magi"),
    (564, 542, "Flavio Palacio"),
    (574, 534, "Lucas Mercado Luna"),
]

with engine.connect() as conn:
    for real_id, temp_id, nombre in MIGRACIONES:
        print(f"\n{'=' * 50}")
        print(f"{nombre}: real={real_id}, temp={temp_id}")
        print(f"{'=' * 50}")
        
        # 1. Transferir circuito_puntos_jugador
        puntos_temp = conn.execute(text("""
            SELECT id, circuito_id, torneo_id, categoria_id, fase_alcanzada, puntos
            FROM circuito_puntos_jugador WHERE usuario_id = :tid
        """), {"tid": temp_id}).fetchall()
        
        if puntos_temp:
            for p in puntos_temp:
                print(f"  Circuito puntos temp: id={p[0]}, circuito={p[1]}, torneo={p[2]}, cat={p[3]}, fase={p[4]}, pts={p[5]}")
            
            # Verificar si el real ya tiene puntos para el mismo torneo/circuito
            for p in puntos_temp:
                existing = conn.execute(text("""
                    SELECT id FROM circuito_puntos_jugador 
                    WHERE usuario_id = :rid AND circuito_id = :cid AND torneo_id = :tid AND categoria_id = :cat
                """), {"rid": real_id, "cid": p[1], "tid": p[2], "cat": p[3]}).fetchone()
                
                if existing:
                    print(f"  ⚠️ Real ya tiene puntos para circuito={p[1]}, torneo={p[2]} -> actualizando")
                    conn.execute(text("""
                        UPDATE circuito_puntos_jugador 
                        SET fase_alcanzada = :fase, puntos = :pts
                        WHERE id = :eid
                    """), {"fase": p[4], "pts": p[5], "eid": existing[0]})
                else:
                    # Transferir: cambiar usuario_id del temp al real
                    conn.execute(text("""
                        UPDATE circuito_puntos_jugador SET usuario_id = :rid WHERE id = :pid
                    """), {"rid": real_id, "pid": p[0]})
                    print(f"  ✅ Transferido puntos circuito id={p[0]} -> usuario {real_id}")
        else:
            print(f"  Sin puntos de circuito del temp")
        
        # 2. Transferir historial_rating
        hist_temp = conn.execute(text("""
            SELECT COUNT(*) FROM historial_rating WHERE id_usuario = :tid
        """), {"tid": temp_id}).scalar()
        
        if hist_temp > 0:
            # Verificar si hay conflicto (mismo partido)
            conn.execute(text("""
                UPDATE historial_rating SET id_usuario = :rid WHERE id_usuario = :tid
                AND id_partido NOT IN (SELECT id_partido FROM historial_rating WHERE id_usuario = :rid2)
            """), {"rid": real_id, "tid": temp_id, "rid2": real_id})
            # Borrar los que quedaron duplicados
            conn.execute(text("DELETE FROM historial_rating WHERE id_usuario = :tid"), {"tid": temp_id})
            print(f"  ✅ Historial rating transferido: {hist_temp} registros")
        else:
            print(f"  Sin historial rating del temp")
        
        # 3. Recalcular partidos_jugados
        parejas = conn.execute(text("""
            SELECT id FROM torneos_parejas WHERE jugador1_id = :uid OR jugador2_id = :uid
        """), {"uid": real_id}).fetchall()
        pareja_ids = [p[0] for p in parejas]
        
        if pareja_ids:
            pids_str = ','.join(str(p) for p in pareja_ids)
            total = conn.execute(text(f"""
                SELECT COUNT(*) FROM partidos 
                WHERE estado = 'confirmado'
                  AND (pareja1_id IN ({pids_str}) OR pareja2_id IN ({pids_str}))
            """)).scalar()
            
            conn.execute(text("UPDATE usuarios SET partidos_jugados = :total WHERE id_usuario = :uid"),
                        {"total": total, "uid": real_id})
            print(f"  ✅ partidos_jugados = {total}")
        
        # 4. Verificar estado final
        u = conn.execute(text("""
            SELECT rating, id_categoria, partidos_jugados FROM usuarios WHERE id_usuario = :uid
        """), {"uid": real_id}).fetchone()
        print(f"  Estado final: rating={u[0]}, cat={u[1]}, pj={u[2]}")
        
        # Puntos circuito del real
        puntos_real = conn.execute(text("""
            SELECT circuito_id, torneo_id, categoria_id, fase_alcanzada, puntos
            FROM circuito_puntos_jugador WHERE usuario_id = :uid
        """), {"uid": real_id}).fetchall()
        for p in puntos_real:
            print(f"  Circuito: c={p[0]}, t={p[1]}, cat={p[2]}, fase={p[3]}, pts={p[4]}")
    
    conn.commit()
    
    print("\n" + "=" * 50)
    print("VERIFICACIÓN FINAL")
    print("=" * 50)
    for real_id, temp_id, nombre in MIGRACIONES:
        u = conn.execute(text("""
            SELECT u.rating, u.id_categoria, u.partidos_jugados, p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": real_id}).fetchone()
        
        parejas = conn.execute(text("""
            SELECT COUNT(*) FROM torneos_parejas WHERE jugador1_id = :uid OR jugador2_id = :uid
        """), {"uid": real_id}).scalar()
        
        puntos = conn.execute(text("""
            SELECT COALESCE(SUM(puntos), 0) FROM circuito_puntos_jugador WHERE usuario_id = :uid
        """), {"uid": real_id}).scalar()
        
        # Temp residual?
        temp_exists = conn.execute(text("SELECT COUNT(*) FROM usuarios WHERE id_usuario = :tid"), {"tid": temp_id}).scalar()
        temp_puntos = conn.execute(text("""
            SELECT COUNT(*) FROM circuito_puntos_jugador WHERE usuario_id = :tid
        """), {"tid": temp_id}).scalar()
        temp_hist = conn.execute(text("""
            SELECT COUNT(*) FROM historial_rating WHERE id_usuario = :tid
        """), {"tid": temp_id}).scalar()
        
        print(f"  {nombre} ({real_id}): {u[3]} {u[4]}, rating={u[0]}, cat={u[1]}, pj={u[2]}, parejas={parejas}, pts_circuito={puntos}")
        print(f"    Temp {temp_id}: existe={bool(temp_exists)}, puntos_residuales={temp_puntos}, hist_residual={temp_hist}")
