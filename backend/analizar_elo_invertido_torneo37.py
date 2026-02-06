"""
Analizar si el ELO está invertido en el torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido, Usuario, PartidoJugador, HistorialRating
from datetime import datetime

load_dotenv()

def analizar_elo_invertido():
    """Analiza si el ELO está invertido en los partidos confirmados"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 ANÁLISIS: ELO INVERTIDO TORNEO 37")
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
            
            # Obtener resultado
            if partido.resultado_padel:
                resultado = partido.resultado_padel
                print(f"Resultado: {resultado.get('sets', {})}")
            
            # Obtener historial de ELO
            historial = db.query(HistorialRating).filter(
                HistorialRating.id_partido == partido.id_partido
            ).all()
            
            if not historial:
                print("⚠️  Sin historial de ELO")
                continue
            
            print(f"\n📈 Cambios de ELO:")
            print("-" * 80)
            
            partido_tiene_error = False
            
            for h in historial:
                usuario = db.query(Usuario).filter(Usuario.id_usuario == h.id_usuario).first()
                if not usuario:
                    continue
                
                # Obtener información del jugador en el partido
                jugador_partido = db.query(PartidoJugador).filter(
                    PartidoJugador.id_partido == partido.id_partido,
                    PartidoJugador.id_usuario == h.id_usuario
                ).first()
                
                if not jugador_partido:
                    continue
                
                # Determinar si ganó
                gano = jugador_partido.pareja_id == partido.ganador_pareja_id
                resultado_texto = "GANÓ ✅" if gano else "PERDIÓ ❌"
                
                # Verificar si el signo del delta es correcto
                signo_correcto = (gano and h.delta > 0) or (not gano and h.delta < 0)
                
                if signo_correcto:
                    marca = "✅ CORRECTO"
                    correctos += 1
                else:
                    marca = "❌ ERROR - ELO INVERTIDO"
                    errores_encontrados += 1
                    partido_tiene_error = True
                
                print(f"\n{usuario.nombre_usuario} ({resultado_texto}):")
                print(f"  Rating antes: {h.rating_antes}")
                print(f"  Delta: {h.delta:+d}")
                print(f"  Rating después: {h.rating_despues}")
                print(f"  {marca}")
                
                if not signo_correcto:
                    if gano:
                        print(f"  ⚠️  PROBLEMA: Ganó pero perdió {abs(h.delta)} puntos")
                    else:
                        print(f"  ⚠️  PROBLEMA: Perdió pero ganó {h.delta} puntos")
            
            if partido_tiene_error:
                print(f"\n🚨 Este partido tiene ELO INVERTIDO")
        
        print("\n" + "="*80)
        print("📊 RESUMEN DEL ANÁLISIS")
        print("="*80)
        print(f"Total de cambios de ELO analizados: {correctos + errores_encontrados}")
        print(f"✅ Correctos: {correctos}")
        print(f"❌ Errores (invertidos): {errores_encontrados}")
        
        if errores_encontrados > 0:
            print(f"\n🚨 SE DETECTARON {errores_encontrados} CAMBIOS DE ELO INVERTIDOS")
            print("⚠️  ACCIÓN REQUERIDA: Corregir el código y reaplicar ELO")
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
    tiene_errores = analizar_elo_invertido()
    sys.exit(1 if tiene_errores else 0)
