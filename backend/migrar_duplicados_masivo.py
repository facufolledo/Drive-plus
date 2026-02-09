"""
Migrar usuarios duplicados de forma masiva
Excluye: Juan Pablo Romero (IDs 80, 124)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

# Lista de migraciones a realizar: (id_origen, id_destino, nombre)
MIGRACIONES = [
    (225, 57, "Fernanda Bustos"),
    (206, 38, "Gabriel Fernández"),
    (129, 210, "Facundo Guerrero"),
    (224, 30, "Matias Moreno"),
    (125, 81, "Juan Romero"),
    (132, 209, "Martin Sanchez"),
]

# Nota: Esther Reyes (97, 98) requiere verificación manual
# Nota: Juan Pablo Romero (80, 124) excluido por solicitud del usuario

def migrar_usuario(conn, id_origen, id_destino, nombre):
    """Migrar datos de un usuario a otro"""
    
    print(f"\n{'='*80}")
    print(f"Migrando: {nombre}")
    print(f"  Origen: ID {id_origen} → Destino: ID {id_destino}")
    print(f"{'='*80}")
    
    try:
        # 1. Actualizar torneos_parejas (jugador1_id)
        result = conn.execute(text("""
            UPDATE torneos_parejas 
            SET jugador1_id = :destino 
            WHERE jugador1_id = :origen
        """), {"origen": id_origen, "destino": id_destino})
        print(f"  ✓ Parejas actualizadas (jugador1): {result.rowcount}")
        
        # 2. Actualizar torneos_parejas (jugador2_id)
        result = conn.execute(text("""
            UPDATE torneos_parejas 
            SET jugador2_id = :destino 
            WHERE jugador2_id = :origen
        """), {"origen": id_origen, "destino": id_destino})
        print(f"  ✓ Parejas actualizadas (jugador2): {result.rowcount}")
        
        # 3. Actualizar historial_rating
        result = conn.execute(text("""
            UPDATE historial_rating 
            SET id_usuario = :destino 
            WHERE id_usuario = :origen
        """), {"origen": id_origen, "destino": id_destino})
        print(f"  ✓ Historial rating actualizado: {result.rowcount}")
        
        # 4. Actualizar partido_jugadores
        result = conn.execute(text("""
            UPDATE partido_jugadores 
            SET id_usuario = :destino 
            WHERE id_usuario = :origen
        """), {"origen": id_origen, "destino": id_destino})
        print(f"  ✓ Partido jugadores actualizado: {result.rowcount}")
        
        # 5. Actualizar partidos creados
        result = conn.execute(text("""
            UPDATE partidos 
            SET creado_por = :destino 
            WHERE creado_por = :origen
        """), {"origen": id_origen, "destino": id_destino})
        print(f"  ✓ Partidos creados actualizados: {result.rowcount}")
        
        # 6. Actualizar rating y partidos_jugados del usuario destino
        # Sumar los partidos jugados
        result = conn.execute(text("""
            UPDATE usuarios 
            SET partidos_jugados = partidos_jugados + (
                SELECT partidos_jugados FROM usuarios WHERE id_usuario = :origen
            )
            WHERE id_usuario = :destino
        """), {"origen": id_origen, "destino": id_destino})
        print(f"  ✓ Partidos jugados sumados")
        
        # Usar el rating más alto
        result = conn.execute(text("""
            UPDATE usuarios 
            SET rating = GREATEST(rating, (
                SELECT rating FROM usuarios WHERE id_usuario = :origen
            ))
            WHERE id_usuario = :destino
        """), {"origen": id_origen, "destino": id_destino})
        print(f"  ✓ Rating actualizado (usando el más alto)")
        
        # 7. Eliminar perfil del usuario origen
        result = conn.execute(text("""
            DELETE FROM perfil_usuarios 
            WHERE id_usuario = :origen
        """), {"origen": id_origen})
        print(f"  ✓ Perfil eliminado: {result.rowcount}")
        
        # 8. Eliminar usuario origen
        result = conn.execute(text("""
            DELETE FROM usuarios 
            WHERE id_usuario = :origen
        """), {"origen": id_origen})
        print(f"  ✓ Usuario eliminado: {result.rowcount}")
        
        print(f"  ✅ Migración completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error en migración: {e}")
        return False

print("🔄 Iniciando migración masiva de usuarios duplicados...")
print("=" * 80)

exitosos = 0
fallidos = 0

with engine.connect() as conn:
    for id_origen, id_destino, nombre in MIGRACIONES:
        if migrar_usuario(conn, id_origen, id_destino, nombre):
            conn.commit()
            exitosos += 1
        else:
            conn.rollback()
            fallidos += 1

print(f"\n{'='*80}")
print(f"📊 RESUMEN FINAL")
print(f"{'='*80}")
print(f"  ✅ Migraciones exitosas: {exitosos}")
print(f"  ❌ Migraciones fallidas: {fallidos}")
print(f"  📝 Total procesadas: {len(MIGRACIONES)}")

print(f"\n⚠️  CASOS PENDIENTES:")
print(f"  1. Esther Reyes (IDs 97, 98) - Requiere verificación manual")
print(f"  2. Juan Pablo Romero (IDs 80, 124) - Excluido por solicitud")

print(f"\n✅ Proceso completado!")
