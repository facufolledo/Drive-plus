"""
Corregir rating y partidos_jugados de TODOS los usuarios
basándose en historial_rating (para rating) y conteo real de partidos confirmados.
NO requiere input interactivo.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from sqlalchemy import text


def main():
    db = SessionLocal()
    try:
        print("=" * 80)
        print("🔧 CORRECCIÓN AUTOMÁTICA DE RATINGS Y PARTIDOS")
        print("=" * 80)
        
        # 1. Corregir rating basándose en el último historial_rating
        print("\n📊 Paso 1: Corrigiendo ratings...")
        
        resultado_rating = db.execute(text("""
            WITH ultimo_historial AS (
                SELECT DISTINCT ON (id_usuario) 
                    id_usuario,
                    rating_despues
                FROM historial_rating
                ORDER BY id_usuario, creado_en DESC
            )
            UPDATE usuarios u
            SET rating = uh.rating_despues
            FROM ultimo_historial uh
            WHERE u.id_usuario = uh.id_usuario
              AND u.rating != uh.rating_despues
            RETURNING u.id_usuario
        """))
        
        ids_rating = resultado_rating.fetchall()
        print(f"   ✅ {len(ids_rating)} usuarios con rating corregido")
        
        # Mostrar detalle de los corregidos
        if ids_rating:
            ids_list = [r[0] for r in ids_rating]
            detalle = db.execute(text("""
                SELECT u.id_usuario, p.nombre, p.apellido, u.rating
                FROM usuarios u
                JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
                WHERE u.id_usuario = ANY(:ids)
                ORDER BY p.apellido
            """), {"ids": ids_list}).fetchall()
            
            for d in detalle:
                print(f"      {d[1]} {d[2]} (ID {d[0]}): rating → {d[3]}")
        
        # 2. Corregir partidos_jugados basándose en historial_rating
        # (usamos historial_rating porque partido_jugadores puede estar vacío)
        print("\n📊 Paso 2: Corrigiendo partidos_jugados...")
        
        resultado_partidos = db.execute(text("""
            WITH conteo_partidos AS (
                SELECT id_usuario, COUNT(*) as total
                FROM historial_rating
                GROUP BY id_usuario
            )
            UPDATE usuarios u
            SET partidos_jugados = cp.total
            FROM conteo_partidos cp
            WHERE u.id_usuario = cp.id_usuario
              AND u.partidos_jugados != cp.total
            RETURNING u.id_usuario
        """))
        
        ids_partidos = resultado_partidos.fetchall()
        print(f"   ✅ {len(ids_partidos)} usuarios con partidos_jugados corregido")
        
        if ids_partidos:
            ids_list = [r[0] for r in ids_partidos]
            detalle = db.execute(text("""
                SELECT u.id_usuario, p.nombre, p.apellido, u.partidos_jugados
                FROM usuarios u
                JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
                WHERE u.id_usuario = ANY(:ids)
                ORDER BY p.apellido
            """), {"ids": ids_list}).fetchall()
            
            for d in detalle:
                print(f"      {d[1]} {d[2]} (ID {d[0]}): partidos → {d[3]}")
        
        db.commit()
        
        # 3. Verificar Damián Tapia específicamente
        print("\n" + "=" * 80)
        print("🔍 VERIFICACIÓN: Damián Tapia")
        print("=" * 80)
        
        tapia = db.execute(text("""
            SELECT u.id_usuario, u.rating, u.partidos_jugados, p.nombre, p.apellido
            FROM usuarios u
            JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.apellido) LIKE '%tapia%' AND LOWER(p.nombre) LIKE '%damian%'
        """)).fetchone()
        
        if tapia:
            print(f"   ID: {tapia[0]}")
            print(f"   Rating: {tapia[1]}")
            print(f"   Partidos: {tapia[2]}")
            print(f"   ✅ Corregido!")
        
        # 4. Verificar otros usuarios migrados
        print("\n" + "=" * 80)
        print("🔍 VERIFICACIÓN: Otros usuarios migrados")
        print("=" * 80)
        
        migrados = db.execute(text("""
            SELECT u.id_usuario, u.rating, u.partidos_jugados, p.nombre, p.apellido, u.email
            FROM usuarios u
            JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.email IN (
                'damian.tapia04@gmail.com',
                'coppedejoaco@gmail.com', 
                'delafuenteemilio4@gmail.com',
                'jerevera97@gmail.com',
                'rodrisaad88@gmail.com',
                'fernanda.ferplast@gmail.com',
                'matis61190@gmail.com',
                'martinalejandrosanchez27@gmail.com',
                'facundo_g10@hotmail.com',
                'leandroruarte695@gmail.com'
            )
            ORDER BY p.apellido
        """)).fetchall()
        
        for m in migrados:
            print(f"   {m[3]} {m[4]} (ID {m[0]}): rating={m[1]}, partidos={m[2]}")
        
        print(f"\n✅ Corrección completada!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
