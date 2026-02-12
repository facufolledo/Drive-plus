"""Debug: verificar datos del circuito zf y por qué no trae ranking"""
import pg8000
import os
from dotenv import load_dotenv

load_dotenv()

# Parsear DATABASE_URL
db_url = os.getenv("DATABASE_URL", "")
# postgresql+pg8000://user:pass@host/db
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

print("=" * 60)
print("1. Circuitos existentes:")
cur.execute("SELECT id, codigo, nombre, activo FROM circuitos")
for row in cur.fetchall():
    print(f"   id={row[0]}, codigo='{row[1]}', nombre='{row[2]}', activo={row[3]}")

print("\n2. Torneos con codigo='zf':")
cur.execute("SELECT id, nombre, estado, codigo FROM torneos WHERE codigo = 'zf'")
torneos_zf = cur.fetchall()
for row in torneos_zf:
    print(f"   id={row[0]}, nombre='{row[1]}', estado='{row[2]}', codigo='{row[3]}'")

if torneos_zf:
    torneo_ids = [str(t[0]) for t in torneos_zf]
    ids_str = ",".join(torneo_ids)
    
    print(f"\n3. Partidos de torneos con codigo zf (ids: {ids_str}):")
    cur.execute(f"SELECT id_partido, id_torneo, estado FROM partidos WHERE id_torneo IN ({ids_str}) LIMIT 20")
    partidos = cur.fetchall()
    for row in partidos:
        print(f"   id_partido={row[0]}, id_torneo={row[1]}, estado='{row[2]}'")
    
    print(f"\n   Total partidos: {len(partidos)}")
    
    if partidos:
        partido_ids = [str(p[0]) for p in partidos]
        pids_str = ",".join(partido_ids)
        
        print(f"\n4. Historial rating de esos partidos:")
        cur.execute(f"SELECT id, id_usuario, id_partido, delta, rating_antes, rating_despues FROM historial_rating WHERE id_partido IN ({pids_str}) LIMIT 20")
        historial = cur.fetchall()
        for row in historial:
            print(f"   id={row[0]}, usuario={row[1]}, partido={row[2]}, delta={row[3]}, antes={row[4]}, despues={row[5]}")
        print(f"\n   Total registros historial: {len(historial)}")
    else:
        print("\n4. No hay partidos, por eso no hay historial")

print("\n5. Verificando torneo 37 (el que tiene partidos jugados):")
cur.execute("SELECT id, nombre, estado, codigo FROM torneos WHERE id = 37")
t37 = cur.fetchone()
if t37:
    print(f"   id={t37[0]}, nombre='{t37[1]}', estado='{t37[2]}', codigo='{t37[3]}'")
else:
    print("   Torneo 37 no encontrado")

print("\n6. Torneos que tienen partidos confirmados/finalizados:")
cur.execute("""
    SELECT t.id, t.nombre, t.codigo, COUNT(p.id_partido) as total_partidos
    FROM torneos t
    JOIN partidos p ON p.id_torneo = t.id
    WHERE p.estado IN ('finalizado', 'confirmado')
    GROUP BY t.id, t.nombre, t.codigo
    ORDER BY total_partidos DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"   torneo_id={row[0]}, nombre='{row[1]}', codigo='{row[2]}', partidos={row[3]}")

conn.close()
print("\nDone!")
