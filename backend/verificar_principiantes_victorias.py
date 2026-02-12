"""Verificar victorias de jugadores principiantes que aparecen en el ranking"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv('backend/.env')
engine = create_engine(os.getenv('DATABASE_URL'))

# Los jugadores que aparecen en la imagen
jugadores = ['sebastiancorzo', 'sergiopansa', 'carlosfernandez', 'leomena10', 'jorgepaz', 'maximilianoyelamo']

with engine.connect() as conn:
    for username in jugadores:
        result = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.rating,
                   COUNT(DISTINCT hr.id_partido) as partidos,
                   COUNT(*) FILTER (WHERE hr.delta > 0) as victorias,
                   COUNT(*) FILTER (WHERE hr.delta < 0) as derrotas
            FROM usuarios u
            LEFT JOIN historial_rating hr ON u.id_usuario = hr.id_usuario
            LEFT JOIN partidos p ON hr.id_partido = p.id_partido AND p.estado IN ('finalizado', 'confirmado')
            WHERE u.nombre_usuario = :username
            GROUP BY u.id_usuario, u.nombre_usuario, u.rating
        """), {"username": username})
        
        row = result.fetchone()
        if row:
            print(f"{row[1]} (ID:{row[0]}) Rating:{row[2]} | {row[3]} partidos | {row[4]}V {row[5]}D")
        else:
            print(f"{username}: NO ENCONTRADO")

    # Ahora verificar qué devuelve el endpoint para estos jugadores
    print("\n--- Verificando endpoint de producción ---")
    import requests
    response = requests.get("https://drive-plus-production.up.railway.app/ranking/?limit=100")
    data = response.json()
    
    for j in data:
        if j.get('nombre_usuario') in jugadores:
            print(f"{j['nombre_usuario']}: partidos_jugados={j.get('partidos_jugados')}, partidos_ganados={j.get('partidos_ganados')}, tendencia={j.get('tendencia')}")
