"""Tests d'intégration : persistance SQLite et flux agent-moteur."""

import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from game_engine.moteur import MoteurJeu
from game_engine.direction import Direction
from agents.agent_astar import AgentAStar
from agents.agent_rl import AgentQL
from agents.joueur_humain import JoueurHumain
from models.agent import Agent as AgentModel
from models.game import Game
from models.game_event import GameEvent
from models.stats import AgentStats


# Fixture : base SQLite en mémoire isolée pour chaque test

@pytest.fixture()
def db_session():
    """Session SQLite en mémoire — isolée et détruite après chaque test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# Helpers

def _enregistrer_partie_test(db, engine: MoteurJeu, agent_type: str, agent_name: str,
                               pending_events: list[dict]) -> Game:
    """Réplique la logique de GameWebSocketManager._enregistrer_partie sur une DB de test."""
    agent = db.query(AgentModel).filter(AgentModel.type == agent_type).first()
    if agent is None:
        agent = AgentModel(name=agent_name, type=agent_type)
        db.add(agent)
        db.commit()
        db.refresh(agent)

    game = Game(
        agent_id=agent.id,
        score=int(engine.score),
        nb_steps=int(engine.step_count),
        duration=1.0,
        longueur_serpent=len(engine.serpent.corps),
        cause_mort=engine.cause_mort or "inconnu",
        taille_grille="20x20",
        obstacles_actifs=False,
    )
    db.add(game)

    stats = db.query(AgentStats).filter(AgentStats.agent_id == agent.id).first()
    if stats is None:
        stats = AgentStats(agent_id=agent.id, games_played=0, avg_score=0.0,
                           best_score=0, win_rate=0.0)
        db.add(stats)
    stats.games_played += 1
    stats.best_score = max(stats.best_score, int(engine.score))
    stats.avg_score = (stats.avg_score * (stats.games_played - 1) + int(engine.score)) / stats.games_played

    db.commit()
    db.refresh(game)

    for ev in pending_events:
        db.add(GameEvent(
            game_id=game.id,
            type_evenement=ev["type"],
            timestamp=ev["timestamp"],
            score=ev["score"],
            direction=ev["direction"],
        ))
    db.commit()

    return game


# Tests SQLite

def test_sqlite_partie_enregistree(db_session):
    """Une partie terminée est bien persistée dans la table games."""
    moteur = MoteurJeu()
    moteur.reset(mode="astar")
    # Forcer game over rapide : serpent au bord gauche allant à gauche
    moteur.serpent.corps = [(0, 10)]
    moteur.serpent.direction = Direction.GAUCHE
    moteur.static_obstacles = set()
    moteur.dynamic_obstacles = {}
    moteur._refresh_obstacles()
    moteur.step()
    assert moteur.game_over

    game = _enregistrer_partie_test(db_session, moteur, "astar", "A*", [])
    assert game.id is not None
    assert game.score >= 0
    assert game.nb_steps == 1
    assert game.cause_mort is not None


def test_sqlite_stats_incrementees(db_session):
    """Jouer deux parties incrémente games_played et met à jour best_score."""
    moteur = MoteurJeu()
    moteur.reset(mode="rl")
    moteur.serpent.corps = [(0, 10)]
    moteur.serpent.direction = Direction.GAUCHE
    moteur.static_obstacles = set()
    moteur.dynamic_obstacles = {}
    moteur._refresh_obstacles()
    moteur.step()

    _enregistrer_partie_test(db_session, moteur, "rl", "Q-Learning", [])
    _enregistrer_partie_test(db_session, moteur, "rl", "Q-Learning", [])

    stats = db_session.query(AgentStats).first()
    assert stats.games_played == 2


def test_sqlite_game_events_sauvegardes(db_session):
    """Les événements de jeu sont liés à la partie dans game_events."""
    moteur = MoteurJeu()
    moteur.reset(mode="astar")
    moteur.serpent.corps = [(0, 10)]
    moteur.serpent.direction = Direction.GAUCHE
    moteur.static_obstacles = set()
    moteur.dynamic_obstacles = {}
    moteur._refresh_obstacles()
    moteur.step()

    events = [
        {"type": "collision", "timestamp": 0.5, "score": 0, "direction": "GAUCHE"},
    ]
    game = _enregistrer_partie_test(db_session, moteur, "astar", "A*", events)

    saved = db_session.query(GameEvent).filter(GameEvent.game_id == game.id).all()
    assert len(saved) == 1
    assert saved[0].type_evenement == "collision"


def test_sqlite_agent_unique_par_type(db_session):
    """Deux parties avec le même agent_type réutilisent le même enregistrement agent."""
    moteur = MoteurJeu()
    moteur.reset(mode="astar")
    moteur.serpent.corps = [(0, 10)]
    moteur.serpent.direction = Direction.GAUCHE
    moteur.static_obstacles = set()
    moteur.dynamic_obstacles = {}
    moteur._refresh_obstacles()
    moteur.step()

    _enregistrer_partie_test(db_session, moteur, "astar", "A*", [])
    _enregistrer_partie_test(db_session, moteur, "astar", "A*", [])

    agents = db_session.query(AgentModel).filter(AgentModel.type == "astar").all()
    assert len(agents) == 1


# Tests flux agent-moteur (sans DB)

def test_flux_astar_moteur_100_steps():
    """A* + moteur : 100 pas sans exception, état cohérent à chaque step."""
    agent = AgentAStar()
    moteur = MoteurJeu()
    moteur.reset(mode="astar")

    for _ in range(100):
        if moteur.game_over:
            break
        direction = agent.choisir_action({"engine": moteur})
        moteur.changer_direction(direction)
        moteur.step()

    state = moteur.get_state_dict()
    assert "score" in state
    assert state["score"] >= 0


def test_flux_rl_moteur_100_steps():
    """QL + moteur : 100 pas sans exception."""
    agent = AgentQL(epsilon=0.0)
    moteur = MoteurJeu()
    moteur.reset(mode="rl")

    for _ in range(100):
        if moteur.game_over:
            break
        direction = agent.choisir_action({"engine": moteur})
        moteur.changer_direction(direction)
        moteur.step()

    assert moteur.score >= 0


def test_flux_joueur_humain_moteur():
    """JoueurHumain transmet la direction au moteur sans erreur."""
    agent = JoueurHumain()
    moteur = MoteurJeu()
    moteur.reset(mode="manual")

    direction = agent.choisir_action({"direction": "UP", "engine": moteur})
    assert direction == Direction.HAUT

    moteur.changer_direction(direction)
    moteur.step()
    assert moteur.step_count == 1


def test_latence_astar_inferieure_50ms():
    """L'inférence A* doit être < 50 ms (critère rapport)."""
    agent = AgentAStar()
    moteur = MoteurJeu()
    moteur.reset(mode="astar")

    debut = time.perf_counter()
    for _ in range(10):
        agent.choisir_action({"engine": moteur})
    duree_ms = (time.perf_counter() - debut) * 1000 / 10

    assert duree_ms < 50, f"Latence A* trop haute : {duree_ms:.2f} ms"


def test_latence_rl_inferieure_5ms():
    """L'inférence QL doit être < 5 ms (lookup dict O(1))."""
    agent = AgentQL(epsilon=0.0)
    moteur = MoteurJeu()
    moteur.reset(mode="rl")

    debut = time.perf_counter()
    for _ in range(50):
        agent.choisir_action({"engine": moteur})
    duree_ms = (time.perf_counter() - debut) * 1000 / 50

    assert duree_ms < 5, f"Latence QL trop haute : {duree_ms:.2f} ms"
