"""Migrar Facundo Rodríguez temp 541 → real 560"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("=" * 80)
print("MIGRACIÓN FACUNDO RODRÍGUEZ")
print("=" * 80)

with engine.connect() as c:
    # Verificar pareja del temp
    pareja = c.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id, t.nombre, tc.nombre as categoria
        FROM torneos_parejas tp
        JOIN torneos t ON tp.torneo_id = t.id
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        WHERE (tp.jugador1_id = 541 OR tp.jugador2_id = 541)
    """)).fetchone()
    
    if pareja:
        print(f"\nPareja encontrada:")
        print(f"  ID: {pareja[0]}")
        print(f"  Torneo: {pareja[3]}")
        print(f"  Categoría: {pareja[4]}")
        print(f"  Jugadores: {pareja[1]} / {pareja[2]}")
        
        # Actualizar pareja
        if pareja[1] == 541:
            c.execute(text("UPDATE torneos_parejas SET jugador1_id = 560 WHERE id = :pid"), {"pid": pareja[0]})
            print(f"\n✓ Actualizado jugador1_id: 541 → 560")
        else:
            c.execute(text("UPDATE torneos_parejas SET jugador2_id = 560 WHERE id = :pid"), {"pid": pareja[0]})
            print(f"\n✓ Actualizado jugador2_id: 541 → 560")
        
        # Actualizar rating del usuario real (usar el del temp que tiene partidos jugados)
        c.execute(text("""
            UPDATE usuarios 
            SET rating = 739, partidos_jugados = 3
            WHERE id_usuario = 560
        """))
        print(f"✓ Rating y partidos actualizados en usuario real (739, 3 partidos)")
        
        # Migrar historial de rating si existe
        historial = c.execute(text("""
            SELECT COUNT(*) FROM historial_rating WHERE id_usuario = 541
        """)).scalar()
        
        if historial > 0:
            c.execute(text("""
                UPDATE historial_rating SET id_usuario = 560 WHERE id_usuario = 541
            """))
            print(f"✓ Migrado historial de rating ({historial} registros)")
        
        c.commit()
        
        # Eliminar temp
        print(f"\nEliminando usuario temp 541...")
        c.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = 541"))
        c.execute(text("DELETE FROM usuarios WHERE id_usuario = 541"))
        c.commit()
        print(f"✓ Usuario temp eliminado")
        
        # Verificar
        print(f"\n{'=' * 80}")
        print("VERIFICACIÓN")
        print(f"{'=' * 80}")
        
        pareja_final = c.execute(text("""
            SELECT tp.id, u1.nombre_usuario, u2.nombre_usuario, u1.rating, u2.rating
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": pareja[0]}).fetchone()
        
        print(f"\nPareja {pareja_final[0]}:")
        print(f"  {pareja_final[1]} (R={pareja_final[3]}) / {pareja_final[2]} (R={pareja_final[4]})")
        
        temp_existe = c.execute(text("SELECT id_usuario FROM usuarios WHERE id_usuario = 541")).fetchone()
        if temp_existe:
            print(f"\n⚠ Usuario 541 aún existe")
        else:
            print(f"\n✅ Usuario 541 eliminado correctamente")
    else:
        print("\n⚠ No se encontró pareja con usuario 541")

print("\n" + "=" * 80)
