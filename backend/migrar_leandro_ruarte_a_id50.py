"""
Script para migrar el Leandro Ruarte duplicado al usuario real (ID 50)
El perfil con @leandroruarte del torneo fue registrado por error - el real es ID 50
Migra: torneos_parejas, historial_rating, partido_jugadores, partidos, etc.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import text
from src.database.config import get_db

load_dotenv()

ID_REAL = 50


def buscar_leandro_duplicado(db) -> int | None:
    """Busca el Leandro Ruarte duplicado (id != 50)"""
    from src.models.driveplus_models import PerfilUsuario, Usuario
    
    # Buscar por perfil: Leandro Ruarte
    perfiles = db.query(PerfilUsuario).filter(
        PerfilUsuario.nombre.ilike('%leandro%'),
        PerfilUsuario.apellido.ilike('%ruarte%')
    ).all()
    
    for p in perfiles:
        if p.id_usuario != ID_REAL:
            return p.id_usuario
    
    # Fallback: buscar por nombre_usuario
    usuario = db.query(Usuario).filter(
        Usuario.nombre_usuario.ilike('%leandroruarte%'),
        Usuario.id_usuario != ID_REAL
    ).first()
    
    return usuario.id_usuario if usuario else None


def migrar_usuario_a_id50(db, id_duplicado: int):
    """Reemplaza todas las referencias del duplicado por ID 50"""
    
    # Formato: (tabla, sql_set_where) - solo columnas que pueden tener el duplicado
    tablas_updates = [
        ("torneos_parejas", "jugador1_id = :real WHERE jugador1_id = :dup"),
        ("torneos_parejas", "jugador2_id = :real WHERE jugador2_id = :dup"),
        ("torneos_parejas", "jugador2_anterior_id = :real WHERE jugador2_anterior_id = :dup"),
        ("torneos_parejas", "pago_verificado_por = :real WHERE pago_verificado_por = :dup"),
        ("historial_rating", "id_usuario = :real WHERE id_usuario = :dup"),
        ("partido_jugadores", "id_usuario = :real WHERE id_usuario = :dup"),
        ("partidos", "id_creador = :real WHERE id_creador = :dup"),
        ("partidos", "creado_por = :real WHERE creado_por = :dup"),
        ("resultados_partidos", "id_reportador = :real WHERE id_reportador = :dup"),
        ("eventos_partido", "id_usuario_actor = :real WHERE id_usuario_actor = :dup"),
        ("confirmaciones", "id_usuario = :real WHERE id_usuario = :dup"),
        ("salas", "id_creador = :real WHERE id_creador = :dup"),
        ("sala_jugadores", "id_usuario = :real WHERE id_usuario = :dup"),
        ("torneo_bloqueos_jugador", "jugador_id = :real WHERE jugador_id = :dup"),
        ("torneo_historial_cambios", "realizado_por = :real WHERE realizado_por = :dup"),
        ("torneos_pagos_historial", "modificado_por = :real WHERE modificado_por = :dup"),
        ("categoria_checkpoints", "id_usuario = :real WHERE id_usuario = :dup"),
        ("organizadores_autorizados", "user_id = :real WHERE user_id = :dup"),
        ("organizadores_autorizados", "autorizado_por = :real WHERE autorizado_por = :dup"),
        ("torneos_organizadores", "user_id = :real WHERE user_id = :dup"),
    ]
    
    # historial_enfrentamientos tiene 4 columnas de jugadores
    historial_cols = ["jugador1_id", "jugador2_id", "jugador3_id", "jugador4_id"]
    
    params = {"real": ID_REAL, "dup": id_duplicado}
    total_cambios = 0
    
    for tabla, set_where in tablas_updates:
        try:
            sql = f"UPDATE {tabla} SET {set_where}"
            result = db.execute(text(sql), params)
            if result.rowcount > 0:
                total_cambios += result.rowcount
                col = set_where.split(" ")[0]
                print(f"  ✅ {tabla}.{col}: {result.rowcount} fila(s)")
        except Exception as e:
            if "column" not in str(e).lower() and "does not exist" not in str(e).lower():
                print(f"  ⚠️  {tabla}: {e}")
    
    for col in historial_cols:
        try:
            sql = f"UPDATE historial_enfrentamientos SET {col} = :real WHERE {col} = :dup"
            result = db.execute(text(sql), params)
            if result.rowcount > 0:
                total_cambios += result.rowcount
                print(f"  ✅ historial_enfrentamientos.{col}: {result.rowcount} fila(s)")
        except Exception as e:
            print(f"  ⚠️  historial_enfrentamientos.{col}: {e}")
    
    return total_cambios


def actualizar_rating_usuario50(db):
    """Actualiza rating y partidos_jugados de usuario 50 según historial"""
    from src.models.driveplus_models import Usuario, HistorialRating
    from src.services.categoria_service import actualizar_categoria_usuario
    
    usuario = db.query(Usuario).filter(Usuario.id_usuario == ID_REAL).first()
    if not usuario:
        print("  ❌ Usuario 50 no encontrado")
        return
    
    # Obtener último historial para rating actual
    ultimo = db.query(HistorialRating).filter(
        HistorialRating.id_usuario == ID_REAL
    ).order_by(HistorialRating.creado_en.desc()).first()
    
    if ultimo:
        usuario.rating = ultimo.rating_despues
        usuario.partidos_jugados = db.query(HistorialRating).filter(
            HistorialRating.id_usuario == ID_REAL
        ).count()
        actualizar_categoria_usuario(db, usuario)
        print(f"  ✅ Usuario 50: rating={usuario.rating}, partidos={usuario.partidos_jugados}")


def migrar_leandro():
    """Migra Leandro Ruarte duplicado a ID 50"""
    db = next(get_db())
    
    try:
        print("\n" + "="*70)
        print("🔄 MIGRAR LEANDRO RUARTE DUPLICADO → ID 50")
        print("="*70 + "\n")
        
        id_dup = buscar_leandro_duplicado(db)
        if not id_dup:
            print("❌ No se encontró Leandro Ruarte duplicado (id != 50)")
            return
        
        print(f"✅ Duplicado encontrado: ID {id_dup}")
        print(f"   Migrando todo a usuario ID {ID_REAL}\n")
        
        print("📋 Actualizando referencias...")
        total = migrar_usuario_a_id50(db, id_dup)
        print(f"\n   Total filas actualizadas: {total}")
        
        print("\n📊 Actualizando rating de usuario 50...")
        actualizar_rating_usuario50(db)
        
        db.commit()
        
        print("\n" + "="*70)
        print("✅ MIGRACIÓN COMPLETADA")
        print("="*70)
        print(f"\n⚠️  El usuario duplicado (ID {id_dup}) sigue existiendo.")
        print("   Podés eliminarlo o desactivarlo si ya no se usa.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrar_leandro()
