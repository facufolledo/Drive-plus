"""
Script para intercambiar los cuartos de final de 7ma en torneo 37
Objetivo: Que Folledo/Barrera (último) vaya arriba para que Barrera vs Millicay en semifinales
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Usar la base de datos de producción en Railway
DATABASE_URL = os.getenv("DATABASE_URL")

# Asegurar que use pg8000 que ya está instalado
if DATABASE_URL and not "pg8000" in DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
    elif DATABASE_URL.startswith("postgresql+psycopg2://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+pg8000://")

print(f"Conectando a: {DATABASE_URL[:50]}...")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def main():
    session = Session()
    
    try:
        # Buscar los partidos de cuartos de 7ma en torneo 37
        partidos = session.execute(text("""
            SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.numero_partido,
                   p1.nombre_pareja as pareja1_nombre,
                   p2.nombre_pareja as pareja2_nombre
            FROM partidos p
            LEFT JOIN torneos_parejas p1 ON p.pareja1_id = p1.id
            LEFT JOIN torneos_parejas p2 ON p.pareja2_id = p2.id
            WHERE p.id_torneo = 37
            AND p.fase = 'cuartos'
            AND p1.categoria_id = 2
            ORDER BY p.numero_partido
        """)).fetchall()
        
        print("\n=== PARTIDOS DE CUARTOS ACTUALES ===")
        for i, p in enumerate(partidos):
            print(f"Partido {p.numero_partido} (ID: {p.id_partido}): {p.pareja1_nombre} vs {p.pareja2_nombre}")
        
        if len(partidos) != 4:
            print(f"\n❌ Error: Se esperaban 4 partidos de cuartos, se encontraron {len(partidos)}")
            return
        
        # Identificar los partidos a intercambiar
        # Queremos que Folledo/Barrera (último, índice 3) vaya arriba (posición 0)
        # Y que Giordano/Tapia (primero, índice 0) vaya abajo (posición 3)
        partido_primero = partidos[0]  # Giordano/Tapia (actualmente arriba)
        partido_ultimo = partidos[3]   # Folledo/Barrera (actualmente abajo)
        
        print(f"\n=== INTERCAMBIO A REALIZAR ===")
        print(f"Partido {partido_ultimo.numero_partido} (Folledo/Barrera) → Posición 1 (arriba)")
        print(f"  {partido_ultimo.pareja1_nombre} vs {partido_ultimo.pareja2_nombre}")
        print(f"Partido {partido_primero.numero_partido} (Giordano/Tapia) → Posición 4 (abajo)")
        print(f"  {partido_primero.pareja1_nombre} vs {partido_primero.pareja2_nombre}")
        print(f"\nResultado: Barrera (ganador) vs Millicay (ganador) en semifinales")
        
        confirmar = input("\n¿Confirmar intercambio? (s/n): ")
        if confirmar.lower() != 's':
            print("❌ Operación cancelada")
            return
        
        # Intercambiar los numero_partido
        session.execute(text("""
            UPDATE partidos
            SET numero_partido = :nuevo_numero
            WHERE id_partido = :partido_id
        """), {"nuevo_numero": partido_ultimo.numero_partido, "partido_id": partido_primero.id_partido})
        
        session.execute(text("""
            UPDATE partidos
            SET numero_partido = :nuevo_numero
            WHERE id_partido = :partido_id
        """), {"nuevo_numero": partido_primero.numero_partido, "partido_id": partido_ultimo.id_partido})
        
        session.commit()
        
        print("\n✅ Intercambio realizado exitosamente")
        print("   Folledo/Barrera ahora está arriba")
        print("   Giordano/Tapia ahora está abajo")
        print("   → Barrera vs Millicay en semifinales ✓")
        
        # Verificar el resultado
        partidos_nuevos = session.execute(text("""
            SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.numero_partido,
                   p1.nombre_pareja as pareja1_nombre,
                   p2.nombre_pareja as pareja2_nombre
            FROM partidos p
            LEFT JOIN torneos_parejas p1 ON p.pareja1_id = p1.id
            LEFT JOIN torneos_parejas p2 ON p.pareja2_id = p2.id
            WHERE p.id_torneo = 37
            AND p.fase = 'cuartos'
            AND p1.categoria_id = 2
            ORDER BY p.numero_partido
        """)).fetchall()
        
        print("\n=== PARTIDOS DE CUARTOS DESPUÉS DEL INTERCAMBIO ===")
        for p in partidos_nuevos:
            print(f"Partido {p.numero_partido} (ID: {p.id_partido}): {p.pareja1_nombre} vs {p.pareja2_nombre}")
        
        print("\n✅ Configuración final:")
        print("   Semifinal 1: Ganador de Folledo/Barrera vs Ganador de Millicay/De la Fuente")
        print("   Semifinal 2: Ganador de Molina/Campos vs Ganador de Giordano/Tapia")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    main()
