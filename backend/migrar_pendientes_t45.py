#!/usr/bin/env python3
"""
Migrar los 4 usuarios pendientes que tienen historial de rating
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

# Usuarios pendientes
PENDIENTES = [
    (551, 195, "Tiago Córdoba"),
    (510, 863, "Kevin Gurgone"),
    (493, 801, "Mario Santander"),
    (193, 838, "Agustin Chumbita"),
]

def migrar_usuario(session, origen_id, destino_id, nombre):
    """Migra todas las referencias de origen_id a destino_id"""
    try:
        print(f"\n🔄 Migrando: {nombre}")
        print(f"   Origen: {origen_id} -> Destino: {destino_id}")
        
        # 1. Actualizar torneos_parejas
        result = session.execute(text("""
            UPDATE torneos_parejas 
            SET jugador1_id = :dest 
            WHERE jugador1_id = :orig
        """), {"orig": origen_id, "dest": destino_id})
        print(f"   ✅ Parejas jugador1: {result.rowcount} actualizadas")
        
        result = session.execute(text("""
            UPDATE torneos_parejas 
            SET jugador2_id = :dest 
            WHERE jugador2_id = :orig
        """), {"orig": origen_id, "dest": destino_id})
        print(f"   ✅ Parejas jugador2: {result.rowcount} actualizadas")
        
        # 2. Actualizar historial_rating
        result = session.execute(text("""
            UPDATE historial_rating 
            SET id_usuario = :dest 
            WHERE id_usuario = :orig
        """), {"orig": origen_id, "dest": destino_id})
        print(f"   ✅ Historial rating: {result.rowcount} actualizados")
        
        # 3. Eliminar usuario origen
        session.execute(text("""
            DELETE FROM perfil_usuarios WHERE id_usuario = :orig
        """), {"orig": origen_id})
        print(f"   ✅ Perfil eliminado")
        
        session.execute(text("""
            DELETE FROM usuarios WHERE id_usuario = :orig
        """), {"orig": origen_id})
        print(f"   ✅ Usuario eliminado")
        
        session.commit()
        print(f"   ✅ Migración completada")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   ❌ Error: {e}")
        return False

def main():
    s = Session()
    try:
        print("=" * 80)
        print("MIGRAR USUARIOS PENDIENTES CON HISTORIAL")
        print("=" * 80)
        
        exitosos = 0
        fallidos = 0
        
        for origen, destino, nombre in PENDIENTES:
            if migrar_usuario(s, origen, destino, nombre):
                exitosos += 1
            else:
                fallidos += 1
        
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"✅ Exitosos: {exitosos}")
        print(f"❌ Fallidos: {fallidos}")
        print(f"📊 Total: {len(PENDIENTES)}")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
