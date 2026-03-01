"""Migrar duplicados de T42 a cuentas reales y limpiar temps innecesarios"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("=" * 80)
print("MIGRACIÓN DE DUPLICADOS T42")
print("=" * 80)

with engine.connect() as c:
    # 1. Nicolás Peñaloza: temp 583 → real 29
    print("\n1. Migrando Nicolás Peñaloza (temp 583 → real 29)...")
    
    # Verificar pareja actual
    pareja = c.execute(text("""
        SELECT id, jugador1_id, jugador2_id, torneo_id, categoria_id
        FROM torneos_parejas
        WHERE (jugador1_id = 583 OR jugador2_id = 583) AND torneo_id = 42
    """)).fetchone()
    
    if pareja:
        print(f"   Pareja encontrada: ID={pareja[0]}, cat={pareja[4]}")
        
        # Actualizar pareja
        if pareja[1] == 583:
            c.execute(text("UPDATE torneos_parejas SET jugador1_id = 29 WHERE id = :pid"), {"pid": pareja[0]})
            print(f"   ✓ Actualizado jugador1_id: 583 → 29")
        else:
            c.execute(text("UPDATE torneos_parejas SET jugador2_id = 29 WHERE id = :pid"), {"pid": pareja[0]})
            print(f"   ✓ Actualizado jugador2_id: 583 → 29")
        
        # Actualizar rating del usuario real si es necesario
        c.execute(text("""
            UPDATE usuarios 
            SET rating = 1400
            WHERE id_usuario = 29 AND rating != 1400
        """))
        print(f"   ✓ Rating actualizado en usuario real")
        
        c.commit()
    else:
        print("   ⚠ No se encontró pareja con temp 583")
    
    # 2. Gastón Romero: temp 593 → real 91
    print("\n2. Migrando Gastón Romero (temp 593 → real 91)...")
    
    pareja = c.execute(text("""
        SELECT id, jugador1_id, jugador2_id, torneo_id, categoria_id
        FROM torneos_parejas
        WHERE (jugador1_id = 593 OR jugador2_id = 593) AND torneo_id = 42
    """)).fetchone()
    
    if pareja:
        print(f"   Pareja encontrada: ID={pareja[0]}, cat={pareja[4]}")
        
        # Actualizar pareja
        if pareja[1] == 593:
            c.execute(text("UPDATE torneos_parejas SET jugador1_id = 91 WHERE id = :pid"), {"pid": pareja[0]})
            print(f"   ✓ Actualizado jugador1_id: 593 → 91")
        else:
            c.execute(text("UPDATE torneos_parejas SET jugador2_id = 91 WHERE id = :pid"), {"pid": pareja[0]})
            print(f"   ✓ Actualizado jugador2_id: 593 → 91")
        
        # Actualizar rating del usuario real si es necesario
        c.execute(text("""
            UPDATE usuarios 
            SET rating = 1400
            WHERE id_usuario = 91 AND rating != 1400
        """))
        print(f"   ✓ Rating actualizado en usuario real")
        
        c.commit()
    else:
        print("   ⚠ No se encontró pareja con temp 593")
    
    # 3. Borrar temp de Joaquín Mercado (512)
    print("\n3. Eliminando temp de Joaquín Mercado (ID 512)...")
    
    # Verificar que no esté en ninguna pareja
    parejas = c.execute(text("""
        SELECT id FROM torneos_parejas
        WHERE jugador1_id = 512 OR jugador2_id = 512
    """)).fetchall()
    
    if parejas:
        print(f"   ⚠ Usuario 512 está en {len(parejas)} pareja(s), NO se eliminará")
    else:
        # Eliminar perfil
        c.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = 512"))
        # Eliminar usuario
        c.execute(text("DELETE FROM usuarios WHERE id_usuario = 512"))
        c.commit()
        print(f"   ✓ Usuario 512 eliminado")
    
    # 4. Verificar resultado final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
    # Parejas de T42 con los usuarios migrados
    print("\nParejas en T42 con Peñaloza (29) y Romero (91):")
    parejas = c.execute(text("""
        SELECT tp.id, 
               u1.nombre_usuario as j1, u2.nombre_usuario as j2,
               c.nombre as categoria
        FROM torneos_parejas tp
        JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
        JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
        JOIN torneo_categorias c ON tp.categoria_id = c.id
        WHERE tp.torneo_id = 42 
          AND (tp.jugador1_id IN (29, 91) OR tp.jugador2_id IN (29, 91))
        ORDER BY tp.id
    """)).fetchall()
    
    for p in parejas:
        print(f"  Pareja {p[0]}: {p[1]} / {p[2]} - {p[3]}")
    
    # Verificar que los temps ya no existen en T42
    print("\nVerificando que temps 583 y 593 ya no están en T42:")
    temps = c.execute(text("""
        SELECT id FROM torneos_parejas
        WHERE torneo_id = 42 AND (jugador1_id IN (583, 593) OR jugador2_id IN (583, 593))
    """)).fetchall()
    
    if temps:
        print(f"  ⚠ Aún hay {len(temps)} pareja(s) con temps")
    else:
        print(f"  ✓ No hay parejas con temps 583 o 593")
    
    # Verificar usuario 512
    print("\nVerificando eliminación de usuario 512:")
    u512 = c.execute(text("SELECT id_usuario FROM usuarios WHERE id_usuario = 512")).fetchone()
    if u512:
        print(f"  ⚠ Usuario 512 aún existe")
    else:
        print(f"  ✓ Usuario 512 eliminado correctamente")

print("\n✅ Migración completada")
