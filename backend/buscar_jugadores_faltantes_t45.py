#!/usr/bin/env python3
"""
Buscar jugadores que parecen estar en la BD con nombres similares
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

JUGADORES_BUSCAR = [
    'RADOSALDOVICH',
    'LIGORRIA',
    'LISANDRO',
    'COPPEDE'
]

def main():
    s = Session()
    try:
        print("=" * 80)
        print("BUSCAR JUGADORES FALTANTES")
        print("=" * 80)
        
        for nombre in JUGADORES_BUSCAR:
            print(f"\n🔍 Buscando: {nombre}")
            print("-" * 80)
            
            # Buscar por nombre o apellido
            resultados = s.execute(text("""
                SELECT 
                    id_usuario,
                    nombre_usuario,
                    nombre,
                    apellido,
                    rating_actual,
                    tipo_usuario
                FROM usuarios
                WHERE UPPER(nombre_usuario) LIKE :patron
                OR UPPER(nombre) LIKE :patron
                OR UPPER(apellido) LIKE :patron
                ORDER BY rating_actual DESC
            """), {"patron": f"%{nombre}%"}).fetchall()
            
            if resultados:
                print(f"✅ Encontrados {len(resultados)} resultados:")
                for r in resultados:
                    print(f"   ID={r.id_usuario:3d} | {r.nombre_usuario:30s} | {r.nombre} {r.apellido} | Rating={r.rating_actual} | {r.tipo_usuario}")
            else:
                print(f"❌ No se encontró ningún usuario con '{nombre}'")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
