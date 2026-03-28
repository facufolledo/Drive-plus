import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("INTERCAMBIO DE PAREJAS 1002 Y 1019 - TORNEO 46 7MA")
print("=" * 80)

try:
    # 1. Verificar parejas
    cur.execute("""
        SELECT 
            tp.id,
            pu1.nombre || ' ' || pu1.apellido as jugador1,
            pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id IN (1002, 1019)
    """)
    
    parejas = {p['id']: p for p in cur.fetchall()}
    
    print("\n📋 PAREJAS A INTERCAMBIAR:")
    print(f"  Pareja 1002: {parejas[1002]['jugador1']} / {parejas[1002]['jugador2']}")
    print(f"  Pareja 1019: {parejas[1019]['jugador1']} / {parejas[1019]['jugador2']}")
    
    # 2. Obtener IDs de zonas
    cur.execute("""
        SELECT id, nombre
        FROM torneo_zonas
        WHERE torneo_id = 46
        AND nombre IN ('Zona A', 'Zona H')
    """)
    
    zonas = {z['nombre']: z['id'] for z in cur.fetchall()}
    zona_a_id = zonas['Zona A']
    zona_h_id = zonas['Zona H']
    
    print(f"\n🏆 ZONAS:")
    print(f"  Zona A: ID {zona_a_id}")
    print(f"  Zona H: ID {zona_h_id}")
    
    # 3. Verificar partidos actuales
    cur.execute("""
        SELECT 
            p.id_partido,
            p.pareja1_id,
            p.pareja2_id,
            p.fecha_hora,
            z.nombre as zona
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        WHERE p.id_torneo = 46
        AND (p.pareja1_id IN (1002, 1019) OR p.pareja2_id IN (1002, 1019))
        ORDER BY z.nombre, p.fecha_hora
    """)
    
    partidos_actuales = cur.fetchall()
    
    print("\n📊 PARTIDOS ACTUALES:")
    for p in partidos_actuales:
        print(f"  Partido {p['id_partido']} - {p['zona']}")
        print(f"    P{p['pareja1_id']} vs P{p['pareja2_id']} - {p['fecha_hora']}")
    
    # 4. INTERCAMBIO: Actualizar cada partido individualmente
    print("\n🔨 EJECUTANDO INTERCAMBIO...")
    
    # Obtener todos los partidos que involucran a estas parejas
    partidos_a_actualizar = []
    
    for p in partidos_actuales:
        nuevo_p1 = p['pareja1_id']
        nuevo_p2 = p['pareja2_id']
        
        # Intercambiar IDs
        if nuevo_p1 == 1002:
            nuevo_p1 = 1019
        elif nuevo_p1 == 1019:
            nuevo_p1 = 1002
            
        if nuevo_p2 == 1002:
            nuevo_p2 = 1019
        elif nuevo_p2 == 1019:
            nuevo_p2 = 1002
        
        partidos_a_actualizar.append({
            'id': p['id_partido'],
            'p1_old': p['pareja1_id'],
            'p2_old': p['pareja2_id'],
            'p1_new': nuevo_p1,
            'p2_new': nuevo_p2
        })
    
    # Actualizar cada partido
    for p in partidos_a_actualizar:
        print(f"  Partido {p['id']}: P{p['p1_old']} vs P{p['p2_old']} → P{p['p1_new']} vs P{p['p2_new']}")
        
        cur.execute("""
            UPDATE partidos
            SET pareja1_id = %s, pareja2_id = %s
            WHERE id_partido = %s
        """, (p['p1_new'], p['p2_new'], p['id']))
    
    conn.commit()
    
    print("  ✅ Intercambio completado")
    
    # 5. Verificar resultado
    print("\n" + "=" * 80)
    print("VERIFICACIÓN POST-INTERCAMBIO")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            p.id_partido,
            p.pareja1_id,
            p.pareja2_id,
            p.fecha_hora,
            z.nombre as zona,
            pu1.nombre || ' ' || pu1.apellido as p1_j1,
            pu2.nombre || ' ' || pu2.apellido as p1_j2,
            pu3.nombre || ' ' || pu3.apellido as p2_j1,
            pu4.nombre || ' ' || pu4.apellido as p2_j2
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id_torneo = 46
        AND (p.pareja1_id IN (1002, 1019) OR p.pareja2_id IN (1002, 1019))
        ORDER BY z.nombre, p.fecha_hora
    """)
    
    partidos_nuevos = cur.fetchall()
    
    print("\n✅ PARTIDOS DESPUÉS DEL INTERCAMBIO:")
    zona_actual = None
    for p in partidos_nuevos:
        if zona_actual != p['zona']:
            zona_actual = p['zona']
            print(f"\n  {p['zona']}:")
        
        dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
        print(f"    Partido {p['id_partido']}: {dia} {p['fecha_hora'].strftime('%H:%M')}")
        print(f"      P{p['pareja1_id']}: {p['p1_j1']} / {p['p1_j2']}")
        print(f"      vs")
        print(f"      P{p['pareja2_id']}: {p['p2_j1']} / {p['p2_j2']}")
    
    print("\n" + "=" * 80)
    print("✅ INTERCAMBIO COMPLETADO")
    print("=" * 80)
    print(f"\nPareja 1002 ({parejas[1002]['jugador1']} / {parejas[1002]['jugador2']}) ahora en Zona H")
    print(f"Pareja 1019 ({parejas[1019]['jugador1']} / {parejas[1019]['jugador2']}) ahora en Zona A")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
