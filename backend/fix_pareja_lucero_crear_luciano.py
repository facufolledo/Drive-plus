#!/usr/bin/env python3
"""
1. Revertir nombre de Luciano a Rodrigo Paez
2. Crear nuevo usuario Luciano Paez
3. Actualizar pareja 822 para usar Luciano en vez de Rodrigo
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

def main():
    s = Session()
    try:
        print("=" * 80)
        print("FIX PAREJA LUCERO - CREAR LUCIANO PAEZ")
        print("=" * 80)
        
        # 1. Revertir Rodrigo
        print("\n1️⃣ Revirtiendo nombre a Rodrigo Paez...")
        s.execute(text("""
            UPDATE perfil_usuarios
            SET nombre = 'Rodrigo'
            WHERE id_usuario = 160
        """))
        print("   ✅ Rodrigo Paez restaurado (ID=160)")
        
        # 2. Crear Luciano Paez
        print("\n2️⃣ Creando usuario Luciano Paez...")
        
        # Insertar usuario
        result = s.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, rating, password_hash)
            VALUES ('luciano.paez.t45', 'luciano.paez@driveplus.temp', 1299, '')
            RETURNING id_usuario
        """))
        luciano_id = result.fetchone()[0]
        print(f"   ✅ Usuario creado: ID={luciano_id}")
        
        # Insertar perfil
        s.execute(text("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (:uid, 'Luciano', 'Paez')
        """), {"uid": luciano_id})
        print(f"   ✅ Perfil creado")
        
        # 3. Actualizar pareja 822
        print("\n3️⃣ Actualizando pareja 822...")
        
        # Verificar pareja actual
        pareja_antes = s.execute(text("""
            SELECT jugador1_id, jugador2_id
            FROM torneos_parejas
            WHERE id = 822
        """)).fetchone()
        print(f"   Antes: J1={pareja_antes.jugador1_id}, J2={pareja_antes.jugador2_id}")
        
        # Actualizar jugador2 de Rodrigo (160) a Luciano
        s.execute(text("""
            UPDATE torneos_parejas
            SET jugador2_id = :luciano_id
            WHERE id = 822
        """), {"luciano_id": luciano_id})
        
        # Verificar actualización
        pareja_despues = s.execute(text("""
            SELECT tp.jugador1_id, tp.jugador2_id,
                   u1.nombre_usuario as j1_user, p1.nombre as j1_nombre,
                   u2.nombre_usuario as j2_user, p2.nombre as j2_nombre
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios p1 ON u1.id_usuario = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON u2.id_usuario = p2.id_usuario
            WHERE tp.id = 822
        """)).fetchone()
        
        print(f"   Después: J1={pareja_despues.jugador1_id}, J2={pareja_despues.jugador2_id}")
        print(f"   ✅ Pareja actualizada:")
        print(f"      J1: {pareja_despues.j1_nombre} (ID={pareja_despues.jugador1_id}, {pareja_despues.j1_user})")
        print(f"      J2: {pareja_despues.j2_nombre} (ID={pareja_despues.jugador2_id}, {pareja_despues.j2_user})")
        
        s.commit()
        
        print("\n" + "=" * 80)
        print("✅ CORRECCIÓN COMPLETADA")
        print("=" * 80)
        print(f"\nResumen:")
        print(f"  - Rodrigo Paez (ID=160) restaurado")
        print(f"  - Luciano Paez (ID={luciano_id}) creado")
        print(f"  - Pareja 822: Nicolas Lucero + Luciano Paez")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
