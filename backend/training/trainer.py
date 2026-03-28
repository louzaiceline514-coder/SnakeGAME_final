"""Boucle d'entraînement pour l'agent Q-Learning."""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable, List, Optional

try:
    import pandas as pd  #  génération du résumé statistique avancé
    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False

from agents.agent_rl import AgentQL
from database import SessionLocal
from game_engine.moteur import MoteurJeu
from models.rl_training import RLTraining


class Trainer:
    """Gère l'entraînement d'un agent RL sur plusieurs épisodes."""

    def __init__(self, sortie_csv: Path) -> None:
        self.sortie_csv = sortie_csv
        self.agent = AgentQL()
        self.moteur = MoteurJeu()
        self._en_cours: bool = False
        self._scores: List[int] = []

    @property
    def en_cours(self) -> bool:
        """Indique si un entraînement est en cours."""
        return self._en_cours

    @property
    def scores(self) -> List[int]:
        """Retourne la liste des scores enregistrés lors du dernier entraînement."""
        return list(self._scores)

    def entrainer(
        self,
        nb_episodes: int,
        callback_progression: Optional[Callable[[int, int, int], None]] = None,
        mode: str = "training",
    ) -> None:
        """Lance la boucle d'entraînement RL et sauvegarde les résultats dans un CSV.

        :param nb_episodes: nombre d'épisodes d'entraînement
        :param callback_progression: fonction appelée périodiquement (episode, nb_episodes, score)
        """
        self._en_cours = True
        self._scores = []

        db_records: List[RLTraining] = []
        try:
            for episode in range(1, nb_episodes + 1):
                # Reset de l'environnement et mesure du temps
                self.moteur.reset(mode=mode)

                # Une session d'entraînement dans l'environnement
                scores = self.agent.entrainer(1, self.moteur)
                score = int(scores[-1]) if scores else 0

                self._scores.append(score)

                db_records.append(RLTraining(
                    episode=episode,
                    recompense_totale=float(score),
                    epsilon=float(self.agent.epsilon),
                    perte_moyenne=0.0,  # erreur TD non agrégée pour Q-table tabulaire
                    score_final=score,
                    taux_apprentissage=float(self.agent.alpha),
                ))

                if callback_progression:
                    callback_progression(episode, nb_episodes, score)
        finally:
            self._en_cours = False

        # Persistance en base de données (batch)
        if db_records:
            db = SessionLocal()
            try:
                db.add_all(db_records)
                db.commit()
            finally:
                db.close()

        # Sauvegarde des scores dans un fichier CSV
        self.sortie_csv.parent.mkdir(parents=True, exist_ok=True)
        with self.sortie_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["episode", "score"])
            for i, score in enumerate(self._scores):
                writer.writerow([i + 1, score])

        # Résumé statistique avec Pandas si disponible
        if _HAS_PANDAS and self._scores:
            df = pd.DataFrame({"episode": range(1, len(self._scores) + 1), "score": self._scores})
            summary = df["score"].describe()
            summary_path = self.sortie_csv.with_name(self.sortie_csv.stem + "_summary.csv")
            summary.to_csv(summary_path, header=["valeur"])
            print(f"[Trainer] Résumé Pandas sauvegardé dans {summary_path}")
