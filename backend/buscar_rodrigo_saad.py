"""
Buscar todas las cuentas relacionadas con Rodrigo Saad
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Usuario, PerfilUsuario
from src.models.torneo_models import TorneoPareja

load_dotenv()

def buscar_rodrigo():
    """Busca todas las cuentas relacionadas con Rodrigo Saad"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 BÚSQUEDA: RODRIGO SAAD")
        print("="*80 + "\n")
        
        # Buscar por diferentes variaciones
        print("1️⃣ Buscando por 'rodrigo'...")
        rodrigos = db.query(Usuario).filter(Usuario.nombre_usuario.ilike('%rodrigo%')).all()
        print(f"   Encontrados: {len(rodrigos)}")
        for u in rodrigos:
            print(f"   • ID: {u.id_usuario} | Username: {u.nombre_usuario} | Email: {u.email} | Rating: {u.rating}")
        
        print("\n2️⃣ Buscando por 'saad'...")
        saads = db.query(Usuario).filter(Usuario.nombre_usuario.ilike('%saad%')).all()
        print(f"   Encontrados: {len(saads)}")
        for u in saads:
            print(f"   • ID: {u.id_usuario} | Username: {u.nombre_usuario} | Email: {u.email} | Rating: {u.rating}")
        
        print("\n3️⃣ Buscando parejas en torneo 37 con 'facundo' (compañero de Rodrigo)...")
        # Buscar a Facundo Folledo primero
        facundo = db.query(Usuario).filter(Usuario.nombre_usuario.ilike('%facundo%folledo%')).first()
        if not facundo:
            facundo = db.query(Usuario).filter(Usuario.nombre_usuario.ilike('%folledo%')).first()
        
        if facundo:
            print(f"   Facundo encontrado: {facundo.nombre_usuario} (ID: {facundo.id_usuario})")
            
            # Buscar su pareja en el torneo 37
            pareja = db.query(TorneoPareja).filter(
                TorneoPareja.torneo_id == 37,
                ((TorneoPareja.jugador1_id == facundo.id_usuario) | (TorneoPareja.jugador2_id == facundo.id_usuario))
            ).first()
            
            if pareja:
                companero_id = pareja.jugador2_id if pareja.jugador1_id == facundo.id_usuario else pareja.jugador1_id
                companero = db.query(Usuario).filter(Usuario.id_usuario == companero_id).first()
                
                if companero:
                    print(f"   Compañero: {companero.nombre_usuario} (ID: {companero.id_usuario})")
                    print(f"   Email: {companero.email}")
                    print(f"   Rating: {companero.rating}")
                    print(f"   Partidos: {companero.partidos_jugados}")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    buscar_rodrigo()
