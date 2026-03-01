"""Verificar que los duplicados fueron eliminados"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

eliminados = [539, 505, 541, 532]

with engine.connect() as conn:
    print("=== VERIFICACIÓN DE LIMPIEZA ===\n")
    
    for uid in eliminados:
        result = conn.execute(text("SELECT COUNT(*) FROM usuarios WHERE id_usuario = :uid"), {"uid": uid}).fetchone()[0]
        if result == 0:
            print(f"  ✅ Usuario {uid} eliminado correctamente")
        else:
            print(f"  ❌ Usuario {uid} AÚN EXISTE")
    
    print("\n=== RESUMEN TORNEO 42 ===")
    parejas = conn.execute(text("""
        SELECT tp.categoria_id, COUNT(*) as total
        FROM torneos_parejas tp
        WHERE tp.torneo_id = 42
        GROUP BY tp.categoria_id
        ORDER BY tp.categoria_id
    """)).fetchall()
    
    categorias = {105: "Principiante", 106: "7ma", 107: "Libre", 108: "5ta", 109: "7ma fem", 110: "6ta fem", 111: "5ta fem"}
    
    for cat_id, total in parejas:
        print(f"  {categorias.get(cat_id, f'Cat {cat_id}')}: {total} parejas")
    
    print("\n✅ Verificación completada")
