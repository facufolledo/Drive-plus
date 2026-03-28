import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("AJUSTE DE HORARIOS - ZONA A Y H - TORNEO 46")
print("=" * 80)

try:
    # 1. Verificar partidos a modificar
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            z.nombre as zona,
            p.pareja1_id,
            p.pareja2_id,
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
        WHERE p.id_partido IN (1206, 1185, 1187, 1204)
        ORDER BY p.id_partido
    """)
    
    partidos = {p['id_partido']: p for p in cur.fetchall()}
    
    print("\n📋 PARTIDOS A MODIFICAR:")
    for pid in [1206, 1185, 1187, 1204]:
        if pid in partidos:
            p = partidos[pid]
            dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
            print(f"\n  Partido {pid} - {p['zona']}")
            print(f"    Actual: {dia} {p['fecha_hora'].strftime('%H:%M')}")
            print(f"    P{p['pareja1_id']}: {p['p1_j1']} / {p['p1_j2']}")
            print(f"    vs")
            print(f"    P{p['pareja2_id']}: {p['p2_j1']} / {p['p2_j2']}")
    
    # 2. Verificar restricciones de las parejas involucradas
    parejas_ids = set()
    for p in partidos.values():
        parejas_ids.add(p['pareja1_id'])
        parejas_ids.add(p['pareja2_id'])
    
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
    """, (list(parejas_ids),))
    
    restricciones_parejas = {p['id']: p for p in cur.fetchall()}
    
    print("\n🔒 RESTRICCIONES DE PAREJAS:")
    for pid, pareja in restricciones_parejas.items():
        print(f"\n  Pareja {pid}: {pareja['jugador1']} / {pareja['jugador2']}")
        if pareja['disponibilidad_horaria']:
            for r in pareja['disponibilidad_horaria']:
                print(f"    ❌ {', '.join(r['dias'])} de {r['horaInicio']} a {r['horaFin']}")
        else:
            print(f"    ✅ Sin restricciones")
    
    # 3. Ver horarios ocupados del sábado
    cur.execute("""
        SELECT 
            p.fecha_hora,
            COUNT(*) as partidos
        FROM partidos p
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        WHERE p.id_torneo = 46
        AND tc.nombre IN ('7ma', '5ta')
        AND p.fecha_hora IS NOT NULL
        AND EXTRACT(DAY FROM p.fecha_hora) = 28
        GROUP BY p.fecha_hora
        ORDER BY p.fecha_hora
    """)
    
    horarios_sabado = cur.fetchall()
    
    print("\n📅 HORARIOS OCUPADOS DEL SÁBADO:")
    for h in horarios_sabado:
        print(f"  {h['fecha_hora'].strftime('%H:%M')}: {h['partidos']} partido(s)")
    
    # 4. APLICAR CAMBIOS
    print("\n" + "=" * 80)
    print("APLICANDO CAMBIOS")
    print("=" * 80)
    
    # Partido 1206: Sábado después de las 11am (probar 13:00)
    print("\n1. Partido 1206 → Sábado 13:00")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 13:00:00'
        WHERE id_partido = 1206
    """)
    print("   ✅ Actualizado")
    
    # Partido 1185: Sábado 14:00
    print("\n2. Partido 1185 → Sábado 14:00")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 14:00:00'
        WHERE id_partido = 1185
    """)
    print("   ✅ Actualizado")
    
    # Partido 1187: Sábado 00:30 (madrugada del sábado)
    print("\n3. Partido 1187 → Sábado 00:30")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 00:30:00'
        WHERE id_partido = 1187
    """)
    print("   ✅ Actualizado")
    
    # Partido 1204: Buscar horario libre del sábado (probar 10:30)
    print("\n4. Partido 1204 → Sábado 10:30")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 10:30:00'
        WHERE id_partido = 1204
    """)
    print("   ✅ Actualizado")
    
    conn.commit()
    
    # 5. Verificar resultado
    print("\n" + "=" * 80)
    print("VERIFICACIÓN POST-CAMBIOS")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            p.id_partido,
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
        WHERE p.id_partido IN (1206, 1185, 1187, 1204)
        ORDER BY p.fecha_hora
    """)
    
    print("\n✅ PARTIDOS ACTUALIZADOS:")
    for p in cur.fetchall():
        dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
        print(f"\n  Partido {p['id_partido']} - {p['zona']}")
        print(f"    {dia} {p['fecha_hora'].strftime('%H:%M')}")
        print(f"    {p['p1_j1']} / {p['p1_j2']} vs {p['p2_j1']} / {p['p2_j2']}")
    
    # Distribución final
    print("\n" + "=" * 80)
    print("DISTRIBUCIÓN FINAL")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            tc.nombre as categoria,
            CASE 
                WHEN EXTRACT(DAY FROM p.fecha_hora) = 27 THEN 'Viernes 27'
                WHEN EXTRACT(DAY FROM p.fecha_hora) = 28 THEN 'Sábado 28'
                ELSE 'Otro'
            END as dia,
            COUNT(*) as total
        FROM partidos p
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        WHERE p.id_torneo = 46 
        AND tc.nombre IN ('7ma', '5ta')
        AND p.fecha_hora IS NOT NULL
        GROUP BY tc.nombre, dia
        ORDER BY tc.nombre, dia
    """)
    
    print("\n📊 Partidos programados:")
    for row in cur.fetchall():
        print(f"   {row['categoria']} - {row['dia']}: {row['total']} partidos")
    
    print("\n" + "=" * 80)
    print("✅ AJUSTES COMPLETADOS")
    print("=" * 80)
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
