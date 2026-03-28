import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("SUGERENCIA DE INTERCAMBIO PARA PAREJA 1037")
print("=" * 80)

print("""
OBJETIVO:
- Pareja 1037 (Palacios/Gurgone) necesita jugar a las 17:00 y 21:00
- Sus rivales actuales en Zona C tienen restricciones después de 19:00 o 20:00

ESTRATEGIA:
Intercambiar pareja 1037 con una pareja de otra zona que:
1. Tenga rivales SIN restricciones en horarios 17:00 y 21:00
2. Pueda jugar en los horarios actuales de Zona C (17:00, 18:00, 11:30 sábado)
""")

# Obtener info de Zona C actual
print(f"\n{'=' * 80}")
print("ZONA C ACTUAL")
print("=" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
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
    AND tz.nombre = 'Zona C'
    AND p.fecha_hora IS NOT NULL
    ORDER BY p.fecha_hora
""")

partidos_zona_c = cur.fetchall()

parejas_zona_c = set()
for p in partidos_zona_c:
    parejas_zona_c.add(p['pareja1_id'])
    parejas_zona_c.add(p['pareja2_id'])
    print(f"\nPartido {p['id_partido']}: {p['fecha_hora'].strftime('%H:%M')}")
    print(f"  P{p['pareja1_id']} vs P{p['pareja2_id']}")

print(f"\nParejas en Zona C: {sorted(parejas_zona_c)}")

# Analizar otras zonas
print(f"\n{'=' * 80}")
print("ANÁLISIS DE OTRAS ZONAS")
print("=" * 80)

zonas = ['Zona A', 'Zona B', 'Zona D', 'Zona E']

for zona_nombre in zonas:
    print(f"\n{'=' * 40}")
    print(f"{zona_nombre}")
    print(f"{'=' * 40}")
    
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
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
        AND tz.nombre = %s
        AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """, (zona_nombre,))
    
    partidos_zona = cur.fetchall()
    
    if not partidos_zona:
        print("  (Sin partidos programados)")
        continue
    
    # Obtener parejas de esta zona
    parejas_zona = set()
    for p in partidos_zona:
        parejas_zona.add(p['pareja1_id'])
        parejas_zona.add(p['pareja2_id'])
    
    print(f"  Parejas: {sorted(parejas_zona)}")
    print(f"  Horarios:")
    for p in partidos_zona:
        print(f"    {p['fecha_hora'].strftime('%A %H:%M')}")
    
    # Analizar cada pareja de esta zona
    print(f"\n  Análisis de parejas:")
    for pareja_id in sorted(parejas_zona):
        # Obtener rivales de esta pareja
        rivales = []
        for p in partidos_zona:
            if p['pareja1_id'] == pareja_id:
                rivales.append((p['pareja2_id'], p['disp2'], f"{p['j1_p2']} / {p['j2_p2']}"))
            elif p['pareja2_id'] == pareja_id:
                rivales.append((p['pareja1_id'], p['disp1'], f"{p['j1_p1']} / {p['j2_p1']}"))
        
        # Verificar si los rivales pueden jugar a las 17:00 y 21:00
        puede_17 = True
        puede_21 = True
        
        for rival_id, disp, nombre in rivales:
            if disp:
                restricciones_viernes = [r for r in disp if r.get('dia') == 'viernes']
                for r in restricciones_viernes:
                    hora_inicio_str = r.get('hora_inicio', '')
                    hora_fin_str = r.get('hora_fin', '')
                    
                    if hora_inicio_str and hora_fin_str:
                        # Parsear horas
                        h_inicio = int(hora_inicio_str.split(':')[0]) + int(hora_inicio_str.split(':')[1]) / 60
                        h_fin = int(hora_fin_str.split(':')[0]) + int(hora_fin_str.split(':')[1]) / 60
                        
                        # Verificar 17:00-18:10
                        if not (18.17 <= h_inicio or 17.0 >= h_fin):
                            puede_17 = False
                        
                        # Verificar 21:00-22:10
                        if not (22.17 <= h_inicio or 21.0 >= h_fin):
                            puede_21 = False
        
        if puede_17 and puede_21:
            print(f"    ✅ Pareja {pareja_id}: Rivales PUEDEN jugar 17:00 y 21:00")
        elif puede_17:
            print(f"    ⚠️  Pareja {pareja_id}: Rivales pueden 17:00 pero NO 21:00")
        elif puede_21:
            print(f"    ⚠️  Pareja {pareja_id}: Rivales pueden 21:00 pero NO 17:00")
        else:
            print(f"    ❌ Pareja {pareja_id}: Rivales NO pueden 17:00 ni 21:00")

print(f"\n{'=' * 80}")
print("RECOMENDACIÓN")
print("=" * 80)

print("""
Buscar una pareja en otra zona donde:
1. Sus 2 rivales NO tengan restricciones en viernes 17:00-18:10 y 21:00-22:10
2. Esa pareja pueda jugar en los horarios actuales de Zona C

Intercambiar:
- Pareja 1037 (Zona C) → Zona X
- Pareja Y (Zona X) → Zona C

Esto permitirá que:
- Pareja 1037 juegue a las 17:00 y 21:00 en Zona X
- Pareja Y juegue en los horarios de Zona C (que sus rivales pueden)
""")

cur.close()
conn.close()
