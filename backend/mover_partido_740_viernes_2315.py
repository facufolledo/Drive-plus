#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=engine)()

# Mover partido 740 al viernes 06/03 23:15
s.execute(text("UPDATE partidos SET fecha_hora = '2026-03-06 23:15:00' WHERE id_partido = 740"))
s.commit()
print("✅ Partido 740 movido al viernes 06/03 23:15")
