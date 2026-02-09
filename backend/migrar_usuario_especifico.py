"""
Migra un usuario duplicado a su cuenta real
Uso: python migrar_usuario_especifico.py <id_duplicado> <id_real>
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from sqlalchemy import text

def migrar_usuario(db, id_duplicado, id_real):
    """Migra todos los datos de un usuario duplicado al real"""
    
    # Verificar que ambos usuarios existen
    duplicado = db.execute(text("""
        SELECT u.id_usuario, u.email, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario = :id
    """), {"id": id_duplicado}).fetchone()
    
    real = db.execute(text("""
        SELECT u.id_usuario, u.email, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario = :id
    """), {"id": id_real}).fetchone()
    
    if not duplicado:
        print(f"❌ Usuario duplicado {id_duplicado} no encontrado")
        return False
    
    if not real:
        print(f"❌ Usuario real {id_real} no encontrado")
        return False
    
    print(f"\n📋 Migración:")
    print(f"   DESDE: ID {duplicado[0]} - {duplicado[2]} {duplicado[3]} ({duplicado[1]})")
    print(f"   HACIA: ID {real[0]} - {real[2]} {real[3]} ({real[1]})")
    
    confirmar = input("\n¿Continuar con la migración? (s/n): ").strip().lower()
    if confirmar != 's':
        print("Cancelado")
        return False
    
    print("\n🔄 Migrando datos...")
    
    # 1. Migrar torneos_parejas
    result = db.execute(text("""
        UPDATE torneos_parejas 
        SET jugador1_id = :id_real 
        WHERE jugador1_id = :id_dup
    """), {"id_real": id_real, "id_dup": id_duplicado})
    print(f"   ✅ Parejas (jugador1): {result.rowcount} actualizadas")
    
    result = db.execute(text("""
        UPDATE torneos_parejas 
        SET jugador2_id = :id_real 
        WHERE jugador2_id = :id_dup
    """), {"id_real": id_real, "id_dup": id_duplicado})
    print(f"   ✅ Parejas (jugador2): {result.rowcount} actualizadas")
    
    # 2. Migrar historial_rating
    result = db.execute(text("""
        UPDATE historial_rating 
        SET id_usuario = :id_real 
        WHERE id_usuario = :id_dup
    """), {"id_real": id_real, "id_dup": id_duplicado})
    print(f"   ✅ Historial rating: {result.rowcount} registros actualizados")
    
    # 3. Migrar partido_jugadores
    result = db.execute(text("""
        UPDATE partido_jugadores 
        SET id_usuario = :id_real 
        WHERE id_usuario = :id_dup
    """), {"id_real": id_real, "id_dup": id_duplicado})
    print(f"   ✅ Partido jugadores: {result.rowcount} actualizados")
    
    # 4. Migrar partidos creados
    result = db.execute(text("""
        UPDATE partidos 
        SET id_creador = :id_real 
        WHERE id_creador = :id_dup
    """), {"id_real": id_real, "id_dup": id_duplicado})
    print(f"   ✅ Partidos creados: {result.rowcount} actualizados")
    
    # 5. Eliminar perfil duplicado
    db.execute(text("""
        DELETE FROM perfil_usuarios WHERE id_usuario = :id_dup
    """), {"id_dup": id_duplicado})
    print(f"   ✅ Perfil duplicado eliminado")
    
    # 6. Eliminar usuario duplicado
    db.execute(text("""
        DELETE FROM usuarios WHERE id_usuario = :id_dup
    """), {"id_dup": id_duplicado})
    print(f"   ✅ Usuario duplicado eliminado")
    
    db.commit()
    print(f"\n✅ Migración completada exitosamente")
    return True

def main():
    if len(sys.argv) != 3:
        print("Uso: python migrar_usuario_especifico.py <id_duplicado> <id_real>")
        print("\nEjemplo:")
        print("  python migrar_usuario_especifico.py 215 228")
        sys.exit(1)
    
    try:
        id_duplicado = int(sys.argv[1])
        id_real = int(sys.argv[2])
    except ValueError:
        print("❌ Los IDs deben ser números enteros")
        sys.exit(1)
    
    db = SessionLocal()
    try:
        migrar_usuario(db, id_duplicado, id_real)
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
