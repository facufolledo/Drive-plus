import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("COMPARAR PARTIDOS - ZONA A vs ZONA E")
print("=" * 80)

# Partido de Zona A (que funciona)
print("\n🔹 PARTIDO DE ZONA A (FUNCIONA)")
print("-" * 80)

cur.execute("""
    SELECT p.*
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 125
    AND tz.nombre = 'Zona A'
    LIMIT 1
""")

partido_a = cur.fetchone()

if partido_a:
    print(f"\nPartido {partido_a['id_partido']}:")
    for key, value in partido_a.items():
        print(f"  {key}: {value}")

# Partidos de Zona E (que NO funcionan)
print("\n" + "=" * 80)
print("🔹 PARTIDOS DE ZONA E (NO FUNCIONAN)")
print("-" * 80)

cur.execute("""
    SELECT p.*
    FROM partidos p
    WHERE p.zona_id = 426
    ORDER BY p.id_partido
""")

partidos_e = cur.fetchall()

for i, p in enumerate(partidos_e, 1):
    print(f"\n{i}. Partido {p['id_partido']}:")
    for key, value in p.items():
        print(f"  {key}: {value}")

# Comparar campos específicos
print("\n" + "=" * 80)
print("COMPARACIÓN DE CAMPOS CRÍTICOS")
print("=" * 80)

if partido_a:
    print("\nZona A (funciona):")
    print(f"  fase: {partido_a.get('fase')}")
    print(f"  tipo_partido: {partido_a.get('tipo_partido')}")
    print(f"  numero_partido: {partido_a.get('numero_partido')}")
    print(f"  estado: {partido_a.get('estado')}")
    
    print("\nZona E (no funciona):")
    for p in partidos_e:
        print(f"\n  Partido {p['id_partido']}:")
        print(f"    fase: {p.get('fase')}")
        print(f"    tipo_partido: {p.get('tipo_partido')}")
        print(f"    numero_partido: {p.get('numero_partido')}")
        print(f"    estado: {p.get('estado')}")

# Verificar si hay diferencias
print("\n" + "=" * 80)
print("DIFERENCIAS DETECTADAS")
print("=" * 80)

diferencias = []

for p in partidos_e:
    if partido_a:
        for key in partido_a.keys():
            if key not in ['id_partido', 'pareja1_id', 'pareja2_id', 'fecha_hora', 'fecha', 'cancha_id', 'created_at', 'updated_at']:
                if p.get(key) != partido_a.get(key):
                    diferencias.append(f"Partido {p['id_partido']}: {key} = {p.get(key)} (Zona A tiene: {partido_a.get(key)})")

if diferencias:
    print("\n⚠️  Diferencias encontradas:")
    for d in diferencias:
        print(f"  - {d}")
    
    # Corregir automáticamente
    print("\n" + "=" * 80)
    print("CORRIGIENDO PARTIDOS DE ZONA E")
    print("=" * 80)
    
    for p in partidos_e:
        updates = []
        values = []
        
        # Copiar campos importantes de Zona A
        if p.get('fase') != partido_a.get('fase') and partido_a.get('fase'):
            updates.append("fase = %s")
            values.append(partido_a.get('fase'))
        
        if p.get('tipo_partido') != partido_a.get('tipo_partido') and partido_a.get('tipo_partido'):
            updates.append("tipo_partido = %s")
            values.append(partido_a.get('tipo_partido'))
        
        if p.get('estado') != partido_a.get('estado') and partido_a.get('estado'):
            updates.append("estado = %s")
            values.append(partido_a.get('estado'))
        
        if updates:
            values.append(p['id_partido'])
            query = f"UPDATE partidos SET {', '.join(updates)} WHERE id_partido = %s"
            cur.execute(query, values)
            print(f"  ✅ Partido {p['id_partido']} actualizado")
    
    conn.commit()
    print("\n✅ Partidos corregidos")
else:
    print("\n✅ No se encontraron diferencias en campos críticos")

# Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL")
print("=" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.fase,
        p.tipo_partido,
        p.estado,
        p.fecha_hora,
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
    WHERE p.zona_id = 426
    ORDER BY p.id_partido
""")

partidos_final = cur.fetchall()

for p in partidos_final:
    print(f"\n✅ Partido {p['id_partido']}: {p['fase']} - {p['tipo_partido']} - {p['estado']}")
    if p['fecha_hora']:
        print(f"   {p['fecha_hora'].strftime('%A %d/%m %H:%M')}")
    else:
        print(f"   SIN HORARIO")
    print(f"   {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")

cur.close()
conn.close()
