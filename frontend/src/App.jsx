import React, { useState } from "react";
import GameGrid from "./components/GameGrid";
import ControlPanel from "./components/ControlPanel";
import Dashboard from "./components/Dashboard";
import StatsComparison from "./components/StatsComparison";
import BattleArena from "./components/BattleArena";
import TrainingPanel from "./components/TrainingPanel";
import AmbientAudioControls from "./components/AmbientAudioControls";
import useWebSocket from "./hooks/useWebSocket";
import useKeyboard from "./hooks/useKeyboard";
import useSoundEffects from "./hooks/useSoundEffects";

function App() {
  const [hasEntered, setHasEntered] = useState(false);
  const [view, setView] = useState("game"); // "game" | "battle" | "stats" | "training"
  useWebSocket(hasEntered);
  useKeyboard(hasEntered);
  useSoundEffects();

  if (!hasEntered) {
    return (
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.15),_transparent_35%),linear-gradient(180deg,_#0f172a_0%,_#1e293b_50%,_#0f172a_100%)] text-slate-50 flex items-center justify-center p-6">
        <div className="w-full max-w-4xl rounded-[2rem] border border-blue-500/15 bg-slate-900/80 p-8 md:p-12 text-center space-y-6 shadow-[0_24px_80px_rgba(15,23,42,0.55)]">
          <div className="space-y-3">
            {/* Charte : Poppins pour les titres */}
            <p className="text-sm uppercase tracking-[0.4em] text-blue-400 font-title">SnakeGame</p>
            <h1 className="text-4xl md:text-6xl font-bold font-title">Jeu, duel IA et statistiques réelles</h1>
            <p className="text-slate-300 max-w-2xl mx-auto">
              Comparer le mode manuel, A* et Q-Learning avec des
              parties enregistrées.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4 text-left">
            {/* Charte : Emerald = Joueur */}
            <div className="rounded-2xl border border-emerald-500/25 bg-slate-800/60 p-4">
              <p className="text-sm font-semibold text-emerald-400">Mode Manuel</p>
              <p className="text-xs text-slate-400 mt-2">Interface agrandie pour mieux suivre la partie.</p>
            </div>
            {/* Charte : Blue = A* */}
            <div className="rounded-2xl border border-blue-500/25 bg-slate-800/60 p-4">
              <p className="text-sm font-semibold text-blue-400">Mode A*</p>
              <p className="text-xs text-slate-400 mt-2">Trajectoires optimisées avec obstacles dynamiques.</p>
            </div>
            {/* Charte : Violet = RL */}
            <div className="rounded-2xl border border-violet-500/25 bg-slate-800/60 p-4">
              <p className="text-sm font-semibold text-violet-400">Mode Q-Learning</p>
              <p className="text-xs text-slate-400 mt-2">Comparaison en direct avec statistiques de vraies parties.</p>
            </div>
          </div>

          <button
            onClick={() => setHasEntered(true)}
            className="px-8 py-3 rounded-2xl bg-gradient-to-r from-blue-500 via-violet-500 to-emerald-500 text-white font-semibold font-title transition-transform hover:scale-[1.02]"
          >
            Start
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.10),_transparent_25%),radial-gradient(circle_at_top_right,_rgba(139,92,246,0.10),_transparent_28%),linear-gradient(180deg,_#0f172a_0%,_#1e293b_50%,_#0f172a_100%)]">
      <header className="border-b border-slate-700 px-6 py-4 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between bg-slate-900/80 backdrop-blur">
        <div>
          {/* Charte : Poppins pour le titre principal */}
          <h1 className="text-xl font-bold font-title text-slate-50">Snake AI Dashboard</h1>
          <p className="mt-1 text-xs uppercase tracking-[0.25em] text-slate-500 font-mono">SnakeGame</p>
        </div>
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
          <nav className="space-x-2">
            {/* Charte : Emerald=Joueur, Blue=A*, Violet=RL, Amber=Obstacles/Warning */}
            <button
              onClick={() => setView("game")}
              className={`px-3 py-1 rounded text-sm font-medium ${view === "game"
                ? "bg-emerald-500 text-white"
                : "bg-slate-800 text-slate-300 border border-slate-700 hover:border-slate-600"
                }`}
            >
              Jeu
            </button>
            <button
              onClick={() => setView("battle")}
              className={`px-3 py-1 rounded text-sm font-medium ${view === "battle"
                ? "bg-blue-500 text-white"
                : "bg-slate-800 text-slate-300 border border-slate-700 hover:border-slate-600"
                }`}
            >
              A* vs Q-Learning
            </button>
            <button
              onClick={() => setView("stats")}
              className={`px-3 py-1 rounded text-sm font-medium ${view === "stats"
                ? "bg-violet-500 text-white"
                : "bg-slate-800 text-slate-300 border border-slate-700 hover:border-slate-600"
                }`}
            >
              Analyse
            </button>
            <button
              onClick={() => setView("training")}
              className={`px-3 py-1 rounded text-sm font-medium ${view === "training"
                ? "bg-amber-500 text-white"
                : "bg-slate-800 text-slate-300 border border-slate-700 hover:border-slate-600"
                }`}
            >
              Entraînement
            </button>
          </nav>
          <AmbientAudioControls />
        </div>
      </header>

      {view === "game" ? (
        <main className="flex-1 grid grid-cols-[minmax(0,1fr)_320px] gap-5 p-5 items-stretch">
          <section className="h-full min-w-0 overflow-hidden">
            <div className="bg-slate-900/80 border border-slate-700 rounded-[2rem] p-5 flex flex-col min-h-[80vh] h-full shadow-[0_20px_80px_rgba(2,6,23,0.45)] overflow-hidden">
              <GameGrid />
            </div>
          </section>
          <section className="grid gap-4 auto-rows-fr h-full">
            <div className="h-full">
              <ControlPanel />
            </div>
            <div className="h-full">
              <Dashboard />
            </div>
          </section>
        </main>
      ) : view === "battle" ? (
        <main className="flex-1 p-5">
          <BattleArena />
        </main>
      ) : view === "stats" ? (
        <main className="flex-1 p-5">
          <section className="bg-slate-950/65 border border-slate-800 rounded-[2rem] p-5 shadow-[0_20px_80px_rgba(2,6,23,0.45)]">
            <StatsComparison />
          </section>
        </main>
      ) : view === "training" ? (
        <main className="flex-1 p-5">
          <section className="bg-slate-950/65 border border-slate-800 rounded-[2rem] p-5 shadow-[0_20px_80px_rgba(2,6,23,0.45)]">
            <TrainingPanel />
          </section>
        </main>
      ) : null}
    </div>
  );
}

export default App;
