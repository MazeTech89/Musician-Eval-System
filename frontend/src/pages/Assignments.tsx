import React, { useEffect, useMemo, useState } from "react";
import { FileAudio2, History, Music2, Type } from "lucide-react";
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
  // Task list, submission form, and scoring feedback states.
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<number | "">(
    "",
  );
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [submissionResult, setSubmissionResult] =
    useState<SubmissionResponse | null>(null);
  const [historyEvaluations, setHistoryEvaluations] = useState<
    EvaluationHistory[]
  >([]);
  const [fieldErrors, setFieldErrors] = useState<{
    assignment?: string;
    audioFile?: string;
  }>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [deletingPerformanceId, setDeletingPerformanceId] = useState<
    number | null
  >(null);

  useEffect(() => {
    // Load active tasks plus evaluation history used for the musician history panel.
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
        setSelectedAssignmentId(
          (current) => current || assignmentResponse.data[0]?.id || "",
        );
      } catch (err: unknown) {
        console.error("Failed to fetch assignments:", err);
        setError(getApiErrorMessage(err, "Failed to load assignments"));
      } finally {
        setLoading(false);
      }
    };

    fetchAssignments();
  }, [user]);

  useEffect(() => {
    // Scoring runs as a background task, so poll the evaluation until it leaves "pending".
    if (!submissionResult || submissionResult.evaluation.status !== "pending") {
      return;
    }

    let cancelled = false;
    let attempts = 0;
    const evaluationId = submissionResult.evaluation.id;
    const maxAttempts = 40; // ~2 minutes at 3s intervals

    const poll = async () => {
      attempts += 1;
      try {
        const response = await api.get<EvaluationHistory>(
          `/evaluations/${evaluationId}`,
        );
        if (cancelled) {
          return;
        }
        if (response.data.status !== "pending") {
          setSubmissionResult((current) =>
            current && current.evaluation.id === evaluationId
              ? { ...current, evaluation: response.data }
              : current,
          );
          const historyResponse = await api.get("/evaluations");
          if (!cancelled) {
            setHistoryEvaluations(historyResponse.data);
          }
          return;
        }
      } catch (err: unknown) {
        console.error("Failed to poll evaluation status:", err);
      }
      if (!cancelled && attempts < maxAttempts) {
        timeoutId = window.setTimeout(poll, 3000);
      }
    };

    let timeoutId = window.setTimeout(poll, 3000);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [submissionResult]);

  const selectedAssignment = useMemo(
    // Resolve the currently selected task object for display/submit defaults.
    () =>
      assignments.find((assignment) => assignment.id === selectedAssignmentId),
    [assignments, selectedAssignmentId],
  );

  const assignmentNameById = useMemo(() => {
    return new Map(
      assignments.map((assignment) => [assignment.id, assignment.title]),
    );
  }, [assignments]);

  const rankedHistory = useMemo(() => {
    // Show newest feedback first for a clearer musician journey.
    return [...historyEvaluations].sort(
      (left, right) =>
        new Date(right.created_at).getTime() -
        new Date(left.created_at).getTime(),
    );
  }, [historyEvaluations]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    // Validate task and audio inputs before posting submission payload.

    if (!selectedAssignmentId) {
      setFieldErrors((current) => ({
        ...current,
        assignment: "Select an assignment first.",
      }));
      setError("Please fix the highlighted fields.");
      return;
    }

    if (!audioFile) {
      setFieldErrors((current) => ({
        ...current,
        audioFile: "Choose an audio file to upload.",
      }));
      setError("Please fix the highlighted fields.");
      return;
    }

    const nextFieldErrors: { assignment?: string; audioFile?: string } = {};
    const assignmentError = validateRequired(
      String(selectedAssignmentId),
      "Assignment",
    );
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
    formData.append(
      "title",
      title || `${selectedAssignment?.title ?? "Assignment"} submission`,
    );
    formData.append("description", description);
    formData.append("audio_file", audioFile);

    try {
      // Assignment submissions are sent to the task-specific endpoint for auto-scoring.
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
    // Removes uploaded audio and associated evaluation record from the musician history.
    if (
      !window.confirm("Delete this uploaded performance and its related score?")
    ) {
      return;
    }

    setDeletingPerformanceId(performanceId);
    setError(null);
    setSuccessMessage(null);

    try {
      await api.delete(`/performances/${performanceId}`);
      setHistoryEvaluations((current) =>
        current.filter(
          (evaluation) => evaluation.performance.id !== performanceId,
        ),
      );
      setSubmissionResult((current) =>
        current?.performance.id === performanceId ? null : current,
      );
      setSuccessMessage("Uploaded performance deleted successfully.");
    } catch (err: unknown) {
      setError(
        getApiErrorMessage(err, "Failed to delete uploaded performance"),
      );
    } finally {
      setDeletingPerformanceId(null);
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
        Please log in.
      </div>
    );
  }

  return (
    <div
      className="min-h-screen staff-bg"
      style={{ backgroundColor: "var(--bg-page)" }}
    >
      <AppHeader
        title="Perform Pro"
        subtitle={isMusician ? "Active Tasks" : "Tasks Overview"}
      />

      <main className="mx-auto max-w-7xl px-3 py-6 sm:px-6 sm:py-8 lg:px-8">
        <div className="space-y-6">
          {/* Active assignments */}
          <section className="rounded-2xl bg-white p-4 shadow-md sm:p-6">
            <div className="mb-4 flex items-center gap-2">
              <Music2 className="h-5 w-5 text-amber-600" aria-hidden="true" />
              <h2
                className="text-xl font-bold"
                style={{ color: "var(--color-primary)" }}
              >
                Active Tasks
              </h2>
            </div>
            {assignments.length === 0 ? (
              <p className="text-gray-500 italic">
                {isMusician
                  ? "No active tasks yet. Check back after an admin publishes one."
                  : "No active tasks yet. Go to Reference Upload to create a task."}
              </p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {assignments.map((assignment) => (
                  <button
                    key={assignment.id}
                    type="button"
                    onClick={() => {
                      setSelectedAssignmentId(assignment.id);
                      setFieldErrors((current) => ({
                        ...current,
                        assignment: undefined,
                      }));
                    }}
                    className={`text-left rounded-xl border-2 p-4 transition music-card ${
                      selectedAssignmentId === assignment.id
                        ? "border-amber-500 bg-amber-50"
                        : "border-gray-200 bg-white hover:border-amber-300"
                    }`}
                  >
                    <div
                      className="font-semibold text-sm"
                      style={{ color: "var(--color-primary)" }}
                    >
                      {assignment.title}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {assignment.description || "No description"}
                    </div>
                    <div className="text-xs text-gray-400 mt-2">
                      Reference: {assignment.reference_track.title}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* Performance submission — musicians only */}
          {isMusician ? (
            <section className="bg-white rounded-2xl shadow-md p-6">
              <div className="mb-4 flex items-center gap-2">
                <FileAudio2
                  className="h-5 w-5 text-amber-600"
                  aria-hidden="true"
                />
                <h2
                  className="text-xl font-bold"
                  style={{ color: "var(--color-primary)" }}
                >
                  Submit a Performance
                </h2>
              </div>
              {selectedAssignment ? (
                <p className="text-sm text-gray-600 mb-4">
                  Submitting against{" "}
                  <span className="font-semibold">
                    {selectedAssignment.title}
                  </span>
                </p>
              ) : (
                <p className="text-sm text-gray-500 mb-4">
                  Select a task above then upload your recording. The AI will
                  score it automatically.
                </p>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label
                    htmlFor="assignment-select"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Task
                  </label>
                  <select
                    id="assignment-select"
                    value={selectedAssignmentId}
                    onChange={(event) => {
                      setSelectedAssignmentId(
                        event.target.value ? Number(event.target.value) : "",
                      );
                      setFieldErrors((current) => ({
                        ...current,
                        assignment: undefined,
                      }));
                    }}
                    className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                  >
                    <option value="">Select a task...</option>
                    {assignments.map((assignment) => (
                      <option key={assignment.id} value={assignment.id}>
                        {assignment.title}
                      </option>
                    ))}
                  </select>
                  {fieldErrors.assignment ? (
                    <p className="mt-1 text-sm text-red-600">
                      {fieldErrors.assignment}
                    </p>
                  ) : null}
                </div>

                <div>
                  <label
                    htmlFor="submission-title"
                    className="mb-1 inline-flex items-center gap-2 text-sm font-medium text-gray-700"
                  >
                    <Type
                      className="h-4 w-4 text-amber-600"
                      aria-hidden="true"
                    />
                    <span>Submission title</span>
                  </label>
                  <input
                    id="submission-title"
                    type="text"
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                    placeholder="My recorded submission"
                  />
                </div>

                <div>
                  <label
                    htmlFor="submission-description"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Description
                  </label>
                  <textarea
                    id="submission-description"
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                    rows={3}
                    placeholder="Notes about this recording"
                  />
                </div>

                <div>
                  <label
                    htmlFor="submission-audio-file"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
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
                    className="block w-full text-sm text-gray-500"
                  />
                  <p className="mt-1 text-xs text-gray-400">
                    Max {MAX_AUDIO_UPLOAD_SIZE_MB} MB
                  </p>
                  {fieldErrors.audioFile ? (
                    <p className="mt-1 text-sm text-red-600">
                      {fieldErrors.audioFile}
                    </p>
                  ) : null}
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
                  style={{ backgroundColor: "var(--color-accent)" }}
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
          ) : null}

          {/* Latest score result */}
          {isMusician && submissionResult ? (
            <section className="bg-white rounded-2xl shadow-md p-6">
              <div className="mb-4 flex items-center gap-2">
                <FileAudio2
                  className="h-5 w-5 text-amber-600"
                  aria-hidden="true"
                />
                <h2
                  className="text-xl font-bold"
                  style={{ color: "var(--color-primary)" }}
                >
                  Latest Score
                </h2>
              </div>
              <p className="text-gray-700 mb-2">
                <span className="font-medium">Performance:</span>{" "}
                {submissionResult.performance.title}
              </p>
              {submissionResult.analysis ? (
                <>
                  <p className="text-gray-700 mb-4">
                    <span className="font-medium">Score:</span>{" "}
                    <span
                      className="text-2xl font-bold"
                      style={{ color: "var(--color-accent)" }}
                    >
                      {submissionResult.analysis.score.toFixed(1)}
                    </span>{" "}
                    / 100
                  </p>
                  <div className="grid gap-2 md:grid-cols-3">
                    {Object.entries(submissionResult.analysis.breakdown).map(
                      ([label, value]) => (
                        <div
                          key={label}
                          className="rounded-xl border border-gray-100 bg-gray-50 p-3"
                        >
                          <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                            {label.replace(/_/g, " ")}
                          </div>
                          <div
                            className="font-bold"
                            style={{ color: "var(--color-primary)" }}
                          >
                            {value.toFixed(2)}
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </>
              ) : submissionResult.evaluation.status === "completed" ? (
                <p className="text-gray-700 mb-2">
                  <span className="font-medium">Score:</span>{" "}
                  <span
                    className="text-2xl font-bold"
                    style={{ color: "var(--color-accent)" }}
                  >
                    {submissionResult.evaluation.score?.toFixed(1) ?? "N/A"}
                  </span>{" "}
                  / 100
                </p>
              ) : submissionResult.evaluation.status === "pending" ? (
                <p className="text-sm text-amber-700">
                  Scoring is running in the background — this can take up to a
                  couple of minutes for longer recordings. This card will update
                  automatically.
                </p>
              ) : (
                <p className="text-sm text-red-600">
                  {submissionResult.evaluation.comments ||
                    "Automatic scoring did not complete."}
                </p>
              )}
            </section>
          ) : null}

          {/* Submission history — musicians only */}
          {isMusician ? (
            <section className="bg-white rounded-2xl shadow-md p-6">
              <div className="mb-4 flex items-center gap-2">
                <History
                  className="h-5 w-5 text-amber-600"
                  aria-hidden="true"
                />
                <h2
                  className="text-xl font-bold"
                  style={{ color: "var(--color-primary)" }}
                >
                  My Submission History
                </h2>
              </div>
              {rankedHistory.length === 0 ? (
                <p className="text-gray-500 italic">
                  No submissions yet. Upload your first performance above.
                </p>
              ) : (
                <div className="space-y-3">
                  {rankedHistory.map((evaluation) => (
                    <div
                      key={evaluation.id}
                      className="rounded-xl border border-gray-100 p-4 flex items-center justify-between gap-4"
                    >
                      <div>
                        <div
                          className="font-semibold text-sm"
                          style={{ color: "var(--color-primary)" }}
                        >
                          {evaluation.performance.title}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">
                          Task:{" "}
                          {evaluation.performance.assignment_id
                            ? assignmentNameById.get(
                                evaluation.performance.assignment_id,
                              ) ||
                              `Task #${evaluation.performance.assignment_id}`
                            : "Direct upload"}
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(evaluation.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div
                            className="text-lg font-bold"
                            style={{ color: "var(--color-accent)" }}
                          >
                            {evaluation.score !== null
                              ? `${evaluation.score.toFixed(1)} / 100`
                              : "Pending"}
                          </div>
                          <div className="text-xs uppercase text-gray-400">
                            {evaluation.status}
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() =>
                            void handleDeletePerformance(
                              evaluation.performance.id,
                            )
                          }
                          disabled={
                            deletingPerformanceId === evaluation.performance.id
                          }
                          className="text-xs text-red-400 hover:text-red-600 disabled:opacity-50"
                        >
                          {deletingPerformanceId === evaluation.performance.id
                            ? "..."
                            : "Delete"}
                        </button>
                      </div>
                      {evaluation.comments ? (
                        <p className="mt-2 text-sm text-gray-600 col-span-full">
                          {evaluation.comments}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </section>
          ) : null}
        </div>
      </main>
    </div>
  );
};

export default Assignments;
