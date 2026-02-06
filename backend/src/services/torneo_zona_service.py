"""
Servicio para gestión de zonas en torneos
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import random
from ..models.torneo_models import Torneo, TorneoZona, TorneoPareja, TorneoZonaPareja
from ..models.driveplus_models import Usuario


class TorneoZonaService:
    """Servicio para gestión de zonas en torneos"""
    
    @staticmethod
    def generar_zonas_automaticas(
        db: Session,
        torneo_id: int,
        user_id: int,
        num_zonas: Optional[int] = None,
        balancear_por_rating: bool = True,
        categoria_id: Optional[int] = None
    ) -> List[TorneoZona]:
        """
        Genera zonas automáticamente y distribuye parejas
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            user_id: ID del usuario que ejecuta (debe ser organizador)
            num_zonas: Número de zonas (si no se especifica, se calcula automáticamente)
            balancear_por_rating: Si True, distribuye parejas por rating para equilibrar zonas
            categoria_id: ID de la categoría (opcional, si se pasa solo genera para esa categoría)
            
        Returns:
            Lista de zonas creadas
        """
        from ..models.torneo_models import TorneoCategoria
        
        # Verificar que el torneo existe y el usuario es organizador
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            raise ValueError("Torneo no encontrado")
        
        if not TorneoZonaService._es_organizador(db, torneo_id, user_id):
            raise ValueError("No tienes permisos para generar zonas en este torneo")
        
        # Verificar categoría si se especificó
        categoria = None
        if categoria_id:
            categoria = db.query(TorneoCategoria).filter(
                TorneoCategoria.id == categoria_id,
                TorneoCategoria.torneo_id == torneo_id
            ).first()
            if not categoria:
                raise ValueError("Categoría no encontrada")
        
        # Obtener parejas inscritas o confirmadas (excluir bajas)
        query = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == torneo_id,
            TorneoPareja.estado.in_(['inscripta', 'confirmada'])
        )
        
        # Filtrar por categoría si se especificó
        if categoria_id:
            query = query.filter(TorneoPareja.categoria_id == categoria_id)
        
        parejas = query.all()
        
        if len(parejas) < 4:
            raise ValueError(f"Se necesitan al menos 4 parejas para generar zonas (actualmente hay {len(parejas)})")
        
        # Calcular número óptimo de zonas si no se especificó
        if num_zonas is None:
            num_zonas = TorneoZonaService._calcular_num_zonas_optimo(len(parejas))
        
        # Validar número de zonas
        if num_zonas < 2:
            raise ValueError("Debe haber al menos 2 zonas")
        
        parejas_por_zona_min = len(parejas) // num_zonas
        parejas_por_zona_max = (len(parejas) + num_zonas - 1) // num_zonas
        
        if parejas_por_zona_min < 2:
            raise ValueError(f"Con {len(parejas)} parejas no se pueden crear {num_zonas} zonas (mínimo 2 parejas por zona)")
        
        if parejas_por_zona_max > 3:
            raise ValueError(f"Con {len(parejas)} parejas y {num_zonas} zonas habría hasta {parejas_por_zona_max} parejas por zona (máximo 3)")
        
        # Eliminar zonas existentes de esta categoría (o todas si no hay categoría)
        if categoria_id:
            # Solo eliminar zonas de esta categoría
            zonas_categoria = db.query(TorneoZona.id).filter(
                TorneoZona.torneo_id == torneo_id,
                TorneoZona.categoria_id == categoria_id
            ).all()
            zona_ids = [z.id for z in zonas_categoria]
            if zona_ids:
                db.query(TorneoZonaPareja).filter(
                    TorneoZonaPareja.zona_id.in_(zona_ids)
                ).delete(synchronize_session=False)
                db.query(TorneoZona).filter(TorneoZona.id.in_(zona_ids)).delete(synchronize_session=False)
        else:
            # Eliminar todas las zonas del torneo
            db.query(TorneoZonaPareja).filter(
                TorneoZonaPareja.zona_id.in_(
                    db.query(TorneoZona.id).filter(TorneoZona.torneo_id == torneo_id)
                )
            ).delete(synchronize_session=False)
            db.query(TorneoZona).filter(TorneoZona.torneo_id == torneo_id).delete()
        
        db.commit()
        
        # Crear zonas (sin prefijo de categoría, ya que se filtra por categoría en la UI)
        zonas = []
        for i in range(num_zonas):
            zona = TorneoZona(
                torneo_id=torneo_id,
                nombre=f"Zona {chr(65 + i)}",  # "Zona A", "Zona B", etc.
                numero_orden=i + 1,
                categoria_id=categoria_id
            )
            db.add(zona)
            zonas.append(zona)
        
        db.flush()
        
        # Distribuir parejas
        if balancear_por_rating:
            TorneoZonaService._distribuir_parejas_balanceadas(db, parejas, zonas)
        else:
            TorneoZonaService._distribuir_parejas_aleatorias(db, parejas, zonas)
        
        # Cambiar estado del torneo
        torneo.estado = 'armando_zonas'
        
        db.commit()
        
        return zonas
    
    @staticmethod
    def _calcular_num_zonas_optimo(num_parejas: int) -> int:
        """
        Calcula el número óptimo de zonas según cantidad de parejas
        Regla: Mínimo 2 parejas por zona, máximo 3 parejas por zona
        """
        if num_parejas < 4:
            return 2  # 4 parejas = 2 zonas de 2
        elif num_parejas <= 6:
            return 2  # 4-6 parejas = 2 zonas de 2-3
        elif num_parejas <= 9:
            return 3  # 7-9 parejas = 3 zonas de 2-3
        elif num_parejas <= 12:
            return 4  # 10-12 parejas = 4 zonas de 2-3
        elif num_parejas <= 15:
            return 5  # 13-15 parejas = 5 zonas de 2-3
        elif num_parejas <= 18:
            return 6  # 16-18 parejas = 6 zonas de 2-3
        else:
            # Para más de 18, calcular dinámicamente
            return (num_parejas + 2) // 3  # Intentar 3 parejas por zona
    
    @staticmethod
    def _distribuir_parejas_balanceadas(
        db: Session,
        parejas: List[TorneoPareja],
        zonas: List[TorneoZona]
    ):
        """Distribuye parejas balanceando por rating promedio"""
        # OPTIMIZACIÓN: Obtener todos los jugadores en una sola query (batch)
        jugadores_ids = set()
        for pareja in parejas:
            jugadores_ids.add(pareja.jugador1_id)
            jugadores_ids.add(pareja.jugador2_id)
        
        # Batch query - traer todos los usuarios de una vez
        usuarios = db.query(Usuario).filter(Usuario.id_usuario.in_(jugadores_ids)).all()
        usuarios_dict = {u.id_usuario: u for u in usuarios}
        
        # Calcular rating promedio de cada pareja (procesamiento en memoria)
        parejas_con_rating = []
        for pareja in parejas:
            jugador1 = usuarios_dict.get(pareja.jugador1_id)
            jugador2 = usuarios_dict.get(pareja.jugador2_id)
            
            rating1 = jugador1.rating if jugador1 and jugador1.rating else 1200
            rating2 = jugador2.rating if jugador2 and jugador2.rating else 1200
            rating_promedio = (rating1 + rating2) / 2
            
            parejas_con_rating.append((pareja, rating_promedio))
        
        # Ordenar por rating descendente
        parejas_con_rating.sort(key=lambda x: x[1], reverse=True)
        
        # Distribuir en serpiente (1->n, n->1, 1->n, ...)
        zona_idx = 0
        direccion = 1
        
        for pareja, rating in parejas_con_rating:
            zona_pareja = TorneoZonaPareja(
                zona_id=zonas[zona_idx].id,
                pareja_id=pareja.id
            )
            db.add(zona_pareja)
            
            # Siguiente zona
            zona_idx += direccion
            if zona_idx >= len(zonas):
                zona_idx = len(zonas) - 1
                direccion = -1
            elif zona_idx < 0:
                zona_idx = 0
                direccion = 1
    
    @staticmethod
    def _distribuir_parejas_aleatorias(
        db: Session,
        parejas: List[TorneoPareja],
        zonas: List[TorneoZona]
    ):
        """Distribuye parejas aleatoriamente"""
        parejas_shuffled = list(parejas)
        random.shuffle(parejas_shuffled)
        
        for i, pareja in enumerate(parejas_shuffled):
            zona_idx = i % len(zonas)
            zona_pareja = TorneoZonaPareja(
                zona_id=zonas[zona_idx].id,
                pareja_id=pareja.id
            )
            db.add(zona_pareja)
    
    @staticmethod
    def listar_zonas(db: Session, torneo_id: int) -> List[dict]:
        """Lista todas las zonas de un torneo con sus parejas (OPTIMIZADO - elimina N+1 queries)"""
        zonas = db.query(TorneoZona).filter(
            TorneoZona.torneo_id == torneo_id
        ).order_by(TorneoZona.numero_orden).all()
        
        if not zonas:
            return []
        
        # OPTIMIZACIÓN 1: Obtener todas las asignaciones en una sola query
        zonas_ids = [z.id for z in zonas]
        asignaciones = db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.zona_id.in_(zonas_ids)
        ).all()
        
        # OPTIMIZACIÓN 2: Obtener todas las parejas en una sola query (batch)
        parejas_ids = [a.pareja_id for a in asignaciones]
        parejas = db.query(TorneoPareja).filter(
            TorneoPareja.id.in_(parejas_ids)
        ).all()
        parejas_dict = {p.id: p for p in parejas}
        
        # OPTIMIZACIÓN 3: Agrupar asignaciones por zona (procesamiento en memoria)
        asignaciones_por_zona = {}
        for asignacion in asignaciones:
            if asignacion.zona_id not in asignaciones_por_zona:
                asignaciones_por_zona[asignacion.zona_id] = []
            asignaciones_por_zona[asignacion.zona_id].append(asignacion)
        
        # Construir resultado (procesamiento en memoria - súper rápido)
        resultado = []
        for zona in zonas:
            asignaciones_zona = asignaciones_por_zona.get(zona.id, [])
            
            parejas_info = []
            for asignacion in asignaciones_zona:
                pareja = parejas_dict.get(asignacion.pareja_id)
                
                if pareja:
                    # Pareja existe
                    parejas_info.append({
                        'id': pareja.id,
                        'jugador1_id': pareja.jugador1_id,
                        'jugador2_id': pareja.jugador2_id,
                        'estado': pareja.estado,
                        'eliminada': False,
                        'disponibilidad_horaria': pareja.disponibilidad_horaria
                    })
                else:
                    # Pareja fue eliminada - mostrar placeholder
                    parejas_info.append({
                        'id': asignacion.pareja_id,
                        'jugador1_id': None,
                        'jugador2_id': None,
                        'estado': 'eliminada',
                        'eliminada': True
                    })
            
            resultado.append({
                'id': zona.id,
                'nombre': zona.nombre,
                'numero': zona.numero_orden,
                'categoria_id': getattr(zona, 'categoria_id', None),
                'parejas': parejas_info
            })
        
        return resultado
    
    @staticmethod
    def obtener_tabla_posiciones(db: Session, zona_id: int) -> dict:
        """
        Obtiene la tabla de posiciones de una zona (incluyendo parejas eliminadas)
        
        Calcula:
        - Partidos jugados
        - Partidos ganados/perdidos
        - Sets ganados/perdidos
        - Games ganados/perdidos
        - Puntos
        """
        from ..models.driveplus_models import Partido
        
        zona = db.query(TorneoZona).filter(TorneoZona.id == zona_id).first()
        if not zona:
            raise ValueError("Zona no encontrada")
        
        # Obtener todas las asignaciones de parejas a esta zona
        asignaciones = db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.zona_id == zona_id
        ).all()
        
        # Inicializar estadísticas para todas las parejas (existentes y eliminadas)
        tabla = []
        for asignacion in asignaciones:
            pareja = db.query(TorneoPareja).filter(
                TorneoPareja.id == asignacion.pareja_id
            ).first()
            
            if pareja:
                # Pareja existe
                tabla.append({
                    'pareja_id': pareja.id,
                    'jugador1_id': pareja.jugador1_id,
                    'jugador2_id': pareja.jugador2_id,
                    'eliminada': False,
                    'partidos_jugados': 0,
                    'partidos_ganados': 0,
                    'partidos_perdidos': 0,
                    'sets_ganados': 0,
                    'sets_perdidos': 0,
                    'games_ganados': 0,
                    'games_perdidos': 0,
                    'puntos': 0
                })
            else:
                # Pareja eliminada
                tabla.append({
                    'pareja_id': asignacion.pareja_id,
                    'jugador1_id': None,
                    'jugador2_id': None,
                    'eliminada': True,
                    'partidos_jugados': 0,
                    'partidos_ganados': 0,
                    'partidos_perdidos': 0,
                    'sets_ganados': 0,
                    'sets_perdidos': 0,
                    'games_ganados': 0,
                    'games_perdidos': 0,
                    'puntos': 0
                })
        
        # Obtener partidos de la zona (confirmados = finalizados)
        partidos = db.query(Partido).filter(
            Partido.id_torneo == zona.torneo_id,
            Partido.zona_id == zona_id,
            Partido.estado == 'confirmado'
        ).all()
        
        # Calcular estadísticas
        for partido in partidos:
            # Usar pareja1_id y pareja2_id directamente
            pareja_a_id = partido.pareja1_id
            pareja_b_id = partido.pareja2_id
            
            if not pareja_a_id or not pareja_b_id:
                continue
            
            # Encontrar índices en tabla
            idx_a = next((i for i, p in enumerate(tabla) if p['pareja_id'] == pareja_a_id), None)
            idx_b = next((i for i, p in enumerate(tabla) if p['pareja_id'] == pareja_b_id), None)
            
            if idx_a is None or idx_b is None:
                continue
            
            # Actualizar partidos jugados
            tabla[idx_a]['partidos_jugados'] += 1
            tabla[idx_b]['partidos_jugados'] += 1
            
            # Obtener resultado
            if partido.resultado_padel:
                resultado = partido.resultado_padel
                sets = resultado.get('sets', [])
                
                # Contar sets y games
                sets_a = 0
                sets_b = 0
                games_a = 0
                games_b = 0
                
                for set_data in sets:
                    if set_data.get('completado'):
                        games_eq_a = set_data.get('gamesEquipoA', 0)
                        games_eq_b = set_data.get('gamesEquipoB', 0)
                        
                        games_a += games_eq_a
                        games_b += games_eq_b
                        
                        if set_data.get('ganador') == 'equipoA':
                            sets_a += 1
                        elif set_data.get('ganador') == 'equipoB':
                            sets_b += 1
                
                # Actualizar estadísticas
                tabla[idx_a]['sets_ganados'] += sets_a
                tabla[idx_a]['sets_perdidos'] += sets_b
                tabla[idx_a]['games_ganados'] += games_a
                tabla[idx_a]['games_perdidos'] += games_b
                
                tabla[idx_b]['sets_ganados'] += sets_b
                tabla[idx_b]['sets_perdidos'] += sets_a
                tabla[idx_b]['games_ganados'] += games_b
                tabla[idx_b]['games_perdidos'] += games_a
                
                # Actualizar ganados/perdidos y puntos usando ganador_pareja_id
                if partido.ganador_pareja_id == pareja_a_id:
                    tabla[idx_a]['partidos_ganados'] += 1
                    tabla[idx_a]['puntos'] += 3
                    tabla[idx_b]['partidos_perdidos'] += 1
                elif partido.ganador_pareja_id == pareja_b_id:
                    tabla[idx_b]['partidos_ganados'] += 1
                    tabla[idx_b]['puntos'] += 3
                    tabla[idx_a]['partidos_perdidos'] += 1
        
        # Ordenar tabla por puntos, diferencia de sets, diferencia de games
        tabla.sort(key=lambda x: (
            -x['puntos'],
            -(x['sets_ganados'] - x['sets_perdidos']),
            -(x['games_ganados'] - x['games_perdidos'])
        ))
        
        # Obtener nombres y usernames de jugadores (solo para parejas existentes)
        from ..models.driveplus_models import Usuario, PerfilUsuario
        jugadores_ids = set()
        for item in tabla:
            if not item['eliminada'] and item['jugador1_id'] and item['jugador2_id']:
                jugadores_ids.add(item['jugador1_id'])
                jugadores_ids.add(item['jugador2_id'])
        
        usuarios = {}
        perfiles = {}
        if jugadores_ids:
            usuarios = {u.id_usuario: u for u in db.query(Usuario).filter(Usuario.id_usuario.in_(jugadores_ids)).all()}
            perfiles = {p.id_usuario: p for p in db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario.in_(jugadores_ids)).all()}
        
        # Agregar posición y nombres
        for i, item in enumerate(tabla):
            item['posicion'] = i + 1
            
            if item['eliminada']:
                # Pareja eliminada - mostrar placeholder
                item['jugador1_nombre'] = "Pareja"
                item['jugador2_nombre'] = "Eliminada"
                item['jugador1_username'] = None
                item['jugador2_username'] = None
                item['pareja_nombre'] = "Pareja Eliminada"
            else:
                # Pareja existente - obtener nombres reales
                p1 = perfiles.get(item['jugador1_id'])
                p2 = perfiles.get(item['jugador2_id'])
                u1 = usuarios.get(item['jugador1_id'])
                u2 = usuarios.get(item['jugador2_id'])
                
                item['jugador1_nombre'] = f"{p1.nombre} {p1.apellido}" if p1 else None
                item['jugador2_nombre'] = f"{p2.nombre} {p2.apellido}" if p2 else None
                item['jugador1_username'] = u1.nombre_usuario if u1 else None
                item['jugador2_username'] = u2.nombre_usuario if u2 else None
                item['pareja_nombre'] = f"{item['jugador1_nombre']} / {item['jugador2_nombre']}" if item['jugador1_nombre'] and item['jugador2_nombre'] else None
        
        return {
            'zona_id': zona_id,
            'zona_nombre': zona.nombre,
            'tabla': tabla
        }
    
    @staticmethod
    def mover_pareja_entre_zonas(
        db: Session,
        pareja_id: int,
        zona_destino_id: int,
        user_id: int
    ):
        """Mueve una pareja de una zona a otra"""
        # Obtener pareja
        pareja = db.query(TorneoPareja).filter(TorneoPareja.id == pareja_id).first()
        if not pareja:
            raise ValueError("Pareja no encontrada")
        
        # Verificar permisos
        if not TorneoZonaService._es_organizador(db, pareja.torneo_id, user_id):
            raise ValueError("No tienes permisos para mover parejas")
        
        # Verificar que la zona destino existe y es del mismo torneo
        zona_destino = db.query(TorneoZona).filter(TorneoZona.id == zona_destino_id).first()
        if not zona_destino:
            raise ValueError("Zona destino no encontrada")
        
        if zona_destino.torneo_id != pareja.torneo_id:
            raise ValueError("La zona destino no pertenece al mismo torneo")
        
        # Eliminar de zona actual
        db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.pareja_id == pareja_id
        ).delete()
        
        # Agregar a zona destino
        zona_pareja = TorneoZonaPareja(
            zona_id=zona_destino_id,
            pareja_id=pareja_id
        )
        db.add(zona_pareja)
        
        db.commit()
        
        return {"message": "Pareja movida exitosamente"}
    
    @staticmethod
    def _es_organizador(db: Session, torneo_id: int, user_id: int) -> bool:
        """Verifica si un usuario es organizador del torneo"""
        from ..models.torneo_models import TorneoOrganizador
        
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            return False
        
        # Creador siempre es organizador
        if torneo.creado_por == user_id:
            return True
        
        # Verificar si es organizador
        organizador = db.query(TorneoOrganizador).filter(
            TorneoOrganizador.torneo_id == torneo_id,
            TorneoOrganizador.user_id == user_id
        ).first()
        
        return organizador is not None
