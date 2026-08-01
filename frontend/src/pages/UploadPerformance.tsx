import React, { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage, validateRequired } from "../utils/form";

interface UploadResponse {
  id: number;
  title: string;
  description: string | null;
  audio_file_url: string | null;
  status: string;
}

const UploadPerformance: React.FC = () => {
  const { user } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ title?: string; audioFile?: string }>({});

  const canUpload = user?.role === "musician" || user?.role === "admin";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const nextFieldErrors: { title?: string; audioFile?: string } = {};
    const titleError = validateRequired(title, "Title");
    if (titleError) {
      nextFieldErrors.title = titleError;
    }
    if (!audioFile) {
      nextFieldErrors.audioFile = "Please choose an audio file to upload.";
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
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Upload failed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!canUpload) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-3xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
          <div className="bg-white shadow rounded-lg p-6">
            <h1 className="text-xl font-semibold text-gray-900">Upload Performance</h1>
            <p className="mt-3 text-gray-600">
              Only musicians and admins can upload performances.
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
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-semibold text-gray-900">Upload Performance</h1>
            <Link to="/" className="text-indigo-600 hover:text-indigo-500">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
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
                accept="audio/*"
                onChange={(e) => {
                  setAudioFile(e.target.files?.[0] ?? null);
                  setFieldErrors((current) => ({ ...current, audioFile: undefined }));
                }}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
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
      </main>
    </div>
  );
};

export default UploadPerformance;
