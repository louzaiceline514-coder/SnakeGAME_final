"""Gestion du WebSocket pour la mise à jour temps réel du jeu."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import orjson
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from agents.agent_astar import AgentAStar
from agents.agent_rl import AgentQL
from config import EPSILON_MIN, TICK_INTERVAL_MS
from database import SessionLocal
from game_engine.direction import Direction
from game_engine.moteur import MoteurJeu
from models.agent import Agent
from models.game import Game
from models.game_event import GameEvent
from models.stats import AgentStats

# Champs qui ne changent qu'au reset (envoyés uniquement dans le message "game_state" complet)
_STATIC_KEYS = frozenset({"obstacles", "taille_grille", "obstacles_actifs", "mode"})

# Compteur global pour le log périodique de la taille des messages (toutes 200 tick)
_MSG_SIZE_LOG_INTERVAL = 200


class GameWebSocketManager:
    """Gère un client WebSocket et la boucle de jeu associée."""

    def __init__(self) -> None:
        self.engine = MoteurJeu()
        self.agent_astar = AgentAStar()
        self.agent_rl = AgentQL(epsilon=EPSILON_MIN)
        self._running = False
        self._last_tick = time.time()
        self._paused = True
        self._tick_ms = TICK_INTERVAL_MS
        self._game_saved = False
        self._replay_frames: list = []
        self._max_replay_frames = 1500
        # Optimisation delta : après le premier état complet, on n'envoie que les champs dynamiques
        self._static_sent: bool = False
        self._tick_count: int = 0

    # Sérialisation / delta

    def _build_full_payload(self, state_dict: Dict[str, Any]) -> bytes:
        """Construit le message complet JSON (premier frame ou après reset)."""
        msg = {"type": "game_state", "payload": state_dict}
        return orjson.dumps(msg)

    def _build_delta_payload(self, state_dict: Dict[str, Any]) -> bytes:
        """Construit un message delta avec uniquement les champs dynamiques."""
        delta = {k: v for k, v in state_dict.items() if k not in _STATIC_KEYS}
        msg = {"type": "game_delta", "payload": delta}
        return orjson.dumps(msg)

    def _log_msg_size(self, payload: bytes) -> None:
        """Log périodique de la taille des messages WebSocket (toutes 200 ticks)."""
        if self._tick_count % _MSG_SIZE_LOG_INTERVAL == 0:
            print(f"[WS] tick={self._tick_count} msg_size={len(payload)} octets")

    # Boucle principale

    async def handle(self, websocket: WebSocket) -> None:
        """Boucle principale de gestion du WebSocket."""
        await websocket.accept()
        self._running = True

        # Premier état complet immédiat
        state_dict = self.engine.get_state_dict()
        payload = self._build_full_payload(state_dict)
        await websocket.send_bytes(payload)
        self._static_sent = True

        producer_task = asyncio.create_task(self._tick_loop(websocket))
        consumer_task = asyncio.create_task(self._receive_loop(websocket))

        done, pending = await asyncio.wait(
            {producer_task, consumer_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        if self._should_persist_current_game():
            self._enregistrer_partie()
        self._running = False

    async def _tick_loop(self, websocket: WebSocket) -> None:
        """Boucle envoyant l'état du jeu à intervalles réguliers."""
        try:
            while self._running:
                await asyncio.sleep(self._tick_ms / 1000.0)
                self._tick_count += 1

                if not self._paused and not self.engine.game_over:
                    # Choix d'action par l'IA si nécessaire
                    if self.engine.mode == "astar":
                        direction = self.agent_astar.choisir_action({"engine": self.engine})
                        self.engine.changer_direction(direction)
                    elif self.engine.mode == "rl":
                        direction = self.agent_rl.choisir_action({"engine": self.engine})
                        self.engine.changer_direction(direction)

                    self.engine.step()
                    if len(self._replay_frames) < self._max_replay_frames:
                        self._replay_frames.append(self.engine.get_state_dict())
                    if self.engine.game_over and not self._game_saved:
                        self._enregistrer_partie()
                        self._game_saved = True

                # Construire l'état et injecter le chemin A* (F6) ou RL
                state_dict = self.engine.get_state_dict()
                if self.engine.mode == "astar":
                    state_dict["astar_path"] = [
                        {"x": x, "y": y} for (x, y) in self.agent_astar.last_path
                    ]
                elif self.engine.mode == "rl" and not self.engine.game_over:
                    # Toujours afficher le chemin : last_path après un move, sinon simulation depuis direction actuelle
                    rl_path_coords = self.agent_rl.last_path or self.agent_rl._simulate_greedy_path(
                        self.engine, self.engine.serpent.direction
                    )
                    state_dict["rl_path"] = [{"x": x, "y": y} for (x, y) in rl_path_coords]

                # Envoi : complet sur premier frame, delta sur les suivants
                if not self._static_sent:
                    payload = self._build_full_payload(state_dict)
                    self._static_sent = True
                else:
                    payload = self._build_delta_payload(state_dict)

                self._log_msg_size(payload)
                await websocket.send_bytes(payload)

        except WebSocketDisconnect:
            self._running = False
        except Exception as e:
            print("Erreur tick_loop WebSocket:", repr(e))
            self._running = False

    async def _receive_loop(self, websocket: WebSocket) -> None:
        """Boucle de réception des messages du frontend."""
        try:
            while self._running:
                raw = await websocket.receive_text()
                data: Dict[str, Any] = orjson.loads(raw)
                msg_type = data.get("type")

                if msg_type == "set_mode":
                    self._save_before_leaving_current_game()
                    mode = data.get("mode", "manual")
                    self.engine.reset(mode=mode)
                    self._paused = True
                    self._game_saved = False
                    self._replay_frames = []
                    self._static_sent = False  # prochain tick → état complet
                elif msg_type == "direction":
                    dir_str = data.get("dir")
                    direction = self._parse_direction(dir_str)
                    if direction and self.engine.mode == "manual":
                        self.engine.changer_direction(direction)
                elif msg_type == "start":
                    self._paused = False
                elif msg_type == "reset":
                    self._save_before_leaving_current_game()
                    self.engine.reset(mode=self.engine.mode)
                    self._paused = True
                    self._game_saved = False
                    self._replay_frames = []
                    self._static_sent = False  # prochain tick → état complet
                elif msg_type == "set_paused":
                    self._paused = bool(data.get("paused", False))
                elif msg_type == "set_speed":
                    try:
                        speed = int(data.get("speed", TICK_INTERVAL_MS))
                        self._tick_ms = max(50, min(500, speed))
                    except (TypeError, ValueError):
                        self._tick_ms = TICK_INTERVAL_MS
        except WebSocketDisconnect:
            self._running = False
        except Exception as e:
            print("Erreur receive_loop WebSocket:", repr(e))
            self._running = False

    def _parse_direction(self, dir_str: str | None) -> Direction | None:
        """Convertit une chaîne en Direction."""
        if dir_str == "UP":
            return Direction.HAUT
        if dir_str == "DOWN":
            return Direction.BAS
        if dir_str == "LEFT":
            return Direction.GAUCHE
        if dir_str == "RIGHT":
            return Direction.DROITE
        return None

    def _enregistrer_partie(self) -> None:
        """Enregistre la partie courante dans la base de données pour l'agent actif."""
        db = SessionLocal()
        try:
            mode = self.engine.mode
            if mode == "astar":
                agent_type = "astar"
                name = "A*"
            elif mode == "rl":
                agent_type = "rl"
                name = "Q-Learning"
            else:
                agent_type = "human"
                name = "Humain"

            agent = db.query(Agent).filter(Agent.type == agent_type).first()
            if agent is None:
                agent = Agent(name=name, type=agent_type)
                db.add(agent)
                db.commit()
                db.refresh(agent)

            score = int(self.engine.score)
            nb_steps = int(self.engine.step_count)
            duration = float(time.time() - self.engine.start_time)

            game = Game(
                agent_id=agent.id,
                score=score,
                nb_steps=nb_steps,
                duration=duration,
                longueur_serpent=len(self.engine.serpent.corps),
                cause_mort=self.engine.cause_mort or "inconnu",
                taille_grille=f"{self.engine.grille.largeur}x{self.engine.grille.hauteur}",
                obstacles_actifs=len(self.engine.grille.obstacles) > 0,
                date_fin=datetime.utcnow(),
            )
            db.add(game)

            stats = db.query(AgentStats).filter(AgentStats.agent_id == agent.id).first()
            if stats is None:
                stats = AgentStats(
                    agent_id=agent.id,
                    games_played=0,
                    avg_score=0.0,
                    best_score=0,
                    win_rate=0.0,
                )
                db.add(stats)

            if stats.games_played is None:
                stats.games_played = 0
            if stats.avg_score is None:
                stats.avg_score = 0.0
            if stats.best_score is None:
                stats.best_score = 0
            if stats.win_rate is None:
                stats.win_rate = 0.0

            old_games = stats.games_played
            stats.games_played = stats.games_played + 1
            stats.best_score = max(stats.best_score, score)
            stats.avg_score = (
                (stats.avg_score * old_games + score) / stats.games_played
                if stats.games_played > 0
                else 0.0
            )
            wins = stats.win_rate * old_games
            if score > 0:
                wins += 1
            stats.win_rate = wins / stats.games_played if stats.games_played > 0 else 0.0

            db.commit()
            db.refresh(game)

            # Sauvegarde des frames de replay
            if self._replay_frames:
                for i, frame in enumerate(self._replay_frames):
                    db.add(GameEvent(
                        game_id=game.id,
                        type_evenement="frame",
                        details_json=orjson.dumps(frame).decode(),
                        timestamp=round(i * (self._tick_ms / 1000.0), 3),
                        score=frame.get("score", 0),
                        direction=frame.get("direction"),
                    ))
                db.commit()
                self._replay_frames = []

            self._game_saved = True
        finally:
            db.close()

    def _should_persist_current_game(self) -> bool:
        """Indique si la partie courante merite d'etre enregistree."""
        return (
            not self._game_saved
            and self.engine.step_count > 0
            and (self.engine.score > 0 or self.engine.mode in {"astar", "rl", "manual"})
        )

    def _save_before_leaving_current_game(self) -> None:
        """Sauvegarde une partie en cours avant reset/changement de mode."""
        if self._should_persist_current_game():
            self._enregistrer_partie()
