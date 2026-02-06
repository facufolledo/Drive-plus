"""
Script para inscribir pareja Villafañe/Direnzo
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
        # Buscar Villafañe
        villafane = session.execute(
            text("SELECT id_usuario, nombre_usuario, email FROM usuarios WHERE nombre_usuario LIKE '%villafa%' OR email LIKE '%villafa%'")
        ).fetchall()
        
        print("Resultados búsqueda Villafañe:")
        for v in villafane:
            print(f"  ID: {v[0]}, Username: {v[1]}, Email: {v[2]}")
        
        if not villafane:
            print("\n❌ No se encontró a Villafañe")
            return
        
        villafane_id = villafane[0][0]
        
        # Buscar Direnzo
        direnzo = session.execute(
            text("SELECT id_usuario FROM usuarios WHERE email = 'franco.direnzo@driveplus.temp'")
        ).fetchone()
        
        if not direnzo:
            print("\n❌ No se encontró a Direnzo")
            return
        
        direnzo_id = direnzo[0]
        
        print(f"\n✅ Villafañe ID: {villafane_id}")
        print(f"✅ Direnzo ID: {direnzo_id}")
        
        # Obtener categoría Principiante
        cat = session.execute(
            text("SELECT id FROM torneo_categorias WHERE torneo_id = 37 AND nombre = 'Principiante'")
        ).fetchone()
        
        cat_id = cat[0]
        
        # Restricciones: NO viernes 09-17h, NO sábado 09-17h
        restricciones = [
            {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "17:00"},
            {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "17:00"}
        ]
        
        restricciones_json = json.dumps(restricciones)
        
        # Inscribir pareja
        result = session.execute(
            text("""
                INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id, estado, categoria_id, disponibilidad_horaria)
                VALUES (37, :j1, :j2, 'confirmada', :cat_id, CAST(:restricciones AS jsonb))
                RETURNING id
            """),
            {"j1": villafane_id, "j2": direnzo_id, "cat_id": cat_id, "restricciones": restricciones_json}
        )
        
        pareja_id = result.fetchone()[0]
        session.commit()
        
        print(f"\n✅ Pareja Villafañe/Direnzo inscrita (ID: {pareja_id})")
        print(f"   Restricciones: NO viernes 09-17h, NO sábado 09-17h")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    inscribir_pareja()
