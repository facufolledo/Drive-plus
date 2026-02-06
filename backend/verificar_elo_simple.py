"""
Verificar ELO de forma simple
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido, Usuario, HistorialRating
from src.models.torneo_models import TorneoPareja

load_dotenv()

def verificar_elo_simple():
    """Verifica el ELO de forma simple"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 VERIFICACIÓN SIMPLE: ELO TORNEO 37")
        print("="*80 + "\n")
        
        # Obtener partidos confirmados con ganador
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.estado == "confirmado",
            Partido.ganador_pareja_id.isnot(None)
        ).all()
        
        print(f"📊 Partidos confirmados con ganador: {len(partidos)}\n")
        
        errores_encontrados = 0
        correctos = 0
        
        for partido in partidos:
            print(f"\n{'='*80}")
            print(f"🏓 PARTIDO {partido.id_partido}")
            print(f"{'='*80}")
            print(f"Pareja {partido.pareja1_id} vs Pareja {partido.pareja2_id}")
            print(f"Ganador: Pareja {partido.ganador_pareja_id}")
            
            # Obtener parejas
            pareja1 = db.query(TorneoPareja).filter(TorneoPareja.id == partido.pareja1_id).first()
            pareja2 = db.query(TorneoPareja).filter(TorneoPareja.id == partido.pareja2_id).first()
            
            if not pareja1 or not pareja2:
                print("⚠️  No se encontraron las parejas")
                continue
            
            # Obtener historial de ELO
            historial = db.query(HistorialRating).filter(
                HistorialRating.id_partido == partido.id_partido
            ).all()
            
            if not historial:
                print("⚠️  Sin historial de ELO")
                continue
            
            print(f"\n📈 Cambios de ELO:")
            print("-" * 80)
            
            for h in historial:
                usuario = db.query(Usuario).filter(Usuario.id_usuario == h.id_usuario).first()
                if not usuario:
                    continue
                
                # Determinar a qué pareja pertenece
                if h.id_usuario in (pareja1.jugador1_id, pareja1.jugador2_id):
                    pareja_id = partido.pareja1_id
                elif h.id_usuario in (pareja2.jugador1_id, pareja2.jugador2_id):
                    pareja_id = partido.pareja2_id
                else:
                    print(f"⚠️  {usuario.nombre_usuario}: No pertenece a ninguna pareja")
                    continue
                
                # Determinar si ganó
                gano = pareja_id == partido.ganador_pareja_id
                resultado_texto = "GANÓ ✅" if gano else "PERDIÓ ❌"
                
                # Verificar si el signo del delta es correcto
                signo_correcto = (gano and h.delta > 0) or (not gano and h.delta < 0)
                
                if signo_correcto:
                    marca = "✅ CORRECTO"
                    correctos += 1
                else:
                    marca = "❌ ERROR - ELO INVERTIDO"
                    errores_encontrados += 1
                
                print(f"\n{usuario.nombre_usuario} ({resultado_texto}):")
                print(f"  Pareja: {pareja_id}")
                print(f"  Rating antes: {h.rating_antes}")
                print(f"  Delta: {h.delta:+d}")
                print(f"  Rating después: {h.rating_despues}")
                print(f"  {marca}")
                
                if not signo_correcto:
                    if gano:
                        print(f"  🚨 PROBLEMA: Ganó pero perdió {abs(h.delta)} puntos")
                    else:
                        print(f"  🚨 PROBLEMA: Perdió pero ganó {h.delta} puntos")
        
        print("\n" + "="*80)
        print("📊 RESUMEN DEL ANÁLISIS")
        print("="*80)
        print(f"Total de cambios de ELO analizados: {correctos + errores_encontrados}")
        print(f"✅ Correctos: {correctos}")
        print(f"❌ Errores (invertidos): {errores_encontrados}")
        
        if errores_encontrados > 0:
            print(f"\n🚨 SE DETECTARON {errores_encontrados} CAMBIOS DE ELO INVERTIDOS")
            print("⚠️  ACCIÓN REQUERIDA: Revertir y corregir el código")
        else:
            print("\n✅ No se detectaron errores en el ELO")
        
        print("="*80 + "\n")
        
        return errores_encontrados > 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    tiene_errores = verificar_elo_simple()
    sys.exit(1 if tiene_errores else 0)
