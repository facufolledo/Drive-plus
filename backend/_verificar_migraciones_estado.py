"""Verificar estado actual de todas las migraciones y qué falta transferir"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Ver tablas que podrían tener referencia a usuarios
    print("=== TABLAS CON PUNTOS/CIRCUITO ===")
    # circuito_puntos?
    tables = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%circuito%'
    """)).fetchall()
    print(f"Tablas circuito: {[t[0] for t in tables]}")
    
    tables2 = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%punto%'
    """)).fetchall()
    print(f"Tablas puntos: {[t[0] for t in tables2]}")
    
    # Columnas de circuito_puntos si existe
    for t in tables + tables2:
        cols = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = :tn ORDER BY ordinal_position
        """), {"tn": t[0]}).fetchall()
        print(f"  {t[0]}: {[c[0] for c in cols]}")

    # Estado actual de los 4 usuarios migrados
    print("\n=== ESTADO ACTUAL USUARIOS MIGRADOS ===")
    for uid, nombre in [(568, "Benjamin Hrellac"), (562, "Juan Magi"), (564, "Flavio Palacio"), (574, "Lucas Mercado Luna")]:
        u = conn.execute(text("""
            SELECT u.id_usuario, u.rating, u.id_categoria, u.partidos_jugados, p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        print(f"\n  {nombre} ({uid}): rating={u[1]}, cat={u[2]}, pj={u[3]}")
        
        # Parejas
        parejas = conn.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
            FROM torneos_parejas tp WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
        """), {"uid": uid}).fetchall()
        pareja_ids = [pa[0] for pa in parejas]
        for pa in parejas:
            print(f"    Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} T{pa[3]}")
        
        # Partidos confirmados
        if pareja_ids:
            pids_str = ','.join(str(p) for p in pareja_ids)
            partidos = conn.execute(text(f"""
                SELECT id_partido, fase, estado, pareja1_id, pareja2_id, ganador_pareja_id
                FROM partidos WHERE estado = 'confirmado'
                  AND (pareja1_id IN ({pids_str}) OR pareja2_id IN ({pids_str}))
                ORDER BY id_partido
            """)).fetchall()
            ganados = sum(1 for p in partidos if p[5] in pareja_ids)
            print(f"    Partidos: {len(partidos)} jugados, {ganados} ganados")
        
        # Historial rating
        hist = conn.execute(text("""
            SELECT COUNT(*) FROM historial_rating WHERE id_usuario = :uid
        """), {"uid": uid}).scalar()
        print(f"    Historial rating: {hist} registros")
        
        # Puntos circuito (si existe la tabla)
        try:
            puntos = conn.execute(text("""
                SELECT * FROM circuito_puntos WHERE usuario_id = :uid
            """), {"uid": uid}).fetchall()
            print(f"    Puntos circuito: {len(puntos)} registros")
            for p in puntos:
                print(f"      {p}")
        except:
            pass
        
        try:
            puntos2 = conn.execute(text("""
                SELECT * FROM circuito_puntos_fase WHERE usuario_id = :uid
            """), {"uid": uid}).fetchall()
            print(f"    Puntos circuito fase: {len(puntos2)} registros")
            for p in puntos2:
                print(f"      {p}")
        except:
            pass

    # Verificar si los temps viejos todavía tienen datos en circuito_puntos
    print("\n=== DATOS RESIDUALES DE TEMPS EN CIRCUITO ===")
    old_temps = [502, 511, 542, 534]
    for tid in old_temps:
        exists = conn.execute(text("SELECT COUNT(*) FROM usuarios WHERE id_usuario = :tid"), {"tid": tid}).scalar()
        if exists:
            print(f"  Temp {tid}: TODAVÍA EXISTE")
        
        try:
            puntos = conn.execute(text("SELECT * FROM circuito_puntos WHERE usuario_id = :tid"), {"tid": tid}).fetchall()
            if puntos:
                print(f"  Temp {tid} circuito_puntos: {len(puntos)} registros")
                for p in puntos:
                    print(f"    {p}")
        except:
            pass
        
        try:
            puntos2 = conn.execute(text("SELECT * FROM circuito_puntos_fase WHERE usuario_id = :tid"), {"tid": tid}).fetchall()
            if puntos2:
                print(f"  Temp {tid} circuito_puntos_fase: {len(puntos2)} registros")
                for p in puntos2:
                    print(f"    {p}")
        except:
            pass
