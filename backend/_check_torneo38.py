import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=e)()

t = s.execute(text("SELECT id, nombre, estado, fecha_inicio, fecha_fin FROM torneos WHERE id = 38")).fetchone()
if t:
    print(f"Torneo: {t[1]} (estado: {t[2]}, {t[3]} al {t[4]})")
else:
    print("Torneo 38 no existe")
    sys.exit()

print("\nCategorías:")
cats = s.execute(text("SELECT id, nombre, genero, estado FROM torneo_categorias WHERE torneo_id = 38 ORDER BY id")).fetchall()
for c in cats:
    print(f"  ID {c[0]}: {c[1]} ({c[2]}) - {c[3]}")

print("\nParejas actuales:")
parejas = s.execute(text("""
    SELECT tp.id, tc.nombre as cat, u1.nombre_usuario, u2.nombre_usuario, tp.estado
    FROM torneos_parejas tp
    JOIN torneo_categorias tc ON tc.id = tp.categoria_id
    JOIN usuarios u1 ON u1.id_usuario = tp.jugador1_id
    JOIN usuarios u2 ON u2.id_usuario = tp.jugador2_id
    WHERE tp.torneo_id = 38
    ORDER BY tc.nombre, tp.id
""")).fetchall()
for p in parejas:
    print(f"  [{p[1]}] Pareja {p[0]}: {p[2]} / {p[3]} ({p[4]})")
if not parejas:
    print("  (ninguna)")

print(f"\nTotal parejas: {len(parejas)}")
s.close()
