#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=engine)()

# Buscar partido con Gurgone y Cejas
resultado = s.execute(text("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        tc.nombre as categoria,
        tca.nombre as cancha,
        u1.nombre_usuario as j1_p1,
        u2.nombre_usuario as j2_p1,
        u3.nombre_usuario as j1_p2,
        u4.nombre_usuario as j2_p2
    FROM partidos p
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
    JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
    JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
    JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
    LEFT JOIN torneo_categorias tc ON tp1.categoria_id = tc.id
    LEFT JOIN torneo_canchas tca ON p.cancha_id = tca.id
    WHERE tp1.torneo_id = 45
    AND (
        u1.nombre_usuario LIKE '%gurgone%' OR u2.nombre_usuario LIKE '%gurgone%' 
        OR u3.nombre_usuario LIKE '%gurgone%' OR u4.nombre_usuario LIKE '%gurgone%'
    )
    AND (
        u1.nombre_usuario LIKE '%cejas%' OR u2.nombre_usuario LIKE '%cejas%' 
        OR u3.nombre_usuario LIKE '%cejas%' OR u4.nombre_usuario LIKE '%cejas%'
    )
""")).fetchall()

for r in resultado:
    print(f"Partido #{r.id_partido}")
    print(f"Fecha: {r.fecha_hora}")
    print(f"Categoría: {r.categoria}")
    print(f"Cancha: {r.cancha}")
    print(f"{r.j1_p1} - {r.j2_p1} vs {r.j1_p2} - {r.j2_p2}")
