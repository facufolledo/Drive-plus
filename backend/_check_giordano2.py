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

cur.execute("SELECT horarios_disponibles, reglas_json FROM torneos WHERE id = 38")
row = cur.fetchone()
h = row[0]
if isinstance(h, str):
    h = json.loads(h)
print(f'Horarios torneo 38: {json.dumps(h, indent=2)}')

r = row[1]
if isinstance(r, str):
    r = json.loads(r)
print(f'\nReglas: {json.dumps(r, indent=2)}')

# Ver canchas del torneo
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'torneos_canchas' ORDER BY ordinal_position")
print("\nColumnas torneos_canchas:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

cur.execute("SELECT * FROM torneos_canchas WHERE torneo_id = 38")
print("\nCanchas torneo 38:")
for row in cur.fetchall():
    print(f"  {row}")

conn.close()
