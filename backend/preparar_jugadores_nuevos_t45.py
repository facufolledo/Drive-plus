#!/usr/bin/env python3
"""
Preparar jugadores nuevos para T45
1. Buscar similares (Radosaldovich, Ligorria)
2. Crear Coppede si no existe
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
        print("PREPARAR JUGADORES NUEVOS - T45")
        print("=" * 80)
        
        # 1. Buscar Radosaldovich
        print("\n1️⃣ Buscando RADOSALDOVICH...")
        rado = s.execute(text("""
            SELECT id_usuario, nombre_usuario, nombre, apellido, rating_actual
            FROM usuarios
            WHERE UPPER(nombre_usuario) LIKE '%RADO%'
            OR UPPER(apellido) LIKE '%RADO%'
            ORDER BY rating_actual DESC
            LIMIT 5
        """)).fetchall()
        
        if rado:
            print("   Encontrados:")
            for r in rado:
                print(f"   ID={r.id_usuario} | {r.nombre_usuario} | {r.nombre} {r.apellido} | Rating={r.rating_actual}")
        else:
            print("   ❌ No encontrado")
        
        # 2. Buscar Ligorria
        print("\n2️⃣ Buscando LIGORRIA LISANDRO...")
        ligorria = s.execute(text("""
            SELECT id_usuario, nombre_usuario, nombre, apellido, rating_actual
            FROM usuarios
            WHERE UPPER(nombre_usuario) LIKE '%LIGORRIA%'
            OR UPPER(nombre_usuario) LIKE '%LISANDRO%'
            OR UPPER(apellido) LIKE '%LIGORRIA%'
            ORDER BY rating_actual DESC
            LIMIT 5
        """)).fetchall()
        
        if ligorria:
            print("   Encontrados:")
            for r in ligorria:
                print(f"   ID={r.id_usuario} | {r.nombre_usuario} | {r.nombre} {r.apellido} | Rating={r.rating_actual}")
        else:
            print("   ❌ No encontrado")
        
        # 3. Buscar Coppede
        print("\n3️⃣ Buscando COPPEDE...")
        coppede = s.execute(text("""
            SELECT id_usuario, nombre_usuario, nombre, apellido, rating_actual
            FROM usuarios
            WHERE UPPER(nombre_usuario) LIKE '%COPPEDE%'
            OR UPPER(apellido) LIKE '%COPPEDE%'
            ORDER BY rating_actual DESC
            LIMIT 5
        """)).fetchall()
        
        if coppede:
            print("   ✅ Ya existe:")
            for r in coppede:
                print(f"   ID={r.id_usuario} | {r.nombre_usuario} | {r.nombre} {r.apellido} | Rating={r.rating_actual}")
        else:
            print("   ❌ No existe, creando...")
            
            # Crear usuario TEMP para Coppede
            # Rating estimado para 4ta categoría: ~1500
            nuevo_id = s.execute(text("""
                INSERT INTO usuarios (
                    nombre_usuario,
                    nombre,
                    apellido,
                    rating_actual,
                    tipo_usuario,
                    partidos_jugados
                )
                VALUES (
                    :username,
                    :nombre,
                    :apellido,
                    :rating,
                    'TEMP',
                    0
                )
                RETURNING id_usuario
            """), {
                "username": "coppede.coppede.4ta.t45",
                "nombre": "Coppede",
                "apellido": "Coppede",
                "rating": 1500
            }).fetchone()
            
            s.commit()
            print(f"   ✅ Usuario creado: ID={nuevo_id.id_usuario}")
            
            # Crear historial inicial
            s.execute(text("""
                INSERT INTO historial_rating (
                    usuario_id,
                    rating_anterior,
                    rating_nuevo,
                    cambio,
                    motivo
                )
                VALUES (
                    :uid,
                    1500,
                    1500,
                    0,
                    'Rating inicial - Torneo 45'
                )
            """), {"uid": nuevo_id.id_usuario})
            
            s.commit()
            print(f"   ✅ Historial creado")
        
        print("\n" + "=" * 80)
        print("✅ PREPARACIÓN COMPLETADA")
        print("=" * 80)
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
