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
        Genera bracket según formato APA (Asociación Padel Argentino).
        Soporta 2, 3, 4, 5 y 6 zonas con los cruces oficiales.
        """
        # Detectar cantidad de zonas
        zonas_set = []
        for c in clasificados:
            z = c.get('zona_nombre')
            if z and z not in zonas_set:
                zonas_set.append(z)
        num_zonas = len(zonas_set)

        if num_zonas >= 2:
            return TorneoPlayoffService._generar_bracket_apa(
                db, torneo_id, clasificados, user_id, categoria_id, num_zonas
            )

        # Fallback sin zonas: bracket estándar
        num_clasificados = len(clasificados)
        bracket_size = TorneoPlayoffService._next_power_of_two(num_clasificados)
        if bracket_size > 16:
            bracket_size = 16
            clasificados = clasificados[:16]

        clasificados_ordenados = TorneoPlayoffService._reordenar_clasificados_evitando_rematches_zona(
            clasificados, bracket_size
        )
        fases = TorneoPlayoffService._determinar_fases(bracket_size)
        num_rondas = len(fases)
        emparejamientos = TorneoPlayoffService._generar_emparejamientos(bracket_size)
        clasificados_dict = {c['seed']: c for c in clasificados_ordenados}

        partidos_creados = []
        partidos_ronda: Dict[int, Dict[int, Partido]] = {i: {} for i in range(num_rondas)}
        fase_inicial = fases[0]

        for i, (seed1, seed2) in enumerate(emparejamientos):
            c1 = clasificados_dict.get(seed1)
            c2 = clasificados_dict.get(seed2)
            pareja1_id = c1['pareja_id'] if c1 else None
            pareja2_id = c2['pareja_id'] if c2 else None
            es_bye = (pareja1_id is not None and pareja2_id is None) or \
                     (pareja1_id is None and pareja2_id is not None)
            ganador_id = None
            estado = 'pendiente'
            if es_bye:
                ganador_id = pareja1_id or pareja2_id
                estado = 'bye'
            partido = Partido(
                id_torneo=torneo_id, categoria_id=categoria_id,
                pareja1_id=pareja1_id, pareja2_id=pareja2_id,
                ganador_pareja_id=ganador_id, fase=fase_inicial,
                numero_partido=i + 1, estado=estado,
                fecha=datetime.now(), id_creador=user_id, tipo='torneo'
            )
            db.add(partido)
            partidos_creados.append(partido)
            partidos_ronda[0][i + 1] = partido

        db.flush()

        for ronda_idx in range(1, num_rondas):
            fase = fases[ronda_idx]
            partidos_ronda_anterior = partidos_ronda[ronda_idx - 1]
            num_partidos_ronda = bracket_size // (2 ** (ronda_idx + 1))
            for i in range(num_partidos_ronda):
                po1 = partidos_ronda_anterior.get(i * 2 + 1)
                po2 = partidos_ronda_anterior.get(i * 2 + 2)
                p1 = po1.ganador_pareja_id if po1 and po1.estado == 'bye' else None
                p2 = po2.ganador_pareja_id if po2 and po2.estado == 'bye' else None
                partido = Partido(
                    id_torneo=torneo_id, categoria_id=categoria_id,
                    pareja1_id=p1, pareja2_id=p2, fase=fase,
                    numero_partido=i + 1, estado='pendiente',
                    fecha=datetime.now(), id_creador=user_id, tipo='torneo'
                )
                db.add(partido)
                partidos_creados.append(partido)
                partidos_ronda[ronda_idx][i + 1] = partido

        db.commit()
        return partidos_creados

    @staticmethod
    def _generar_bracket_apa(
        db: Session,
        torneo_id: int,
        clasificados: List[Dict],
        user_id: int,
        categoria_id: Optional[int],
        num_zonas: int
    ) -> List[Partido]:
        """
        Genera bracket según formato oficial APA para 2-6 zonas.

        Los BYEs NO se crean como partidos — en su lugar, las parejas que
        pasan directo se setean directamente en la ronda siguiente.
        Solo se crean partidos reales (ambas parejas presentes).

        numero_partido sigue la convención de bracket binario para que
        avanzar_ganador funcione: siguiente = (n+1)//2, impar→p1, par→p2.
        """
        # Agrupar por zona
        zonas: Dict[str, List[Dict]] = {}
        nombres_zonas_orden = []
        for c in clasificados:
            z = c.get('zona_nombre', '')
            if z not in zonas:
                zonas[z] = []
                nombres_zonas_orden.append(z)
            zonas[z].append(c)

        for z in zonas:
            zonas[z] = sorted(zonas[z], key=lambda x: (x['posicion'], -x.get('puntos', 0)))

        zona_map = {}
        letras = ['A', 'B', 'C', 'D', 'E', 'F']
        for i, nombre in enumerate(nombres_zonas_orden[:num_zonas]):
            zona_map[letras[i]] = nombre

        def gp(letra: str, pos: int) -> Optional[int]:
            """Get pareja_id by zona letter and position (1=1st, 2=2nd)"""
            nombre = zona_map.get(letra)
            if not nombre or nombre not in zonas:
                return None
            lista = zonas[nombre]
            return lista[pos - 1]['pareja_id'] if pos - 1 < len(lista) else None

        # Definir estructura del bracket por cantidad de zonas.
        # Cada ronda es una lista de slots. Cada slot es:
        #   (zona_ref, zona_ref) — partido real entre dos parejas de zona
        #   (zona_ref, None)     — BYE, pareja pasa directo (NO se crea partido)
        #   ('prev', 'prev')     — ambos vienen de ronda anterior
        # numero_partido se asigna secuencialmente (1, 2, 3...) dentro de cada fase.
        # La conexión entre rondas usa: partido N de ronda R alimenta
        # partido ceil(N/2) de ronda R+1, como p1 si N es impar, p2 si N es par.

        if num_zonas == 2:
            rondas = [
                ('semis', [
                    (('A', 1), ('B', 2)),
                    (('A', 2), ('B', 1)),
                ]),
                ('final', [
                    ('prev', 'prev'),
                ]),
            ]
        elif num_zonas == 3:
            # APA 3 zonas: 4tos con 2 BYEs + semis + final
            # Slot 1: BYE 1°A (no se crea, se setea en semi#1 p1)
            # Slot 2: 2°B vs 2°C (partido real)
            # Slot 3: BYE 1°B (no se crea, se setea en semi#2 p1)
            # Slot 4: 1°C vs 2°A (partido real)
            rondas = [
                ('4tos', [
                    (('A', 1), None),      # BYE → semi#1 p1
                    (('B', 2), ('C', 2)),   # real → semi#1 p2
                    (('B', 1), None),      # BYE → semi#2 p1
                    (('C', 1), ('A', 2)),   # real → semi#2 p2
                ]),
                ('semis', [
                    ('prev', 'prev'),
                    ('prev', 'prev'),
                ]),
                ('final', [
                    ('prev', 'prev'),
                ]),
            ]
        elif num_zonas == 4:
            # APA 4 zonas: todos juegan 4tos, sin BYEs
            rondas = [
                ('4tos', [
                    (('A', 1), ('C', 2)),
                    (('B', 2), ('D', 1)),
                    (('C', 1), ('A', 2)),
                    (('D', 2), ('B', 1)),
                ]),
                ('semis', [
                    ('prev', 'prev'),
                    ('prev', 'prev'),
                ]),
                ('final', [
                    ('prev', 'prev'),
                ]),
            ]
        elif num_zonas == 5:
            # APA 5 zonas (imagen oficial):
            # 8vos slot 1: BYE 1°A         → 4tos#1 p1
            # 8vos slot 2: 2°B vs 2°C      → 4tos#1 p2
            # 8vos slot 3: BYE 1°E         → 4tos#2 p1
            # 8vos slot 4: BYE 1°D         → 4tos#2 p2
            # 8vos slot 5: BYE 1°C         → 4tos#3 p1
            # 8vos slot 6: BYE 2°E         → 4tos#3 p2
            # 8vos slot 7: BYE 1°B         → 4tos#4 p2 (via slot 8)
            # 8vos slot 8: 2°A vs 2°D      → 4tos#4 p1 (via slot 7)
            # Wait — slot 7 impar → p1, slot 8 par → p2
            # So: 4tos#4 p1=ganador(slot7=BYE 1°B)=1°B, p2=ganador(slot8=2°A vs 2°D)
            # But APA image shows: ganador(2°A vs 2°D) vs 1°B
            # That means ganador should be p1 and 1°B should be p2
            # To achieve this: slot 7 = 2°A vs 2°D (real), slot 8 = BYE 1°B
            # Then: 4tos#4 p1=ganador(2°A vs 2°D), p2=1°B ✅
            rondas = [
                ('8vos', [
                    (('A', 1), None),       # slot 1: BYE 1°A
                    (('B', 2), ('C', 2)),    # slot 2: 2°B vs 2°C (real)
                    (('E', 1), None),       # slot 3: BYE 1°E
                    (('D', 1), None),       # slot 4: BYE 1°D
                    (('C', 1), None),       # slot 5: BYE 1°C
                    (('E', 2), None),       # slot 6: BYE 2°E
                    (('A', 2), ('D', 2)),    # slot 7: 2°A vs 2°D (real)
                    (('B', 1), None),       # slot 8: BYE 1°B
                ]),
                ('4tos', [
                    ('prev', 'prev'),  # 4tos#1: 1°A vs ganador(2°B vs 2°C)
                    ('prev', 'prev'),  # 4tos#2: 1°E vs 1°D
                    ('prev', 'prev'),  # 4tos#3: 1°C vs 2°E
                    ('prev', 'prev'),  # 4tos#4: ganador(2°A vs 2°D) vs 1°B
                ]),
                ('semis', [
                    ('prev', 'prev'),
                    ('prev', 'prev'),
                ]),
                ('final', [
                    ('prev', 'prev'),
                ]),
            ]
        else:  # num_zonas == 6
            # APA 6 zonas: 8vos con 4 BYEs + 4tos + semis + final
            rondas = [
                ('8vos', [
                    (('A', 1), None),               # slot 1: BYE 1°A
                    (('F', 2), ('C', 2)),            # slot 2: 2°F vs 2°C (real)
                    (('D', 1), None),               # slot 3: BYE 1°D
                    (('E', 1), ('B', 2)),            # slot 4: 1°E vs 2°B (real)
                    (('C', 1), None),               # slot 5: BYE 1°C
                    (('A', 2), ('F', 1)),            # slot 6: 2°A vs 1°F (real)
                    (('B', 1), None),               # slot 7: BYE 1°B
                    (('E', 2), ('D', 2)),            # slot 8: 2°E vs 2°D (real)
                ]),
                ('4tos', [
                    ('prev', 'prev'),
                    ('prev', 'prev'),
                    ('prev', 'prev'),
                    ('prev', 'prev'),
                ]),
                ('semis', [
                    ('prev', 'prev'),
                    ('prev', 'prev'),
                ]),
                ('final', [
                    ('prev', 'prev'),
                ]),
            ]

        # Generar partidos ronda por ronda
        partidos_creados = []
        partidos_por_fase: Dict[str, List[Partido]] = {}

        for ronda_idx, (fase, cruces) in enumerate(rondas):
            partidos_por_fase[fase] = []

            for i, cruce in enumerate(cruces):
                num = i + 1
                p1_id = None
                p2_id = None

                if ronda_idx == 0:
                    # Primera ronda: resolver desde zonas
                    c1, c2 = cruce
                    if c1 is not None and isinstance(c1, tuple):
                        p1_id = gp(c1[0], c1[1])
                    if c2 is not None and isinstance(c2, tuple):
                        p2_id = gp(c2[0], c2[1])
                else:
                    # Rondas siguientes: p1 y p2 vienen de ganadores de ronda anterior
                    fase_anterior = rondas[ronda_idx - 1][0]
                    partidos_ant = partidos_por_fase.get(fase_anterior, [])
                    # Partido i recibe ganadores de partidos (i*2) y (i*2+1) de ronda anterior
                    idx1 = i * 2
                    idx2 = i * 2 + 1
                    if idx1 < len(partidos_ant) and partidos_ant[idx1].estado == 'bye':
                        p1_id = partidos_ant[idx1].ganador_pareja_id
                    if idx2 < len(partidos_ant) and partidos_ant[idx2].estado == 'bye':
                        p2_id = partidos_ant[idx2].ganador_pareja_id

                # Determinar BYE: solo en primera ronda (BYEs reales del formato APA).
                # En rondas siguientes, p2=None significa "rival por determinar", no BYE.
                es_bye = ronda_idx == 0 and (p1_id is not None and p2_id is None)
                ganador_id = p1_id if es_bye else None
                estado = 'bye' if es_bye else 'pendiente'

                partido = Partido(
                    id_torneo=torneo_id,
                    categoria_id=categoria_id,
                    pareja1_id=p1_id,
                    pareja2_id=p2_id,
                    ganador_pareja_id=ganador_id,
                    fase=fase,
                    numero_partido=num,
                    estado=estado,
                    fecha=datetime.now(),
                    id_creador=user_id,
                    tipo='torneo'
                )
                db.add(partido)
                partidos_creados.append(partido)
                partidos_por_fase[fase].append(partido)

            db.flush()

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
