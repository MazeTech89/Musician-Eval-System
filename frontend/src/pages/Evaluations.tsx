import React, { useMemo, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import AppHeader from "../components/AppHeader";
import { useAuth } from "../contexts/AuthContext";
import {
  getApiErrorMessage,
  validateRequired,
  validateScore,
} from "../utils/form";
import {
  ACCEPTED_AUDIO_FILE_TYPES,
  MAX_AUDIO_UPLOAD_SIZE_MB,
  validateAudioFileSize,
} from "../utils/audio";

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
  const isMusician = user?.role === "musician";
  const isAdmin = user?.role === "admin";
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
  const [referenceTrackError, setReferenceTrackError] = useState<string | null>(null);
  const [newAssignmentTitle, setNewAssignmentTitle] = useState("");
  const [newAssignmentDescription, setNewAssignmentDescription] = useState("");
  const [selectedReferenceTrackId, setSelectedReferenceTrackId] = useState<number>(0);
  const [creatingAssignment, setCreatingAssignment] = useState(false);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<number>(0);
  const [assignmentAnalysisLoading, setAssignmentAnalysisLoading] = useState(false);
  const [assignmentAnalysisError, setAssignmentAnalysisError] = useState<string | null>(null);
  const [assignmentAnalysisResult, setAssignmentAnalysisResult] = useState<AnalysisResult | null>(null);
  const [evaluationFormError, setEvaluationFormError] = useState<string | null>(null);
  const [analysisFormError, setAnalysisFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [deletingEvaluationId, setDeletingEvaluationId] = useState<number | null>(null);
  const [deletingReferenceTrackId, setDeletingReferenceTrackId] = useState<number | null>(null);
  const [deletingAssignmentId, setDeletingAssignmentId] = useState<number | null>(null);

  const canCreateEvaluations = user?.role === "evaluator" || user?.role === "admin";
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
          canCreateEvaluations ? api.get("/performances") : Promise.resolve({ data: [] }),
        ]);
        setEvaluations(evalResponse.data);
        if (isAdmin) {
          setPerformances(perfResponse.data);
          const [referenceResponse, assignmentResponse] = await Promise.all([
            api.get("/reference-tracks"),
            api.get("/assignments"),
          ]);
          setReferenceTracks(referenceResponse.data);
          setAssignments(assignmentResponse.data);
        } else {
          if (canCreateEvaluations) {
            setPerformances(perfResponse.data);
          }
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
  }, [user, canCreateEvaluations, isAdmin, isLoading]);

  const handleCreateEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    const nextError = !selectedPerformance
      ? "Select a performance."
      : validateScore(score);
    if (nextError) {
      setEvaluationFormError(nextError);
      return;
    }

    setEvaluationFormError(null);
    setSuccessMessage(null);
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
      setSuccessMessage("Evaluation created successfully.");
    } catch (err: unknown) {
      console.error("Failed to create evaluation:", err);
      setEvaluationFormError(getApiErrorMessage(err, "Failed to create evaluation"));
    } finally {
      setSubmitting(false);
    }
  };

  const handleAnalyzePerformance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPerformance) {
      setAnalysisFormError("Select a performance.");
      return;
    }
    if (!referenceFile) {
      setAnalysisFormError("Choose a reference audio file.");
      return;
    }
    const referenceFileError = validateAudioFileSize(referenceFile, "Reference audio file");
    if (referenceFileError) {
      setAnalysisFormError(referenceFileError);
      return;
    }

    setAnalysisFormError(null);
    setSuccessMessage(null);
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const formData = new FormData();
      formData.append("reference_audio", referenceFile);

      const response = await api.post(
        `/performances/${selectedPerformance}/analyze-audio`,
        formData,
      );
      setAnalysisResult(response.data);
      const evalResponse = await api.get("/evaluations");
      setEvaluations(evalResponse.data);
      setSelectedPerformance(0);
      setReferenceFile(null);
      setScore(0);
      setComments("");
      setSuccessMessage("Similarity analysis completed successfully.");
    } catch (err: unknown) {
      console.error("Failed to analyze performance:", err);
      setAnalysisFormError(getApiErrorMessage(err, "Failed to analyze performance"));
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleCreateReferenceTrack = async (e: React.FormEvent) => {
    e.preventDefault();
    const titleError = validateRequired(newReferenceTrackTitle, "Title");
    if (titleError) {
      setReferenceTrackError(titleError);
      return;
    }
    if (!referenceTrackFile) {
      setReferenceTrackError("Choose a reference audio file.");
      return;
    }
    const referenceTrackFileError = validateAudioFileSize(
      referenceTrackFile,
      "Reference audio file",
    );
    if (referenceTrackFileError) {
      setReferenceTrackError(referenceTrackFileError);
      return;
    }

    setReferenceTrackError(null);
    setSuccessMessage(null);
    setCreatingReferenceTrack(true);
    try {
      const formData = new FormData();
      formData.append("title", newReferenceTrackTitle);
      formData.append("description", newReferenceTrackDescription);
      formData.append("audio_file", referenceTrackFile);

      await api.post("/reference-tracks", formData);
      const response = await api.get("/reference-tracks");
      setReferenceTracks(response.data);
      setNewReferenceTrackTitle("");
      setNewReferenceTrackDescription("");
      setReferenceTrackFile(null);
      setSuccessMessage("Reference track saved successfully.");
    } catch (err: unknown) {
      console.error("Failed to create reference track:", err);
      setReferenceTrackError(
        getApiErrorMessage(err, "Failed to create reference track"),
      );
    } finally {
      setCreatingReferenceTrack(false);
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    const titleError = validateRequired(newAssignmentTitle, "Assignment title");
    if (titleError) {
      setAssignmentError(titleError);
      return;
    }
    if (!selectedReferenceTrackId) {
      setAssignmentError("Select a reference track.");
      return;
    }

    setAssignmentError(null);
    setSuccessMessage(null);
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
      setSuccessMessage("Assignment saved successfully.");
    } catch (err: unknown) {
      console.error("Failed to create assignment:", err);
      setAssignmentError(getApiErrorMessage(err, "Failed to create assignment"));
    } finally {
      setCreatingAssignment(false);
    }
  };

  const handleAnalyzeWithAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPerformance) {
      setAssignmentAnalysisError("Select a performance.");
      return;
    }
    if (!selectedAssignmentId) {
      setAssignmentAnalysisError("Select an assignment.");
      return;
    }

    setAssignmentAnalysisLoading(true);
    setAssignmentAnalysisError(null);
    setSuccessMessage(null);
    try {
      const response = await api.post(
        `/assignments/${selectedAssignmentId}/performances/${selectedPerformance}/analyze`,
      );
      setAssignmentAnalysisResult(response.data);
      const evalResponse = await api.get("/evaluations");
      setEvaluations(evalResponse.data);
      setSelectedPerformance(0);
      setSelectedAssignmentId(0);
      setSuccessMessage("Assignment analysis completed successfully.");
    } catch (err: unknown) {
      console.error("Failed to analyze with assignment:", err);
      setAssignmentAnalysisError(
        getApiErrorMessage(err, "Failed to analyze with assignment"),
      );
    } finally {
      setAssignmentAnalysisLoading(false);
    }
  };

  const handleDeleteEvaluation = async (evaluationId: number) => {
    if (!window.confirm("Delete this evaluation?")) {
      return;
    }

    setDeletingEvaluationId(evaluationId);
    setError(null);
    setSuccessMessage(null);
    try {
      await api.delete(`/evaluations/${evaluationId}`);
      setEvaluations((current) => current.filter((evaluation) => evaluation.id !== evaluationId));
      setSuccessMessage("Evaluation deleted successfully.");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Failed to delete evaluation"));
    } finally {
      setDeletingEvaluationId(null);
    }
  };

  const handleDeleteReferenceTrack = async (referenceTrackId: number) => {
    if (!window.confirm("Delete this reference track?")) {
      return;
    }

    setDeletingReferenceTrackId(referenceTrackId);
    setReferenceTrackError(null);
    setSuccessMessage(null);
    try {
      await api.delete(`/reference-tracks/${referenceTrackId}`);
      setReferenceTracks((current) => current.filter((track) => track.id !== referenceTrackId));
      setSelectedReferenceTrackId((current) =>
        current === referenceTrackId ? 0 : current,
      );
      setSuccessMessage("Reference track deleted successfully.");
    } catch (err: unknown) {
      setReferenceTrackError(getApiErrorMessage(err, "Failed to delete reference track"));
    } finally {
      setDeletingReferenceTrackId(null);
    }
  };

  const handleDeleteAssignment = async (assignmentId: number) => {
    if (!window.confirm("Delete this assignment? Linked performances will be preserved.")) {
      return;
    }

    setDeletingAssignmentId(assignmentId);
    setAssignmentError(null);
    setSuccessMessage(null);
    try {
      await api.delete(`/assignments/${assignmentId}`);
      setAssignments((current) =>
        current.filter((assignment) => assignment.id !== assignmentId),
      );
      setSelectedAssignmentId((current) => (current === assignmentId ? 0 : current));
      setSuccessMessage("Assignment deleted successfully.");
    } catch (err: unknown) {
      setAssignmentError(getApiErrorMessage(err, "Failed to delete assignment"));
    } finally {
      setDeletingAssignmentId(null);
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
  const workflowSteps = isAdmin
    ? [
        "1. Open your profile and confirm security settings and MFA.",
        "2. Review reference tracks and assignments in the admin tools below.",
        "3. Choose a performance to score or analyze.",
        "4. Save the evaluation or run similarity analysis, then check the ranked list.",
      ]
    : [
        "1. Open your profile and confirm security settings and MFA.",
        "2. Choose a performance to score.",
        "3. Save the evaluation, then check the ranked list.",
        "4. Return to the dashboard when you're ready for the next item.",
      ];

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader
        title="Evaluations"
        subtitle="Review submissions, score performances, and manage reference-backed analysis."
      />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {successMessage ? (
          <section className="px-4 sm:px-0 mb-6">
            <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-700">
              {successMessage}
            </div>
          </section>
        ) : null}
        <section className="px-4 sm:px-0 mb-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Your workflow</h2>
            <ol className="space-y-2 text-sm text-gray-700">
              {workflowSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
        </section>

        {canCreateEvaluations && (
          <div className="px-4 sm:px-0 mb-6 flex justify-end">
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              {showCreateForm ? "Cancel" : "New Evaluation"}
            </button>
          </div>
        )}
        {canCreateEvaluations && (
          <div className="px-4 py-6 sm:px-0 mb-6 space-y-6">
            {showCreateForm && (
              <div className="bg-white shadow rounded-md p-6">
                <h2 className="text-lg font-semibold mb-4">Create Evaluation</h2>
                <form onSubmit={handleCreateEvaluation}>
                  <div className="mb-4">
                    <label
                      htmlFor="create-evaluation-performance"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Performance
                    </label>
                    <select
                      id="create-evaluation-performance"
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
                    <label
                      htmlFor="create-evaluation-score"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Score (0-100)
                    </label>
                    <input
                      id="create-evaluation-score"
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={score}
                      onChange={(e) => setScore(Number(e.target.value))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label
                      htmlFor="create-evaluation-comments"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Comments
                    </label>
                    <textarea
                      id="create-evaluation-comments"
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
                  {evaluationFormError && (
                    <p className="mt-4 text-sm text-red-600">{evaluationFormError}</p>
                  )}
                </form>
              </div>
            )}

              {isAdmin ? (
              <div className="bg-white shadow rounded-md p-6">
                <h2 className="text-lg font-semibold mb-4">
                  Auto-score a performance from a reference audio track
                </h2>
                <form onSubmit={handleAnalyzePerformance}>
                  <div className="mb-4">
                    <label
                      htmlFor="analysis-performance"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Performance
                    </label>
                    <select
                      id="analysis-performance"
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
                    <label
                      htmlFor="analysis-reference-file"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Reference audio
                    </label>
                    <input
                      id="analysis-reference-file"
                      type="file"
                      accept={ACCEPTED_AUDIO_FILE_TYPES}
                      onChange={(e) => {
                        const nextFile = e.target.files?.[0] ?? null;
                        setReferenceFile(nextFile);
                        setAnalysisFormError(validateAudioFileSize(nextFile, "Reference audio file"));
                      }}
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      Maximum file size: {MAX_AUDIO_UPLOAD_SIZE_MB} MB.
                    </p>
                  </div>
                  <button
                    type="submit"
                    disabled={analysisLoading}
                    className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {analysisLoading ? "Analyzing..." : "Run similarity analysis"}
                  </button>
                </form>
                {(analysisFormError || analysisError) && (
                  <p className="mt-4 text-sm text-red-600">
                    {analysisFormError || analysisError}
                  </p>
                )}
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
            ) : null}

            {isAdmin ? (
            <div className="bg-white shadow rounded-md p-6">
              <h2 className="text-lg font-semibold mb-4">Manage reusable reference tracks</h2>
              <form onSubmit={handleCreateReferenceTrack}>
                <div className="mb-4">
                  <label
                    htmlFor="reference-track-title"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Title
                  </label>
                  <input
                    id="reference-track-title"
                    type="text"
                    value={newReferenceTrackTitle}
                    onChange={(e) => setNewReferenceTrackTitle(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label
                    htmlFor="reference-track-description"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Description
                  </label>
                  <textarea
                    id="reference-track-description"
                    value={newReferenceTrackDescription}
                    onChange={(e) => setNewReferenceTrackDescription(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    rows={3}
                  />
                </div>
                <div className="mb-4">
                  <label
                    htmlFor="reference-track-audio"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Reference audio file
                  </label>
                  <input
                    id="reference-track-audio"
                    type="file"
                    accept={ACCEPTED_AUDIO_FILE_TYPES}
                    onChange={(e) => {
                      const nextFile = e.target.files?.[0] ?? null;
                      setReferenceTrackFile(nextFile);
                      setReferenceTrackError(
                        validateAudioFileSize(nextFile, "Reference audio file"),
                      );
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Maximum file size: {MAX_AUDIO_UPLOAD_SIZE_MB} MB.
                  </p>
                </div>
                <button
                  type="submit"
                  disabled={creatingReferenceTrack}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creatingReferenceTrack ? "Saving..." : "Save reference track"}
                </button>
                {referenceTrackError && (
                  <p className="mt-4 text-sm text-red-600">{referenceTrackError}</p>
                )}
              </form>
              {referenceTracks.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-gray-700">Saved reference tracks</h3>
                  <ul className="mt-2 space-y-2">
                    {referenceTracks.map((track) => (
                      <li
                        key={track.id}
                        className="flex items-start justify-between gap-4 rounded border border-gray-200 px-3 py-2 text-sm text-gray-600"
                      >
                        <div>
                          <span className="font-medium text-gray-900">{track.title}</span>
                          {track.description ? ` — ${track.description}` : ""}
                        </div>
                        {user?.role === "admin" ? (
                          <button
                            type="button"
                            onClick={() => void handleDeleteReferenceTrack(track.id)}
                            disabled={deletingReferenceTrackId === track.id}
                            className="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                          >
                            {deletingReferenceTrackId === track.id ? "Deleting..." : "Delete"}
                          </button>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            ) : null}

            {isAdmin ? (
              <>
            <div className="bg-white shadow rounded-md p-6">
              <h2 className="text-lg font-semibold mb-4">Create an assignment from a reference track</h2>
              <form onSubmit={handleCreateAssignment}>
                <div className="mb-4">
                  <label
                    htmlFor="assignment-title"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Assignment title
                  </label>
                  <input
                    id="assignment-title"
                    type="text"
                    value={newAssignmentTitle}
                    onChange={(e) => setNewAssignmentTitle(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label
                    htmlFor="assignment-description"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Description
                  </label>
                  <textarea
                    id="assignment-description"
                    value={newAssignmentDescription}
                    onChange={(e) => setNewAssignmentDescription(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    rows={3}
                  />
                </div>
                <div className="mb-4">
                  <label
                    htmlFor="assignment-reference-track"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Reference track
                  </label>
                  <select
                    id="assignment-reference-track"
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
                {assignmentError && <p className="mt-4 text-sm text-red-600">{assignmentError}</p>}
              </form>
              {assignments.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-gray-700">Assignments</h3>
                  <ul className="mt-2 space-y-2">
                    {assignments.map((assignment) => (
                      <li
                        key={assignment.id}
                        className="flex items-start justify-between gap-4 rounded border border-gray-200 px-3 py-2 text-sm text-gray-600"
                      >
                        <div>
                          <span className="font-medium text-gray-900">{assignment.title}</span>
                          {assignment.description ? ` — ${assignment.description}` : ""}
                        </div>
                        {user?.role === "admin" ? (
                          <button
                            type="button"
                            onClick={() => void handleDeleteAssignment(assignment.id)}
                            disabled={deletingAssignmentId === assignment.id}
                            className="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                          >
                            {deletingAssignmentId === assignment.id ? "Deleting..." : "Delete"}
                          </button>
                        ) : null}
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
                  <label
                    htmlFor="assignment-analysis-performance"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Performance
                  </label>
                  <select
                    id="assignment-analysis-performance"
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
                  <label
                    htmlFor="assignment-analysis-assignment"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Assignment
                  </label>
                  <select
                    id="assignment-analysis-assignment"
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
              </>
            ) : null}
          </div>
        )}

        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            {evaluations.length === 0 ? (
              <div className="p-6 text-center text-gray-500 space-y-3">
                <p>
                  {isMusician
                    ? "No evaluations yet. Submit a performance in Assignments to see feedback here."
                    : "No evaluations yet. Create an evaluation above or upload a performance to start building history."}
                </p>
                {isMusician ? (
                  <Link to="/assignments" className="inline-block text-indigo-600 hover:text-indigo-500">
                    Go to Assignments
                  </Link>
                ) : null}
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
                       {canCreateEvaluations ? (
                         <button
                           type="button"
                           onClick={() => void handleDeleteEvaluation(evaluation.id)}
                           disabled={deletingEvaluationId === evaluation.id}
                           className="ml-4 rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                         >
                           {deletingEvaluationId === evaluation.id ? "Deleting..." : "Delete"}
                         </button>
                       ) : null}
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
