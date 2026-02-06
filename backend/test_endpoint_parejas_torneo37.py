"""
Test para verificar qué devuelve el endpoint de parejas del torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_endpoint_parejas():
    session = Session()
    
    try:
        # Simular lo que hace el endpoint GET /torneos/37/parejas
        parejas = session.execute(
            text("""
                SELECT 
                    tp.id,
                    tp.disponibilidad_horaria,
                    u1.nombre_usuario as j1_username,
                    u2.nombre_usuario as j2_username
                FROM torneos_parejas tp
                JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
                WHERE tp.torneo_id = 37
                ORDER BY tp.id
                LIMIT 5
            """)
        ).fetchall()
        
        print("=" * 80)
        print("ENDPOINT GET /torneos/37/parejas - Primeras 5 parejas")
        print("=" * 80)
        
        for p in parejas:
            print(f"\nPareja #{p[0]}")
            print(f"  Jugadores: {p[2]} / {p[3]}")
            print(f"  disponibilidad_horaria en DB:")
            if p[1]:
                print(json.dumps(p[1], indent=4))
            else:
                print("    null")
            
    finally:
        session.close()

if __name__ == "__main__":
    test_endpoint_parejas()
