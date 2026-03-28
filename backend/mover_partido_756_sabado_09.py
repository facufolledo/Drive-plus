#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=engine)()

# Mover partido 756 al sábado 07/03 09:00
s.execute(text("UPDATE partidos SET fecha_hora = '2026-03-07 09:00:00' WHERE id_partido = 756"))
s.commit()
print("✅ Partido 756 movido al sábado 07/03 09:00")
