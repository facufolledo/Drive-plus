import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR ESTADO PARTIDOS 7MA - TORNEO 46")
print("=" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.estado,
        p.ganador_pareja_id,
        p.resultado_padel,
        tz.nombre as zona
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE p.id_torneo = 46
    AND p.categoria_id = 126
    AND p.fase = 'zona'
    ORDER BY tz.numero_orden, p.id_partido
""")

partidos = cur.fetchall()

print(f"\nTotal partidos de zona: {len(partidos)}")

# Agrupar por estado
por_estado = {}
for p in partidos:
    estado = p['estado']
    if estado not in por_estado:
        por_estado[estado] = []
    por_estado[estado].append(p)

print("\nPartidos por estado:")
for estado, lista in por_estado.items():
    print(f"  {estado}: {len(lista)} partidos")

# Verificar si tienen ganador pero no están finalizados
con_ganador_no_finalizados = [p for p in partidos if p['ganador_pareja_id'] and p['estado'] != 'finalizado']

print(f"\nPartidos con ganador pero NO finalizados: {len(con_ganador_no_finalizados)}")

if con_ganador_no_finalizados:
    print("\nPrimeros 5:")
    for p in con_ganador_no_finalizados[:5]:
        print(f"  Partido {p['id_partido']} ({p['zona']}): estado='{p['estado']}', ganador={p['ganador_pareja_id']}")

# PASO 2: Actualizar estado a 'finalizado' si tienen ganador
if con_ganador_no_finalizados:
    print("\n2️⃣  ACTUALIZAR ESTADO A 'finalizado'")
    print("-" * 80)
    
    respuesta = input(f"\n¿Actualizar {len(con_ganador_no_finalizados)} partidos a estado 'finalizado'? (s/n): ")
    
    if respuesta.lower() == 's':
        for p in con_ganador_no_finalizados:
            cur.execute("""
                UPDATE partidos
                SET estado = 'finalizado'
                WHERE id_partido = %s
            """, (p['id_partido'],))
        
        conn.commit()
        print(f"\n✅ {len(con_ganador_no_finalizados)} partidos actualizados a 'finalizado'")
    else:
        print("\n❌ Operación cancelada")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("VERIFICACIÓN COMPLETADA")
print("=" * 80)
