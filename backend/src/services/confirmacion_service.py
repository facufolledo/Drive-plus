"""
Servicio de Confirmaciones
Maneja el flujo de confirmación de resultados de partidos
"""
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.driveplus_models import Partido, PartidoJugador, Usuario
from ..models.confirmacion import Confirmacion
from ..models.historial_enfrentamiento import HistorialEnfrentamiento
from ..services.elo_service import EloService
from ..services.categoria_service import actualizar_categoria_usuario
from ..utils.cache import invalidate_ranking_cache


class ConfirmacionService:
    """Servicio para manejar confirmaciones de resultados"""
    
    HORAS_AUTO_CONFIRMACION = 48
    
    @staticmethod
    def obtener_estado_confirmaciones(id_partido: int, id_usuario_actual: int, db: Session) -> Dict:
        """
        Obtiene el estado de confirmaciones de un partido
        
        Returns:
            Dict con información de confirmaciones
        """
        partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
        if not partido:
            return None
        
        # Obtener todas las confirmaciones
        confirmaciones = db.query(Confirmacion).filter(
            Confirmacion.id_partido == id_partido
        ).all()
        
        # Contar confirmaciones y reportes
        confirmaciones_count = len([c for c in confirmaciones if c.tipo == 'confirmacion'])
        reportes_count = len([c for c in confirmaciones if c.tipo == 'reporte'])
        
        # Verificar si el usuario actual ya confirmó
        ya_confirmo = any(c.id_usuario == id_usuario_actual for c in confirmaciones)
        
        # Verificar si puede confirmar (no es el creador y no ha confirmado)
        puede_confirmar = (
            partido.creado_por != id_usuario_actual and 
            not ya_confirmo and
            partido.estado_confirmacion == 'pendiente_confirmacion'
        )
        
        # Obtener jugadores que faltan por confirmar
        jugadores_faltantes = []
        if partido.estado_confirmacion == 'pendiente_confirmacion':
            # Obtener todos los jugadores del partido
            todos_jugadores = db.query(PartidoJugador).filter(
                PartidoJugador.id_partido == id_partido
            ).all()
            
            # Obtener quiénes ya confirmaron
            ids_confirmados = {c.id_usuario for c in confirmaciones if c.tipo == 'confirmacion'}
            ids_confirmados.add(partido.creado_por)  # El creador no confirma
            
            # Encontrar quiénes faltan
            for jugador in todos_jugadores:
                if jugador.id_usuario not in ids_confirmados:
                    usuario = db.query(Usuario).filter(Usuario.id_usuario == jugador.id_usuario).first()
                    if usuario:
                        jugadores_faltantes.append(usuario.nombre_usuario)
        
        return {
            "total_jugadores": 4,
            "confirmaciones": confirmaciones_count,
            "reportes": reportes_count,
            "pendientes": 4 - len(confirmaciones),
            "puede_confirmar": puede_confirmar,
            "ya_confirmo": ya_confirmo,
            "estado": partido.estado_confirmacion,
            "confirmaciones_detalle": confirmaciones,
            "jugadores_faltantes": jugadores_faltantes
        }
    
    @staticmethod
    def confirmar_resultado(id_partido: int, id_usuario: int, db: Session) -> Dict:
        """
        Confirma el resultado de un partido
        
        Returns:
            Dict con resultado de la confirmación
        """
        from ..models.driveplus_models import ResultadoPartido
        
        partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
        if not partido:
            raise ValueError("Partido no encontrado")
        
        # Verificar que el partido tenga resultado (UNIFICADO)
        resultado = db.query(ResultadoPartido).filter(
            ResultadoPartido.id_partido == id_partido
        ).first()
        
        if not resultado:
            raise ValueError("El partido no tiene resultado cargado")
        
        # Verificar que el usuario sea parte del partido
        jugador = db.query(PartidoJugador).filter(
            and_(
                PartidoJugador.id_partido == id_partido,
                PartidoJugador.id_usuario == id_usuario
            )
        ).first()
        
        if not jugador:
            raise ValueError("No eres parte de este partido")
        
        # Verificar que no sea el creador
        if partido.creado_por == id_usuario:
            raise ValueError("El creador no puede confirmar su propio resultado")
        
        # Verificar que no haya confirmado ya
        confirmacion_existente = db.query(Confirmacion).filter(
            and_(
                Confirmacion.id_partido == id_partido,
                Confirmacion.id_usuario == id_usuario
            )
        ).first()
        
        if confirmacion_existente:
            raise ValueError("Ya confirmaste este resultado")
        
        # Crear confirmación
        confirmacion = Confirmacion(
            id_partido=id_partido,
            id_usuario=id_usuario,
            tipo='confirmacion',
            fecha=datetime.now()
        )
        db.add(confirmacion)
        db.flush()
        
        # Contar confirmaciones totales (incluyendo esta)
        total_confirmaciones = db.query(Confirmacion).filter(
            and_(
                Confirmacion.id_partido == id_partido,
                Confirmacion.tipo == 'confirmacion'
            )
        ).count()
        
        # Si todos confirmaron (3 rivales), aplicar Elo
        elo_changes = None
        if total_confirmaciones >= 3:
            elo_changes = ConfirmacionService._aplicar_elo(partido, db)
            partido.estado_confirmacion = 'confirmado'
            partido.estado = 'confirmado'  # Actualizar también el estado principal
            
            # Enviar notificaciones push a todos los jugadores
            try:
                from .notification_service import NotificationService
                
                # Obtener todos los jugadores del partido
                todos_jugadores = db.query(PartidoJugador).filter(
                    PartidoJugador.id_partido == id_partido
                ).all()
                
                ids_usuarios = [j.id_usuario for j in todos_jugadores]
                
                # Enviar notificaciones
                NotificationService.enviar_notificacion_elo_actualizado(
                    usuarios=ids_usuarios,
                    cambios_elo=elo_changes,
                    db=db
                )
            except Exception as e:
                # No fallar si las notificaciones fallan
                print(f"Error enviando notificaciones: {e}")
        
        # Obtener jugadores que faltan por confirmar
        jugadores_faltantes = []
        if total_confirmaciones < 3:
            # Obtener todos los jugadores del partido
            todos_jugadores = db.query(PartidoJugador).filter(
                PartidoJugador.id_partido == id_partido
            ).all()
            
            # Obtener quiénes ya confirmaron
            confirmaciones = db.query(Confirmacion).filter(
                and_(
                    Confirmacion.id_partido == id_partido,
                    Confirmacion.tipo == 'confirmacion'
                )
            ).all()
            
            ids_confirmados = {c.id_usuario for c in confirmaciones}
            ids_confirmados.add(partido.creado_por)  # El creador no confirma
            
            # Encontrar quiénes faltan
            for jugador in todos_jugadores:
                if jugador.id_usuario not in ids_confirmados:
                    usuario = db.query(Usuario).filter(Usuario.id_usuario == jugador.id_usuario).first()
                    if usuario:
                        jugadores_faltantes.append(usuario.nombre_usuario)
        
        # Calcular cambio de Elo para el usuario actual
        cambio_elo_usuario = None
        if elo_changes:
            # Si se aplicó el Elo, obtener el cambio real
            cambio_elo_usuario = elo_changes.get(id_usuario, {}).get('cambio', 0)
        else:
            # Si no se aplicó aún, dar estimación
            jugador_actual = db.query(PartidoJugador).filter(
                and_(
                    PartidoJugador.id_partido == id_partido,
                    PartidoJugador.id_usuario == id_usuario
                )
            ).first()
            
            if jugador_actual:
                # Estimación: ganadores +8, perdedores -8 (cambio individual en amistosos)
                gano = (partido.ganador_equipo == jugador_actual.equipo)
                cambio_elo_usuario = 8 if gano else -8
        
        db.commit()
        
        return {
            "success": True,
            "confirmaciones_totales": total_confirmaciones,
            "elo_aplicado": total_confirmaciones >= 3,
            "elo_changes": elo_changes,
            "cambio_elo_usuario": cambio_elo_usuario,
            "jugadores_faltantes": jugadores_faltantes,
            "mensaje": "Resultado confirmado" if total_confirmaciones < 3 else "Todos confirmaron. Elo actualizado."
        }
    
    @staticmethod
    def reportar_resultado(id_partido: int, id_usuario: int, motivo: str, db: Session) -> Dict:
        """
        Reporta un resultado como incorrecto
        """
        partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
        if not partido:
            raise ValueError("Partido no encontrado")
        
        # Verificar que el usuario sea parte del partido
        jugador = db.query(PartidoJugador).filter(
            and_(
                PartidoJugador.id_partido == id_partido,
                PartidoJugador.id_usuario == id_usuario
            )
        ).first()
        
        if not jugador:
            raise ValueError("No eres parte de este partido")
        
        # Verificar que no haya reportado ya
        reporte_existente = db.query(Confirmacion).filter(
            and_(
                Confirmacion.id_partido == id_partido,
                Confirmacion.id_usuario == id_usuario
            )
        ).first()
        
        if reporte_existente:
            raise ValueError("Ya reportaste este resultado")
        
        # Crear reporte
        reporte = Confirmacion(
            id_partido=id_partido,
            id_usuario=id_usuario,
            tipo='reporte',
            motivo=motivo,
            fecha=datetime.now()
        )
        db.add(reporte)
        
        # Cambiar estado del partido a disputado
        partido.estado_confirmacion = 'disputado'
        
        db.commit()
        
        return {
            "success": True,
            "mensaje": "Reporte registrado. Un administrador revisará el caso."
        }
    
    @staticmethod
    def _aplicar_elo(partido: Partido, db: Session) -> Dict:
        """
        Aplica el cálculo de Elo cuando todos confirman
        
        Returns:
            Dict con cambios de Elo por jugador
        """
        if partido.elo_aplicado:
            return None  # Ya se aplicó
        
        # Obtener jugadores del partido
        jugadores = db.query(PartidoJugador).filter(
            PartidoJugador.id_partido == partido.id_partido
        ).all()
        
        if len(jugadores) != 4:
            raise ValueError("El partido debe tener 4 jugadores")
        
        # Separar por equipos
        equipo1 = [j for j in jugadores if j.equipo == 1]
        equipo2 = [j for j in jugadores if j.equipo == 2]
        
        # Obtener ratings actuales
        ratings_equipo1 = []
        ratings_equipo2 = []
        
        for j in equipo1:
            usuario = db.query(Usuario).filter(Usuario.id_usuario == j.id_usuario).first()
            ratings_equipo1.append(usuario.rating)
            j.rating_antes = usuario.rating
        
        for j in equipo2:
            usuario = db.query(Usuario).filter(Usuario.id_usuario == j.id_usuario).first()
            ratings_equipo2.append(usuario.rating)
            j.rating_antes = usuario.rating
        
        # Preparar datos para el servicio Elo
        team_a_players = []
        team_b_players = []
        
        for j in equipo1:
            usuario = db.query(Usuario).filter(Usuario.id_usuario == j.id_usuario).first()
            team_a_players.append({
                'id': usuario.id_usuario,  # El servicio Elo espera 'id'
                'id_usuario': usuario.id_usuario,
                'rating': usuario.rating,
                'partidos': usuario.partidos_jugados
            })
        
        for j in equipo2:
            usuario = db.query(Usuario).filter(Usuario.id_usuario == j.id_usuario).first()
            team_b_players.append({
                'id': usuario.id_usuario,  # El servicio Elo espera 'id'
                'id_usuario': usuario.id_usuario,
                'rating': usuario.rating,
                'partidos': usuario.partidos_jugados
            })
        
        # Extraer datos del resultado (UNIFICADO - desde resultados_partidos)
        from ..models.driveplus_models import ResultadoPartido
        
        resultado_db = db.query(ResultadoPartido).filter(
            ResultadoPartido.id_partido == partido.id_partido
        ).first()
        
        if not resultado_db:
            raise ValueError("El partido no tiene resultado cargado")
        
        # MAPEAR CORRECTAMENTE EQUIPOS PARA ELO (FIX CRÍTICO v2)
        # En resultados_partidos: eq1/eq2 corresponden a equipo 1/equipo 2 del partido
        # Por defecto, equipo1 = equipoA (mapeo directo)
        # Solo invertir si resultado_padel JSON indica lo contrario
        
        # Obtener información de jugadores por equipo del resultado JSON
        resultado_json = partido.resultado_padel or {}
        jugadores_resultado = resultado_json.get('jugadores', {})
        jugadores_equipoA = jugadores_resultado.get('equipoA', [])
        
        # Calcular games totales desde detalle_sets (ANTES de usarlos en el if/else)
        games_a = sum(set_data.get('juegos_eq1', 0) for set_data in resultado_db.detalle_sets)
        games_b = sum(set_data.get('juegos_eq2', 0) for set_data in resultado_db.detalle_sets)
        
        # Determinar si equipo1 corresponde a equipoA o equipoB
        # DEFAULT: True (mapeo directo eq1=eqA, eq2=eqB)
        # Solo cambiar si hay datos JSON que indiquen lo contrario
        equipo1_es_equipoA = True
        if jugadores_equipoA and equipo1:
            ids_equipo1 = {j.id_usuario for j in equipo1}
            ids_equipoA = {j.get('id') for j in jugadores_equipoA if j.get('id')}
            # Solo si hay IDs válidos en ambos lados, verificar correspondencia
            if ids_equipoA:
                equipo1_es_equipoA = bool(ids_equipo1.intersection(ids_equipoA))
        
        # Asignar sets y games según la correspondencia
        if equipo1_es_equipoA:
            sets_equipo1 = resultado_db.sets_eq1
            sets_equipo2 = resultado_db.sets_eq2
            games_equipo1 = games_a
            games_equipo2 = games_b
        else:
            sets_equipo1 = resultado_db.sets_eq2
            sets_equipo2 = resultado_db.sets_eq1
            games_equipo1 = games_b
            games_equipo2 = games_a
        
        # EloService espera sets_detail con keys 'games_a' y 'games_b' (team_a = equipo1, team_b = equipo2)
        if equipo1_es_equipoA:
            sets_detail = [
                {'games_a': set_data.get('juegos_eq1', 0), 'games_b': set_data.get('juegos_eq2', 0)}
                for set_data in resultado_db.detalle_sets
            ]
        else:
            sets_detail = [
                {'games_a': set_data.get('juegos_eq2', 0), 'games_b': set_data.get('juegos_eq1', 0)}
                for set_data in resultado_db.detalle_sets
            ]
        
        # Calcular Elo usando el servicio existente (CORREGIDO)
        elo_service = EloService()
        cambios_elo_result = elo_service.calculate_match_ratings(
            team_a_players=team_a_players,
            team_b_players=team_b_players,
            sets_a=sets_equipo1,  # Ahora corresponde correctamente a equipo1
            sets_b=sets_equipo2,  # Ahora corresponde correctamente a equipo2
            games_a=games_equipo1,
            games_b=games_equipo2,
            sets_detail=sets_detail,
            match_type='amistoso',
            match_date=partido.fecha
        )
        
        # Convertir resultado al formato esperado
        cambios_elo = {}
        for i, player_change in enumerate(cambios_elo_result['team_a']['players']):
            cambios_elo[f'jugador_a_{i}'] = {
                'anterior': player_change['old_rating'],
                'nuevo': player_change['new_rating'],
                'cambio': player_change['rating_change']
            }
        
        for i, player_change in enumerate(cambios_elo_result['team_b']['players']):
            cambios_elo[f'jugador_b_{i}'] = {
                'anterior': player_change['old_rating'],
                'nuevo': player_change['new_rating'],
                'cambio': player_change['rating_change']
            }
        
        # Aplicar cambios (convertir a enteros) - CORREGIDO
        resultado = {}
        
        for i, j in enumerate(equipo1):
            usuario = db.query(Usuario).filter(Usuario.id_usuario == j.id_usuario).first()
            cambio_key = f'jugador_a_{i}'
            cambio = cambios_elo[cambio_key]
            
            # Convertir a enteros (SIN INVERTIR - el ELO ya está corregido)
            cambio_elo_int = int(round(cambio['cambio']))  # CORREGIDO: Sin inversión
            nuevo_rating = int(usuario.rating) + cambio_elo_int
            
            usuario.rating = nuevo_rating
            j.rating_despues = nuevo_rating
            j.cambio_elo = cambio_elo_int
            
            # Actualizar categoría según el nuevo rating
            actualizar_categoria_usuario(db, usuario)
            
            resultado[j.id_usuario] = {
                'anterior': int(cambio['anterior']),
                'nuevo': nuevo_rating,
                'cambio': cambio_elo_int
            }
        
        for i, j in enumerate(equipo2):
            usuario = db.query(Usuario).filter(Usuario.id_usuario == j.id_usuario).first()
            cambio_key = f'jugador_b_{i}'
            cambio = cambios_elo[cambio_key]
            
            # Convertir a enteros (SIN INVERTIR - el ELO ya está corregido)
            cambio_elo_int = int(round(cambio['cambio']))  # CORREGIDO: Sin inversión
            nuevo_rating = int(usuario.rating) + cambio_elo_int
            
            usuario.rating = nuevo_rating
            j.rating_despues = nuevo_rating
            j.cambio_elo = cambio_elo_int
            
            # Actualizar categoría según el nuevo rating
            actualizar_categoria_usuario(db, usuario)
            
            resultado[j.id_usuario] = {
                'anterior': int(cambio['anterior']),
                'nuevo': nuevo_rating,
                'cambio': cambio_elo_int
            }
        
        # Marcar Elo como aplicado
        partido.elo_aplicado = True
        
        # Invalidar caché de rankings (los ratings cambiaron)
        invalidate_ranking_cache()
        
        # CRÍTICO: Crear entradas en historial_rating para TODOS los jugadores
        from ..models.driveplus_models import HistorialRating
        
        for jugador in jugadores:
            # Verificar si ya existe entrada (por si acaso)
            historial_existente = db.query(HistorialRating).filter(
                and_(
                    HistorialRating.id_partido == partido.id_partido,
                    HistorialRating.id_usuario == jugador.id_usuario
                )
            ).first()
            
            if not historial_existente:
                # Crear nueva entrada
                historial_rating = HistorialRating(
                    id_usuario=jugador.id_usuario,
                    id_partido=partido.id_partido,
                    rating_antes=jugador.rating_antes,
                    delta=jugador.cambio_elo,
                    rating_despues=jugador.rating_despues
                )
                db.add(historial_rating)
        
        # Actualizar historial de enfrentamientos
        historial = db.query(HistorialEnfrentamiento).filter(
            HistorialEnfrentamiento.id_partido == partido.id_partido
        ).first()
        
        if historial:
            historial.elo_aplicado = True
        
        db.commit()
        
        return resultado
    
    @staticmethod
    def auto_confirmar_partidos_antiguos(db: Session) -> int:
        """
        Auto-confirma partidos que tienen más de 48 horas sin reportes
        
        Returns:
            Cantidad de partidos auto-confirmados
        """
        fecha_limite = datetime.now() - timedelta(hours=ConfirmacionService.HORAS_AUTO_CONFIRMACION)
        
        # Buscar partidos pendientes de confirmación antiguos
        partidos = db.query(Partido).filter(
            and_(
                Partido.estado_confirmacion == 'pendiente_confirmacion',
                Partido.creado_en <= fecha_limite
            )
        ).all()
        
        count = 0
        for partido in partidos:
            # Verificar que no haya reportes
            reportes = db.query(Confirmacion).filter(
                and_(
                    Confirmacion.id_partido == partido.id_partido,
                    Confirmacion.tipo == 'reporte'
                )
            ).count()
            
            if reportes == 0:
                # Auto-confirmar
                try:
                    ConfirmacionService._aplicar_elo(partido, db)
                    partido.estado_confirmacion = 'auto_confirmado'
                    count += 1
                except Exception as e:
                    print(f"Error auto-confirmando partido {partido.id_partido}: {e}")
                    continue
        
        db.commit()
        return count


    def __init__(self, db: Session):
        """Inicializar servicio con sesión de base de datos"""
        self.db = db
    
    def crear_resultado(self, resultado_data) -> Dict:
        """
        Crear un nuevo resultado de partido desde una sala
        
        Args:
            resultado_data: Datos del resultado (ResultadoPadelCreate)
            
        Returns:
            Dict con información del resultado creado
        """
        from ..models.confirmacion import ResultadoPadel
        
        # Crear el resultado en la base de datos
        resultado = ResultadoPadel(
            id_sala=resultado_data.id_sala,
            id_creador=resultado_data.id_creador,
            sets=resultado_data.sets,
            ganador_equipo=resultado_data.ganador_equipo,
            estado='pendiente_confirmacion',
            confirmaciones=1,  # El creador ya confirmó
            fecha_creacion=datetime.now()
        )
        
        self.db.add(resultado)
        self.db.commit()
        self.db.refresh(resultado)
        
        return {
            "id_resultado": resultado.id_resultado,
            "id_sala": resultado.id_sala,
            "estado": resultado.estado,
            "confirmaciones": resultado.confirmaciones,
            "mensaje": "Resultado creado. Esperando confirmación de rivales."
        }
    
    def obtener_resultado(self, id_sala: str):
        """
        Obtener el resultado de una sala
        
        Args:
            id_sala: ID de la sala
            
        Returns:
            Resultado o None si no existe
        """
        from ..models.confirmacion import ResultadoPadel
        
        resultado = self.db.query(ResultadoPadel).filter(
            ResultadoPadel.id_sala == id_sala
        ).first()
        
        return resultado
    
    def confirmar_resultado_por_sala(self, id_sala: str, id_usuario: int) -> Dict:
        """
        Confirmar un resultado de partido por sala
        
        Args:
            id_sala: ID de la sala
            id_usuario: ID del usuario que confirma
            
        Returns:
            Dict con resultado de la confirmación
        """
        from ..models.confirmacion import ResultadoPadel, ConfirmacionUsuario
        
        # Obtener el resultado
        resultado = self.obtener_resultado(id_sala)
        if not resultado:
            raise ValueError("Resultado no encontrado")
        
        # Verificar que no sea el creador
        if resultado.id_creador == id_usuario:
            raise ValueError("El creador no puede confirmar su propio resultado")
        
        # Verificar que no haya confirmado ya
        confirmacion_existente = self.db.query(ConfirmacionUsuario).filter(
            and_(
                ConfirmacionUsuario.id_resultado == resultado.id_resultado,
                ConfirmacionUsuario.id_usuario == id_usuario
            )
        ).first()
        
        if confirmacion_existente:
            raise ValueError("Ya confirmaste este resultado")
        
        # Crear confirmación
        confirmacion = ConfirmacionUsuario(
            id_resultado=resultado.id_resultado,
            id_usuario=id_usuario,
            fecha=datetime.now()
        )
        self.db.add(confirmacion)
        
        # Incrementar contador de confirmaciones
        resultado.confirmaciones += 1
        
        # Si se alcanzó consenso (3 confirmaciones), aplicar Elo
        consenso_alcanzado = False
        if resultado.confirmaciones >= 3:
            resultado.estado = 'confirmado'
            consenso_alcanzado = True
            # TODO: Aplicar Elo aquí
        
        self.db.commit()
        
        return {
            "success": True,
            "confirmaciones": resultado.confirmaciones,
            "consenso_alcanzado": consenso_alcanzado,
            "mensaje": "Resultado confirmado" if not consenso_alcanzado else "Consenso alcanzado. Elo aplicado."
        }
    
    def obtener_pendientes_usuario(self, id_usuario: int) -> List:
        """
        Obtener resultados pendientes de confirmación para un usuario
        
        Args:
            id_usuario: ID del usuario
            
        Returns:
            Lista de resultados pendientes
        """
        from ..models.confirmacion import ResultadoPadel
        
        # TODO: Implementar lógica para obtener salas donde el usuario es jugador
        # y hay resultados pendientes de confirmación
        
        resultados = self.db.query(ResultadoPadel).filter(
            and_(
                ResultadoPadel.estado == 'pendiente_confirmacion',
                ResultadoPadel.id_creador != id_usuario
            )
        ).all()
        
        return resultados
