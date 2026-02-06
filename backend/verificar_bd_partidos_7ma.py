"""
Script para verificar exactamente qué hay en la BD
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import text
from src.database.config import get_db

load_dotenv()

def verificar_bd():
    """Verifica los datos exactos en la BD"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 VERIFICAR BD - PARTIDOS 7MA")
        print("="*80 + "\n")
        
        # Query directo a la BD
        query = text("""
            SELECT 
                id_partido,
                pareja1_id,
                pareja2_id,
                zona_id,
                cancha_id,
                fecha_hora AT TIME ZONE 'UTC' as fecha_utc,
                fecha_hora AT TIME ZONE 'America/Argentina/Buenos_Aires' as fecha_arg
            FROM partidos
            WHERE id_torneo = 37 AND categoria_id = 85
            ORDER BY fecha_hora
        """)
        
        result = db.execute(query)
        partidos = result.fetchall()
        
        print(f"Total partidos: {len(partidos)}\n")
        print("ID | Pareja1 vs Pareja2 | Zona | Cancha | Fecha UTC | Fecha ARG")
        print("-" * 100)
        
        for p in partidos:
            print(f"{p[0]:3} | {p[1]:3} vs {p[2]:3} | {p[3] if p[3] else 'None':4} | {p[4]:2} | {p[5]} | {p[6]}")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_bd()
