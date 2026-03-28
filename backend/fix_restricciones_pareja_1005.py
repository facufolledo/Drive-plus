"""
Corregir restricciones de pareja 1005 (Apostolo + Roldán) - 7MA
Solo pueden jugar viernes a las 17:00 y 22:00
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine, text

env_file = os.path.join(os.path.dirname(__file__), '.env.production')
DATABASE_URL = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

engine = create_engine(DATABASE_URL)

PAREJA_ID = 1005

# Disponibles: viernes 17:00 y 22:00 (solo esos dos horarios)
# Restricciones: todo excepto viernes 17:00-18:00 y 22:00-23:00
RESTRICCIONES = [
    {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "17:00"},
    {"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "22:00"},
    {"dias": ["viernes"], "horaInicio": "23:00", "horaFin": "23:59"},
    {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "23:59"},
    {"dias": ["domingo"], "horaInicio": "00:00", "horaFin": "23:59"},
]

def main():
    print("=" * 80)
    print(f"CORRIGIENDO RESTRICCIONES PAREJA {PAREJA_ID}")
    print("=" * 80)
    
    with engine.connect() as conn:
        pareja = conn.execute(text("""
            SELECT tp.id, u1.nombre_usuario, u2.nombre_usuario, p1.nombre, p1.apellido, p2.nombre, p2.apellido
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios p1 ON u1.id_usuario = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON u2.id_usuario = p2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": PAREJA_ID}).fetchone()
        
        if not pareja:
            print(f"❌ ERROR: Pareja {PAREJA_ID} no encontrada")
            return
        
        print(f"✅ Pareja: {pareja[3]} {pareja[4]} + {pareja[5]} {pareja[6]}")
        print(f"   Disponibles: viernes 17:00 y 22:00 SOLAMENTE")
        print(f"   Restricciones: {len(RESTRICCIONES)} bloques\n")
        
        restr_json = json.dumps(RESTRICCIONES)
        
        conn.execute(text("""
            UPDATE torneos_parejas 
            SET disponibilidad_horaria = CAST(:r AS jsonb)
            WHERE id = :pid
        """), {"pid": PAREJA_ID, "r": restr_json})
        
        conn.commit()
        
        print("✅ Restricciones actualizadas correctamente")

if __name__ == "__main__":
    main()
