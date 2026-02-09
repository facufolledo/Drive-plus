"""
Configuración del algoritmo Elo avanzado para pádel 2 vs 2
Todos los parámetros son ajustables para optimizar el sistema según las necesidades
"""

from typing import Dict, Tuple
from enum import Enum

class Desenlace(str, Enum):
    """
    Enum para los diferentes tipos de desenlace de partido
    """
    NORMAL = "normal"
    WO_EQ1 = "wo_eq1"  # Walk Over ganado por equipo 1
    WO_EQ2 = "wo_eq2"  # Walk Over ganado por equipo 2
    RET_EQ1 = "ret_eq1"  # Retiro ganado por equipo 1
    RET_EQ2 = "ret_eq2"  # Retiro ganado por equipo 2

class EloConfig:
    """
    Configuración centralizada para el algoritmo Elo avanzado
    Permite ajustar todos los parámetros del sistema de rating
    """
    
    # === PARÁMETROS BÁSICOS ===
    
    # Escala Elo estándar (ajustar para cambiar sensibilidad)
    ELO_SCALE = 400
    
    # === FACTORES K POR EXPERIENCIA ===
    
    # Rangos de partidos jugados y sus factores K correspondientes (AUMENTADOS PARA PRINCIPIANTES)
    # Objetivo: Permitir que jugadores iniciales suban ~50 puntos por victoria
    # Un jugador principiante que gana debería subir aproximadamente 40-60 puntos
    K_FACTORS = {
        "nuevo": {
            "max_partidos": 15,
            "k_value": 400   # Muy alto para principiantes (0-15 partidos) - sube ~50 pts por victoria
        },
        "intermedio": {
            "max_partidos": 30,
            "k_value": 300   # Alto para jugadores con experiencia media (16-30 partidos)
        },
        "estable": {
            "max_partidos": 60,
            "k_value": 200   # Moderado para jugadores establecidos (31-60 partidos)
        },
        "experto": {
            "max_partidos": float('inf'),  # Sin límite superior
            "k_value": 150   # Más bajo para expertos (61+ partidos)
        }
    }
    
    # === MULTIPLICADORES POR SETS ===
    
    # Multiplicador por cada set de diferencia
    SETS_MULTIPLIER = 0.1
    
    # === MARGEN DE GAMES ===
    
    # Cap para el margen de games (evita que dominen el resultado)
    GAMES_MARGIN_CAP = 0.15
    
    # Multiplicador para el margen de games
    GAMES_MULTIPLIER = 0.3
    
    # Número mínimo de games para considerar el margen
    MIN_TOTAL_GAMES = 12
    
    # === SUAVIZADOR DE DERROTAS ===
    
    # Piso del suavizador (mínimo castigo para favoritos)
    FAVORITE_LOSS_FLOOR = 0.6
    
    # Techo del suavizador (máximo castigo para favoritos)
    FAVORITE_LOSS_CEILING = 1.0
    
    # === CAPS POR ROL ===
    
    # Caps para underdogs (mayor premio por victoria) - AJUSTADOS PARA MAYOR ESTABILIDAD
    UNDERDOG_CAPS = {
        "win": 15,    # Máximo ganancia (reducido de 35 a 15)
        "loss": -12   # Máximo pérdida (reducido de -25 a -12)
    }
    
    # Caps para favoritos (castigo moderado por derrota) - AJUSTADOS PARA MAYOR ESTABILIDAD
    FAVORITE_CAPS = {
        "win": 12,    # Máximo ganancia (reducido de 25 a 12)
        "loss": -15   # Máximo pérdida (reducido de -35 a -15)
    }
    
    # === NUEVO: CONFIABILIDAD/VOLATILIDAD ===
    
    # Límites de volatilidad
    VOLATILIDAD_MIN = 0.7
    VOLATILIDAD_MAX = 1.3
    
    # Factores de ajuste de volatilidad
    VOLATILIDAD_DOWN_FACTOR = 0.98   # cumple expectativas
    VOLATILIDAD_UP_FACTOR = 1.02     # resultado sorpresivo
    
    # Umbrales para ajustar volatilidad
    VOLATILIDAD_STABLE_THRESHOLD = 0.15  # Si |S-E| < 0.15, estabilizar
    VOLATILIDAD_VOLATILE_THRESHOLD = 0.35  # Si |S-E| > 0.35, aumentar volatilidad
    
    # === NUEVO: ANTI-ABUSO ===
    
    # Configuración para detectar abuso de partidos repetidos
    ABUSE_CHECK_WINDOW_H = 48  # Ventana de tiempo en horas
    ABUSE_SAME4_THRESHOLD = 3  # Número de partidos con mismos 4 jugadores
    ABUSE_MULTIPLIER = 0.5     # Multiplicador para reducir impacto
    
    # === NUEVO: TIPOS DE PARTIDO ===
    
    # Caps según tipo de partido - BALANCEADOS PARA TORNEOS (60% SUBA)
    MATCH_TYPE_CAPS = {
        "amistoso": {"win": 15, "loss": -15},    # Partidos casuales (ajustado para ser más significativo)
        "torneo": {"win": 100, "loss": -50},   # Partidos de torneo (recompensa muy alta)
        "final": {"win": 140, "loss": -70},    # Finales de torneo (1.4x que semifinal)
        "zona": {"win": 75, "loss": -38},      # Partidos de zona
        "cuartos": {"win": 80, "loss": -40},   # Cuartos de final
        "semi": {"win": 100, "loss": -50}      # Semifinales
    }
    
    # === NUEVO: CAPS POR CATEGORÍA DE ORIGEN ===
    
    # Caps específicos según la categoría de origen del jugador.
    # AUMENTADOS para permitir mayor movilidad en categorías bajas
    CATEGORY_ORIGIN_CAPS = {
        "Principiante": {"win": 100, "loss": -50},  # Aumentado de 50 a 100 para permitir subidas rápidas
        "8va": {"win": 80, "loss": -40},            # Aumentado de 50 a 80
        "7ma": {"win": 70, "loss": -35},            # Aumentado de 50 a 70
        "6ta": {"win": 60, "loss": -30},            # Aumentado de 50 a 60
        "5ta": {"win": 50, "loss": -25},            # Mantenido en 50
        "4ta": {"win": 50, "loss": -25},            # Mantenido en 50
        "Libre": {"win": 40, "loss": -20}           # Mantenido en 40
    }
    
    # === NUEVO: INACTIVIDAD ===
    
    # Decay por inactividad
    DECAY_PER_MONTH = 0.005   # 0.5% por mes
    
    # === NUEVO: SISTEMA DE BLOQUEO TEMPORAL DE K ===
    
    # Bloqueo temporal de K para evitar abuso de partidos consecutivos
    K_LOCK_WINDOW_H = 4        # Ventana de tiempo en horas
    K_LOCK_MATCHES = 3         # Número de partidos que activan el bloqueo
    K_LOCK_MULTIPLIER = 0.5    # Multiplicador de K cuando está bloqueado
    
    # === NUEVO: LÍMITE DE PARTIDOS POR DÍA ===
    
    # Límite máximo de partidos por día para evitar farmeo
    MAX_MATCHES_PER_DAY = 5    # Después de esto, K = 0
    
    # === NUEVO: BONUS Y PENALIZACIONES ===
    
    # Bonus por victoria sorpresiva (S-E > 0.6)
    SURPRISE_VICTORY_THRESHOLD = 0.6
    SURPRISE_VICTORY_BONUS = 0.05  # +5% del K final
    
    # Penalización por derrota sin sets ganados (6-0 6-0)
    TOTAL_LOSS_PENALTY = 1.10  # Pierden un 10% más si fue paliza total
    
    # === NUEVO: AJUSTE DE VOLATILIDAD POR RACHA ===
    
    # Ajuste de volatilidad según rachas de victorias siendo underdog
    STREAK_VOLATILITY_BOOST = 0.1  # Incremento de volatilidad por racha
    STREAK_THRESHOLD = 3           # Número de victorias seguidas para activar boost
    
    # === NUEVO: INMUNIDAD POST-ASCENSO ===
    
    # Sistema de inmunidad post-ascenso para evitar bajadas inmediatas
    POST_ASCENSION_IMMUNITY_MATCHES = 2  # Número de partidos con inmunidad
    POST_ASCENSION_MAX_LOSS = 0.3        # Máximo 30% de pérdida normal
    
    # === NUEVO: SOPORTE PARA REVISIÓN MANUAL ===
    
    # Flag para override manual de S y E
    MANUAL_OVERRIDE_ENABLED = True
    DECAY_MAX = 0.05          # 5% máximo
    
    # === NUEVO: BONUS POR MARGEN ===
    
    # Bonus por sets dominantes
    DOMINANT_SET_BONUS = 0.05  # Bonus si hay set 6-0 o 6-1
    
    # Reducción por tie-breaks
    TIEBREAK_REDUCTION = 0.7   # Reducir margen si hay 7-6
    
    # === CONFIGURACIONES ESPECIALES ===
    
    # Configuración para Walk Over
    WO_CONFIG = {
        "winner_score": 1.0,
        "loser_score": 0.0
    }
    
    # Configuración para Retiro
    RETIREMENT_CONFIG = {
        "default_score": 0.5,  # Score por defecto si no hay sets jugados
        "use_games": False     # Si considerar games en caso de retiro
    }
    
    # === VALIDACIONES ===
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Valida que la configuración sea coherente
        
        Returns:
            bool: True si la configuración es válida
        """
        try:
            # Validar factores K
            if cls.K_FACTORS["nuevo"]["max_partidos"] >= cls.K_FACTORS["intermedio"]["max_partidos"]:
                return False
            
            if cls.K_FACTORS["intermedio"]["max_partidos"] >= cls.K_FACTORS["estable"]["max_partidos"]:
                return False
            
            if cls.K_FACTORS["estable"]["max_partidos"] >= cls.K_FACTORS["experto"]["max_partidos"]:
                return False
            
            # Validar suavizador
            if cls.FAVORITE_LOSS_FLOOR >= cls.FAVORITE_LOSS_CEILING:
                return False
            
            if cls.FAVORITE_LOSS_FLOOR < 0 or cls.FAVORITE_LOSS_CEILING > 1:
                return False
            
            # Validar caps
            if cls.UNDERDOG_CAPS["win"] <= 0 or cls.UNDERDOG_CAPS["loss"] >= 0:
                return False
            
            if cls.FAVORITE_CAPS["win"] <= 0 or cls.FAVORITE_CAPS["loss"] >= 0:
                return False
            
            # Validar multiplicadores
            if cls.SETS_MULTIPLIER < 0:
                return False
            
            if cls.GAMES_MARGIN_CAP < 0 or cls.GAMES_MULTIPLIER < 0:
                return False
            
            # Validar volatilidad
            if cls.VOLATILIDAD_MIN >= cls.VOLATILIDAD_MAX:
                return False
            
            if cls.VOLATILIDAD_DOWN_FACTOR >= 1.0 or cls.VOLATILIDAD_UP_FACTOR <= 1.0:
                return False
            
            # Validar anti-abuso
            if cls.ABUSE_MULTIPLIER <= 0 or cls.ABUSE_MULTIPLIER > 1:
                return False
            
            # Validar decay
            if cls.DECAY_PER_MONTH < 0 or cls.DECAY_MAX < 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def get_k_factor(cls, partidos_jugados: int) -> int:
        """
        Obtiene el factor K basado en la experiencia del jugador
        
        Args:
            partidos_jugados: Número de partidos jugados
            
        Returns:
            int: Factor K correspondiente
        """
        for level, config in cls.K_FACTORS.items():
            if partidos_jugados <= config["max_partidos"]:
                return config["k_value"]
        
        # Fallback al valor experto
        return cls.K_FACTORS["experto"]["k_value"]
    
    @classmethod
    def get_role_caps(cls, team_rating: float, opponent_rating: float) -> Tuple[float, float]:
        """
        Obtiene los caps según el rol del equipo
        
        Args:
            team_rating: Rating del equipo
            opponent_rating: Rating del oponente
            
        Returns:
            Tuple[float, float]: (cap_win, cap_loss)
        """
        if team_rating < opponent_rating:
            # Underdog
            return cls.UNDERDOG_CAPS["win"], cls.UNDERDOG_CAPS["loss"]
        else:
            # Favorito
            return cls.FAVORITE_CAPS["win"], cls.FAVORITE_CAPS["loss"]
    
    @classmethod
    def k_with_volatility(cls, k_base: float, vol: float) -> float:
        """
        Aplica volatilidad al factor K base
        
        Args:
            k_base: Factor K base por experiencia
            vol: Factor de volatilidad del jugador
            
        Returns:
            float: Factor K ajustado por volatilidad
        """
        from math import isfinite
        v = vol if isfinite(vol) else 1.0
        v = max(cls.VOLATILIDAD_MIN, min(cls.VOLATILIDAD_MAX, v))
        return k_base * v
    
    @classmethod
    def get_category_origin_caps(cls, team_rating: float) -> Tuple[float, float]:
        """
        Obtiene caps según la categoría de origen del jugador
        
        Args:
            team_rating: Rating del equipo
            
        Returns:
            Tuple[float, float]: (cap_win, cap_loss)
        """
        # Determinar categoría por rating
        if team_rating >= 1800:
            category = "Libre"
        elif team_rating >= 1600:
            category = "4ta"
        elif team_rating >= 1400:
            category = "5ta"
        elif team_rating >= 1200:
            category = "6ta"
        elif team_rating >= 1000:
            category = "7ma"
        elif team_rating >= 500:
            category = "8va"
        else:
            category = "Principiante"
        
        # Obtener caps de la categoría
        caps = cls.CATEGORY_ORIGIN_CAPS.get(category, {"win": 100, "loss": -50})
        return caps["win"], caps["loss"]
    
    @classmethod
    def caps_for_match_type(cls, tipo: str, team_rating: float, opp_rating: float) -> Tuple[float, float]:
        """
        Obtiene caps según tipo de partido (PRIORIDAD A CATEGORÍA DE ORIGEN PARA TORNEOS)
        
        Args:
            tipo: Tipo de partido (amistoso, torneo, final, zona, cuartos, semi)
            team_rating: Rating del equipo
            opp_rating: Rating del oponente
            
        Returns:
            Tuple[float, float]: (cap_win, cap_loss)
        """
        # Para partidos de torneo, usar caps por categoría de origen
        if tipo in ["torneo", "final", "zona", "cuartos", "semi"]:
            return cls.get_category_origin_caps(team_rating)
        
        # Para partidos amistosos, usar caps por tipo de partido
        mt = cls.MATCH_TYPE_CAPS.get(tipo)
        if mt:
            return mt["win"], mt["loss"]
        
        # Fallback a caps por rol solo si no hay tipo específico
        return cls.get_role_caps(team_rating, opp_rating)
    
    @classmethod
    def get_config_summary(cls) -> Dict:
        """
        Obtiene un resumen de la configuración actual
        
        Returns:
            Dict: Resumen de la configuración
        """
        return {
            "elo_scale": cls.ELO_SCALE,
            "k_factors": cls.K_FACTORS,
            "sets_multiplier": cls.SETS_MULTIPLIER,
            "games_margin_cap": cls.GAMES_MARGIN_CAP,
            "games_multiplier": cls.GAMES_MULTIPLIER,
            "min_total_games": cls.MIN_TOTAL_GAMES,
            "favorite_loss_floor": cls.FAVORITE_LOSS_FLOOR,
            "favorite_loss_ceiling": cls.FAVORITE_LOSS_CEILING,
            "underdog_caps": cls.UNDERDOG_CAPS,
            "favorite_caps": cls.FAVORITE_CAPS,
            "volatilidad_min": cls.VOLATILIDAD_MIN,
            "volatilidad_max": cls.VOLATILIDAD_MAX,
            "abuse_multiplier": cls.ABUSE_MULTIPLIER,
            "match_type_caps": cls.MATCH_TYPE_CAPS,
            "decay_per_month": cls.DECAY_PER_MONTH,
            "decay_max": cls.DECAY_MAX,
            "dominant_set_bonus": cls.DOMINANT_SET_BONUS,
            "tiebreak_reduction": cls.TIEBREAK_REDUCTION,
            "wo_config": cls.WO_CONFIG,
            "retirement_config": cls.RETIREMENT_CONFIG,
            "is_valid": cls.validate_config()
        }

# Configuraciones predefinidas para diferentes tipos de torneos
class TournamentConfigs:
    """
    Configuraciones predefinidas para diferentes tipos de torneos
    """
    
    @staticmethod
    def get_amateur_config() -> Dict:
        """Configuración para torneos amateur (más volátil)"""
        return {
            "k_factors": {
                "nuevo": {"max_partidos": 3, "k_value": 56},
                "intermedio": {"max_partidos": 10, "k_value": 48},
                "estable": {"max_partidos": 25, "k_value": 40},
                "experto": {"max_partidos": float('inf'), "k_value": 32}
            },
            "sets_multiplier": 0.15,
            "games_margin_cap": 0.20,
            "underdog_caps": {"win": 40, "loss": -30},
            "favorite_caps": {"win": 30, "loss": -40},
            "volatilidad_min": 0.6,
            "volatilidad_max": 1.4,
            "dominant_set_bonus": 0.08,
            "match_type_caps": {
                "amistoso": {"win": 20, "loss": -20},
                "torneo": {"win": 40, "loss": -30},
                "final": {"win": 45, "loss": -35}
            }
        }
    
    @staticmethod
    def get_professional_config() -> Dict:
        """Configuración para torneos profesionales (más estable)"""
        return {
            "k_factors": {
                "nuevo": {"max_partidos": 10, "k_value": 40},
                "intermedio": {"max_partidos": 25, "k_value": 32},
                "estable": {"max_partidos": 50, "k_value": 24},
                "experto": {"max_partidos": float('inf'), "k_value": 16}
            },
            "sets_multiplier": 0.08,
            "games_margin_cap": 0.12,
            "underdog_caps": {"win": 30, "loss": -20},
            "favorite_caps": {"win": 20, "loss": -30},
            "volatilidad_min": 0.8,
            "volatilidad_max": 1.2,
            "dominant_set_bonus": 0.03,
            "match_type_caps": {
                "amistoso": {"win": 10, "loss": -10},
                "torneo": {"win": 30, "loss": -20},
                "final": {"win": 33, "loss": -22}
            }
        }
    
    @staticmethod
    def get_development_config() -> Dict:
        """Configuración para desarrollo y pruebas (máxima volatilidad)"""
        return {
            "k_factors": {
                "nuevo": {"max_partidos": 2, "k_value": 64},
                "intermedio": {"max_partidos": 5, "k_value": 56},
                "estable": {"max_partidos": 15, "k_value": 48},
                "experto": {"max_partidos": float('inf'), "k_value": 40}
            },
            "sets_multiplier": 0.20,
            "games_margin_cap": 0.25,
            "underdog_caps": {"win": 50, "loss": -35},
            "favorite_caps": {"win": 35, "loss": -50},
            "volatilidad_min": 0.5,
            "volatilidad_max": 1.5,
            "dominant_set_bonus": 0.10,
            "match_type_caps": {
                "amistoso": {"win": 25, "loss": -25},
                "torneo": {"win": 50, "loss": -35},
                "final": {"win": 55, "loss": -40}
            }
        }

# Función para aplicar configuración personalizada
def apply_custom_config(config_dict: Dict) -> None:
    """
    Aplica una configuración personalizada al algoritmo Elo
    
    Args:
        config_dict: Diccionario con la nueva configuración
    """
    for key, value in config_dict.items():
        if hasattr(EloConfig, key.upper()):
            setattr(EloConfig, key.upper(), value)
        elif hasattr(EloConfig, key):
            setattr(EloConfig, key, value)
        else:
            print(f"Advertencia: Parámetro '{key}' no reconocido")

# === NUEVAS FUNCIONES DE CONFIGURACIÓN ===

def get_config_summary() -> Dict:
    """Obtener resumen de la configuración actual"""
    return {
        "elo_scale": EloConfig.ELO_SCALE,
        "k_factors": EloConfig.K_FACTORS,
        "sets_multiplier": EloConfig.SETS_MULTIPLIER,
        "games_margin_cap": EloConfig.GAMES_MARGIN_CAP,
        "games_multiplier": EloConfig.GAMES_MULTIPLIER,
        "min_total_games": EloConfig.MIN_TOTAL_GAMES,
        "favorite_loss_floor": EloConfig.FAVORITE_LOSS_FLOOR,
        "favorite_loss_ceiling": EloConfig.FAVORITE_LOSS_CEILING,

        # Caps generales por rol
        "underdog_caps": EloConfig.UNDERDOG_CAPS,
        "favorite_caps": EloConfig.FAVORITE_CAPS,

        # Volatilidad
        "volatilidad_min": EloConfig.VOLATILIDAD_MIN,
        "volatilidad_max": EloConfig.VOLATILIDAD_MAX,
        "volatilidad_down_factor": EloConfig.VOLATILIDAD_DOWN_FACTOR,
        "volatilidad_up_factor": EloConfig.VOLATILIDAD_UP_FACTOR,
        "volatilidad_stable_threshold": EloConfig.VOLATILIDAD_STABLE_THRESHOLD,
        "volatilidad_volatile_threshold": EloConfig.VOLATILIDAD_VOLATILE_THRESHOLD,

        # Anti-abuso
        "abuse_check_window_h": EloConfig.ABUSE_CHECK_WINDOW_H,
        "abuse_same4_threshold": EloConfig.ABUSE_SAME4_THRESHOLD,
        "abuse_multiplier": EloConfig.ABUSE_MULTIPLIER,

        # Caps por tipo de partido y por categoría de origen
        "match_type_caps": EloConfig.MATCH_TYPE_CAPS,
        "category_origin_caps": EloConfig.CATEGORY_ORIGIN_CAPS,

        # Inactividad
        "decay_per_month": EloConfig.DECAY_PER_MONTH,
        "decay_max": EloConfig.DECAY_MAX,

        # Bonus por margen
        "dominant_set_bonus": EloConfig.DOMINANT_SET_BONUS,
        "tiebreak_reduction": EloConfig.TIEBREAK_REDUCTION,

        # Sistema de bloqueo temporal de K y límite diario
        "k_lock_window_h": EloConfig.K_LOCK_WINDOW_H,
        "k_lock_matches": EloConfig.K_LOCK_MATCHES,
        "k_lock_multiplier": EloConfig.K_LOCK_MULTIPLIER,
        "max_matches_per_day": EloConfig.MAX_MATCHES_PER_DAY,

        # Bonus/penalizaciones
        "surprise_victory_threshold": EloConfig.SURPRISE_VICTORY_THRESHOLD,
        "surprise_victory_bonus": EloConfig.SURPRISE_VICTORY_BONUS,
        "total_loss_penalty": EloConfig.TOTAL_LOSS_PENALTY,

        # Rachas e inmunidad post-ascenso
        "streak_volatility_boost": EloConfig.STREAK_VOLATILITY_BOOST,
        "streak_threshold": EloConfig.STREAK_THRESHOLD,
        "post_ascension_immunity_matches": EloConfig.POST_ASCENSION_IMMUNITY_MATCHES,
        "post_ascension_max_loss": EloConfig.POST_ASCENSION_MAX_LOSS,

        # Overrides y especiales
        "manual_override_enabled": EloConfig.MANUAL_OVERRIDE_ENABLED,
        "wo_config": EloConfig.WO_CONFIG,
        "retirement_config": EloConfig.RETIREMENT_CONFIG,
    }

def export_config_to_json(filename="elo_config.json"):
    """Exportar configuración ELO como archivo JSON"""
    import json
    import os
    
    config = get_config_summary()
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    return filename


# Función utilitaria para clamp
def clamp(x: float, lo: float, hi: float) -> float:
    """
    Función utilitaria para limitar un valor entre un mínimo y máximo
    
    Args:
        x: Valor a limitar
        lo: Límite inferior
        hi: Límite superior
        
    Returns:
        float: Valor limitado
    """
    return max(lo, min(hi, x))

