"""
Servicio para gestión global de fixture considerando todas las categorías y canchas
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..models.torneo_models import (
    Torneo, TorneoZona, TorneoPareja, TorneoCancha, 
    TorneoCategoria
)
from ..models.driveplus_models import Partido


class TorneoFixtureGlobalService:
    """
    Servicio para generar fixture considerando:
    - Todas las categorías del torneo
    - Todas las canchas disponibles
    - Disponibilidad horaria de parejas
    - No más partidos simultáneos que canchas disponibles
    """
    
    DURACION_PARTIDO_MINUTOS = 70
    
    @staticmethod
    def generar_fixture_completo(
        db: Session,
        torneo_id: int,
        user_id: int,
        categoria_id: Optional[int] = None
    ) -> Dict:
        """
        Genera fixture completo para todas las zonas y categorías del torneo
        o solo para una categoría específica
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            user_id: ID del usuario organizador
            categoria_id: (Opcional) ID de categoría específica
            
        Returns:
            Dict con partidos generados y estadísticas
        """
        # Verificar permisos
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            raise ValueError("Torneo no encontrado")
        
        if torneo.creado_por != user_id:
            raise ValueError("No tienes permisos")
        
        # 🔴 FIX CRÍTICO: Si no se especifica categoría, generar por categoría secuencialmente
        if not categoria_id:
            # Obtener todas las categorías del torneo
            categorias = db.query(TorneoCategoria).filter(
                TorneoCategoria.torneo_id == torneo_id
            ).all()
            
            if not categorias:
                raise ValueError("No hay categorías en el torneo")
            
            # Generar fixture para cada categoría secuencialmente
            resultado_total = {
                "partidos_generados": 0,
                "partidos_no_programados": 0,
                "zonas_procesadas": 0,
                "canchas_utilizadas": 0,
                "slots_utilizados": 0,
                "partidos": [],
                "partidos_sin_programar": []
            }
            
            for categoria in categorias:
# DEBUG: print(f"\n🔄 Generando fixture para categoría {categoria.nombre} (ID {categoria.id})...")
                try:
                    resultado_cat = TorneoFixtureGlobalService._generar_fixture_categoria(
                        db, torneo_id, user_id, categoria.id
                    )
                    
                    # Acumular resultados
                    resultado_total["partidos_generados"] += resultado_cat["partidos_generados"]
                    resultado_total["partidos_no_programados"] += resultado_cat["partidos_no_programados"]
                    resultado_total["zonas_procesadas"] += resultado_cat["zonas_procesadas"]
                    resultado_total["partidos"].extend(resultado_cat["partidos"])
                    resultado_total["partidos_sin_programar"].extend(resultado_cat["partidos_sin_programar"])
                    
# DEBUG: print(f"   ✅ {resultado_cat['partidos_generados']} partidos programados")
                except Exception as e:
                    print(f"   ⚠️  Error en categoría {categoria.nombre}: {e}")
                    continue
            
            return resultado_total
        
        # Si se especifica categoría, generar solo para esa categoría
        return TorneoFixtureGlobalService._generar_fixture_categoria(
            db, torneo_id, user_id, categoria_id
        )
    
    @staticmethod
    def _generar_fixture_categoria(
        db: Session,
        torneo_id: int,
        user_id: int,
        categoria_id: int
    ) -> Dict:
        """
        Genera fixture para una categoría específica
        Considera partidos ya programados de otras categorías
        """
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        
        # Obtener zonas de la categoría
        zonas = db.query(TorneoZona).filter(
            TorneoZona.torneo_id == torneo_id,
            TorneoZona.categoria_id == categoria_id
        ).all()
        
        if not zonas:
            raise ValueError(f"No hay zonas para la categoría {categoria_id}")
        
        # Obtener canchas disponibles
        canchas = db.query(TorneoCancha).filter(
            TorneoCancha.torneo_id == torneo_id,
            TorneoCancha.activa == True
        ).all()
        
        if not canchas:
            raise ValueError("No hay canchas configuradas")
        
        num_canchas = len(canchas)
        
        # Obtener horarios del torneo
        horarios_torneo = torneo.horarios_disponibles or {}
        
        # 🔴 CRÍTICO: Cargar partidos ya programados de OTRAS categorías
        partidos_existentes = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase == 'zona',
            Partido.categoria_id != categoria_id,
            Partido.fecha_hora.isnot(None)
        ).all()
        
# DEBUG: print(f"   📊 Partidos existentes de otras categorías: {len(partidos_existentes)}")
        
        # Generar todos los partidos de todas las zonas
        todos_partidos = []
        for zona in zonas:
            partidos_zona = TorneoFixtureGlobalService._generar_partidos_zona(
                db, zona
            )
            todos_partidos.extend(partidos_zona)
        
        # Obtener disponibilidad de todas las parejas involucradas
        parejas_disponibilidad = TorneoFixtureGlobalService._obtener_disponibilidad_parejas(
            db, todos_partidos, torneo
        )
        
        # Generar slots de tiempo disponibles
        slots_disponibles = TorneoFixtureGlobalService._generar_slots_torneo(
            torneo, horarios_torneo
        )
        
        # Asignar horarios y canchas a los partidos
        resultado_asignacion = TorneoFixtureGlobalService._asignar_horarios_y_canchas(
            db,
            todos_partidos,
            parejas_disponibilidad,
            slots_disponibles,
            canchas,
            num_canchas,
            partidos_existentes  # Pasar partidos existentes
        )
        
        partidos_programados = resultado_asignacion['partidos_programados']
        partidos_no_programados = resultado_asignacion['partidos_no_programados']
        
        # Guardar partidos en la base de datos (solo de esta categoría)
        TorneoFixtureGlobalService._guardar_partidos(
            db, torneo_id, partidos_programados, categoria_id
        )
        
        return {
            "partidos_generados": len(partidos_programados),
            "partidos_no_programados": len(partidos_no_programados),
            "zonas_procesadas": len(zonas),
            "canchas_utilizadas": num_canchas,
            "slots_utilizados": len(set(p['slot'] for p in partidos_programados)),
            "partidos": partidos_programados,
            "partidos_sin_programar": partidos_no_programados
        }
    
    @staticmethod
    def _generar_partidos_zona(
        db: Session,
        zona: TorneoZona
    ) -> List[Dict]:
        """
        Genera todos los partidos de una zona (round-robin)
        
        Returns:
            Lista de dicts con info de partidos
        """
        from ..models.torneo_models import TorneoZonaPareja
        
        # Obtener parejas de la zona
        parejas = db.query(TorneoPareja).join(
            TorneoZonaPareja,
            TorneoZonaPareja.pareja_id == TorneoPareja.id
        ).filter(
            TorneoZonaPareja.zona_id == zona.id
        ).all()
        
        if len(parejas) < 2:
            return []
        
        # Generar todos contra todos
        partidos = []
        for i in range(len(parejas)):
            for j in range(i + 1, len(parejas)):
                partidos.append({
                    "zona_id": zona.id,
                    "zona_nombre": zona.nombre,
                    "categoria_id": zona.categoria_id,
                    "pareja1_id": parejas[i].id,
                    "pareja2_id": parejas[j].id,
                    "pareja1": parejas[i],
                    "pareja2": parejas[j]
                })
        
        return partidos
    
    @staticmethod
    def _obtener_disponibilidad_parejas(
        db: Session,
        partidos: List[Dict],
        torneo: Torneo
    ) -> Dict[int, Dict]:
        """
        Obtiene restricciones horarias de todas las parejas
        
        🔴 SEMÁNTICA CLARA: disponibilidad_horaria = RESTRICCIONES (NO pueden jugar)
        
        Formato de entrada (JSON en DB):
        [
            {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
        ]
        
        Formato de salida:
        {
            pareja_id: {
                'restricciones_por_dia': {
                    'viernes': [(540, 1140)]  # minutos desde medianoche
                },
                'raw': <datos originales para debug>
            }
        }
        
        Returns:
            Dict {pareja_id: {'restricciones_por_dia': {dia: [(inicio, fin)]}, 'raw': ...}}
        """
        parejas_ids = set()
        for partido in partidos:
            parejas_ids.add(partido['pareja1_id'])
            parejas_ids.add(partido['pareja2_id'])
        
        resultado = {}
        
        for pareja_id in parejas_ids:
            pareja = db.query(TorneoPareja).filter(TorneoPareja.id == pareja_id).first()
            if not pareja:
# DEBUG: print(f"⚠️  Pareja {pareja_id} no encontrada en DB")
                continue
            
            restricciones_raw = pareja.disponibilidad_horaria
            
            # 🔴 LOGGING CRÍTICO: Ver datos crudos
# DEBUG: print(f"\n🔍 Pareja #{pareja_id}:")
# DEBUG: print(f"   Raw DB: {restricciones_raw}")
# DEBUG: print(f"   Tipo: {type(restricciones_raw)}")
            
            # Parseo robusto con múltiples formatos
            franjas_restricciones = []
            
            if not restricciones_raw:
                # Caso 1: None o vacío → Sin restricciones
# DEBUG: print(f"   ✅ Sin restricciones (disponible siempre)")
                resultado[pareja_id] = {
                    'restricciones_por_dia': {},
                    'raw': None
                }
                continue
            
            elif isinstance(restricciones_raw, list):
                # Caso 2: Lista directa [{'dias': [...], 'horaInicio': ..., 'horaFin': ...}]
                franjas_restricciones = restricciones_raw
# DEBUG: print(f"   📋 Formato: lista directa con {len(franjas_restricciones)} franjas")
            
            elif isinstance(restricciones_raw, dict):
                # Caso 3: Dict con 'franjas' key
                if 'franjas' in restricciones_raw:
                    franjas_restricciones = restricciones_raw['franjas']
# DEBUG: print(f"   📋 Formato: dict con franjas ({len(franjas_restricciones)} franjas)")
                # Caso 4: Dict con 'restricciones_por_dia' (ya procesado)
                elif 'restricciones_por_dia' in restricciones_raw:
# DEBUG: print(f"   📋 Formato: ya procesado")
                    resultado[pareja_id] = restricciones_raw
                    continue
                # Caso 5: Dict directo con dias/horaInicio/horaFin
                elif 'dias' in restricciones_raw and 'horaInicio' in restricciones_raw:
                    franjas_restricciones = [restricciones_raw]
# DEBUG: print(f"   📋 Formato: dict directo (convertido a lista)")
                else:
                    # Caso 6: Dict con estructura desconocida → tratar como sin restricciones
# DEBUG: print(f"   ⚠️  Dict sin estructura conocida → tratando como sin restricciones")
                    resultado[pareja_id] = {
                        'restricciones_por_dia': {},
                        'raw': restricciones_raw
                    }
                    continue
            
            else:
                # Caso 7: Tipo inesperado
                print(f"   ❌ Tipo inesperado: {type(restricciones_raw)} → tratando como sin restricciones")
                resultado[pareja_id] = {
                    'restricciones_por_dia': {},
                    'raw': restricciones_raw
                }
                continue
            
            # 🔴 PROCESAR FRANJAS COMO RESTRICCIONES (horarios bloqueados)
            restricciones_por_dia = {}
            
            for idx, franja in enumerate(franjas_restricciones):
                if not isinstance(franja, dict):
# DEBUG: print(f"   ⚠️  Franja {idx} no es dict: {franja}")
                    continue
                
                dias = franja.get('dias', [])
                hora_inicio = franja.get('horaInicio') or franja.get('hora_inicio') or franja.get('desde', '00:00')
                hora_fin = franja.get('horaFin') or franja.get('hora_fin') or franja.get('hasta', '23:59')
                
                if not dias:
# DEBUG: print(f"   ⚠️  Franja {idx} sin días: {franja}")
                    continue
                
                # Convertir a minutos
                try:
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                except (ValueError, IndexError, AttributeError) as e:
                    print(f"   ❌ Error parseando horas en franja {idx}: {e}")
                    continue
                
                # Normalizar días a lowercase
                for dia in dias:
                    dia_norm = str(dia).strip().lower()
                    if dia_norm not in restricciones_por_dia:
                        restricciones_por_dia[dia_norm] = []
                    restricciones_por_dia[dia_norm].append((inicio_mins, fin_mins))
# DEBUG: print(f"   🚫 {dia_norm}: NO puede {hora_inicio}-{hora_fin} ({inicio_mins}-{fin_mins} mins)")
            
            resultado[pareja_id] = {
                'restricciones_por_dia': restricciones_por_dia,
                'raw': restricciones_raw
            }
            
            if not restricciones_por_dia:
                pass  # Sin restricciones válidas
        
        return resultado
    
    @staticmethod
    def _generar_slots_torneo(
        torneo: Torneo,
        horarios_torneo: Dict
    ) -> List[Tuple[str, str, str]]:
        """
        Genera todos los slots de tiempo disponibles del torneo
        
        Returns:
            Lista de tuplas (fecha, dia_semana, hora)
        """
        slots = []
        
        # 🔴 FIX: Normalizar horarios_torneo si viene como lista
        if isinstance(horarios_torneo, list):
            # Convertir lista a dict por día
            dict_por_dia = {}
            for franja in horarios_torneo:
                desde = franja.get("horaInicio") or franja.get("desde", "08:00")
                hasta = franja.get("horaFin") or franja.get("hasta", "23:00")
                for d in franja.get("dias", []):
                    d = (d or "").strip().lower()
                    dict_por_dia[d] = {"inicio": desde, "fin": hasta}
            horarios_torneo = dict_por_dia
        
        fecha_inicio = torneo.fecha_inicio
        fecha_fin = torneo.fecha_fin
        
        # Iterar por cada día del torneo
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            dia_semana = TorneoFixtureGlobalService._obtener_dia_semana(fecha_actual)
            
            # Intentar obtener horarios específicos del día
            horarios_dia = None
            
            # Formato nuevo: horarios por día específico (viernes, sabado, domingo, etc.)
            if dia_semana in horarios_torneo:
                horarios_dia = horarios_torneo[dia_semana]
            # Formato viejo: horarios por tipo de día (semana, finDeSemana)
            else:
                tipo_dia = 'finDeSemana' if dia_semana in ['sabado', 'domingo'] else 'semana'
                franjas = horarios_torneo.get(tipo_dia, [])
                
                if not franjas:
                    # Si no hay franjas definidas, usar horario por defecto
                    franjas = [{'desde': '08:00', 'hasta': '23:00'}]
                
                # Generar slots para cada franja (formato viejo)
                for franja in franjas:
                    hora_desde = franja.get('desde', '08:00')
                    hora_hasta = franja.get('hasta', '23:00')
                    
                    hora_actual = datetime.strptime(hora_desde, '%H:%M')
                    hora_limite = datetime.strptime(hora_hasta, '%H:%M')
                    
                    # IMPORTANTE: Asegurar que no se generen slots que excedan el límite
                    # Restar 70 minutos del límite para que el partido termine antes del cierre
                    hora_limite_ajustada = hora_limite - timedelta(minutes=70)
                    
                    while hora_actual <= hora_limite_ajustada:
                        slots.append((
                            fecha_actual.strftime('%Y-%m-%d'),
                            dia_semana,
                            hora_actual.strftime('%H:%M')
                        ))
                        hora_actual += timedelta(minutes=70)
                
                fecha_actual += timedelta(days=1)
                continue
            
            # Formato nuevo: procesar horarios del día específico
            if horarios_dia and isinstance(horarios_dia, dict):
                hora_desde = horarios_dia.get('inicio') or horarios_dia.get('desde', '08:00')
                hora_hasta = horarios_dia.get('fin') or horarios_dia.get('hasta', '23:00')
                
                hora_actual = datetime.strptime(hora_desde, '%H:%M')
                hora_limite = datetime.strptime(hora_hasta, '%H:%M')
                
                # IMPORTANTE: Asegurar que no se generen slots que excedan el límite
                # Restar 70 minutos del límite para que el partido termine antes del cierre
                hora_limite_ajustada = hora_limite - timedelta(minutes=70)
                
                while hora_actual <= hora_limite_ajustada:
                    slots.append((
                        fecha_actual.strftime('%Y-%m-%d'),
                        dia_semana,
                        hora_actual.strftime('%H:%M')
                    ))
                    hora_actual += timedelta(minutes=70)
            
            fecha_actual += timedelta(days=1)
        
        return slots
    
    @staticmethod
    def _obtener_dia_semana(fecha: datetime.date) -> str:
        """Convierte fecha a nombre de día en español"""
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        return dias[fecha.weekday()]
    
    @staticmethod
    def _asignar_horarios_y_canchas(
        db: Session,
        partidos: List[Dict],
        parejas_disponibilidad: Dict[int, Dict],
        slots_disponibles: List[Tuple[str, str, str]],
        canchas: List[TorneoCancha],
        num_canchas: int,
        partidos_existentes: List[Partido] = None
    ) -> Dict:
        """
        Asigna horarios y canchas a los partidos considerando:
        - Disponibilidad de parejas (RESPETADA ESTRICTAMENTE)
        - Mínimo 180 minutos (3 horas) entre partidos del mismo jugador
        - Máximo N partidos simultáneos (N = número de canchas)
        - No repetir cancha/horario
        - Partidos ya programados de otras categorías (NUEVO)
        
        Args:
            partidos_existentes: Lista de partidos ya programados (de otras categorías)
        
        Returns:
            Dict con partidos_programados y partidos_no_programados
        """
        partidos_programados = []
        partidos_no_programados = []
        
        # Mapa de ocupación: {(fecha, hora): [cancha_id, ...]}
        ocupacion_canchas = defaultdict(list)
        
        # Tracking de partidos por jugador: {jugador_id: [datetime, ...]}
        partidos_por_jugador = defaultdict(list)
        
        # NUEVO: Inicializar con partidos existentes de otras categorías
        if partidos_existentes:
            for partido_existente in partidos_existentes:
                if partido_existente.fecha_hora and partido_existente.cancha_id:
                    # Marcar ocupación de cancha
                    fecha_str = partido_existente.fecha_hora.strftime('%Y-%m-%d')
                    hora_str = partido_existente.fecha_hora.strftime('%H:%M')
                    ocupacion_canchas[(fecha_str, hora_str)].append(partido_existente.cancha_id)
                    
                    # Obtener parejas del partido existente
                    pareja1 = db.query(TorneoPareja).filter(TorneoPareja.id == partido_existente.pareja1_id).first()
                    pareja2 = db.query(TorneoPareja).filter(TorneoPareja.id == partido_existente.pareja2_id).first()
                    
                    if pareja1 and pareja2:
                        # Registrar partidos de jugadores
                        jugadores_existentes = [
                            pareja1.jugador1_id, 
                            pareja1.jugador2_id, 
                            pareja2.jugador1_id, 
                            pareja2.jugador2_id
                        ]
                        for jugador_id in jugadores_existentes:
                            # Convertir a naive para evitar error offset-naive vs offset-aware
                            fh = partido_existente.fecha_hora
                            if fh.tzinfo is not None:
                                fh = fh.replace(tzinfo=None)
                            partidos_por_jugador[jugador_id].append(fh)
        
        # Ordenar partidos por prioridad (ej: zonas con menos partidos primero)
        partidos_ordenados = sorted(partidos, key=lambda p: p['zona_id'])
        
        for partido in partidos_ordenados:
            pareja1_id = partido['pareja1_id']
            pareja2_id = partido['pareja2_id']
            
            # Obtener parejas para obtener jugadores
            pareja1 = db.query(TorneoPareja).filter(TorneoPareja.id == pareja1_id).first()
            pareja2 = db.query(TorneoPareja).filter(TorneoPareja.id == pareja2_id).first()
            
            if not pareja1 or not pareja2:
                continue
            
            # Lista de todos los jugadores involucrados
            jugadores = [pareja1.jugador1_id, pareja1.jugador2_id, pareja2.jugador1_id, pareja2.jugador2_id]
            
            # Obtener disponibilidad de ambas parejas
            datos_pareja1 = parejas_disponibilidad.get(pareja1_id, {'restricciones_por_dia': {}})
            datos_pareja2 = parejas_disponibilidad.get(pareja2_id, {'restricciones_por_dia': {}})
            
# DEBUG: print(f"\n🎾 Buscando slot para partido: Pareja {pareja1_id} vs Pareja {pareja2_id}")
            
            # Buscar slot compatible
            slot_asignado = None
            cancha_asignada = None
            
            for fecha, dia, hora in slots_disponibles:
                # 1. VERIFICAR DISPONIBILIDAD HORARIA
                hora_mins = int(hora.split(':')[0]) * 60 + int(hora.split(':')[1])
                
# DEBUG: print(f"   🔍 Evaluando slot: {fecha} {dia} {hora} ({hora_mins} mins)")
                
                # Verificar pareja 1
# DEBUG: print(f"      Verificando Pareja {pareja1_id}:")
                pareja1_disponible = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
                    dia, hora_mins, datos_pareja1
                )
                
                # Verificar pareja 2
# DEBUG: print(f"      Verificando Pareja {pareja2_id}:")
                pareja2_disponible = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
                    dia, hora_mins, datos_pareja2
                )
                
                if not (pareja1_disponible and pareja2_disponible):
# DEBUG: print(f"      ❌ Slot rechazado por restricciones horarias")
                    continue
                
                # 2. VERIFICAR TIEMPO MÍNIMO ENTRE PARTIDOS (180 MINUTOS = 3 HORAS)
                fecha_hora_slot = datetime.strptime(f"{fecha} {hora}", '%Y-%m-%d %H:%M')
                
                conflicto_tiempo = False
                for jugador_id in jugadores:
                    for fecha_hora_existente in partidos_por_jugador[jugador_id]:
                        diferencia_minutos = abs((fecha_hora_slot - fecha_hora_existente).total_seconds() / 60)
                        if diferencia_minutos < 180:  # Mínimo 180 minutos (3 horas)
# DEBUG: print(f"      ❌ Jugador {jugador_id} tiene partido muy cercano ({diferencia_minutos:.0f} mins)")
                            conflicto_tiempo = True
                            break
                    if conflicto_tiempo:
                        break
                
                if conflicto_tiempo:
                    continue
                
                # 3. VERIFICAR CANCHA DISPONIBLE
                canchas_ocupadas = ocupacion_canchas[(fecha, hora)]
                cancha_libre = None
                
                for cancha in canchas:
                    if cancha.id not in canchas_ocupadas:
                        cancha_libre = cancha
                        break
                
                if not cancha_libre:
# DEBUG: print(f"      ❌ No hay canchas disponibles en este slot")
                    continue
                
                # ✅ SLOT VÁLIDO ENCONTRADO
# DEBUG: print(f"      ✅ SLOT VÁLIDO - Cancha {cancha_libre.nombre}")
                slot_asignado = (fecha, dia, hora)
                cancha_asignada = cancha_libre
                break
            
            if slot_asignado and cancha_asignada:
                # PROGRAMAR PARTIDO
                fecha, dia, hora = slot_asignado
                fecha_hora_slot = datetime.strptime(f"{fecha} {hora}", '%Y-%m-%d %H:%M')
                
                # Marcar ocupación de cancha
                ocupacion_canchas[(fecha, hora)].append(cancha_asignada.id)
                
                # Registrar partidos de jugadores
                for jugador_id in jugadores:
                    partidos_por_jugador[jugador_id].append(fecha_hora_slot)
                
                # Agregar partido programado
                partidos_programados.append({
                    **partido,
                    "fecha": fecha,
                    "hora": hora,
                    "slot": f"{fecha} {hora}",
                    "cancha_id": cancha_asignada.id,
                    "cancha_nombre": cancha_asignada.nombre
                })
                
            else:
                # NO SE PUDO PROGRAMAR - Agregar a lista de no programados
                # Obtener información detallada para el reporte
                
                # Obtener nombres de jugadores
                pareja1_nombres = "Pareja desconocida"
                pareja2_nombres = "Pareja desconocida"
                
                if pareja1:
                    from ..models.driveplus_models import Usuario
                    j1 = db.query(Usuario).filter(Usuario.id_usuario == pareja1.jugador1_id).first()
                    j2 = db.query(Usuario).filter(Usuario.id_usuario == pareja1.jugador2_id).first()
                    if j1 and j2:
                        pareja1_nombres = f"{j1.nombre_usuario} & {j2.nombre_usuario}"
                
                if pareja2:
                    from ..models.driveplus_models import Usuario
                    j1 = db.query(Usuario).filter(Usuario.id_usuario == pareja2.jugador1_id).first()
                    j2 = db.query(Usuario).filter(Usuario.id_usuario == pareja2.jugador2_id).first()
                    if j1 and j2:
                        pareja2_nombres = f"{j1.nombre_usuario} & {j2.nombre_usuario}"
                
                # Obtener información de la categoría
                categoria_info = "Categoría desconocida"
                if partido.get('categoria_id'):
                    categoria = db.query(TorneoCategoria).filter(TorneoCategoria.id == partido['categoria_id']).first()
                    if categoria:
                        genero_icon = "♂" if categoria.genero == "masculino" else "♀" if categoria.genero == "femenino" else "⚥"
                        categoria_info = f"{genero_icon} {categoria.nombre}"
                
                # Formatear restricciones para mostrar
                def formatear_restricciones(datos):
                    restricciones_por_dia = datos.get('restricciones_por_dia', {})
                    if not restricciones_por_dia:
                        return "Sin restricciones (disponible en todos los horarios del torneo)"
                    
                    result = []
                    for dia, rangos in restricciones_por_dia.items():
                        for inicio_mins, fin_mins in rangos:
                            inicio_str = f"{inicio_mins // 60:02d}:{inicio_mins % 60:02d}"
                            fin_str = f"{fin_mins // 60:02d}:{fin_mins % 60:02d}"
                            result.append(f"NO disponible {dia} {inicio_str}-{fin_str}")
                    return ", ".join(result)
                
                # Agregar a lista de no programados con detalles
                partidos_no_programados.append({
                    "zona_id": partido['zona_id'],
                    "zona_nombre": partido['zona_nombre'],
                    "categoria_id": partido['categoria_id'],
                    "categoria_nombre": categoria_info,
                    "pareja1_id": pareja1_id,
                    "pareja2_id": pareja2_id,
                    "pareja1_nombre": pareja1_nombres,
                    "pareja2_nombre": pareja2_nombres,
                    "motivo": "Sin horarios compatibles o conflicto de tiempo mínimo entre partidos",
                    "disponibilidad_pareja1": formatear_restricciones(datos_pareja1),
                    "disponibilidad_pareja2": formatear_restricciones(datos_pareja2)
                })
        
        return {
            "partidos_programados": partidos_programados,
            "partidos_no_programados": partidos_no_programados
        }
    
    @staticmethod
    def _verificar_disponibilidad_pareja(dia: str, hora_mins: int, datos_pareja: Dict) -> bool:
        """
        Verifica si una pareja está disponible en un día y hora específicos
        
        🔴 SEMÁNTICA CLARA: Verifica que NO esté en ninguna RESTRICCIÓN
        
        Args:
            dia: Día de la semana en español lowercase (lunes, martes, etc.)
            hora_mins: Hora en minutos desde medianoche
            datos_pareja: Dict con 'restricciones_por_dia' {dia: [(inicio, fin)]}
            
        Returns:
            bool: True si está disponible (NO restringido), False si está restringido
        """
        restricciones_por_dia = datos_pareja.get('restricciones_por_dia', {})
        
        # 🔴 LOGGING DETALLADO
# DEBUG: print(f"      🔍 Verificando {dia} {hora_mins//60:02d}:{hora_mins%60:02d}")
# DEBUG: print(f"         Restricciones: {restricciones_por_dia}")
        
        # Sin restricciones = disponible siempre
        if not restricciones_por_dia:
# DEBUG: print(f"         ✅ Sin restricciones → DISPONIBLE")
            return True
        
        # Verificar si el día tiene restricciones
        if dia not in restricciones_por_dia:
# DEBUG: print(f"         ✅ Día sin restricciones → DISPONIBLE")
            return True  # Día sin restricciones = disponible todo el día
        
        # Verificar si la hora está en alguna restricción
        rangos_restringidos = restricciones_por_dia[dia]
# DEBUG: print(f"         Rangos restringidos en {dia}: {rangos_restringidos}")
        
        for inicio_mins, fin_mins in rangos_restringidos:
            # 🔴 FIX CRÍTICO: Verificar solapamiento correcto
            # El partido dura 70 minutos: [hora_mins, hora_mins + 70]
            # La restricción es: [inicio_mins, fin_mins]
            # Hay solapamiento si: partido_inicio < restriccion_fin AND partido_fin > restriccion_inicio
            # Si el partido empieza EXACTAMENTE cuando termina la restricción, NO es conflicto
            partido_fin = hora_mins + 70
            
            # 🔴 CORRECCIÓN: Si el partido empieza ANTES que el fin de la restricción
            # Y el partido termina DESPUÉS del inicio de la restricción
            if hora_mins < fin_mins and partido_fin > inicio_mins:
# DEBUG: print(f"         ❌ SOLAPAMIENTO con restricción {inicio_mins//60:02d}:{inicio_mins%60:02d}-{fin_mins//60:02d}:{fin_mins%60:02d}")
# DEBUG: print(f"            Partido: {hora_mins//60:02d}:{hora_mins%60:02d}-{partido_fin//60:02d}:{partido_fin%60:02d}")
# DEBUG: print(f"            Restricción: {inicio_mins//60:02d}:{inicio_mins%60:02d}-{fin_mins//60:02d}:{fin_mins%60:02d}")
# DEBUG: print(f"            Condición: {hora_mins} <= {fin_mins} AND {partido_fin} > {inicio_mins}")
                return False  # Hay solapamiento = NO disponible
        
# DEBUG: print(f"         ✅ Sin solapamiento → DISPONIBLE")
        return True  # No hay solapamiento con ninguna restricción = disponible
    
    @staticmethod
    def _guardar_partidos(
        db: Session,
        torneo_id: int,
        partidos_programados: List[Dict],
        categoria_id: Optional[int] = None
    ):
        """
        Guarda los partidos programados en la base de datos
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            partidos_programados: Lista de partidos a guardar
            categoria_id: (Opcional) Si se especifica, solo elimina partidos de esa categoría antes de guardar
        """
        # Eliminar partidos existentes de fase de grupos
        query = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase == 'zona'
        )
        
        # Filtrar por categoría si se especifica
        if categoria_id:
            query = query.filter(Partido.categoria_id == categoria_id)
        
        query.delete()
        db.commit()
        
        # Crear nuevos partidos
        # Get tournament creator for id_creador
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        
        for i, partido_data in enumerate(partidos_programados):
            fecha_hora_str = f"{partido_data['fecha']} {partido_data['hora']}:00"
            # Crear datetime naive (sin timezone) para evitar conversiones UTC
            fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M:%S')
            
            partido = Partido(
                id_torneo=torneo_id,
                zona_id=partido_data['zona_id'],
                fase='zona',
                numero_partido=i + 1,
                pareja1_id=partido_data['pareja1_id'],
                pareja2_id=partido_data['pareja2_id'],
                cancha_id=partido_data['cancha_id'],
                fecha_hora=fecha_hora,
                fecha=fecha_hora,  # Also set fecha field
                estado='pendiente',
                tipo='torneo',
                id_creador=torneo.creado_por if torneo else 1,
                categoria_id=partido_data.get('categoria_id')
            )
            db.add(partido)
        
        db.commit()
