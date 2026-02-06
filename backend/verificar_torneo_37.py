"""
Script para verificar el torneo 37 y sus parejas con restricciones
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def verificar_torneo37():
    """Verifica el torneo 37 y sus parejas"""
    session = Session()
    
    try:
        print("=" * 80)
        print("VERIFICACIÓN TORNEO 37")
        print("=" * 80)
        
        # Información del torneo
        torneo = session.execute(
            text("""
                SELECT id, nombre, fecha_inicio, fecha_fin, estado
                FROM torneos WHERE id = 37
            """)
        ).fetchone()
        
        if not torneo:
            print("❌ El torneo 37 no existe")
            return
        
        print(f"\n📋 TORNEO:")
        print(f"   ID: {torneo[0]}")
        print(f"   Nombre: {torneo[1]}")
        print(f"   Fecha inicio: {torneo[2]}")
        print(f"   Fecha fin: {torneo[3]}")
        print(f"   Estado: {torneo[4]}")
        
        # Categorías del torneo
        categorias = session.execute(
            text("""
                SELECT id, nombre, genero, max_parejas
                FROM torneo_categorias
                WHERE torneo_id = 37
            """)
        ).fetchall()
        
        print(f"\n📊 CATEGORÍAS ({len(categorias)}):")
        for cat in categorias:
            print(f"   • ID {cat[0]}: {cat[1]} ({cat[2]}) - Max {cat[3]} parejas")
        
        # Parejas inscritas
        parejas = session.execute(
            text("""
                SELECT 
                    tp.id,
                    u1.nombre_usuario as j1_username,
                    pu1.nombre as j1_nombre,
                    pu1.apellido as j1_apellido,
                    u2.nombre_usuario as j2_username,
                    pu2.nombre as j2_nombre,
                    pu2.apellido as j2_apellido,
                    tp.estado,
                    tp.disponibilidad_horaria,
                    tc.nombre as categoria
                FROM torneos_parejas tp
                JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
                LEFT JOIN perfil_usuarios pu1 ON u1.id_usuario = pu1.id_usuario
                LEFT JOIN perfil_usuarios pu2 ON u2.id_usuario = pu2.id_usuario
                LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
                WHERE tp.torneo_id = 37
                ORDER BY tp.id
            """)
        ).fetchall()
        
        print(f"\n👥 PAREJAS INSCRITAS ({len(parejas)}):")
        print("=" * 80)
        
        for p in parejas:
            pareja_id = p[0]
            j1_nombre = f"{p[2]} {p[3]}" if p[2] and p[3] else p[1]
            j2_nombre = f"{p[5]} {p[6]}" if p[5] and p[6] else p[4]
            estado = p[7]
            restricciones = p[8]
            categoria = p[9] or "Sin categoría"
            
            print(f"\n🎾 Pareja #{pareja_id}: {j1_nombre} / {j2_nombre}")
            print(f"   Estado: {estado}")
            print(f"   Categoría: {categoria}")
            
            if restricciones:
                print(f"   Restricciones horarias:")
                for r in restricciones:
                    dias = ", ".join(r['dias'])
                    print(f"      • {dias}: NO pueden de {r['horaInicio']} a {r['horaFin']}")
            else:
                print(f"   Sin restricciones horarias")
        
        # Horarios del torneo
        horarios = session.execute(
            text("""
                SELECT horarios_disponibles
                FROM torneos
                WHERE id = 37
            """)
        ).fetchone()
        
        if horarios and horarios[0]:
            print(f"\n⏰ HORARIOS DEL TORNEO:")
            for h in horarios[0]:
                dias = ", ".join(h['dias'])
                print(f"   • {dias}: {h['horaInicio']} - {h['horaFin']}")
        else:
            print(f"\n⚠️  El torneo no tiene horarios configurados")
        
        # Canchas
        canchas = session.execute(
            text("""
                SELECT id, nombre, activa
                FROM torneo_canchas
                WHERE torneo_id = 37
            """)
        ).fetchall()
        
        if canchas:
            print(f"\n🏟️  CANCHAS ({len(canchas)}):")
            for c in canchas:
                estado = "✅ Activa" if c[2] else "❌ Inactiva"
                print(f"   • {c[1]} - {estado}")
        else:
            print(f"\n⚠️  El torneo no tiene canchas configuradas")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verificar_torneo37()
