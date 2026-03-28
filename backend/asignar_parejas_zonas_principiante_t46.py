import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ASIGNAR PAREJAS A ZONAS - PRINCIPIANTE T46")
print("=" * 80)

# Mapeo de parejas a zonas
zonas_parejas = {
    400: [1048, 1042, 1041],  # Zona A: Ludueña/Apostolo, Aballay/Ríos, Jatuff/Alcazar
    401: [1043, 1044, 1045],  # Zona B
    402: [1046, 1047, 1049],  # Zona C
    403: [1050, 1051, 1052]   # Zona D
}

try:
    # Verificar si existe columna zona_id en torneos_parejas
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'torneos_parejas' AND column_name = 'zona_id'
    """)
    
    tiene_zona_id = cur.fetchone() is not None
    
    if tiene_zona_id:
        print("\n✅ La tabla torneos_parejas tiene columna zona_id")
        print("\n🔄 Asignando parejas a zonas...")
        
        for zona_id, parejas_ids in zonas_parejas.items():
            # Obtener nombre de zona
            cur.execute("SELECT nombre FROM torneo_zonas WHERE id = %s", (zona_id,))
            zona = cur.fetchone()
            
            if not zona:
                print(f"  ⚠️  Zona {zona_id} no encontrada")
                continue
            
            print(f"\n  {zona['nombre']} (ID: {zona_id}):")
            
            for pareja_id in parejas_ids:
                # Actualizar zona_id
                cur.execute("""
                    UPDATE torneos_parejas
                    SET zona_id = %s
                    WHERE id = %s
                """, (zona_id, pareja_id))
                
                # Obtener nombres
                cur.execute("""
                    SELECT 
                        pu1.nombre || ' ' || pu1.apellido as j1,
                        pu2.nombre || ' ' || pu2.apellido as j2
                    FROM torneos_parejas tp
                    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
                    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
                    WHERE tp.id = %s
                """, (pareja_id,))
                
                pareja = cur.fetchone()
                print(f"    ✅ Pareja {pareja_id}: {pareja['j1']} / {pareja['j2']}")
        
        conn.commit()
        print(f"\n✅ Parejas asignadas a zonas correctamente")
        
    else:
        print("\n⚠️  La tabla torneos_parejas NO tiene columna zona_id")
        print("   Las parejas se asignan a zonas a través de los partidos")
        print("   Usa el botón 'Generar 3ra' en el frontend para crear los partidos")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
