import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";

interface Performance {
  id: number;
  title: string;
  description: string | null;
  musician_id: number;
  audio_file_url: string | null;
  submitted_at: string;
  status: string;
}

const Performances: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [performances, setPerformances] = useState<Performance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const canCreate = user?.role === "musician" || user?.role === "admin";

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!user) {
      setLoading(false);
      return;
    }

    const fetchPerformances = async () => {
      try {
        const response = await api.get("/performances");
        setPerformances(response.data);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to load performances";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchPerformances();
  }, [user, isLoading]);

  const handleCreatePerformance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !audioUrl) return;

    setSubmitting(true);
    try {
      await api.post("/performances", {
        title,
        description,
        audio_file_url: audioUrl,
      });
      const response = await api.get("/performances");
      setPerformances(response.data);
      setTitle("");
      setDescription("");
      setAudioUrl("");
      setShowForm(false);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to create performance";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading || loading) {
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
            Please log in to view performances
          </p>
          <Link to="/login" className="text-indigo-600 hover:text-indigo-500">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Performances
              </h1>
            </div>
            <div className="flex items-center gap-4">
              {canCreate && (
                <button
                  onClick={() => setShowForm(!showForm)}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                >
                  {showForm ? "Cancel" : "New Performance"}
                </button>
              )}
              <Link to="/" className="text-indigo-600 hover:text-indigo-500">
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {error && (
            <div className="mb-6 bg-red-100 border border-red-300 text-red-700 rounded-md p-4">
              {error}
            </div>
          )}

          {showForm && canCreate && (
            <div className="mb-6 bg-white shadow rounded-md p-6">
              <h2 className="text-lg font-semibold mb-4">
                Submit a Performance
              </h2>
              <form onSubmit={handleCreatePerformance} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Title
                  </label>
                  <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Performance title"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    rows={3}
                    placeholder="Optional description"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Audio URL
                  </label>
                  <input
                    value={audioUrl}
                    onChange={(e) => setAudioUrl(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="https://example.com/audio.mp3"
                    required
                  />
                </div>
                <div>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {submitting ? "Submitting..." : "Create Performance"}
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-5 sm:px-6">
              <h2 className="text-lg font-semibold text-gray-900">
                Your Performances
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                {canCreate
                  ? "Create and review your performance submissions."
                  : "View available performances."}
              </p>
            </div>
            {performances.length === 0 ? (
              <div className="px-4 py-6 text-center text-gray-500">
                No performances found.
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {performances.map((performance) => (
                  <li key={performance.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-lg font-medium text-gray-900">
                            {performance.title}
                          </div>
                          <div className="mt-1 text-sm text-gray-500">
                            {performance.description ||
                              "No description provided."}
                          </div>
                          <div className="mt-2 text-sm text-gray-500">
                            <span className="font-medium">Status:</span>{" "}
                            {performance.status}
                          </div>
                          <div className="mt-1 text-sm text-gray-500">
                            <span className="font-medium">Submitted:</span>{" "}
                            {new Date(
                              performance.submitted_at,
                            ).toLocaleString()}
                          </div>
                          <div className="mt-1 text-sm text-gray-500">
                            <a
                              href={performance.audio_file_url ?? "#"}
                              target="_blank"
                              rel="noreferrer"
                              className="text-indigo-600 hover:text-indigo-500"
                            >
                              View audio
                            </a>
                          </div>
                        </div>
                        <div className="text-sm text-gray-500 text-right">
                          <div>Musician ID: {performance.musician_id}</div>
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

export default Performances;
