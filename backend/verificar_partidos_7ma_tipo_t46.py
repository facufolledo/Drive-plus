import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR PARTIDOS 7MA - TIPO Y ID_TORNEO")
print("=" * 80)

# Buscar partidos de 7ma
cur.execute("""
    SELECT 
        p.id_partido,
        p.tipo,
        p.id_torneo,
        p.fase,
        p.fecha_hora,
        p.cancha_id,
        tc.nombre as categoria,
        tz.nombre as zona,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.categoria_id = 126
    AND tz.torneo_id = 46
    ORDER BY p.fecha_hora NULLS LAST, p.id_partido
""")

partidos = cur.fetchall()

print(f"\n📊 Total partidos de 7ma: {len(partidos)}")

# Contar por tipo
cur.execute("""
    SELECT 
        p.tipo,
        COUNT(*) as total
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE p.categoria_id = 126
    AND tz.torneo_id = 46
    GROUP BY p.tipo
""")

tipos = cur.fetchall()

print("\nDistribución por tipo:")
for t in tipos:
    print(f"  {t['tipo']}: {t['total']} partidos")

# Mostrar partidos con tipo incorrecto
print("\n" + "=" * 80)
print("PARTIDOS CON TIPO INCORRECTO")
print("=" * 80)

incorrectos = [p for p in partidos if p['tipo'] != 'torneo' or p['id_torneo'] != 46]

if incorrectos:
    print(f"\n⚠️  {len(incorrectos)} partidos con tipo incorrecto:")
    
    for p in incorrectos:
        print(f"\n  Partido {p['id_partido']}: tipo={p['tipo']}, id_torneo={p['id_torneo']}, fase={p['fase']}")
        if p['fecha_hora']:
            print(f"    {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
        else:
            print(f"    SIN HORARIO")
        print(f"    {p['categoria']} - {p['zona']}")
        print(f"    {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")
    
    # Corregir
    print("\n" + "=" * 80)
    print("CORRIGIENDO PARTIDOS")
    print("=" * 80)
    
    for p in incorrectos:
        cur.execute("""
            UPDATE partidos
            SET tipo = 'torneo', id_torneo = 46, fase = 'zona'
            WHERE id_partido = %s
        """, (p['id_partido'],))
        print(f"  ✅ Partido {p['id_partido']} corregido")
    
    conn.commit()
    print(f"\n✅ {len(incorrectos)} partidos corregidos")
else:
    print("\n✅ Todos los partidos de 7ma tienen tipo='torneo' e id_torneo=46")

# Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL")
print("=" * 80)

cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN tipo = 'torneo' THEN 1 END) as tipo_torneo,
        COUNT(CASE WHEN id_torneo = 46 THEN 1 END) as id_torneo_46,
        COUNT(CASE WHEN fase = 'zona' THEN 1 END) as fase_zona
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE p.categoria_id = 126
    AND tz.torneo_id = 46
""")

stats = cur.fetchone()

print(f"\nTotal partidos 7ma: {stats['total']}")
print(f"  Con tipo='torneo': {stats['tipo_torneo']}")
print(f"  Con id_torneo=46: {stats['id_torneo_46']}")
print(f"  Con fase='zona': {stats['fase_zona']}")

if stats['total'] == stats['tipo_torneo'] == stats['id_torneo_46'] == stats['fase_zona']:
    print("\n✅ Todos los partidos están correctos")
else:
    print("\n⚠️  Aún hay partidos con datos incorrectos")

cur.close()
conn.close()
