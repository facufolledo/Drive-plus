"""Corregir partidos de 8va para que coincidan con la imagen del usuario"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Cancha 5=76, Cancha 6=77, Cancha 7=78, Cancha 8=79

with engine.connect() as c:
    # ZONA B:
    # P445: Rodríguez/Castelli vs Pérez/Rodríguez -> vie 15:00 Cancha 6 (estaba Cancha 7)
    c.execute(text("UPDATE partidos SET cancha_id = 77 WHERE id_partido = 445"))
    print("P445: Cancha 7 -> Cancha 6 ✅")

    # P443: Moreno/Antúnez vs Rodríguez/Castelli -> sáb 12:30 Cancha 6 (estaba vie 22:00 Cancha 8)
    c.execute(text("""
        UPDATE partidos SET fecha_hora = '2026-02-21 12:30:00', fecha = '2026-02-21', cancha_id = 77
        WHERE id_partido = 443
    """))
    print("P443: vie 22:00 C8 -> sáb 12:30 Cancha 6 ✅")

    # P444: Moreno/Antúnez vs Pérez/Rodríguez -> sáb 09:00 Cancha 5 (ya OK)
    print("P444: sáb 09:00 Cancha 5 (ya OK) ✅")

    # ZONA C:
    # P446: Moreno/Saracho vs Ferreyra/Cortez -> sáb 09:00 Cancha 7 (ya OK)
    print("P446: sáb 09:00 Cancha 7 (ya OK) ✅")

    # P447: Moreno/Saracho vs Mercado/Callazo -> sáb 12:30 Cancha 7 (estaba Cancha 6)
    c.execute(text("UPDATE partidos SET cancha_id = 78 WHERE id_partido = 447"))
    print("P447: Cancha 6 -> Cancha 7 ✅")

    # P448: Ferreyra/Cortez vs Mercado/Callazo -> sáb 16:00 Cancha 6 (ya OK)
    print("P448: sáb 16:00 Cancha 6 (ya OK) ✅")

    # ZONA D:
    # P449: Frías/Pérez vs Algarrilla/Millicay -> sáb 14:30 Cancha 7 (estaba 14:50 Cancha 5)
    c.execute(text("""
        UPDATE partidos SET fecha_hora = '2026-02-21 14:30:00', cancha_id = 78
        WHERE id_partido = 449
    """))
    print("P449: sáb 14:50 C5 -> sáb 14:30 Cancha 7 ✅")

    c.commit()

    # Verificar todo
    print("\n=== VERIFICACIÓN 8VA COMPLETA ===")
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, tc.nombre, tz.nombre,
               p1n.nombre || ' ' || p1n.apellido || ' / ' || p2n.nombre || ' ' || p2n.apellido,
               p3n.nombre || ' ' || p3n.apellido || ' / ' || p4n.nombre || ' ' || p4n.apellido
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.id_torneo = 38 AND p.categoria_id = 89
        ORDER BY p.zona_id, p.fecha_hora
    """)).fetchall()
    
    current_zona = None
    for r in rows:
        if r[3] != current_zona:
            current_zona = r[3]
            print(f"\n  {r[3]}:")
        fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        dia = fh.strftime('%a %d/%m').replace('Fri','VIE').replace('Sat','SÁB')
        print(f"    P{r[0]} | {dia} {fh.strftime('%H:%M')} | {r[2]} | {r[4]} vs {r[5]}")
