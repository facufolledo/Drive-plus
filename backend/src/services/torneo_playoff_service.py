"""
Servicio para gestión de playoffs (fase de eliminación) en torneos
Genera brackets dinámicos con BYEs automáticos
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import math

from ..models.torneo_models import (
    Torneo, TorneoZona, TorneoPareja, TorneoCategoria,
    EstadoTorneo
)
from ..models.driveplus_models import Partido


class TorneoPlayoffService:
    """Servicio para gestión de playoffs en torneos"""
    
    @staticmethod
    def _next_power_of_two(n: int) -> int:
        """Calcula la siguiente potencia de 2"""
        p = 1
        while p < n:
            p *= 2
        return p
    
    @staticmethod
    def generar_playoffs(
        db: Session,
        torneo_id: int,
        user_id: int,
        clasificados_por_zona: int = 2,
        categoria_id: Optional[int] = None
    ) -> List[Partido]:
        """Genera playoffs. Si categoria_id se pasa, solo para esa categoría; si no, para todas."""
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            raise ValueError("Torneo no encontrado")
        
        if not TorneoPlayoffService._es_organizador(db, torneo_id, user_id):
            raise ValueError("No tienes permisos para generar playoffs")
        
        todos_partidos = []
        
        if categoria_id is not None:
            partidos = TorneoPlayoffService._generar_playoffs_categoria(
                db, torneo_id, user_id, categoria_id, clasificados_por_zona
            )
            todos_partidos.extend(partidos)
        else:
            categorias = db.query(TorneoCategoria).filter(
                TorneoCategoria.torneo_id == torneo_id
            ).all()
            if categorias:
                for categoria in categorias:
                    partidos = TorneoPlayoffService._generar_playoffs_categoria(
                        db, torneo_id, user_id, categoria.id, clasificados_por_zona
                    )
                    todos_partidos.extend(partidos)
            else:
                partidos = TorneoPlayoffService._generar_playoffs_categoria(
                    db, torneo_id, user_id, None, clasificados_por_zona
                )
                todos_partidos.extend(partidos)
        
        if todos_partidos:
            torneo.estado = EstadoTorneo.FASE_ELIMINACION
        db.commit()
        
        return todos_partidos
    
    @staticmethod
    def _generar_playoffs_categoria(
        db: Session,
        torneo_id: int,
        user_id: int,
        categoria_id: Optional[int],
        clasificados_por_zona: int
    ) -> List[Partido]:
        """Genera playoffs para una categoría específica"""
        # Eliminar playoffs existentes de esta categoría
        query_delete = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final'])
        )
        if categoria_id:
            query_delete = query_delete.filter(Partido.categoria_id == categoria_id)
        else:
            query_delete = query_delete.filter(Partido.categoria_id.is_(None))
        query_delete.delete(synchronize_session=False)
        db.commit()
        
        # Obtener clasificados
        clasificados = TorneoPlayoffService._obtener_clasificados_categoria(
            db, torneo_id, categoria_id, clasificados_por_zona
        )
        
        if len(clasificados) < 2:
            return []
        
        # Generar bracket completo con BYEs explícitos
        partidos = TorneoPlayoffService._generar_bracket_con_byes(
            db, torneo_id, clasificados, user_id, categoria_id
        )
        
        return partidos
    
    @staticmethod
    def _obtener_clasificados_categoria(
        db: Session,
        torneo_id: int,
        categoria_id: Optional[int],
        clasificados_por_zona: int
    ) -> List[Dict]:
        """Obtiene los clasificados ordenados por posición y puntos"""
        from ..services.torneo_zona_service import TorneoZonaService
        from ..models.torneo_models import TorneoZonaPareja
        
        query_zonas = db.query(TorneoZona).filter(TorneoZona.torneo_id == torneo_id)
        if categoria_id:
            query_zonas = query_zonas.filter(TorneoZona.categoria_id == categoria_id)
        else:
            query_zonas = query_zonas.filter(TorneoZona.categoria_id.is_(None))
        
        zonas = query_zonas.order_by(TorneoZona.numero_orden).all()
        clasificados = []
        
        if not zonas:
            # Sin zonas, obtener parejas directamente
            query_parejas = db.query(TorneoPareja).filter(
                TorneoPareja.torneo_id == torneo_id,
                TorneoPareja.estado.in_(['inscripta', 'confirmada'])
            )
            if categoria_id:
                query_parejas = query_parejas.filter(TorneoPareja.categoria_id == categoria_id)
            
            parejas = query_parejas.all()
            for i, pareja in enumerate(parejas):
                clasificados.append({
                    'pareja_id': pareja.id,
                    'posicion': i + 1,
                    'puntos': 0,
                    'rating': 1200
                })
            return clasificados
        
        # Obtener clasificados de cada zona
        for zona in zonas:
            try:
                resultado = TorneoZonaService.obtener_tabla_posiciones(db, zona.id)
                tabla = resultado.get('tabla', [])
                
                for i, pos in enumerate(tabla[:clasificados_por_zona]):
                    # Usar posición de la tabla (1º, 2º, ...) para que playoffs emparejen 1º vs 2º
                    posicion_tabla = pos.get('posicion', i + 1)
                    if not isinstance(posicion_tabla, int):
                        posicion_tabla = int(posicion_tabla) if posicion_tabla else (i + 1)
                    clasificados.append({
                        'pareja_id': pos['pareja_id'],
                        'posicion': posicion_tabla,
                        'puntos': pos.get('puntos', 0),
                        'rating': pos.get('rating_promedio', 1200),
                        'zona_nombre': zona.nombre
                    })
            except Exception:
                parejas_zona = db.query(TorneoPareja).join(
                    TorneoZonaPareja, TorneoZonaPareja.pareja_id == TorneoPareja.id
                ).filter(TorneoZonaPareja.zona_id == zona.id).all()
                
                for i, pareja in enumerate(parejas_zona[:clasificados_por_zona]):
                    clasificados.append({
                        'pareja_id': pareja.id,
                        'posicion': i + 1,
                        'puntos': 0,
                        'rating': 1200,
                        'zona_nombre': zona.nombre
                    })
        
        return clasificados

    
    @staticmethod
    def _generar_bracket_con_byes(
        db: Session,
        torneo_id: int,
        clasificados: List[Dict],
        user_id: int,
        categoria_id: Optional[int]
    ) -> List[Partido]:
        """
        Genera bracket completo con BYEs explícitos en la BD
        
        - Calcula potencia de 2 necesaria
        - Crea TODOS los partidos (incluyendo BYEs)
        - BYEs tienen pareja2_id = NULL y ganador ya seteado
        """
        num_clasificados = len(clasificados)
        bracket_size = TorneoPlayoffService._next_power_of_two(num_clasificados)
        
        # Limitar a 16
        if bracket_size > 16:
            bracket_size = 16
            clasificados = clasificados[:16]
            num_clasificados = 16
        
        num_byes = bracket_size - num_clasificados
        
        # Reordenar para evitar que rivales de la misma zona se crucen hasta la final
        clasificados_ordenados = TorneoPlayoffService._reordenar_clasificados_evitando_rematches_zona(
            clasificados, bracket_size
        )
        
        # Determinar fases
        fases = TorneoPlayoffService._determinar_fases(bracket_size)
        num_rondas = len(fases)
        
        # Generar emparejamientos de primera ronda (estándar de bracket)
        emparejamientos = TorneoPlayoffService._generar_emparejamientos(bracket_size)
        
        # Crear diccionario de clasificados por seed
        clasificados_dict = {c['seed']: c for c in clasificados_ordenados}
        
        partidos_creados = []
        # Estructura para trackear partidos por ronda y posición
        # partidos_ronda[ronda][posicion] = partido
        partidos_ronda: Dict[int, Dict[int, Partido]] = {i: {} for i in range(num_rondas)}
        
        # RONDA 1: Crear todos los partidos (normales y BYEs)
        fase_inicial = fases[0]
        
        for i, (seed1, seed2) in enumerate(emparejamientos):
            c1 = clasificados_dict.get(seed1)
            c2 = clasificados_dict.get(seed2)
            
            pareja1_id = c1['pareja_id'] if c1 else None
            pareja2_id = c2['pareja_id'] if c2 else None
            
            # Determinar si es BYE
            es_bye = (pareja1_id is not None and pareja2_id is None) or \
                     (pareja1_id is None and pareja2_id is not None)
            
            # Si es BYE, el ganador es la pareja que existe
            ganador_id = None
            estado = 'pendiente'
            if es_bye:
                ganador_id = pareja1_id or pareja2_id
                estado = 'bye'
            
            partido = Partido(
                id_torneo=torneo_id,
                categoria_id=categoria_id,
                pareja1_id=pareja1_id,
                pareja2_id=pareja2_id,
                ganador_pareja_id=ganador_id,
                fase=fase_inicial,
                numero_partido=i + 1,
                estado=estado,
                fecha=datetime.now(),
                id_creador=user_id,
                tipo='torneo'
            )
            db.add(partido)
            partidos_creados.append(partido)
            partidos_ronda[0][i + 1] = partido
        
        db.flush()
        
        # RONDAS SIGUIENTES: Crear partidos vacíos o con ganadores de BYE
        for ronda_idx in range(1, num_rondas):
            fase = fases[ronda_idx]
            partidos_ronda_anterior = partidos_ronda[ronda_idx - 1]
            num_partidos_ronda = bracket_size // (2 ** (ronda_idx + 1))
            
            for i in range(num_partidos_ronda):
                # Cada partido recibe ganadores de 2 partidos de la ronda anterior
                partido_origen_1 = partidos_ronda_anterior.get(i * 2 + 1)
                partido_origen_2 = partidos_ronda_anterior.get(i * 2 + 2)
                
                # Si el partido origen es BYE, ya sabemos el ganador
                pareja1_id = None
                pareja2_id = None
                
                if partido_origen_1 and partido_origen_1.estado == 'bye':
                    pareja1_id = partido_origen_1.ganador_pareja_id
                
                if partido_origen_2 and partido_origen_2.estado == 'bye':
                    pareja2_id = partido_origen_2.ganador_pareja_id
                
                partido = Partido(
                    id_torneo=torneo_id,
                    categoria_id=categoria_id,
                    pareja1_id=pareja1_id,
                    pareja2_id=pareja2_id,
                    fase=fase,
                    numero_partido=i + 1,
                    estado='pendiente',
                    fecha=datetime.now(),
                    id_creador=user_id,
                    tipo='torneo'
                )
                db.add(partido)
                partidos_creados.append(partido)
                partidos_ronda[ronda_idx][i + 1] = partido
        
        db.commit()
        return partidos_creados
    
    @staticmethod
    def _determinar_fases(bracket_size: int) -> List[str]:
        """Determina las fases según el tamaño del bracket"""
        if bracket_size == 2:
            return ['final']
        elif bracket_size == 4:
            return ['semis', 'final']
        elif bracket_size == 8:
            return ['4tos', 'semis', 'final']
        elif bracket_size == 16:
            return ['8vos', '4tos', 'semis', 'final']
        else:
            return ['16avos', '8vos', '4tos', 'semis', 'final']
    
    @staticmethod
    def _seeds_por_mitad_bracket(bracket_size: int) -> tuple:
        """
        Retorna (mitad1, mitad2) con los seeds de cada mitad del bracket.
        Las parejas de la misma zona deben estar en mitades opuestas para
        no cruzarse hasta la final.
        """
        if bracket_size == 2:
            return ([1], [2])
        elif bracket_size == 4:
            return ([1, 4], [2, 3])
        elif bracket_size == 8:
            return ([1, 4, 5, 8], [2, 3, 6, 7])
        elif bracket_size == 16:
            return ([1, 4, 5, 8, 9, 12, 13, 16], [2, 3, 6, 7, 10, 11, 14, 15])
        else:
            m = bracket_size // 2
            return (list(range(1, m + 1)), list(range(m + 1, bracket_size + 1)))
    
    @staticmethod
    def _reordenar_clasificados_evitando_rematches_zona(
        clasificados: List[Dict],
        bracket_size: int
    ) -> List[Dict]:
        """
        Reordena clasificados y asigna seeds respetando:
        1) En cada cruce de 1ª ronda: un 1º de zona vs un 2º de zona (nunca 1º vs 1º ni 2º vs 2º).
        2) 1º y 2º de la misma zona en mitades opuestas del bracket para no cruzarse hasta la final.
        """
        mitad1, mitad2 = TorneoPlayoffService._seeds_por_mitad_bracket(bracket_size)

        # Agrupar por zona (zona_nombre puede no existir si no hay zonas)
        zonas: Dict[str, List[Dict]] = {}
        sin_zona: List[Dict] = []
        for c in clasificados:
            zona = c.get('zona_nombre') or c.get('zona_id') or '_sin_zona'
            if zona == '_sin_zona':
                sin_zona.append(c)
            else:
                if zona not in zonas:
                    zonas[zona] = []
                zonas[zona].append(c)

        # Ordenar cada zona por posición y puntos (1º, 2º, ...)
        for zona in zonas:
            zonas[zona] = sorted(
                zonas[zona],
                key=lambda x: (x['posicion'], -x.get('puntos', 0), -x.get('rating', 1200))
            )

        # Si no hay zonas (ej. torneo sin fase grupos), usar orden estándar por posición
        if not zonas:
            ordenados = sorted(
                clasificados,
                key=lambda x: (x['posicion'], -x.get('puntos', 0), -x.get('rating', 1200))
            )
            for i, c in enumerate(ordenados):
                c['seed'] = i + 1
            return ordenados

        # Orden de zonas = orden de aparición en clasificados (coincide con numero_orden del fixture)
        nombres_zonas = []
        for c in clasificados:
            z = c.get('zona_nombre') or c.get('zona_id') or '_sin_zona'
            if z != '_sin_zona' and z not in nombres_zonas:
                nombres_zonas.append(z)
        n_zonas = len(nombres_zonas)
        mid = n_zonas // 2

        # Primera mitad de zonas: 1º → mitad superior del bracket, 2º → mitad inferior.
        # Segunda mitad de zonas: 1º → mitad inferior, 2º → mitad superior.
        # Así cada mitad del bracket tiene N/2 primeros y N/2 segundos, y misma zona no se repite hasta la final.
        top_list: List[Dict] = []
        bottom_list: List[Dict] = []
        for i, nombre in enumerate(nombres_zonas):
            lista = zonas[nombre]
            if len(lista) >= 1:
                if i < mid:
                    top_list.append(lista[0])
                    if len(lista) >= 2:
                        bottom_list.append(lista[1])
                else:
                    bottom_list.append(lista[0])
                    if len(lista) >= 2:
                        top_list.append(lista[1])
        # Clasificados 3º, 4º, etc. (si hay): repartir alternando entre top y bottom
        for nombre in nombres_zonas:
            lista = zonas[nombre]
            for j in range(2, len(lista)):
                if len(top_list) <= len(bottom_list):
                    top_list.append(lista[j])
                else:
                    bottom_list.append(lista[j])

        # Sin zona: repartir por posición (1º a top, 2º a bottom, etc.)
        sin_zona_ord = sorted(
            sin_zona,
            key=lambda x: (x['posicion'], -x.get('puntos', 0), -x.get('rating', 1200))
        )
        for i, c in enumerate(sin_zona_ord):
            if i % 2 == 0:
                top_list.append(c)
            else:
                bottom_list.append(c)

        # Dentro de cada mitad: primero todos los 1º (por puntos/rating), luego todos los 2º.
        # Así en los emparejamientos (1-8), (4-5), etc. cada par queda 1º vs 2º.
        def _es_primer(p: Dict) -> bool:
            pos = p.get('posicion')
            return pos == 1 or pos == '1' or (pos is not None and int(pos) == 1)

        def key_posicion_puntos(x: Dict) -> tuple:
            pos = x.get('posicion')
            pos_int = int(pos) if pos is not None else 0
            return (pos_int, -x.get('puntos', 0), -x.get('rating', 1200))

        top_1sts = sorted([c for c in top_list if _es_primer(c)], key=key_posicion_puntos)
        top_2nds = sorted([c for c in top_list if not _es_primer(c)], key=key_posicion_puntos)
        top_list = top_1sts + top_2nds

        bottom_1sts = sorted([c for c in bottom_list if _es_primer(c)], key=key_posicion_puntos)
        bottom_2nds = sorted([c for c in bottom_list if not _es_primer(c)], key=key_posicion_puntos)
        bottom_list = bottom_1sts + bottom_2nds

        # Asignar seeds: mitad1 a top_list, mitad2 a bottom_list
        for i, c in enumerate(top_list):
            if i < len(mitad1):
                c['seed'] = mitad1[i]
        for i, c in enumerate(bottom_list):
            if i < len(mitad2):
                c['seed'] = mitad2[i]

        return top_list + bottom_list
    
    @staticmethod
    def _generar_emparejamientos(bracket_size: int) -> List[tuple]:
        """
        Genera emparejamientos estándar de bracket
        Seed 1 vs último, etc. para que los mejores se encuentren en la final
        """
        if bracket_size == 2:
            return [(1, 2)]
        elif bracket_size == 4:
            return [(1, 4), (2, 3)]
        elif bracket_size == 8:
            return [(1, 8), (4, 5), (2, 7), (3, 6)]
        elif bracket_size == 16:
            return [
                (1, 16), (8, 9), (4, 13), (5, 12),
                (2, 15), (7, 10), (3, 14), (6, 11)
            ]
        else:
            emparejamientos = []
            for i in range(bracket_size // 2):
                emparejamientos.append((i + 1, bracket_size - i))
            return emparejamientos

    
    @staticmethod
    def listar_partidos_playoffs(
        db: Session,
        torneo_id: int,
        categoria_id: Optional[int] = None
    ) -> Dict[str, List[Partido]]:
        """Lista partidos de playoffs agrupados por fase"""
        query = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final'])
        )
        
        if categoria_id:
            query = query.filter(Partido.categoria_id == categoria_id)
        
        partidos = query.order_by(Partido.numero_partido).all()
        
        partidos_por_fase = {
            '16avos': [],
            '8vos': [],
            '4tos': [],
            'semis': [],
            'final': []
        }
        
        for partido in partidos:
            fase = partido.fase
            if fase == 'cuartos':
                fase = '4tos'
            elif fase == 'semifinal':
                fase = 'semis'
            
            if fase in partidos_por_fase:
                partidos_por_fase[fase].append(partido)
        
        return partidos_por_fase

    @staticmethod
    def eliminar_playoffs(
        db: Session,
        torneo_id: int,
        user_id: int,
        categoria_id: Optional[int] = None
    ) -> int:
        """
        Elimina todos los partidos de playoffs del torneo (o solo de una categoría).
        Solo organizadores. Si se eliminan todos los playoffs, el torneo vuelve a fase_grupos.
        Devuelve la cantidad de partidos eliminados.
        """
        if not TorneoPlayoffService._es_organizador(db, torneo_id, user_id):
            raise ValueError("No tienes permisos para eliminar playoffs")

        query_delete = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final'])
        )
        if categoria_id is not None:
            query_delete = query_delete.filter(Partido.categoria_id == categoria_id)
        else:
            query_delete = query_delete.filter(Partido.categoria_id.is_(None))

        count = query_delete.delete(synchronize_session=False)
        db.commit()

        # Si no quedan partidos de playoffs en el torneo, volver estado a fase_grupos
        restantes = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final'])
        ).count()
        if restantes == 0:
            torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
            if torneo:
                torneo.estado = EstadoTorneo.FASE_GRUPOS
                db.commit()

        return count
    
    @staticmethod
    def avanzar_ganador(
        db: Session,
        partido_id: int,
        pareja_ganadora_id: int
    ) -> Optional[Partido]:
        """Avanza al ganador de un partido a la siguiente ronda"""
        partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
        
        if not partido:
            raise ValueError("Partido no encontrado")
        
        if partido.fase == 'final':
            # Verificar si todas las finales terminaron
            torneo = db.query(Torneo).filter(Torneo.id == partido.id_torneo).first()
            if torneo:
                finales_pendientes = db.query(Partido).filter(
                    Partido.id_torneo == partido.id_torneo,
                    Partido.fase == 'final',
                    Partido.estado.notin_(['confirmado', 'bye'])
                ).count()
                
                if finales_pendientes == 0:
                    torneo.estado = EstadoTorneo.FINALIZADO
                    db.commit()
            return None
        
        # Determinar siguiente fase
        siguiente_fase = TorneoPlayoffService._obtener_siguiente_fase(partido.fase)
        numero_siguiente = (partido.numero_partido + 1) // 2
        
        partido_siguiente = db.query(Partido).filter(
            Partido.id_torneo == partido.id_torneo,
            Partido.fase == siguiente_fase,
            Partido.numero_partido == numero_siguiente,
            Partido.categoria_id == partido.categoria_id
        ).first()
        
        if partido_siguiente:
            if partido.numero_partido % 2 == 1:
                partido_siguiente.pareja1_id = pareja_ganadora_id
            else:
                partido_siguiente.pareja2_id = pareja_ganadora_id
            
            db.commit()
            return partido_siguiente
        
        return None
    
    @staticmethod
    def _obtener_siguiente_fase(fase_actual: str) -> str:
        """Obtiene la siguiente fase del torneo"""
        mapa = {
            '16avos': '8vos',
            '8vos': '4tos',
            '4tos': 'semis',
            'cuartos': 'semis',
            'semis': 'final',
            'semifinal': 'final'
        }
        return mapa.get(fase_actual, 'final')
    
    @staticmethod
    def _es_organizador(db: Session, torneo_id: int, user_id: int) -> bool:
        """Verifica si un usuario es organizador de un torneo"""
        from ..models.torneo_models import TorneoOrganizador
        
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if torneo and torneo.creado_por == user_id:
            return True
        
        try:
            org = db.query(TorneoOrganizador).filter(
                TorneoOrganizador.torneo_id == torneo_id,
                TorneoOrganizador.user_id == user_id
            ).first()
            return org is not None
        except Exception:
            return False
