"""Analizar duplicados que están en parejas del T42"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# IDs de los duplicados encontrados (temp nuevos T42)
duplicados_t42 = [
    598,  # Lurdes Martinez (duplicado de Lucas Martinez 194?)
]

# Otros posibles duplicados a revisar
otros_duplicados = [
    (539, 6),    # Matías Castelli
    (551, 195),  # Tiago Córdoba
    (552, 504),  # Camilo Nieto
    (541, 560),  # Facundo Rodríguez
]

with engine.connect() as conn:
    print("=== DUPLICADOS EN PAREJAS T42 ===\n")
    
    # Verificar parejas T42
    parejas = conn.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.categoria_id,
               p1.nombre || ' ' || p1.apellido as j1,
               p2.nombre || ' ' || p2.apellido as j2,
               u1.email as email1, u2.email as email2
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
        LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
        LEFT JOIN usuarios u1 ON u1.id_usuario = tp.jugador1_id
        LEFT JOIN usuarios u2 ON u2.id_usuario = tp.jugador2_id
        WHERE tp.torneo_id = 42
        ORDER BY tp.categoria_id, tp.id
    """)).fetchall()
    
    print(f"Total parejas T42: {len(parejas)}\n")
    
    # Buscar duplicados en las parejas
    ids_en_parejas = set()
    for p in parejas:
        ids_en_parejas.add(p[1])
        ids_en_parejas.add(p[2])
    
    print("=== DUPLICADOS DETECTADOS EN T42 ===")
    
    # Lurdes Martinez vs Lucas Martinez
    if 598 in ids_en_parejas:
        print("\n1. Lurdes Martinez (598) está en T42")
        pareja = [p for p in parejas if p[1] == 598 or p[2] == 598][0]
        print(f"   Pareja {pareja[0]}: {pareja[4]} / {pareja[5]}")
        print(f"   ⚠️ Posible duplicado con Lucas Martinez (194)")
        print(f"   ACCIÓN: Revisar si son la misma persona")
    
    print("\n=== OTROS USUARIOS T42 A REVISAR ===")
    
    # Listar todos los temps T42
    temps_t42 = conn.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email
        FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.email LIKE '%@temp.com'
        ORDER BY u.id_usuario
    """)).fetchall()
    
    temps_en_t42 = [t for t in temps_t42 if t[0] in ids_en_parejas]
    
    print(f"\nTemps T42 en parejas ({len(temps_en_t42)}):")
    for t in temps_en_t42:
        print(f"  {t[0]}: {t[1]} {t[2]}")
