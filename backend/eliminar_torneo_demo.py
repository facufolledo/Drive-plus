#!/usr/bin/env python3
"""
Eliminar torneo demo (ID 41) y los 120 usuarios ficticios.
Ejecutar: .\venv\Scripts\python.exe eliminar_torneo_demo.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 41

def eliminar():
    s = Session()
    try:
        t = s.execute(text("SELECT nombre FROM torneos WHERE id = :t"), {"t": TORNEO_ID}).fetchone()
        if not t:
            print(f"❌ Torneo {TORNEO_ID} no existe")
            return
        print(f"🗑️  Eliminando: {t[0]} (ID: {TORNEO_ID})")

        # Partidos del torneo (si se generó fixture)
        r = s.execute(text("DELETE FROM partido_jugadores WHERE id_partido IN (SELECT id_partido FROM partidos WHERE id_torneo = :t)"), {"t": TORNEO_ID})
        print(f"   partido_jugadores: {r.rowcount}")
        r = s.execute(text("DELETE FROM resultados_partidos WHERE id_partido IN (SELECT id_partido FROM partidos WHERE id_torneo = :t)"), {"t": TORNEO_ID})
        print(f"   resultados_partidos: {r.rowcount}")
        r = s.execute(text("DELETE FROM partidos WHERE id_torneo = :t"), {"t": TORNEO_ID})
        print(f"   partidos: {r.rowcount}")

        # Zonas
        r = s.execute(text("DELETE FROM torneo_zona_parejas WHERE zona_id IN (SELECT id FROM torneo_zonas WHERE torneo_id = :t)"), {"t": TORNEO_ID})
        print(f"   zona_parejas: {r.rowcount}")
        r = s.execute(text("DELETE FROM torneo_tabla_posiciones WHERE zona_id IN (SELECT id FROM torneo_zonas WHERE torneo_id = :t)"), {"t": TORNEO_ID})
        print(f"   tabla_posiciones: {r.rowcount}")
        r = s.execute(text("DELETE FROM torneo_zonas WHERE torneo_id = :t"), {"t": TORNEO_ID})
        print(f"   zonas: {r.rowcount}")

        # Slots
        r = s.execute(text("DELETE FROM torneo_slots WHERE torneo_id = :t"), {"t": TORNEO_ID})
        print(f"   slots: {r.rowcount}")

        # Parejas, canchas, categorías, torneo
        r = s.execute(text("DELETE FROM torneos_parejas WHERE torneo_id = :t"), {"t": TORNEO_ID})
        print(f"   parejas: {r.rowcount}")
        r = s.execute(text("DELETE FROM torneo_canchas WHERE torneo_id = :t"), {"t": TORNEO_ID})
        print(f"   canchas: {r.rowcount}")
        r = s.execute(text("DELETE FROM torneo_categorias WHERE torneo_id = :t"), {"t": TORNEO_ID})
        print(f"   categorías: {r.rowcount}")
        r = s.execute(text("DELETE FROM torneos WHERE id = :t"), {"t": TORNEO_ID})
        print(f"   torneo: {r.rowcount}")
        s.commit()

        # Usuarios demo en batch
        s.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')"))
        r = s.execute(text("DELETE FROM usuarios WHERE email LIKE 'demo%@demo.com'"))
        s.commit()
        print(f"   usuarios demo: {r.rowcount}")

        if os.path.exists("demo_torneo_ids.json"):
            os.remove("demo_torneo_ids.json")

        print("\n✅ Todo eliminado")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
        s.rollback()
    finally:
        s.close()

if __name__ == "__main__":
    eliminar()
