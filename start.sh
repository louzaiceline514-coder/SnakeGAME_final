#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          Snake AI - SAE4 UPJV            ║"
echo "║    Installation et lancement automatique ║"
echo "╚══════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python3"
PIP="$VENV/bin/pip"

# --- Verification Python ---
echo "[Verification] Python..."
if ! command -v python3 &>/dev/null; then
    echo " ERREUR : Python3 n'est pas installe."
    echo " Installez-le avec : sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
echo " OK : $(python3 --version)"

# --- Verification Node.js ---
echo "[Verification] Node.js..."
if ! command -v node &>/dev/null; then
    echo " ERREUR : Node.js n'est pas installe."
    echo " Installez-le avec : sudo apt install nodejs npm"
    exit 1
fi
echo " OK : Node.js $(node --version)"

echo ""

# --- Creation de l'environnement virtuel ---
echo "[1/5] Environnement virtuel Python..."
if [ ! -d "$VENV" ]; then
    echo " Creation du venv dans $VENV..."
    python3 -m venv "$VENV"
    if [ $? -ne 0 ]; then
        echo " ERREUR : Impossible de creer le venv."
        echo " Essayez : sudo apt install python3-venv"
        exit 1
    fi
    echo " OK : venv cree."
else
    echo " OK : venv deja present."
fi

# --- Installation deps Python via le venv directement ---
echo "[2/5] Installation des dependances Python..."
"$PIP" install --upgrade pip --quiet
"$PIP" install -r "$SCRIPT_DIR/backend/requirements.txt" --quiet
if [ $? -ne 0 ]; then
    echo " ERREUR : pip install a echoue."
    exit 1
fi
echo " OK : dependances Python installees."

# --- Installation dependances Node.js ---
echo "[3/5] Installation des dependances Node.js..."
ROLLUP_LINUX="$SCRIPT_DIR/frontend/node_modules/@rollup/rollup-linux-x64-gnu"
ROLLUP_MUSL="$SCRIPT_DIR/frontend/node_modules/@rollup/rollup-linux-x64-musl"
# Si node_modules existe sans binaire rollup Linux = installe depuis Windows -> on supprime et reinstalle
if [ -d "$SCRIPT_DIR/frontend/node_modules" ] && [ ! -d "$ROLLUP_LINUX" ] && [ ! -d "$ROLLUP_MUSL" ]; then
    echo " node_modules installe sur Windows (binaires incompatibles). Reinstallation Linux..."
    rm -rf "$SCRIPT_DIR/frontend/node_modules"
fi
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    cd "$SCRIPT_DIR/frontend" && npm install --silent
    if [ $? -ne 0 ]; then
        echo " ERREUR : npm install a echoue."
        exit 1
    fi
    echo " OK : node_modules installe (Linux)."
else
    echo " OK : node_modules deja present."
fi

echo ""

# --- Lancement backend avec le python du venv directement ---
echo "[4/5] Demarrage du backend FastAPI (port 8000)..."
cd "$SCRIPT_DIR/backend"
"$PYTHON" -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 4

# --- Lancement frontend ---
echo "[5/5] Demarrage du frontend Vite..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
sleep 5

# --- Ouverture navigateur ---
echo ""
echo " Ouverture du navigateur..."
xdg-open http://localhost:5174 2>/dev/null || echo " Ouvrez manuellement : http://localhost:5174"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Snake AI est pret !                    ║"
echo "║   http://localhost:5174                  ║"
echo "║                                          ║"
echo "║   Appuyez sur Ctrl+C pour stopper        ║"
echo "╚══════════════════════════════════════════╝"
echo ""

trap "echo '' && echo 'Arret en cours...' && kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
