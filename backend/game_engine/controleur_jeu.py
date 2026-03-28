"""ControleurJeu : façade orientée-objet qui orchestre tous les composants du jeu.

Correspond à la classe ControleurJeu du diagramme de classes du rapport de conception.
Ce contrôleur coordonne MoteurJeu, Nourriture, Obstacle et CollecteurStatistiques
en respectant la séparation des responsabilités décrite dans le rapport.
"""

from __future__ import annotations

from typing import List, Optional

from game_engine.collecteur_statistiques import CollecteurStatistiques
from game_engine.direction import Direction
from game_engine.moteur import MoteurJeu
from game_engine.nourriture import Nourriture
from game_engine.obstacle import Obstacle


class ControleurJeu:
    """Façade qui assemble Nourriture, Obstacle, CollecteurStatistiques et MoteurJeu.

    Utilisation :
        ctrl = ControleurJeu(mode="astar")
        ctrl.changer_direction(Direction.DROITE)
        ctrl.step()
        print(ctrl.score, ctrl.game_over)
        print(ctrl.collecteur.to_dict())
    """

    def __init__(self, mode: str = "manual") -> None:
        self._moteur = MoteurJeu()
        self._moteur.reset(mode=mode)
        self.nourriture = Nourriture(self._moteur.grille.nourriture)
        self.collecteur = CollecteurStatistiques()

    #  Cycle de vie                                                        

    def reset(self, mode: Optional[str] = None) -> None:
        """Réinitialise complètement le jeu et synchronise les objets-valeur."""
        self._moteur.reset(mode=mode)
        self.nourriture = Nourriture(self._moteur.grille.nourriture)

    def changer_direction(self, direction: Direction) -> None:
        """Transmet la nouvelle direction au moteur."""
        self._moteur.changer_direction(direction)

    def step(self) -> None:
        """Avance d'un pas de temps et met à jour les objets-valeur.

        Si la partie se termine lors de ce step, les statistiques sont
        automatiquement enregistrées dans le CollecteurStatistiques.
        """
        self._moteur.step()
        self.nourriture = Nourriture(self._moteur.grille.nourriture)

        if self._moteur.game_over:
            self.collecteur.enregistrer_partie(
                score=self._moteur.score,
                steps=self._moteur.step_count,
                longueur=len(self._moteur.serpent.corps),
                cause_mort=self._moteur.cause_mort,
            )


    #  Accesseurs                                                          

    def get_obstacles(self) -> List[Obstacle]:
        """Retourne la liste des obstacles actifs (statiques + dynamiques)."""
        obstacles: List[Obstacle] = [
            Obstacle(pos, Obstacle.TYPE_STATIQUE)
            for pos in self._moteur.static_obstacles
        ]
        obstacles += [
            Obstacle(pos, Obstacle.TYPE_DYNAMIQUE, age)
            for pos, age in self._moteur.dynamic_obstacles.items()
        ]
        return obstacles

    @property
    def moteur(self) -> MoteurJeu:
        """Accès direct au moteur sous-jacent (pour compatibilité avec les agents)."""
        return self._moteur

    @property
    def score(self) -> int:
        return self._moteur.score

    @property
    def game_over(self) -> bool:
        return self._moteur.game_over

    @property
    def step_count(self) -> int:
        return self._moteur.step_count

    @property
    def mode(self) -> str:
        return self._moteur.mode

    def get_state_dict(self) -> dict:
        """Délègue la sérialisation au moteur."""
        return self._moteur.get_state_dict()
