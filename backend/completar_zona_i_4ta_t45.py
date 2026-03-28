import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45
FECHA_JUEVES = datetime(2026, 3, 5, 17, 0)
CANCHA_3 = 91

def main():
    s = Session()
    try:
        print("=" * 80)
        print("COMPLETAR 4TA ZONA I - T45")
        print("=" * 80)
        
        # Buscar zona I de 4ta
        zona = s.execute(text("""
            SELECT tz.id
            FROM torneo_zonas tz
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = :tid
            AND tc.nombre = '4ta'
            AND tz.nombre = 'Zona I'
        """), {"tid": TORNEO_ID}).fetchone()
        
        if not zona:
            print("❌ Zona I de 4ta no encontrada")
            return
        
        # Verificar parejas actuales
        parejas = s.execute(text("""
            SELECT tp.id
            FROM torneos_parejas tp
            JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
            WHERE tzp.zona_id = :zid
            ORDER BY tp.id
        """), {"zid": zona.id}).fetchall()
        
        print(f"\nParejas actuales en Zona I: {len(parejas)}")
        
        if len(parejas) < 2:
            print(f"⚠️  Inscribiendo segunda pareja...")
            
            # Buscar o crear usuario CONFIRMAR
            usuario = s.execute(text("""
                SELECT id_usuario FROM usuarios WHERE nombre_usuario = 'confirmar.confirmar.4ta.t45'
            """)).fetchone()
            
            if not usuario:
                usuario_result = s.execute(text("""
                    INSERT INTO usuarios (nombre_usuario, email, password_hash, rating)
                    VALUES ('confirmar.confirmar.4ta.t45', 'confirmar@temp.com', 'temp', 1500)
                    RETURNING id_usuario
                """))
                usuario_id = usuario_result.fetchone()[0]
            else:
                usuario_id = usuario[0]
            
            # Crear pareja
            pareja_result = s.execute(text("""
                INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id, pago_estado)
                VALUES (:tid, :j1, :j2, 'pagado')
                RETURNING id
            """), {
                "tid": TORNEO_ID,
                "j1": usuario_id,
                "j2": usuario_id
            })
            
            pareja_id = pareja_result.fetchone()[0]
            
            # Asignar a zona
            s.execute(text("""
                INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
                VALUES (:zona, :pareja)
            """), {
                "zona": zona.id,
                "pareja": pareja_id
            })
            
            print(f"✅ Pareja inscrita: ID {pareja_id}")
            
            # Actualizar lista de parejas
            parejas = s.execute(text("""
                SELECT tp.id
                FROM torneos_parejas tp
                JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
                WHERE tzp.zona_id = :zid
                ORDER BY tp.id
            """), {"zid": zona.id}).fetchall()
        
        if len(parejas) >= 2:
            # Verificar si existe el partido
            partido = s.execute(text("""
                SELECT COUNT(*)
                FROM partidos
                WHERE zona_id = :zid
            """), {"zid": zona.id}).scalar()
            
            if partido > 0:
                print(f"✅ Ya existe {partido} partido(s)")
            else:
                # Crear partido 1vs2
                print("\nCreando partido 1vs2...")
                s.execute(text("""
                    INSERT INTO partidos (
                        pareja1_id, pareja2_id, zona_id, fecha_hora, fecha,
                        cancha_id, estado, id_creador
                    ) VALUES (
                        :p1, :p2, :zona, :fecha, :fecha_solo,
                        :cancha, 'pendiente', 1
                    )
                """), {
                    "p1": parejas[0][0],
                    "p2": parejas[1][0],
                    "zona": zona.id,
                    "fecha": FECHA_JUEVES,
                    "fecha_solo": FECHA_JUEVES.date(),
                    "cancha": CANCHA_3
                })
                print("✅ Partido creado")
        
        s.commit()
        print("\n✅ Zona I completada")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
