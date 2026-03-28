#!/usr/bin/env python3
"""
Corregir restricciones horarias de parejas 8va del torneo 45
Solo actualiza disponibilidad_horaria, no crea ni elimina parejas
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

# Mapeo de usernames a restricciones correctas
# None = sin restricciones (libre)
RESTRICCIONES_CORRECTAS = {
    # P1: Estevez/Oropel - JUEVES: DESP 22:00, VIERNES: LIBRE
    ("rogelio.estevez", "brajan.oropel"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"}
    ],
    
    # P2: Colina/Colina - JUEVES: DESP 19:00, VIERNES: DESP 19:00
    ("jeremias.colina", "franco.colina"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
    ],
    
    # P3: Olivera/Gregori - JUEVES: DESP 20:00, VIERNES: DESP 20:00
    ("lucas.olivera.t45", "gregori.lucas"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "20:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
    ],
    
    # P4: Britos/Salas - JUEVES: DESP 19:00, VIERNES: DESP 20:00
    ("maxi.britos.t45", "nairo.salas"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
    ],
    
    # P5: Brizuela/Ceballo - JUEVES: 22:00, VIERNES: DESP 22:00
    ("martin.brizuela.t45", "santiago.ceballo"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}
    ],
    
    # P6: Alfaro/Velazque - JUEVES Y VIERNES: DESDE 14 A 16 Y DESP 22
    ("axel.alfaro", "juan.velazque"): [
        {"dias": ["jueves", "viernes"], "horaInicio": "09:00", "horaFin": "14:00"},
        {"dias": ["jueves", "viernes"], "horaInicio": "16:00", "horaFin": "22:00"}
    ],
    
    # P7: Alfaro/Manrique - SIN PROBLEMA
    ("benha.alfaro", "federico.manrique"): None,
    
    # P8: Zaracho/Mercado - DOS PARTIDOS viernes = NO pueden jueves
    ("chilecito.zaracho", "mercado.mercado"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "23:00"}
    ],
    
    # P9: Barro/Barros - JUEVES: DESP 20:00, VIERNES: DESP 20:00
    ("maximiliano.barro", "rodrigo.barros.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "20:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
    ],
    
    # P10: Almada/Medina - JUEVES: 14 O 15 (solo pueden de 14 a 15)
    ("lucas.almada.t45", "jorge.medina.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "14:00"},
        {"dias": ["jueves"], "horaInicio": "15:00", "horaFin": "23:00"}
    ],
    
    # P11: Toledo/Tramontin - JUEVES: DESP 22:00, VIERNES: DESP 22:00, SÁBADO: DESP 14:00
    ("leandro.toledo.t45", "matias.tramontin"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "14:00"}
    ],
    
    # P12: Calderon/Vera - JUEVES: DESP 19
    ("ariel.calderon", "jere.vera.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"}
    ],
    
    # P13: Cardenas/Rojas - LIBRE
    ("tobias.cardenas", "agustin.rojas.t45"): None,
    
    # P14: Villanova/Fernandez - VIERNES: DESP 14:00
    ("ignacio.villanova", "facundo.fernandez.t45"): [
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"}
    ],
    
    # P15: Luna/Boris - JUEVES: DESP 22:00, VIERNES: DESP 22:00
    ("leonardo.luna.t45", "nieto.boris"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}
    ],
    
    # P16: Cortez/Aguilar - JUEVES: DESP 22:01, VIERNES: DESP 22:01
    ("agustin.cortez.t45", "agustin.aguilar.t45"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:01"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:01"}
    ],
    
    # P17: Diogenes/Diamante - SIN PROBLEMAS
    ("miranda.diogenes", "bautista.diamante"): None,
    
    # P18: Gonzalez/Morales - JUEVES: DESP 22, VIERNES: DESP 22, SÁBADO: DESP 12
    ("jeremias.gonzalez.t45", "morales.imanol"): [
        {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"}
    ],
}


def corregir_restricciones():
    s = Session()
    try:
        print("=" * 70)
        print(f"CORREGIR RESTRICCIONES - TORNEO {TORNEO_ID} - 8va")
        print("=" * 70)
        
        actualizadas = 0
        errores = []
        
        for (user1, user2), restricciones in RESTRICCIONES_CORRECTAS.items():
            try:
                # Buscar IDs de usuarios
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
                
                # Buscar pareja
                pareja = s.execute(text("""
                    SELECT id, disponibilidad_horaria 
                    FROM torneos_parejas
                    WHERE torneo_id = :t 
                    AND ((jugador1_id = :j1 AND jugador2_id = :j2)
                         OR (jugador1_id = :j2 AND jugador2_id = :j1))
                """), {"t": TORNEO_ID, "j1": u1_id, "j2": u2_id}).fetchone()
                
                if not pareja:
                    errores.append(f"{user1}/{user2}: Pareja no encontrada")
                    continue
                
                pareja_id = pareja[0]
                restricciones_actuales = pareja[1]
                
                # Convertir restricciones a JSON
                if restricciones is None:
                    nuevo_json = None
                    restr_str = "Sin restricciones"
                else:
                    nuevo_json = json.dumps(restricciones)
                    restr_str = f"{len(restricciones)} restricción(es)"
                
                # Actualizar
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
        
        # Confirmar cambios
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
