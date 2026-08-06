export const MAX_AUDIO_UPLOAD_SIZE_MB = 300;
export const MAX_AUDIO_UPLOAD_SIZE_BYTES =
  MAX_AUDIO_UPLOAD_SIZE_MB * 1024 * 1024;

// Kept in sync with backend/app/core/config.py's max_audio_upload_size_mb and
// upload_security.py's allowed types/extensions — this is a client-side pre-check only;
// the backend independently re-validates (including magic-byte signature checks).
export const ACCEPTED_AUDIO_FILE_TYPES = [
  "audio/wav",
  "audio/x-wav",
  "audio/mpeg",
  "audio/mp3",
  "audio/x-mp3",
  "audio/x-mpeg",
  "audio/ogg",
  "audio/webm",
  "audio/mp4",
  "audio/flac",
  ".wav",
  ".mp3",
  ".ogg",
  ".webm",
  ".mp4",
  ".flac",
].join(",");

export function validateAudioFileSize(
  file: File | null,
  label = "Audio file",
): string | null {
  if (!file) {
    return null;
  }

  if (file.size <= 0) {
    return `${label} is empty. Please select a valid audio file.`;
  }

  if (file.size > MAX_AUDIO_UPLOAD_SIZE_BYTES) {
    return `${label} must be ${MAX_AUDIO_UPLOAD_SIZE_MB} MB or smaller.`;
  }

  return null;
}
