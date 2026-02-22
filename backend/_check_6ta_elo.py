import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Verificar historial de los jugadores de 6ta que tenían partidos con resultado
    # Ruarte (50), Hrellac (502), Ortiz (494), Speziale (197)
    for uid in [50, 502, 494, 197]:
        u = c.execute(text("""
            SELECT u.rating, u.partidos_jugados, pu.nombre || ' ' || pu.apellido
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        hist = c.execute(text("""
            SELECT id_partido, rating_antes, delta, rating_despues
            FROM historial_rating WHERE id_usuario = :uid ORDER BY id_historial
        """), {"uid": uid}).fetchall()
        print(f"ID {uid}: {u[2]} rating={u[0]} partidos={u[1]}")
        for h in hist:
            print(f"  P{h[0]}: {h[1]} -> {h[3]} (delta {h[2]})")
        if not hist:
            print(f"  Sin historial")
    
    # Verificar si hay historial huérfano (partidos que ya no existen)
    huerfanos = c.execute(text("""
        SELECT h.id_partido, COUNT(*) 
        FROM historial_rating h
        LEFT JOIN partidos p ON h.id_partido = p.id_partido
        WHERE p.id_partido IS NULL
        GROUP BY h.id_partido
    """)).fetchall()
    print(f"\nHistorial huérfano (partidos eliminados): {len(huerfanos)}")
    for h in huerfanos:
        print(f"  P{h[0]}: {h[1]} registros")
