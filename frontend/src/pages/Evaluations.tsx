import React, { useState, useEffect } from "react";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";

interface Performance {
  id: number;
  title: string;
  description: string | null;
  musician_id: number;
  submitted_at: string;
  status: string;
}

interface Evaluation {
  id: number;
  performance_id: number;
  evaluator_id: number;
  score: number | null;
  comments: string | null;
  status: string;
  created_at: string;
  performance: Performance;
}

const Evaluations: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [performances, setPerformances] = useState<Performance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedPerformance, setSelectedPerformance] = useState<number>(0);
  const [score, setScore] = useState<number>(0);
  const [comments, setComments] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  const isEvaluator = user?.role === "evaluator" || user?.role === "admin";

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!user) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        const [evalResponse, perfResponse] = await Promise.all([
          api.get("/evaluations"),
          isEvaluator ? api.get("/performances") : Promise.resolve({ data: [] }),
        ]);
        setEvaluations(evalResponse.data);
        if (isEvaluator) {
          setPerformances(perfResponse.data);
        }
      } catch (err: unknown) {
        console.error("Failed to fetch data:", err);
        const message =
          err instanceof Error ? err.message : "Failed to load data";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, isEvaluator]);

  const handleCreateEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPerformance || !score) return;

    setSubmitting(true);
    try {
      await api.post("/evaluations", {
        performance_id: selectedPerformance,
        score,
        comments,
      });
      const response = await api.get("/evaluations");
      setEvaluations(response.data);
      setShowCreateForm(false);
      setSelectedPerformance(0);
      setScore(0);
      setComments("");
    } catch (err: unknown) {
      console.error("Failed to create evaluation:", err);
      const message =
        err instanceof Error ? err.message : "Failed to create evaluation";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-600">
            Please log in to view evaluations
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-red-600 text-center">
          <p className="text-lg font-semibold">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Evaluations
              </h1>
            </div>
            <div className="flex items-center gap-4">
              {isEvaluator && (
                <button
                  onClick={() => setShowCreateForm(!showCreateForm)}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                >
                  {showCreateForm ? "Cancel" : "New Evaluation"}
                </button>
              )}
              <a href="/" className="text-indigo-600 hover:text-indigo-500">
                Dashboard
              </a>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {showCreateForm && isEvaluator && (
          <div className="px-4 py-6 sm:px-0 mb-6">
            <div className="bg-white shadow rounded-md p-6">
              <h2 className="text-lg font-semibold mb-4">Create Evaluation</h2>
              <form onSubmit={handleCreateEvaluation}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Performance
                  </label>
                  <select
                    value={selectedPerformance}
                    onChange={(e) => setSelectedPerformance(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  >
                    <option value={0}>Select a performance</option>
                    {performances.map((perf) => (
                      <option key={perf.id} value={perf.id}>
                        {perf.title} - {perf.status}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Score (0-100)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={score}
                    onChange={(e) => setScore(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Comments
                  </label>
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    rows={3}
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {submitting ? "Submitting..." : "Submit Evaluation"}
                </button>
              </form>
            </div>
          </div>
        )}

        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            {evaluations.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No evaluations found
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {evaluations.map((evaluation) => (
                  <li key={evaluation.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <div className="w-10 h-10 bg-indigo-500 rounded-full flex items-center justify-center">
                              <span className="text-white font-semibold">
                                {evaluation.score ?? "?"}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {evaluation.performance.title}
                            </div>
                            <div className="text-sm text-gray-500">
                              {evaluation.comments || "No comments"}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              Status: {evaluation.status}
                            </div>
                          </div>
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(evaluation.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Evaluations;
