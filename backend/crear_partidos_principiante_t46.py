import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CREAR PARTIDOS PRINCIPIANTE - TORNEO 46")
print("=" * 80)

# Obtener categoría Principiante
cur.execute("""
    SELECT id FROM torneo_categorias
    WHERE torneo_id = 46 AND nombre = 'Principiante'
""")

categoria = cur.fetchone()
categoria_id = categoria['id']

# Configuración de zonas con sus parejas
zonas_parejas = {
    400: [1048, 1042, 1041],  # Zona A
    401: [1043, 1044, 1045],  # Zona B
    402: [1046, 1047, 1049],  # Zona C
    403: [1050, 1051, 1052]   # Zona D
}

print(f"\n📋 CREANDO PARTIDOS PARA 4 ZONAS")

try:
    partidos_creados = 0
    
    for zona_id, parejas in zonas_parejas.items():
        # Obtener nombre de zona
        cur.execute("SELECT nombre FROM torneo_zonas WHERE id = %s", (zona_id,))
        zona_nombre = cur.fetchone()['nombre']
        
        print(f"\n{zona_nombre} (ID: {zona_id}):")
        
        # Crear partidos: todos contra todos (3 parejas = 3 partidos)
        # Pareja 1 vs Pareja 2
        # Pareja 1 vs Pareja 3
        # Pareja 2 vs Pareja 3
        
        partidos_zona = [
            (parejas[0], parejas[1]),
            (parejas[0], parejas[2]),
            (parejas[1], parejas[2])
        ]
        
        for p1_id, p2_id in partidos_zona:
            # Obtener nombres de parejas
            cur.execute("""
                SELECT 
                    pu1.nombre || ' ' || pu1.apellido as j1,
                    pu2.nombre || ' ' || pu2.apellido as j2
                FROM torneos_parejas tp
                JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
                JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
                WHERE tp.id = %s
            """, (p1_id,))
            pareja1 = cur.fetchone()
            
            cur.execute("""
                SELECT 
                    pu1.nombre || ' ' || pu1.apellido as j1,
                    pu2.nombre || ' ' || pu2.apellido as j2
                FROM torneos_parejas tp
                JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
                JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
                WHERE tp.id = %s
            """, (p2_id,))
            pareja2 = cur.fetchone()
            
            # Crear partido (con fecha temporal que se actualizará después)
            cur.execute("""
                INSERT INTO partidos (
                    id_torneo, categoria_id, zona_id, pareja1_id, pareja2_id, estado, fecha, id_creador
                )
                VALUES (46, %s, %s, %s, %s, 'pendiente', '2026-03-28 00:00:00', 1)
                RETURNING id_partido
            """, (categoria_id, zona_id, p1_id, p2_id))
            
            partido_id = cur.fetchone()['id_partido']
            partidos_creados += 1
            
            print(f"  ✅ Partido {partido_id}: P{p1_id} ({pareja1['j1']}/{pareja1['j2']}) vs P{p2_id} ({pareja2['j1']}/{pareja2['j2']})")
    
    conn.commit()
    
    print(f"\n" + "=" * 80)
    print(f"✅ {partidos_creados} PARTIDOS CREADOS EXITOSAMENTE")
    print("=" * 80)
    print(f"\n📊 RESUMEN:")
    print(f"  - 4 zonas de 3 parejas")
    print(f"  - 3 partidos por zona (todos contra todos)")
    print(f"  - Total: {partidos_creados} partidos sin horario")
    print(f"\n⚠️  Los horarios se asignarán después respetando las restricciones")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
