import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("AJUSTES 5TA - INTERCAMBIO PAREJAS Y HORARIO PARTIDO 1163")
print("=" * 80)

try:
    # 1. Verificar parejas a intercambiar
    cur.execute("""
        SELECT 
            tp.id,
            pu1.nombre || ' ' || pu1.apellido as jugador1,
            pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id IN (1038, 1030)
    """)
    
    parejas = {p['id']: p for p in cur.fetchall()}
    
    print("\n📋 PAREJAS A INTERCAMBIAR:")
    print(f"  Pareja 1038: {parejas[1038]['jugador1']} / {parejas[1038]['jugador2']} (Zona C)")
    print(f"  Pareja 1030: {parejas[1030]['jugador1']} / {parejas[1030]['jugador2']} (Zona E)")
    
    # 2. Ver partidos actuales de estas parejas
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            z.nombre as zona,
            p.pareja1_id,
            p.pareja2_id
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        WHERE p.id_torneo = 46
        AND (p.pareja1_id IN (1038, 1030) OR p.pareja2_id IN (1038, 1030))
        ORDER BY z.nombre, p.fecha_hora
    """)
    
    partidos_actuales = cur.fetchall()
    
    print("\n📊 PARTIDOS ACTUALES:")
    for p in partidos_actuales:
        print(f"  Partido {p['id_partido']} - {p['zona']}: P{p['pareja1_id']} vs P{p['pareja2_id']} - {p['fecha_hora']}")
    
    # 3. INTERCAMBIO: Reemplazar 1038 por 1030 y viceversa
    print("\n🔨 EJECUTANDO INTERCAMBIO DE PAREJAS...")
    
    partidos_a_actualizar = []
    
    for p in partidos_actuales:
        nuevo_p1 = p['pareja1_id']
        nuevo_p2 = p['pareja2_id']
        
        if nuevo_p1 == 1038:
            nuevo_p1 = 1030
        elif nuevo_p1 == 1030:
            nuevo_p1 = 1038
            
        if nuevo_p2 == 1038:
            nuevo_p2 = 1030
        elif nuevo_p2 == 1030:
            nuevo_p2 = 1038
        
        partidos_a_actualizar.append({
            'id': p['id_partido'],
            'p1_new': nuevo_p1,
            'p2_new': nuevo_p2
        })
    
    for p in partidos_a_actualizar:
        cur.execute("""
            UPDATE partidos
            SET pareja1_id = %s, pareja2_id = %s
            WHERE id_partido = %s
        """, (p['p1_new'], p['p2_new'], p['id']))
        print(f"  ✅ Partido {p['id']}: P{p['p1_new']} vs P{p['p2_new']}")
    
    # 4. AJUSTAR HORARIO DEL PARTIDO 1163
    print("\n🔨 AJUSTANDO HORARIO DEL PARTIDO 1163...")
    
    # Ver horario actual
    cur.execute("""
        SELECT fecha_hora
        FROM partidos
        WHERE id_partido = 1163
    """)
    
    horario_actual = cur.fetchone()['fecha_hora']
    print(f"  Horario actual: {horario_actual}")
    
    # Ver horarios ocupados entre 17:00 y 22:00 del viernes
    cur.execute("""
        SELECT 
            p.fecha_hora,
            COUNT(*) as partidos
        FROM partidos p
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        WHERE p.id_torneo = 46
        AND tc.nombre IN ('7ma', '5ta')
        AND p.fecha_hora IS NOT NULL
        AND EXTRACT(DAY FROM p.fecha_hora) = 27
        AND EXTRACT(HOUR FROM p.fecha_hora) BETWEEN 17 AND 22
        GROUP BY p.fecha_hora
        ORDER BY p.fecha_hora
    """)
    
    horarios_ocupados = cur.fetchall()
    
    print("\n  📅 Horarios ocupados viernes 17:00-22:00:")
    for h in horarios_ocupados:
        print(f"    {h['fecha_hora'].strftime('%H:%M')}: {h['partidos']} partido(s)")
    
    # Elegir horario con menos partidos (o uno libre)
    # Probar 20:00
    nuevo_horario = '2026-03-27 20:00:00'
    
    print(f"\n  Nuevo horario: Viernes 20:00")
    
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = %s
        WHERE id_partido = 1163
    """, (nuevo_horario,))
    
    print("  ✅ Horario actualizado")
    
    conn.commit()
    
    # 5. VERIFICACIÓN
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
        WHERE p.id_torneo = 46
        AND (p.pareja1_id IN (1038, 1030) OR p.pareja2_id IN (1038, 1030))
        ORDER BY z.nombre, p.fecha_hora
    """)
    
    print("\n✅ PARTIDOS DESPUÉS DEL INTERCAMBIO:")
    zona_actual = None
    for p in cur.fetchall():
        if zona_actual != p['zona']:
            zona_actual = p['zona']
            print(f"\n  {p['zona']}:")
        
        dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
        print(f"    Partido {p['id_partido']}: {dia} {p['fecha_hora'].strftime('%H:%M')}")
        print(f"      {p['p1_j1']} / {p['p1_j2']} vs {p['p2_j1']} / {p['p2_j2']}")
    
    print("\n" + "=" * 80)
    print("✅ AJUSTES COMPLETADOS")
    print("=" * 80)
    print(f"\nPareja 1038 ({parejas[1038]['jugador1']} / {parejas[1038]['jugador2']}) ahora en Zona E")
    print(f"Pareja 1030 ({parejas[1030]['jugador1']} / {parejas[1030]['jugador2']}) ahora en Zona C")
    print(f"Partido 1163 movido a viernes 20:00")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
