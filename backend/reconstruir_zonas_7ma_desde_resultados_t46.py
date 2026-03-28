import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("RECONSTRUIR ZONAS 7MA DESDE RESULTADOS - TORNEO 46")
print("=" * 80)

# PASO 1: Identificar partidos de 7ma (categoria_id=126 tiene 8 zonas)
print("\n1️⃣  IDENTIFICAR PARTIDOS DE 7MA")
print("-" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.categoria_id,
        p.zona_id,
        tz.nombre as zona_nombre,
        p.pareja1_id,
        p.pareja2_id,
        p.ganador_pareja_id,
        p.resultado_padel,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2
    FROM partidos p
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE p.id_torneo = 46
    AND p.tipo = 'torneo'
    AND p.fase = 'zona'
    AND p.categoria_id = 126
    ORDER BY tz.numero_orden, p.id_partido
""")

partidos_7ma = cur.fetchall()

print(f"\nTotal partidos de 7ma (cat 126): {len(partidos_7ma)}")
print(f"Esperados: 8 zonas × 3 partidos = 24 partidos")

# Agrupar por zona
partidos_por_zona = {}
for p in partidos_7ma:
    zona = p['zona_nombre'] or f"Zona ID {p['zona_id']}"
    if zona not in partidos_por_zona:
        partidos_por_zona[zona] = []
    partidos_por_zona[zona].append(p)

print(f"\nZonas encontradas: {len(partidos_por_zona)}")
for zona, partidos in sorted(partidos_por_zona.items()):
    print(f"  {zona}: {len(partidos)} partidos")

# PASO 2: Extraer parejas únicas de cada zona
print("\n2️⃣  EXTRAER PAREJAS POR ZONA")
print("-" * 80)

parejas_por_zona = {}
for zona, partidos in partidos_por_zona.items():
    parejas_set = set()
    for p in partidos:
        parejas_set.add(p['pareja1_id'])
        parejas_set.add(p['pareja2_id'])
    parejas_por_zona[zona] = list(parejas_set)
    print(f"\n{zona}: {len(parejas_set)} parejas")
    for pareja_id in parejas_set:
        # Buscar nombre de la pareja
        partido_ejemplo = next((pt for pt in partidos if pt['pareja1_id'] == pareja_id), None)
        if not partido_ejemplo:
            partido_ejemplo = next((pt for pt in partidos if pt['pareja2_id'] == pareja_id), None)
        
        if partido_ejemplo:
            if partido_ejemplo['pareja1_id'] == pareja_id:
                print(f"    Pareja {pareja_id}: {partido_ejemplo['j1_p1']}/{partido_ejemplo['j2_p1']}")
            else:
                print(f"    Pareja {pareja_id}: {partido_ejemplo['j1_p2']}/{partido_ejemplo['j2_p2']}")

# PASO 3: Calcular puntos de cada pareja en cada zona
print("\n3️⃣  CALCULAR PUNTOS POR PAREJA")
print("-" * 80)

puntos_por_pareja = {}  # {zona: {pareja_id: {puntos, pj, pg, pp, gf, gc}}}

for zona, partidos in partidos_por_zona.items():
    puntos_por_pareja[zona] = {}
    
    # Inicializar todas las parejas de la zona
    for pareja_id in parejas_por_zona[zona]:
        puntos_por_pareja[zona][pareja_id] = {
            'puntos': 0,
            'pj': 0,
            'pg': 0,
            'pp': 0,
            'gf': 0,
            'gc': 0
        }
    
    # Procesar cada partido
    for p in partidos:
        if not p['ganador_pareja_id']:
            continue  # Partido sin resultado
        
        p1_id = p['pareja1_id']
        p2_id = p['pareja2_id']
        ganador_id = p['ganador_pareja_id']
        resultado = p['resultado_padel']  # Formato: "6-4 6-3"
        
        # Parsear resultado
        gf_p1, gc_p1 = 0, 0
        if resultado:
            try:
                sets = resultado.split()
                for s in sets:
                    if '-' in s:
                        g1, g2 = s.split('-')
                        gf_p1 += int(g1)
                        gc_p1 += int(g2)
            except:
                pass
        
        gf_p2 = gc_p1
        gc_p2 = gf_p1
        
        # Actualizar stats
        if p1_id in puntos_por_pareja[zona]:
            puntos_por_pareja[zona][p1_id]['pj'] += 1
            puntos_por_pareja[zona][p1_id]['gf'] += gf_p1
            puntos_por_pareja[zona][p1_id]['gc'] += gc_p1
            if ganador_id == p1_id:
                puntos_por_pareja[zona][p1_id]['pg'] += 1
                puntos_por_pareja[zona][p1_id]['puntos'] += 2
            else:
                puntos_por_pareja[zona][p1_id]['pp'] += 1
        
        if p2_id in puntos_por_pareja[zona]:
            puntos_por_pareja[zona][p2_id]['pj'] += 1
            puntos_por_pareja[zona][p2_id]['gf'] += gf_p2
            puntos_por_pareja[zona][p2_id]['gc'] += gc_p2
            if ganador_id == p2_id:
                puntos_por_pareja[zona][p2_id]['pg'] += 1
                puntos_por_pareja[zona][p2_id]['puntos'] += 2
            else:
                puntos_por_pareja[zona][p2_id]['pp'] += 1

# Mostrar tabla de posiciones de cada zona
for zona in sorted(puntos_por_pareja.keys()):
    print(f"\n{zona}:")
    print(f"  {'Pareja':<10} {'PJ':<4} {'PG':<4} {'PP':<4} {'GF':<4} {'GC':<4} {'Pts':<4}")
    print(f"  {'-'*50}")
    
    # Ordenar por puntos, luego por diferencia de games
    parejas_ordenadas = sorted(
        puntos_por_pareja[zona].items(),
        key=lambda x: (x[1]['puntos'], x[1]['gf'] - x[1]['gc'], x[1]['gf']),
        reverse=True
    )
    
    for pareja_id, stats in parejas_ordenadas:
        dif = stats['gf'] - stats['gc']
        print(f"  {pareja_id:<10} {stats['pj']:<4} {stats['pg']:<4} {stats['pp']:<4} "
              f"{stats['gf']:<4} {stats['gc']:<4} {stats['puntos']:<4} (dif: {dif:+d})")

# PASO 4: Verificar estado actual de torneo_zona_parejas
print("\n4️⃣  VERIFICAR ESTADO ACTUAL DE TORNEO_ZONA_PAREJAS")
print("-" * 80)

cur.execute("""
    SELECT 
        tz.nombre as zona_nombre,
        tzp.pareja_id,
        tzp.puntos,
        tzp.partidos_jugados,
        tzp.partidos_ganados,
        tzp.partidos_perdidos
    FROM torneo_zona_parejas tzp
    JOIN torneo_zonas tz ON tzp.zona_id = tz.id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 126
    ORDER BY tz.numero_orden, tzp.puntos DESC
""")

zona_parejas_actual = cur.fetchall()

print(f"\nRegistros actuales en torneo_zona_parejas para 7ma: {len(zona_parejas_actual)}")

if zona_parejas_actual:
    print("\nPrimeros 10 registros:")
    for zp in zona_parejas_actual[:10]:
        print(f"  {zp['zona_nombre']}: Pareja {zp['pareja_id']} - {zp['puntos']} pts "
              f"({zp['partidos_ganados']}-{zp['partidos_perdidos']})")

# PASO 5: Comparar con lo calculado
print("\n5️⃣  COMPARACIÓN: ACTUAL vs CALCULADO")
print("-" * 80)

# Crear dict de lo actual
actual_dict = {}
for zp in zona_parejas_actual:
    zona = zp['zona_nombre']
    if zona not in actual_dict:
        actual_dict[zona] = {}
    actual_dict[zona][zp['pareja_id']] = zp['puntos']

# Comparar
diferencias = []
for zona, parejas_calc in puntos_por_pareja.items():
    for pareja_id, stats_calc in parejas_calc.items():
        puntos_calc = stats_calc['puntos']
        puntos_actual = actual_dict.get(zona, {}).get(pareja_id, None)
        
        if puntos_actual is None:
            diferencias.append({
                'zona': zona,
                'pareja_id': pareja_id,
                'problema': 'FALTA EN torneo_zona_parejas',
                'puntos_calc': puntos_calc
            })
        elif puntos_actual != puntos_calc:
            diferencias.append({
                'zona': zona,
                'pareja_id': pareja_id,
                'problema': 'PUNTOS INCORRECTOS',
                'puntos_actual': puntos_actual,
                'puntos_calc': puntos_calc
            })

print(f"\nDiferencias encontradas: {len(diferencias)}")

if diferencias:
    print("\nDetalle de diferencias:")
    for d in diferencias[:20]:
        print(f"  {d['zona']} - Pareja {d['pareja_id']}: {d['problema']}")
        if 'puntos_actual' in d:
            print(f"    Actual: {d['puntos_actual']} pts | Calculado: {d['puntos_calc']} pts")
        else:
            print(f"    Calculado: {d['puntos_calc']} pts")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("ANÁLISIS COMPLETADO")
print("=" * 80)
