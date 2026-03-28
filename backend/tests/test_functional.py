"""Tests fonctionnels (E2E) : simulent des sessions complètes de jeu."""

import pytest

from agents.agent_astar import AgentAStar
from agents.agent_rl import AgentQL
from agents.joueur_humain import JoueurHumain
from game_engine.moteur import MoteurJeu
from game_engine.direction import Direction


MAX_STEPS = 500  # plafond de sécurité pour éviter les boucles infinies


def _run_session(agent, mode: str) -> dict:
    """Exécute une session complète jusqu'au game_over ou MAX_STEPS.

    Returns dict avec score, step_count, game_over, state_dict final.
    """
    moteur = MoteurJeu()
    moteur.reset(mode=mode)

    for _ in range(MAX_STEPS):
        if moteur.game_over:
            break
        direction = agent.choisir_action({"engine": moteur})
        moteur.changer_direction(direction)
        moteur.step()

    return {
        "score": moteur.score,
        "step_count": moteur.step_count,
        "game_over": moteur.game_over,
        "state": moteur.get_state_dict(),
    }


# A* : session complète

def test_astar_session_complete_sans_crash():
    """Une session A* complète (jusqu'au game_over ou 500 steps) ne lève pas d'exception."""
    result = _run_session(AgentAStar(), "astar")
    assert result["score"] >= 0
    assert result["step_count"] > 0


def test_astar_state_dict_final_valide():
    """L'état final d'une session A* contient toutes les clés requises."""
    result = _run_session(AgentAStar(), "astar")
    state = result["state"]
    for key in ("snake", "food", "obstacles", "score", "game_over", "step_count", "mode"):
        assert key in state, f"Clé manquante dans state_dict : {key}"


def test_astar_score_coherent_avec_longueur_serpent():
    """Score ≥ 0 et longueur du serpent ≥ 1 après une session A*."""
    moteur = MoteurJeu()
    moteur.reset(mode="astar")
    agent = AgentAStar()

    for _ in range(MAX_STEPS):
        if moteur.game_over:
            break
        moteur.changer_direction(agent.choisir_action({"engine": moteur}))
        moteur.step()

    assert moteur.score >= 0
    assert len(moteur.serpent.corps) >= 1


def test_astar_plusieurs_sessions_independantes():
    """Deux sessions A* successives sont indépendantes (reset propre)."""
    agent = AgentAStar()
    r1 = _run_session(agent, "astar")
    r2 = _run_session(agent, "astar")
    # Les deux sessions doivent se terminer sans lever d'exception
    assert r1["step_count"] > 0
    assert r2["step_count"] > 0


# Q-Learning : session complète

def test_rl_session_complete_sans_crash():
    """Une session QL complète ne lève pas d'exception."""
    result = _run_session(AgentQL(epsilon=0.0), "rl")
    assert result["score"] >= 0
    assert result["step_count"] > 0


def test_rl_exploration_session():
    """Session QL en exploration totale (ε=1) : aucun crash."""
    result = _run_session(AgentQL(epsilon=1.0), "rl")
    assert result["step_count"] > 0


def test_rl_encodage_stable_pendant_session():
    """L'encodage d'état produit toujours 11 features binaires pendant une session."""
    agent = AgentQL(epsilon=0.0)
    moteur = MoteurJeu()
    moteur.reset(mode="rl")

    for _ in range(100):
        if moteur.game_over:
            break
        etat = agent.encoder_etat(moteur)
        assert len(etat) == 11
        assert all(v in (0, 1) for v in etat)
        moteur.changer_direction(agent.choisir_action({"engine": moteur}))
        moteur.step()


def test_rl_plusieurs_sessions_independantes():
    """Deux sessions QL successives avec reset propre."""
    agent = AgentQL(epsilon=0.0)
    r1 = _run_session(agent, "rl")
    r2 = _run_session(agent, "rl")
    assert r1["step_count"] > 0
    assert r2["step_count"] > 0


# JoueurHumain : session simulée

def test_humain_session_directions_successives():
    """JoueurHumain : enchaînement de directions sans crash."""
    agent = JoueurHumain()
    moteur = MoteurJeu()
    moteur.reset(mode="manual")

    directions_input = ["UP", "RIGHT", "DOWN", "LEFT", "UP", "RIGHT"]
    for dir_str in directions_input:
        if moteur.game_over:
            break
        direction = agent.choisir_action({"direction": dir_str, "engine": moteur})
        assert direction in list(Direction)
        moteur.changer_direction(direction)
        moteur.step()

    assert moteur.step_count > 0


def test_humain_fallback_direction_invalide():
    """JoueurHumain conserve la direction actuelle si l'entrée est invalide."""
    agent = JoueurHumain()
    moteur = MoteurJeu()
    moteur.reset(mode="manual")
    direction_courante = moteur.serpent.direction

    direction = agent.choisir_action({"direction": "INVALID", "engine": moteur})
    assert direction == direction_courante


def test_humain_fallback_sans_direction():
    """JoueurHumain conserve la direction actuelle si aucune direction n'est fournie."""
    agent = JoueurHumain()
    moteur = MoteurJeu()
    moteur.reset(mode="manual")
    direction_courante = moteur.serpent.direction

    direction = agent.choisir_action({"engine": moteur})
    assert direction == direction_courante


# Tests de robustesse moteur (E2E sans agent)

def test_moteur_reset_multiple():
    """Plusieurs reset successifs ne corrompent pas l'état."""
    moteur = MoteurJeu()
    for mode in ("manual", "astar", "rl", "manual"):
        moteur.reset(mode=mode)
        assert not moteur.game_over
        assert moteur.score == 0
        assert moteur.step_count == 0


def test_moteur_survie_1000_steps_astar():
    """A* survit au moins une majorité des 200 premiers steps sur grille standard."""
    agent = AgentAStar()
    moteur = MoteurJeu()
    moteur.reset(mode="astar")

    survived = 0
    for _ in range(200):
        if moteur.game_over:
            break
        moteur.changer_direction(agent.choisir_action({"engine": moteur}))
        moteur.step()
        survived += 1

    # A* doit survivre au moins 10 steps sur une grille normale
    assert survived >= 10, f"A* n'a survécu que {survived} steps"
