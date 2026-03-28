"""Agent IA choisissant une direction sûre de manière aléatoire."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from agents.base_agent import Agent
from game_engine.direction import Direction
from game_engine.moteur import MoteurJeu


class AgentAleatoire(Agent):
    """Agent qui choisit aléatoirement parmi les directions qui n'entraînent pas
    une mort immédiate (mur, corps, obstacle).

    Cet agent sert de référence inférieure dans les benchmarks : ses performances
    sont naturellement en dessous de Q-Learning et A*, mais il ne meurt pas
    systématiquement au premier pas.
    """

    def __init__(self) -> None:
        super().__init__(name="Aléatoire")

    def _est_surete(self, moteur: MoteurJeu, direction: Direction) -> bool:
        """Retourne True si le déplacement dans cette direction n'est pas fatal."""
        x, y = moteur.serpent.tete
        nx, ny = x + direction.dx, y + direction.dy
        if not moteur.grille.est_dans_grille(nx, ny):
            return False
        if (nx, ny) in moteur.serpent.corps[1:]:
            return False
        if (nx, ny) in moteur.grille.obstacles:
            return False
        return True

    def choisir_action(self, state: Dict[str, Any]) -> Direction:
        """Choisit une direction sûre aléatoirement parmi les options disponibles.

        Si toutes les directions sont fatales (cul-de-sac), conserve la direction
        courante (mort inévitable, comportement gracieux).
        """
        moteur: MoteurJeu = state["engine"]
        current: Direction = moteur.serpent.direction
        opposite: Direction = Direction.opposite(current)

        # Candidats : toutes les directions sauf le demi-tour strict
        candidats: List[Direction] = [d for d in Direction if d != opposite]
        surets: List[Direction] = [d for d in candidats if self._est_surete(moteur, d)]

        if surets:
            return random.choice(surets)

        # Cul-de-sac : tous les candidats sont fatals, conserver la direction
        safe_all: List[Direction] = [d for d in Direction if self._est_surete(moteur, d)]
        if safe_all:
            return random.choice(safe_all)

        return current
