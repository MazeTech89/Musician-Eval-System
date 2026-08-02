import React, { useEffect, useMemo, useState } from "react";
import api from "../api/axios";
import AppHeader from "../components/AppHeader";

interface MusicianUser {
  id: number;
  username: string;
  first_name: string | null;
  last_name: string | null;
  email: string;
  instrument_type: string | null;
  skill_level: string | null;
  availability: string | null;
  is_active: boolean;
  role: string;
}

interface Performance {
  id: number;
  title: string;
  musician_id: number;
  assignment_id: number | null;
  submitted_at: string;
  status: string;
}

interface EvaluationFromApi {
  id: number;
  performance_id: number;
  score: number | null;
  status: string;
  created_at: string;
  performance: Performance;
}

interface Assignment {
  id: number;
  title: string;
}

interface MusicianRow {
  musician: MusicianUser;
  submissions: Array<{
    evaluationId: number;
    performanceTitle: string;
    taskTitle: string;
    score: number | null;
    status: string;
    submittedAt: string;
  }>;
  bestScore: number | null;
  avgScore: number | null;
  totalSubmissions: number;
}

function scoreBadgeClass(score: number): string {
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

const MusicianResults: React.FC = () => {
  const [users, setUsers] = useState<MusicianUser[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationFromApi[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    Promise.all([
      api.get<MusicianUser[]>("/users"),
      api.get<EvaluationFromApi[]>("/evaluations"),
      api.get<Assignment[]>("/assignments"),
    ])
      .then(([usersRes, evalRes, assignRes]) => {
        setUsers(usersRes.data.filter((u) => u.role === "musician"));
        setEvaluations(evalRes.data);
        setAssignments(assignRes.data);
      })
      .catch(() => setError("Failed to load musician results."))
      .finally(() => setLoading(false));
  }, []);

  const assignmentById = useMemo(
    () => new Map(assignments.map((a) => [a.id, a.title])),
    [assignments],
  );

  const musicianRows = useMemo<MusicianRow[]>(() => {
    return users.map((musician) => {
      const myEvals = evaluations.filter(
        (e) => e.performance.musician_id === musician.id,
      );
      const scored = myEvals.filter((e) => e.score !== null && e.score !== undefined);
      const scores = scored.map((e) => e.score as number);
      const bestScore = scores.length > 0 ? Math.max(...scores) : null;
      const avgScore = scores.length > 0 ? scores.reduce((s, v) => s + v, 0) / scores.length : null;

      const submissions = myEvals
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .map((e) => ({
          evaluationId: e.id,
          performanceTitle: e.performance.title,
          taskTitle: e.performance.assignment_id
            ? (assignmentById.get(e.performance.assignment_id) ?? "Unknown task")
            : "Direct upload",
          score: e.score,
          status: e.status,
          submittedAt: e.performance.submitted_at,
        }));

      return { musician, submissions, bestScore, avgScore, totalSubmissions: myEvals.length };
    });
  }, [users, evaluations, assignmentById]);

  const filteredRows = useMemo(() => {
    if (!search.trim()) return musicianRows;
    const q = search.toLowerCase();
    return musicianRows.filter(
      (r) =>
        r.musician.username.toLowerCase().includes(q) ||
        (r.musician.first_name ?? "").toLowerCase().includes(q) ||
        (r.musician.last_name ?? "").toLowerCase().includes(q) ||
        (r.musician.instrument_type ?? "").toLowerCase().includes(q),
    );
  }, [musicianRows, search]);

  const sortedRows = useMemo(
    () =>
      [...filteredRows].sort((a, b) => {
        if (b.bestScore === null && a.bestScore === null) return 0;
        if (b.bestScore === null) return -1;
        if (a.bestScore === null) return 1;
        return b.bestScore - a.bestScore;
      }),
    [filteredRows],
  );

  return (
    <div className="min-h-screen staff-bg" style={{ backgroundColor: "var(--bg-page)" }}>
      <AppHeader title="Musician Evaluation System" subtitle="Musician Results" />

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Hero */}
        <div
          className="rounded-2xl p-8 mb-8 text-white relative overflow-hidden"
          style={{ background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%)" }}
        >
          <span className="text-5xl absolute right-8 top-6 opacity-20 pointer-events-none select-none">📊</span>
          <h2 className="text-3xl font-bold mb-2 font-display">Musician Performance Results</h2>
          <p className="text-indigo-200 max-w-xl">
            AI-generated scores for every musician's submission. Click a row to expand individual submission history.
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="wave-bars">{[1,2,3,4,5,6].map((i) => <span key={i} />)}</div>
            <span className="ml-4 text-gray-500">Loading results…</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 rounded-xl p-4 mb-6">{error}</div>
        )}

        {!loading && !error && (
          <>
            {/* Search */}
            <div className="mb-4">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="🔍  Search by name, username, or instrument…"
                className="w-full max-w-md rounded-lg border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
            </div>

            {sortedRows.length === 0 ? (
              <div className="bg-white rounded-2xl shadow p-10 text-center">
                <p className="text-5xl mb-4">🎵</p>
                <p className="text-gray-500">
                  {search ? "No musicians match your search." : "No musician accounts found."}
                </p>
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-md overflow-hidden">
                <table className="min-w-full divide-y divide-gray-100">
                  <thead>
                    <tr style={{ backgroundColor: "var(--color-primary)" }}>
                      {["#", "Musician", "Instrument", "Skill Level", "Availability", "Submissions", "Best Score", "Avg Score", ""].map((h) => (
                        <th key={h} className="px-5 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {sortedRows.map((row, idx) => (
                      <React.Fragment key={row.musician.id}>
                        {/* Musician summary row */}
                        <tr
                          className={`cursor-pointer transition ${
                            expandedId === row.musician.id ? "bg-amber-50" : idx % 2 === 0 ? "bg-white" : "bg-gray-50"
                          } hover:bg-amber-50`}
                          onClick={() =>
                            setExpandedId(expandedId === row.musician.id ? null : row.musician.id)
                          }
                        >
                          <td className="px-5 py-4 text-sm text-gray-400 font-medium">{idx + 1}</td>
                          <td className="px-5 py-4">
                            <div className="font-semibold text-sm" style={{ color: "var(--color-primary)" }}>
                              {row.musician.first_name && row.musician.last_name
                                ? `${row.musician.first_name} ${row.musician.last_name}`
                                : row.musician.username}
                            </div>
                            <div className="text-xs text-gray-400">@{row.musician.username}</div>
                            <div className="text-xs text-gray-400">{row.musician.email}</div>
                          </td>
                          <td className="px-5 py-4 text-sm capitalize text-gray-600">
                            {row.musician.instrument_type ?? <span className="text-gray-300">—</span>}
                          </td>
                          <td className="px-5 py-4 text-sm capitalize text-gray-600">
                            {row.musician.skill_level ?? <span className="text-gray-300">—</span>}
                          </td>
                          <td className="px-5 py-4 text-sm capitalize text-gray-600">
                            {row.musician.availability ?? <span className="text-gray-300">—</span>}
                          </td>
                          <td className="px-5 py-4 text-sm text-center font-medium" style={{ color: "var(--color-primary)" }}>
                            {row.totalSubmissions}
                          </td>
                          <td className="px-5 py-4">
                            {row.bestScore !== null ? (
                              <span className={`score-badge ${scoreBadgeClass(row.bestScore)}`}>
                                {Math.round(row.bestScore)}
                              </span>
                            ) : (
                              <span className="text-sm text-gray-300 italic">No score</span>
                            )}
                          </td>
                          <td className="px-5 py-4 text-sm text-gray-600">
                            {row.avgScore !== null ? `${row.avgScore.toFixed(1)}` : <span className="text-gray-300">—</span>}
                          </td>
                          <td className="px-5 py-4 text-sm text-amber-500">
                            {row.totalSubmissions > 0 ? (expandedId === row.musician.id ? "▲" : "▼") : ""}
                          </td>
                        </tr>

                        {/* Expanded submission history */}
                        {expandedId === row.musician.id && row.submissions.length > 0 && (
                          <tr>
                            <td colSpan={9} className="bg-amber-50 px-5 py-4">
                              <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "var(--color-primary)" }}>
                                Submission history for {row.musician.first_name ?? row.musician.username}
                              </p>
                              <table className="w-full text-sm divide-y divide-amber-200">
                                <thead>
                                  <tr className="text-left text-xs font-semibold text-gray-500">
                                    <th className="pb-2 pr-6">Performance</th>
                                    <th className="pb-2 pr-6">Task</th>
                                    <th className="pb-2 pr-6">Submitted</th>
                                    <th className="pb-2 pr-6">Status</th>
                                    <th className="pb-2">AI Score</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-amber-100">
                                  {row.submissions.map((s) => (
                                    <tr key={s.evaluationId}>
                                      <td className="py-2 pr-6 font-medium text-gray-700">{s.performanceTitle}</td>
                                      <td className="py-2 pr-6 text-gray-500">{s.taskTitle}</td>
                                      <td className="py-2 pr-6 text-gray-500">{formatDate(s.submittedAt)}</td>
                                      <td className="py-2 pr-6">
                                        <span
                                          className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                                            s.status === "completed"
                                              ? "bg-green-100 text-green-700"
                                              : s.status === "pending"
                                              ? "bg-yellow-100 text-yellow-700"
                                              : "bg-gray-100 text-gray-600"
                                          }`}
                                        >
                                          {s.status}
                                        </span>
                                      </td>
                                      <td className="py-2">
                                        {s.score !== null ? (
                                          <span className={`score-badge ${scoreBadgeClass(s.score)}`} style={{ width: "2.5rem", height: "2.5rem", fontSize: "0.75rem" }}>
                                            {Math.round(s.score)}
                                          </span>
                                        ) : (
                                          <span className="text-gray-400 italic text-xs">Pending</span>
                                        )}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default MusicianResults;
