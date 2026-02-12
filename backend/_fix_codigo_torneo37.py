"""Asignar codigo 'zf' al torneo 37 para que cuente en el ranking del circuito Zona Fitness"""
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

print("Antes:")
cur.execute("SELECT id, nombre, codigo FROM torneos WHERE id = 37")
row = cur.fetchone()
print(f"  Torneo 37: nombre='{row[1]}', codigo='{row[2]}'")

cur.execute("UPDATE torneos SET codigo = 'zf' WHERE id = 37")
conn.commit()

print("\nDespués:")
cur.execute("SELECT id, nombre, codigo FROM torneos WHERE id = 37")
row = cur.fetchone()
print(f"  Torneo 37: nombre='{row[1]}', codigo='{row[2]}'")

print("\nTorneos con codigo 'zf' ahora:")
cur.execute("SELECT id, nombre, estado, codigo FROM torneos WHERE codigo = 'zf'")
for row in cur.fetchall():
    print(f"  id={row[0]}, nombre='{row[1]}', estado='{row[2]}'")

conn.close()
print("\nListo! Ahora el ranking del circuito debería mostrar los jugadores del torneo 37.")
