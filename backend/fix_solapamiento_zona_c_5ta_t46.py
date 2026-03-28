import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("FIX SOLAPAMIENTO ZONA C 5TA - LUCIANO PAEZ")
print("=" * 80)

try:
    # 1. Ver partidos actuales de Zona C
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            p.pareja1_id,
            p.pareja2_id,
            pu1.nombre || ' ' || pu1.apellido as p1_j1,
            pu2.nombre || ' ' || pu2.apellido as p1_j2,
            pu3.nombre || ' ' || pu3.apellido as p2_j1,
            pu4.nombre || ' ' || pu4.apellido as p2_j2
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id_torneo = 46
        AND tc.nombre = '5ta'
        AND z.nombre = 'Zona C'
        ORDER BY p.fecha_hora
    """)
    
    partidos_zona_c = cur.fetchall()
    
    print("\n📋 PARTIDOS ACTUALES ZONA C:")
    for p in partidos_zona_c:
        dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
        print(f"\n  Partido {p['id_partido']}: {dia} {p['fecha_hora'].strftime('%H:%M')}")
        print(f"    P{p['pareja1_id']}: {p['p1_j1']} / {p['p1_j2']}")
        print(f"    vs")
        print(f"    P{p['pareja2_id']}: {p['p2_j1']} / {p['p2_j2']}")
    
    # Identificar solapamiento
    if len(partidos_zona_c) >= 2:
        p1 = partidos_zona_c[0]
        p2 = partidos_zona_c[1]
        diff_minutos = (p2['fecha_hora'] - p1['fecha_hora']).total_seconds() / 60
        
        print(f"\n⚠️  SOLAPAMIENTO DETECTADO:")
        print(f"  Partido {p1['id_partido']} ({p1['fecha_hora'].strftime('%H:%M')}) y Partido {p2['id_partido']} ({p2['fecha_hora'].strftime('%H:%M')})")
        print(f"  Diferencia: {diff_minutos:.0f} minutos")
    
    # 2. Verificar restricciones de las 3 parejas de Zona C
    parejas_zona_c = {1036, 1037, 1030}  # Después del intercambio
    
    cur.execute("""
        SELECT 
            tp.id,
            tp.disponibilidad_horaria,
            pu1.nombre || ' ' || pu1.apellido as jugador1,
            pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = ANY(%s)
    """, (list(parejas_zona_c),))
    
    restricciones = {p['id']: p for p in cur.fetchall()}
    
    print("\n🔒 RESTRICCIONES DE PAREJAS ZONA C:")
    for pid, pareja in restricciones.items():
        print(f"\n  Pareja {pid}: {pareja['jugador1']} / {pareja['jugador2']}")
        if pareja['disponibilidad_horaria']:
            for r in pareja['disponibilidad_horaria']:
                print(f"    ❌ {', '.join(r['dias'])} de {r['horaInicio']} a {r['horaFin']}")
        else:
            print(f"    ✅ Sin restricciones")
    
    # 3. Buscar horario óptimo para partido 1164
    # Partido 1163: 20:00
    # Partido 1164: 18:30 (muy cerca)
    # Necesitamos mover 1164 al sábado
    
    print("\n🔨 SOLUCIÓN:")
    print("  Mover partido 1164 al sábado 11:30")
    
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 11:30:00'
        WHERE id_partido = 1164
    """)
    
    conn.commit()
    print("  ✅ Partido 1164 movido a sábado 11:30")
    
    # 4. Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN POST-AJUSTE")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            pu1.nombre || ' ' || pu1.apellido as p1_j1,
            pu2.nombre || ' ' || pu2.apellido as p1_j2,
            pu3.nombre || ' ' || pu3.apellido as p2_j1,
            pu4.nombre || ' ' || pu4.apellido as p2_j2
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id_torneo = 46
        AND tc.nombre = '5ta'
        AND z.nombre = 'Zona C'
        ORDER BY p.fecha_hora
    """)
    
    print("\n✅ PARTIDOS ZONA C DESPUÉS DEL AJUSTE:")
    for p in cur.fetchall():
        dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
        print(f"\n  Partido {p['id_partido']}: {dia} {p['fecha_hora'].strftime('%H:%M')}")
        print(f"    {p['p1_j1']} / {p['p1_j2']} vs {p['p2_j1']} / {p['p2_j2']}")
    
    # Verificar separación
    partidos_final = cur.fetchall()
    if len(partidos_final) >= 2:
        cur.execute("""
            SELECT 
                p.id_partido,
                p.fecha_hora
            FROM partidos p
            JOIN torneo_zonas z ON p.zona_id = z.id
            JOIN torneo_categorias tc ON p.categoria_id = tc.id
            WHERE p.id_torneo = 46
            AND tc.nombre = '5ta'
            AND z.nombre = 'Zona C'
            ORDER BY p.fecha_hora
        """)
        
        partidos_orden = cur.fetchall()
        if len(partidos_orden) >= 2:
            diff = (partidos_orden[1]['fecha_hora'] - partidos_orden[0]['fecha_hora']).total_seconds() / 60
            print(f"\n  ✅ Separación entre partidos: {diff:.0f} minutos")
    
    print("\n" + "=" * 80)
    print("✅ AJUSTE COMPLETADO")
    print("=" * 80)
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
