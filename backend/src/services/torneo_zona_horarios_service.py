"""
Servicio mejorado para generación de zonas con compatibilidad horaria
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import random

from ..models.torneo_models import Torneo, TorneoZona, TorneoPareja, TorneoZonaPareja
from ..models.driveplus_models import Usuario


class TorneoZonaHorariosService:
    """Servicio para generación de zonas considerando disponibilidad horaria"""
    
    DURACION_PARTIDO_MINUTOS = 70
    
    @staticmethod
    def generar_zonas_con_horarios(
        db: Session,
        torneo_id: int,
        user_id: int,
        num_zonas: Optional[int] = None,
        num_canchas: int = 3,
        categoria_id: Optional[int] = None
    ) -> Dict:
        """
        Genera zonas considerando:
        1. Balance de rating
        2. Compatibilidad horaria entre parejas de la misma zona
        3. Generación de fixture respetando canchas disponibles
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            user_id: ID del usuario organizador
            num_zonas: Número de zonas (opcional, se calcula automáticamente)
            num_canchas: Número de canchas disponibles
            categoria_id: ID de categoría (opcional)
            
        Returns:
            Dict con zonas creadas y fixture generado
        """
        from ..models.torneo_models import TorneoCategoria
        
        # Verificar permisos
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            raise ValueError("Torneo no encontrado")
        
        if torneo.creado_por != user_id:
            raise ValueError("No tienes permisos para generar zonas")
        
        # Obtener parejas confirmadas
        query = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == torneo_id,
            TorneoPareja.estado.in_(['inscripta', 'confirmada'])
        )
        
        if categoria_id:
            query = query.filter(TorneoPareja.categoria_id == categoria_id)
        
        parejas = query.all()
        
        if len(parejas) < 4:
            raise ValueError(f"Se necesitan al menos 4 parejas (hay {len(parejas)})")
        
        # Calcular número óptimo de zonas
        if num_zonas is None:
            num_zonas = TorneoZonaHorariosService._calcular_num_zonas(len(parejas))
        
        # Obtener horarios del torneo
        horarios_torneo = torneo.horarios_disponibles or {}
        
        # Analizar compatibilidad horaria de parejas
        parejas_con_datos = TorneoZonaHorariosService._analizar_parejas(
            db, parejas, horarios_torneo
        )
        
        # Agrupar parejas por compatibilidad horaria
        grupos_compatibles = TorneoZonaHorariosService._agrupar_por_compatibilidad(
            parejas_con_datos, num_zonas
        )
        
        # Limpiar zonas existentes
        TorneoZonaHorariosService._limpiar_zonas_existentes(
            db, torneo_id, categoria_id
        )
        
        # Crear zonas
        zonas = []
        for i in range(num_zonas):
            zona = TorneoZona(
                torneo_id=torneo_id,
                nombre=f"Zona {chr(65 + i)}",
                numero_orden=i + 1,
                categoria_id=categoria_id
            )
            db.add(zona)
            zonas.append(zona)
        
        db.flush()
        
        # Distribuir parejas en zonas
        distribucion = TorneoZonaHorariosService._distribuir_parejas_inteligente(
            db, parejas_con_datos, zonas, grupos_compatibles
        )
        
        # Cambiar estado del torneo
        torneo.estado = 'armando_zonas'
        db.commit()
        
        return {
            "zonas_creadas": len(zonas),
            "zonas": [
                {
                    "id": z.id,
                    "nombre": z.nombre,
                    "parejas": distribucion.get(z.id, [])
                }
                for z in zonas
            ],
            "compatibilidad_promedio": TorneoZonaHorariosService._calcular_compatibilidad_promedio(
                distribucion, parejas_con_datos
            )
        }
    
    @staticmethod
    def _calcular_num_zonas(num_parejas: int) -> int:
        """Calcula número óptimo de zonas (2-3 parejas por zona)"""
        if num_parejas <= 6:
            return 2
        elif num_parejas <= 9:
            return 3
        elif num_parejas <= 12:
            return 4
        elif num_parejas <= 15:
            return 5
        else:
            return (num_parejas + 2) // 3
    
    @staticmethod
    def _analizar_parejas(
        db: Session,
        parejas: List[TorneoPareja],
        horarios_torneo: Dict
    ) -> List[Dict]:
        """
        Analiza cada pareja y extrae:
        - Rating promedio
        - Disponibilidad horaria
        - Slots disponibles
        """
        # OPTIMIZACIÓN: Obtener todos los jugadores en una sola query (batch)
        jugadores_ids = set()
        for pareja in parejas:
            jugadores_ids.add(pareja.jugador1_id)
            jugadores_ids.add(pareja.jugador2_id)
        
        # Batch query - traer todos los usuarios de una vez
        usuarios = db.query(Usuario).filter(Usuario.id_usuario.in_(jugadores_ids)).all()
        usuarios_dict = {u.id_usuario: u for u in usuarios}
        
        # Procesar parejas (en memoria - súper rápido)
        parejas_datos = []
        
        for pareja in parejas:
            # Obtener jugadores del diccionario
            j1 = usuarios_dict.get(pareja.jugador1_id)
            j2 = usuarios_dict.get(pareja.jugador2_id)
            
            rating1 = j1.rating if j1 and j1.rating else 1200
            rating2 = j2.rating if j2 and j2.rating else 1200
            rating_promedio = (rating1 + rating2) / 2
            
            # Obtener disponibilidad horaria de la pareja
            disponibilidad = pareja.disponibilidad_horaria or {}
            
            # Convertir disponibilidad a slots de tiempo
            slots = TorneoZonaHorariosService._extraer_slots_disponibles(
                disponibilidad, horarios_torneo
            )
            
            parejas_datos.append({
                "pareja": pareja,
                "rating": rating_promedio,
                "disponibilidad": disponibilidad,
                "slots": slots
            })
        
        return parejas_datos
    
    @staticmethod
    def _extraer_slots_disponibles(
        disponibilidad_pareja: any,  # Puede ser Dict o List
        horarios_torneo: Dict
    ) -> Set[Tuple[str, str]]:
        """
        Extrae slots de tiempo disponibles para una pareja
        
        IMPORTANTE: disponibilidad_pareja ahora contiene RESTRICCIONES (horarios NO disponibles)
        
        Returns:
            Set de tuplas (dia, hora) ej: {('sabado', '18:00'), ('domingo', '10:00')}
        """
        # Generar TODOS los slots del torneo primero
        todos_slots = set()
        for tipo_dia, franjas in horarios_torneo.items():
            if not franjas:
                continue
            for franja in franjas:
                desde = franja.get('desde', '08:00')
                hasta = franja.get('hasta', '23:00')
                # Generar slots cada 70 minutos
                hora_actual = TorneoZonaHorariosService._parse_hora(desde)
                hora_fin = TorneoZonaHorariosService._parse_hora(hasta)
                while hora_actual < hora_fin:
                    todos_slots.add((tipo_dia, hora_actual.strftime('%H:%M')))
                    hora_actual += timedelta(minutes=70)
        
        # Si la pareja no tiene restricciones, está disponible en todos los horarios
        if not disponibilidad_pareja:
            return todos_slots
        
        # Extraer restricciones (horarios NO disponibles)
        restricciones = set()
        
        # Manejar ambos formatos: array directo o objeto con "franjas"
        franjas_restricciones = []
        if isinstance(disponibilidad_pareja, list):
            # Formato nuevo: array directo
            franjas_restricciones = disponibilidad_pareja
        elif isinstance(disponibilidad_pareja, dict):
            # Formato antiguo: objeto con "franjas"
            franjas_restricciones = disponibilidad_pareja.get('franjas', [])
        
        # Procesar restricciones
        for franja in franjas_restricciones:
            dias = franja.get('dias', [])
            hora_inicio = franja.get('horaInicio', '08:00')
            hora_fin = franja.get('horaFin', '23:00')
            
            # Generar slots RESTRINGIDOS para cada día
            for dia in dias:
                hora_actual = TorneoZonaHorariosService._parse_hora(hora_inicio)
                hora_limite = TorneoZonaHorariosService._parse_hora(hora_fin)
                
                while hora_actual < hora_limite:
                    restricciones.add((dia, hora_actual.strftime('%H:%M')))
                    hora_actual += timedelta(minutes=70)
        
        # Retornar slots disponibles = todos los slots - restricciones
        slots_disponibles = todos_slots - restricciones
        
        return slots_disponibles
    
    @staticmethod
    def _parse_hora(hora_str: str) -> datetime:
        """Convierte string de hora a datetime"""
        try:
            return datetime.strptime(hora_str, '%H:%M')
        except:
            return datetime.strptime('08:00', '%H:%M')
    
    @staticmethod
    def _calcular_compatibilidad(slots1: Set, slots2: Set) -> float:
        """
        Calcula compatibilidad horaria entre dos parejas
        
        Returns:
            Porcentaje de slots compatibles (0.0 a 1.0)
        """
        if not slots1 or not slots2:
            return 1.0  # Si alguna no tiene restricciones, son compatibles
        
        interseccion = slots1 & slots2
        union = slots1 | slots2
        
        if not union:
            return 0.0
        
        return len(interseccion) / len(union)
    
    @staticmethod
    def _agrupar_por_compatibilidad(
        parejas_datos: List[Dict],
        num_zonas: int
    ) -> List[List[Dict]]:
        """
        Agrupa parejas maximizando compatibilidad horaria dentro de cada grupo
        
        Usa algoritmo greedy:
        1. Ordena parejas por rating
        2. Asigna a zonas balanceando rating y compatibilidad
        """
        # Ordenar por rating descendente
        parejas_ordenadas = sorted(parejas_datos, key=lambda x: x['rating'], reverse=True)
        
        # Inicializar grupos
        grupos = [[] for _ in range(num_zonas)]
        
        # Distribuir en serpiente considerando compatibilidad
        for pareja_data in parejas_ordenadas:
            # Encontrar el grupo con mejor compatibilidad y menor tamaño
            mejor_grupo_idx = TorneoZonaHorariosService._encontrar_mejor_grupo(
                pareja_data, grupos
            )
            grupos[mejor_grupo_idx].append(pareja_data)
        
        return grupos
    
    @staticmethod
    def _encontrar_mejor_grupo(
        pareja_data: Dict,
        grupos: List[List[Dict]]
    ) -> int:
        """
        Encuentra el mejor grupo para una pareja considerando:
        1. Compatibilidad horaria con parejas del grupo
        2. Tamaño del grupo (balance)
        """
        mejor_idx = 0
        mejor_score = -1
        
        for idx, grupo in enumerate(grupos):
            if not grupo:
                # Grupo vacío, score alto
                score = 100
            else:
                # Calcular compatibilidad promedio con el grupo
                compatibilidades = []
                for otra_pareja in grupo:
                    comp = TorneoZonaHorariosService._calcular_compatibilidad(
                        pareja_data['slots'],
                        otra_pareja['slots']
                    )
                    compatibilidades.append(comp)
                
                compatibilidad_promedio = sum(compatibilidades) / len(compatibilidades)
                
                # Penalizar grupos más grandes
                penalizacion_tamano = len(grupo) * 0.1
                
                score = compatibilidad_promedio - penalizacion_tamano
            
            if score > mejor_score:
                mejor_score = score
                mejor_idx = idx
        
        return mejor_idx
    
    @staticmethod
    def _distribuir_parejas_inteligente(
        db: Session,
        parejas_datos: List[Dict],
        zonas: List[TorneoZona],
        grupos_compatibles: List[List[Dict]]
    ) -> Dict[int, List[int]]:
        """
        Distribuye parejas en zonas según grupos de compatibilidad
        
        Returns:
            Dict {zona_id: [pareja_id, ...]}
        """
        distribucion = {}
        
        for zona, grupo in zip(zonas, grupos_compatibles):
            parejas_ids = []
            for pareja_data in grupo:
                pareja = pareja_data['pareja']
                
                # Crear relación zona-pareja
                zona_pareja = TorneoZonaPareja(
                    zona_id=zona.id,
                    pareja_id=pareja.id
                )
                db.add(zona_pareja)
                parejas_ids.append(pareja.id)
            
            distribucion[zona.id] = parejas_ids
        
        return distribucion
    
    @staticmethod
    def _calcular_compatibilidad_promedio(
        distribucion: Dict[int, List[int]],
        parejas_datos: List[Dict]
    ) -> float:
        """Calcula compatibilidad promedio de todas las zonas"""
        parejas_dict = {p['pareja'].id: p for p in parejas_datos}
        
        compatibilidades = []
        
        for zona_id, parejas_ids in distribucion.items():
            if len(parejas_ids) < 2:
                continue
            
            # Calcular compatibilidad entre todas las parejas de la zona
            for i in range(len(parejas_ids)):
                for j in range(i + 1, len(parejas_ids)):
                    p1 = parejas_dict.get(parejas_ids[i])
                    p2 = parejas_dict.get(parejas_ids[j])
                    
                    if p1 and p2:
                        comp = TorneoZonaHorariosService._calcular_compatibilidad(
                            p1['slots'], p2['slots']
                        )
                        compatibilidades.append(comp)
        
        if not compatibilidades:
            return 0.0
        
        return sum(compatibilidades) / len(compatibilidades)
    
    @staticmethod
    def _limpiar_zonas_existentes(
        db: Session,
        torneo_id: int,
        categoria_id: Optional[int]
    ):
        """Elimina zonas existentes del torneo/categoría"""
        if categoria_id:
            zonas_ids = [z.id for z in db.query(TorneoZona.id).filter(
                TorneoZona.torneo_id == torneo_id,
                TorneoZona.categoria_id == categoria_id
            ).all()]
        else:
            zonas_ids = [z.id for z in db.query(TorneoZona.id).filter(
                TorneoZona.torneo_id == torneo_id
            ).all()]
        
        if zonas_ids:
            db.query(TorneoZonaPareja).filter(
                TorneoZonaPareja.zona_id.in_(zonas_ids)
            ).delete(synchronize_session=False)
            db.query(TorneoZona).filter(TorneoZona.id.in_(zonas_ids)).delete(synchronize_session=False)
        
        db.commit()
