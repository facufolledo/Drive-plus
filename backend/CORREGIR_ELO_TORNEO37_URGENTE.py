"""
SCRIPT URGENTE: Corregir ELO invertido en torneo 37
El bug: Los ganadores pierden puntos y los perdedores ganan puntos
Solución: Revertir todos los cambios de ELO y reaplicarlos correctamente
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

def corregir_elo_torneo37():
    """Corrige el ELO de todos los partidos del torneo 37"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🚨 CORRECCIÓN URGENTE: ELO INVERTIDO TORNEO 37")
        print("="*80 + "\n")
        
        # 1. Obtener todos los partidos finalizados del torneo 37 con ELO aplicado
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.estado == "finalizado",
            Partido.elo_aplicado == True
        ).all()
        
        print(f"📊 Partidos con ELO aplicado: {len(partidos)}\n")
        
        if len(partidos) == 0:
            print("✅ No hay partidos con ELO aplicado")
            return
        
        print("🔄 PASO 1: Revertir ELO mal aplicado")
        print("-" * 80)
        
        for partido in partidos:
            print(f"\nPartido {partido.id_partido}:")
            
            # Obtener jugadores del partido
            jugadores_partido = db.query(PartidoJugador).filter(
                PartidoJugador.id_partido == partido.id_partido
            ).all()
            
            for jp in jugadores_partido:
                if jp.rating_antes is not None and jp.cambio_elo is not None:
                    # Revertir: volver al rating anterior
                    usuario = db.query(Usuario).filter(Usuario.id_usuario == jp.id_usuario).first()
                    if usuario:
                        print(f"  Usuario {usuario.nombre_usuario}:")
                        print(f"    Rating actual: {usuario.rating}")
                        print(f"    Rating antes: {jp.rating_antes}")
                        print(f"    Cambio ELO (MAL): {jp.cambio_elo}")
                        
                        # Revertir al rating anterior
                        usuario.rating = jp.rating_antes
                        print(f"    ✅ Revertido a: {usuario.rating}")
            
            # Marcar partido como no procesado
            partido.elo_aplicado = False
            
            # Eliminar entradas del historial de rating de este partido
            db.query(HistorialRating).filter(
                HistorialRating.id_partido == partido.id_partido
            ).delete()
        
        db.commit()
        
        print("\n" + "="*80)
        print("✅ PASO 1 COMPLETADO: ELO Revertido")
        print("="*80 + "\n")
        
        print("🔄 PASO 2: Reaplicar ELO CORRECTAMENTE")
        print("-" * 80)
        print("\n⚠️  IMPORTANTE: Ahora debes ejecutar el endpoint de guardar resultado")
        print("para cada partido nuevamente, o usar el script de reaplicar ELO.\n")
        
        # Mostrar partidos que necesitan reaplicación
        print("📋 Partidos que necesitan reaplicar ELO:")
        print("-" * 80)
        
        for partido in partidos:
            print(f"  Partido {partido.id_partido}: Pareja {partido.pareja1_id} vs {partido.pareja2_id}")
            if partido.ganador_pareja_id:
                print(f"    Ganador: Pareja {partido.ganador_pareja_id}")
        
        print("\n" + "="*80)
        print("✅ CORRECCIÓN COMPLETADA")
        print("="*80)
        print("\n⚠️  SIGUIENTE PASO:")
        print("1. El ELO ha sido revertido")
        print("2. Los partidos están marcados como 'elo_aplicado = False'")
        print("3. Cuando vuelvas a cargar los resultados desde el frontend,")
        print("   el ELO se aplicará correctamente con el código corregido")
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  ADVERTENCIA: Este script revertirá el ELO de TODOS los partidos del torneo 37")
    print("¿Estás seguro de continuar? (escribe 'SI' para confirmar)")
    
    # En producción, comentar esta línea y ejecutar directamente
    # confirmacion = input("> ")
    # if confirmacion.upper() == "SI":
    corregir_elo_torneo37()
    # else:
    #     print("Operación cancelada")
