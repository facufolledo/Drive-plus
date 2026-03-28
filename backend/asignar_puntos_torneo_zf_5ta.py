"""
Script para asignar puntos del torneo ZF 5ta al ranking del circuito
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.production'))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: Variable DATABASE_URL no encontrada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# Jugadores confirmados con sus IDs y puntos
JUGADORES_CONFIRMADOS = [
    {"id_usuario": 603, "nombre": "Loto Juan", "puntos": 1000, "fase": "campeon"},
    {"id_usuario": 602, "nombre": "Navarro Martín", "puntos": 1000, "fase": "campeon"},
    {"id_usuario": 201, "nombre": "Calderón Juan", "puntos": 600, "fase": "semis"},
    {"id_usuario": 88, "nombre": "Villegas Ignacio", "puntos": 600, "fase": "semis"},
    {"id_usuario": 31, "nombre": "Nani tomas", "puntos": 600, "fase": "semis"},
    {"id_usuario": 590, "nombre": "Ábrego maxi", "puntos": 600, "fase": "semis"},
    {"id_usuario": 586, "nombre": "Castro Joel", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 587, "nombre": "Aguilar Gonzalo", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 240, "nombre": "Farran Bastian", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 1024, "nombre": "Montiel nazareno", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 500, "nombre": "Diaz mateo", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 589, "nombre": "Sosa Bautista", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 75, "nombre": "Nieto Axel", "puntos": 100, "fase": "zona"},
    {"id_usuario": 555, "nombre": "Tello sergio", "puntos": 100, "fase": "zona"},
    {"id_usuario": 588, "nombre": "Casas Miguel", "puntos": 100, "fase": "zona"},
    {"id_usuario": 496, "nombre": "Brizuela joaquin", "puntos": 100, "fase": "zona"},
    {"id_usuario": 200, "nombre": "Oliva Bautista", "puntos": 100, "fase": "zona"},
    {"id_usuario": 29, "nombre": "Peñaloza Nicolás", "puntos": 100, "fase": "zona"},
]

def main():
    print("=" * 80)
    print("ASIGNACIÓN DE PUNTOS - TORNEO ZF 5TA (EXTERNO)")
    print("=" * 80)
    print()
    
    TORNEO_EXTERNO_NOMBRE = "ZF-5TA-MAR2026"
    CATEGORIA_NOMBRE = "5ta"
    
    with engine.connect() as conn:
        # 1. Obtener el ID del circuito ZF
        circuito = conn.execute(text("""
            SELECT id, nombre, codigo FROM circuitos WHERE codigo = 'zf'
        """)).fetchone()
        
        if not circuito:
            print("❌ ERROR: No se encontró el circuito 'zf'")
            print("   Verifica que el circuito esté creado en la base de datos")
            return
        
        circuito_id = circuito.id
        print(f"✅ Circuito encontrado: {circuito.nombre} (ID: {circuito_id})")
        print()
        
        # 2. Verificar si ya existen puntos para este torneo externo
        puntos_existentes = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM circuito_puntos_jugador 
            WHERE circuito_id = :circuito_id 
              AND torneo_externo = :torneo_externo
        """), {"circuito_id": circuito_id, "torneo_externo": TORNEO_EXTERNO_NOMBRE}).fetchone()
        
        if puntos_existentes.count > 0:
            print(f"⚠️  Ya existen {puntos_existentes.count} registros de puntos para este torneo")
            respuesta = input("   ¿Deseas eliminarlos y volver a crearlos? (s/n): ")
            if respuesta.lower() == 's':
                try:
                    conn.execute(text("""
                        DELETE FROM circuito_puntos_jugador 
                        WHERE circuito_id = :circuito_id AND torneo_externo = :torneo_externo
                    """), {"circuito_id": circuito_id, "torneo_externo": TORNEO_EXTERNO_NOMBRE})
                    conn.commit()
                    print("   ✅ Registros anteriores eliminados")
                except Exception as e:
                    conn.rollback()
                    print(f"   ❌ Error al eliminar: {e}")
                    return
            else:
                print("   ❌ Operación cancelada")
                return
        
        print()
        print("=" * 80)
        print("INSERTANDO PUNTOS")
        print("=" * 80)
        print()
        
        # 3. Insertar puntos para cada jugador
        insertados = 0
        errores = 0
        
        for jugador in JUGADORES_CONFIRMADOS:
            try:
                # Verificar que el usuario existe
                usuario = conn.execute(text("""
                    SELECT id_usuario, nombre_usuario FROM usuarios WHERE id_usuario = :id
                """), {"id": jugador["id_usuario"]}).fetchone()
                
                if not usuario:
                    print(f"❌ Usuario ID {jugador['id_usuario']} no existe - SALTANDO")
                    errores += 1
                    continue
                
                # Verificar si ya existe este registro
                existe = conn.execute(text("""
                    SELECT id FROM circuito_puntos_jugador
                    WHERE circuito_id = :circuito_id
                      AND torneo_externo = :torneo_externo
                      AND categoria_nombre = :categoria_nombre
                      AND usuario_id = :usuario_id
                """), {
                    "circuito_id": circuito_id,
                    "torneo_externo": TORNEO_EXTERNO_NOMBRE,
                    "categoria_nombre": CATEGORIA_NOMBRE,
                    "usuario_id": jugador["id_usuario"]
                }).fetchone()
                
                if existe:
                    # Actualizar
                    conn.execute(text("""
                        UPDATE circuito_puntos_jugador
                        SET fase_alcanzada = :fase,
                            puntos = :puntos
                        WHERE id = :id
                    """), {
                        "id": existe.id,
                        "fase": jugador["fase"],
                        "puntos": jugador["puntos"]
                    })
                    print(f"🔄 ID {jugador['id_usuario']:3d} - {jugador['nombre']:30s} - {jugador['puntos']:4d} pts ({jugador['fase']}) [ACTUALIZADO]")
                else:
                    # Insertar nuevo
                    conn.execute(text("""
                        INSERT INTO circuito_puntos_jugador 
                            (circuito_id, torneo_id, torneo_externo, categoria_id, categoria_nombre, usuario_id, fase_alcanzada, puntos)
                        VALUES 
                            (:circuito_id, NULL, :torneo_externo, NULL, :categoria_nombre, :usuario_id, :fase, :puntos)
                    """), {
                        "circuito_id": circuito_id,
                        "torneo_externo": TORNEO_EXTERNO_NOMBRE,
                        "categoria_nombre": CATEGORIA_NOMBRE,
                        "usuario_id": jugador["id_usuario"],
                        "fase": jugador["fase"],
                        "puntos": jugador["puntos"]
                    })
                    print(f"✅ ID {jugador['id_usuario']:3d} - {jugador['nombre']:30s} - {jugador['puntos']:4d} pts ({jugador['fase']})")
                
                insertados += 1
                
            except Exception as e:
                print(f"❌ Error con ID {jugador['id_usuario']} ({jugador['nombre']}): {e}")
                errores += 1
                conn.rollback()
                # Continuar con el siguiente
        
        # Commit al final
        try:
            conn.commit()
        except Exception as e:
            print(f"❌ Error al hacer commit final: {e}")
            conn.rollback()
        
        print()
        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"✅ Puntos insertados: {insertados}")
        print(f"❌ Errores: {errores}")
        print()
        
        # 4. Verificar el ranking actualizado
        print("=" * 80)
        print("RANKING ACTUALIZADO (Top 20)")
        print("=" * 80)
        print()
        
        ranking = conn.execute(text("""
            SELECT 
                u.id_usuario,
                COALESCE(pu.nombre || ' ' || pu.apellido, u.nombre_usuario) as nombre,
                SUM(cpj.puntos) as total_puntos,
                COUNT(DISTINCT COALESCE(cpj.torneo_externo, CAST(cpj.torneo_id AS TEXT))) as torneos_jugados
            FROM circuito_puntos_jugador cpj
            JOIN usuarios u ON cpj.usuario_id = u.id_usuario
            LEFT JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE cpj.circuito_id = :circuito_id
              AND (cpj.categoria_nombre = :categoria_nombre OR cpj.categoria_id IN (
                  SELECT id_categoria FROM categorias WHERE nombre = :categoria_nombre
              ))
            GROUP BY u.id_usuario, pu.nombre, pu.apellido, u.nombre_usuario
            ORDER BY total_puntos DESC
            LIMIT 20
        """), {"circuito_id": circuito_id, "categoria_nombre": CATEGORIA_NOMBRE}).fetchall()
        
        for i, row in enumerate(ranking, 1):
            print(f"{i:2d}. {row.nombre:40s} - {row.total_puntos:5d} pts ({row.torneos_jugados} torneos)")
        
        print()
        print("=" * 80)
        print("✅ PROCESO COMPLETADO")
        print("=" * 80)

if __name__ == "__main__":
    main()
