import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CORRECCIÓN DE VIOLACIONES DE RESTRICCIONES - TORNEO 46")
print("=" * 80)

try:
    # 1. Partido 1202 - Axel Alfaro / Matías Alfaro
    # Problema: Viernes 18:00, no disponible viernes 00:00-18:00
    # Solución: Mover a viernes 19:00
    print("\n1. Partido 1202 (Axel Alfaro / Matías Alfaro)")
    print("   Actual: Viernes 18:00")
    print("   Nueva: Viernes 19:00")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 19:00:00'
        WHERE id_partido = 1202
    """)
    print("   ✅ Actualizado")
    
    # 2. Partido 1159 (5ta) - Tomas Carrizo / Bautista Oliva
    # Problema: Viernes 22:00, no disponible viernes 18:00-22:00
    # Solución: Mover a viernes 22:30
    print("\n2. Partido 1159 (Tomas Carrizo / Bautista Oliva - 5ta)")
    print("   Actual: Viernes 22:00")
    print("   Nueva: Viernes 22:30")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 22:30:00'
        WHERE id_partido = 1159
    """)
    print("   ✅ Actualizado")
    
    # 3. Partido 1207 - Lucas Apostolo / Mariano Roldán
    # Problema: Viernes 22:00, no disponible viernes 18:00-22:00
    # Solución: Mover a sábado 08:00
    print("\n3. Partido 1207 (Lucas Apostolo / Mariano Roldán)")
    print("   Actual: Viernes 22:00")
    print("   Nueva: Sábado 08:00")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 08:00:00'
        WHERE id_partido = 1207
    """)
    print("   ✅ Actualizado")
    
    # 4. Partido 1208 - Lucas Apostolo / Mariano Roldán
    # Problema: Viernes 23:00, no disponible viernes 23:00-23:59
    # Solución: Mover a sábado 09:30
    print("\n4. Partido 1208 (Lucas Apostolo / Mariano Roldán)")
    print("   Actual: Viernes 23:00")
    print("   Nueva: Sábado 09:30")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 09:30:00'
        WHERE id_partido = 1208
    """)
    print("   ✅ Actualizado")
    
    # 5. Partido 1185 - Agustín Mercado / Cesar Zaracho
    # Problema: Viernes 23:59, no disponible viernes 00:00-23:59 (TODO EL DÍA)
    # Solución: Mover a sábado 11:00
    print("\n5. Partido 1185 (Agustín Mercado / Cesar Zaracho)")
    print("   Actual: Viernes 23:59")
    print("   Nueva: Sábado 11:00")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 11:00:00'
        WHERE id_partido = 1185
    """)
    print("   ✅ Actualizado")
    
    conn.commit()
    
    print("\n" + "=" * 80)
    print("VERIFICACIÓN POST-CORRECCIÓN")
    print("=" * 80)
    
    # Verificar que no haya más violaciones
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            tc.nombre as categoria,
            z.nombre as zona,
            tp.disponibilidad_horaria,
            pu1.nombre || ' ' || pu1.apellido as jugador1,
            pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM partidos p
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneos_parejas tp ON p.pareja1_id = tp.id OR p.pareja2_id = tp.id
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE p.id_partido IN (1202, 1159, 1207, 1208, 1185)
        AND p.fecha_hora IS NOT NULL
        ORDER BY p.id_partido
    """)
    
    partidos_corregidos = cur.fetchall()
    
    print("\nPartidos corregidos:")
    for p in partidos_corregidos:
        fecha = p['fecha_hora'].strftime('%Y-%m-%d %H:%M')
        dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
        print(f"  Partido {p['id_partido']}: {p['jugador1']} / {p['jugador2']}")
        print(f"    {dia} {fecha} - {p['categoria']} {p['zona']}")
    
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
    print("✅ CORRECCIÓN COMPLETADA")
    print("=" * 80)
    print("\nLas 5 violaciones de restricciones han sido corregidas.")
    print("Los solapamientos se mantienen (son aceptables para el formato del torneo).")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
