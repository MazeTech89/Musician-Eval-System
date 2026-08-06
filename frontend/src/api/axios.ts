import axios, { AxiosHeaders } from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "/api/v1";
// Tokens are also mirrored into localStorage for the Authorization header below (in addition
// to the HttpOnly cookies the backend sets); this is a deliberate tradeoff so the SPA can
// read/attach the access token itself, at the cost of XSS-exposed token storage.
const AUTH_ACCESS_TOKEN_KEY = "auth.access_token";
const AUTH_REFRESH_TOKEN_KEY = "auth.refresh_token";

const getStoredAccessToken = () =>
  window.localStorage.getItem(AUTH_ACCESS_TOKEN_KEY);
const getStoredRefreshToken = () =>
  window.localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);

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
  // Sends the backend's HttpOnly auth cookies alongside every request (belt-and-braces
  // alongside the Authorization header set in the request interceptor below).
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    // Let the browser set its own multipart/form-data Content-Type (with boundary);
    // an explicit application/json header here would break file upload requests.
    if (config.headers instanceof AxiosHeaders) {
      config.headers.delete("Content-Type");
    } else if (config.headers) {
      delete config.headers["Content-Type"];
      delete config.headers["content-type"];
    }
  }

  const accessToken = getStoredAccessToken();
  if (accessToken) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Auth endpoints must never trigger the refresh-and-retry flow below, otherwise a
// plain invalid-credentials 401 on login recurses into /auth/refresh indefinitely.
const AUTH_ENDPOINT_PATHS = ["/auth/login", "/auth/register", "/auth/refresh"];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthEndpoint = AUTH_ENDPOINT_PATHS.some((path) =>
      originalRequest?.url?.includes(path),
    );

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !isAuthEndpoint
    ) {
      // _retry flag prevents an infinite refresh loop if the refreshed token is
      // itself rejected with another 401.
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
        // Replay the original failed request now that a fresh access token is stored.
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh itself failed (expired/invalid refresh token): force a clean re-login.
        clearStoredAuthTokens();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default api;
