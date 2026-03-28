#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

s = Session()
zonas = s.execute(text("""
    SELECT tc.nombre as cat, tz.id, tz.nombre as zona
    FROM torneo_zonas tz
    JOIN torneo_categorias tc ON tz.categoria_id = tc.id
    WHERE tc.torneo_id = 45
    ORDER BY tc.nombre, tz.nombre
""")).fetchall()

for z in zonas:
    print(f"{z.cat} - Zona {z.zona} (ID={z.id})")
s.close()
