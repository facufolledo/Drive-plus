#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=engine)()
s.execute(text("UPDATE partidos SET fecha_hora = '2026-03-07 13:40:00', cancha_id = 91 WHERE id_partido = 762"))
s.commit()
print("✅ Partido 762 movido a sábado 13:40 Cancha 3")
