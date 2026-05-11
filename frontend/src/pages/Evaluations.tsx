import React, { useState, useEffect } from "react";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";

interface Evaluation {
  id: string;
  performance_id: string;
  evaluator_id: string;
  score: number | null;
  comments: string | null;
  status: string;
  created_at: string;
  performance: {
    id: string;
    title: string;
    description: string | null;
    musician_id: string;
    submitted_at: string;
    status: string;
  };
}

const Evaluations: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!user) {
      setLoading(false);
      return;
    }

    const fetchEvaluations = async () => {
      try {
        const response = await api.get("/evaluations");
        setEvaluations(response.data);
      } catch (err: unknown) {
        console.error("Failed to fetch evaluations:", err);
        const message =
          err instanceof Error ? err.message : "Failed to load evaluations";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchEvaluations();
  }, [user]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading evaluations...
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
        Loading evaluations...
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
            <div className="flex items-center">
              <a href="/" className="text-indigo-600 hover:text-indigo-500">
                Back to Dashboard
              </a>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {evaluations.map((evaluation) => (
                <li key={evaluation.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 bg-indigo-500 rounded-full flex items-center justify-center">
                            <span className="text-white font-semibold">
                              {evaluation.score ? evaluation.score : "?"}
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
          </div>
        </div>
      </main>
    </div>
  );
};

export default Evaluations;
