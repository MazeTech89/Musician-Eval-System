import axios from "axios";

type ApiErrorResponse = {
  detail?: string | string[] | Array<{ msg?: string }>;
};

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const detail = error.response?.data?.detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => (typeof item === "string" ? item : item.msg))
        .filter((item): item is string => typeof item === "string" && item.trim().length > 0);
      if (messages.length > 0) {
        return messages.join(", ");
      }
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

export function validateEmail(value: string, label = "Email"): string | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return `${label} is required.`;
  }

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(trimmed)) {
    return `Enter a valid ${label.toLowerCase()}.`;
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
