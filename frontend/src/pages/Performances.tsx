import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";
import ProtectedLayout from "../components/ProtectedLayout";
import PageNav from "../components/PageNav";

interface Performance {
  id: number;
  title: string;
  description: string | null;
  musician_id: number;
  submitted_at: string;
  status: string;
  audio_file_url?: string | null;
  analysis?: any | null;
}

const Performances: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [performances, setPerformances] = useState<Performance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const canCreate =
    user?.role?.toLowerCase() === "musician" ||
    user?.role?.toLowerCase() === "admin";

  useEffect(() => {
    if (isLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchPerformances = async () => {
      try {
        const resp = await api.get("/performances/");
        setPerformances(resp.data || []);
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Failed to load performances";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchPerformances();
  }, [user, isLoading]);

  const handleCreatePerformance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/performances", { title, description });
      const resp = await api.get("/performances/");
      setPerformances(resp.data || []);
      setShowForm(false);
      setTitle("");
      setDescription("");
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to create performance";
      setError(msg);
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
            Please log in to view performances
          </p>
          <Link to="/login" className="text-indigo-600 hover:text-indigo-500">
            Go to Login
          </Link>
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

  return (
    <ProtectedLayout
      title="Performances"
      subtitle="Upload and manage your performance submissions"
    >
      <div className="px-4 py-6 sm:px-0">
        <PageNav title="Your Performances" showBackButton={true} backTo="/" />

        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Performances</h2>
          {canCreate && (
            <button
              onClick={() => setShowForm(!showForm)}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              {showForm ? "Cancel" : "New Performance"}
            </button>
          )}
        </div>

        {error && (
          <div className="mb-6 bg-red-100 border border-red-300 text-red-700 rounded-md p-4">
            {error}
          </div>
        )}

        {showForm && canCreate && (
          <div className="mb-6 bg-white shadow rounded-md p-6">
            <h2 className="text-lg font-semibold mb-4">Submit a Performance</h2>
            <form onSubmit={handleCreatePerformance} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Title
                </label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
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
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  rows={3}
                  placeholder="Optional description"
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
            <h3 className="text-lg font-semibold text-gray-900">
              Your Performances
            </h3>
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
              {performances.map((p) => (
                <li key={p.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-lg font-medium text-gray-900">
                          {p.title}
                        </div>
                        <div className="mt-1 text-sm text-gray-500">
                          {p.description || "No description provided."}
                        </div>
                        <div className="mt-2 text-sm text-gray-500">
                          <span className="font-medium">Status:</span>{" "}
                          {p.status}
                        </div>
                        <div className="mt-1 text-sm text-gray-500">
                          <span className="font-medium">Submitted:</span>{" "}
                          {new Date(p.submitted_at).toLocaleString()}
                        </div>
                        {p.audio_file_url && (
                          <div className="mt-1 text-sm text-gray-500">
                            <a
                              href={p.audio_file_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-indigo-600 hover:text-indigo-500"
                            >
                              View audio
                            </a>
                          </div>
                        )}
                      </div>
                      <div className="text-sm text-gray-500 text-right">
                        <div>Musician ID: {p.musician_id}</div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </ProtectedLayout>
  );
};

export default Performances;
