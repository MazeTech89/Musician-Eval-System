import axios, { AxiosHeaders } from "axios";

// Base URL can be overridden per environment via VITE_API_URL; defaults to same-origin API path
const baseURL = import.meta.env.VITE_API_URL ?? "/api/v1";
const AUTH_ACCESS_TOKEN_KEY = "auth.access_token";
const AUTH_REFRESH_TOKEN_KEY = "auth.refresh_token";

const getStoredAccessToken = () =>
  window.localStorage.getItem(AUTH_ACCESS_TOKEN_KEY);
const getStoredRefreshToken = () =>
  window.localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);

// Persist tokens returned from login/refresh so subsequent requests can attach them
export const setStoredAuthTokens = (
  accessToken?: string | null,
  refreshToken?: string | null,
) => {
  if (accessToken) {
    window.localStorage.setItem(AUTH_ACCESS_TOKEN_KEY, accessToken);
  } else {
    window.localStorage.removeItem(AUTH_ACCESS_TOKEN_KEY);
  }

  if (refreshToken) {
    window.localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, refreshToken);
  } else {
    window.localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
  }
};

export const clearStoredAuthTokens = () => {
  window.localStorage.removeItem(AUTH_ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
};

const api = axios.create({
  baseURL,
  withCredentials: true, // Send HttpOnly auth cookies alongside bearer tokens
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    // Let the browser set the multipart boundary automatically for file uploads
    if (config.headers instanceof AxiosHeaders) {
      config.headers.delete("Content-Type");
    } else if (config.headers) {
      delete config.headers["Content-Type"];
      delete config.headers["content-type"];
    }
  }

  // Attach the bearer token (in addition to cookies) for API clients that need it
  const accessToken = getStoredAccessToken();
  if (accessToken) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      // Attempt exactly one silent token refresh before giving up and redirecting to login
      originalRequest._retry = true;

      try {
        const refreshToken = getStoredRefreshToken();
        const response = await api.post(
          "/auth/refresh",
          refreshToken ? { refresh_token: refreshToken } : undefined,
        );
        const nextAccessToken = response.data?.access_token;
        const nextRefreshToken = response.data?.refresh_token ?? refreshToken;
        setStoredAuthTokens(nextAccessToken, nextRefreshToken);
        // Retry the original request with the freshly refreshed token
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed too; clear stale tokens and force re-authentication
        clearStoredAuthTokens();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default api;
