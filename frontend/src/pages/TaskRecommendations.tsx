import React, { useEffect, useState } from "react";
import AppHeader from "../components/AppHeader";
import api from "../api/axios";

interface BestMusician {
  id: number;
  username: string;
  first_name: string | null;
  last_name: string | null;
  instrument_type: string | null;
  skill_level: string | null;
  score: number;
}

interface TaskRecommendation {
  assignment_id: number;
  assignment_title: string;
  description: string | null;
  reference_track_title: string | null;
  total_submissions: number;
  best_musician: BestMusician | null;
}

function scoreBadgeClass(score: number): string {
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

const TaskRecommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<TaskRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<TaskRecommendation[]>("/assignments/recommendations")
      .then((res) => setRecommendations(res.data))
      .catch(() => setError("Failed to load recommendations."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen staff-bg" style={{ backgroundColor: "var(--bg-page)" }}>
      <AppHeader title="Musician Evaluation System" subtitle="Task Rankings" />

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Page header */}
        <div
          className="rounded-2xl p-8 mb-8 text-white relative overflow-hidden"
          style={{ background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%)" }}
        >
          <span className="text-5xl absolute right-8 top-6 opacity-20 pointer-events-none select-none">🏆</span>
          <h2 className="text-3xl font-bold mb-2 font-display">Task Rankings</h2>
          <p className="text-indigo-200 max-w-xl">
            AI-scored recommendations — the best musician for each active task based on performance scores.
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="wave-bars">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <span key={i} />
              ))}
            </div>
            <span className="ml-4 text-gray-500">Loading rankings…</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 rounded-xl p-4 mb-6">{error}</div>
        )}

        {!loading && !error && recommendations.length === 0 && (
          <div className="bg-white rounded-2xl shadow p-10 text-center">
            <p className="text-5xl mb-4">🎵</p>
            <p className="text-gray-500">
              No scored submissions yet. Once musicians submit performances and the AI scores them, rankings will appear here.
            </p>
          </div>
        )}

        {!loading && recommendations.length > 0 && (
          <div className="overflow-hidden rounded-2xl shadow-md bg-white">
            <table className="min-w-full divide-y divide-gray-100">
              <thead>
                <tr style={{ backgroundColor: "var(--color-primary)" }}>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">#</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">Task</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">Reference Track</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">Submissions</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">Best Musician</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">Instrument</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">Skill</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {recommendations.map((rec, idx) => (
                  <tr key={rec.assignment_id} className={idx % 2 === 0 ? "bg-white" : "bg-amber-50"}>
                    <td className="px-6 py-4 text-sm text-gray-400 font-medium">{idx + 1}</td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-sm" style={{ color: "var(--color-primary)" }}>
                        {rec.assignment_title}
                      </p>
                      {rec.description ? (
                        <p className="text-xs text-gray-400 mt-0.5 max-w-xs truncate">{rec.description}</p>
                      ) : null}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {rec.reference_track_title ?? <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-6 py-4 text-sm text-center font-medium" style={{ color: "var(--color-primary)" }}>
                      {rec.total_submissions}
                    </td>
                    <td className="px-6 py-4">
                      {rec.best_musician ? (
                        <div>
                          <p className="font-semibold text-sm" style={{ color: "var(--color-primary)" }}>
                            {rec.best_musician.first_name && rec.best_musician.last_name
                              ? `${rec.best_musician.first_name} ${rec.best_musician.last_name}`
                              : rec.best_musician.username}
                          </p>
                          <p className="text-xs text-gray-400">@{rec.best_musician.username}</p>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-300 italic">No scored submissions</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm capitalize text-gray-600">
                      {rec.best_musician?.instrument_type ?? <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-6 py-4 text-sm capitalize text-gray-600">
                      {rec.best_musician?.skill_level ?? <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-6 py-4">
                      {rec.best_musician ? (
                        <span className={`score-badge ${scoreBadgeClass(rec.best_musician.score)}`}>
                          {Math.round(rec.best_musician.score)}
                        </span>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
};

export default TaskRecommendations;
