#!/usr/bin/env python3
"""
Ejecutar migraciones de usuarios duplicados del torneo 45
Criterio: TEMP->FIREBASE (usar Firebase), TEMP->TEMP (usar mayor rating)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

# Migraciones a ejecutar (origen -> destino)
MIGRACIONES = [
    # TEMP -> FIREBASE
    (855, 67, "Carlos Gudiño"),
    (829, 228, "Jere Vera"),
    (845, 88, "Ignacio Villegas"),
    
    # TEMP -> TEMP (usar mayor rating)
    (195, 551, "Tiago Córdoba - usar 195 (rating 1499 > 709)"),  # Invertir
    (863, 510, "Kevin Gurgone - usar 863 (rating 1899 > 1812)"),  # Mantener
    (841, 865, "Juan Magui - usar 865 (rating 1899 > 1699)"),  # Invertir
    (768, 814, "Axel Nieto - usar 814 (rating 1699 > 1299)"),  # Invertir
    (852, 864, "Matias Olivera - usar 864 (rating 1899 > 1699)"),  # Invertir
    (801, 493, "Mario Santander - usar 801 (rating 1299 > 1269)"),  # Mantener
    (868, 767, "Suarez Suarez - usar 868 (rating 1899 > 1299)"),  # Mantener
    (838, 193, "Agustin Chumbita - usar 838 (rating 1699 > 1510)"),  # Mantener
]

# Ajustar según rating
MIGRACIONES_AJUSTADAS = [
    (855, 67, "Carlos Gudiño"),
    (829, 228, "Jere Vera"),
    (845, 88, "Ignacio Villegas"),
    (551, 195, "Tiago Córdoba"),  # Invertido
    (510, 863, "Kevin Gurgone"),  # Invertido
    (841, 865, "Juan Magui"),
    (768, 814, "Axel Nieto"),
    (852, 864, "Matias Olivera"),
    (493, 801, "Mario Santander"),  # Invertido
    (767, 868, "Suarez Suarez"),  # Invertido
    (193, 838, "Agustin Chumbita"),  # Invertido
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
        print("EJECUTAR MIGRACIONES - USUARIOS DUPLICADOS T45")
        print("=" * 80)
        
        exitosos = 0
        fallidos = 0
        
        for origen, destino, nombre in MIGRACIONES_AJUSTADAS:
            if migrar_usuario(s, origen, destino, nombre):
                exitosos += 1
            else:
                fallidos += 1
        
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"✅ Exitosos: {exitosos}")
        print(f"❌ Fallidos: {fallidos}")
        print(f"📊 Total: {len(MIGRACIONES_AJUSTADAS)}")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
