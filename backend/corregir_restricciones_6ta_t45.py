#!/usr/bin/env python3
"""
Corregir restricciones horarias de parejas 6ta del torneo 45
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

# Restricciones correctas para 6ta
RESTRICCIONES_CORRECTAS = {
    # P1: Tejada/Corzo - J: DESP 21:00, V: POR LA MAÑANA/23HS
    ("rodrigo.tejada.t45", "nicolas.corzo.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "21:00"},
        {"dias": ["viernes"], "horaInicio": "12:00", "horaFin": "23:00"}
    ],
    
    # P2: Ortiz/Suarez - J: POR LA MAÑANA/23HS, V: POR LA MAÑANA/23HS
    ("ortiz.ortiz.t45", "suarez.suarez.t45"): [
        {"dias": ["jueves"], "horaInicio": "12:00", "horaFin": "23:00"},
        {"dias": ["viernes"], "horaInicio": "12:00", "horaFin": "23:00"}
    ],
    
    # P3: Nieto/Nieto - J: vacío, V: DESP 20:00
    ("axel.nieto.t45", "stefy.nieto.t45"): [
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
    ],
    
    # P4: Molina/Molina - SIN PROBLEMAS
    ("alvaro.molina.t45", "alejo.molina.t45"): None,
    
    # P5: Bazan/Rodriguez - J: DESP 22:00, V: DESP 22:00
    ("isaias.bazan.t45", "valentino.rodriguez.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}
    ],
    
    # P7: Stepanios/Fuentes - J: DESP 19:00, V: DESP 19:00
    ("stepanios.yoyo.t45", "gere.fuentes.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
    ],
    
    # P9: Gurgone/Palacio - V: DESP 20:00 DOS PARTIDOS = NO jueves, V hasta 20:00
    ("cristian.gurgone.t45", "benjamin.palacio.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "23:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
    ],
    
    # P11: Oliva/Leyes - J: DESP 18:00, V: DESP 18:00
    ("juan.oliva.t45", "franco.leyes.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"}
    ],
    
    # P12: Romero/Romero - V: DESP 17:00 DOS PARTIDOS = NO jueves, V hasta 17:00
    ("francisco.romero.t45", "fernando.romero.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "23:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "17:00"}
    ],
    
    # P13: Ontivero/Ontivero - J: DESP 18:00, V: DESP 20:00
    ("saul.ontivero.t45", "isaias.ontivero.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
    ],
    
    # P14: Cordero/Perez - J: DESP 17 A 22, V: DESP 19:00
    ("fernando.cordero.t45", "cristian.perez.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "17:00"},
        {"dias": ["jueves"], "horaInicio": "22:00", "horaFin": "23:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
    ],
    
    # P15: Sanchez/Arrebola - J: DOS PARTIDOS DESP 21 = J hasta 21:00, V NO pueden
    ("martin.sanchez.t45", "pluma.arrebola.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "21:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "23:00"}
    ],
    
    # P16: Ceballo/Pamelin - J: DESP 21:00, V: DESP 21:00
    ("lazaro.ceballo.t45", "jorge.pamelin.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "21:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
    ],
    
    # P17: Cejas/Redes - V: DESP 18:00 DOS PARTIDOS = NO jueves, V hasta 18:00
    ("tomas.cejas.t45", "tomas.redes.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "23:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"}
    ],
    
    # P18: Llabante/Cordoba - J: DESP 19:00, V: DESP 19:00
    ("federico.llabante.t45", "santiago.cordoba.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
    ],
    
    # P19: Santillan/Paredes - J: DEP 22:00, V: DEP 22:00, S: DESDE 14 A 15/DESP 21
    ("kike.santillan.t45", "fabio.paredes.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "14:00"},
        {"dias": ["sabado"], "horaInicio": "15:00", "horaFin": "21:00"}
    ],
    
    # P20: Lobos/Santander - J: DESDE 18 A 22, V: DESDE 18 A 22, S: A LA MAÑANA NO
    ("javier.lobos.t45", "mario.santander.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"},
        {"dias": ["jueves"], "horaInicio": "22:00", "horaFin": "23:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"},
        {"dias": ["viernes"], "horaInicio": "22:00", "horaFin": "23:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"}
    ],
    
    # P21: Ferreyra/Bustos - J: DESP 21:00, V: DESP 21:00
    ("ferreyra.ferreyra.t45", "bustos.bustos.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "21:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
    ],
    
    # P22: Vega/Martin - V: DESP 22:00
    ("maxi.vega.t45", "facundo.martin.t45"): [
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}
    ],
    
    # P23: Nis/Fuentes - J: DESP 19:00, V: DESP 19:00, S: POR LA MAÑANA NO
    ("juan.nis.t45", "agustin.fuentes.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"}
    ],
    
    # P24: Carrizo/Juarez - J: DESP 14:00, V: DESP 14:00
    ("matias.carrizo.t45", "lucas.juarez.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "14:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"}
    ],
    
    # P25: Salazar/Charazo - J: DESP 18:00, V: ANTES DE 20:00
    ("jeremias.salazar.t45", "jeremias.charazo.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"},
        {"dias": ["viernes"], "horaInicio": "20:00", "horaFin": "23:00"}
    ],
    
    # P26: Rosa/Estrada - J: DESP 18:00
    ("matias.rosa.t45", "miguel.estrada.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"}
    ],
}


def corregir_restricciones():
    s = Session()
    try:
        print("=" * 70)
        print(f"CORREGIR RESTRICCIONES - TORNEO {TORNEO_ID} - 6ta")
        print("=" * 70)
        
        actualizadas = 0
        errores = []
        
        for (user1, user2), restricciones in RESTRICCIONES_CORRECTAS.items():
            try:
                u1 = s.execute(text(
                    "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
                ), {"u": user1}).fetchone()
                
                u2 = s.execute(text(
                    "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
                ), {"u": user2}).fetchone()
                
                if not u1 or not u2:
                    errores.append(f"{user1}/{user2}: Usuarios no encontrados")
                    continue
                
                u1_id, u2_id = u1[0], u2[0]
                
                pareja = s.execute(text("""
                    SELECT id FROM torneos_parejas
                    WHERE torneo_id = :t 
                    AND ((jugador1_id = :j1 AND jugador2_id = :j2)
                         OR (jugador1_id = :j2 AND jugador2_id = :j1))
                """), {"t": TORNEO_ID, "j1": u1_id, "j2": u2_id}).fetchone()
                
                if not pareja:
                    errores.append(f"{user1}/{user2}: Pareja no encontrada")
                    continue
                
                pareja_id = pareja[0]
                
                if restricciones is None:
                    nuevo_json = None
                    restr_str = "Sin restricciones"
                else:
                    nuevo_json = json.dumps(restricciones)
                    restr_str = f"{len(restricciones)} restricción(es)"
                
                if nuevo_json is None:
                    s.execute(text("""
                        UPDATE torneos_parejas 
                        SET disponibilidad_horaria = NULL
                        WHERE id = :pid
                    """), {"pid": pareja_id})
                else:
                    s.execute(text("""
                        UPDATE torneos_parejas 
                        SET disponibilidad_horaria = CAST(:r AS jsonb)
                        WHERE id = :pid
                    """), {"pid": pareja_id, "r": nuevo_json})
                
                print(f"✅ Pareja {pareja_id} ({user1}/{user2}) - {restr_str}")
                actualizadas += 1
                
            except Exception as e:
                errores.append(f"{user1}/{user2}: {e}")
                print(f"❌ Error en {user1}/{user2}: {e}")
        
        if actualizadas > 0:
            print(f"\n{'=' * 70}")
            print(f"📊 RESUMEN:")
            print(f"   ✅ Actualizadas: {actualizadas}")
            print(f"   ❌ Errores: {len(errores)}")
            print(f"{'=' * 70}")
            
            if errores:
                print("\nErrores:")
                for e in errores:
                    print(f"  • {e}")
            
            confirmar = input("\n¿Confirmar cambios? (si/no): ").strip().lower()
            
            if confirmar == 'si':
                s.commit()
                print("\n✅ Restricciones actualizadas exitosamente")
            else:
                s.rollback()
                print("\n❌ Cambios descartados")
        else:
            print("\n⚠️  No se actualizó ninguna pareja")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        s.rollback()
    finally:
        s.close()


if __name__ == "__main__":
    corregir_restricciones()
