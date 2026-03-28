# Snake AI – SAE4 · Licence 3 Informatique UPJV

Application web complète autour du jeu du serpent (Snake Game), comparant deux agents IA :
- **A\*** : pathfinding optimal avec heuristique de Manhattan + flood fill + tail-chasing
- **Q-Learning** : apprentissage par renforcement tabulaire (Q-table JSON, 11 features NumPy)

Le mode Manuel permet de jouer soi-même au clavier.

---

## Table des matières

1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Lancement](#lancement)
4. [Manuel d'utilisation](#manuel-dutilisation)
   - [Mode Jeu](#mode-jeu)
   - [Mode A\* vs Q-Learning (Battle Arena)](#mode-a-vs-q-learning-battle-arena)
   - [Mode Entraînement](#mode-entraînement)
   - [Mode Statistiques](#mode-statistiques)
5. [Contrôles clavier](#contrôles-clavier)
6. [Lancement des tests](#lancement-des-tests)
7. [Description des algorithmes](#description-des-algorithmes)
8. [Structure du projet](#structure-du-projet)
9. [Base de données](#base-de-données)
10. [Documentation](#documentation)
11. [Dépannage](#dépannage)

---

## Architecture

```
Frontend (React 18 + Redux)  ←──WebSocket / REST──→  Backend (FastAPI + Python)
         │                                                      │
    Vite + Tailwind                               Moteur de jeu + IA (A*, QL)
    Redux (game/stats/ui/ws)                      SQLite (SQLAlchemy ORM)
```

- **Frontend** : Single Page Application React 18 avec Redux Toolkit pour l'état global.
- **Backend** : FastAPI avec support WebSocket natif (async/await) + sérialisation orjson.
- **IA** : Agent A* (min-heap, heuristique Manhattan, flood fill, tail-chasing) et Agent Q-Learning (Q-table JSON, 11 features NumPy uint8).
- **Base de données** : SQLite via SQLAlchemy (5 tables : agents, games, game_events, agent_stats, rl_training).
- **Rendu** : Canvas HTML5 bi-couche (fond statique + entités dynamiques) pour des performances optimales.

---

## Installation

### Prérequis

- Python 3.10+ avec `pip`
- Node.js 18+ avec `npm`

### Cloner le dépôt

```bash
git clone https://github.com/louzaiceline514-coder/SnakeGAME_final.git
cd SnakeGAME_final
```

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Lancement

### Lancement automatique (recommandé)

| Système | Action |
|---|---|
| **Windows** | Double-cliquez sur **`start.bat`** à la racine |
| **Linux** | `./start.sh` dans un terminal |
| **macOS** | Double-cliquez sur **`start.command`** depuis le Finder |

Le script démarre le backend, le frontend, et ouvre automatiquement le navigateur sur **`http://localhost:5174`**.

### Lancement manuel

Ouvrir **deux terminaux** :

**Terminal 1 – Backend :**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Le backend est disponible sur `http://localhost:8000`.
Swagger UI : `http://localhost:8000/docs`
La base de données `snake.db` est créée automatiquement à la racine du projet.

**Terminal 2 – Frontend :**
```bash
cd frontend
npm run dev
```

L'application est accessible sur **`http://localhost:5174`**.

> Si vous avez déjà une base `snake.db` d'une version précédente, supprimez-la avant de relancer le backend afin que les nouvelles tables soient créées correctement.

---

## Manuel d'utilisation

### Écran d'accueil

Au premier lancement, un écran de présentation s'affiche avec les trois modes disponibles.
Cliquez sur **Lancer en mode [X]** pour entrer dans l'application.

---

### Mode Jeu

Vue principale accessible via le bouton **Jouer** dans la barre de navigation.

**Panneau de contrôle (à droite) :**

| Élément | Description |
|---|---|
| **Sélecteur de mode** | Choisir entre Manuel, A* ou Q-Learning |
| **Bouton Start** | Démarre la partie (le jeu ne se lance pas seul) |
| **Bouton Pause/Resume** | Met en pause ou reprend la partie |
| **Bouton Reset** | Réinitialise la partie dans le mode courant |
| **Curseur de vitesse** | Ajuste la vitesse de tick (50 ms → rapide, 500 ms → lent) |

**Grille de jeu :**

| Élément | Couleur |
|---|---|
| Serpent (tête) | Vert vif avec yeux |
| Serpent (corps) | Vert avec dégradé |
| Nourriture | Rouge avec tige verte |
| Obstacles statiques | Gris foncé |
| Obstacles dynamiques | Gris clair |
| Chemin A* planifié | Bleu semi-transparent |
| Décisions Q-Learning | Violet semi-transparent |

---

### Mode A\* vs Q-Learning (Battle Arena)

Accessible via le bouton **A\* vs QL**.

Ce mode lance **simultanément** deux serpents IA indépendants sur deux grilles :

1. Cliquez **Start Battle** pour démarrer les deux agents.
2. Les statistiques live (score, steps, latence d'inférence, epsilon RL) s'affichent en temps réel.
3. Les graphiques BarChart et RadarChart comparent les performances.

> Les deux agents jouent sur une grille **25×25** avec obstacles statiques et dynamiques.

---

### Mode Entraînement

Accessible via le bouton **Entrainement**.

| Champ | Description |
|---|---|
| **Nombre d'épisodes** | Nombre de parties à jouer (max 100 par requête, défaut 80) |
| **Mode performance** | Désactive les obstacles pour accélérer la convergence RL |
| **Entrainer Q-Learning** | Lance l'entraînement RL côté serveur |
| **Benchmarker A\*** | Lance le benchmark A* |

**Résultats :**
- Courbe des scores par épisode (LineChart)
- Résumé : score moyen, meilleur score (MetricCards RL moyen / RL meilleur / A* moyen / A* meilleur)

Pour le RL, la Q-table est sauvegardée automatiquement dans `qtable.json` à la racine du projet et rechargée à chaque démarrage du backend.

---

### Mode Statistiques

Accessible via le bouton **Stats**.

Affiche la comparaison des performances entre A* et Q-Learning basée sur les parties réellement enregistrées en base de données :

- **Score moyen**, **meilleur score**, **taux de survie**, **nombre de parties jouées**
- **Historique des parties** (tableau des 200 dernières parties IA)

**Exports disponibles :**
- **CSV** : export brut de l'historique
- **JSON** : export structuré complet

---

## Contrôles clavier

| Touche | Action |
|---|---|
| `↑` ou `Z` | Déplacer le serpent vers le haut |
| `↓` ou `S` | Déplacer le serpent vers le bas |
| `←` ou `Q` | Déplacer le serpent vers la gauche |
| `→` ou `D` | Déplacer le serpent vers la droite |

> Les contrôles clavier ne sont actifs qu'en **mode Manuel**.
> Un demi-tour immédiat (ex. gauche → droite) est automatiquement ignoré.

---

## Lancement des tests

### Tests backend (pytest)

Depuis la **racine du projet** :

```bash
python -m pytest tests/ backend/tests/ -v
```

Couverture :

| Fichier | Tests |
|---|---|
| `tests/test_serpent.py` | Déplacement, croissance, collisions, demi-tour |
| `tests/test_grille.py` | Génération nourriture/obstacles, voisins, NumPy grid |
| `tests/test_moteur.py` | Cycle de jeu, step, reset, cause_mort |
| `tests/test_astar.py` | Chemin simple, heuristique Manhattan, obstacles, fallback survie |
| `tests/test_rl.py` | Encodage état (11 features), mise à jour Q-table, équation de Bellman, décroissance epsilon |
| `tests/test_api.py` | Routes REST /api/health, /api/game, /api/stats, /api/agents |
| `backend/tests/test_classes_diagramme.py` | Nourriture, Obstacle, CollecteurStatistiques, ControleurJeu, TypeCellule, EtatJeu, AgentAleatoire (39 tests) |
| `backend/tests/test_functional.py` | Sessions complètes A*, RL et humain (E2E sans DB) |
| `backend/tests/test_integration.py` | Persistance SQLite, flux agent-moteur, latences A* et RL |
| `backend/tests/test_websocket.py` | Connexion WebSocket, messages binaires orjson, deltas game_delta |

### Tests frontend (Vitest)

```bash
cd frontend
npm test
```

| Fichier | Couverture |
|---|---|
| `gameSlice.test.js` | Réducteurs Redux setGameState, applyDelta, setMode |
| `uiSlice.test.js` | Réducteurs Redux vitesse, vue |
| `Dashboard.test.jsx` | Rendu composant Dashboard avec différents états Redux |
| `BattleArena.test.jsx` | Rendu, boutons Start/Pause/Reset, scores initiaux, reset |
| `TrainingPanel.test.jsx` | Rendu, boutons, input épisodes, MetricCards, état Redux préchargé, toggle obstacles |

---

## Description des algorithmes

### Algorithme A\*

1. Maintient une file de priorité (min-heap `heapq`) avec le coût `f = g + h`.
2. `g` = distance parcourue depuis la tête du serpent.
3. `h` = distance de Manhattan vers la nourriture.
4. Le corps du serpent et les obstacles sont des cases interdites.
5. **Stratégie de survie** : si aucun chemin vers la nourriture n'est sûr, l'agent suit sa propre queue (tail-chasing via un second appel A*) pour temporiser.
6. Un **flood fill** (BFS) estime l'espace libre accessible pour éviter les culs-de-sac.

**Performances mesurées (80 épisodes) :** score moyen 31.79, meilleur score 42, survie 98.75 %

### Q-Learning (apprentissage par renforcement)

1. **État** : tuple binaire de 11 features calculé via une grille NumPy uint8 :
   - Danger devant / gauche / droite (relatif à la direction actuelle)
   - Direction actuelle (one-hot sur 4 bits)
   - Position relative de la nourriture (haut / bas / gauche / droite)
2. **Q-table** : dictionnaire Python associant chaque état à 4 Q-valeurs (une par direction).
3. **Politique** : epsilon-greedy (ε décroît de 1.0 → 0.01, ×0.995 par épisode).
4. **Mise à jour** : équation de Bellman — `Q(s,a) ← Q(s,a) + α [r + γ max Q(s',a') − Q(s,a)]`.
5. **Récompenses** : +10 (nourriture), −10 (mort), +1 (rapprochement), −1 (éloignement).
6. La Q-table est sauvegardée dans `qtable.json` et rechargée automatiquement.

**Performances mesurées (80 épisodes) :** score moyen 9.10, meilleur score 23, survie 88.75 %

---

## Structure du projet

```
SnakeGAME_final/
├── backend/
│   ├── agents/
│   │   ├── agent_astar.py          # Agent A* : heapq, Manhattan, flood fill, tail-chasing
│   │   ├── agent_rl.py             # Agent Q-Learning : Q-table JSON, 11 features NumPy uint8
│   │   └── base_agent.py           # Classe abstraite Agent + AgentAleatoire
│   ├── game_engine/
│   │   ├── direction.py            # Enum Direction (HAUT/BAS/GAUCHE/DROITE) avec dx/dy
│   │   ├── grille.py               # Grille 25×25 + to_numpy_grid() NumPy uint8
│   │   ├── moteur.py               # MoteurJeu : step(), reset(), cause_mort
│   │   ├── serpent.py              # Logique du serpent (corps list[dict])
│   │   ├── nourriture.py           # Classe Nourriture (diagramme de classes)
│   │   ├── obstacle.py             # Classe Obstacle statique/dynamique
│   │   ├── collecteur_statistiques.py  # Agrégation statistiques parties
│   │   └── controleur_jeu.py       # Façade ControleurJeu
│   ├── models/
│   │   ├── agent.py                # ORM Table agents
│   │   ├── game.py                 # ORM Table games
│   │   ├── game_event.py           # ORM Table game_events
│   │   ├── rl_training.py          # ORM Table rl_training
│   │   └── stats.py                # ORM Table agent_stats
│   ├── routes/
│   │   ├── game_routes.py          # /api/game
│   │   ├── agents_routes.py        # /api/agent (init, step, save)
│   │   ├── stats_routes.py         # /api/stats (comparison, history, replay)
│   │   └── training_routes.py      # /api/training (run, results)
│   ├── tests/
│   │   ├── test_classes_diagramme.py  # 39 tests diagramme de classes
│   │   ├── test_functional.py      # E2E sessions complètes
│   │   ├── test_integration.py     # SQLite + latences
│   │   └── test_websocket.py       # Tests WebSocket
│   ├── training/
│   │   └── trainer.py              # Boucle entraînement RL + sauvegarde BDD
│   ├── config.py                   # Paramètres globaux (GRID_SIZE=25, RL params, CORS)
│   ├── database.py                 # Engine SQLite + SessionLocal + seed 3 agents
│   ├── main.py                     # App FastAPI, CORS, /ws, montage routeurs
│   └── websocket_handler.py        # Boucle WebSocket asynchrone (delta protocol, orjson)
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── App.jsx             # Routeur SPA (WelcomeScreen / vues)
│       │   ├── BattleArena.jsx     # Duel A* vs RL + graphiques Recharts
│       │   ├── ControlPanel.jsx    # Start/Pause/Reset/Mode/Vitesse
│       │   ├── Dashboard.jsx       # Score/steps/mode/état temps réel
│       │   ├── GameGrid.jsx        # Container ResizeObserver → Snake
│       │   ├── Snake.jsx           # Canvas bi-couche (fond + entités + FPS)
│       │   ├── StatsComparison.jsx # Stats comparatives + export CSV/JSON
│       │   └── TrainingPanel.jsx   # Entraînement RL/A* + toggle performance
│       ├── hooks/
│       │   ├── useWebSocket.js     # Connexion WS, dispatch Redux, delta/full state
│       │   └── useKeyboard.js      # Flèches + ZQSD → direction via WS
│       ├── services/
│       │   ├── api.js              # Axios, base URL http://localhost:8000
│       │   └── websocket.js        # WSService + backoff exponentiel reconnexion
│       ├── store/
│       │   ├── gameSlice.js        # setGameState / applyDelta / setMode
│       │   ├── statsSlice.js       # fetchTrainingResults (createAsyncThunk)
│       │   ├── wsSlice.js          # connected, lastMessage
│       │   └── uiSlice.js          # speed, view
│       └── tests/
│           ├── setup.js            # Mocks globaux : ResizeObserver + Canvas getContext
│           ├── gameSlice.test.js
│           ├── uiSlice.test.js
│           ├── Dashboard.test.jsx
│           ├── BattleArena.test.jsx
│           └── TrainingPanel.test.jsx
├── tests/                          # Tests backend pytest (racine)
│   ├── test_serpent.py
│   ├── test_grille.py
│   ├── test_moteur.py
│   ├── test_astar.py
│   ├── test_rl.py
│   └── test_api.py
├── docs/
│   ├── Manuel d'utilisation.pdf    # Manuel utilisateur complet
│   ├── manuel_installation.pdf     # Guide d'installation Windows/Linux/macOS
│   └── schema_base_de_donnees.pdf  # Schéma BDD + requêtes types
├── start.bat                       # Lancement automatique Windows
├── start.sh                        # Lancement automatique Linux
├── start.command                   # Lancement automatique macOS
├── qtable.json                     # Q-table entraînée (rechargée au démarrage)
└── snake.db                        # Base SQLite (générée au premier lancement)
```

---

## Base de données

La base SQLite (`snake.db`) est créée automatiquement au démarrage du backend à la **racine du projet**.

| Table | Contenu |
|---|---|
| `agents` | 3 agents : humain, astar, rl (créés automatiquement) |
| `games` | Parties jouées (score, durée, cause_mort, longueur_serpent, taille_grille…) |
| `game_events` | Événements détaillés par partie (move, food, collision) |
| `agent_stats` | Statistiques agrégées par agent (score moyen, meilleur score, taux de survie) |
| `rl_training` | Historique des épisodes d'entraînement RL (score, epsilon, alpha…) |

> Si vous avez une base existante sans les nouvelles tables, supprimez `snake.db` et relancez le backend.

---

## Documentation

Les documents sont disponibles dans le dossier `docs/` :

| Fichier | Description |
|---|---|
| `docs/Manuel d'utilisation.pdf` | Manuel utilisateur complet (modes, contrôles, interface) |
| `docs/manuel_installation.pdf` | Guide d'installation détaillé Windows / Linux / macOS |
| `docs/schema_base_de_donnees.pdf` | Schéma de la base de données SQLite et requêtes types |

---

## Dépannage

| Problème | Solution |
|---|---|
| `uvicorn: command not found` | `pip install uvicorn` dans l'environnement Python actif |
| Erreur CORS au lancement | Vérifier que le frontend tourne sur le port 5174 (ou ajouter le port dans `config.py`) |
| WebSocket déconnecté | Relancer le backend, puis rafraîchir le frontend |
| Q-table vide / mauvaises performances RL | Lancer un entraînement depuis le panneau Entraînement (au moins 50 épisodes) |
| `snake.db` avec tables manquantes | Supprimer `snake.db`, relancer `uvicorn main:app --reload --port 8000` |
| Tests frontend échouent | Lancer `npm install` dans `frontend/` puis `npm test` |
| Tests backend échouent | Lancer depuis la racine avec `python -m pytest tests/ backend/tests/ -v` |
| macOS : `start.command` bloqué | Clic droit → Ouvrir → Ouvrir quand même |
| Python introuvable sur Linux/macOS | Utiliser `python3` et `pip3` à la place de `python` et `pip` |
