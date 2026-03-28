"""
Corregir restricciones de 7ma torneo 46
Convertir disponibilidades a restricciones (invertir la lógica)
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

TORNEO_ID = 46

# Restricciones CORRECTAS (horarios NO disponibles)
# Usuario dice "viernes +16" = disponible después de las 16 = NO disponible antes de las 16
RESTRICCIONES_CORRECTAS = {
    # Pareja 1: Lucero + Folledo - viernes +16 resto libre
    1002: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "16:00"}],
    
    # Pareja 2: Diaz Alvaro + Montivero - viernes +19, sábado hasta 20
    1003: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "19:00"},
        {"dias": ["sabado"], "horaInicio": "20:00", "horaFin": "23:59"}
    ],
    
    # Pareja 3: Moreno Matías + Moreno Cristian - viernes antes 17 o desp 22, sábado +19
    1004: [
        {"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "22:00"},
        {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "19:00"}
    ],
    
    # Pareja 4: Apostolo + Roldán - viernes 17 y 22 (disponible entre 17-22)
    1005: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "17:00"},
        {"dias": ["viernes"], "horaInicio": "22:00", "horaFin": "23:59"}
    ],
    
    # Pareja 5: Barros + Cruz - viernes +20
    1006: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "20:00"}],
    
    # Pareja 6: Millicay + Heredia - viernes 18 (solo a las 18)
    1007: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "18:00"},
        {"dias": ["viernes"], "horaInicio": "19:00", "horaFin": "23:59"}
    ],
    
    # Pareja 7: Juin + López - viernes +18 antes 00, sábado +12
    1008: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "18:00"},
        {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "12:00"}
    ],
    
    # Pareja 8: Yaryura + Diaz Santi - sin problema
    1009: [],
    
    # Pareja 9: Bedini + Johannesen - viernes +14, sábado menos 17 (antes de 17)
    1010: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "14:00"},
        {"dias": ["sabado"], "horaInicio": "17:00", "horaFin": "23:59"}
    ],
    
    # Pareja 10: Silva + Aguilar - viernes solo 00:30, sábado 14
    1011: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "00:30"},
        {"dias": ["viernes"], "horaInicio": "01:00", "horaFin": "23:59"},
        {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "14:00"},
        {"dias": ["sabado"], "horaInicio": "15:00", "horaFin": "23:59"}
    ],
    
    # Pareja 11: Diaz Nazareno + Salido - sábado +12
    1012: [{"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "12:00"}],
    
    # Pareja 12: Romero + Romero Jr - viernes +19
    1013: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "19:00"}],
    
    # Pareja 13: Brizuela + Moreno Valentín - viernes no puede, sábado libre
    1014: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "23:59"}],
    
    # Pareja 14: Alfaro + Alfaro - viernes +18
    1015: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "18:00"}],
    
    # Pareja 15: Bicet + Aguilar - viernes +15
    1016: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "15:00"}],
    
    # Pareja 16: Mercado + Zaracho - viernes +00 (después de medianoche = todo el día)
    1017: [],
    
    # Pareja 17: Villarrubia + Ibañaz - viernes +20
    1018: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "20:00"}],
    
    # Pareja 18: Nieto + Olivera - sábado +14
    1019: [{"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "14:00"}],
    
    # Pareja 19: Aredes + Aredes - viernes +14 antes 22 (disponible 14-22)
    1020: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "14:00"},
        {"dias": ["viernes"], "horaInicio": "22:00", "horaFin": "23:59"}
    ],
    
    # Pareja 20: Millicay Federico + Carrizo - viernes +20:30
    1021: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "20:30"}],
    
    # Pareja 21: Saldaño + Vásquez - viernes +17
    1022: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "17:00"}],
    
    # Pareja 22: Gonzales + Letterucci - viernes +18, sábado +15
    1023: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "18:00"},
        {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "15:00"}
    ],
    
    # Pareja 23: Diaz Exequiel + Jofre - viernes +22, sábado +17
    1024: [
        {"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "22:00"},
        {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "17:00"}
    ],
    
    # Pareja 24: Diaz Leo + Barroca - viernes +23
    1025: [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "23:00"}],
}

def main():
    print("=" * 80)
    print(f"CORRIGIENDO RESTRICCIONES TORNEO {TORNEO_ID} - 7MA")
    print("=" * 80)
    
    with engine.connect() as conn:
        cat = conn.execute(text("""
            SELECT id FROM torneo_categorias WHERE torneo_id = :tid AND nombre = '7ma'
        """), {"tid": TORNEO_ID}).fetchone()
        
        if not cat:
            print("❌ ERROR: Categoría 7ma no encontrada")
            return
        
        CATEGORIA_ID = cat.id
        print(f"✅ Categoría 7ma: ID {CATEGORIA_ID}\n")
        
        actualizadas = 0
        for pareja_id, restricciones in RESTRICCIONES_CORRECTAS.items():
            # Verificar que la pareja existe
            pareja = conn.execute(text("""
                SELECT id, jugador1_id, jugador2_id 
                FROM torneos_parejas 
                WHERE id = :pid AND torneo_id = :tid AND categoria_id = :cid
            """), {"pid": pareja_id, "tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchone()
            
            if not pareja:
                print(f"⚠️  Pareja {pareja_id} no encontrada - SALTANDO")
                continue
            
            # Actualizar restricciones
            restr_json = json.dumps(restricciones) if restricciones else None
            
            conn.execute(text("""
                UPDATE torneos_parejas 
                SET disponibilidad_horaria = CAST(:r AS jsonb)
                WHERE id = :pid
            """), {"pid": pareja_id, "r": restr_json})
            
            n_restr = len(restricciones) if restricciones else 0
            print(f"✅ Pareja {pareja_id} actualizada - {n_restr} restricción(es)")
            actualizadas += 1
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ {actualizadas} parejas actualizadas")
        print("=" * 80)

if __name__ == "__main__":
    main()
