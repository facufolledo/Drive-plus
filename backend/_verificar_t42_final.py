"""Verificar estado final del Torneo 42"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("=" * 80)
print("ESTADO FINAL TORNEO 42")
print("=" * 80)

with engine.connect() as c:
    # Info del torneo
    torneo = c.execute(text("""
        SELECT id, nombre, estado, fecha_inicio, fecha_fin
        FROM torneos WHERE id = 42
    """)).fetchone()
    
    print(f"\nTorneo: {torneo[1]} (ID={torneo[0]})")
    print(f"Estado: {torneo[2]}")
    print(f"Fechas: {torneo[3]} a {torneo[4]}")
    
    # Categorías
    print("\n" + "=" * 80)
    print("PAREJAS POR CATEGORÍA")
    print("=" * 80)
    
    categorias = c.execute(text("""
        SELECT tc.id, tc.nombre, tc.genero, COUNT(tp.id) as total_parejas
        FROM torneo_categorias tc
        LEFT JOIN torneos_parejas tp ON tc.id = tp.categoria_id AND tp.torneo_id = 42
        WHERE tc.torneo_id = 42
        GROUP BY tc.id, tc.nombre, tc.genero
        ORDER BY tc.id
    """)).fetchall()
    
    for cat in categorias:
        print(f"\n{cat[1]} ({cat[2]}): {cat[3]} parejas")
        
        # Listar parejas de esta categoría
        parejas = c.execute(text("""
            SELECT tp.id,
                   COALESCE(p1.nombre || ' ' || p1.apellido, u1.nombre_usuario) as j1,
                   COALESCE(p2.nombre || ' ' || p2.apellido, u2.nombre_usuario) as j2,
                   u1.rating as r1, u2.rating as r2,
                   u1.email as e1, u2.email as e2
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios p1 ON u1.id_usuario = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON u2.id_usuario = p2.id_usuario
            WHERE tp.torneo_id = 42 AND tp.categoria_id = :cat_id
            ORDER BY tp.id
        """), {"cat_id": cat[0]}).fetchall()
        
        for p in parejas:
            tipo1 = "TEMP" if (p[5] and ("@temp.com" in p[5] or "@driveplus.temp" in p[5])) else "REAL"
            tipo2 = "TEMP" if (p[6] and ("@temp.com" in p[6] or "@driveplus.temp" in p[6])) else "REAL"
            print(f"  {p[0]:3d}. {p[1]:25s} (R={p[3]}, {tipo1}) / {p[2]:25s} (R={p[4]}, {tipo2})")
    
    # Verificar que no haya temps sin migrar
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE USUARIOS TEMP")
    print("=" * 80)
    
    temps_en_t42 = c.execute(text("""
        SELECT DISTINCT u.id_usuario, u.nombre_usuario, u.email, u.rating
        FROM usuarios u
        JOIN torneos_parejas tp ON (u.id_usuario = tp.jugador1_id OR u.id_usuario = tp.jugador2_id)
        WHERE tp.torneo_id = 42 
          AND (u.email LIKE '%@temp.com' OR u.email LIKE '%@driveplus.temp')
        ORDER BY u.id_usuario
    """)).fetchall()
    
    if temps_en_t42:
        print(f"\n⚠ Hay {len(temps_en_t42)} usuarios temp en T42:")
        for t in temps_en_t42:
            print(f"  ID={t[0]}, user={t[1]}, email={t[2]}, rating={t[3]}")
    else:
        print("\n✅ No hay usuarios temp en T42 - todos migrados correctamente")

print("\n" + "=" * 80)
