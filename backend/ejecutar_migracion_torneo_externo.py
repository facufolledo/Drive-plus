"""
Script para ejecutar la migración que permite torneos externos (torneo_id NULL)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.production'))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: Variable DATABASE_URL no encontrada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def main():
    print("=" * 80)
    print("MIGRACIÓN: Permitir torneos externos (torneo_id NULL)")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        try:
            # 1. Permitir NULL en torneo_id
            print("1. Permitiendo NULL en torneo_id...")
            conn.execute(text("""
                ALTER TABLE circuito_puntos_jugador 
                    ALTER COLUMN torneo_id DROP NOT NULL
            """))
            conn.commit()
            print("   ✅ torneo_id ahora acepta NULL")
            print()
            
        except Exception as e:
            if "does not exist" in str(e).lower() or "no existe" in str(e).lower():
                print("   ⚠️  La columna ya permite NULL")
            else:
                print(f"   ⚠️  {e}")
            conn.rollback()
        
        try:
            # 2. Permitir NULL en categoria_id (para torneos externos)
            print("2. Permitiendo NULL en categoria_id...")
            conn.execute(text("""
                ALTER TABLE circuito_puntos_jugador 
                    ALTER COLUMN categoria_id DROP NOT NULL
            """))
            conn.commit()
            print("   ✅ categoria_id ahora acepta NULL")
            print()
            
        except Exception as e:
            if "does not exist" in str(e).lower():
                print("   ⚠️  La columna ya permite NULL")
            else:
                print(f"   ⚠️  {e}")
            conn.rollback()
        
        try:
            # 3. Agregar columna torneo_externo
            print("3. Agregando columna torneo_externo...")
            conn.execute(text("""
                ALTER TABLE circuito_puntos_jugador 
                    ADD COLUMN IF NOT EXISTS torneo_externo VARCHAR(100)
            """))
            conn.commit()
            print("   ✅ Columna torneo_externo agregada")
            print()
            
        except Exception as e:
            print(f"   ⚠️  {e}")
            conn.rollback()
        
        try:
            # 4. Agregar columna categoria_nombre (para torneos externos)
            print("4. Agregando columna categoria_nombre...")
            conn.execute(text("""
                ALTER TABLE circuito_puntos_jugador 
                    ADD COLUMN IF NOT EXISTS categoria_nombre VARCHAR(50)
            """))
            conn.commit()
            print("   ✅ Columna categoria_nombre agregada")
            print()
            
        except Exception as e:
            print(f"   ⚠️  {e}")
            conn.rollback()
        
        try:
            # 5. Eliminar índice único anterior
            print("5. Actualizando índices únicos...")
            conn.execute(text("""
                DROP INDEX IF EXISTS idx_circuito_puntos_jugador_unique
            """))
            conn.commit()
            print("   ✅ Índice anterior eliminado")
            
        except Exception as e:
            print(f"   ⚠️  {e}")
            conn.rollback()
        
        try:
            # 6. Crear índice único para torneos con ID
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_circuito_puntos_jugador_unique_con_torneo
                    ON circuito_puntos_jugador(circuito_id, torneo_id, categoria_id, usuario_id)
                    WHERE torneo_id IS NOT NULL
            """))
            conn.commit()
            print("   ✅ Índice único para torneos con ID creado")
            
        except Exception as e:
            print(f"   ⚠️  {e}")
            conn.rollback()
        
        try:
            # 7. Crear índice único para torneos externos
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_circuito_puntos_jugador_unique_externo
                    ON circuito_puntos_jugador(circuito_id, torneo_externo, categoria_nombre, usuario_id)
                    WHERE torneo_id IS NULL AND torneo_externo IS NOT NULL
            """))
            conn.commit()
            print("   ✅ Índice único para torneos externos creado")
            print()
            
        except Exception as e:
            print(f"   ⚠️  {e}")
            conn.rollback()
        
        print("=" * 80)
        print("✅ MIGRACIÓN COMPLETADA")
        print("=" * 80)
        print()
        print("Ahora puedes ejecutar: python asignar_puntos_torneo_zf_7ma.py")

if __name__ == "__main__":
    main()
