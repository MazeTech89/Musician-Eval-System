import axios from "axios";

type ApiErrorResponse = {
  detail?: string | string[];
};

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const detail = error.response?.data?.detail;
    if (Array.isArray(detail)) {
      return detail.join(", ");
    }
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallback;
}

export function validateRequired(value: string, label: string): string | null {
  if (!value.trim()) {
    return `${label} is required.`;
  }
  return null;
}

export function validateMinLength(
  value: string,
  label: string,
  minLength: number,
): string | null {
  if (value.trim().length < minLength) {
    return `${label} must be at least ${minLength} characters.`;
  }
  return null;
}

export function validatePassword(password: string): string | null {
  return validateMinLength(password, "Password", 8);
}

export function validateScore(score: number): string | null {
  if (!Number.isFinite(score) || score < 0 || score > 100) {
    return "Score must be between 0 and 100.";
  }
  return null;
}
