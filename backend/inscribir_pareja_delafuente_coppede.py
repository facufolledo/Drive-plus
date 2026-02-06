"""
Inscribir pareja Emilio De La Fuente / Joaquín Coppede en torneo 37 - 7ma
Pueden viernes después de las 19h, resto libre
Restricción: viernes 09:00-19:00
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

def inscribir_pareja():
    session = Session()
    
    try:
        print("=" * 80)
        print("INSCRIBIENDO PAREJA: Emilio De La Fuente / Joaquín Coppede")
        print("=" * 80)
        
        # Buscar jugadores
        emilio = session.execute(
            text("SELECT id_usuario, nombre_usuario FROM usuarios WHERE nombre_usuario = 'emiliodelafuente'")
        ).fetchone()
        
        joaquin = session.execute(
            text("SELECT id_usuario, nombre_usuario FROM usuarios WHERE nombre_usuario = 'joaquincoppede'")
        ).fetchone()
        
        if not emilio:
            print("❌ Emilio De La Fuente no encontrado")
            return
        
        if not joaquin:
            print("❌ Joaquín Coppede no encontrado")
            return
        
        print(f"\n✅ Jugadores encontrados:")
        print(f"   Emilio: ID {emilio[0]} (@{emilio[1]})")
        print(f"   Joaquín: ID {joaquin[0]} (@{joaquin[1]})")
        
        # Obtener categoría 7ma del torneo 37
        categoria = session.execute(
            text("""
                SELECT id, nombre 
                FROM torneo_categorias 
                WHERE torneo_id = 37 AND nombre = '7ma'
            """)
        ).fetchone()
        
        if not categoria:
            print("❌ Categoría 7ma no encontrada en torneo 37")
            return
        
        print(f"\n✅ Categoría: {categoria[1]} (ID: {categoria[0]})")
        
        # Restricciones: NO pueden viernes 09:00-19:00
        restricciones = [
            {
                "dias": ["viernes"],
                "horaInicio": "09:00",
                "horaFin": "19:00"
            }
        ]
        
        # Inscribir pareja
        session.execute(
            text("""
                INSERT INTO torneos_parejas 
                (torneo_id, jugador1_id, jugador2_id, categoria_id, estado, disponibilidad_horaria, created_at)
                VALUES (37, :j1_id, :j2_id, :cat_id, 'confirmada', :restricciones, NOW())
            """),
            {
                "j1_id": emilio[0],
                "j2_id": joaquin[0],
                "cat_id": categoria[0],
                "restricciones": json.dumps(restricciones)
            }
        )
        
        session.commit()
        
        # Obtener ID de la pareja creada
        pareja = session.execute(
            text("""
                SELECT id FROM torneos_parejas 
                WHERE torneo_id = 37 
                AND jugador1_id = :j1_id 
                AND jugador2_id = :j2_id
            """),
            {"j1_id": emilio[0], "j2_id": joaquin[0]}
        ).fetchone()
        
        print(f"\n✅ Pareja inscrita exitosamente!")
        print(f"   ID Pareja: {pareja[0]}")
        print(f"   Categoría: 7ma")
        print(f"   Estado: confirmada")
        print(f"\n   Restricciones horarias:")
        print(f"      • Viernes: NO pueden de 09:00 a 19:00")
        print(f"      • Sábado: Disponibles todo el día")
        print(f"      • Domingo: Disponibles todo el día")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    inscribir_pareja()
