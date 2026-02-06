"""
SCRIPT COMPLETO: Corregir ELO invertido en torneo 37
1. Revierte todos los cambios de ELO mal aplicados
2. Reapl ica el ELO correctamente usando el código corregido
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido, Usuario, HistorialRating
from src.models.torneo_models import TorneoPareja
from src.services.elo_service import EloService
from datetime import datetime

load_dotenv()

def revertir_elo_torneo37(db: Session):
    """Revierte el ELO mal aplicado"""
    print("\n" + "="*80)
    print("🔄 PASO 1: REVERTIR ELO MAL APLICADO")
    print("="*80 + "\n")
    
    # Obtener partidos confirmados con historial de ELO
    partidos = db.query(Partido).filter(
        Partido.id_torneo == 37,
        Partido.estado == "confirmado",
        Partido.ganador_pareja_id.isnot(None)
    ).all()
    
    print(f"📊 Partidos a revertir: {len(partidos)}\n")
    
    total_revertidos = 0
    
    for partido in partidos:
        print(f"Partido {partido.id_partido}:")
        
        # Obtener historial de ELO
        historial = db.query(HistorialRating).filter(
            HistorialRating.id_partido == partido.id_partido
        ).all()
        
        if not historial:
            print("  ⚠️  Sin historial de ELO")
            continue
        
        for h in historial:
            usuario = db.query(Usuario).filter(Usuario.id_usuario == h.id_usuario).first()
            if usuario:
                print(f"  {usuario.nombre_usuario}: {usuario.rating} → {h.rating_antes}")
                usuario.rating = h.rating_antes
                total_revertidos += 1
        
        # Eliminar historial de ELO
        db.query(HistorialRating).filter(
            HistorialRating.id_partido == partido.id_partido
        ).delete()
    
    db.commit()
    
    print(f"\n✅ Revertidos {total_revertidos} cambios de ELO")
    print(f"✅ Eliminados {total_revertidos} registros de historial")
    
    return len(partidos)

def reaplicar_elo_torneo37(db: Session):
    """Reapl ica el ELO correctamente"""
    print("\n" + "="*80)
    print("🔄 PASO 2: REAPLICAR ELO CORRECTAMENTE")
    print("="*80 + "\n")
    
    # Obtener partidos confirmados sin historial de ELO
    partidos = db.query(Partido).filter(
        Partido.id_torneo == 37,
        Partido.estado == "confirmado",
        Partido.ganador_pareja_id.isnot(None)
    ).all()
    
    print(f"📊 Partidos a procesar: {len(partidos)}\n")
    
    elo_service = EloService()
    total_aplicados = 0
    errores = 0
    
    for partido in partidos:
        print(f"\nPartido {partido.id_partido}: Pareja {partido.pareja1_id} vs {partido.pareja2_id}")
        print(f"Ganador: Pareja {partido.ganador_pareja_id}")
        
        try:
            # Obtener parejas
            pareja1 = db.query(TorneoPareja).filter(TorneoPareja.id == partido.pareja1_id).first()
            pareja2 = db.query(TorneoPareja).filter(TorneoPareja.id == partido.pareja2_id).first()
            
            if not pareja1 or not pareja2:
                print("  ❌ Error: No se encontraron las parejas")
                errores += 1
                continue
            
            # Obtener jugadores
            j1_p1 = db.query(Usuario).filter(Usuario.id_usuario == pareja1.jugador1_id).first()
            j2_p1 = db.query(Usuario).filter(Usuario.id_usuario == pareja1.jugador2_id).first()
            j1_p2 = db.query(Usuario).filter(Usuario.id_usuario == pareja2.jugador1_id).first()
            j2_p2 = db.query(Usuario).filter(Usuario.id_usuario == pareja2.jugador2_id).first()
            
            if not all([j1_p1, j2_p1, j1_p2, j2_p2]):
                print("  ❌ Error: No se encontraron todos los jugadores")
                errores += 1
                continue
            
            # Obtener resultado
            resultado = partido.resultado_padel
            if not resultado or 'sets' not in resultado:
                print("  ❌ Error: No se encontró resultado")
                errores += 1
                continue
            
            sets = resultado['sets']
            
            # Contar sets ganados por cada equipo
            sets_a = sum(1 for s in sets if s.get('ganador') == 'equipoA' and s.get('completado'))
            sets_b = sum(1 for s in sets if s.get('ganador') == 'equipoB' and s.get('completado'))
            
            # Contar games
            games_a = sum(s.get('gamesEquipoA', 0) for s in sets if s.get('completado'))
            games_b = sum(s.get('gamesEquipoB', 0) for s in sets if s.get('completado'))
            
            print(f"  Resultado: {sets_a}-{sets_b} sets, {games_a}-{games_b} games")
            
            # Preparar datos para ELO
            team_a_players = [
                {
                    "rating": j1_p1.rating,
                    "partidos": j1_p1.partidos_jugados,
                    "volatilidad": getattr(j1_p1, 'volatilidad', 1.0),
                    "id": j1_p1.id_usuario
                },
                {
                    "rating": j2_p1.rating,
                    "partidos": j2_p1.partidos_jugados,
                    "volatilidad": getattr(j2_p1, 'volatilidad', 1.0),
                    "id": j2_p1.id_usuario
                }
            ]
            
            team_b_players = [
                {
                    "rating": j1_p2.rating,
                    "partidos": j1_p2.partidos_jugados,
                    "volatilidad": getattr(j1_p2, 'volatilidad', 1.0),
                    "id": j1_p2.id_usuario
                },
                {
                    "rating": j2_p2.rating,
                    "partidos": j2_p2.partidos_jugados,
                    "volatilidad": getattr(j2_p2, 'volatilidad', 1.0),
                    "id": j2_p2.id_usuario
                }
            ]
            
            # Calcular nuevos ratings
            nuevos_ratings = elo_service.calculate_match_ratings(
                team_a_players=team_a_players,
                team_b_players=team_b_players,
                sets_a=sets_a,
                sets_b=sets_b,
                games_a=games_a,
                games_b=games_b,
                desenlace="normal",
                match_type="torneo",
                match_date=partido.fecha or datetime.now()
            )
            
            # Aplicar cambios
            jugadores = [
                (j1_p1, nuevos_ratings['team_a']['players'][0]),
                (j2_p1, nuevos_ratings['team_a']['players'][1]),
                (j1_p2, nuevos_ratings['team_b']['players'][0]),
                (j2_p2, nuevos_ratings['team_b']['players'][1])
            ]
            
            print("  📈 Cambios de ELO:")
            
            for usuario, player_data in jugadores:
                rating_antes = usuario.rating
                rating_despues = player_data['new_rating']
                delta = player_data['rating_change']
                
                # Actualizar usuario
                usuario.rating = int(rating_despues)
                usuario.partidos_jugados += 1
                
                # Crear historial
                historial = HistorialRating(
                    id_usuario=usuario.id_usuario,
                    id_partido=partido.id_partido,
                    rating_antes=rating_antes,
                    delta=int(delta),
                    rating_despues=int(rating_despues)
                )
                db.add(historial)
                
                # Determinar si ganó
                if usuario.id_usuario in (pareja1.jugador1_id, pareja1.jugador2_id):
                    pareja_id = partido.pareja1_id
                else:
                    pareja_id = partido.pareja2_id
                
                gano = pareja_id == partido.ganador_pareja_id
                resultado_texto = "GANÓ ✅" if gano else "PERDIÓ ❌"
                
                # Verificar que el signo sea correcto
                signo_correcto = (gano and delta > 0) or (not gano and delta < 0)
                marca = "✅" if signo_correcto else "❌"
                
                print(f"    {marca} {usuario.nombre_usuario} ({resultado_texto}): {rating_antes} → {rating_despues} ({int(delta):+d})")
                
                total_aplicados += 1
            
            db.commit()
            print("  ✅ ELO aplicado correctamente")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            errores += 1
            db.rollback()
    
    print(f"\n✅ Aplicados {total_aplicados} cambios de ELO")
    if errores > 0:
        print(f"⚠️  {errores} errores encontrados")
    
    return total_aplicados, errores

def corregir_elo_completo():
    """Ejecuta la corrección completa del ELO"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🚨 CORRECCIÓN COMPLETA: ELO INVERTIDO TORNEO 37")
        print("="*80)
        
        # Paso 1: Revertir
        partidos_revertidos = revertir_elo_torneo37(db)
        
        # Paso 2: Reaplicar
        cambios_aplicados, errores = reaplicar_elo_torneo37(db)
        
        # Resumen final
        print("\n" + "="*80)
        print("📊 RESUMEN FINAL")
        print("="*80)
        print(f"Partidos procesados: {partidos_revertidos}")
        print(f"Cambios de ELO aplicados: {cambios_aplicados}")
        print(f"Errores: {errores}")
        
        if errores == 0:
            print("\n✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
        else:
            print(f"\n⚠️  CORRECCIÓN COMPLETADA CON {errores} ERRORES")
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  ADVERTENCIA: Este script revertirá y reaplicará el ELO de TODOS los partidos del torneo 37")
    print("¿Estás seguro de continuar? (escribe 'SI' para confirmar)")
    
    # En producción, descomentar esta línea
    # confirmacion = input("> ")
    # if confirmacion.upper() == "SI":
    corregir_elo_completo()
    # else:
    #     print("Operación cancelada")
