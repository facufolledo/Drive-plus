#!/usr/bin/env python3
"""
Verificar restricciones de Nicolas Lucero y su pareja
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def main():
    s = Session()
    try:
        print("=" * 80)
        print("VERIFICAR RESTRICCIONES - NICOLAS LUCERO Y PAREJA")
        print("=" * 80)
        
        # Buscar Nicolas Lucero
        lucero = s.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.apellido) LIKE '%lucero%'
              AND LOWER(p.nombre) LIKE '%nico%'
        """)).fetchall()
        
        print("\n🔍 Usuarios Lucero encontrados:")
        for l in lucero:
            print(f"   ID={l.id_usuario}, user={l.nombre_usuario}, {l.nombre} {l.apellido}")
        
        if not lucero:
            print("   ❌ No encontrado")
            return
        
        lucero_id = None
        for l in lucero:
            # Verificar si tiene pareja en torneo 45
            tiene_pareja = s.execute(text("""
                SELECT COUNT(*) as total
                FROM torneos_parejas
                WHERE torneo_id = :tid
                  AND (jugador1_id = :uid OR jugador2_id = :uid)
            """), {"tid": TORNEO_ID, "uid": l.id_usuario}).fetchone()
            
            if tiene_pareja.total > 0:
                lucero_id = l.id_usuario
                print(f"\n✅ Usuario con pareja en T45: ID={lucero_id}")
                break
        
        if not lucero_id:
            print("\n❌ Ningún Lucero tiene pareja en torneo 45")
            return
        
        # Buscar su pareja en el torneo 45
        pareja = s.execute(text("""
            SELECT tp.id as pareja_id,
                   u1.id_usuario as j1_id, u1.nombre_usuario as j1_user,
                   p1.nombre as j1_nombre, p1.apellido as j1_apellido,
                   u2.id_usuario as j2_id, u2.nombre_usuario as j2_user,
                   p2.nombre as j2_nombre, p2.apellido as j2_apellido,
                   tc.nombre as categoria
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios p1 ON u1.id_usuario = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON u2.id_usuario = p2.id_usuario
            LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            WHERE tp.torneo_id = :tid
              AND (tp.jugador1_id = :uid OR tp.jugador2_id = :uid)
        """), {"tid": TORNEO_ID, "uid": lucero_id}).fetchone()
        
        if not pareja:
            print(f"\n❌ No se encontró pareja para usuario {lucero_id} en torneo {TORNEO_ID}")
            return
        
        print(f"\n📋 Pareja encontrada:")
        print(f"   ID: {pareja.pareja_id}")
        print(f"   Categoría: {pareja.categoria}")
        print(f"   J1: {pareja.j1_nombre} {pareja.j1_apellido} (ID={pareja.j1_id})")
        print(f"   J2: {pareja.j2_nombre} {pareja.j2_apellido} (ID={pareja.j2_id})")
        
        # Verificar restricciones de la pareja
        print(f"\n" + "=" * 80)
        print("RESTRICCIONES DE LA PAREJA")
        print("=" * 80)
        
        restricciones_json = s.execute(text("""
            SELECT disponibilidad_horaria
            FROM torneos_parejas
            WHERE id = :pid
        """), {"pid": pareja.pareja_id}).fetchone()
        
        if restricciones_json and restricciones_json.disponibilidad_horaria:
            import json
            restricciones = restricciones_json.disponibilidad_horaria
            print(f"\n✅ Restricciones encontradas:\n")
            print(json.dumps(restricciones, indent=2, ensure_ascii=False))
        else:
            print("\n⚠️  No hay restricciones configuradas (puede jugar cualquier horario)")
        
        # Verificar partidos programados
        print(f"\n" + "=" * 80)
        print("PARTIDOS PROGRAMADOS")
        print("=" * 80)
        
        partidos = s.execute(text("""
            SELECT p.id_partido, p.fecha_hora, tc.nombre as cancha,
                   tcat.nombre as categoria, tz.nombre as zona
            FROM partidos p
            LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
            LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
            LEFT JOIN torneos_parejas tp ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
            LEFT JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
            WHERE (p.pareja1_id = :pid OR p.pareja2_id = :pid)
              AND p.fecha_hora IS NOT NULL
            ORDER BY p.fecha_hora
        """), {"pid": pareja.pareja_id}).fetchall()
        
        if partidos:
            print(f"\n✅ {len(partidos)} partidos programados:\n")
            for p in partidos:
                # Convertir a hora local (UTC-3)
                from datetime import timedelta
                hora_local = p.fecha_hora - timedelta(hours=3)
                dia_semana = hora_local.strftime('%A')
                dias_es = {
                    'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miercoles',
                    'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sabado', 'Sunday': 'domingo'
                }
                dia_es = dias_es.get(dia_semana, dia_semana)
                
                print(f"   Partido #{p.id_partido}")
                print(f"   📅 {hora_local.strftime('%d/%m/%Y %H:%M')} ({dia_es})")
                print(f"   🏟️  {p.cancha} - {p.categoria} {p.zona}")
                print()
        else:
            print("\n⚠️  No hay partidos programados")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
