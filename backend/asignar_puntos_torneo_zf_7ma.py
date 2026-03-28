"""
Script para asignar puntos del torneo ZF 7ma al ranking del circuito
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
    {"id_usuario": 43, "nombre": "Montivero Federico", "puntos": 1000, "fase": "campeon"},
    {"id_usuario": 495, "nombre": "Diaz Alvaro", "puntos": 1000, "fase": "campeon"},
    {"id_usuario": 81, "nombre": "Romero Juan Pablo", "puntos": 800, "fase": "subcampeon"},
    {"id_usuario": 1025, "nombre": "Gallardo Pablo", "puntos": 800, "fase": "subcampeon"},
    {"id_usuario": 50, "nombre": "Ruarte Leandro", "puntos": 600, "fase": "semis"},
    {"id_usuario": 568, "nombre": "Hrellac Benjamín", "puntos": 600, "fase": "semis"},
    {"id_usuario": 5, "nombre": "Millicay Gustavo", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 55, "nombre": "Heredia Ezequiel", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 209, "nombre": "Sanchez Martin", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 499, "nombre": "Rodolzadovich Sebastián", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 30, "nombre": "Moreno Matías", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 85, "nombre": "Moreno Cristian", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 490, "nombre": "Alegre Franco", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 596, "nombre": "Gonzales Pablo", "puntos": 400, "fase": "cuartos"},
    {"id_usuario": 60, "nombre": "Vega Luis", "puntos": 100, "fase": "zona"},
    {"id_usuario": 71, "nombre": "Terán Marcos", "puntos": 100, "fase": "zona"},
    {"id_usuario": 210, "nombre": "Guerrero Facundo", "puntos": 100, "fase": "zona"},
    {"id_usuario": 1026, "nombre": "Olivera Joaquín", "puntos": 100, "fase": "zona"},
    {"id_usuario": 595, "nombre": "Espejo Juan", "puntos": 100, "fase": "zona"},
    {"id_usuario": 216, "nombre": "Calderón Marcos", "puntos": 100, "fase": "zona"},
]

def main():
    print("=" * 80)
    print("ASIGNACIÓN DE PUNTOS - TORNEO ZF 7MA (EXTERNO)")
    print("=" * 80)
    print()
    
    TORNEO_EXTERNO_NOMBRE = "ZF-7MA-MAR2026"
    CATEGORIA_NOMBRE = "7ma"
    
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
        
        # 2. Verificar si las columnas necesarias existen
        check_columns = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'circuito_puntos_jugador' 
              AND column_name IN ('torneo_externo', 'categoria_nombre')
        """)).fetchall()
        
        if len(check_columns) < 2:
            print("⚠️  La tabla necesita migración para soportar torneos externos")
            print("   Ejecuta primero: python ejecutar_migracion_torneo_externo.py")
            return
        
        print(f"✅ Tabla preparada para torneos externos")
        print()
        
        # 3. Verificar si ya existen puntos para este torneo externo
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
        
        # 4. Insertar puntos para cada jugador
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
        
        # 5. Verificar el ranking actualizado
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
