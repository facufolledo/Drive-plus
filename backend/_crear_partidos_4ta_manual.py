"""Crear partidos manuales de 4ta torneo 38 - Zonas B, C, E
Ya se cambiaron las zonas desde la app, solo falta crear los partidos con horarios específicos.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

TORNEO_ID = 38
CATEGORIA_ID = 87  # 4ta

try:
    # 1. Verificar zonas actuales y parejas
    print("=== ZONAS ACTUALES 4ta (cat 87) ===\n")
    zonas = s.execute(text(
        "SELECT z.id, z.nombre FROM torneo_zonas z WHERE z.torneo_id = 38 AND z.categoria_id = 87 ORDER BY z.nombre"
    )).fetchall()
    
    for zona in zonas:
        print(f"Zona {zona[1]} (ID {zona[0]}):")
        parejas = s.execute(text(
            "SELECT zp.pareja_id, p1.nombre, p1.apellido, p2.nombre, p2.apellido "
            "FROM torneo_zona_parejas zp "
            "JOIN torneos_parejas tp ON zp.pareja_id = tp.id "
            "LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario "
            "LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario "
            "WHERE zp.zona_id = :zid"
        ), {"zid": zona[0]}).fetchall()
        for p in parejas:
            print(f"  Pareja {p[0]}: {p[1]} {p[2]} / {p[3]} {p[4]}")
    
    # 2. Verificar partidos existentes de 4ta
    partidos_existentes = s.execute(text(
        "SELECT id_partido, pareja1_id, pareja2_id, fecha_hora, cancha_id, zona_id "
        "FROM partidos WHERE id_torneo = 38 AND categoria_id = 87 AND fase = 'zona'"
    )).fetchall()
    print(f"\nPartidos existentes 4ta: {len(partidos_existentes)}")
    for p in partidos_existentes:
        print(f"  Partido {p[0]}: P{p[1]} vs P{p[2]} - {p[3]} cancha {p[4]} zona {p[5]}")

    # 3. Canchas
    canchas = s.execute(text(
        "SELECT id, nombre FROM torneo_canchas WHERE torneo_id = 38 ORDER BY id"
    )).fetchall()
    print(f"\nCanchas:")
    for c in canchas:
        print(f"  ID={c[0]}, {c[1]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
finally:
    s.close()
