"""
Verificar estados de partidos del torneo 37
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

def verificar_estados():
    """Verifica los estados de los partidos del torneo 37"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 VERIFICACIÓN: ESTADOS DE PARTIDOS TORNEO 37")
        print("="*80 + "\n")
        
        # Obtener TODOS los partidos del torneo 37
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37
        ).all()
        
        print(f"📊 Total partidos del torneo 37: {len(partidos)}\n")
        
        # Agrupar por estado
        estados = {}
        for partido in partidos:
            estado = partido.estado or "sin_estado"
            if estado not in estados:
                estados[estado] = []
            estados[estado].append(partido)
        
        print("📋 Partidos por estado:")
        print("-" * 80)
        for estado, lista in estados.items():
            print(f"\n{estado.upper()}: {len(lista)} partidos")
            for p in lista[:5]:  # Mostrar solo los primeros 5
                print(f"   • Partido {p.id_partido}: Pareja {p.pareja1_id} vs {p.pareja2_id}")
                if p.ganador_pareja_id:
                    print(f"     Ganador: Pareja {p.ganador_pareja_id}")
                    
                    # Verificar si tiene historial de ELO
                    historial = db.query(HistorialRating).filter(
                        HistorialRating.id_partido == p.id_partido
                    ).count()
                    
                    if historial > 0:
                        print(f"     ✅ Tiene {historial} registros de ELO")
                        
                        # Mostrar los cambios
                        cambios = db.query(HistorialRating).filter(
                            HistorialRating.id_partido == p.id_partido
                        ).all()
                        
                        for c in cambios:
                            usuario = db.query(Usuario).filter(Usuario.id_usuario == c.id_usuario).first()
                            if usuario:
                                # Determinar si ganó
                                jugador_partido = db.query(PartidoJugador).filter(
                                    PartidoJugador.id_partido == p.id_partido,
                                    PartidoJugador.id_usuario == c.id_usuario
                                ).first()
                                
                                if jugador_partido:
                                    gano = jugador_partido.pareja_id == p.ganador_pareja_id
                                    resultado = "GANÓ" if gano else "PERDIÓ"
                                    
                                    # Verificar si el signo es correcto
                                    signo_correcto = (gano and c.delta > 0) or (not gano and c.delta < 0)
                                    marca = "✅" if signo_correcto else "❌"
                                    
                                    print(f"       {marca} {usuario.nombre_usuario}: {resultado}, delta={c.delta:+d}")
                    else:
                        print(f"     ⚠️  Sin historial de ELO")
            
            if len(lista) > 5:
                print(f"   ... y {len(lista) - 5} más")
        
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
    verificar_estados()
