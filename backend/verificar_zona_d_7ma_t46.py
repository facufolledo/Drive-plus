import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

# Obtener categoria_id de 7ma
cur.execute("""
    SELECT id FROM torneo_categorias 
    WHERE torneo_id = 46 AND nombre = '7ma'
""")
categoria_7ma = cur.fetchone()
categoria_id = categoria_7ma['id']

print(f"Categoría 7ma: ID {categoria_id}\n")

# Ver todas las zonas de 7ma
cur.execute("""
    SELECT id, nombre, numero_orden
    FROM torneo_zonas
    WHERE torneo_id = 46 AND categoria_id = %s
    ORDER BY numero_orden
""", (categoria_id,))

zonas = cur.fetchall()
print(f"Zonas de 7ma: {len(zonas)}")
for z in zonas:
    print(f"  - {z['nombre']} (ID: {z['id']})")

# Ver partidos de Zona D
cur.execute("""
    SELECT 
        z.nombre as zona,
        p.id_partido,
        p.fecha_hora,
        tp1.id as pareja1_id,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        tp2.id as pareja2_id,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2
    FROM partidos p
    JOIN torneo_zonas z ON p.zona_id = z.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46 
    AND p.categoria_id = %s
    AND z.nombre = 'Zona D'
    ORDER BY p.id_partido
""", (categoria_id,))

print("\n\nPartidos de Zona D:")
partidos = cur.fetchall()
for p in partidos:
    fecha = p['fecha_hora'].strftime('%Y-%m-%d %H:%M') if p['fecha_hora'] else 'Sin horario'
    print(f"  Partido {p['id_partido']}: P{p['pareja1_id']} ({p['j1_p1']}/{p['j2_p1']}) vs P{p['pareja2_id']} ({p['j1_p2']}/{p['j2_p2']}) - {fecha}")

# Contar parejas únicas en Zona D
parejas_unicas = set()
for p in partidos:
    parejas_unicas.add(p['pareja1_id'])
    parejas_unicas.add(p['pareja2_id'])

print(f"\nTotal partidos en Zona D: {len(partidos)}")
print(f"Parejas únicas en Zona D: {len(parejas_unicas)}")
print(f"Parejas: {sorted(parejas_unicas)}")

# Si hay 3 parejas, debería haber 3 partidos (todos contra todos)
if len(parejas_unicas) == 3:
    print("\n⚠️  PROBLEMA: Zona D tiene 3 parejas pero debería tener 3 partidos (todos contra todos)")
    print(f"   Actualmente tiene: {len(partidos)} partidos")
    
    # Ver qué partidos faltan
    parejas_list = sorted(parejas_unicas)
    partidos_esperados = [
        (parejas_list[0], parejas_list[1]),
        (parejas_list[0], parejas_list[2]),
        (parejas_list[1], parejas_list[2])
    ]
    
    partidos_existentes = [(p['pareja1_id'], p['pareja2_id']) for p in partidos]
    
    print("\n   Partidos que deberían existir:")
    for p1, p2 in partidos_esperados:
        existe = (p1, p2) in partidos_existentes or (p2, p1) in partidos_existentes
        status = "✓" if existe else "✗ FALTA"
        print(f"     {status} Pareja {p1} vs Pareja {p2}")

cur.close()
conn.close()
