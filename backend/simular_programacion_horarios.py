"""
Script de simulación de programación de horarios
NO TOCA LA BASE DE DATOS - Solo simula en memoria
"""
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import random

class SimuladorProgramacionHorarios:
    """Simula la programación de partidos respetando horarios"""
    
    DURACION_PARTIDO_MINUTOS = 70
    
    def __init__(self):
        self.parejas = []
        self.horarios_torneo = {}
        self.canchas = []
        self.partidos_programados = []
        self.partidos_sin_programar = []
    
    def configurar_torneo(self, horarios: Dict):
        """
        Configurar horarios del torneo
        
        Formato:
        {
            "lunes": [{"desde": "18:00", "hasta": "23:00"}],
            "martes": [{"desde": "18:00", "hasta": "23:00"}],
            ...
        }
        """
        self.horarios_torneo = horarios
        print(f"✅ Horarios del torneo configurados:")
        for dia, franjas in horarios.items():
            for franja in franjas:
                print(f"   • {dia.capitalize()}: {franja['desde']} - {franja['hasta']}")
    
    def agregar_canchas(self, num_canchas: int):
        """Agregar canchas disponibles"""
        self.canchas = [f"Cancha {i+1}" for i in range(num_canchas)]
        print(f"\n✅ {num_canchas} canchas configuradas: {', '.join(self.canchas)}")
    
    def agregar_pareja(self, nombre: str, disponibilidad: Dict = None):
        """
        Agregar pareja con su disponibilidad
        
        Formato disponibilidad:
        {
            "franjas": [
                {"dias": ["lunes", "martes"], "horaInicio": "18:00", "horaFin": "22:00"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "23:00"}
            ]
        }
        
        Si disponibilidad es None, la pareja está disponible en todos los horarios del torneo
        """
        pareja_id = len(self.parejas) + 1
        slots = self._extraer_slots_disponibles(disponibilidad or {})
        
        self.parejas.append({
            "id": pareja_id,
            "nombre": nombre,
            "disponibilidad": disponibilidad,
            "slots": slots
        })
        
        print(f"\n✅ Pareja agregada: {nombre}")
        if disponibilidad:
            print(f"   Restricciones horarias:")
            for franja in disponibilidad.get('franjas', []):
                dias_str = ', '.join([d.capitalize() for d in franja['dias']])
                print(f"   • {dias_str}: {franja['horaInicio']} - {franja['horaFin']}")
        else:
            print(f"   Sin restricciones (disponible en todos los horarios del torneo)")
        print(f"   Total slots disponibles: {len(slots)}")
    
    def _extraer_slots_disponibles(self, disponibilidad: Dict) -> Set[Tuple[str, str]]:
        """Extrae slots de tiempo disponibles para una pareja"""
        slots = set()
        
        # Si no tiene disponibilidad, usar todos los horarios del torneo
        if not disponibilidad or not disponibilidad.get('franjas'):
            for dia, franjas in self.horarios_torneo.items():
                for franja in franjas:
                    desde = franja['desde']
                    hasta = franja['hasta']
                    hora_actual = self._parse_hora(desde)
                    hora_fin = self._parse_hora(hasta)
                    while hora_actual < hora_fin:
                        slots.add((dia, hora_actual.strftime('%H:%M')))
                        hora_actual += timedelta(minutes=self.DURACION_PARTIDO_MINUTOS)
            return slots
        
        # Procesar disponibilidad específica
        for franja in disponibilidad.get('franjas', []):
            dias = franja.get('dias', [])
            hora_inicio = franja.get('horaInicio', '08:00')
            hora_fin = franja.get('horaFin', '23:00')
            
            for dia in dias:
                # Verificar que el día esté en los horarios del torneo
                if dia not in self.horarios_torneo:
                    continue
                
                # Intersectar con horarios del torneo
                for franja_torneo in self.horarios_torneo[dia]:
                    inicio_torneo = self._parse_hora(franja_torneo['desde'])
                    fin_torneo = self._parse_hora(franja_torneo['hasta'])
                    inicio_pareja = self._parse_hora(hora_inicio)
                    fin_pareja = self._parse_hora(hora_fin)
                    
                    # Calcular intersección
                    inicio_real = max(inicio_torneo, inicio_pareja)
                    fin_real = min(fin_torneo, fin_pareja)
                    
                    if inicio_real < fin_real:
                        hora_actual = inicio_real
                        while hora_actual < fin_real:
                            slots.add((dia, hora_actual.strftime('%H:%M')))
                            hora_actual += timedelta(minutes=self.DURACION_PARTIDO_MINUTOS)
        
        return slots
    
    def _parse_hora(self, hora_str: str) -> datetime:
        """Convierte string de hora a datetime"""
        try:
            return datetime.strptime(hora_str, '%H:%M')
        except:
            return datetime.strptime('08:00', '%H:%M')
    
    def _calcular_compatibilidad(self, pareja1: Dict, pareja2: Dict) -> float:
        """Calcula compatibilidad horaria entre dos parejas (0.0 a 1.0)"""
        slots1 = pareja1['slots']
        slots2 = pareja2['slots']
        
        if not slots1 or not slots2:
            return 1.0
        
        interseccion = slots1 & slots2
        union = slots1 | slots2
        
        if not union:
            return 0.0
        
        return len(interseccion) / len(union)
    
    def generar_fixture_zona(self, parejas_zona: List[Dict]) -> List[Dict]:
        """Genera fixture round-robin para una zona (todos contra todos)"""
        n = len(parejas_zona)
        if n < 2:
            return []
        
        partidos = []
        
        # Generar todos los enfrentamientos posibles (round-robin completo)
        for i in range(n):
            for j in range(i + 1, n):
                local = parejas_zona[i]
                visitante = parejas_zona[j]
                
                # Verificar que no sea el mismo equipo
                if local['id'] == visitante['id']:
                    continue
                
                partidos.append({
                    "ronda": len(partidos) // (n // 2) + 1 if n > 2 else 1,
                    "local": local,
                    "visitante": visitante,
                    "slots_compatibles": local['slots'] & visitante['slots']
                })
        
        return partidos
    
    def programar_partidos(self, partidos: List[Dict]) -> List[Dict]:
        """
        Programa partidos en slots específicos respetando:
        1. Disponibilidad de ambas parejas
        2. Disponibilidad de canchas
        3. Horarios del torneo
        """
        # Crear calendario de canchas
        calendario = defaultdict(lambda: defaultdict(list))  # {dia: {hora: [canchas_ocupadas]}}
        
        partidos_programados = []
        partidos_sin_programar = []
        
        for partido in partidos:
            slots_compatibles = list(partido['slots_compatibles'])
            
            if not slots_compatibles:
                partidos_sin_programar.append({
                    **partido,
                    "motivo": "Sin horarios compatibles entre las parejas"
                })
                continue
            
            # Intentar asignar a un slot
            programado = False
            random.shuffle(slots_compatibles)  # Aleatorizar para mejor distribución
            
            for dia, hora in slots_compatibles:
                # Verificar si hay cancha disponible
                canchas_ocupadas = calendario[dia][hora]
                canchas_disponibles = [c for c in self.canchas if c not in canchas_ocupadas]
                
                if canchas_disponibles:
                    cancha = canchas_disponibles[0]
                    calendario[dia][hora].append(cancha)
                    
                    partidos_programados.append({
                        **partido,
                        "dia": dia,
                        "hora": hora,
                        "cancha": cancha,
                        "programado": True
                    })
                    programado = True
                    break
            
            if not programado:
                partidos_sin_programar.append({
                    **partido,
                    "motivo": "No hay canchas disponibles en horarios compatibles"
                })
        
        return partidos_programados, partidos_sin_programar
    
    def simular(self):
        """Ejecuta la simulación completa"""
        print(f"\n{'='*80}")
        print(f"SIMULACIÓN DE PROGRAMACIÓN DE HORARIOS")
        print(f"{'='*80}\n")
        
        if len(self.parejas) < 2:
            print("❌ Se necesitan al menos 2 parejas para simular")
            self.partidos_programados = []
            self.partidos_sin_programar = []
            return
        
        # Analizar compatibilidad entre parejas (solo mostrar algunas)
        print(f"\n📊 ANÁLISIS DE COMPATIBILIDAD HORARIA (muestra)")
        print(f"{'─'*80}")
        
        compatibilidades = []
        for i, p1 in enumerate(self.parejas):
            for j, p2 in enumerate(self.parejas):
                if i < j:
                    compat = self._calcular_compatibilidad(p1, p2)
                    compatibilidades.append((p1['nombre'], p2['nombre'], compat))
        
        # Mostrar solo las primeras 10 y las últimas 5
        for nombre1, nombre2, compat in compatibilidades[:10]:
            emoji = "✅" if compat > 0.7 else "⚠️" if compat > 0.3 else "❌"
            print(f"{emoji} {nombre1} vs {nombre2}: {compat*100:.1f}% compatible")
        
        if len(compatibilidades) > 15:
            print(f"... ({len(compatibilidades) - 15} comparaciones más)")
            for nombre1, nombre2, compat in compatibilidades[-5:]:
                emoji = "✅" if compat > 0.7 else "⚠️" if compat > 0.3 else "❌"
                print(f"{emoji} {nombre1} vs {nombre2}: {compat*100:.1f}% compatible")
        
        # Generar fixture (simulamos 1 zona con todas las parejas)
        print(f"\n🎯 GENERANDO FIXTURE")
        print(f"{'─'*80}")
        
        partidos = self.generar_fixture_zona(self.parejas)
        print(f"✅ {len(partidos)} partidos generados")
        
        # Programar partidos
        print(f"\n📅 PROGRAMANDO PARTIDOS EN HORARIOS")
        print(f"{'─'*80}")
        
        programados, sin_programar = self.programar_partidos(partidos)
        
        # Guardar como atributos de la clase
        self.partidos_programados = programados
        self.partidos_sin_programar = sin_programar
        
        # Resultados
        print(f"\n{'='*80}")
        print(f"RESULTADOS DE LA SIMULACIÓN")
        print(f"{'='*80}\n")
        
        print(f"✅ Partidos programados: {len(programados)}/{len(partidos)} ({len(programados)/len(partidos)*100:.1f}%)")
        print(f"❌ Partidos sin programar: {len(sin_programar)}/{len(partidos)} ({len(sin_programar)/len(partidos)*100:.1f}%)")
        
        if programados and len(programados) <= 20:
            print(f"\n📋 PARTIDOS PROGRAMADOS:")
            print(f"{'─'*80}")
            for p in programados:
                print(f"• {p['local']['nombre']} vs {p['visitante']['nombre']}")
                print(f"  {p['dia'].capitalize()} {p['hora']} - {p['cancha']}")
        elif programados:
            print(f"\n📋 PRIMEROS 10 PARTIDOS PROGRAMADOS:")
            print(f"{'─'*80}")
            for p in programados[:10]:
                print(f"• {p['local']['nombre']} vs {p['visitante']['nombre']}")
                print(f"  {p['dia'].capitalize()} {p['hora']} - {p['cancha']}")
            print(f"\n... y {len(programados) - 10} partidos más")
        
        if sin_programar and len(sin_programar) <= 20:
            print(f"\n⚠️  PARTIDOS SIN PROGRAMAR:")
            print(f"{'─'*80}")
            for p in sin_programar:
                print(f"• {p['local']['nombre']} vs {p['visitante']['nombre']}")
                print(f"  Motivo: {p['motivo']}")
                slots = list(p['slots_compatibles'])
                if slots:
                    print(f"  Slots compatibles: {len(slots)}")
        elif sin_programar:
            print(f"\n⚠️  PRIMEROS 10 PARTIDOS SIN PROGRAMAR:")
            print(f"{'─'*80}")
            for p in sin_programar[:10]:
                print(f"• {p['local']['nombre']} vs {p['visitante']['nombre']}")
                print(f"  Motivo: {p['motivo']}")
            print(f"\n... y {len(sin_programar) - 10} partidos más sin programar")
        
        print()


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    sim = SimuladorProgramacionHorarios()
    
    # 1. Configurar horarios del torneo
    sim.configurar_torneo({
        "viernes": [{"desde": "18:00", "hasta": "23:00"}],
        "sabado": [{"desde": "09:00", "hasta": "23:00"}],
        "domingo": [{"desde": "09:00", "hasta": "23:00"}]
    })
    
    # 2. Configurar canchas
    sim.agregar_canchas(3)
    
    # 3. Agregar parejas con sus restricciones
    
    # Pareja 1: Solo puede viernes y sábado tarde
    sim.agregar_pareja("Juan/Pedro", {
        "franjas": [
            {"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "23:00"},
            {"dias": ["sabado"], "horaInicio": "18:00", "horaFin": "23:00"}
        ]
    })
    
    # Pareja 2: Solo puede sábado y domingo mañana
    sim.agregar_pareja("Carlos/Luis", {
        "franjas": [
            {"dias": ["sabado", "domingo"], "horaInicio": "09:00", "horaFin": "14:00"}
        ]
    })
    
    # Pareja 3: Disponible todo el torneo
    sim.agregar_pareja("Ana/María", None)
    
    # Pareja 4: Solo domingos
    sim.agregar_pareja("Diego/Martín", {
        "franjas": [
            {"dias": ["domingo"], "horaInicio": "09:00", "horaFin": "23:00"}
        ]
    })
    
    # 4. Ejecutar simulación
    sim.simular()
