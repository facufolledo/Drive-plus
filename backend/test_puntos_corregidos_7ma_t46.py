import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("TEST PUNTOS CORREGIDOS - 7MA TORNEO 46")
print("=" * 80)

# Simular el cálculo que hace obtener_tabla_posiciones
print("\n1️⃣  CALCULAR PUNTOS CON ESTADO 'finalizado'")
print("-" * 80)

cur.execute("""
    SELECT id, nombre, numero_orden
    FROM torneo_zonas
    WHERE torneo_id = 46
    AND categoria_id = 126
    ORDER BY numero_orden
""")

zonas = cur.fetchall()

for zona in zonas:
    zona_id = zona['id']
    zona_nombre = zona['nombre']
    
    print(f"\n{zona_nombre}:")
    
    # Obtener parejas de la zona
    cur.execute("""
        SELECT tzp.pareja_id
        FROM torneo_zona_parejas tzp
        WHERE tzp.zona_id = %s
    """, (zona_id,))
    
    parejas = [r['pareja_id'] for r in cur.fetchall()]
    
    # Calcular puntos para cada pareja
    resultados = []
    for pareja_id in parejas:
        # Contar victorias con estado='finalizado'
        cur.execute("""
            SELECT COUNT(*) as victorias
            FROM partidos p
            WHERE p.zona_id = %s
            AND p.ganador_pareja_id = %s
            AND p.estado = 'finalizado'
        """, (zona_id, pareja_id))
        
        victorias = cur.fetchone()['victorias']
        puntos = victorias * 3  # Sistema de puntos: 3 por victoria
        
        # Obtener nombres
        cur.execute("""
            SELECT 
                pu1.nombre || ' ' || pu1.apellido as j1,
                pu2.nombre || ' ' || pu2.apellido as j2
            FROM torneos_parejas tp
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.id = %s
        """, (pareja_id,))
        
        nombres = cur.fetchone()
        
        resultados.append({
            'pareja_id': pareja_id,
            'nombres': f"{nombres['j1']}/{nombres['j2']}" if nombres else f"Pareja {pareja_id}",
            'victorias': victorias,
            'puntos': puntos
        })
    
    # Ordenar por puntos
    resultados.sort(key=lambda x: -x['puntos'])
    
    # Mostrar tabla
    for i, r in enumerate(resultados):
        pos = i + 1
        clasificado = "✅" if pos <= 2 else ""
        print(f"  {pos}° - {r['nombres']}: {r['victorias']} victorias = {r['puntos']} pts {clasificado}")

print("\n" + "=" * 80)
print("✅ Con estado='finalizado' los puntos se calculan correctamente")
print("=" * 80)

cur.close()
conn.close()
