import React, { useEffect, useMemo, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage, validateRequired } from "../utils/form";

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
  analysis: {
    performance_id: number;
    score: number;
    reference_filename: string;
    created_evaluation_id: number;
    breakdown: Record<string, number>;
  };
}

const Assignments: React.FC = () => {
  const { user, isLoading } = useAuth();
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
    }
    if (Object.keys(nextFieldErrors).length > 0) {
      setFieldErrors(nextFieldErrors);
      setError("Please fix the highlighted fields.");
      return;
    }

    setFieldErrors({});
    setSubmitting(true);
    setError(null);
    setSubmissionResult(null);

    const formData = new FormData();
    formData.append("title", title || `${selectedAssignment?.title ?? "Assignment"} submission`);
    formData.append("description", description);
    formData.append("audio_file", audioFile);

    try {
      const response = await api.post<SubmissionResponse>(
        `/assignments/${selectedAssignmentId}/submissions`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );
      setSubmissionResult(response.data);
      const historyResponse = await api.get("/evaluations");
      setHistoryEvaluations(historyResponse.data);
      setTitle("");
      setDescription("");
      setAudioFile(null);
    } catch (err: unknown) {
      console.error("Failed to submit assignment performance:", err);
      setError(getApiErrorMessage(err, "Failed to submit performance"));
    } finally {
      setSubmitting(false);
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
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Assignments</h1>
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
        <div className="px-4 py-6 sm:px-0 space-y-6">
          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Active assignments</h2>
            {assignments.length === 0 ? (
              <p className="text-gray-600">No active assignments yet.</p>
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
              <p className="text-sm text-gray-600 mb-4">Select an assignment to submit against.</p>
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
                  accept="audio/*"
                  onChange={(event) => {
                    setAudioFile(event.target.files?.[0] ?? null);
                    setFieldErrors((current) => ({ ...current, audioFile: undefined }));
                  }}
                  className="mt-1 block w-full text-sm text-gray-500"
                />
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
          </section>

          {submissionResult ? (
            <section className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Latest score</h2>
              <p className="text-gray-700">
                <span className="font-medium">Score:</span> {submissionResult.analysis.score.toFixed(1)}
              </p>
              <p className="text-gray-700">
                <span className="font-medium">Performance:</span> {submissionResult.performance.title}
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
            </section>
          ) : null}

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Your submission history
            </h2>
            {rankedHistory.length === 0 ? (
              <p className="text-gray-600">No submissions yet.</p>
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
