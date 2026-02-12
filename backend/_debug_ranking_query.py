"""Debug: simular la query exacta del endpoint ranking_circuito"""
import pg8000
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL", "")
parts = db_url.replace("postgresql+pg8000://", "").split("@")
user_pass = parts[0].split(":")
host_db = parts[1].split("/")

conn = pg8000.connect(
    user=user_pass[0],
    password=user_pass[1],
    host=host_db[0],
    database=host_db[1],
    ssl_context=True
)
cur = conn.cursor()

# Paso 1: IDs de torneos con codigo zf
cur.execute("SELECT id FROM torneos WHERE codigo = 'zf'")
torneo_ids = [r[0] for r in cur.fetchall()]
print(f"1. Torneo IDs con codigo 'zf': {torneo_ids}")

# Paso 2: Partidos de esos torneos
cur.execute(f"""
    SELECT id_partido, id_torneo, estado 
    FROM partidos 
    WHERE id_torneo IN ({','.join(str(t) for t in torneo_ids)})
    AND estado IN ('finalizado', 'confirmado')
    LIMIT 10
""")
partidos = cur.fetchall()
print(f"\n2. Partidos finalizados/confirmados (primeros 10):")
for p in partidos:
    print(f"   id_partido={p[0]}, id_torneo={p[1]}, estado='{p[2]}'")

cur.execute(f"""
    SELECT COUNT(*) FROM partidos 
    WHERE id_torneo IN ({','.join(str(t) for t in torneo_ids)})
    AND estado IN ('finalizado', 'confirmado')
""")
total = cur.fetchone()[0]
print(f"   Total: {total}")

# Paso 3: Verificar historial_rating para esos partidos
if partidos:
    partido_ids = [str(p[0]) for p in partidos]
    cur.execute(f"""
        SELECT hr.id_usuario, hr.id_partido, hr.delta, hr.rating_antes, hr.rating_despues
        FROM historial_rating hr
        WHERE hr.id_partido IN ({','.join(partido_ids)})
        LIMIT 10
    """)
    historial = cur.fetchall()
    print(f"\n3. Historial rating para esos partidos (primeros 10):")
    for h in historial:
        print(f"   usuario={h[0]}, partido={h[1]}, delta={h[2]}, antes={h[3]}, despues={h[4]}")
    
    cur.execute(f"""
        SELECT COUNT(*) FROM historial_rating hr
        WHERE hr.id_partido IN (
            SELECT id_partido FROM partidos WHERE id_torneo IN ({','.join(str(t) for t in torneo_ids)})
            AND estado IN ('finalizado', 'confirmado')
        )
    """)
    total_hr = cur.fetchone()[0]
    print(f"   Total registros historial: {total_hr}")

# Paso 4: Verificar la columna id_partido en historial_rating
print("\n4. Estructura de historial_rating:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'historial_rating'
    ORDER BY ordinal_position
""")
for col in cur.fetchall():
    print(f"   {col[0]}: {col[1]}")

# Paso 5: Verificar si historial_rating tiene id_partido NULL
cur.execute("SELECT COUNT(*) FROM historial_rating WHERE id_partido IS NULL")
null_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM historial_rating WHERE id_partido IS NOT NULL")
not_null_count = cur.fetchone()[0]
print(f"\n5. historial_rating: id_partido NULL={null_count}, NOT NULL={not_null_count}")

# Paso 6: Muestra algunos registros de historial_rating
cur.execute("SELECT id, id_usuario, id_partido, delta FROM historial_rating ORDER BY id DESC LIMIT 5")
print("\n6. Últimos 5 registros de historial_rating:")
for r in cur.fetchall():
    print(f"   id={r[0]}, usuario={r[1]}, partido={r[2]}, delta={r[3]}")

# Paso 7: Simular la query completa del endpoint
print("\n7. Simulando query del ranking:")
cur.execute(f"""
    SELECT 
        hr.id_usuario,
        SUM(CASE WHEN hr.delta > 0 THEN hr.delta ELSE 0 END) as puntos,
        COUNT(DISTINCT hr.id_partido) as partidos_jugados,
        SUM(CASE WHEN hr.delta > 0 THEN 1 ELSE 0 END) as partidos_ganados
    FROM historial_rating hr
    JOIN partidos p ON hr.id_partido = p.id_partido
    WHERE p.id_torneo IN ({','.join(str(t) for t in torneo_ids)})
    AND p.estado IN ('finalizado', 'confirmado')
    GROUP BY hr.id_usuario
    HAVING SUM(CASE WHEN hr.delta > 0 THEN hr.delta ELSE 0 END) > 0
    ORDER BY puntos DESC
    LIMIT 10
""")
ranking = cur.fetchall()
print(f"   Resultados: {len(ranking)}")
for r in ranking:
    print(f"   usuario={r[0]}, puntos={r[1]}, partidos={r[2]}, ganados={r[3]}")

conn.close()
