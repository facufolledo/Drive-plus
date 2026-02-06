"""
Verificar historial de rating completo del torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.config import get_db
from src.models.driveplus_models import Partido, Usuario, PartidoJugador, HistorialRating
from datetime import datetime

load_dotenv()

def verificar_historial_completo():
    """Verifica el historial de rating completo"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 VERIFICACIÓN: HISTORIAL DE RATING TORNEO 37")
        print("="*80 + "\n")
        
        # Obtener todos los registros de historial_rating del torneo 37
        # Para partidos de torneo, necesitamos determinar la pareja del jugador
        query = text("""
            SELECT 
                hr.id_historial,
                hr.id_usuario,
                hr.id_partido,
                hr.rating_antes,
                hr.delta,
                hr.rating_despues,
                hr.creado_en,
                u.nombre_usuario,
                p.ganador_pareja_id,
                p.pareja1_id,
                p.pareja2_id,
                tp1.jugador1_id as p1_j1,
                tp1.jugador2_id as p1_j2,
                tp2.jugador1_id as p2_j1,
                tp2.jugador2_id as p2_j2
            FROM historial_rating hr
            JOIN partidos p ON hr.id_partido = p.id_partido
            JOIN usuarios u ON hr.id_usuario = u.id_usuario
            LEFT JOIN torneos_parejas tp1 ON tp1.id_pareja = p.pareja1_id
            LEFT JOIN torneos_parejas tp2 ON tp2.id_pareja = p.pareja2_id
            WHERE p.id_torneo = 37
            ORDER BY hr.creado_en DESC, hr.id_partido
        """)
        
        resultados = db.execute(query).fetchall()
        
        print(f"📊 Total registros de historial: {len(resultados)}\n")
        
        if len(resultados) == 0:
            print("⚠️  No hay registros de historial de rating para el torneo 37")
            return
        
        # Agrupar por partido
        partidos_dict = {}
        for r in resultados:
            id_partido = r[2]
            if id_partido not in partidos_dict:
                partidos_dict[id_partido] = []
            partidos_dict[id_partido].append(r)
        
        print(f"📋 Partidos con historial de ELO: {len(partidos_dict)}\n")
        
        errores_encontrados = 0
        correctos = 0
        
        for id_partido, registros in partidos_dict.items():
            print(f"\n{'='*80}")
            print(f"🏓 PARTIDO {id_partido}")
            print(f"{'='*80}")
            
            ganador_pareja_id = registros[0][8]
            pareja1_id = registros[0][9]
            pareja2_id = registros[0][10]
            print(f"Pareja 1: {pareja1_id} vs Pareja 2: {pareja2_id}")
            print(f"Ganador: Pareja {ganador_pareja_id}")
            
            print(f"\n📈 Cambios de ELO:")
            print("-" * 80)
            
            for r in registros:
                nombre_usuario = r[7]
                rating_antes = r[3]
                delta = r[4]
                rating_despues = r[5]
                id_usuario = r[1]
                
                # Determinar a qué pareja pertenece el jugador
                p1_j1 = r[11]
                p1_j2 = r[12]
                p2_j1 = r[13]
                p2_j2 = r[14]
                
                if id_usuario in (p1_j1, p1_j2):
                    pareja_id = pareja1_id
                elif id_usuario in (p2_j1, p2_j2):
                    pareja_id = pareja2_id
                else:
                    pareja_id = None
                
                # Determinar si ganó
                gano = pareja_id == ganador_pareja_id if pareja_id else None
                
                if gano is None:
                    resultado_texto = "PAREJA DESCONOCIDA ⚠️"
                    marca = "⚠️  NO SE PUEDE VERIFICAR"
                else:
                    resultado_texto = "GANÓ ✅" if gano else "PERDIÓ ❌"
                    
                    # Verificar si el signo del delta es correcto
                    signo_correcto = (gano and delta > 0) or (not gano and delta < 0)
                    
                    if signo_correcto:
                        marca = "✅ CORRECTO"
                        correctos += 1
                    else:
                        marca = "❌ ERROR - ELO INVERTIDO"
                        errores_encontrados += 1
                
                print(f"\n{nombre_usuario} ({resultado_texto}):")
                if pareja_id:
                    print(f"  Pareja: {pareja_id}")
                print(f"  Rating antes: {rating_antes}")
                print(f"  Delta: {delta:+d}")
                print(f"  Rating después: {rating_despues}")
                print(f"  {marca}")
                
                if gano is not None and not signo_correcto:
                    if gano:
                        print(f"  🚨 PROBLEMA: Ganó pero perdió {abs(delta)} puntos")
                    else:
                        print(f"  🚨 PROBLEMA: Perdió pero ganó {delta} puntos")
        
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
    tiene_errores = verificar_historial_completo()
    sys.exit(1 if tiene_errores else 0)
