"""Mover P465 a cancha libre a las 23:00 (C6 está ocupada por P396 a 22:50)"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Ver qué canchas están ocupadas entre 22:10 y 23:50 (ventana de 50min antes y después)
    ocupadas = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, tc.nombre
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_torneo = 38 
          AND p.fecha_hora >= '2026-02-20 22:10:00'
          AND p.fecha_hora <= '2026-02-20 23:50:00'
        ORDER BY p.fecha_hora
    """)).fetchall()
    
    print("Partidos cerca de 23:00 viernes:")
    for r in ocupadas:
        print(f"  P{r[0]} {r[1]} {r[3]} (ID {r[2]})")
    
    # Canchas ocupadas a las 23:00 o que solapan con 23:00-23:50
    cancha_ids_ocupadas = set()
    for r in ocupadas:
        cancha_ids_ocupadas.add(r[2])
    
    print(f"\nCanchas con partidos en ventana: {cancha_ids_ocupadas}")
    
    # Buscar cancha libre
    for cid in [76, 77, 78, 79]:
        if cid not in cancha_ids_ocupadas:
            nombre = c.execute(text("SELECT nombre FROM torneo_canchas WHERE id = :id"), {"id": cid}).fetchone()[0]
            print(f"\nMoviendo P465 a {nombre} (ID {cid})")
            c.execute(text("UPDATE partidos SET cancha_id = :c WHERE id_partido = 465"), {"c": cid})
            c.commit()
            print("✅ Hecho")
            break
    else:
        print("\n❌ Todas las canchas ocupadas en esa ventana")
        # Intentar con C8 (79) que puede no tener partido exacto a 23:00
        print("Verificando C8 específicamente a las 23:00...")
        c8 = c.execute(text("""
            SELECT id_partido, fecha_hora FROM partidos 
            WHERE id_torneo = 38 AND cancha_id = 79 
            AND fecha_hora BETWEEN '2026-02-20 22:10:00' AND '2026-02-20 23:50:00'
        """)).fetchall()
        if not c8:
            print("C8 libre! Moviendo...")
            c.execute(text("UPDATE partidos SET cancha_id = 79 WHERE id_partido = 465"))
            c.commit()
            print("✅ Hecho")
