import os, json, re
from dotenv import load_dotenv
import pg8000

load_dotenv()
url = os.getenv('DATABASE_URL')
m = re.match(r'postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+?)(?:\?.*)?$', url)
user, pwd, host, port, db = m.groups()
port = int(port) if port else 5432

conn = pg8000.connect(user=user, password=pwd, host=host, port=port, database=db, ssl_context=True)
cur = conn.cursor()

# Buscar Giordano y Tapia
cur.execute("SELECT id_usuario, nombre_usuario FROM usuarios WHERE nombre_usuario ILIKE '%giordano%' OR nombre_usuario ILIKE '%tapia%'")
print("Usuarios encontrados:")
user_ids = []
for row in cur.fetchall():
    print(f"  ID: {row[0]}, Username: {row[1]}")
    user_ids.append(row[0])

# Buscar parejas del torneo 38
for uid in user_ids:
    cur.execute("SELECT id, jugador1_id, jugador2_id, disponibilidad_horaria, categoria_id FROM torneos_parejas WHERE torneo_id = 38 AND (jugador1_id = %s OR jugador2_id = %s)", (uid, uid))
    for row in cur.fetchall():
        print(f'\nPareja ID: {row[0]}, J1: {row[1]}, J2: {row[2]}, Cat: {row[4]}')
        disp = row[3]
        if isinstance(disp, str):
            disp = json.loads(disp)
        print(f'Restricciones (NO puede jugar): {json.dumps(disp, indent=2, ensure_ascii=False)}')

# Horarios torneo
cur.execute("SELECT horarios_disponibles, intervalo_minutos FROM torneos WHERE id = 38")
row = cur.fetchone()
h = row[0]
if isinstance(h, str):
    h = json.loads(h)
print(f'\nHorarios torneo 38: {json.dumps(h, indent=2)}')
print(f'Intervalo: {row[1]} minutos')

conn.close()
