import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage, validateRequired } from "../utils/form";

const Login: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({});
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const nextFieldErrors: { username?: string; password?: string } = {};
    const usernameError = validateRequired(username, "Username");
    const passwordError = validateRequired(password, "Password");
    if (usernameError) {
      nextFieldErrors.username = usernameError;
    }
    if (passwordError) {
      nextFieldErrors.password = passwordError;
    }
    if (Object.keys(nextFieldErrors).length > 0) {
      setFieldErrors(nextFieldErrors);
      setError("Please fix the highlighted fields.");
      return;
    }

    setFieldErrors({});
    setIsLoading(true);
    setError("");

    try {
      await login(username, password, totpCode || undefined);
      navigate("/");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Invalid credentials"));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label htmlFor="login-username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                id="login-username"
                name="username"
                type="text"
                required
                autoComplete="username"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Username"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setFieldErrors((current) => ({ ...current, username: undefined }));
                }}
              />
              {fieldErrors.username ? (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.username}</p>
              ) : null}
            </div>
            <div>
              <label htmlFor="login-password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="login-password"
                name="password"
                type="password"
                required
                autoComplete="current-password"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setFieldErrors((current) => ({ ...current, password: undefined }));
                }}
              />
              {fieldErrors.password ? (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p>
              ) : null}
            </div>
            <div>
              <label htmlFor="login-totp" className="block text-sm font-medium text-gray-700 mb-1">
                MFA code (optional)
              </label>
              <input
                id="login-totp"
                name="totpCode"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="6-digit code"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">{error}</div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </button>
          </div>

          <div className="text-center">
            <Link to="/forgot-password" className="text-indigo-600 hover:text-indigo-500">
              Forgot your password?
            </Link>
          </div>

          <div className="text-center">
            <Link
              to="/register"
              className="text-indigo-600 hover:text-indigo-500"
            >
              Don't have an account? Register
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
