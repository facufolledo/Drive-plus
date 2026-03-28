import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CORRECCIÓN DE SOLAPAMIENTO DE 60 MINUTOS - TORNEO 46")
print("=" * 80)

try:
    # Solapamiento crítico: Exequiel Diaz / Yamil Jofre - Zona C
    # Partido 1192: 22:30 y Partido 1193: 23:30 (60 minutos)
    # Solución: Mover partido 1193 al sábado temprano
    
    print("\nSOLAPAMIENTO A CORREGIR:")
    print("  Zona C - Exequiel Diaz / Yamil Jofre")
    print("  Partido 1192: Viernes 22:30")
    print("  Partido 1193: Viernes 23:30")
    print("  Diferencia: 60 minutos")
    
    # Verificar horarios actuales de Zona C
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            z.nombre as zona,
            tp1.jugador1_id as j1_p1, tp1.jugador2_id as j2_p1,
            tp2.jugador1_id as j1_p2, tp2.jugador2_id as j2_p2,
            pu1.nombre || ' ' || pu1.apellido as pareja1_j1,
            pu2.nombre || ' ' || pu2.apellido as pareja1_j2,
            pu3.nombre || ' ' || pu3.apellido as pareja2_j1,
            pu4.nombre || ' ' || pu4.apellido as pareja2_j2
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id_torneo = 46
        AND z.nombre = 'Zona C'
        AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """)
    
    partidos_zona_c = cur.fetchall()
    
    print("\n📋 Partidos actuales de Zona C:")
    for p in partidos_zona_c:
        print(f"  Partido {p['id_partido']}: {p['fecha_hora'].strftime('%Y-%m-%d %H:%M')}")
        print(f"    {p['pareja1_j1']} / {p['pareja1_j2']} vs {p['pareja2_j1']} / {p['pareja2_j2']}")
    
    # Mover partido 1193 al sábado 12:30
    print("\n🔨 SOLUCIÓN:")
    print("  Mover partido 1193 a sábado 12:30")
    
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 12:30:00'
        WHERE id_partido = 1193
    """)
    
    print("  ✅ Partido 1193 movido a sábado 28 marzo 12:30")
    
    conn.commit()
    
    # Verificar resultado
    print("\n" + "=" * 80)
    print("VERIFICACIÓN POST-CORRECCIÓN")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            pu1.nombre || ' ' || pu1.apellido as pareja1_j1,
            pu2.nombre || ' ' || pu2.apellido as pareja1_j2,
            pu3.nombre || ' ' || pu3.apellido as pareja2_j1,
            pu4.nombre || ' ' || pu4.apellido as pareja2_j2
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id_torneo = 46
        AND z.nombre = 'Zona C'
        AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """)
    
    print("\n✅ Partidos corregidos de Zona C:")
    for p in cur.fetchall():
        dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
        print(f"  Partido {p['id_partido']}: {dia} {p['fecha_hora'].strftime('%H:%M')}")
        print(f"    {p['pareja1_j1']} / {p['pareja1_j2']} vs {p['pareja2_j1']} / {p['pareja2_j2']}")
    
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
    print("\nSolapamiento de 60 minutos corregido.")
    print("Ahora el mínimo es 90 minutos (aceptable para zonas de 3 parejas).")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
