import React, { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  ChevronDown,
  ChevronUp,
  Loader2,
  RefreshCw,
  Search,
} from "lucide-react";
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
    performanceId: number;
    assignmentId: number | null;
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
  // Thresholds mirror the visual color-coding used across the admin results/rankings views.
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

const MusicianResults: React.FC = () => {
  const [users, setUsers] = useState<MusicianUser[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationFromApi[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [rescoringEvaluationId, setRescoringEvaluationId] = useState<
    number | null
  >(null);

  const reloadResults = async () => {
    const [usersRes, evalRes, assignRes] = await Promise.all([
      api.get<MusicianUser[]>("/auth/users"),
      api.get<EvaluationFromApi[]>("/evaluations"),
      api.get<Assignment[]>("/assignments"),
    ]);
    setUsers(usersRes.data.filter((u) => u.role === "musician"));
    setEvaluations(evalRes.data);
    setAssignments(assignRes.data);
  };

  useEffect(() => {
    reloadResults()
      .catch(() => setError("Failed to load musician results."))
      .finally(() => setLoading(false));
  }, []);

  const handleRescore = async (
    evaluationId: number,
    assignmentId: number | null,
    performanceId: number,
  ) => {
    if (!assignmentId) {
      setError(
        "This submission is not linked to a task, so it cannot be re-scored here.",
      );
      return;
    }

    setError(null);
    setSuccess(null);
    setRescoringEvaluationId(evaluationId);
    try {
      const response = await api.post(
        `/assignments/${assignmentId}/performances/${performanceId}/analyze`,
      );
      const newEvaluationId: number = response.data.evaluation_id;

      // Scoring runs as a background task, so poll the new evaluation until it leaves "pending".
      const maxAttempts = 40; // ~2 minutes at 3s intervals
      let finalStatus: string | null = null;
      for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 3000));
        const evalStatusResponse = await api.get(
          `/evaluations/${newEvaluationId}`,
        );
        if (evalStatusResponse.data.status !== "pending") {
          finalStatus = evalStatusResponse.data.status;
          break;
        }
      }

      await reloadResults();

      if (finalStatus === "completed") {
        setSuccess("Scoring was re-run successfully.");
      } else if (finalStatus === "cancelled") {
        setError(
          "Re-scoring failed. Make sure the task has a valid reference track.",
        );
      } else {
        setError(
          "Re-scoring is taking longer than expected. Refresh shortly to see the result.",
        );
      }
    } catch (err) {
      setError(
        "Failed to re-run scoring. Make sure the task has a valid reference track.",
      );
    } finally {
      setRescoringEvaluationId(null);
    }
  };

  const assignmentById = useMemo(
    () => new Map(assignments.map((a) => [a.id, a.title])),
    [assignments],
  );

  const musicianRows = useMemo<MusicianRow[]>(() => {
    return users.map((musician) => {
      const myEvals = evaluations.filter(
        (e) => e.performance.musician_id === musician.id,
      );
      const scored = myEvals.filter(
        (e) => e.score !== null && e.score !== undefined,
      );
      const scores = scored.map((e) => e.score as number);
      const bestScore = scores.length > 0 ? Math.max(...scores) : null;
      const avgScore =
        scores.length > 0
          ? scores.reduce((s, v) => s + v, 0) / scores.length
          : null;

      const submissions = myEvals
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        )
        .map((e) => ({
          evaluationId: e.id,
          performanceId: e.performance.id,
          assignmentId: e.performance.assignment_id,
          performanceTitle: e.performance.title,
          taskTitle: e.performance.assignment_id
            ? (assignmentById.get(e.performance.assignment_id) ??
              "Unknown task")
            : "Direct upload",
          score: e.score,
          status: e.status,
          submittedAt: e.performance.submitted_at,
        }));

      return {
        musician,
        submissions,
        bestScore,
        avgScore,
        totalSubmissions: myEvals.length,
      };
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
        // Musicians with no completed score yet are pushed to the bottom rather than
        // sorting as 0, so "no submissions" isn't visually indistinguishable from "failed".
        if (b.bestScore === null && a.bestScore === null) return 0;
        if (b.bestScore === null) return -1;
        if (a.bestScore === null) return 1;
        return b.bestScore - a.bestScore;
      }),
    [filteredRows],
  );

  return (
    <div
      className="min-h-screen staff-bg"
      style={{ backgroundColor: "var(--bg-page)" }}
    >
      <AppHeader title="Perform Pro" subtitle="Musician Results" />

      <main className="mx-auto max-w-7xl px-3 py-6 sm:px-6 sm:py-8 lg:px-8">
        {/* Hero */}
        <div className="perform-pro-hero rounded-2xl p-8 mb-8 text-white">
          <BarChart3
            className="absolute right-24 top-6 h-12 w-12 opacity-20"
            aria-hidden="true"
          />
          <div className="flex items-center gap-3">
            <BarChart3 className="h-8 w-8 text-rose-100" aria-hidden="true" />
            <h2 className="text-3xl font-bold font-display">
              Musician Performance Results
            </h2>
          </div>
          <p className="max-w-xl text-cyan-100">
            AI-generated scores for every musician's submission. Click a row to
            expand individual submission history.
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="wave-bars">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <span key={i} />
              ))}
            </div>
            <span className="ml-4 text-gray-500">Loading results...</span>
          </div>
        )}

        {success && (
          <div className="mb-6 rounded-xl bg-green-50 p-4 text-green-700">
            {success}
          </div>
        )}
        {error && (
          <div className="bg-red-50 text-red-700 rounded-xl p-4 mb-6">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Search */}
            <div className="mb-4">
              <label className="relative block w-full max-w-md">
                <Search
                  className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400"
                  aria-hidden="true"
                />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by name, username, or instrument..."
                  className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </label>
            </div>

            {sortedRows.length === 0 ? (
              <div className="bg-white rounded-2xl shadow p-10 text-center">
                <BarChart3
                  className="mx-auto mb-4 h-12 w-12 text-amber-600"
                  aria-hidden="true"
                />
                <p className="text-gray-500">
                  {search
                    ? "No musicians match your search."
                    : "No musician accounts found."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl bg-white shadow-md">
                <table className="min-w-full divide-y divide-gray-100">
                  <thead>
                    <tr style={{ backgroundColor: "var(--color-primary)" }}>
                      {[
                        "#",
                        "Musician",
                        "Instrument",
                        "Skill Level",
                        "Availability",
                        "Submissions",
                        "Best Score",
                        "Avg Score",
                        "",
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-5 py-4 text-left text-xs font-bold uppercase tracking-widest text-amber-300"
                        >
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
                            expandedId === row.musician.id
                              ? "bg-amber-50"
                              : idx % 2 === 0
                                ? "bg-white"
                                : "bg-gray-50"
                          } hover:bg-amber-50`}
                          onClick={() =>
                            setExpandedId(
                              expandedId === row.musician.id
                                ? null
                                : row.musician.id,
                            )
                          }
                        >
                          <td className="px-5 py-4 text-sm text-gray-400 font-medium">
                            {idx + 1}
                          </td>
                          <td className="px-5 py-4">
                            <div
                              className="font-semibold text-sm"
                              style={{ color: "var(--color-primary)" }}
                            >
                              {row.musician.first_name && row.musician.last_name
                                ? `${row.musician.first_name} ${row.musician.last_name}`
                                : row.musician.username}
                            </div>
                            <div className="text-xs text-gray-400">
                              @{row.musician.username}
                            </div>
                            <div className="text-xs text-gray-400">
                              {row.musician.email}
                            </div>
                          </td>
                          <td className="px-5 py-4 text-sm capitalize text-gray-600">
                            {row.musician.instrument_type ?? (
                              <span className="text-gray-300">Not set</span>
                            )}
                          </td>
                          <td className="px-5 py-4 text-sm capitalize text-gray-600">
                            {row.musician.skill_level ?? (
                              <span className="text-gray-300">Not set</span>
                            )}
                          </td>
                          <td className="px-5 py-4 text-sm capitalize text-gray-600">
                            {row.musician.availability ?? (
                              <span className="text-gray-300">Not set</span>
                            )}
                          </td>
                          <td
                            className="px-5 py-4 text-sm text-center font-medium"
                            style={{ color: "var(--color-primary)" }}
                          >
                            {row.totalSubmissions}
                          </td>
                          <td className="px-5 py-4">
                            {row.bestScore !== null ? (
                              <span
                                className={`score-badge ${scoreBadgeClass(row.bestScore)}`}
                              >
                                {Math.round(row.bestScore)}
                              </span>
                            ) : (
                              <span className="text-sm text-gray-400 italic">
                                {row.totalSubmissions > 0
                                  ? "Pending"
                                  : "No score"}
                              </span>
                            )}
                          </td>
                          <td className="px-5 py-4 text-sm text-gray-600">
                            {row.avgScore !== null ? (
                              `${row.avgScore.toFixed(1)}`
                            ) : (
                              <span className="text-gray-400">
                                {row.totalSubmissions > 0
                                  ? "Pending"
                                  : "No score"}
                              </span>
                            )}
                          </td>
                          <td className="px-5 py-4 text-sm text-amber-500">
                            {row.totalSubmissions > 0 ? (
                              expandedId === row.musician.id ? (
                                <ChevronUp
                                  className="h-4 w-4"
                                  aria-hidden="true"
                                />
                              ) : (
                                <ChevronDown
                                  className="h-4 w-4"
                                  aria-hidden="true"
                                />
                              )
                            ) : null}
                          </td>
                        </tr>

                        {/* Expanded submission history */}
                        {expandedId === row.musician.id &&
                          row.submissions.length > 0 && (
                            <tr>
                              <td colSpan={9} className="bg-amber-50 px-5 py-4">
                                <p
                                  className="text-xs font-bold uppercase tracking-widest mb-3"
                                  style={{ color: "var(--color-primary)" }}
                                >
                                  Submission history for{" "}
                                  {row.musician.first_name ??
                                    row.musician.username}
                                </p>
                                <div className="overflow-x-auto">
                                  <table className="w-full min-w-[560px] text-sm divide-y divide-amber-200">
                                    <thead>
                                      <tr className="text-left text-xs font-semibold text-gray-500">
                                        <th className="pb-2 pr-6">
                                          Performance
                                        </th>
                                        <th className="pb-2 pr-6">Task</th>
                                        <th className="pb-2 pr-6">Submitted</th>
                                        <th className="pb-2 pr-6">Status</th>
                                        <th className="pb-2">AI Score</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-amber-100">
                                      {row.submissions.map((s) => (
                                        <tr key={s.evaluationId}>
                                          <td className="py-2 pr-6 font-medium text-gray-700">
                                            {s.performanceTitle}
                                          </td>
                                          <td className="py-2 pr-6 text-gray-500">
                                            {s.taskTitle}
                                          </td>
                                          <td className="py-2 pr-6 text-gray-500">
                                            {formatDate(s.submittedAt)}
                                          </td>
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
                                              <span
                                                className={`score-badge ${scoreBadgeClass(s.score)}`}
                                                style={{
                                                  width: "2.5rem",
                                                  height: "2.5rem",
                                                  fontSize: "0.75rem",
                                                }}
                                              >
                                                {Math.round(s.score)}
                                              </span>
                                            ) : (
                                              <div className="flex items-center gap-3">
                                                <span className="text-gray-400 italic text-xs">
                                                  Pending
                                                </span>
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    void handleRescore(
                                                      s.evaluationId,
                                                      s.assignmentId,
                                                      s.performanceId,
                                                    )
                                                  }
                                                  disabled={
                                                    rescoringEvaluationId ===
                                                    s.evaluationId
                                                  }
                                                  className="inline-flex items-center gap-1 rounded border border-amber-200 px-2 py-1 text-xs font-medium text-amber-700 hover:bg-amber-50 disabled:opacity-50"
                                                >
                                                  {rescoringEvaluationId ===
                                                  s.evaluationId ? (
                                                    <Loader2
                                                      className="h-3.5 w-3.5 animate-spin"
                                                      aria-hidden="true"
                                                    />
                                                  ) : (
                                                    <RefreshCw
                                                      className="h-3.5 w-3.5"
                                                      aria-hidden="true"
                                                    />
                                                  )}
                                                  <span>Re-score</span>
                                                </button>
                                              </div>
                                            )}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
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
