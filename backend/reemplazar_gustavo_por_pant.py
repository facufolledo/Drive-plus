import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def reemplazar_gustavo_por_pant():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("REEMPLAZAR: Gustavo Millicay por Pant Millicay")
    print("=" * 80)
    
    # IDs conocidos
    gustavo_id = 5
    pant_id = 79
    
    # Buscar pareja de Gustavo Millicay en Torneo 45
    cur.execute("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tc.nombre as categoria
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        WHERE tp.torneo_id = 45
        AND (tp.jugador1_id = %s OR tp.jugador2_id = %s)
    """, (gustavo_id, gustavo_id))
    
    parejas_gustavo = cur.fetchall()
    
    if parejas_gustavo:
        print(f"\n📋 Parejas de Gustavo Millicay (ID {gustavo_id}) en Torneo 45:")
        for p in parejas_gustavo:
            print(f"   Pareja {p['id']} - {p['categoria']}: {p['jugador1']} / {p['jugador2']}")
            
            # Reemplazar Gustavo por Pant
            if p['jugador1_id'] == gustavo_id:
                cur.execute("""
                    UPDATE torneos_parejas
                    SET jugador1_id = %s
                    WHERE id = %s
                """, (pant_id, p['id']))
                print(f"   ✅ Jugador1 actualizado: Gustavo -> Pant")
            elif p['jugador2_id'] == gustavo_id:
                cur.execute("""
                    UPDATE torneos_parejas
                    SET jugador2_id = %s
                    WHERE id = %s
                """, (pant_id, p['id']))
                print(f"   ✅ Jugador2 actualizado: Gustavo -> Pant")
    else:
        print(f"\n❌ No se encontraron parejas de Gustavo Millicay (ID {gustavo_id}) en Torneo 45")
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
    # Verificar parejas de Pant
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tc.nombre as categoria,
               tz.nombre as zona
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        LEFT JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
        LEFT JOIN torneo_zonas tz ON tzp.zona_id = tz.id
        WHERE tp.torneo_id = 45
        AND (tp.jugador1_id = %s OR tp.jugador2_id = %s)
    """, (pant_id, pant_id))
    
    parejas_pant = cur.fetchall()
    
    if parejas_pant:
        print(f"\n✅ Parejas de Pant Millicay (ID {pant_id}):")
        for p in parejas_pant:
            print(f"   Pareja {p['id']} - {p['zona']} - {p['categoria']}")
            print(f"   {p['jugador1']} / {p['jugador2']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ REEMPLAZO COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    reemplazar_gustavo_por_pant()
