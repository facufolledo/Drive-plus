import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR ANTES DE ELIMINAR TEMPS")
print("=" * 80)

usuarios_a_eliminar = [
    {"id": 175, "nombre": "Dario Barrionuevo (viejo)"},
    {"id": 1102, "nombre": "Pablo Toledo (temp)"},
    {"id": 1154, "nombre": "Mauri Macia (temp)"}
]

for user in usuarios_a_eliminar:
    user_id = user['id']
    print(f"\n{'=' * 80}")
    print(f"USUARIO {user_id}: {user['nombre']}")
    print("=" * 80)
    
    # Parejas en CUALQUIER torneo
    cur.execute("""
        SELECT 
            tp.id,
            tp.torneo_id,
            t.nombre as torneo_nombre
        FROM torneos_parejas tp
        JOIN torneos t ON tp.torneo_id = t.id
        WHERE tp.jugador1_id = %s OR tp.jugador2_id = %s
    """, (user_id, user_id))
    
    parejas = cur.fetchall()
    
    if parejas:
        print(f"\n⚠️  TIENE {len(parejas)} PAREJAS:")
        for p in parejas:
            print(f"  - Pareja {p['id']} en Torneo {p['torneo_id']} ({p['torneo_nombre']})")
    else:
        print(f"\n✓ Sin parejas")
    
    # Partidos en CUALQUIER torneo
    cur.execute("""
        SELECT COUNT(*) as total
        FROM partidos p
        JOIN torneos_parejas tp ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
        WHERE tp.jugador1_id = %s OR tp.jugador2_id = %s
    """, (user_id, user_id))
    
    partidos = cur.fetchone()['total']
    if partidos > 0:
        print(f"  ⚠️  TIENE {partidos} PARTIDOS")
    else:
        print(f"  ✓ Sin partidos")
    
    # Historial rating
    cur.execute("""
        SELECT COUNT(*) as total FROM historial_rating WHERE id_usuario = %s
    """, (user_id,))
    
    historial = cur.fetchone()['total']
    if historial > 0:
        print(f"  ⚠️  TIENE {historial} registros en historial_rating")
    else:
        print(f"  ✓ Sin historial")
    
    # Salas
    cur.execute("""
        SELECT COUNT(*) as total FROM salas WHERE id_creador = %s
    """, (user_id,))
    
    salas = cur.fetchone()['total']
    if salas > 0:
        print(f"  ⚠️  TIENE {salas} salas creadas")
    else:
        print(f"  ✓ Sin salas")
    
    # Decisión
    if parejas or partidos > 0 or historial > 0 or salas > 0:
        print(f"\n❌ NO SE PUEDE ELIMINAR - Tiene referencias activas")
    else:
        print(f"\n✅ SE PUEDE ELIMINAR - Sin referencias")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)

print("\nSi algún usuario tiene parejas en otros torneos (no T46),")
print("necesitamos migrar TODAS sus parejas, no solo las de T46.")

cur.close()
conn.close()
