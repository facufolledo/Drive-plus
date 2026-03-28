import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ANÁLISIS COMPLETO 5TA - TODAS LAS ZONAS")
print("=" * 80)

# Obtener todos los partidos de 5ta con horarios viernes tarde/noche
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tz.nombre as zona,
        tp1.id as pareja1_id,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        tp2.id as pareja2_id,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2,
        tp1.disponibilidad_horaria as disp1,
        tp2.disponibilidad_horaria as disp2
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46
    AND tc.nombre = '5ta'
    AND p.fecha_hora IS NOT NULL
    AND EXTRACT(DOW FROM p.fecha_hora) = 5
    AND EXTRACT(HOUR FROM p.fecha_hora) >= 17
    ORDER BY tz.nombre, p.fecha_hora
""")

partidos_viernes_tarde = cur.fetchall()

print(f"\n📊 PARTIDOS VIERNES TARDE/NOCHE (17:00+):")
print("=" * 80)

for p in partidos_viernes_tarde:
    hora = p['fecha_hora'].strftime('%H:%M')
    print(f"\n{p['zona']} - Partido {p['id_partido']} - {hora}")
    print(f"  Pareja {p['pareja1_id']}: {p['j1_p1']} / {p['j2_p1']}")
    print(f"  vs")
    print(f"  Pareja {p['pareja2_id']}: {p['j1_p2']} / {p['j2_p2']}")
    
    # Buscar restricciones después de las 19:00
    for pareja_id, disp, nombre in [(p['pareja1_id'], p['disp1'], f"{p['j1_p1']} / {p['j2_p1']}"),
                                      (p['pareja2_id'], p['disp2'], f"{p['j1_p2']} / {p['j2_p2']}")]:
        if disp:
            restricciones_viernes = [r for r in disp if r.get('dia') == 'viernes']
            for r in restricciones_viernes:
                hora_fin_str = r.get('hora_fin', '')
                if hora_fin_str:
                    hora_fin_parts = hora_fin_str.split(':')
                    hora_fin_num = int(hora_fin_parts[0])
                    if hora_fin_num <= 19 or hora_fin_num >= 20:
                        print(f"  ⚠️  Pareja {pareja_id} ({nombre}): NO disponible {r.get('hora_inicio')}-{hora_fin_str}")

# Buscar parejas con Benjamin Palacios o Cristian Gurgone
print(f"\n{'=' * 80}")
print("BUSCAR BENJAMIN PALACIOS Y CRISTIAN GURGONE")
print("=" * 80)

cur.execute("""
    SELECT 
        tp.id as pareja_id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2,
        tc.nombre as categoria,
        tz.nombre as zona
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    JOIN torneo_categorias tc ON tp.categoria_id = tc.id
    LEFT JOIN torneo_zonas tz ON tp.id IN (
        SELECT DISTINCT pareja1_id FROM partidos WHERE id_torneo = 46 AND zona_id = tz.id
        UNION
        SELECT DISTINCT pareja2_id FROM partidos WHERE id_torneo = 46 AND zona_id = tz.id
    )
    WHERE tp.torneo_id = 46
    AND (
        LOWER(pu1.nombre || ' ' || pu1.apellido) LIKE '%benjamin%palacios%'
        OR LOWER(pu2.nombre || ' ' || pu2.apellido) LIKE '%benjamin%palacios%'
        OR LOWER(pu1.nombre || ' ' || pu1.apellido) LIKE '%cristian%gurgone%'
        OR LOWER(pu2.nombre || ' ' || pu2.apellido) LIKE '%cristian%gurgone%'
    )
""")

parejas_buscadas = cur.fetchall()

for p in parejas_buscadas:
    print(f"\nPareja {p['pareja_id']}: {p['j1']} / {p['j2']}")
    print(f"  Categoría: {p['categoria']}")
    if p['zona']:
        print(f"  Zona: {p['zona']}")

# Obtener todos los partidos de esa pareja
if parejas_buscadas:
    pareja_id = parejas_buscadas[0]['pareja_id']
    
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            p.cancha_id,
            tz.nombre as zona,
            CASE 
                WHEN p.pareja1_id = %s THEN p.pareja2_id
                ELSE p.pareja1_id
            END as rival_id
        FROM partidos p
        LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
        WHERE p.id_torneo = 46
        AND (p.pareja1_id = %s OR p.pareja2_id = %s)
        AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """, (pareja_id, pareja_id, pareja_id))
    
    partidos_pareja = cur.fetchall()
    
    print(f"\n{'=' * 80}")
    print(f"PARTIDOS DE PAREJA {pareja_id}")
    print("=" * 80)
    
    for p in partidos_pareja:
        print(f"\nPartido {p['id_partido']} - {p['zona']}")
        print(f"  {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
        print(f"  vs Pareja {p['rival_id']}")

cur.close()
conn.close()
