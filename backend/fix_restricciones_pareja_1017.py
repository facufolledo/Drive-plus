"""
Corregir restricciones de pareja 1017 (Agustín Mercado + Cesar Zaracho) - 7MA
Pueden jugar sábado 00:30 (viernes noche después de medianoche)
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

PAREJA_ID = 1017

# Disponibles: sábado 00:30 (viernes noche después de medianoche)
# Restricciones: viernes todo el día (00:00-23:59), sábado después de 01:00 (01:00-23:59)
RESTRICCIONES = [
    {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "23:59"},
    {"dias": ["sabado"], "horaInicio": "01:00", "horaFin": "23:59"},
]

def main():
    print("=" * 80)
    print(f"CORRIGIENDO RESTRICCIONES PAREJA {PAREJA_ID}")
    print("=" * 80)
    
    with engine.connect() as conn:
        pareja = conn.execute(text("""
            SELECT tp.id, u1.nombre_usuario, u2.nombre_usuario
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": PAREJA_ID}).fetchone()
        
        if not pareja:
            print(f"❌ ERROR: Pareja {PAREJA_ID} no encontrada")
            return
        
        print(f"✅ Pareja: {pareja[1]} + {pareja[2]}")
        print(f"   Disponibles: sábado 00:30 (viernes noche)")
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
