"""Agent IA utilisant le Q-Learning pour apprendre à jouer au Snake."""

from __future__ import annotations

import json
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from config import (
    ALPHA,
    EPSILON_DECAY,
    EPSILON_MIN,
    EPSILON_START,
    GAMMA,
    QTABLE_PATH,
)
from game_engine.direction import Direction
from game_engine.moteur import MoteurJeu
from agents.base_agent import Agent

StateKey = Tuple[int, ...]


class AgentQL(Agent):
    """Agent Q-Learning avec encodage d'état binaire (11 features)."""

    def __init__(self, epsilon: Optional[float] = None) -> None:
        super().__init__(name="Q-Learning")
        self.alpha = ALPHA
        self.gamma = GAMMA
        self.epsilon = EPSILON_START if epsilon is None else epsilon
        self.q_table: Dict[str, List[float]] = {}
        self.actions = [Direction.GAUCHE, Direction.DROITE, Direction.HAUT, Direction.BAS]
        self.last_path: List[Tuple[int, int]] = []
        self.charger_qtable()

    # ------------------ Gestion Q-table ------------------ #
    def _state_to_key(self, state: StateKey) -> str:
        return ",".join(str(v) for v in state)

    def obtenir_q_valeurs(self, state: StateKey) -> List[float]:
        key = self._state_to_key(state)
        if key not in self.q_table:
            self.q_table[key] = [0.0 for _ in self.actions]
        return self.q_table[key]

    def _is_safe_direction(self, moteur: MoteurJeu, direction: Direction) -> bool:
        tete_x, tete_y = moteur.serpent.tete
        nx, ny = tete_x + direction.dx, tete_y + direction.dy
        if not moteur.grille.est_dans_grille(nx, ny):
            return False
        if (nx, ny) in moteur.grille.obstacles:
            return False
        if (nx, ny) in list(moteur.serpent.corps)[1:]:
            return False
        return True

    def _safe_actions(self, moteur: MoteurJeu) -> List[Direction]:
        return [direction for direction in self.actions if self._is_safe_direction(moteur, direction)]

    def _distance_to_food(self, moteur: MoteurJeu, direction: Direction) -> float:
        if moteur.grille.nourriture is None:
            return 0.0
        nx = moteur.serpent.tete[0] + direction.dx
        ny = moteur.serpent.tete[1] + direction.dy
        fx, fy = moteur.grille.nourriture
        return abs(fx - nx) + abs(fy - ny)

    def sauvegarder_qtable(self) -> None:
        """Sauvegarde la Q-table dans un fichier JSON."""
        QTABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
        QTABLE_PATH.write_text(json.dumps(self.q_table), encoding="utf-8")

    def charger_qtable(self) -> None:
        """Charge la Q-table depuis le fichier JSON si disponible."""
        if QTABLE_PATH.exists():
            try:
                loaded = json.loads(QTABLE_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.q_table = {
                        str(key): [float(value) for value in values]
                        for key, values in loaded.items()
                        if isinstance(values, list)
                    }
                else:
                    self.q_table = {}
            except Exception:
                self.q_table = {}

    # Encodage d'état  #
    def encoder_etat(self, moteur: MoteurJeu) -> StateKey:
        """Encode l'état du jeu en 11 caractéristiques binaires.

        (danger_straight, danger_left, danger_right,
         dir_up, dir_down, dir_left, dir_right,
         food_up, food_down, food_left, food_right)

        Les vérifications de danger utilisent une matrice NumPy uint8 (to_numpy_grid)
        pour un accès O(1) aux cellules sans parcours de listes Python.
        Valeurs : 0=vide, 1=corps, 2=nourriture, 3=obstacle.
        """
        tete_x, tete_y = moteur.serpent.tete
        dir_actuelle = moteur.serpent.direction
        food = moteur.grille.nourriture
        corps = list(moteur.serpent.corps)

        # Grille NumPy uint8 — indexée [y, x]
        grid = moteur.grille.to_numpy_grid(corps)
        h, w = grid.shape

        def danger_si_direction(direction: Direction) -> int:
            nx, ny = tete_x + direction.dx, tete_y + direction.dy
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                return 1
            cell = int(grid[ny, nx])
            # 1 = corps, 3 = obstacle → danger ; 0 = vide, 2 = nourriture → sûr
            return 1 if cell == 1 or cell == 3 else 0

        # Orientation relative : avant/gauche/droite par rapport à la direction actuelle
        if dir_actuelle == Direction.HAUT:
            move_straight, move_left, move_right = Direction.HAUT, Direction.GAUCHE, Direction.DROITE
        elif dir_actuelle == Direction.BAS:
            move_straight, move_left, move_right = Direction.BAS, Direction.DROITE, Direction.GAUCHE
        elif dir_actuelle == Direction.GAUCHE:
            move_straight, move_left, move_right = Direction.GAUCHE, Direction.BAS, Direction.HAUT
        else:
            move_straight, move_left, move_right = Direction.DROITE, Direction.HAUT, Direction.BAS

        danger_straight = danger_si_direction(move_straight)
        danger_left = danger_si_direction(move_left)
        danger_right = danger_si_direction(move_right)

        dir_up = 1 if dir_actuelle == Direction.HAUT else 0
        dir_down = 1 if dir_actuelle == Direction.BAS else 0
        dir_left = 1 if dir_actuelle == Direction.GAUCHE else 0
        dir_right = 1 if dir_actuelle == Direction.DROITE else 0

        food_up = food_down = food_left = food_right = 0
        if food:
            fx, fy = food
            if fy < tete_y:
                food_up = 1
            elif fy > tete_y:
                food_down = 1
            if fx < tete_x:
                food_left = 1
            elif fx > tete_x:
                food_right = 1

        return (
            danger_straight,
            danger_left,
            danger_right,
            dir_up,
            dir_down,
            dir_left,
            dir_right,
            food_up,
            food_down,
            food_left,
            food_right,
        )

    # Politique et mise à jour  #
    def choisir_action(self, state: Dict[str, Any]) -> Direction:
        """Politique epsilon-greedy basée sur la Q-table."""
        moteur: MoteurJeu = state["engine"]
        encoded = self.encoder_etat(moteur)
        q_vals = self.obtenir_q_valeurs(encoded)
        safe_actions = self._safe_actions(moteur)

        if not safe_actions:
            return moteur.serpent.direction

        if random.random() < self.epsilon:
            chosen = random.choice(safe_actions)
            self.last_path = self._simulate_greedy_path(moteur, chosen)
            return chosen

        scored_actions = []
        for index, direction in enumerate(self.actions):
            if direction not in safe_actions:
                continue
            scored_actions.append((q_vals[index], -self._distance_to_food(moteur, direction), direction))

        if not scored_actions:
            return random.choice(safe_actions)

        max_q = max(score for score, _, _ in scored_actions)
        meilleures = [
            direction
            for score, _, direction in scored_actions
            if math.isclose(score, max_q) or score == max_q
        ]

        if len(meilleures) == 1:
            self.last_path = self._simulate_greedy_path(moteur, meilleures[0])
            return meilleures[0]

        meilleures.sort(key=lambda direction: self._distance_to_food(moteur, direction))
        self.last_path = self._simulate_greedy_path(moteur, meilleures[0])
        return meilleures[0]

    # Simulation chemin greedy (visualisation)  

    def _greedy_dir_from_pos(
        self,
        x: int,
        y: int,
        current_dir: Direction,
        food: Optional[Tuple[int, int]],
        obstacles: set,
        corps_set: set,
        visited: set,
        w: int,
        h: int,
    ) -> Optional[Direction]:
        """Choisit la direction greedy depuis une position simulée (Q-table + manhattan)."""
        food_up = food_down = food_left = food_right = 0
        if food:
            fx, fy = food
            if fy < y:
                food_up = 1
            elif fy > y:
                food_down = 1
            if fx < x:
                food_left = 1
            elif fx > x:
                food_right = 1

        def is_blocked(d: Direction) -> int:
            nx2, ny2 = x + d.dx, y + d.dy
            if not (0 <= nx2 < w and 0 <= ny2 < h):
                return 1
            if (nx2, ny2) in obstacles or (nx2, ny2) in corps_set or (nx2, ny2) in visited:
                return 1
            return 0

        if current_dir == Direction.HAUT:
            ms, ml, mr = Direction.HAUT, Direction.GAUCHE, Direction.DROITE
        elif current_dir == Direction.BAS:
            ms, ml, mr = Direction.BAS, Direction.DROITE, Direction.GAUCHE
        elif current_dir == Direction.GAUCHE:
            ms, ml, mr = Direction.GAUCHE, Direction.BAS, Direction.HAUT
        else:
            ms, ml, mr = Direction.DROITE, Direction.HAUT, Direction.BAS

        state: StateKey = (
            is_blocked(ms), is_blocked(ml), is_blocked(mr),
            1 if current_dir == Direction.HAUT else 0,
            1 if current_dir == Direction.BAS else 0,
            1 if current_dir == Direction.GAUCHE else 0,
            1 if current_dir == Direction.DROITE else 0,
            food_up, food_down, food_left, food_right,
        )
        q_vals = self.obtenir_q_valeurs(state)
        safe_dirs = [d for d in self.actions if not is_blocked(d)]
        if not safe_dirs:
            return None
        return max(safe_dirs, key=lambda d: q_vals[self.actions.index(d)])

    def _simulate_greedy_path(
        self, moteur: MoteurJeu, first_dir: Direction, max_steps: int = 15
    ) -> List[Tuple[int, int]]:
        """Simule le chemin greedy sur max_steps pas (approximation sans copie moteur)."""
        path: List[Tuple[int, int]] = []
        x, y = moteur.serpent.tete
        direction = first_dir
        obstacles: set = set(moteur.grille.obstacles)
        corps_set: set = set(moteur.serpent.corps)
        food: Optional[Tuple[int, int]] = moteur.grille.nourriture
        w, h = moteur.grille.largeur, moteur.grille.hauteur
        visited: set = {(x, y)}

        for _ in range(max_steps):
            nx, ny = x + direction.dx, y + direction.dy
            if not (0 <= nx < w and 0 <= ny < h):
                break
            if (nx, ny) in obstacles or (nx, ny) in corps_set or (nx, ny) in visited:
                break
            path.append((nx, ny))
            visited.add((nx, ny))
            x, y = nx, ny
            if food and (x, y) == food:
                break
            next_dir = self._greedy_dir_from_pos(x, y, direction, food, obstacles, corps_set, visited, w, h)
            if next_dir is None:
                break
            direction = next_dir

        return path

    def update_Q(
        self,
        state: StateKey,
        action: Direction,
        reward: float,
        next_state: StateKey,
    ) -> None:
        """Met à jour la Q-table via l'équation de Bellman."""
        q_vals = self.obtenir_q_valeurs(state)
        next_q_vals = self.obtenir_q_valeurs(next_state)
        a_idx = self.actions.index(action)
        old_q = q_vals[a_idx]
        target = reward + self.gamma * max(next_q_vals)
        q_vals[a_idx] = old_q + self.alpha * (target - old_q)

    # Boucle d'entraînement 
    def entrainer(self, nb_episodes: int, env: MoteurJeu) -> List[float]:
        """Boucle d'entraînement RL sur N épisodes, retourne la liste des scores.

        +10 manger, -10 mourir, +1 se rapprocher de la nourriture, -1 s'en éloigner.
        """
        scores: List[float] = []

        for _ in range(nb_episodes):
            env.reset(mode="training")
            state = self.encoder_etat(env)
            prev_score = env.score

            while not env.game_over:
                action = self.choisir_action({"engine": env})
                env.changer_direction(action)

                # Distance à la nourriture avant déplacement
                prev_dist = None
                if env.grille.nourriture:
                    fx, fy = env.grille.nourriture
                    sx, sy = env.serpent.tete
                    prev_dist = abs(fx - sx) + abs(fy - sy)

                env.step()

                reward = 0.0
                if env.game_over:
                    reward -= 10.0
                else:
                    # Distance après déplacement
                    if env.grille.nourriture and prev_dist is not None:
                        fx, fy = env.grille.nourriture
                        sx, sy = env.serpent.tete
                        new_dist = abs(fx - sx) + abs(fy - sy)
                        if new_dist < prev_dist:
                            reward += 1.0
                        elif new_dist > prev_dist:
                            reward -= 1.0

                    # Pomme mangée : le score vient d'augmenter
                    if env.score > prev_score:
                        reward += 10.0
                        prev_score = env.score

                next_state = self.encoder_etat(env)
                self.update_Q(state, action, reward, next_state)
                state = next_state

            scores.append(env.score)
            # Décroissance de epsilon
            if self.epsilon > EPSILON_MIN:
                self.epsilon *= EPSILON_DECAY

        self.sauvegarder_qtable()
        return scores
