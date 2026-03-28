import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

# Obtener categoria_id de 7ma
cur.execute("SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma'")
categoria_id = cur.fetchone()['id']

# Distribución por día
cur.execute("""
    SELECT 
        CASE 
            WHEN EXTRACT(DAY FROM fecha_hora) = 27 THEN 'Viernes 27'
            WHEN EXTRACT(DAY FROM fecha_hora) = 28 THEN 'Sábado 28'
            ELSE 'Otro'
        END as dia,
        COUNT(*) as total
    FROM partidos
    WHERE id_torneo = 46 AND categoria_id = %s
    GROUP BY dia
    ORDER BY dia
""", (categoria_id,))

print("📊 Distribución de partidos de 7ma por día:\n")
for row in cur.fetchall():
    print(f"  {row['dia']}: {row['total']} partidos")

# Partidos del sábado
cur.execute("""
    SELECT 
        p.id_partido,
        TO_CHAR(p.fecha_hora, 'HH24:MI') as hora,
        z.nombre as zona
    FROM partidos p
    JOIN torneo_zonas z ON p.zona_id = z.id
    WHERE p.id_torneo = 46 
    AND p.categoria_id = %s
    AND EXTRACT(DAY FROM p.fecha_hora) = 28
    ORDER BY p.fecha_hora
""", (categoria_id,))

print("\n📋 Partidos del sábado 28:")
for p in cur.fetchall():
    print(f"  Partido {p['id_partido']}: {p['zona']} - {p['hora']}")

cur.close()
conn.close()
