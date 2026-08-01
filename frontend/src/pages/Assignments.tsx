import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import AppHeader from "../components/AppHeader";
import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage, validateRequired } from "../utils/form";
import {
  ACCEPTED_AUDIO_FILE_TYPES,
  MAX_AUDIO_UPLOAD_SIZE_MB,
  validateAudioFileSize,
} from "../utils/audio";

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
  reference_track: ReferenceTrack;
}

interface Performance {
  id: number;
  title: string;
  description: string | null;
  audio_file_url: string | null;
  assignment_id: number | null;
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
  updated_at: string;
}

interface EvaluationHistory extends Evaluation {
  performance: Performance;
}

interface SubmissionResponse {
  performance: Performance;
  evaluation: Evaluation;
  analysis?: {
    performance_id: number;
    score: number;
    reference_filename: string;
    created_evaluation_id: number;
    breakdown: Record<string, number>;
  } | null;
  message?: string | null;
}

const Assignments: React.FC = () => {
  const { user, isLoading } = useAuth();
  const isMusician = user?.role === "musician";
  const isEvaluator = user?.role === "evaluator" || user?.role === "admin";
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<number | "">("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [submissionResult, setSubmissionResult] = useState<SubmissionResponse | null>(null);
  const [historyEvaluations, setHistoryEvaluations] = useState<EvaluationHistory[]>([]);
  const [fieldErrors, setFieldErrors] = useState<{ assignment?: string; audioFile?: string }>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [deletingPerformanceId, setDeletingPerformanceId] = useState<number | null>(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchAssignments = async () => {
      try {
        const [assignmentResponse, evaluationResponse] = await Promise.all([
          api.get("/assignments"),
          api.get("/evaluations"),
        ]);
        setAssignments(assignmentResponse.data);
        setHistoryEvaluations(evaluationResponse.data);
        setSelectedAssignmentId((current) => current || assignmentResponse.data[0]?.id || "");
      } catch (err: unknown) {
        console.error("Failed to fetch assignments:", err);
        setError(getApiErrorMessage(err, "Failed to load assignments"));
      } finally {
        setLoading(false);
      }
    };

    fetchAssignments();
  }, [user]);

  const selectedAssignment = useMemo(
    () => assignments.find((assignment) => assignment.id === selectedAssignmentId),
    [assignments, selectedAssignmentId],
  );

  const assignmentNameById = useMemo(() => {
    return new Map(assignments.map((assignment) => [assignment.id, assignment.title]));
  }, [assignments]);

  const rankedHistory = useMemo(() => {
    return [...historyEvaluations].sort(
      (left, right) =>
        new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
    );
  }, [historyEvaluations]);

  const workflowSteps = isMusician
    ? [
        "1. Open the active assignment you want to submit against.",
        "2. Add a title, description, and audio file.",
        "3. Submit the performance and wait for scoring or pending review.",
        "4. Check your submission history for feedback and results.",
      ]
    : [
        "1. Review the active assignments and reference tracks.",
        "2. Use Evaluations to create or inspect scoring history.",
        "3. Open a submission to review the attached performance.",
        "4. Return here to monitor activity and recent uploads.",
      ];

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!selectedAssignmentId) {
      setFieldErrors((current) => ({ ...current, assignment: "Select an assignment first." }));
      setError("Please fix the highlighted fields.");
      return;
    }

    if (!audioFile) {
      setFieldErrors((current) => ({ ...current, audioFile: "Choose an audio file to upload." }));
      setError("Please fix the highlighted fields.");
      return;
    }

    const nextFieldErrors: { assignment?: string; audioFile?: string } = {};
    const assignmentError = validateRequired(String(selectedAssignmentId), "Assignment");
    if (assignmentError) {
      nextFieldErrors.assignment = assignmentError;
    }
    if (!audioFile) {
      nextFieldErrors.audioFile = "Choose an audio file to upload.";
    } else {
      const audioFileError = validateAudioFileSize(audioFile);
      if (audioFileError) {
        nextFieldErrors.audioFile = audioFileError;
      }
    }
    if (Object.keys(nextFieldErrors).length > 0) {
      setFieldErrors(nextFieldErrors);
      setError("Please fix the highlighted fields.");
      return;
    }

    setFieldErrors({});
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    setSubmissionResult(null);

    const formData = new FormData();
    formData.append("title", title || `${selectedAssignment?.title ?? "Assignment"} submission`);
    formData.append("description", description);
    formData.append("audio_file", audioFile);

    try {
      const response = await api.post<SubmissionResponse>(
        `/assignments/${selectedAssignmentId}/submissions`,
        formData,
      );
      setSubmissionResult(response.data);
      const historyResponse = await api.get("/evaluations");
      setHistoryEvaluations(historyResponse.data);
      setTitle("");
      setDescription("");
      setAudioFile(null);
      setSuccessMessage("Performance submitted successfully.");
    } catch (err: unknown) {
      console.error("Failed to submit assignment performance:", err);
      setError(getApiErrorMessage(err, "Failed to submit performance"));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePerformance = async (performanceId: number) => {
    if (!window.confirm("Delete this uploaded performance and its related score?")) {
      return;
    }

    setDeletingPerformanceId(performanceId);
    setError(null);
    setSuccessMessage(null);

    try {
      await api.delete(`/performances/${performanceId}`);
      setHistoryEvaluations((current) =>
        current.filter((evaluation) => evaluation.performance.id !== performanceId),
      );
      setSubmissionResult((current) =>
        current?.performance.id === performanceId ? null : current,
      );
      setSuccessMessage("Uploaded performance deleted successfully.");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Failed to delete uploaded performance"));
    } finally {
      setDeletingPerformanceId(null);
    }
  };

  if (isLoading || loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  if (!user) {
    return <div className="flex justify-center items-center h-screen">Please log in.</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader title="Assignments" subtitle="View active assignments, submit performances, and review history." />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Your workflow</h2>
            <ol className="space-y-2 text-sm text-gray-700">
              {workflowSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Active assignments</h2>
            {assignments.length === 0 ? (
              <div className="space-y-3">
                <p className="text-gray-600">
                  {isMusician
                    ? "No active assignments yet. Check back after an admin publishes one."
                    : "No active assignments yet. Create a reference track and assignment in Evaluations to get started."}
                </p>
                {isEvaluator ? (
                  <Link to="/evaluations" className="text-indigo-600 hover:text-indigo-500">
                    Go to Evaluations
                  </Link>
                ) : null}
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {assignments.map((assignment) => (
                  <button
                    key={assignment.id}
                    type="button"
                    onClick={() => {
                      setSelectedAssignmentId(assignment.id);
                      setFieldErrors((current) => ({ ...current, assignment: undefined }));
                    }}
                    className={`text-left rounded-lg border p-4 transition ${
                      selectedAssignmentId === assignment.id
                        ? "border-indigo-500 bg-indigo-50"
                        : "border-gray-200 bg-white hover:border-indigo-300"
                    }`}
                  >
                    <div className="font-semibold text-gray-900">{assignment.title}</div>
                    <div className="text-sm text-gray-600 mt-1">
                      {assignment.description || "No description provided"}
                    </div>
                    <div className="text-sm text-gray-500 mt-2">
                      Reference: {assignment.reference_track.title}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Submit a performance</h2>
            {selectedAssignment ? (
              <p className="text-sm text-gray-600 mb-4">
                You are submitting against <span className="font-medium">{selectedAssignment.title}</span>.
              </p>
            ) : (
              <p className="text-sm text-gray-600 mb-4">
                Select an assignment to submit against. Your upload will appear in your history after scoring.
              </p>
            )}

            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="assignment-select" className="block text-sm font-medium text-gray-700">
                  Assignment
                </label>
                <select
                  id="assignment-select"
                  value={selectedAssignmentId}
                  onChange={(event) => {
                    setSelectedAssignmentId(
                      event.target.value ? Number(event.target.value) : "",
                    );
                    setFieldErrors((current) => ({ ...current, assignment: undefined }));
                  }}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                >
                  <option value="">Select an assignment</option>
                  {assignments.map((assignment) => (
                    <option key={assignment.id} value={assignment.id}>
                      {assignment.title}
                    </option>
                  ))}
                </select>
                {fieldErrors.assignment ? (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.assignment}</p>
                ) : null}
              </div>

              <div>
                <label htmlFor="submission-title" className="block text-sm font-medium text-gray-700">
                  Submission title
                </label>
                <input
                  id="submission-title"
                  type="text"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  placeholder="My recorded submission"
                />
              </div>

              <div>
                <label htmlFor="submission-description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="submission-description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  rows={4}
                  placeholder="Add notes about the recording"
                />
              </div>

              <div>
                <label htmlFor="submission-audio-file" className="block text-sm font-medium text-gray-700">
                  Audio file
                </label>
                <input
                  id="submission-audio-file"
                  type="file"
                  accept={ACCEPTED_AUDIO_FILE_TYPES}
                  onChange={(event) => {
                    const nextFile = event.target.files?.[0] ?? null;
                    setAudioFile(nextFile);
                    setFieldErrors((current) => ({
                      ...current,
                      audioFile: validateAudioFileSize(nextFile) ?? undefined,
                    }));
                  }}
                  className="mt-1 block w-full text-sm text-gray-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Maximum file size: {MAX_AUDIO_UPLOAD_SIZE_MB} MB.
                </p>
                {fieldErrors.audioFile ? (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.audioFile}</p>
                ) : null}
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
              >
                {submitting ? "Submitting..." : "Submit and score"}
              </button>
            </form>

            {error ? (
              <p className="mt-4 text-sm text-red-600">{error}</p>
            ) : null}
            {successMessage ? (
              <p className="mt-4 text-sm text-green-600">{successMessage}</p>
            ) : null}
          </section>

          {submissionResult ? (
            <section className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Latest score</h2>
              <p className="text-gray-700">
                <span className="font-medium">Performance:</span> {submissionResult.performance.title}
              </p>
              {submissionResult.analysis ? (
                <>
                  <p className="text-gray-700">
                    <span className="font-medium">Score:</span> {submissionResult.analysis.score.toFixed(1)}
                  </p>
                  <p className="text-gray-700">
                    <span className="font-medium">Reference:</span> {submissionResult.analysis.reference_filename}
                  </p>
                  <div className="mt-4 grid gap-2 md:grid-cols-2">
                    {Object.entries(submissionResult.analysis.breakdown).map(([label, value]) => (
                      <div key={label} className="rounded border border-gray-200 p-3">
                        <div className="text-xs uppercase text-gray-500">{label.replace(/_/g, " ")}</div>
                        <div className="text-gray-900 font-semibold">{value.toFixed(2)}</div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="mt-2 text-sm text-amber-700">
                  {submissionResult.message || "Upload succeeded. Automatic scoring is pending."}
                </p>
              )}
            </section>
          ) : null}

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Your submission history
            </h2>
            {rankedHistory.length === 0 ? (
              <p className="text-gray-600">
                {isMusician
                  ? "No submissions yet. Upload your first performance to see scoring here."
                  : "No submissions yet. Musicians will see their scored performances here after upload."}
              </p>
            ) : (
              <div className="space-y-3">
                {rankedHistory.map((evaluation) => (
                  <div
                    key={evaluation.id}
                    className="rounded-lg border border-gray-200 p-4"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="font-medium text-gray-900">
                          {evaluation.performance.title}
                        </div>
                        <div className="text-sm text-gray-500">
                          Assignment:{" "}
                          {evaluation.performance.assignment_id
                            ? assignmentNameById.get(evaluation.performance.assignment_id) ||
                              `Assignment #${evaluation.performance.assignment_id}`
                            : "Unassigned"}
                        </div>
                        <div className="text-sm text-gray-500">
                          Submitted: {new Date(evaluation.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-semibold text-indigo-600">
                          {evaluation.score !== null
                            ? `${evaluation.score.toFixed(1)} / 100`
                            : "Pending"}
                        </div>
                        <div className="text-xs uppercase tracking-wide text-gray-500">
                          {evaluation.status}
                        </div>
                      </div>
                    </div>
                    {(isMusician || user.role === "admin") ? (
                      <button
                        type="button"
                        onClick={() => void handleDeletePerformance(evaluation.performance.id)}
                        disabled={deletingPerformanceId === evaluation.performance.id}
                        className="mt-3 rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                      >
                        {deletingPerformanceId === evaluation.performance.id ? "Deleting..." : "Delete upload"}
                      </button>
                    ) : null}
                    {evaluation.comments ? (
                      <p className="mt-3 text-sm text-gray-600">{evaluation.comments}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
};

export default Assignments;
