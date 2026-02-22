"""Debug: verificar estado de 4ta en torneo 38 para generar fixture"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

print("=== TORNEO 38 - DEBUG 4ta (cat 87) ===\n")

# Horarios del torneo
t = s.execute(text("SELECT horarios_disponibles, fecha_inicio, fecha_fin FROM torneos WHERE id = 38")).fetchone()
print(f"Fechas: {t[1]} a {t[2]}")
print(f"Horarios disponibles: {t[0]}")

# Canchas
canchas = s.execute(text("SELECT id, nombre, activa FROM torneo_canchas WHERE torneo_id = 38")).fetchall()
print(f"\nCanchas ({len(canchas)}):")
for c in canchas:
    print(f"  ID={c[0]}, {c[1]}, activa={c[2]}")

# Zonas de 4ta
zonas = s.execute(text("SELECT id, nombre, categoria_id FROM torneo_zonas WHERE torneo_id = 38 AND categoria_id = 87")).fetchall()
print(f"\nZonas 4ta ({len(zonas)}):")
for z in zonas:
    print(f"  ID={z[0]}, nombre={z[1]}, cat={z[2]}")

# Parejas en zonas
if zonas:
    for z in zonas:
        pz = s.execute(text("SELECT id, zona_id, pareja_id FROM torneo_zona_parejas WHERE zona_id = :zid"), {"zid": z[0]}).fetchall()
        print(f"  Zona {z[0]} ({z[1]}): {len(pz)} parejas")

# Parejas en 4ta
parejas = s.execute(text(
    "SELECT tp.id, p1.nombre, p1.apellido, p2.nombre, p2.apellido, tp.disponibilidad_horaria "
    "FROM torneos_parejas tp "
    "LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario "
    "LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario "
    "WHERE tp.torneo_id = 38 AND tp.categoria_id = 87 ORDER BY tp.id"
)).fetchall()
print(f"\nParejas 4ta ({len(parejas)}):")
for p in parejas:
    print(f"  Pareja {p[0]}: {p[1]} {p[2]} + {p[3]} {p[4]} | restr: {p[5]}")

# Partidos existentes en torneo 38
partidos = s.execute(text(
    "SELECT id, categoria_id, fase, fecha_hora, cancha_id FROM partidos WHERE id_torneo = 38"
)).fetchall()
print(f"\nPartidos existentes torneo 38: {len(partidos)}")
cats = {}
for p in partidos:
    cats[p[1]] = cats.get(p[1], 0) + 1
for c, n in cats.items():
    print(f"  Cat {c}: {n} partidos")

# Zonas de 6ta
zonas6 = s.execute(text("SELECT id, nombre FROM torneo_zonas WHERE torneo_id = 38 AND categoria_id = 88")).fetchall()
print(f"\nZonas 6ta ({len(zonas6)}):")
for z in zonas6:
    print(f"  ID={z[0]}, {z[1]}")

s.close()
