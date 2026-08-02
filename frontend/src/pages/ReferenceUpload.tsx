import React, { useEffect, useState } from "react";
import api from "../api/axios";
import AppHeader from "../components/AppHeader";
import { getApiErrorMessage, validateRequired } from "../utils/form";
import { ACCEPTED_AUDIO_FILE_TYPES, MAX_AUDIO_UPLOAD_SIZE_MB, validateAudioFileSize } from "../utils/audio";

interface ReferenceTrack {
  id: number;
  title: string;
  description: string | null;
  audio_file_url: string;
  created_at: string;
  is_active: boolean;
}

interface Assignment {
  id: number;
  title: string;
  description: string | null;
  reference_track_id: number;
  is_active: boolean;
  reference_track: ReferenceTrack;
}

const ReferenceUpload: React.FC = () => {
  const [referenceTracks, setReferenceTracks] = useState<ReferenceTrack[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Reference track form
  const [rtTitle, setRtTitle] = useState("");
  const [rtDescription, setRtDescription] = useState("");
  const [rtFile, setRtFile] = useState<File | null>(null);
  const [rtError, setRtError] = useState<string | null>(null);
  const [rtSubmitting, setRtSubmitting] = useState(false);
  const [rtFileError, setRtFileError] = useState<string | null>(null);

  // Assignment form
  const [aTitle, setATitle] = useState("");
  const [aDescription, setADescription] = useState("");
  const [aRefTrackId, setARefTrackId] = useState<number>(0);
  const [aError, setAError] = useState<string | null>(null);
  const [aSubmitting, setASubmitting] = useState(false);

  // Delete state
  const [deletingRtId, setDeletingRtId] = useState<number | null>(null);
  const [deletingAId, setDeletingAId] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([api.get("/reference-tracks"), api.get("/assignments")])
      .then(([rtRes, aRes]) => {
        setReferenceTracks(rtRes.data);
        setAssignments(aRes.data);
        if (rtRes.data.length > 0) setARefTrackId(rtRes.data[0].id);
      })
      .catch(() => setError("Failed to load data."))
      .finally(() => setLoading(false));
  }, []);

  const handleUploadReferenceTrack = async (e: React.FormEvent) => {
    e.preventDefault();
    const titleErr = validateRequired(rtTitle, "Title");
    if (titleErr) { setRtError(titleErr); return; }
    if (!rtFile) { setRtError("Choose an audio file."); return; }
    const fileErr = validateAudioFileSize(rtFile, "Reference audio");
    if (fileErr) { setRtError(fileErr); return; }

    setRtError(null);
    setSuccess(null);
    setRtSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("title", rtTitle);
      fd.append("description", rtDescription);
      fd.append("audio_file", rtFile);
      await api.post("/reference-tracks", fd);
      const res = await api.get("/reference-tracks");
      setReferenceTracks(res.data);
      if (aRefTrackId === 0 && res.data.length > 0) setARefTrackId(res.data[0].id);
      setRtTitle("");
      setRtDescription("");
      setRtFile(null);
      setSuccess("Reference track uploaded successfully.");
    } catch (err: unknown) {
      setRtError(getApiErrorMessage(err, "Failed to upload reference track."));
    } finally {
      setRtSubmitting(false);
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    const titleErr = validateRequired(aTitle, "Task title");
    if (titleErr) { setAError(titleErr); return; }
    if (!aRefTrackId) { setAError("Select a reference track."); return; }

    setAError(null);
    setSuccess(null);
    setASubmitting(true);
    try {
      const fd = new FormData();
      fd.append("title", aTitle);
      fd.append("description", aDescription);
      fd.append("reference_track_id", String(aRefTrackId));
      await api.post("/assignments", fd, { headers: { "Content-Type": "multipart/form-data" } });
      const res = await api.get("/assignments");
      setAssignments(res.data);
      setATitle("");
      setADescription("");
      setSuccess("Task created successfully.");
    } catch (err: unknown) {
      setAError(getApiErrorMessage(err, "Failed to create task."));
    } finally {
      setASubmitting(false);
    }
  };

  const handleDeleteReferenceTrack = async (id: number) => {
    if (!window.confirm("Delete this reference track?")) return;
    setDeletingRtId(id);
    try {
      await api.delete(`/reference-tracks/${id}`);
      setReferenceTracks((t) => t.filter((r) => r.id !== id));
      if (aRefTrackId === id) setARefTrackId(0);
      setSuccess("Reference track deleted.");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Failed to delete reference track."));
    } finally {
      setDeletingRtId(null);
    }
  };

  const handleDeleteAssignment = async (id: number) => {
    if (!window.confirm("Delete this task?")) return;
    setDeletingAId(id);
    try {
      await api.delete(`/assignments/${id}`);
      setAssignments((a) => a.filter((x) => x.id !== id));
      setSuccess("Task deleted.");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Failed to delete task."));
    } finally {
      setDeletingAId(null);
    }
  };

  return (
    <div className="min-h-screen staff-bg" style={{ backgroundColor: "var(--bg-page)" }}>
      <AppHeader title="Musician Evaluation System" subtitle="Reference Upload" />

      <main className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Hero */}
        <div
          className="rounded-2xl p-8 text-white relative overflow-hidden"
          style={{ background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%)" }}
        >
          <span className="text-5xl absolute right-8 top-6 opacity-20 pointer-events-none select-none">🎼</span>
          <h2 className="text-3xl font-bold mb-2 font-display">Reference Audio Upload</h2>
          <p className="text-indigo-200 max-w-xl">
            Upload a reference recording for each task. Musicians' submissions will be automatically
            scored by the AI engine against this audio.
          </p>
        </div>

        {/* Global messages */}
        {success && (
          <div className="rounded-xl bg-green-50 border border-green-200 px-5 py-3 text-green-700 text-sm flex items-center gap-2">
            <span>✓</span> {success}
          </div>
        )}
        {error && (
          <div className="rounded-xl bg-red-50 border border-red-200 px-5 py-3 text-red-700 text-sm">{error}</div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="wave-bars">{[1,2,3,4,5,6].map((i) => <span key={i} />)}</div>
            <span className="ml-4 text-gray-500">Loading…</span>
          </div>
        ) : (
          <div className="grid gap-8 lg:grid-cols-2">
            {/* ── Left column: Upload reference track ── */}
            <div className="space-y-6">
              {/* Upload form */}
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h3 className="text-lg font-bold mb-4" style={{ color: "var(--color-primary)" }}>
                  🎵 Upload Reference Track
                </h3>
                <form onSubmit={handleUploadReferenceTrack} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                    <input
                      type="text"
                      value={rtTitle}
                      onChange={(e) => setRtTitle(e.target.value)}
                      placeholder="e.g. Beethoven Symphony No. 5 Reference"
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      value={rtDescription}
                      onChange={(e) => setRtDescription(e.target.value)}
                      rows={2}
                      placeholder="Optional notes about this reference recording"
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Audio file *</label>
                    <input
                      type="file"
                      accept={ACCEPTED_AUDIO_FILE_TYPES}
                      onChange={(e) => {
                        const f = e.target.files?.[0] ?? null;
                        setRtFile(f);
                        setRtFileError(validateAudioFileSize(f) ?? null);
                      }}
                      className="block w-full text-sm text-gray-500"
                    />
                    <p className="mt-1 text-xs text-gray-400">Max {MAX_AUDIO_UPLOAD_SIZE_MB} MB</p>
                    {rtFileError && <p className="mt-1 text-sm text-red-600">{rtFileError}</p>}
                  </div>
                  {rtError && <p className="text-sm text-red-600">{rtError}</p>}
                  <button
                    type="submit"
                    disabled={rtSubmitting}
                    className="w-full rounded-lg py-2.5 text-sm font-semibold text-white disabled:opacity-50"
                    style={{ backgroundColor: "var(--color-accent)" }}
                  >
                    {rtSubmitting ? "Uploading…" : "Upload Reference Track"}
                  </button>
                </form>
              </div>

              {/* Existing reference tracks */}
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h3 className="text-lg font-bold mb-4" style={{ color: "var(--color-primary)" }}>
                  Uploaded Reference Tracks ({referenceTracks.length})
                </h3>
                {referenceTracks.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">No reference tracks uploaded yet.</p>
                ) : (
                  <ul className="space-y-3">
                    {referenceTracks.map((rt) => (
                      <li key={rt.id} className="flex items-start justify-between gap-3 rounded-lg border border-gray-100 p-3">
                        <div>
                          <p className="font-medium text-sm" style={{ color: "var(--color-primary)" }}>{rt.title}</p>
                          {rt.description && <p className="text-xs text-gray-400 mt-0.5">{rt.description}</p>}
                        </div>
                        <button
                          type="button"
                          onClick={() => handleDeleteReferenceTrack(rt.id)}
                          disabled={deletingRtId === rt.id}
                          className="text-xs text-red-500 hover:text-red-700 shrink-0 disabled:opacity-50"
                        >
                          {deletingRtId === rt.id ? "Deleting…" : "Delete"}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* ── Right column: Create task ── */}
            <div className="space-y-6">
              {/* Create task form */}
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h3 className="text-lg font-bold mb-4" style={{ color: "var(--color-primary)" }}>
                  🎯 Create a Task
                </h3>
                <p className="text-sm text-gray-500 mb-4">
                  Link a reference track to create a task. Musicians will submit their recordings against it.
                </p>
                <form onSubmit={handleCreateAssignment} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Task title *</label>
                    <input
                      type="text"
                      value={aTitle}
                      onChange={(e) => setATitle(e.target.value)}
                      placeholder="e.g. Q1 Piano Evaluation"
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      value={aDescription}
                      onChange={(e) => setADescription(e.target.value)}
                      rows={2}
                      placeholder="Optional task details"
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Reference track *</label>
                    {referenceTracks.length === 0 ? (
                      <p className="text-sm text-amber-600 italic">Upload a reference track first.</p>
                    ) : (
                      <select
                        value={aRefTrackId}
                        onChange={(e) => setARefTrackId(Number(e.target.value))}
                        className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                      >
                        <option value={0}>Select reference track…</option>
                        {referenceTracks.map((rt) => (
                          <option key={rt.id} value={rt.id}>{rt.title}</option>
                        ))}
                      </select>
                    )}
                  </div>
                  {aError && <p className="text-sm text-red-600">{aError}</p>}
                  <button
                    type="submit"
                    disabled={aSubmitting || referenceTracks.length === 0}
                    className="w-full rounded-lg py-2.5 text-sm font-semibold text-white disabled:opacity-50"
                    style={{ backgroundColor: "var(--color-accent)" }}
                  >
                    {aSubmitting ? "Creating…" : "Create Task"}
                  </button>
                </form>
              </div>

              {/* Active tasks */}
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h3 className="text-lg font-bold mb-4" style={{ color: "var(--color-primary)" }}>
                  Active Tasks ({assignments.length})
                </h3>
                {assignments.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">No tasks yet.</p>
                ) : (
                  <ul className="space-y-3">
                    {assignments.map((a) => (
                      <li key={a.id} className="flex items-start justify-between gap-3 rounded-lg border border-gray-100 p-3">
                        <div>
                          <p className="font-medium text-sm" style={{ color: "var(--color-primary)" }}>{a.title}</p>
                          <p className="text-xs text-gray-400 mt-0.5">
                            Reference: {a.reference_track?.title ?? "—"}
                          </p>
                          {a.description && <p className="text-xs text-gray-400">{a.description}</p>}
                        </div>
                        <button
                          type="button"
                          onClick={() => handleDeleteAssignment(a.id)}
                          disabled={deletingAId === a.id}
                          className="text-xs text-red-500 hover:text-red-700 shrink-0 disabled:opacity-50"
                        >
                          {deletingAId === a.id ? "Deleting…" : "Delete"}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default ReferenceUpload;
