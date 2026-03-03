#!/usr/bin/env python3
r"""
Eliminar torneo demo y los usuarios ficticios.
Ejecutar: python backend/eliminar_torneo_demo.py [TORNEO_ID]
Si no se pasa ID, solo elimina usuarios demo.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

def eliminar(torneo_id=None):
    s = Session()
    try:
        # Si hay archivo con IDs, usarlo
        if os.path.exists("demo_torneo_ids.json") and not torneo_id:
            with open("demo_torneo_ids.json", "r") as f:
                data = json.load(f)
                torneo_id = data.get("torneo_id")
                print(f"📄 Usando ID del archivo: {torneo_id}")
        
        if torneo_id:
            t = s.execute(text("SELECT nombre FROM torneos WHERE id = :t"), {"t": torneo_id}).fetchone()
            if not t:
                print(f"⚠️  Torneo {torneo_id} no existe, solo eliminando usuarios demo...")
            else:
                print(f"🗑️  Eliminando: {t[0]} (ID: {torneo_id})")

                # Partidos del torneo (si se generó fixture)
                r = s.execute(text("DELETE FROM partido_jugadores WHERE id_partido IN (SELECT id_partido FROM partidos WHERE id_torneo = :t)"), {"t": torneo_id})
                print(f"   partido_jugadores: {r.rowcount}")
                r = s.execute(text("DELETE FROM resultados_partidos WHERE id_partido IN (SELECT id_partido FROM partidos WHERE id_torneo = :t)"), {"t": torneo_id})
                print(f"   resultados_partidos: {r.rowcount}")
                r = s.execute(text("DELETE FROM partidos WHERE id_torneo = :t"), {"t": torneo_id})
                print(f"   partidos: {r.rowcount}")

                # Zonas
                r = s.execute(text("DELETE FROM torneo_zona_parejas WHERE zona_id IN (SELECT id FROM torneo_zonas WHERE torneo_id = :t)"), {"t": torneo_id})
                print(f"   zona_parejas: {r.rowcount}")
                r = s.execute(text("DELETE FROM torneo_tabla_posiciones WHERE zona_id IN (SELECT id FROM torneo_zonas WHERE torneo_id = :t)"), {"t": torneo_id})
                print(f"   tabla_posiciones: {r.rowcount}")
                r = s.execute(text("DELETE FROM torneo_zonas WHERE torneo_id = :t"), {"t": torneo_id})
                print(f"   zonas: {r.rowcount}")

                # Slots
                r = s.execute(text("DELETE FROM torneo_slots WHERE torneo_id = :t"), {"t": torneo_id})
                print(f"   slots: {r.rowcount}")

                # Parejas, canchas, categorías, torneo
                r = s.execute(text("DELETE FROM torneos_parejas WHERE torneo_id = :t"), {"t": torneo_id})
                print(f"   parejas: {r.rowcount}")
                r = s.execute(text("DELETE FROM torneo_canchas WHERE torneo_id = :t"), {"t": torneo_id})
                print(f"   canchas: {r.rowcount}")
                r = s.execute(text("DELETE FROM torneo_categorias WHERE torneo_id = :t"), {"t": torneo_id})
                print(f"   categorías: {r.rowcount}")
                r = s.execute(text("DELETE FROM torneos WHERE id = :t"), {"t": torneo_id})
                print(f"   torneo: {r.rowcount}")
                s.commit()
                print("   ✅ Torneo eliminado")

        # Usuarios demo en batch (siempre)
        print("\n🗑️  Eliminando usuarios demo y sus dependencias...")
        
        # 1. Primero eliminar partidos que involucran parejas con usuarios demo
        r = s.execute(text("""
            DELETE FROM partido_jugadores 
            WHERE id_partido IN (
                SELECT p.id_partido FROM partidos p
                WHERE p.pareja1_id IN (
                    SELECT id FROM torneos_parejas 
                    WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                       OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                )
                OR p.pareja2_id IN (
                    SELECT id FROM torneos_parejas 
                    WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                       OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                )
            )
        """))
        print(f"   partido_jugadores: {r.rowcount}")
        
        r = s.execute(text("""
            DELETE FROM resultados_partidos 
            WHERE id_partido IN (
                SELECT p.id_partido FROM partidos p
                WHERE p.pareja1_id IN (
                    SELECT id FROM torneos_parejas 
                    WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                       OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                )
                OR p.pareja2_id IN (
                    SELECT id FROM torneos_parejas 
                    WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                       OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                )
            )
        """))
        print(f"   resultados_partidos: {r.rowcount}")
        
        r = s.execute(text("""
            DELETE FROM partidos 
            WHERE pareja1_id IN (
                SELECT id FROM torneos_parejas 
                WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                   OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
            )
            OR pareja2_id IN (
                SELECT id FROM torneos_parejas 
                WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                   OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
            )
        """))
        print(f"   partidos: {r.rowcount}")
        
        # 2. Eliminar zona_parejas que referencian parejas con usuarios demo
        r = s.execute(text("""
            DELETE FROM torneo_zona_parejas 
            WHERE pareja_id IN (
                SELECT id FROM torneos_parejas 
                WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                   OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
            )
        """))
        print(f"   zona_parejas: {r.rowcount}")
        
        # 3. Eliminar tabla_posiciones que referencian parejas con usuarios demo
        r = s.execute(text("""
            DELETE FROM torneo_tabla_posiciones 
            WHERE pareja_id IN (
                SELECT id FROM torneos_parejas 
                WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
                   OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
            )
        """))
        print(f"   tabla_posiciones: {r.rowcount}")
        
        # 4. Ahora sí eliminar parejas con usuarios demo
        r = s.execute(text("""
            DELETE FROM torneos_parejas 
            WHERE jugador1_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
               OR jugador2_id IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')
        """))
        print(f"   parejas con usuarios demo: {r.rowcount}")
        
        # 5. Finalmente eliminar perfil y usuarios
        s.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')"))
        r = s.execute(text("DELETE FROM usuarios WHERE email LIKE 'demo%@demo.com'"))
        s.commit()
        print(f"   usuarios demo: {r.rowcount}")

        if os.path.exists("demo_torneo_ids.json"):
            os.remove("demo_torneo_ids.json")
            print("   📄 Archivo demo_torneo_ids.json eliminado")

        print("\n✅ Limpieza completada")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
        s.rollback()
    finally:
        s.close()

if __name__ == "__main__":
    tid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    eliminar(tid)
