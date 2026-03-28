"""Agent IA utilisant l'algorithme A* pour rejoindre la nourriture."""

from __future__ import annotations

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

from agents.base_agent import Agent
from game_engine.direction import Direction
from game_engine.grille import Grille
from game_engine.moteur import MoteurJeu

Coord = Tuple[int, int]


class AgentAStar(Agent):
    """Agent basé sur A* qui cherche un chemin sûr jusqu'à la nourriture."""

    def __init__(self) -> None:
        super().__init__(name="A*")
        self.last_path: List[Coord] = []  # dernier chemin calculé (pour visualisation F6)

    def _heuristique(self, a: Coord, b: Coord) -> int:
        """Distance de Manhattan entre deux cases."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _reconstruire_chemin(self, came_from: Dict[Coord, Coord], current: Coord) -> List[Coord]:
        """Reconstruit le chemin depuis la nourriture jusqu'à la tête."""
        chemin = [current]
        while current in came_from:
            current = came_from[current]
            chemin.append(current)
        chemin.reverse()
        return chemin

    def _astar(
        self,
        grille: Grille,
        depart: Coord,
        objectif: Coord,
        forbidden: Set[Coord],
    ) -> Optional[List[Coord]]:
        """Algorithme A* classique sur la grille."""
        open_set: List[Tuple[int, Coord]] = []
        heapq.heappush(open_set, (0, depart))
        came_from: Dict[Coord, Coord] = {}
        g_score: Dict[Coord, int] = {depart: 0}
        f_score: Dict[Coord, int] = {depart: self._heuristique(depart, objectif)}
        visited: Set[Coord] = set()

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == objectif:
                return self._reconstruire_chemin(came_from, current)
            if current in visited:
                continue
            visited.add(current)

            for voisin in grille.obtenir_voisins(*current):
                if voisin in forbidden:
                    continue
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(voisin, 1_000_000_000):
                    came_from[voisin] = current
                    g_score[voisin] = tentative_g
                    f_score[voisin] = tentative_g + self._heuristique(voisin, objectif)
                    heapq.heappush(open_set, (f_score[voisin], voisin))
        return None

    def _direction_depuis_deplacement(self, src: Coord, dst: Coord) -> Direction:
        """Convertit deux coordonnées adjacentes en une direction."""
        dx = dst[0] - src[0]
        dy = dst[1] - src[1]
        for direction in Direction:
            if (direction.dx, direction.dy) == (dx, dy):
                return direction
        return Direction.DROITE

    def _espace_libre(self, grille: Grille, tete: Coord, forbidden: Set[Coord]) -> int:
        """Estime l'espace libre accessible via flood fill."""
        stack = [tete]
        vus: Set[Coord] = set()
        while stack and len(vus) < 200:
            x, y = stack.pop()
            if (x, y) in vus or (x, y) in forbidden:
                continue
            vus.add((x, y))
            for voisin in grille.obtenir_voisins(x, y):
                if voisin not in vus and voisin not in forbidden:
                    stack.append(voisin)
        return len(vus)

    def _simuler_etat(
        self,
        corps: List[Coord],
        direction: Direction,
        nourriture: Coord | None,
    ) -> tuple[Optional[List[Coord]], bool]:
        """Simule un déplacement et retourne le nouveau corps."""
        tete_x, tete_y = corps[0]
        nouvelle_tete = (tete_x + direction.dx, tete_y + direction.dy)
        if nouvelle_tete in corps[1:]:
            return None, False

        nouveau_corps = [nouvelle_tete] + list(corps)
        mange = nourriture == nouvelle_tete
        if not mange:
            nouveau_corps.pop()
        return nouveau_corps, mange

    def _peut_rejoindre_queue(
        self,
        grille: Grille,
        corps: List[Coord],
        obstacles: Set[Coord],
    ) -> bool:
        """vérifie si la tête peut rejoindre la queue avec le corps simulé."""
        if len(corps) <= 1:
            return True
        tete = corps[0]
        queue = corps[-1]
        forbidden = set(corps[1:-1]) | obstacles
        return self._astar(grille, tete, queue, forbidden) is not None

    def _longueur_chemin_queue(
        self,
        grille: Grille,
        corps: List[Coord],
        obstacles: Set[Coord],
    ) -> Optional[int]:
        """retourne la longueur du chemin vers la queue depuis un état simulé."""
        if len(corps) <= 1:
            return 0
        chemin = self._astar(grille, corps[0], corps[-1], set(corps[1:-1]) | obstacles)
        if chemin is None:
            return None
        return len(chemin)

    def _longueur_chemin_nourriture(
        self,
        grille: Grille,
        corps: List[Coord],
        obstacles: Set[Coord],
        nourriture: Coord | None,
    ) -> Optional[int]:
        """Retourne la longueur du chemin vers la nourriture depuis un état simulé."""
        if nourriture is None:
            return None
        chemin = self._astar(grille, corps[0], nourriture, set(corps[1:]) | obstacles)
        if chemin is None:
            return None
        return len(chemin)

    def _score_direction(
        self,
        grille: Grille,
        corps: List[Coord],
        obstacles: Set[Coord],
        nourriture: Coord | None,
        direction: Direction,
        current_direction: Direction | None = None,
    ) -> Optional[Tuple[int, int, int, int, int]]:
        """Calcule un score global privilégiant la survie puis la progression."""
        if current_direction is not None and direction == Direction.opposite(current_direction):
            return None
        nx = corps[0][0] + direction.dx
        ny = corps[0][1] + direction.dy
        if not grille.est_dans_grille(nx, ny):
            return None
        if (nx, ny) in obstacles:
            return None

        simulation = self._simuler_etat(corps, direction, nourriture)
        if simulation[0] is None:
            return None
        nouveau_corps, _ = simulation

        queue_path_len = self._longueur_chemin_queue(grille, nouveau_corps, obstacles)
        tail_access = 1 if queue_path_len is not None else 0
        espace = self._espace_libre(grille, nouveau_corps[0], set(nouveau_corps[1:]) | obstacles)
        marge = espace - len(nouveau_corps)
        safety_band = 1 if tail_access and marge >= 4 else 0
        food_path_len = self._longueur_chemin_nourriture(grille, nouveau_corps, obstacles, nourriture)
        food_score = -food_path_len if food_path_len is not None else -10_000
        distance_food = -self._heuristique(nouveau_corps[0], nourriture) if nourriture else 0
        queue_score = -(queue_path_len or 10_000)
        return (safety_band, tail_access, marge, queue_score, max(food_score, distance_food))

    def _choose_tail_first_direction(
        self,
        grille: Grille,
        corps: List[Coord],
        obstacles: Set[Coord],
        nourriture: Coord | None,
        current_direction: Direction,
    ) -> Optional[Direction]:
        """Mode survie fort pour l'arène: suivre la queue tant qu'une pomme n'est pas clairement sûre."""
        if len(corps) > 1:
            queue_path = self._astar(grille, corps[0], corps[-1], set(corps[1:-1]) | obstacles)
            if queue_path and len(queue_path) >= 2:
                direction = self._direction_depuis_deplacement(queue_path[0], queue_path[1])
                score = self._score_direction(
                    grille,
                    corps,
                    obstacles,
                    nourriture,
                    direction,
                    current_direction,
                )
                if score is not None and score[0] >= 1 and score[2] >= 5:
                    return direction
        return None

    def _choose_battle_action(self, moteur: MoteurJeu) -> Direction:
        """Politique spéciale battle: survie longue avant score immédiat."""
        grille = moteur.grille
        corps = list(moteur.serpent.corps)
        obstacles = set(grille.obstacles)
        nourriture = grille.nourriture
        current_direction = moteur.serpent.direction

        tail_direction = self._choose_tail_first_direction(
            grille,
            corps,
            obstacles,
            nourriture,
            current_direction,
        )

        if nourriture is not None:
            chemin_food = self._astar(grille, corps[0], nourriture, set(corps[1:]) | obstacles)
            if chemin_food and len(chemin_food) >= 2:
                direction_food = self._direction_depuis_deplacement(chemin_food[0], chemin_food[1])
                score_food = self._score_direction(
                    grille,
                    corps,
                    obstacles,
                    nourriture,
                    direction_food,
                    current_direction,
                )
                if score_food is not None and score_food[0] >= 1 and score_food[2] >= 7:
                    return direction_food

        if tail_direction is not None:
            return tail_direction

        scores: List[Tuple[Tuple[int, int, int, int, int], Direction]] = []
        for direction in Direction:
            score = self._score_direction(
                grille,
                corps,
                obstacles,
                nourriture,
                direction,
                current_direction,
            )
            if score is not None:
                scores.append((score, direction))
        if not scores:
            return moteur.serpent.direction
        scores.sort(key=lambda item: item[0], reverse=True)
        return scores[0][1]

    def choisir_action(self, state: Dict[str, Any]) -> Direction:
        """Choisit une direction sûre et efficace pour continuer à survivre."""
        moteur: MoteurJeu = state["engine"]
        grille = moteur.grille
        corps = list(moteur.serpent.corps)
        obstacles = set(grille.obstacles)
        nourriture = grille.nourriture
        current_direction = moteur.serpent.direction

        # Réinitialise le chemin courant (pour la visualisation F6)
        self.last_path = []

        if moteur.mode == "battle":
            return self._choose_battle_action(moteur)

        if not nourriture:
            return moteur.serpent.direction

        # Tentative directe : chemin vers la nourriture seulement si l'état d'arrivée reste viable.
        chemin = self._astar(grille, corps[0], nourriture, set(corps[1:]) | obstacles)
        if chemin and len(chemin) >= 2:
            direction = self._direction_depuis_deplacement(chemin[0], chemin[1])
            if direction != Direction.opposite(current_direction):
                simulation = self._simuler_etat(corps, direction, nourriture)
            else:
                simulation = (None, False)
            if simulation[0] is not None:
                queue_path_len = self._longueur_chemin_queue(grille, simulation[0], obstacles)
                espace = self._espace_libre(
                    grille,
                    simulation[0][0],
                    set(simulation[0][1:]) | obstacles,
                )
                marge = espace - len(simulation[0])
                if queue_path_len is not None and marge >= 4:
                    # Stocker le chemin planifié (sans la case de tête) pour la visualisation
                    self.last_path = chemin[1:]
                    return direction

        scores: List[Tuple[Tuple[int, int, int, int, int], Direction]] = []
        for direction in Direction:
            score = self._score_direction(
                grille,
                corps,
                obstacles,
                nourriture,
                direction,
                current_direction,
            )
            if score is not None:
                scores.append((score, direction))

        if not scores:
            return moteur.serpent.direction

        scores.sort(key=lambda item: item[0], reverse=True)
        return scores[0][1]
