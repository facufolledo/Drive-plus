"""
Inscribir 2 parejas nuevas en torneo 38, categoría 6ta:
- Pareja 1: Ruarte Leandro + Ellerak Benjamin (viernes desp de 15)
- Pareja 2: Oliva Bautista + Cruz Juan (viernes desp 18, sábado desp 14)
"""
import pg8000
import os, re, ssl
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
m = re.match(r'postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(\w+)', DATABASE_URL)
user, password, host, port, dbname = m.group(1), m.group(2), m.group(3), int(m.group(4) or 5432), m.group(5)

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

conn = pg8000.connect(host=host, port=port, user=user, password=password, database=dbname, ssl_context=ssl_ctx)
cursor = conn.cursor()

print("=== PASO 1: Buscar usuarios existentes ===")
nombres = ['ruarte', 'ellerak', 'oliva baut', 'cruz juan']
for nombre in nombres:
    parts = nombre.split()
    if len(parts) == 2:
        cursor.execute(
            "SELECT id_usuario, nombre_usuario, nombre, apellido, email FROM usuarios WHERE (LOWER(nombre) LIKE %s AND LOWER(apellido) LIKE %s) OR (LOWER(apellido) LIKE %s AND LOWER(nombre) LIKE %s) LIMIT 5",
            (f"%{parts[0]}%", f"%{parts[1]}%", f"%{parts[0]}%", f"%{parts[1]}%")
        )
    else:
        cursor.execute(
            "SELECT id_usuario, nombre_usuario, nombre, apellido, email FROM usuarios WHERE LOWER(apellido) LIKE %s OR LOWER(nombre_usuario) LIKE %s LIMIT 5",
            (f"%{nombre}%", f"%{nombre}%")
        )
    rows = cursor.fetchall()
    print(f"\n  Búsqueda '{nombre}':")
    if rows:
        for r in rows:
            print(f"    ID={r[0]}, user={r[1]}, nombre={r[2]} {r[3]}, email={r[4]}")
    else:
        print(f"    No encontrado")

# Buscar también por nombre
for nombre in ['leandro', 'benjamin', 'bautista', 'juan']:
    cursor.execute(
        "SELECT id_usuario, nombre_usuario, nombre, apellido, email FROM usuarios WHERE LOWER(nombre) LIKE %s LIMIT 3",
        (f"%{nombre}%",)
    )
    rows = cursor.fetchall()
    if rows:
        print(f"\n  Nombre '{nombre}':")
        for r in rows:
            print(f"    ID={r[0]}, user={r[1]}, nombre={r[2]} {r[3]}, email={r[4]}")

print("\n=== PASO 2: Categorías torneo 38 ===")
cursor.execute("SELECT id, nombre FROM categorias WHERE torneo_id = 38")
cats = cursor.fetchall()
for c in cats:
    print(f"  Cat ID={c[0]}, nombre={c[1]}")

cat_6ta_id = None
for c in cats:
    if '6' in str(c[1]).lower():
        cat_6ta_id = c[0]
        break
print(f"\n  Categoría 6ta ID: {cat_6ta_id}")

if cat_6ta_id:
    cursor.execute(
        "SELECT tp.id, tp.jugador1_id, tp.jugador2_id, u1.nombre, u1.apellido, u2.nombre, u2.apellido FROM torneos_parejas tp LEFT JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario LEFT JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario WHERE tp.torneo_id = 38 AND tp.categoria_id = %s",
        (cat_6ta_id,)
    )
    parejas = cursor.fetchall()
    print(f"  Total parejas inscritas: {len(parejas)}")
    for p in parejas:
        print(f"    Pareja ID={p[0]}: {p[3]} {p[4]} + {p[5]} {p[6]}")

conn.close()
print("\nDone.")
