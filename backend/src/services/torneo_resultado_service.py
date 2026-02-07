"""
Servicio para gestión de resultados en torneos
"""
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from ..models.driveplus_models import Partido
from ..models.torneo_models import TorneoPareja, TorneoZona
from ..services.categoria_service import actualizar_categoria_usuario


class TorneoResultadoService:
    """Servicio para cargar y gestionar resultados de partidos de torneo"""
    
    @staticmethod
    def cargar_resultado(
        db: Session,
        partido_id: int,
        resultado_data: Dict,
        user_id: int
    ) -> Partido:
        """
        Carga el resultado de un partido de torneo
        
        Args:
            db: Sesión de base de datos
            partido_id: ID del partido
            resultado_data: Datos del resultado en formato JSON
            user_id: ID del usuario que carga el resultado
            
        Returns:
            Partido actualizado
        """
        # Obtener partido
        partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
        if not partido:
            raise ValueError("Partido no encontrado")
        
        # Verificar que sea partido de torneo
        if partido.tipo != 'torneo':
            raise ValueError("Este partido no es de torneo")
        
        # Verificar que el partido esté pendiente
        if partido.estado == 'confirmado':
            raise ValueError("El partido ya está confirmado")
        
        # Validar resultado
        TorneoResultadoService._validar_resultado(resultado_data)
        
        # Determinar ganador
        ganador_pareja_id = TorneoResultadoService._determinar_ganador(
            resultado_data, partido.pareja1_id, partido.pareja2_id
        )
        
        # Actualizar partido
        partido.resultado_padel = resultado_data
        partido.estado = 'confirmado'  # Usar 'confirmado' en lugar de 'finalizado'
        partido.ganador_pareja_id = ganador_pareja_id
        
        # Aplicar ELO y actualizar estadísticas de jugadores
        try:
            TorneoResultadoService._aplicar_elo_torneo(db, partido, resultado_data, ganador_pareja_id)
            partido.elo_aplicado = True
            logger.info(f"ELO aplicado correctamente para partido {partido.id_partido}")
        except Exception as e:
            import traceback
            logger.error(f"Error aplicando ELO en torneo: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            partido.elo_aplicado = False
        
        db.commit()
        db.refresh(partido)
        
        # Si es partido de playoffs, avanzar ganador a siguiente fase
        if partido.fase and partido.fase != 'zona':
            TorneoResultadoService._avanzar_ganador_playoff(db, partido, ganador_pareja_id)
        else:
            # Si es partido de zona, verificar si se completaron todas las zonas
            # para auto-generar playoffs
            TorneoResultadoService._verificar_auto_playoffs(db, partido.id_torneo)
        
        return partido
    
    @staticmethod
    def _verificar_auto_playoffs(db: Session, torneo_id: int) -> bool:
        """
        Verifica si todas las zonas están completas y auto-genera playoffs si corresponde
        
        Returns:
            True si se generaron playoffs automáticamente
        """
        from ..models.torneo_models import Torneo, TorneoZona
        
        # Obtener torneo
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            return False
        
        # Solo auto-generar si está en fase_grupos
        if str(torneo.estado) not in ['fase_grupos', 'EstadoTorneo.FASE_GRUPOS']:
            return False
        
        # Verificar si ya hay partidos de playoffs
        partidos_playoffs = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase != 'zona',
            Partido.fase.isnot(None)
        ).count()
        
        if partidos_playoffs > 0:
            # Ya hay playoffs generados
            return False
        
        # Obtener todas las zonas
        zonas = db.query(TorneoZona).filter(TorneoZona.torneo_id == torneo_id).all()
        if not zonas:
            return False
        
        # Verificar que todas las zonas estén completas
        todas_completas = True
        for zona in zonas:
            if not TorneoResultadoService.verificar_zona_completa(db, zona.id):
                todas_completas = False
                break
        
        if not todas_completas:
            return False
        
        # Todas las zonas completas - generar playoffs automáticamente
        try:
            from ..services.torneo_playoff_service import TorneoPlayoffService
            
            logger.info(f"Auto-generando playoffs para torneo {torneo_id}")
            TorneoPlayoffService.generar_playoffs(
                db=db,
                torneo_id=torneo_id,
                user_id=torneo.creado_por,  # Usar el creador del torneo
                clasificados_por_zona=2
            )
            logger.info(f"Playoffs auto-generados exitosamente para torneo {torneo_id}")
            return True
        except Exception as e:
            logger.error(f"Error auto-generando playoffs: {e}")
            return False
    
    @staticmethod
    def _avanzar_ganador_playoff(
        db: Session,
        partido: Partido,
        ganador_pareja_id: int
    ) -> Optional[Partido]:
        """
        Avanza al ganador de un partido de playoff a la siguiente ronda
        
        Args:
            db: Sesión de base de datos
            partido: Partido finalizado
            ganador_pareja_id: ID de la pareja ganadora
            
        Returns:
            Partido de siguiente ronda actualizado, o None si es la final
        """
        from ..models.torneo_models import Torneo
        
        logger.info(f"Avanzando ganador {ganador_pareja_id} de partido {partido.id_partido} fase {partido.fase}")
        
        # Si es la final, marcar torneo como finalizado
        if partido.fase == 'final':
            torneo = db.query(Torneo).filter(Torneo.id == partido.id_torneo).first()
            if torneo:
                torneo.estado = 'finalizado'  # String en lugar de Enum
                db.commit()
                logger.info(f"Torneo {partido.id_torneo} marcado como finalizado")
            return None
        
        # Determinar siguiente fase
        fases_orden = ['16avos', '8vos', '4tos', 'semis', 'final']
        fase_actual = partido.fase
        if fase_actual == 'semifinal':
            fase_actual = 'semis'
        elif fase_actual == 'cuartos':
            fase_actual = '4tos'
            
        try:
            idx_actual = fases_orden.index(fase_actual)
            siguiente_fase = fases_orden[idx_actual + 1]
        except (ValueError, IndexError):
            return None
        
        # Buscar o crear partido de siguiente ronda
        # Lógica: el ganador del partido N va al partido (N+1)//2 de la siguiente fase
        numero_partido = partido.numero_partido or 1
        numero_siguiente = (numero_partido + 1) // 2
        
        partido_siguiente = db.query(Partido).filter(
            Partido.id_torneo == partido.id_torneo,
            Partido.fase == siguiente_fase,
            Partido.numero_partido == numero_siguiente,
            Partido.categoria_id == partido.categoria_id
        ).first()
        
        # Si no existe el partido de siguiente fase, crearlo (poco habitual; el bracket ya los crea)
        if not partido_siguiente:
            partido_siguiente = Partido(
                id_torneo=partido.id_torneo,
                categoria_id=partido.categoria_id,
                fase=siguiente_fase,
                numero_partido=numero_siguiente,
                estado='pendiente',
                fecha=partido.fecha,
                id_creador=partido.id_creador,
                tipo='torneo'
            )
            db.add(partido_siguiente)
            db.flush()
        
        # Asignar ganador a la posición correspondiente
        # Partido impar -> pareja1, Partido par -> pareja2
        if numero_partido % 2 == 1:
            partido_siguiente.pareja1_id = ganador_pareja_id
            logger.info(f"Asignado ganador {ganador_pareja_id} como pareja1 en partido {partido_siguiente.id_partido} ({siguiente_fase})")
        else:
            partido_siguiente.pareja2_id = ganador_pareja_id
            logger.info(f"Asignado ganador {ganador_pareja_id} como pareja2 en partido {partido_siguiente.id_partido} ({siguiente_fase})")
        
        db.commit()
        db.refresh(partido_siguiente)
        
        logger.info(f"Partido siguiente actualizado: pareja1={partido_siguiente.pareja1_id}, pareja2={partido_siguiente.pareja2_id}")
        
        # Verificar si el partido siguiente ya tiene ambas parejas y una es de bye
        # Si es así, verificar si necesita crear el siguiente partido
        TorneoResultadoService._verificar_partido_listo(db, partido_siguiente)
        
        return partido_siguiente
    
    @staticmethod
    def _verificar_partido_listo(db: Session, partido: Partido) -> None:
        """
        Verifica si un partido tiene ambas parejas asignadas.
        Si una pareja viene de bye y la otra acaba de ser asignada,
        el partido está listo para jugarse.
        """
        if partido.pareja1_id and partido.pareja2_id:
            logger.info(f"Partido {partido.id_partido} ({partido.fase}) listo: {partido.pareja1_id} vs {partido.pareja2_id}")
    
    @staticmethod
    def _validar_resultado(resultado: Dict) -> None:
        """
        Valida que el resultado sea válido según reglas de pádel
        
        Reglas:
        - Debe haber al menos 2 sets
        - Máximo 3 sets
        - Un equipo debe ganar al menos 2 sets
        - Cada set debe tener un ganador claro
        - Games válidos: 6-0, 6-1, 6-2, 6-3, 6-4, 7-5, 7-6 (tiebreak)
        """
        if 'sets' not in resultado:
            raise ValueError("El resultado debe incluir los sets")
        
        sets = resultado['sets']
        
        if len(sets) < 2:
            raise ValueError("Debe haber al menos 2 sets")
        
        if len(sets) > 3:
            raise ValueError("No puede haber más de 3 sets")
        
        # Contar sets ganados por cada equipo
        sets_equipo_a = 0
        sets_equipo_b = 0
        
        for i, set_data in enumerate(sets):
            if not set_data.get('completado'):
                raise ValueError(f"El set {i+1} no está completado")
            
            games_a = set_data.get('gamesEquipoA', 0)
            games_b = set_data.get('gamesEquipoB', 0)
            
            # Validar games
            if not TorneoResultadoService._validar_games(games_a, games_b):
                raise ValueError(f"Games inválidos en set {i+1}: {games_a}-{games_b}")
            
            # Contar ganador del set
            if set_data.get('ganador') == 'equipoA':
                sets_equipo_a += 1
            elif set_data.get('ganador') == 'equipoB':
                sets_equipo_b += 1
            else:
                raise ValueError(f"El set {i+1} debe tener un ganador")
        
        # Verificar que haya un ganador claro
        if sets_equipo_a < 2 and sets_equipo_b < 2:
            raise ValueError("Debe haber un ganador con al menos 2 sets")
        
        # Verificar que el ganador tenga 2 sets
        if max(sets_equipo_a, sets_equipo_b) < 2:
            raise ValueError("El ganador debe tener al menos 2 sets")
        
        # Si hay 3 sets, verificar que sea 2-1
        if len(sets) == 3:
            if not ((sets_equipo_a == 2 and sets_equipo_b == 1) or 
                    (sets_equipo_a == 1 and sets_equipo_b == 2)):
                raise ValueError("Con 3 sets, el resultado debe ser 2-1")
    
    @staticmethod
    def _validar_games(games_a: int, games_b: int) -> bool:
        """
        Valida que los games sean válidos según reglas de pádel
        
        Resultados válidos:
        - 6-0, 6-1, 6-2, 6-3, 6-4 (victoria normal)
        - 7-5 (victoria con ventaja)
        - 7-6 (victoria en tiebreak)
        """
        # Ordenar para facilitar validación
        mayor = max(games_a, games_b)
        menor = min(games_a, games_b)
        
        # Victoria 6-X (X <= 4)
        if mayor == 6 and menor <= 4:
            return True
        
        # Victoria 7-5
        if mayor == 7 and menor == 5:
            return True
        
        # Victoria 7-6 (tiebreak)
        if mayor == 7 and menor == 6:
            return True
        
        return False
    
    @staticmethod
    def _determinar_ganador(
        resultado: Dict,
        pareja1_id: int,
        pareja2_id: int
    ) -> int:
        """Determina qué pareja ganó el partido"""
        sets = resultado['sets']
        
        sets_equipo_a = sum(1 for s in sets if s.get('ganador') == 'equipoA')
        sets_equipo_b = sum(1 for s in sets if s.get('ganador') == 'equipoB')
        
        if sets_equipo_a > sets_equipo_b:
            return pareja1_id
        else:
            return pareja2_id
    
    @staticmethod
    def obtener_clasificados_zona(
        db: Session,
        zona_id: int,
        num_clasificados: int = 2
    ) -> List[Dict]:
        """
        Obtiene las parejas clasificadas de una zona
        
        Args:
            db: Sesión de base de datos
            zona_id: ID de la zona
            num_clasificados: Número de parejas que clasifican (default: 2)
            
        Returns:
            Lista de parejas clasificadas ordenadas por posición
        """
        from ..services.torneo_zona_service import TorneoZonaService
        
        # Obtener tabla de posiciones
        tabla = TorneoZonaService.obtener_tabla_posiciones(db, zona_id)
        
        # Tomar los primeros N clasificados
        clasificados = tabla['tabla'][:num_clasificados]
        
        return clasificados
    
    @staticmethod
    def verificar_zona_completa(db: Session, zona_id: int) -> bool:
        """
        Verifica si todos los partidos de una zona están finalizados
        
        Returns:
            True si todos los partidos están finalizados
        """
        # Contar partidos pendientes (no confirmados)
        partidos_pendientes = db.query(Partido).filter(
            Partido.zona_id == zona_id,
            Partido.estado != 'confirmado'
        ).count()
        
        return partidos_pendientes == 0
    
    @staticmethod
    def obtener_estadisticas_partido(
        db: Session,
        partido_id: int
    ) -> Dict:
        """
        Obtiene estadísticas detalladas de un partido
        
        Returns:
            Dict con estadísticas del partido
        """
        partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
        if not partido:
            raise ValueError("Partido no encontrado")
        
        if not partido.resultado_padel:
            return {
                "partido_id": partido_id,
                "estado": partido.estado,
                "tiene_resultado": False
            }
        
        resultado = partido.resultado_padel
        sets = resultado.get('sets', [])
        
        # Calcular estadísticas
        total_games_a = sum(s.get('gamesEquipoA', 0) for s in sets)
        total_games_b = sum(s.get('gamesEquipoB', 0) for s in sets)
        
        sets_a = sum(1 for s in sets if s.get('ganador') == 'equipoA')
        sets_b = sum(1 for s in sets if s.get('ganador') == 'equipoB')
        
        return {
            "partido_id": partido_id,
            "estado": partido.estado,
            "tiene_resultado": True,
            "pareja1_id": partido.pareja1_id,
            "pareja2_id": partido.pareja2_id,
            "ganador_pareja_id": partido.ganador_pareja_id,
            "sets": {
                "pareja1": sets_a,
                "pareja2": sets_b
            },
            "games": {
                "pareja1": total_games_a,
                "pareja2": total_games_b
            },
            "detalle_sets": sets
        }
    
    @staticmethod
    def corregir_resultado(
        db: Session,
        partido_id: int,
        nuevo_resultado: Dict,
        user_id: int
    ) -> Partido:
        """
        Corrige el resultado de un partido ya finalizado
        
        Solo organizadores pueden corregir resultados
        """
        partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
        if not partido:
            raise ValueError("Partido no encontrado")
        
        # Verificar permisos (debe ser organizador del torneo)
        from ..services.torneo_zona_service import TorneoZonaService
        if not TorneoZonaService._es_organizador(db, partido.id_torneo, user_id):
            raise ValueError("No tienes permisos para corregir este resultado")
        
        # Validar nuevo resultado
        TorneoResultadoService._validar_resultado(nuevo_resultado)
        
        # Determinar nuevo ganador
        ganador_pareja_id = TorneoResultadoService._determinar_ganador(
            nuevo_resultado, partido.pareja1_id, partido.pareja2_id
        )
        
        # Actualizar
        partido.resultado_padel = nuevo_resultado
        partido.ganador_pareja_id = ganador_pareja_id
        
        db.commit()
        db.refresh(partido)
        
        return partido

    @staticmethod
    def _aplicar_elo_torneo(
        db: Session,
        partido: Partido,
        resultado_data: Dict,
        ganador_pareja_id: int
    ) -> Dict:
        """
        Aplica el cálculo de ELO para partidos de torneo y actualiza estadísticas
        
        Args:
            db: Sesión de base de datos
            partido: Partido finalizado
            resultado_data: Datos del resultado
            ganador_pareja_id: ID de la pareja ganadora
            
        Returns:
            Dict con cambios de ELO por jugador
        """
        from ..models.driveplus_models import Usuario, HistorialRating
        from ..services.elo_service import EloService
        from sqlalchemy import text
        
        # Obtener parejas usando SQL directo para evitar problemas con Enum
        result1 = db.execute(text(
            "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :id"
        ), {'id': partido.pareja1_id}).fetchone()
        
        result2 = db.execute(text(
            "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :id"
        ), {'id': partido.pareja2_id}).fetchone()
        
        if not result1 or not result2:
            raise ValueError("No se encontraron las parejas del partido")
        
        # Crear objetos simples con los datos de las parejas
        class ParejaData:
            def __init__(self, row):
                self.id = row[0]
                self.jugador1_id = row[1]
                self.jugador2_id = row[2]
        
        pareja1 = ParejaData(result1)
        pareja2 = ParejaData(result2)
        
        # Obtener los 4 jugadores
        jugadores_ids = [
            pareja1.jugador1_id, pareja1.jugador2_id,
            pareja2.jugador1_id, pareja2.jugador2_id
        ]
        
        jugadores = {}
        for jid in jugadores_ids:
            usuario = db.query(Usuario).filter(Usuario.id_usuario == jid).first()
            if usuario:
                jugadores[jid] = usuario
        
        if len(jugadores) != 4:
            raise ValueError("No se encontraron todos los jugadores")
        
        # Preparar datos para el servicio ELO
        team_a_players = [
            {
                'id': pareja1.jugador1_id,
                'id_usuario': pareja1.jugador1_id,
                'rating': jugadores[pareja1.jugador1_id].rating or 1200,
                'partidos': jugadores[pareja1.jugador1_id].partidos_jugados or 0
            },
            {
                'id': pareja1.jugador2_id,
                'id_usuario': pareja1.jugador2_id,
                'rating': jugadores[pareja1.jugador2_id].rating or 1200,
                'partidos': jugadores[pareja1.jugador2_id].partidos_jugados or 0
            }
        ]
        
        team_b_players = [
            {
                'id': pareja2.jugador1_id,
                'id_usuario': pareja2.jugador1_id,
                'rating': jugadores[pareja2.jugador1_id].rating or 1200,
                'partidos': jugadores[pareja2.jugador1_id].partidos_jugados or 0
            },
            {
                'id': pareja2.jugador2_id,
                'id_usuario': pareja2.jugador2_id,
                'rating': jugadores[pareja2.jugador2_id].rating or 1200,
                'partidos': jugadores[pareja2.jugador2_id].partidos_jugados or 0
            }
        ]
        
        # Extraer datos del resultado
        sets = resultado_data.get('sets', [])
        sets_a = sum(1 for s in sets if s.get('ganador') == 'equipoA')
        sets_b = sum(1 for s in sets if s.get('ganador') == 'equipoB')
        games_a = sum(s.get('gamesEquipoA', 0) for s in sets)
        games_b = sum(s.get('gamesEquipoB', 0) for s in sets)
        
        # MAPEAR CORRECTAMENTE PAREJAS PARA ELO (FIX CRÍTICO - BUG ELO INVERTIDO)
        # El frontend (ModalCargarResultado) SIEMPRE usa: pareja1 = equipoA, pareja2 = equipoB
        # El resultado enviado NO incluye 'jugadores', solo 'sets' con gamesEquipoA/gamesEquipoB
        # DEFAULT: pareja1_es_equipoA = True (convención del frontend)
        # Solo invertir si hay jugadores en el resultado Y pareja1 NO está en equipoA
        
        jugadores_resultado = resultado_data.get('jugadores', {})
        jugadores_equipoA = jugadores_resultado.get('equipoA', [])
        
        pareja1_es_equipoA = True  # DEFAULT: frontend usa pareja1=equipoA, pareja2=equipoB
        if jugadores_equipoA:
            ids_pareja1 = {pareja1.jugador1_id, pareja1.jugador2_id}
            ids_equipoA = {j.get('id') for j in jugadores_equipoA if j.get('id')}
            pareja1_es_equipoA = bool(ids_pareja1.intersection(ids_equipoA))
        
        # Asignar sets correctamente según la correspondencia
        if pareja1_es_equipoA:
            # pareja1 = equipoA, pareja2 = equipoB
            sets_pareja1 = sets_a  # sets de equipoA
            sets_pareja2 = sets_b  # sets de equipoB
            games_pareja1 = games_a
            games_pareja2 = games_b
        else:
            # pareja1 = equipoB, pareja2 = equipoA (INVERTIDO - caso raro con jugadores en resultado)
            sets_pareja1 = sets_b  # sets de equipoB
            sets_pareja2 = sets_a  # sets de equipoA
            games_pareja1 = games_b
            games_pareja2 = games_a
        
        # Convertir sets al formato esperado por EloService
        # games_a = team_a (pareja1), games_b = team_b (pareja2)
        if pareja1_es_equipoA:
            sets_detail = [
                {'games_a': s.get('gamesEquipoA', 0), 'games_b': s.get('gamesEquipoB', 0)}
                for s in sets
            ]
        else:
            sets_detail = [
                {'games_a': s.get('gamesEquipoB', 0), 'games_b': s.get('gamesEquipoA', 0)}
                for s in sets
            ]
        
        # Calcular ELO (CORREGIDO)
        elo_service = EloService()
        cambios_elo_result = elo_service.calculate_match_ratings(
            team_a_players=team_a_players,
            team_b_players=team_b_players,
            sets_a=sets_pareja1,  # Ahora corresponde correctamente a pareja1
            sets_b=sets_pareja2,  # Ahora corresponde correctamente a pareja2
            games_a=games_pareja1,
            games_b=games_pareja2,
            sets_detail=sets_detail,
            match_type='torneo',
            match_date=partido.fecha or datetime.now()
        )
        
        # Aplicar cambios de ELO y actualizar estadísticas
        resultado_elo = {}
        
        # Equipo A (pareja1)
        for i, player_data in enumerate(cambios_elo_result['team_a']['players']):
            jid = [pareja1.jugador1_id, pareja1.jugador2_id][i]
            usuario = jugadores[jid]
            
            rating_antes = usuario.rating or 1200
            nuevo_rating = int(round(player_data['new_rating']))
            cambio = int(round(player_data['rating_change']))
            
            # Actualizar usuario
            usuario.rating = nuevo_rating
            usuario.partidos_jugados = (usuario.partidos_jugados or 0) + 1
            
            # Actualizar categoría según el nuevo rating
            actualizar_categoria_usuario(db, usuario)
            
            # Crear historial de rating
            historial = HistorialRating(
                id_usuario=jid,
                id_partido=partido.id_partido,
                rating_antes=rating_antes,
                delta=cambio,
                rating_despues=nuevo_rating
            )
            db.add(historial)
            
            resultado_elo[jid] = {
                'anterior': rating_antes,
                'nuevo': nuevo_rating,
                'cambio': cambio
            }
        
        # Equipo B (pareja2)
        for i, player_data in enumerate(cambios_elo_result['team_b']['players']):
            jid = [pareja2.jugador1_id, pareja2.jugador2_id][i]
            usuario = jugadores[jid]
            
            rating_antes = usuario.rating or 1200
            nuevo_rating = int(round(player_data['new_rating']))
            cambio = int(round(player_data['rating_change']))
            
            # Actualizar usuario
            usuario.rating = nuevo_rating
            usuario.partidos_jugados = (usuario.partidos_jugados or 0) + 1
            
            # Actualizar categoría según el nuevo rating
            actualizar_categoria_usuario(db, usuario)
            
            # Crear historial de rating
            historial = HistorialRating(
                id_usuario=jid,
                id_partido=partido.id_partido,
                rating_antes=rating_antes,
                delta=cambio,
                rating_despues=nuevo_rating
            )
            db.add(historial)
            
            resultado_elo[jid] = {
                'anterior': rating_antes,
                'nuevo': nuevo_rating,
                'cambio': cambio
            }
        
        # Flush para asegurar que los cambios se persistan
        db.flush()
        
        logger.info(f"ELO aplicado para partido de torneo {partido.id_partido}: {resultado_elo}")
        
        return resultado_elo
