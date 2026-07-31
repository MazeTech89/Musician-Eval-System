import React, { useMemo, useState, useEffect } from "react";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";

interface Performance {
  id: number;
  title: string;
  description: string | null;
  musician_id: number;
  assignment_id: number | null;
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

interface AnalysisResult {
  performance_id: number;
  score: number;
  reference_filename: string;
  created_evaluation_id: number;
  breakdown: Record<string, number>;
}

interface ReferenceTrack {
  id: number;
  title: string;
  description: string | null;
  audio_file_url: string;
  created_by_id: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

interface Assignment {
  id: number;
  title: string;
  description: string | null;
  reference_track_id: number;
  created_by_id: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  reference_track?: ReferenceTrack;
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
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [referenceTracks, setReferenceTracks] = useState<ReferenceTrack[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [newReferenceTrackTitle, setNewReferenceTrackTitle] = useState("");
  const [newReferenceTrackDescription, setNewReferenceTrackDescription] = useState("");
  const [referenceTrackFile, setReferenceTrackFile] = useState<File | null>(null);
  const [creatingReferenceTrack, setCreatingReferenceTrack] = useState(false);
  const [newAssignmentTitle, setNewAssignmentTitle] = useState("");
  const [newAssignmentDescription, setNewAssignmentDescription] = useState("");
  const [selectedReferenceTrackId, setSelectedReferenceTrackId] = useState<number>(0);
  const [creatingAssignment, setCreatingAssignment] = useState(false);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<number>(0);
  const [assignmentAnalysisLoading, setAssignmentAnalysisLoading] = useState(false);
  const [assignmentAnalysisError, setAssignmentAnalysisError] = useState<string | null>(null);
  const [assignmentAnalysisResult, setAssignmentAnalysisResult] = useState<AnalysisResult | null>(null);

  const isEvaluator = user?.role === "evaluator" || user?.role === "admin";
  const assignmentById = useMemo(() => {
    return new Map(assignments.map((assignment) => [assignment.id, assignment]));
  }, [assignments]);

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
          const [referenceResponse, assignmentResponse] = await Promise.all([
            api.get("/reference-tracks"),
            api.get("/assignments"),
          ]);
          setReferenceTracks(referenceResponse.data);
          setAssignments(assignmentResponse.data);
        } else {
          setReferenceTracks([]);
          setAssignments([]);
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
  }, [user, isEvaluator, isLoading]);

  const handleCreateEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPerformance || score < 0 || score > 100) return;

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

  const handleAnalyzePerformance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPerformance || !referenceFile) return;

    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const formData = new FormData();
      formData.append("reference_audio", referenceFile);

      const response = await api.post(
        `/performances/${selectedPerformance}/analyze-audio`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        },
      );
      setAnalysisResult(response.data);
      const evalResponse = await api.get("/evaluations");
      setEvaluations(evalResponse.data);
      setSelectedPerformance(0);
      setReferenceFile(null);
      setScore(0);
      setComments("");
    } catch (err: unknown) {
      console.error("Failed to analyze performance:", err);
      const message =
        err instanceof Error ? err.message : "Failed to analyze performance";
      setAnalysisError(message);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleCreateReferenceTrack = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReferenceTrackTitle || !referenceTrackFile) return;

    setCreatingReferenceTrack(true);
    try {
      const formData = new FormData();
      formData.append("title", newReferenceTrackTitle);
      formData.append("description", newReferenceTrackDescription);
      formData.append("audio_file", referenceTrackFile);

      await api.post("/reference-tracks", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const response = await api.get("/reference-tracks");
      setReferenceTracks(response.data);
      setNewReferenceTrackTitle("");
      setNewReferenceTrackDescription("");
      setReferenceTrackFile(null);
    } catch (err: unknown) {
      console.error("Failed to create reference track:", err);
      const message =
        err instanceof Error ? err.message : "Failed to create reference track";
      setError(message);
    } finally {
      setCreatingReferenceTrack(false);
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAssignmentTitle || !selectedReferenceTrackId) return;

    setCreatingAssignment(true);
    try {
      const formData = new FormData();
      formData.append("title", newAssignmentTitle);
      formData.append("description", newAssignmentDescription);
      formData.append("reference_track_id", String(selectedReferenceTrackId));

      await api.post("/assignments", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const response = await api.get("/assignments");
      setAssignments(response.data);
      setNewAssignmentTitle("");
      setNewAssignmentDescription("");
      setSelectedReferenceTrackId(0);
    } catch (err: unknown) {
      console.error("Failed to create assignment:", err);
      const message = err instanceof Error ? err.message : "Failed to create assignment";
      setError(message);
    } finally {
      setCreatingAssignment(false);
    }
  };

  const handleAnalyzeWithAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPerformance || !selectedAssignmentId) return;

    setAssignmentAnalysisLoading(true);
    setAssignmentAnalysisError(null);
    try {
      const response = await api.post(
        `/assignments/${selectedAssignmentId}/performances/${selectedPerformance}/analyze`,
      );
      setAssignmentAnalysisResult(response.data);
      const evalResponse = await api.get("/evaluations");
      setEvaluations(evalResponse.data);
      setSelectedPerformance(0);
      setSelectedAssignmentId(0);
    } catch (err: unknown) {
      console.error("Failed to analyze with assignment:", err);
      const message =
        err instanceof Error ? err.message : "Failed to analyze with assignment";
      setAssignmentAnalysisError(message);
    } finally {
      setAssignmentAnalysisLoading(false);
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

  const rankedEvaluations = [...evaluations].sort((left, right) => {
    const leftScore = left.score ?? -1;
    const rightScore = right.score ?? -1;
    return rightScore - leftScore;
  });

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
        {isEvaluator && (
          <div className="px-4 py-6 sm:px-0 mb-6 space-y-6">
            {showCreateForm && (
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
            )}

            <div className="bg-white shadow rounded-md p-6">
              <h2 className="text-lg font-semibold mb-4">
                Auto-score a performance from a reference audio track
              </h2>
              <form onSubmit={handleAnalyzePerformance}>
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
                    Reference audio
                  </label>
                  <input
                    type="file"
                    accept="audio/wav,audio/x-wav,audio/mpeg,audio/ogg,audio/webm,audio/mp4,audio/flac"
                    onChange={(e) => setReferenceFile(e.target.files?.[0] ?? null)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={analysisLoading}
                  className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 disabled:opacity-50"
                >
                  {analysisLoading ? "Analyzing..." : "Run similarity analysis"}
                </button>
              </form>
              {analysisError && <p className="mt-4 text-sm text-red-600">{analysisError}</p>}
              {analysisResult && (
                <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                  <p className="font-semibold">
                    Similarity score: {analysisResult.score.toFixed(2)} / 100
                  </p>
                  <p className="mt-1">
                    Reference: {analysisResult.reference_filename}
                  </p>
                  <div className="mt-2 grid gap-2 md:grid-cols-2">
                    {Object.entries(analysisResult.breakdown).map(([label, value]) => (
                      <div key={label} className="rounded bg-white px-3 py-2 shadow-sm">
                        <div className="text-xs uppercase tracking-wide text-gray-500">
                          {label.replace(/_/g, " ")}
                        </div>
                        <div className="text-sm font-medium text-gray-900">
                          {(value * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="bg-white shadow rounded-md p-6">
              <h2 className="text-lg font-semibold mb-4">Manage reusable reference tracks</h2>
              <form onSubmit={handleCreateReferenceTrack}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title
                  </label>
                  <input
                    type="text"
                    value={newReferenceTrackTitle}
                    onChange={(e) => setNewReferenceTrackTitle(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newReferenceTrackDescription}
                    onChange={(e) => setNewReferenceTrackDescription(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    rows={3}
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reference audio file
                  </label>
                  <input
                    type="file"
                    accept="audio/wav,audio/x-wav,audio/mpeg,audio/ogg,audio/webm,audio/mp4,audio/flac"
                    onChange={(e) => setReferenceTrackFile(e.target.files?.[0] ?? null)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={creatingReferenceTrack}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creatingReferenceTrack ? "Saving..." : "Save reference track"}
                </button>
              </form>
              {referenceTracks.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-gray-700">Saved reference tracks</h3>
                  <ul className="mt-2 space-y-2">
                    {referenceTracks.map((track) => (
                      <li key={track.id} className="rounded border border-gray-200 px-3 py-2 text-sm text-gray-600">
                        <span className="font-medium text-gray-900">{track.title}</span>
                        {track.description ? ` — ${track.description}` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="bg-white shadow rounded-md p-6">
              <h2 className="text-lg font-semibold mb-4">Create an assignment from a reference track</h2>
              <form onSubmit={handleCreateAssignment}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Assignment title
                  </label>
                  <input
                    type="text"
                    value={newAssignmentTitle}
                    onChange={(e) => setNewAssignmentTitle(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newAssignmentDescription}
                    onChange={(e) => setNewAssignmentDescription(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    rows={3}
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reference track
                  </label>
                  <select
                    value={selectedReferenceTrackId}
                    onChange={(e) => setSelectedReferenceTrackId(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  >
                    <option value={0}>Select a reference track</option>
                    {referenceTracks.map((track) => (
                      <option key={track.id} value={track.id}>
                        {track.title}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={creatingAssignment}
                  className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 disabled:opacity-50"
                >
                  {creatingAssignment ? "Saving..." : "Save assignment"}
                </button>
              </form>
              {assignments.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-gray-700">Assignments</h3>
                  <ul className="mt-2 space-y-2">
                    {assignments.map((assignment) => (
                      <li key={assignment.id} className="rounded border border-gray-200 px-3 py-2 text-sm text-gray-600">
                        <span className="font-medium text-gray-900">{assignment.title}</span>
                        {assignment.description ? ` — ${assignment.description}` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="bg-white shadow rounded-md p-6">
              <h2 className="text-lg font-semibold mb-4">Analyze a performance with an assignment</h2>
              <form onSubmit={handleAnalyzeWithAssignment}>
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
                    Assignment
                  </label>
                  <select
                    value={selectedAssignmentId}
                    onChange={(e) => setSelectedAssignmentId(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  >
                    <option value={0}>Select an assignment</option>
                    {assignments.map((assignment) => (
                      <option key={assignment.id} value={assignment.id}>
                        {assignment.title}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={assignmentAnalysisLoading}
                  className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 disabled:opacity-50"
                >
                  {assignmentAnalysisLoading ? "Analyzing..." : "Analyze with assignment"}
                </button>
              </form>
              {assignmentAnalysisError && (
                <p className="mt-4 text-sm text-red-600">{assignmentAnalysisError}</p>
              )}
              {assignmentAnalysisResult && (
                <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                  <p className="font-semibold">
                    Similarity score: {assignmentAnalysisResult.score.toFixed(2)} / 100
                  </p>
                  <p className="mt-1">
                    Reference: {assignmentAnalysisResult.reference_filename}
                  </p>
                </div>
              )}
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
                {rankedEvaluations.map((evaluation, index) => (
                  <li key={evaluation.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <div className="w-10 h-10 bg-indigo-500 rounded-full flex items-center justify-center">
                              <span className="text-white font-semibold">
                                #{index + 1}
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
                              Assignment:{" "}
                              {evaluation.performance.assignment_id
                                ? assignmentById.get(evaluation.performance.assignment_id)?.title ||
                                  `Assignment #${evaluation.performance.assignment_id}`
                                : "Direct review"}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              Status: {evaluation.status}
                            </div>
                            <div className="text-xs font-medium text-indigo-600 mt-1">
                              Score: {evaluation.score !== null ? `${evaluation.score.toFixed(1)} / 100` : "Pending"}
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
