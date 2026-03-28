import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("BUSCAR 7MA POR PARTIDOS CON RESULTADOS - T46")
print("=" * 80)

# Buscar partidos de zona con resultados en cada categoría
for cat_id in [125, 126, 127]:
    print(f"\n{'=' * 80}")
    print(f"CATEGORÍA {cat_id}")
    print("=" * 80)
    
    # Ver zonas
    cur.execute("""
        SELECT id, nombre
        FROM torneo_zonas
        WHERE torneo_id = 46 AND categoria_id = %s
        ORDER BY nombre
    """, (cat_id,))
    
    zonas = cur.fetchall()
    print(f"\nZonas: {', '.join([z['nombre'] for z in zonas])}")
    
    # Ver partidos con resultado
    cur.execute("""
        SELECT 
            p.id_partido,
            p.zona_id,
            tz.nombre as zona_nombre,
            p.estado,
            p.ganador_pareja_id,
            p.resultado_padel,
            pu1.nombre || ' ' || pu1.apellido as j1_p1,
            pu2.nombre || ' ' || pu2.apellido as j2_p1,
            pu3.nombre || ' ' || pu3.apellido as j1_p2,
            pu4.nombre || ' ' || pu4.apellido as j2_p2
        FROM partidos p
        JOIN torneo_zonas tz ON p.zona_id = tz.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id_torneo = 46
        AND p.categoria_id = %s
        AND p.fase = 'zona'
        AND p.estado = 'finalizado'
        ORDER BY p.id_partido
        LIMIT 3
    """, (cat_id,))
    
    partidos = cur.fetchall()
    
    print(f"\nPartidos finalizados: {len(partidos)} (mostrando primeros 3)")
    for p in partidos:
        print(f"\n  Partido {p['id_partido']} - {p['zona_nombre']}")
        print(f"    {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")
        if p['resultado_padel']:
            print(f"    Resultado: {p['resultado_padel']}")
        else:
            print(f"    Ganador: Pareja {p['ganador_pareja_id']}")
    
    # Contar total de partidos y finalizados
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN estado = 'finalizado' THEN 1 END) as finalizados
        FROM partidos
        WHERE id_torneo = 46
        AND categoria_id = %s
        AND fase = 'zona'
    """, (cat_id,))
    
    stats = cur.fetchone()
    print(f"\n  Total: {stats['finalizados']}/{stats['total']} partidos finalizados")

print("\n" + "=" * 80)
print("IDENTIFICAR 7MA")
print("=" * 80)
print("\nBasándome en los nombres de jugadores, ¿cuál categoría es 7ma?")

cur.close()
conn.close()
