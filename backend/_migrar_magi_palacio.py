"""Migrar temps a cuentas reales: Juan Magi (511→562), Flavio Palacio (542→564)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

MIGRACIONES = [
    {"nombre": "Juan Magi", "temp_id": 511, "real_id": 562},
    {"nombre": "Flavio Palacio", "temp_id": 542, "real_id": 564},
]

with engine.connect() as conn:
    for m in MIGRACIONES:
        temp_id = m["temp_id"]
        real_id = m["real_id"]
        nombre = m["nombre"]
        
        print(f"\n{'='*60}")
        print(f"MIGRANDO: {nombre} (temp {temp_id} → real {real_id})")
        print(f"{'='*60}")
        
        # 1. Verificar que el temp existe
        temp = conn.execute(text(
            "SELECT id_usuario, email FROM usuarios WHERE id_usuario = :id"
        ), {"id": temp_id}).fetchone()
        if not temp:
            print(f"  ❌ Temp {temp_id} no existe, saltando")
            continue
        print(f"  Temp: {temp[1]}")
        
        # 2. Verificar que el real existe
        real = conn.execute(text(
            "SELECT id_usuario, email FROM usuarios WHERE id_usuario = :id"
        ), {"id": real_id}).fetchone()
        if not real:
            print(f"  ❌ Real {real_id} no existe, saltando")
            continue
        print(f"  Real: {real[1]}")
        
        # 3. Migrar torneos_parejas (jugador1_id y jugador2_id)
        r1 = conn.execute(text(
            "UPDATE torneos_parejas SET jugador1_id = :real WHERE jugador1_id = :temp"
        ), {"real": real_id, "temp": temp_id})
        r2 = conn.execute(text(
            "UPDATE torneos_parejas SET jugador2_id = :real WHERE jugador2_id = :temp"
        ), {"real": real_id, "temp": temp_id})
        print(f"  torneos_parejas: j1={r1.rowcount}, j2={r2.rowcount}")
        
        # 4. Migrar historial_rating
        r3 = conn.execute(text(
            "UPDATE historial_rating SET id_usuario = :real WHERE id_usuario = :temp"
        ), {"real": real_id, "temp": temp_id})
        print(f"  historial_rating: {r3.rowcount}")
        
        # 5. Migrar rating del temp al real (copiar rating actual)
        temp_rating = conn.execute(text(
            "SELECT rating, id_categoria FROM usuarios WHERE id_usuario = :id"
        ), {"id": temp_id}).fetchone()
        if temp_rating and temp_rating[0]:
            conn.execute(text(
                "UPDATE usuarios SET rating = :r, id_categoria = :c WHERE id_usuario = :id"
            ), {"r": temp_rating[0], "c": temp_rating[1], "id": real_id})
            print(f"  Rating copiado: {temp_rating[0]} (cat {temp_rating[1]})")
        
        # 6. Eliminar perfil del temp
        conn.execute(text(
            "DELETE FROM perfil_usuarios WHERE id_usuario = :id"
        ), {"id": temp_id})
        
        # 8. Eliminar usuario temp
        conn.execute(text(
            "DELETE FROM usuarios WHERE id_usuario = :id"
        ), {"id": temp_id})
        print(f"  ✅ Temp {temp_id} eliminado")
    
    conn.commit()
    print("\n✅ MIGRACIÓN COMPLETA")
    
    # Verificar
    print("\n=== VERIFICACIÓN ===")
    for m in MIGRACIONES:
        parejas = conn.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.id_torneo
            FROM torneos_parejas tp
            WHERE tp.jugador1_id = :rid OR tp.jugador2_id = :rid
        """), {"rid": m["real_id"]}).fetchall()
        print(f"\n{m['nombre']} (ID {m['real_id']}):")
        for p in parejas:
            print(f"  Pareja {p[0]} | T{p[3]} | j1={p[1]} j2={p[2]}")
        
        hist = conn.execute(text(
            "SELECT COUNT(*) FROM historial_rating WHERE id_usuario = :id"
        ), {"id": m["real_id"]}).scalar()
        print(f"  Historial: {hist} registros")
