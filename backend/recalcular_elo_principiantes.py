"""
Script para recalcular ELO de jugadores principiantes con K-factor más alto
Objetivo: Permitir que jugadores iniciales suban más rápido de Principiante a 8va
"""

import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar conexión a la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no está configurada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# === NUEVA CONFIGURACIÓN DE K-FACTORS ===
# Aumentamos K-factor para jugadores con pocos partidos
NUEVOS_K_FACTORS = {
    "nuevo": {"max_partidos": 10, "k_value": 250},      # 0-10 partidos: K=250 (antes 200)
    "intermedio": {"max_partidos": 25, "k_value": 200}, # 11-25 partidos: K=200 (antes 180)
    "estable": {"max_partidos": 50, "k_value": 150},    # 26-50 partidos: K=150 (antes 20)
    "experto": {"max_partidos": float('inf'), "k_value": 100}  # 51+ partidos: K=100 (antes 15)
}

def get_nuevo_k_factor(partidos_jugados: int) -> int:
    """Obtener nuevo K-factor basado en partidos jugados"""
    for level, config in NUEVOS_K_FACTORS.items():
        if partidos_jugados <= config["max_partidos"]:
            return config["k_value"]
    return NUEVOS_K_FACTORS["experto"]["k_value"]

def obtener_jugadores_principiantes(session):
    """Obtener todos los jugadores de categoría Principiante"""
    query = text("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario as username,
            pu.nombre,
            pu.apellido,
            u.rating as rating_actual,
            u.sexo,
            u.partidos_jugados
        FROM usuarios u
        INNER JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        INNER JOIN categorias c ON u.id_categoria = c.id_categoria
        WHERE c.nombre = 'Principiante'
        ORDER BY u.partidos_jugados DESC, u.rating DESC
    """)
    
    result = session.execute(query)
    return result.fetchall()

def obtener_partidos_usuario(session, usuario_id: int):
    """Obtener todos los partidos de un usuario en orden cronológico"""
    query = text("""
        SELECT 
            p.id_partido,
            p.id_torneo,
            p.fase,
            p.pareja1_id,
            p.pareja2_id,
            p.resultado_pareja1,
            p.resultado_pareja2,
            p.sets_pareja1,
            p.sets_pareja2,
            p.games_pareja1,
            p.games_pareja2,
            p.estado,
            p.fecha_programada,
            p.fecha_inicio,
            p.fecha_fin,
            t.tipo as tipo_torneo,
            -- Jugadores de pareja 1
            pj1_u1.id_usuario as p1_j1_id,
            pj1_u2.id_usuario as p1_j2_id,
            -- Jugadores de pareja 2
            pj2_u1.id_usuario as p2_j1_id,
            pj2_u2.id_usuario as p2_j2_id
        FROM partidos p
        INNER JOIN torneos t ON p.id_torneo = t.id_torneo
        INNER JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id_pareja
        INNER JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id_pareja
        LEFT JOIN partido_jugadores pj1_u1 ON tp1.jugador1_id = pj1_u1.id_usuario AND p.id_partido = pj1_u1.id_partido
        LEFT JOIN partido_jugadores pj1_u2 ON tp1.jugador2_id = pj1_u2.id_usuario AND p.id_partido = pj1_u2.id_partido
        LEFT JOIN partido_jugadores pj2_u1 ON tp2.jugador1_id = pj2_u1.id_usuario AND p.id_partido = pj2_u1.id_partido
        LEFT JOIN partido_jugadores pj2_u2 ON tp2.jugador2_id = pj2_u2.id_usuario AND p.id_partido = pj2_u2.id_partido
        WHERE p.estado = 'finalizado'
          AND (tp1.jugador1_id = :usuario_id 
               OR tp1.jugador2_id = :usuario_id
               OR tp2.jugador1_id = :usuario_id
               OR tp2.jugador2_id = :usuario_id)
        ORDER BY 
            COALESCE(p.fecha_fin, p.fecha_inicio, p.fecha_programada) ASC,
            p.id_partido ASC
    """)
    
    result = session.execute(query, {"usuario_id": usuario_id})
    return result.fetchall()

def recalcular_elo_usuario(session, usuario_id: int, rating_inicial: int, sexo: str, dry_run: bool = True):
    """
    Recalcular ELO de un usuario desde cero con nuevos K-factors
    
    Returns:
        dict: Información del recálculo
    """
    from src.services.elo_service import EloService
    from src.services.elo_config import EloConfig
    
    # Temporalmente modificar K-factors en EloConfig
    original_k_factors = EloConfig.K_FACTORS.copy()
    EloConfig.K_FACTORS = NUEVOS_K_FACTORS
    
    elo_service = EloService()
    
    # Obtener todos los partidos del usuario
    partidos = obtener_partidos_usuario(session, usuario_id)
    
    if not partidos:
        EloConfig.K_FACTORS = original_k_factors
        return {
            "usuario_id": usuario_id,
            "partidos_procesados": 0,
            "rating_inicial": rating_inicial,
            "rating_final": rating_inicial,
            "cambio_total": 0
        }
    
    # Inicializar rating
    rating_actual = rating_inicial
    partidos_jugados = 0
    cambios = []
    
    print(f"\n{'='*80}")
    print(f"Recalculando ELO para usuario {usuario_id}")
    print(f"Rating inicial: {rating_inicial}")
    print(f"Total de partidos: {len(partidos)}")
    print(f"{'='*80}\n")
    
    for partido in partidos:
        # Determinar si el usuario está en pareja1 o pareja2
        usuario_en_pareja1 = (partido.p1_j1_id == usuario_id or partido.p1_j2_id == usuario_id)
        
        if usuario_en_pareja1:
            # Usuario en pareja 1
            mi_pareja_id = partido.pareja1_id
            oponente_pareja_id = partido.pareja2_id
            sets_ganados = partido.sets_pareja1 or 0
            sets_perdidos = partido.sets_pareja2 or 0
            games_ganados = partido.games_pareja1 or 0
            games_perdidos = partido.games_pareja2 or 0
            
            # Obtener compañero
            companero_id = partido.p1_j2_id if partido.p1_j1_id == usuario_id else partido.p1_j1_id
            
            # Obtener oponentes
            oponente1_id = partido.p2_j1_id
            oponente2_id = partido.p2_j2_id
        else:
            # Usuario en pareja 2
            mi_pareja_id = partido.pareja2_id
            oponente_pareja_id = partido.pareja1_id
            sets_ganados = partido.sets_pareja2 or 0
            sets_perdidos = partido.sets_pareja1 or 0
            games_ganados = partido.games_pareja2 or 0
            games_perdidos = partido.games_pareja1 or 0
            
            # Obtener compañero
            companero_id = partido.p2_j2_id if partido.p2_j1_id == usuario_id else partido.p2_j1_id
            
            # Obtener oponentes
            oponente1_id = partido.p1_j1_id
            oponente2_id = partido.p1_j2_id
        
        # Obtener ratings de todos los jugadores en el momento del partido
        # (simplificado: usamos rating actual, en producción deberíamos usar rating histórico)
        query_ratings = text("""
            SELECT id_usuario, rating
            FROM usuarios
            WHERE id_usuario IN (:u1, :u2, :u3, :u4)
        """)
        
        ratings_result = session.execute(query_ratings, {
            "u1": usuario_id,
            "u2": companero_id,
            "u3": oponente1_id,
            "u4": oponente2_id
        })
        
        ratings_dict = {row.id_usuario: row.rating for row in ratings_result}
        
        # Usar rating actual del usuario (que estamos recalculando)
        rating_usuario = rating_actual
        rating_companero = ratings_dict.get(companero_id, 1000)
        rating_oponente1 = ratings_dict.get(oponente1_id, 1000)
        rating_oponente2 = ratings_dict.get(oponente2_id, 1000)
        
        # Calcular nuevo K-factor
        k_factor = get_nuevo_k_factor(partidos_jugados)
        
        # Preparar datos para EloService
        team_a_players = [
            {"rating": rating_usuario, "partidos": partidos_jugados, "volatilidad": 1.0, "id": usuario_id},
            {"rating": rating_companero, "partidos": 10, "volatilidad": 1.0, "id": companero_id}
        ]
        
        team_b_players = [
            {"rating": rating_oponente1, "partidos": 10, "volatilidad": 1.0, "id": oponente1_id},
            {"rating": rating_oponente2, "partidos": 10, "volatilidad": 1.0, "id": oponente2_id}
        ]
        
        # Determinar tipo de partido
        if partido.fase in ['4tos', 'semis', 'final']:
            match_type = partido.fase
        elif partido.fase == 'zona':
            match_type = 'zona'
        elif partido.tipo_torneo == 'torneo':
            match_type = 'torneo'
        else:
            match_type = 'amistoso'
        
        # Calcular ELO
        try:
            resultado = elo_service.calculate_match_ratings(
                team_a_players=team_a_players,
                team_b_players=team_b_players,
                sets_a=sets_ganados,
                sets_b=sets_perdidos,
                games_a=games_ganados,
                games_b=games_perdidos,
                match_type=match_type
            )
            
            # Obtener cambio de rating del usuario
            delta = resultado["team_a"]["players"][0]["rating_change"]
            nuevo_rating = resultado["team_a"]["players"][0]["new_rating"]
            
            cambios.append({
                "partido_id": partido.id_partido,
                "rating_antes": rating_actual,
                "delta": delta,
                "rating_despues": nuevo_rating,
                "k_factor": k_factor,
                "sets": f"{sets_ganados}-{sets_perdidos}",
                "games": f"{games_ganados}-{games_perdidos}",
                "tipo": match_type
            })
            
            print(f"Partido {partido.id_partido}: {rating_actual} → {nuevo_rating} ({delta:+.1f}) | "
                  f"Sets: {sets_ganados}-{sets_perdidos} | K={k_factor} | Tipo: {match_type}")
            
            rating_actual = nuevo_rating
            partidos_jugados += 1
            
        except Exception as e:
            print(f"❌ Error en partido {partido.id_partido}: {e}")
            continue
    
    # Restaurar K-factors originales
    EloConfig.K_FACTORS = original_k_factors
    
    cambio_total = rating_actual - rating_inicial
    
    print(f"\n{'='*80}")
    print(f"✅ Recálculo completado")
    print(f"Rating inicial: {rating_inicial}")
    print(f"Rating final: {rating_actual}")
    print(f"Cambio total: {cambio_total:+.1f}")
    print(f"Partidos procesados: {partidos_jugados}")
    print(f"{'='*80}\n")
    
    # Si no es dry-run, actualizar en la base de datos
    if not dry_run:
        # Actualizar rating actual
        update_query = text("""
            UPDATE usuarios
            SET rating = :nuevo_rating
            WHERE id_usuario = :usuario_id
        """)
        session.execute(update_query, {
            "nuevo_rating": rating_actual,
            "usuario_id": usuario_id
        })
        
        # Actualizar historial de rating
        for cambio in cambios:
            update_historial = text("""
                UPDATE historial_rating
                SET 
                    rating_antes = :rating_antes,
                    delta = :delta,
                    rating_despues = :rating_despues
                WHERE id_usuario = :usuario_id
                  AND id_partido = :partido_id
            """)
            session.execute(update_historial, {
                "rating_antes": cambio["rating_antes"],
                "delta": cambio["delta"],
                "rating_despues": cambio["rating_despues"],
                "usuario_id": usuario_id,
                "partido_id": cambio["partido_id"]
            })
        
        session.commit()
        print(f"✅ Cambios guardados en la base de datos")
    
    return {
        "usuario_id": usuario_id,
        "partidos_procesados": partidos_jugados,
        "rating_inicial": rating_inicial,
        "rating_final": rating_actual,
        "cambio_total": cambio_total,
        "cambios": cambios
    }

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Recalcular ELO de jugadores principiantes")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin guardar cambios")
    parser.add_argument("--usuario-id", type=int, help="Recalcular solo un usuario específico")
    
    args = parser.parse_args()
    
    session = Session()
    
    try:
        if args.usuario_id:
            # Recalcular solo un usuario
            query = text("""
                SELECT rating_actual, sexo
                FROM perfil_usuarios
                WHERE id_usuario = :usuario_id
            """)
            result = session.execute(query, {"usuario_id": args.usuario_id})
            row = result.fetchone()
            
            if not row:
                print(f"❌ Usuario {args.usuario_id} no encontrado")
                return
            
            print(f"\n{'='*80}")
            print(f"RECALCULANDO ELO - Usuario {args.usuario_id}")
            print(f"Modo: {'DRY RUN (simulación)' if args.dry_run else 'PRODUCCIÓN (guardará cambios)'}")
            print(f"{'='*80}\n")
            
            resultado = recalcular_elo_usuario(
                session, 
                args.usuario_id, 
                row.rating_actual, 
                row.sexo,
                dry_run=args.dry_run
            )
            
            print(f"\n✅ Recálculo completado para usuario {args.usuario_id}")
            print(f"Rating: {resultado['rating_inicial']} → {resultado['rating_final']} ({resultado['cambio_total']:+.1f})")
            
        else:
            # Recalcular todos los jugadores principiantes
            jugadores = obtener_jugadores_principiantes(session)
            
            print(f"\n{'='*80}")
            print(f"RECALCULANDO ELO - Todos los jugadores Principiantes")
            print(f"Modo: {'DRY RUN (simulación)' if args.dry_run else 'PRODUCCIÓN (guardará cambios)'}")
            print(f"Total de jugadores: {len(jugadores)}")
            print(f"{'='*80}\n")
            
            resultados = []
            
            for jugador in jugadores:
                print(f"\n--- Procesando: {jugador.nombre} {jugador.apellido} (@{jugador.username}) ---")
                print(f"Rating actual: {jugador.rating_actual}")
                print(f"Partidos jugados: {jugador.partidos_jugados}")
                
                resultado = recalcular_elo_usuario(
                    session,
                    jugador.id_usuario,
                    jugador.rating_actual,
                    jugador.sexo,
                    dry_run=args.dry_run
                )
                
                resultados.append(resultado)
            
            # Resumen final
            print(f"\n{'='*80}")
            print(f"RESUMEN FINAL")
            print(f"{'='*80}\n")
            
            for resultado in resultados:
                print(f"Usuario {resultado['usuario_id']}: "
                      f"{resultado['rating_inicial']} → {resultado['rating_final']} "
                      f"({resultado['cambio_total']:+.1f}) | "
                      f"{resultado['partidos_procesados']} partidos")
            
            if args.dry_run:
                print(f"\n⚠️  DRY RUN: No se guardaron cambios en la base de datos")
                print(f"Ejecuta sin --dry-run para aplicar los cambios")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    
    finally:
        session.close()

if __name__ == "__main__":
    main()
