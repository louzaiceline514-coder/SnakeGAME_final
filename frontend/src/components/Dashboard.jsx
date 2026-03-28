import React from "react";
import { useSelector } from "react-redux";

// tableau de bord temps réel pour la partie en cours.

// charte : couleur du mode selon l'agent
const modeLabel = { manual: "Manuel", astar: "A*", rl: "Q-Learning", random: "Aléatoire" };
const modeColor = { manual: "text-emerald-400", astar: "text-blue-400", rl: "text-violet-400", random: "text-amber-400" };

function Dashboard() {
  const { score, stepCount, mode, gameOver } = useSelector((state) => state.game);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-3 h-full">
      {/* Charte : Poppins pour les titres */}
      <h2 className="text-sm font-semibold text-slate-100 font-title">Dashboard temps réel</h2>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-slate-700/50 rounded-lg p-2">
          <p className="text-slate-400">Score actuel</p>
          {/* Charte : Emerald = Joueur/Serpent, JetBrains Mono pour les stats */}
          <p className="text-lg font-semibold text-emerald-400 font-mono">{score}</p>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-2">
          <p className="text-slate-400">Steps</p>
          {/* Charte : Blue = accent primaire A*, utilisé pour les stats neutres */}
          <p className="text-lg font-semibold text-blue-400 font-mono">{stepCount}</p>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-2">
          <p className="text-slate-400">Mode</p>
          {/* Charte : couleur selon l'agent actif */}
          <p className={`text-sm font-semibold ${modeColor[mode] || "text-slate-100"}`}>
            {modeLabel[mode] || mode}
          </p>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-2">
          <p className="text-slate-400">État</p>
          {/* Charte : Red = Collision/Danger, Emerald = succès */}
          <p className={`text-sm font-semibold ${gameOver ? "text-red-400" : "text-emerald-400"}`}>
            {gameOver ? "Terminé" : "En cours"}
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
