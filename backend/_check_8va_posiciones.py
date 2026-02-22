"""Ver posiciones de cada zona de 8va T38"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()

zonas = db.execute(text("""
    SELECT id, nombre FROM torneo_zonas
    WHERE torneo_id = 38 AND categoria_id = 89
    ORDER BY numero_orden
""")).fetchall()

for z in zonas:
    zid, zname = z
    # Obtener parejas con partidos ganados/jugados/sets
    result = db.execute(text("""
        WITH pareja_ids AS (
            SELECT DISTINCT x.pid FROM (
                SELECT pareja1_id as pid FROM partidos WHERE zona_id = :zid AND fase = 'zona' AND pareja1_id IS NOT NULL
                UNION
                SELECT pareja2_id as pid FROM partidos WHERE zona_id = :zid AND fase = 'zona' AND pareja2_id IS NOT NULL
            ) x
        ),
        stats AS (
            SELECT pi.pid,
                COUNT(CASE WHEN p.ganador_pareja_id = pi.pid THEN 1 END) as ganados,
                COUNT(CASE WHEN p.estado = 'confirmado' THEN 1 END) as jugados
            FROM pareja_ids pi
            LEFT JOIN partidos p ON (p.pareja1_id = pi.pid OR p.pareja2_id = pi.pid) 
                AND p.zona_id = :zid AND p.fase = 'zona'
            GROUP BY pi.pid
        )
        SELECT s.pid, s.ganados, s.jugados,
               COALESCE(pu1.nombre,'') || ' ' || COALESCE(pu1.apellido,'') || '/' ||
               COALESCE(pu2.nombre,'') || ' ' || COALESCE(pu2.apellido,'')
        FROM stats s
        JOIN torneos_parejas tp ON tp.id = s.pid
        LEFT JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
        LEFT JOIN perfil_usuarios pu1 ON u1.id_usuario = pu1.id_usuario
        LEFT JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON u2.id_usuario = pu2.id_usuario
        ORDER BY s.ganados DESC, s.jugados ASC
    """), {"zid": zid})
    
    print(f"\n{zname}:")
    for idx, r in enumerate(result.fetchall()):
        pid, gan, jug, nombre = r
        print(f"  {idx+1}° Pareja {pid}: {nombre} ({gan}G/{jug}J)")

# Estado de partidos de zona
print("\n=== ESTADO PARTIDOS ZONA ===")
for z in zonas:
    zid, zname = z
    result = db.execute(text("""
        SELECT estado, COUNT(*) FROM partidos
        WHERE zona_id = :zid AND fase = 'zona'
        GROUP BY estado
    """), {"zid": zid})
    print(f"  {zname}: {dict(result.fetchall())}")

db.close()
