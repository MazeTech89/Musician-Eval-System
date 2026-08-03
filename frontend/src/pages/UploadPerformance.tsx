import React, { useEffect, useState } from "react";
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

interface UploadResponse {
  id: number;
  title: string;
  description: string | null;
  audio_file_url: string | null;
  status: string;
}

interface PerformanceSummary extends UploadResponse {
  musician_id: number;
  assignment_id: number | null;
  submitted_at: string;
}

const UploadPerformance: React.FC = () => {
  const { user } = useAuth();
  // Upload form state and feedback messages.
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ title?: string; audioFile?: string }>({});
  const [performances, setPerformances] = useState<PerformanceSummary[]>([]);
  const [loadingPerformances, setLoadingPerformances] = useState(true);
  const [deletingPerformanceId, setDeletingPerformanceId] = useState<number | null>(null);

  const canUpload = user?.role === "musician";
  const workflowSteps = [
    "1. Open Assignments and confirm the assignment you want to submit against.",
    "2. Fill in a clear title and optional notes.",
    "3. Choose your audio file and keep it within the size limit.",
    "4. Submit, then review the result in Evaluations.",
  ];

  useEffect(() => {
    // Only musicians can load/manage their own uploads from this screen.
    if (!canUpload) {
      setLoadingPerformances(false);
      return;
    }

    const loadPerformances = async () => {
      try {
        const response = await api.get<PerformanceSummary[]>("/performances");
        setPerformances(response.data);
      } catch (err: unknown) {
        setError(getApiErrorMessage(err, "Failed to load uploaded performances"));
      } finally {
        setLoadingPerformances(false);
      }
    };

    loadPerformances();
  }, [canUpload]);

  const refreshPerformances = async () => {
    // Re-query after create/delete so history always reflects persisted backend state.
    const response = await api.get<PerformanceSummary[]>("/performances");
    setPerformances(response.data);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Perform client-side validation for title and file constraints before upload.
    const nextFieldErrors: { title?: string; audioFile?: string } = {};
    const titleError = validateRequired(title, "Title");
    if (titleError) {
      nextFieldErrors.title = titleError;
    }
    if (!audioFile) {
      nextFieldErrors.audioFile = "Please choose an audio file to upload.";
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
    setError("");
    setSuccess("");

    setIsSubmitting(true);

    try {
      // Use multipart/form-data for binary audio payload + metadata.
      const formData = new FormData();
      formData.append("title", title);
      formData.append("description", description);
      formData.append("audio_file", audioFile!);

      const response = await api.post<UploadResponse>("/performances/upload-audio", formData);

      const upload = response.data;
      setSuccess(
        `Uploaded successfully: ${upload.title}. Status: ${upload.status}.`,
      );
      setTitle("");
      setDescription("");
      setAudioFile(null);
      await refreshPerformances();
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Upload failed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeletePerformance = async (performanceId: number) => {
    // Deleting a performance also removes the related score/evaluation server-side.
    if (!window.confirm("Delete this uploaded performance?")) {
      return;
    }

    setDeletingPerformanceId(performanceId);
    setError("");
    setSuccess("");

    try {
      await api.delete(`/performances/${performanceId}`);
      setPerformances((current) =>
        current.filter((performance) => performance.id !== performanceId),
      );
      setSuccess("Uploaded performance deleted successfully.");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Failed to delete uploaded performance"));
    } finally {
      setDeletingPerformanceId(null);
    }
  };

  if (!canUpload) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-3xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
          <div className="bg-white shadow rounded-lg p-6">
            <h1 className="text-xl font-semibold text-gray-900">Upload Performance</h1>
            <p className="mt-3 text-gray-600">
              Only musicians and admins can upload performances. If you are a musician,
              choose your assignment first so the submission is tied to the right workflow.
            </p>
            <Link to="/" className="mt-4 inline-block text-indigo-600 hover:text-indigo-500">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader
        title="Upload Performance"
        subtitle="Send in a performance file for your active assignment. Check Assignments first if you need to pick one."
      />

      <main className="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="space-y-6">
          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Your workflow</h2>
            <ol className="space-y-2 text-sm text-gray-700">
              {workflowSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>

          <div className="bg-white shadow rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                Title
              </label>
              <input
                id="title"
                type="text"
                required
                minLength={3}
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  setFieldErrors((current) => ({ ...current, title: undefined }));
                }}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="Performance title"
              />
              {fieldErrors.title ? <p className="mt-1 text-sm text-red-600">{fieldErrors.title}</p> : null}
            </div>

            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Description (optional)
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                rows={4}
                placeholder="Add notes about this performance"
              />
            </div>

            <div>
              <label htmlFor="audio-file" className="block text-sm font-medium text-gray-700 mb-1">
                Audio file
              </label>
              <input
                id="audio-file"
                type="file"
                required
                accept={ACCEPTED_AUDIO_FILE_TYPES}
                onChange={(e) => {
                  const nextFile = e.target.files?.[0] ?? null;
                  setAudioFile(nextFile);
                  setFieldErrors((current) => ({
                    ...current,
                    audioFile: validateAudioFileSize(nextFile) ?? undefined,
                  }));
                }}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
              <p className="mt-1 text-sm text-gray-500">
                Maximum file size: {MAX_AUDIO_UPLOAD_SIZE_MB} MB.
              </p>
              {fieldErrors.audioFile ? (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.audioFile}</p>
              ) : null}
            </div>

            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            {success ? <p className="text-sm text-green-600">{success}</p> : null}

            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? "Uploading..." : "Upload performance"}
            </button>
          </form>
          </div>

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {user?.role === "admin" ? "Uploaded performances" : "Your uploaded performances"}
            </h2>
            {loadingPerformances ? (
              <p className="text-sm text-gray-600">Loading uploaded performances...</p>
            ) : performances.length === 0 ? (
              <p className="text-sm text-gray-600">
                No uploaded performances yet. Submit one above to manage it here.
              </p>
            ) : (
              <div className="space-y-3">
                {performances.map((performance) => (
                  <div
                    key={performance.id}
                    className="flex items-start justify-between gap-4 rounded-lg border border-gray-200 p-4"
                  >
                    <div>
                      <div className="font-medium text-gray-900">{performance.title}</div>
                      <div className="text-sm text-gray-500">
                        Submitted: {new Date(performance.submitted_at).toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-500">
                        Assignment:{" "}
                        {performance.assignment_id ? `Assignment #${performance.assignment_id}` : "Direct upload"}
                      </div>
                      <div className="text-sm text-gray-500">Status: {performance.status}</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => void handleDeletePerformance(performance.id)}
                      disabled={deletingPerformanceId === performance.id}
                      className="rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                    >
                      {deletingPerformanceId === performance.id ? "Deleting..." : "Delete"}
                    </button>
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

export default UploadPerformance;
