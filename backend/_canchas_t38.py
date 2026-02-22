"""Crear 3 canchas para torneo 38: Cancha 5, 6 y 7"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

try:
    # Ver si ya hay canchas
    existentes = s.execute(text(
        "SELECT id, nombre, activa FROM torneo_canchas WHERE torneo_id = 38"
    )).fetchall()
    if existentes:
        print("Canchas existentes en torneo 38:")
        for r in existentes:
            print(f"  ID={r[0]}, nombre={r[1]}, activa={r[2]}")
        print("Eliminando existentes...")
        s.execute(text("DELETE FROM torneo_canchas WHERE torneo_id = 38"))

    # Insertar Cancha 5, 6, 7
    for nombre in ["Cancha 5", "Cancha 6", "Cancha 7"]:
        r = s.execute(text(
            "INSERT INTO torneo_canchas (torneo_id, nombre, activa) VALUES (38, :n, true) RETURNING id"
        ), {"n": nombre})
        cid = r.fetchone()[0]
        print(f"✅ {nombre} creada (ID: {cid})")

    s.commit()

    # Verificar
    final = s.execute(text(
        "SELECT id, nombre, activa FROM torneo_canchas WHERE torneo_id = 38 ORDER BY id"
    )).fetchall()
    print(f"\nCanchas torneo 38:")
    for r in final:
        print(f"  ID={r[0]}, {r[1]}, activa={r[2]}")

except Exception as e:
    print(f"❌ Error: {e}")
    s.rollback()
finally:
    s.close()
