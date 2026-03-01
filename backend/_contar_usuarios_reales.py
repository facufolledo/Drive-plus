"""Contar usuarios reales (no temp) en el sistema"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== ESTADÍSTICAS DE USUARIOS ===\n")
    
    # Total usuarios
    total = conn.execute(text("SELECT COUNT(*) FROM usuarios")).fetchone()[0]
    print(f"Total usuarios: {total}")
    
    # Usuarios reales (no temp)
    reales = conn.execute(text("""
        SELECT COUNT(*) FROM usuarios 
        WHERE email NOT LIKE '%@driveplus.temp' 
        AND email NOT LIKE '%@temp.com'
    """)).fetchone()[0]
    print(f"Usuarios reales: {reales}")
    
    # Temps T38
    temps_t38 = conn.execute(text("""
        SELECT COUNT(*) FROM usuarios 
        WHERE email LIKE '%@driveplus.temp'
    """)).fetchone()[0]
    print(f"Temps T38: {temps_t38}")
    
    # Temps T42
    temps_t42 = conn.execute(text("""
        SELECT COUNT(*) FROM usuarios 
        WHERE email LIKE '%@temp.com'
    """)).fetchone()[0]
    print(f"Temps T42: {temps_t42}")
    
    print(f"\n=== DESGLOSE USUARIOS REALES ===\n")
    
    # Usuarios con Firebase (password_hash vacío o null)
    firebase = conn.execute(text("""
        SELECT COUNT(*) FROM usuarios 
        WHERE (password_hash IS NULL OR password_hash = '')
        AND email NOT LIKE '%@driveplus.temp' 
        AND email NOT LIKE '%@temp.com'
    """)).fetchone()[0]
    print(f"Con Firebase: {firebase}")
    
    # Usuarios con password local
    local = conn.execute(text("""
        SELECT COUNT(*) FROM usuarios 
        WHERE password_hash IS NOT NULL AND password_hash != ''
        AND email NOT LIKE '%@driveplus.temp' 
        AND email NOT LIKE '%@temp.com'
    """)).fetchone()[0]
    print(f"Con password local: {local}")
    
    print(f"\n=== USUARIOS REALES CON PARTIDOS JUGADOS ===\n")
    
    con_partidos = conn.execute(text("""
        SELECT COUNT(*) FROM usuarios 
        WHERE partidos_jugados > 0
        AND email NOT LIKE '%@driveplus.temp' 
        AND email NOT LIKE '%@temp.com'
    """)).fetchone()[0]
    print(f"Con partidos jugados: {con_partidos}")
    
    sin_partidos = conn.execute(text("""
        SELECT COUNT(*) FROM usuarios 
        WHERE partidos_jugados = 0
        AND email NOT LIKE '%@driveplus.temp' 
        AND email NOT LIKE '%@temp.com'
    """)).fetchone()[0]
    print(f"Sin partidos jugados: {sin_partidos}")
    
    print("\n✅ Análisis completado")
