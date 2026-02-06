"""
Verificar estado del ELO en el torneo 37
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

def verificar_elo_torneo37():
    """Verifica el estado del ELO en el torneo 37"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 VERIFICACIÓN: ELO TORNEO 37")
        print("="*80 + "\n")
        
        # 1. Obtener todos los partidos finalizados del torneo 37
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.estado == "finalizado"
        ).all()
        
        print(f"📊 Total partidos finalizados: {len(partidos)}\n")
        
        if len(partidos) == 0:
            print("✅ No hay partidos finalizados")
            return
        
        print("🔍 Analizando partidos con resultados:")
        print("-" * 80)
        
        for partido in partidos:
            print(f"\n🏓 Partido {partido.id_partido}:")
            print(f"   Pareja {partido.pareja1_id} vs Pareja {partido.pareja2_id}")
            print(f"   Ganador: Pareja {partido.ganador_pareja_id}")
            print(f"   ELO aplicado: {partido.elo_aplicado}")
            
            # Obtener historial de rating de este partido
            historial = db.query(HistorialRating).filter(
                HistorialRating.id_partido == partido.id_partido
            ).all()
            
            if historial:
                print(f"   📈 Cambios de ELO registrados: {len(historial)}")
                for h in historial:
                    usuario = db.query(Usuario).filter(Usuario.id_usuario == h.id_usuario).first()
                    if usuario:
                        print(f"      • {usuario.nombre_usuario}:")
                        print(f"        Rating antes: {h.rating_antes}")
                        print(f"        Delta: {h.delta:+d}")
                        print(f"        Rating después: {h.rating_despues}")
                        
                        # Verificar si ganó o perdió
                        jugador_partido = db.query(PartidoJugador).filter(
                            PartidoJugador.id_partido == partido.id_partido,
                            PartidoJugador.id_usuario == h.id_usuario
                        ).first()
                        
                        if jugador_partido:
                            # Determinar si ganó
                            if jugador_partido.pareja_id == partido.ganador_pareja_id:
                                resultado = "GANÓ"
                                # Si ganó pero el delta es negativo, hay un problema
                                if h.delta < 0:
                                    print(f"        ⚠️  ERROR: GANÓ pero perdió {abs(h.delta)} puntos")
                            else:
                                resultado = "PERDIÓ"
                                # Si perdió pero el delta es positivo, hay un problema
                                if h.delta > 0:
                                    print(f"        ⚠️  ERROR: PERDIÓ pero ganó {h.delta} puntos")
                            
                            print(f"        Resultado: {resultado}")
            else:
                print(f"   ⚠️  No hay historial de ELO para este partido")
        
        print("\n" + "="*80)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_elo_torneo37()
