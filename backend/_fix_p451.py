import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Solo cambiar el resultado: de 1-6 1-6 a 5-7 3-6
    # Pareja1=625 (Ortiz/Speziale), Pareja2=631 (Ruarte/Ellerak)
    # Ruarte ganó 7-5 6-3, así que equipoA=625 sacó 5 y 3, equipoB=631 sacó 7 y 6
    nuevo_resultado = '{"sets": [{"gamesEquipoA": 5, "gamesEquipoB": 7, "ganador": "equipoB", "completado": true}, {"gamesEquipoA": 3, "gamesEquipoB": 6, "ganador": "equipoB", "completado": true}]}'
    
    c.execute(text("UPDATE partidos SET resultado_padel = CAST(:r AS jsonb) WHERE id_partido = 451"),
             {"r": nuevo_resultado})
    c.commit()
    
    # Verificar
    p = c.execute(text("SELECT resultado_padel FROM partidos WHERE id_partido = 451")).fetchone()
    print(f"P451 resultado actualizado: {p[0]}")
