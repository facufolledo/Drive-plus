import math
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from .elo_config import EloConfig, Desenlace, clamp
from ..utils.logger import Loggers

logger = Loggers.elo()


class EloService:
    """
    Servicio para el cálculo del algoritmo Elo avanzado para pádel 2 vs 2
    Implementa el algoritmo diseñado específicamente para el proyecto Drive+
    """
    
    def __init__(self):
        # La configuración se obtiene de EloConfig
        pass
    
    def get_k_factor_by_experience(self, partidos_jugados: int) -> int:
        """
        Obtener factor K basado en la experiencia del jugador
        
        Args:
            partidos_jugados: Número de partidos jugados
            
        Returns:
            int: Factor K correspondiente
        """
        return EloConfig.get_k_factor(partidos_jugados)
    
    def calculate_team_rating(self, player1_rating: float, player2_rating: float) -> float:
        """
        Calcular rating promedio del equipo
        
        Args:
            player1_rating: Rating del jugador 1
            player2_rating: Rating del jugador 2
            
        Returns:
            float: Rating promedio del equipo
        """
        return (player1_rating + player2_rating) / 2
    
    def calculate_expected_score(self, team_a_rating: float, team_b_rating: float) -> Tuple[float, float]:
        """
        Calcular expectativa de victoria usando modelo logístico Elo
        
        Args:
            team_a_rating: Rating del equipo A
            team_b_rating: Rating del equipo B
            
        Returns:
            Tuple[float, float]: (expectativa_equipo_a, expectativa_equipo_b)
        """
        rating_diff = team_a_rating - team_b_rating
        expected_a = 1.0 / (1.0 + math.pow(10, -rating_diff / EloConfig.ELO_SCALE))
        expected_b = 1.0 - expected_a
        
        return expected_a, expected_b
    
    def calculate_sets_score(self, sets_a: int, sets_b: int) -> float:
        """
        Calcular puntuación base por sets
        
        Args:
            sets_a: Sets ganados por equipo A
            sets_b: Sets ganados por equipo B
            
        Returns:
            float: Puntuación base por sets (0.0 a 1.0)
        """
        total_sets = sets_a + sets_b
        if total_sets == 0:
            return 0.5  # Empate por defecto
        
        return sets_a / total_sets
    
    def calculate_games_margin(self, games_a: int, games_b: int, total_games: int) -> float:
        """
        Calcular margen de games con cap (versión mejorada)
        
        Args:
            games_a: Games ganados por equipo A
            games_b: Games ganados por equipo B
            total_games: Total de games jugados
            
        Returns:
            float: Margen de games capado
        """
        max_games = max(EloConfig.MIN_TOTAL_GAMES, total_games)
        raw = ((games_a - games_b) / max_games) * EloConfig.GAMES_MULTIPLIER
        return clamp(raw, -EloConfig.GAMES_MARGIN_CAP, EloConfig.GAMES_MARGIN_CAP)
    
    def calculate_final_score(self, sets_score: float, games_margin: float) -> float:
        """
        Calcular puntuación final combinando sets y games
        
        Args:
            sets_score: Puntuación base por sets
            games_margin: Margen de games
            
        Returns:
            float: Puntuación final (0.0 a 1.0)
        """
        final_score = sets_score + games_margin
        return max(0.0, min(1.0, final_score))
    
    def calculate_sets_multiplier(self, sets_a: int, sets_b: int) -> float:
        """
        Calcular multiplicador por diferencia de sets
        
        Args:
            sets_a: Sets ganados por equipo A
            sets_b: Sets ganados por equipo B
            
        Returns:
            float: Multiplicador de sets
        """
        return 1.0 + EloConfig.SETS_MULTIPLIER * abs(sets_a - sets_b)
    
    def calculate_team_k_factor(self, player1_games: int, player2_games: int) -> float:
        """
        Calcular factor K promedio del equipo
        
        Args:
            player1_games: Partidos jugados por jugador 1
            player2_games: Partidos jugados por jugador 2
            
        Returns:
            float: Factor K promedio del equipo
        """
        k1 = self.get_k_factor_by_experience(player1_games)
        k2 = self.get_k_factor_by_experience(player2_games)
        return (k1 + k2) / 2
    
    def calculate_base_delta(self, team_k: float, actual_score: float, expected_score: float, sets_multiplier: float) -> float:
        """
        Calcular delta base del equipo
        
        Args:
            team_k: Factor K del equipo
            actual_score: Puntuación real
            expected_score: Puntuación esperada
            sets_multiplier: Multiplicador por sets
            
        Returns:
            float: Delta base del equipo
        """
        return team_k * (actual_score - expected_score) * sets_multiplier
    
    def calculate_loss_softener(self, team_rating: float, opponent_rating: float, actual_score: float, expected_score: float) -> float:
        """
        Calcular suavizador de derrotas para favoritos (BUG CORREGIDO)
        
        Args:
            team_rating: Rating del equipo
            opponent_rating: Rating del oponente
            actual_score: Puntuación real
            expected_score: Puntuación esperada
            
        Returns:
            float: Factor de suavizado
        """
        # Solo aplicar si es favorito y no cumplió expectativa
        if team_rating > opponent_rating and actual_score < expected_score and expected_score > 0:
            span = EloConfig.FAVORITE_LOSS_CEILING - EloConfig.FAVORITE_LOSS_FLOOR
            ratio = max(0.0, min(1.0, actual_score / expected_score))
            soft = EloConfig.FAVORITE_LOSS_FLOOR + span * ratio
            return max(EloConfig.FAVORITE_LOSS_FLOOR, min(EloConfig.FAVORITE_LOSS_CEILING, soft))
        
        return 1.0  # Sin suavizado
    
    def get_role_caps(self, team_rating: float, opponent_rating: float) -> Tuple[float, float]:
        """
        Obtener caps por rol (underdog vs favorito)
        
        Args:
            team_rating: Rating del equipo
            opponent_rating: Rating del oponente
            
        Returns:
            Tuple[float, float]: (cap_win, cap_loss)
        """
        return EloConfig.get_role_caps(team_rating, opponent_rating)
    
    def apply_rating_caps(self, delta: float, cap_win: float, cap_loss: float) -> float:
        """
        Aplicar caps al cambio de rating
        
        Args:
            delta: Delta del rating
            cap_win: Cap para victoria
            cap_loss: Cap para derrota
            
        Returns:
            float: Delta con caps aplicados
        """
        return max(cap_loss, min(cap_win, delta))
    
    def split_team_delta(self, delta_team: float, r1: float, r2: float, mode: str = "proportional") -> Tuple[float, float]:
        """
        Repartir delta del equipo entre jugadores
        
        Args:
            delta_team: Delta total del equipo
            r1: Rating del jugador 1
            r2: Rating del jugador 2
            mode: Modo de reparto ("equal", "inverse", "proportional")
            
        Returns:
            Tuple[float, float]: (delta_jugador_1, delta_jugador_2)
        """
        if mode == "equal":
            return delta_team / 2, delta_team / 2
        elif mode == "inverse":
            # pesos ∝ 1/ri (jugador de menor rating absorbe más)
            w1 = 1.0 / max(1.0, r1)
            w2 = 1.0 / max(1.0, r2)
            s = w1 + w2
            return delta_team * (w1 / s), delta_team * (w2 / s)
        elif mode == "proportional":
            # pesos ∝ ri (jugador de mayor rating absorbe más)
            w1 = max(1.0, r1)
            w2 = max(1.0, r2)
            s = w1 + w2
            return delta_team * (w1 / s), delta_team * (w2 / s)
        else:
            # Default a proportional
            return self.split_team_delta(delta_team, r1, r2, "proportional")
    
    def calculate_dominant_set_bonus(self, sets_detail: List[Dict]) -> float:
        """
        Calcular bonus por sets dominantes
        
        Args:
            sets_detail: Lista de detalles de sets [{"games_a": int, "games_b": int}]
            
        Returns:
            float: Bonus por sets dominantes
        """
        bonus = 0.0
        for set_detail in sets_detail:
            games_a = set_detail.get("games_a", 0)
            games_b = set_detail.get("games_b", 0)
            
            # Bonus por set dominante (6-0 o 6-1)
            if (games_a == 6 and games_b <= 1) or (games_b == 6 and games_a <= 1):
                bonus += EloConfig.DOMINANT_SET_BONUS
        
        return bonus
    
    def calculate_tiebreak_reduction(self, sets_detail: List[Dict]) -> float:
        """
        Calcular reducción por tie-breaks
        
        Args:
            sets_detail: Lista de detalles de sets [{"games_a": int, "games_b": int}]
            
        Returns:
            float: Factor de reducción por tie-breaks
        """
        tiebreak_count = 0
        total_sets = len(sets_detail)
        
        for set_detail in sets_detail:
            games_a = set_detail.get("games_a", 0)
            games_b = set_detail.get("games_b", 0)
            
            # Detectar tie-break (7-6)
            if (games_a == 7 and games_b == 6) or (games_b == 7 and games_a == 6):
                tiebreak_count += 1
        
        if total_sets > 0:
            tiebreak_ratio = tiebreak_count / total_sets
            return 1.0 - (tiebreak_ratio * (1.0 - EloConfig.TIEBREAK_REDUCTION))
        
        return 1.0
    
    def check_abuse_pattern(self, team_a_players: List[Dict], team_b_players: List[Dict], 
                          match_date: datetime, recent_matches: List[Dict]) -> bool:
        """
        Verificar si hay patrón de abuso (mismos 4 jugadores jugando repetidamente)
        
        Args:
            team_a_players: Jugadores del equipo A
            team_b_players: Jugadores del equipo B
            match_date: Fecha del partido
            recent_matches: Lista de partidos recientes
            
        Returns:
            bool: True si se detecta abuso
        """
        # Obtener IDs de jugadores
        player_ids = set()
        for player in team_a_players + team_b_players:
            if "id" in player:
                player_ids.add(player["id"])
        
        if len(player_ids) != 4:
            return False  # No son exactamente 4 jugadores únicos
        
        # Contar partidos con estos mismos jugadores en la ventana de tiempo
        window_start = match_date - timedelta(hours=EloConfig.ABUSE_CHECK_WINDOW_H)
        same_player_matches = 0
        
        for match in recent_matches:
            match_date_obj = match.get("fecha")
            if not match_date_obj:
                continue
                
            if match_date_obj < window_start:
                continue
            
            # Verificar si el partido tiene los mismos 4 jugadores
            match_player_ids = set()
            for player in match.get("jugadores", []):
                if "id" in player:
                    match_player_ids.add(player["id"])
            
            if match_player_ids == player_ids:
                same_player_matches += 1
        
        return same_player_matches >= EloConfig.ABUSE_SAME4_THRESHOLD
    
    def update_player_volatility(self, player: Dict, actual_score: float, expected_score: float) -> float:
        """
        Actualizar volatilidad del jugador basado en su desempeño
        
        Args:
            player: Datos del jugador
            actual_score: Puntuación real del equipo
            expected_score: Puntuación esperada del equipo
            
        Returns:
            float: Nueva volatilidad
        """
        current_vol = player.get("volatilidad", 1.0)
        gap = abs(actual_score - expected_score)
        
        if gap < EloConfig.VOLATILIDAD_STABLE_THRESHOLD:
            # Cumple expectativas - estabilizar
            new_vol = current_vol * EloConfig.VOLATILIDAD_DOWN_FACTOR
        elif gap > EloConfig.VOLATILIDAD_VOLATILE_THRESHOLD:
            # Resultado sorpresivo - aumentar volatilidad
            new_vol = current_vol * EloConfig.VOLATILIDAD_UP_FACTOR
        else:
            # Sin cambios
            new_vol = current_vol
        
        return clamp(new_vol, EloConfig.VOLATILIDAD_MIN, EloConfig.VOLATILIDAD_MAX)
    
    def calculate_match_ratings(
        self,
        team_a_players: List[Dict[str, Any]],
        team_b_players: List[Dict[str, Any]],
        sets_a: int,
        sets_b: int,
        games_a: int = 0,
        games_b: int = 0,
        sets_detail: List[Dict] = None,
        desenlace: str = Desenlace.NORMAL.value,
        match_type: str = "torneo",
        match_date: datetime = None,
        recent_matches: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calcular nuevos ratings para un partido de pádel 2 vs 2 (VERSIÓN MEJORADA)
        
        Args:
            team_a_players: Lista de jugadores del equipo A [{"rating": float, "partidos": int, "volatilidad": float, "id": int}]
            team_b_players: Lista de jugadores del equipo B [{"rating": float, "partidos": int, "volatilidad": float, "id": int}]
            sets_a: Sets ganados por equipo A
            sets_b: Sets ganados por equipo B
            games_a: Games ganados por equipo A
            games_b: Games ganados por equipo B
            sets_detail: Lista de detalles de sets [{"games_a": int, "games_b": int}]
            desenlace: Tipo de desenlace (normal, wo_eq1, wo_eq2, ret_eq1, ret_eq2)
            match_type: Tipo de partido (amistoso, torneo, final)
            match_date: Fecha del partido
            recent_matches: Lista de partidos recientes para verificar abuso
            
        Returns:
            Dict: Resultados del cálculo Elo
        """
        # Validar equipos
        if len(team_a_players) != 2 or len(team_b_players) != 2:
            raise ValueError("Cada equipo debe tener exactamente 2 jugadores")
        
        # 1. Calcular ratings de equipo
        team_a_rating = self.calculate_team_rating(
            team_a_players[0]["rating"], 
            team_a_players[1]["rating"]
        )
        team_b_rating = self.calculate_team_rating(
            team_b_players[0]["rating"], 
            team_b_players[1]["rating"]
        )
        
        # 2. Calcular expectativas
        expected_a, expected_b = self.calculate_expected_score(team_a_rating, team_b_rating)
        
        # 3. Calcular puntuación real según desenlace
        if desenlace == Desenlace.WO_EQ1.value:
            actual_score_a = 1.0
            actual_score_b = 0.0
        elif desenlace == Desenlace.WO_EQ2.value:
            actual_score_a = 0.0
            actual_score_b = 1.0
        elif desenlace == Desenlace.RET_EQ1.value:
            # Retiro ganado por equipo 1
            total_sets = sets_a + sets_b
            if total_sets > 0:
                actual_score_a = sets_a / total_sets
                actual_score_b = sets_b / total_sets
            else:
                actual_score_a = 0.5
                actual_score_b = 0.5
        elif desenlace == Desenlace.RET_EQ2.value:
            # Retiro ganado por equipo 2
            total_sets = sets_a + sets_b
            if total_sets > 0:
                actual_score_a = sets_a / total_sets
                actual_score_b = sets_b / total_sets
            else:
                actual_score_a = 0.5
                actual_score_b = 0.5
        else:
            # Partido normal - CORREGIDO: El ganador SIEMPRE debe tener score > 0.5
            # Determinar quién ganó basándose en sets
            team_a_won = sets_a > sets_b
            
            # Calcular score base por sets (proporcional)
            sets_score_a = self.calculate_sets_score(sets_a, sets_b)
            total_games = games_a + games_b
            games_margin = self.calculate_games_margin(games_a, games_b, total_games)
            
            # Score ajustado por margen de games
            raw_score_a = self.calculate_final_score(sets_score_a, games_margin)
            
            # CRÍTICO: Asegurar que el ganador tenga score >= 0.6 y perdedor <= 0.4
            # Esto evita que el ganador pierda puntos por tener expectativa alta
            if team_a_won:
                # A ganó: su score debe ser al menos 0.6 (victoria clara)
                actual_score_a = max(0.6, raw_score_a)
                actual_score_b = 1.0 - actual_score_a
            else:
                # B ganó: score de A debe ser máximo 0.4
                actual_score_a = min(0.4, raw_score_a)
                actual_score_b = 1.0 - actual_score_a
        
        # 4. Calcular multiplicadores y factores K con volatilidad
        sets_multiplier = self.calculate_sets_multiplier(sets_a, sets_b)
        
        # Bonus por sets dominantes
        dominant_bonus = 0.0
        tiebreak_reduction = 1.0
        
        # Para walkovers, no aplicar bonus por sets
        if desenlace in (Desenlace.WO_EQ1.value, Desenlace.WO_EQ2.value):
            sets_multiplier = 1.0
            dominant_bonus = 0.0
            tiebreak_reduction = 1.0
        elif sets_detail:
            dominant_bonus = self.calculate_dominant_set_bonus(sets_detail)
            tiebreak_reduction = self.calculate_tiebreak_reduction(sets_detail)
        
        # Aplicar bonus y reducción
        sets_multiplier += dominant_bonus
        sets_multiplier *= tiebreak_reduction
        
        # Factor K con volatilidad
        team_a_k_base = self.calculate_team_k_factor(
            team_a_players[0]["partidos"], 
            team_a_players[1]["partidos"]
        )
        team_b_k_base = self.calculate_team_k_factor(
            team_b_players[0]["partidos"], 
            team_b_players[1]["partidos"]
        )
        
        # Aplicar volatilidad
        vol_a1 = team_a_players[0].get("volatilidad", 1.0)
        vol_a2 = team_a_players[1].get("volatilidad", 1.0)
        vol_b1 = team_b_players[0].get("volatilidad", 1.0)
        vol_b2 = team_b_players[1].get("volatilidad", 1.0)
        
        team_a_k = EloConfig.k_with_volatility(team_a_k_base, (vol_a1 + vol_a2) / 2)
        team_b_k = EloConfig.k_with_volatility(team_b_k_base, (vol_b1 + vol_b2) / 2)
        
        # Aplicar K-lock y límites diarios por jugador
        if match_date is None:
            match_date = datetime.now()
            
        # Verificar K-lock para cada jugador del equipo A
        for i, player in enumerate(team_a_players):
            if self.check_k_lock(player["id"], match_date):
                team_a_k *= EloConfig.K_LOCK_MULTIPLIER
            if self.check_daily_matches_limit(player["id"], match_date):
                team_a_k = 0.0
                break  # Si cualquier jugador excede el límite, el equipo no gana puntos
        
        # Verificar K-lock para cada jugador del equipo B
        for i, player in enumerate(team_b_players):
            if self.check_k_lock(player["id"], match_date):
                team_b_k *= EloConfig.K_LOCK_MULTIPLIER
            if self.check_daily_matches_limit(player["id"], match_date):
                team_b_k = 0.0
                break  # Si cualquier jugador excede el límite, el equipo no gana puntos
        
        # 5. Calcular delta base - CORREGIDO: Separar signo (resultado) de magnitud (rendimiento)
        # REGLA FUNDAMENTAL: Ganador SIEMPRE sube, perdedor SIEMPRE baja
        # La expectativa solo afecta CUÁNTO, no EL SIGNO
        
        # Determinar quién ganó realmente
        team_a_won = sets_a > sets_b
        team_b_won = sets_b > sets_a
        
        # Calcular magnitud base usando la diferencia de expectativa
        # Favoritos ganan menos puntos, underdogs ganan más puntos
        if team_a_won:
            # A ganó: calcular cuánto debería ganar basado en expectativa
            if expected_a > 0.5:  # A era favorito
                # Favorito gana pocos puntos (mínimo 1, máximo basado en performance)
                magnitude_a = max(1.0, team_a_k * (1.0 - expected_a) * sets_multiplier)
            else:  # A era underdog
                # Underdog gana muchos puntos
                magnitude_a = team_a_k * (1.0 - expected_a) * sets_multiplier
            
            # B perdió: pierde puntos proporcionales
            magnitude_b = team_b_k * expected_b * sets_multiplier
            
            delta_base_a = abs(magnitude_a)   # Positivo (ganador)
            delta_base_b = -abs(magnitude_b)  # Negativo (perdedor)
            
        elif team_b_won:
            # B ganó: calcular cuánto debería ganar basado en expectativa
            if expected_b > 0.5:  # B era favorito
                # Favorito gana pocos puntos (mínimo 1, máximo basado en performance)
                magnitude_b = max(1.0, team_b_k * (1.0 - expected_b) * sets_multiplier)
            else:  # B era underdog
                # Underdog gana muchos puntos
                magnitude_b = team_b_k * (1.0 - expected_b) * sets_multiplier
            
            # A perdió: pierde puntos proporcionales
            magnitude_a = team_a_k * expected_a * sets_multiplier
            
            delta_base_a = -abs(magnitude_a)  # Negativo (perdedor)
            delta_base_b = abs(magnitude_b)   # Positivo (ganador)
            
        else:
            # Empate (muy raro en pádel): cambios mínimos basados en expectativa
            delta_base_a = team_a_k * (actual_score_a - expected_a) * sets_multiplier * 0.1
            delta_base_b = team_b_k * (actual_score_b - expected_b) * sets_multiplier * 0.1
        
        # 6. Aplicar suavizador de derrotas
        loss_softener_a = self.calculate_loss_softener(
            team_a_rating, team_b_rating, actual_score_a, expected_a
        )
        loss_softener_b = self.calculate_loss_softener(
            team_b_rating, team_a_rating, actual_score_b, expected_b
        )
        
        delta_soft_a = delta_base_a * loss_softener_a
        delta_soft_b = delta_base_b * loss_softener_b
        
        # 7. Aplicar caps según tipo de partido y rol
        cap_win_a, cap_loss_a = EloConfig.caps_for_match_type(match_type, team_a_rating, team_b_rating)
        cap_win_b, cap_loss_b = EloConfig.caps_for_match_type(match_type, team_b_rating, team_a_rating)
        
        delta_cap_a = self.apply_rating_caps(delta_soft_a, cap_win_a, cap_loss_a)
        delta_cap_b = self.apply_rating_caps(delta_soft_b, cap_win_b, cap_loss_b)
        
        # 8. Verificar abuso y aplicar multiplicador si es necesario
        abuse_detected = False
        if match_date and recent_matches:
            abuse_detected = self.check_abuse_pattern(
                team_a_players, team_b_players, match_date, recent_matches
            )
        
        if abuse_detected:
            delta_cap_a *= EloConfig.ABUSE_MULTIPLIER
            delta_cap_b *= EloConfig.ABUSE_MULTIPLIER
        
        # 9. Repartir a los jugadores usando la función mejorada
        da1, da2 = self.split_team_delta(
            delta_cap_a, 
            team_a_players[0]["rating"], 
            team_a_players[1]["rating"], 
            mode="proportional"
        )
        db1, db2 = self.split_team_delta(
            delta_cap_b, 
            team_b_players[0]["rating"], 
            team_b_players[1]["rating"], 
            mode="proportional"
        )
        
        # 10. Calcular nuevos ratings (redondeados)
        new_rating_a1 = int(round(team_a_players[0]["rating"] + da1))
        new_rating_a2 = int(round(team_a_players[1]["rating"] + da2))
        new_rating_b1 = int(round(team_b_players[0]["rating"] + db1))
        new_rating_b2 = int(round(team_b_players[1]["rating"] + db2))
        
        # 11. Actualizar volatilidad de jugadores
        new_vol_a1 = self.update_player_volatility(team_a_players[0], actual_score_a, expected_a)
        new_vol_a2 = self.update_player_volatility(team_a_players[1], actual_score_a, expected_a)
        new_vol_b1 = self.update_player_volatility(team_b_players[0], actual_score_b, expected_b)
        new_vol_b2 = self.update_player_volatility(team_b_players[1], actual_score_b, expected_b)
        
        return {
            "team_a": {
                "old_rating": team_a_rating,
                "new_rating": (new_rating_a1 + new_rating_a2) / 2,
                "rating_change": delta_cap_a,
                "players": [
                    {
                        "player_index": 0,
                        "old_rating": team_a_players[0]["rating"],
                        "new_rating": new_rating_a1,
                        "rating_change": da1,
                        "old_volatility": team_a_players[0].get("volatilidad", 1.0),
                        "new_volatility": new_vol_a1
                    },
                    {
                        "player_index": 1,
                        "old_rating": team_a_players[1]["rating"],
                        "new_rating": new_rating_a2,
                        "rating_change": da2,
                        "old_volatility": team_a_players[1].get("volatilidad", 1.0),
                        "new_volatility": new_vol_a2
                    }
                ]
            },
            "team_b": {
                "old_rating": team_b_rating,
                "new_rating": (new_rating_b1 + new_rating_b2) / 2,
                "rating_change": delta_cap_b,
                "players": [
                    {
                        "player_index": 0,
                        "old_rating": team_b_players[0]["rating"],
                        "new_rating": new_rating_b1,
                        "rating_change": db1,
                        "old_volatility": team_b_players[0].get("volatilidad", 1.0),
                        "new_volatility": new_vol_b1
                    },
                    {
                        "player_index": 1,
                        "old_rating": team_b_players[1]["rating"],
                        "new_rating": new_rating_b2,
                        "rating_change": db2,
                        "old_volatility": team_b_players[1].get("volatilidad", 1.0),
                        "new_volatility": new_vol_b2
                    }
                ]
            },
            "match_details": {
                "expected_a": expected_a,
                "expected_b": expected_b,
                "actual_score_a": actual_score_a,
                "actual_score_b": actual_score_b,
                "sets_multiplier": sets_multiplier,
                "dominant_bonus": dominant_bonus,
                "tiebreak_reduction": tiebreak_reduction,
                "team_a_k": team_a_k,
                "team_b_k": team_b_k,
                "team_a_k_base": team_a_k_base,
                "team_b_k_base": team_b_k_base,
                "loss_softener_a": loss_softener_a,
                "loss_softener_b": loss_softener_b,
                "caps_a": (cap_win_a, cap_loss_a),
                "caps_b": (cap_win_b, cap_loss_b),
                "match_type": match_type,
                "abuse_detected": abuse_detected,
                "desenlace": desenlace
            }
        }
    
    def get_rating_category(self, rating: float) -> str:
        """
        Obtener la categoría del rating Elo
        
        Args:
            rating: Rating Elo del jugador
            
        Returns:
            str: Categoría del rating
        """
        if rating >= 2400:
            return "Grand Master"
        elif rating >= 2200:
            return "International Master"
        elif rating >= 2000:
            return "Master"
        elif rating >= 1800:
            return "Expert"
        elif rating >= 1600:
            return "Advanced"
        elif rating >= 1400:
            return "Intermediate"
        elif rating >= 1200:
            return "Beginner"
        else:
            return "Novice"
    
    def calculate_win_probability(self, team_a_rating: float, team_b_rating: float) -> Dict[str, float]:
        """
        Calcular la probabilidad de victoria para cada equipo
        
        Args:
            team_a_rating: Rating del equipo A
            team_b_rating: Rating del equipo B
            
        Returns:
            Dict: Probabilidades de victoria para cada equipo
        """
        expected_a, expected_b = self.calculate_expected_score(team_a_rating, team_b_rating)
        
        return {
            "team_a_win_probability": expected_a,
            "team_b_win_probability": expected_b
        }
    
    def calculate_inactivity_decay(self, last_match_date: datetime, current_date: datetime = None) -> float:
        """
        Calcular decay por inactividad
        
        Args:
            last_match_date: Fecha del último partido
            current_date: Fecha actual (opcional)
            
        Returns:
            float: Factor de decay (1.0 = sin decay, 0.95 = 5% de decay)
        """
        if current_date is None:
            current_date = datetime.now()
        
        months_inactive = (current_date - last_match_date).days / 30.0
        decay_factor = min(months_inactive * EloConfig.DECAY_PER_MONTH, EloConfig.DECAY_MAX)
        
        return 1.0 - decay_factor
    
    # === NUEVAS FUNCIONALIDADES DEL SISTEMA ELO AVANZADO ===
    
    def check_k_lock(self, user_id: int, match_time: datetime) -> bool:
        """
        Verificar si el usuario está en bloqueo temporal de K
        
        Args:
            user_id: ID del usuario
            match_time: Fecha y hora del partido
            
        Returns:
            bool: True si está bloqueado, False si no
        """
        # TODO: Implementar consulta a la base de datos
        # Por ahora retornamos False (no bloqueado)
        return False
    
    def check_daily_matches_limit(self, user_id: int, match_date: datetime) -> bool:
        """
        Verificar si el usuario ha excedido el límite de partidos por día
        
        Args:
            user_id: ID del usuario
            match_date: Fecha del partido
            
        Returns:
            bool: True si ha excedido el límite, False si no
        """
        # TODO: Implementar consulta a la base de datos
        # Por ahora retornamos False (no excedido)
        return False
    
    def is_surprise_victory(self, actual_score: float, expected_score: float) -> bool:
        """
        Verificar si fue una victoria sorpresiva
        
        Args:
            actual_score: Score real (1.0 = victoria, 0.0 = derrota)
            expected_score: Score esperado
            
        Returns:
            bool: True si fue sorpresiva, False si no
        """
        if actual_score == 1.0:  # Solo para victorias
            surprise_factor = actual_score - expected_score
            return surprise_factor > EloConfig.SURPRISE_VICTORY_THRESHOLD
        return False
    
    def is_total_loss(self, sets_ganados: int, sets_perdidos: int) -> bool:
        """
        Verificar si fue una derrota total (sin sets ganados)
        
        Args:
            sets_ganados: Sets ganados por el jugador
            sets_perdidos: Sets perdidos por el jugador
            
        Returns:
            bool: True si fue derrota total, False si no
        """
        return sets_ganados == 0 and sets_perdidos > 0
    
    def calculate_streak_volatility_boost(self, user_id: int, is_underdog: bool, won: bool) -> float:
        """
        Calcular boost de volatilidad por racha de victorias siendo underdog
        
        Args:
            user_id: ID del usuario
            is_underdog: Si era underdog en este partido
            won: Si ganó el partido
            
        Returns:
            float: Factor de boost de volatilidad
        """
        if not is_underdog or not won:
            return 0.0
        
        # TODO: Implementar consulta a la base de datos para contar rachas
        # Por ahora retornamos 0 (sin boost)
        return 0.0
    
    def check_post_ascension_immunity(self, user_id: int) -> bool:
        """
        Verificar si el usuario tiene inmunidad post-ascenso
        
        Args:
            user_id: ID del usuario
            
        Returns:
            bool: True si tiene inmunidad, False si no
        """
        # TODO: Implementar consulta a la base de datos
        # Por ahora retornamos False (sin inmunidad)
        return False
    
    def get_category_by_rating(self, rating: int, sexo: str = "masculino") -> str:
        """
        Obtener categoría por rating y sexo
        
        Args:
            rating: Rating del jugador
            sexo: Sexo del jugador ("masculino" o "femenino")
            
        Returns:
            str: Nombre de la categoría
        """
        if sexo == "femenino":
            # Categorías femeninas: Principiante, 8va, 7ma, 6ta, 5ta, Libre
            if rating >= 1600:
                return "Libre"
            elif rating >= 1400:
                return "5ta"
            elif rating >= 1200:
                return "6ta"
            elif rating >= 1000:
                return "7ma"
            elif rating >= 500:
                return "8va"
            else:
                return "Principiante"
        else:
            # Categorías masculinas: Principiante, 8va, 7ma, 6ta, 5ta, 4ta, Libre
            if rating >= 1800:
                return "Libre"
            elif rating >= 1600:
                return "4ta"
            elif rating >= 1400:
                return "5ta"
            elif rating >= 1200:
                return "6ta"
            elif rating >= 1000:
                return "7ma"
            elif rating >= 500:
                return "8va"
            else:
                return "Principiante"
    
    def log_elo_change(self, user_id: int, elo_antes: int, elo_despues: int, 
                      partido_id: int, match_type: str = None,
                      sets_ganados: int = None, sets_perdidos: int = None,
                      k_factor: float = None, volatilidad: float = None,
                      fue_underdog: bool = None, fue_sorpresiva: bool = None,
                      fue_derrota_total: bool = None, manual_override: bool = False,
                      notas: str = None):
        """
        Registrar cambio de ELO en el historial usando la tabla HistorialRating existente
        
        Args:
            user_id: ID del usuario
            elo_antes: Rating antes del partido
            elo_despues: Rating después del partido
            partido_id: ID del partido (requerido)
            match_type: Tipo de partido (opcional)
            sets_ganados: Sets ganados (opcional)
            sets_perdidos: Sets perdidos (opcional)
            k_factor: K factor usado (opcional)
            volatilidad: Volatilidad usada (opcional)
            fue_underdog: Si era underdog (opcional)
            fue_sorpresiva: Si fue victoria sorpresiva (opcional)
            fue_derrota_total: Si fue derrota total (opcional)
            manual_override: Si fue override manual (opcional)
            notas: Notas adicionales (opcional)
        """
        # La tabla HistorialRating es perfecta para esto:
        # - id_usuario: user_id
        # - id_partido: partido_id  
        # - rating_antes: elo_antes
        # - delta: elo_despues - elo_antes
        # - rating_despues: elo_despues
        # - creado_en: automático
        
        # TODO: Implementar inserción en la tabla HistorialRating
        # from src.models.driveplus_models import HistorialRating
        # from src.database.config import get_db
        # 
        # db = next(get_db())
        # historial = HistorialRating(
        #     id_usuario=user_id,
        #     id_partido=partido_id,
        #     rating_antes=elo_antes,
        #     delta=elo_despues - elo_antes,
        #     rating_despues=elo_despues
        # )
        # db.add(historial)
        # db.commit()
        
        # Para datos adicionales, usar EventoPartido.meta:
        # evento_meta = {
        #     "match_type": match_type,
        #     "sets_ganados": sets_ganados,
        #     "sets_perdidos": sets_perdidos,
        #     "k_factor": k_factor,
        #     "volatilidad": volatilidad,
        #     "fue_underdog": fue_underdog,
        #     "fue_sorpresiva": fue_sorpresiva,
        #     "fue_derrota_total": fue_derrota_total,
        #     "manual_override": manual_override,
        #     "notas": notas
        # }
        pass
    
    def create_category_checkpoint(self, user_id: int, categoria_anterior: str, 
                                 categoria_nueva: str, rating_ascenso: int,
                                 partido_id: int = None):
        """
        Crear checkpoint de ascenso de categoría
        
        Args:
            user_id: ID del usuario
            categoria_anterior: Categoría anterior
            categoria_nueva: Categoría nueva
            rating_ascenso: Rating al momento del ascenso
            partido_id: ID del partido que causó el ascenso (opcional)
        """
        # TODO: Implementar inserción en la base de datos
        pass
