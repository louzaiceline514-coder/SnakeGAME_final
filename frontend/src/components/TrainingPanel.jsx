import React, { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { api } from "../services/api";
import { fetchTrainingResults } from "../store/statsSlice";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

function TrainingPanel() {
  const [episodes, setEpisodes] = useState(80);
  const [withObstacles, setWithObstacles] = useState(true);
  const [loading, setLoading] = useState("");
  const dispatch = useDispatch();
  const {
    rlTrainingScores,
    astarBenchmarkScores,
    rlTrainingSummary,
    astarBenchmarkSummary
  } = useSelector((state) => state.stats);

  useEffect(() => {
    dispatch(fetchTrainingResults());
  }, [dispatch]);

  const handleRun = async (agentType) => {
    setLoading(agentType);
    try {
      await api.post("/api/training/start", { episodes, agent_type: agentType, with_obstacles: withObstacles });
      await dispatch(fetchTrainingResults());
    } finally {
      setLoading("");
    }
  };

  const lineData = useMemo(() => {
    const maxLength = Math.max(rlTrainingScores.length, astarBenchmarkScores.length);
    return Array.from({ length: maxLength }, (_, index) => ({
      episode: index + 1,
      rl: rlTrainingScores[index] ?? null,
      astar: astarBenchmarkScores[index] ?? null
    }));
  }, [rlTrainingScores, astarBenchmarkScores]);

  const summaryData = [
    {
      name: "Q-Learning",
      avg: Number((rlTrainingSummary.avg_score ?? 0).toFixed(2)),
      best: rlTrainingSummary.best_score ?? 0,
      survival: Number(((rlTrainingSummary.survival_rate ?? 0) * 100).toFixed(1))
    },
    {
      name: "A*",
      avg: Number((astarBenchmarkSummary.avg_score ?? 0).toFixed(2)),
      best: astarBenchmarkSummary.best_score ?? 0,
      survival: Number(((astarBenchmarkSummary.survival_rate ?? 0) * 100).toFixed(1))
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">Entrainement et analyse des algorithmes</h2>
        <p className="text-sm text-slate-400 mt-1">
          Cette section compare un vrai entrainement Q-Learning avec un benchmark A* sur plusieurs
          episodes, sans polluer les statistiques du mode Jeu.
        </p>
      </div>

      <div className="grid xl:grid-cols-2 gap-4">
        <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4 space-y-4">
          <h3 className="text-sm font-medium text-emerald-300">Q-Learning</h3>
          <p className="text-xs text-slate-400">
            Lance un entrainement reel du modele RL et observe la progression episode par episode.
          </p>
          <button
            onClick={() => handleRun("rl")}
            disabled={loading !== ""}
            className="w-full px-3 py-2 rounded bg-emerald-500 text-slate-950 text-sm font-semibold disabled:opacity-50"
          >
            {loading === "rl" ? "Entrainement RL en cours..." : "Entrainer Q-Learning"}
          </button>
        </div>

        <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4 space-y-4">
          <h3 className="text-sm font-medium text-sky-300">A*</h3>
          <p className="text-xs text-slate-400">
            Lance un benchmark repetable sur plusieurs episodes pour mesurer les performances de A*.
          </p>
          <button
            onClick={() => handleRun("astar")}
            disabled={loading !== ""}
            className="w-full px-3 py-2 rounded bg-sky-500 text-slate-950 text-sm font-semibold disabled:opacity-50"
          >
            {loading === "astar" ? "Benchmark A* en cours..." : "Benchmarker A*"}
          </button>
        </div>
      </div>

      <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4 space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-100">Nombre d&apos;épisodes</p>
            <p className="text-xs text-slate-400">
              Même volume de test pour comparer proprement les deux algorithmes.
            </p>
          </div>
          <input
            type="number"
            value={episodes}
            onChange={(e) => setEpisodes(parseInt(e.target.value, 10) || 0)}
            className="w-32 bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-100 text-sm"
            min={10}
            max={100}
          />
        </div>
        <div className="flex items-center justify-between gap-4 border-t border-slate-700 pt-4">
          <div>
            <p className="text-sm font-medium text-slate-100">Mode performance (sans obstacles)</p>
            <p className="text-xs text-slate-400">
              Désactive tous les obstacles pour mesurer les performances maximales.
            </p>
          </div>
          <button
            onClick={() => setWithObstacles((v) => !v)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${withObstacles ? "bg-slate-600" : "bg-emerald-500"}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${withObstacles ? "translate-x-1" : "translate-x-6"}`}
            />
          </button>
        </div>
        {!withObstacles && (
          <p className="text-xs text-amber-300 bg-amber-500/10 rounded-lg px-3 py-2 border border-amber-500/20">
            Mode performance actif grille sans obstacles.
          </p>
        )}
      </div>

      <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard
          title="RL moyen"
          value={rlTrainingSummary.avg_score?.toFixed(2) ?? "0.00"}
          accent="text-emerald-400"
        />
        <MetricCard
          title="RL meilleur"
          value={rlTrainingSummary.best_score ?? 0}
          accent="text-emerald-400"
        />
        <MetricCard
          title="A* moyen"
          value={astarBenchmarkSummary.avg_score?.toFixed(2) ?? "0.00"}
          accent="text-sky-400"
        />
        <MetricCard
          title="A* meilleur"
          value={astarBenchmarkSummary.best_score ?? 0}
          accent="text-sky-400"
        />
      </div>

      <div className="grid xl:grid-cols-2 gap-4">
        <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4 h-[360px]">
          <p className="text-sm font-medium text-slate-100 mb-1">Courbe des episodes</p>
          <p className="text-xs text-slate-400 mb-4">
            Comparaison directe des scores obtenus pendant l&apos;entrainement RL et le benchmark A*.
          </p>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={lineData}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="episode" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="rl" name="Q-Learning" stroke="#22c55e" dot={false} />
              <Line type="monotone" dataKey="astar" name="A*" stroke="#38bdf8" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4 h-[360px]">
          <p className="text-sm font-medium text-slate-100 mb-1">Synthese des performances</p>
          <p className="text-xs text-slate-400 mb-4">
            Score moyen, meilleur score et taux de survie pour chaque algorithme.
          </p>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={summaryData}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip />
              <Legend />
              <Bar dataKey="avg" fill="#10b981" name="Score moyen" />
              <Bar dataKey="best" fill="#a855f7" name="Meilleur score" />
              <Bar dataKey="survival" fill="#38bdf8" name="Taux de survie (%)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, accent }) {
  return (
    <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{title}</p>
      <p className={`mt-2 text-2xl font-semibold ${accent}`}>{value}</p>
    </div>
  );
}

export default TrainingPanel;
