"""
Corregir rating de usuarios que fueron migrados desde cuentas duplicadas.
El problema: al migrar historial_rating y partido_jugadores, no se recalculó
el rating final del usuario destino basándose en los deltas del historial.

Este script:
1. Busca usuarios que tienen historial_rating pero cuyo rating actual
   no coincide con el último rating_despues del historial
2. Muestra el diagnóstico
3. Corrige el rating
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from sqlalchemy import text


def diagnosticar_y_corregir(db, solo_diagnostico=True):
    """
    Busca usuarios cuyo rating actual no coincide con su último historial.
    """
    
    print("=" * 80)
    print("🔍 DIAGNÓSTICO: Usuarios con rating desactualizado")
    print("=" * 80)
    
    # Buscar usuarios que tienen historial_rating
    # y comparar su rating actual con el último rating_despues
    resultado = db.execute(text("""
        WITH ultimo_historial AS (
            SELECT DISTINCT ON (id_usuario) 
                id_usuario,
                rating_despues,
                creado_en
            FROM historial_rating
            ORDER BY id_usuario, creado_en DESC
        ),
        partidos_count AS (
            SELECT id_usuario, COUNT(*) as total_partidos
            FROM partido_jugadores
            GROUP BY id_usuario
        )
        SELECT 
            u.id_usuario,
            u.email,
            p.nombre,
            p.apellido,
            u.rating as rating_actual,
            uh.rating_despues as rating_correcto,
            u.partidos_jugados as partidos_registrados,
            COALESCE(pc.total_partidos, 0) as partidos_reales,
            uh.creado_en as ultimo_partido_fecha
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN ultimo_historial uh ON u.id_usuario = uh.id_usuario
        LEFT JOIN partidos_count pc ON u.id_usuario = pc.id_usuario
        WHERE u.rating != uh.rating_despues
           OR u.partidos_jugados != COALESCE(pc.total_partidos, 0)
        ORDER BY ABS(u.rating - uh.rating_despues) DESC
    """)).fetchall()
    
    if not resultado:
        print("\n✅ No se encontraron usuarios con rating desactualizado.")
        return []
    
    print(f"\n⚠️  Se encontraron {len(resultado)} usuarios con discrepancias:\n")
    
    usuarios_a_corregir = []
    
    for row in resultado:
        id_usuario = row[0]
        email = row[1]
        nombre = row[2]
        apellido = row[3]
        rating_actual = row[4]
        rating_correcto = row[5]
        partidos_registrados = row[6]
        partidos_reales = row[7]
        ultimo_fecha = row[8]
        
        diff_rating = rating_correcto - rating_actual
        diff_partidos = partidos_reales - partidos_registrados
        
        tiene_problema = False
        
        if diff_rating != 0:
            tiene_problema = True
        if diff_partidos != 0:
            tiene_problema = True
            
        if tiene_problema:
            print(f"  👤 {nombre} {apellido} (ID: {id_usuario}, {email})")
            if diff_rating != 0:
                signo = "+" if diff_rating > 0 else ""
                print(f"     Rating: {rating_actual} → {rating_correcto} ({signo}{diff_rating})")
            if diff_partidos != 0:
                print(f"     Partidos: {partidos_registrados} → {partidos_reales} (diff: {diff_partidos})")
            print(f"     Último partido: {ultimo_fecha}")
            print()
            
            usuarios_a_corregir.append({
                'id': id_usuario,
                'nombre': f"{nombre} {apellido}",
                'rating_actual': rating_actual,
                'rating_correcto': rating_correcto,
                'partidos_registrados': partidos_registrados,
                'partidos_reales': partidos_reales,
            })
    
    if not solo_diagnostico and usuarios_a_corregir:
        print("\n" + "=" * 80)
        print("🔧 CORRIGIENDO...")
        print("=" * 80)
        
        for u in usuarios_a_corregir:
            # Corregir rating
            db.execute(text("""
                UPDATE usuarios 
                SET rating = :rating, partidos_jugados = :partidos
                WHERE id_usuario = :id
            """), {
                "rating": u['rating_correcto'],
                "partidos": u['partidos_reales'],
                "id": u['id']
            })
            print(f"  ✅ {u['nombre']} (ID {u['id']}): rating {u['rating_actual']} → {u['rating_correcto']}, partidos {u['partidos_registrados']} → {u['partidos_reales']}")
        
        db.commit()
        print(f"\n✅ {len(usuarios_a_corregir)} usuarios corregidos exitosamente!")
    
    return usuarios_a_corregir


def buscar_damian_tapia(db):
    """Buscar específicamente a Damián Tapia para diagnóstico detallado"""
    
    print("\n" + "=" * 80)
    print("🔍 DETALLE: Damián Tapia")
    print("=" * 80)
    
    # Buscar usuario
    usuario = db.execute(text("""
        SELECT u.id_usuario, u.email, u.rating, u.partidos_jugados, u.id_categoria,
               p.nombre, p.apellido
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.apellido) LIKE '%tapia%' AND LOWER(p.nombre) LIKE '%damian%'
    """)).fetchone()
    
    if not usuario:
        print("  ❌ Damián Tapia no encontrado")
        return
    
    id_usuario = usuario[0]
    print(f"  ID: {id_usuario}")
    print(f"  Email: {usuario[1]}")
    print(f"  Rating actual: {usuario[2]}")
    print(f"  Partidos jugados: {usuario[3]}")
    print(f"  Categoría ID: {usuario[4]}")
    
    # Ver historial de rating
    historial = db.execute(text("""
        SELECT h.id_historial, h.id_partido, h.rating_antes, h.delta, h.rating_despues, h.creado_en
        FROM historial_rating h
        WHERE h.id_usuario = :id
        ORDER BY h.creado_en ASC
    """), {"id": id_usuario}).fetchall()
    
    print(f"\n  📊 Historial de rating ({len(historial)} registros):")
    for h in historial:
        signo = "+" if h[3] >= 0 else ""
        print(f"     Partido {h[1]}: {h[2]} {signo}{h[3]} → {h[4]} ({h[5]})")
    
    if historial:
        ultimo = historial[-1]
        print(f"\n  📌 Rating según último historial: {ultimo[4]}")
        print(f"  📌 Rating actual en tabla usuarios: {usuario[2]}")
        if ultimo[4] != usuario[2]:
            print(f"  ⚠️  DIFERENCIA: {ultimo[4] - usuario[2]} puntos!")
        else:
            print(f"  ✅ Rating coincide")
    
    # Ver partidos jugados reales
    partidos = db.execute(text("""
        SELECT COUNT(*) FROM partido_jugadores WHERE id_usuario = :id
    """), {"id": id_usuario}).fetchone()
    
    print(f"\n  📌 Partidos en partido_jugadores: {partidos[0]}")
    print(f"  📌 Partidos en tabla usuarios: {usuario[3]}")
    if partidos[0] != usuario[3]:
        print(f"  ⚠️  DIFERENCIA: {partidos[0] - usuario[3]} partidos!")


def main():
    db = SessionLocal()
    try:
        # Primero diagnosticar a Damián Tapia específicamente
        buscar_damian_tapia(db)
        
        # Luego diagnosticar todos
        print("\n")
        usuarios = diagnosticar_y_corregir(db, solo_diagnostico=True)
        
        if usuarios:
            print("\n" + "=" * 80)
            respuesta = input("¿Corregir todos los usuarios? (s/n): ").strip().lower()
            if respuesta == 's':
                diagnosticar_y_corregir(db, solo_diagnostico=False)
            else:
                print("Cancelado. Ejecutá de nuevo para corregir.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
