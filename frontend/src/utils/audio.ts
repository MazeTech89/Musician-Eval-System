export const MAX_AUDIO_UPLOAD_SIZE_MB = 300;
export const MAX_AUDIO_UPLOAD_SIZE_BYTES = MAX_AUDIO_UPLOAD_SIZE_MB * 1024 * 1024;

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

  if (file.size > MAX_AUDIO_UPLOAD_SIZE_BYTES) {
    return `${label} must be ${MAX_AUDIO_UPLOAD_SIZE_MB} MB or smaller.`;
  }

  return null;
}
