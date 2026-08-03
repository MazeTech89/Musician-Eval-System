import React, { useState } from "react";
import { Music4 } from "lucide-react";
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
    <div
      className="flex min-h-screen items-center justify-center bg-[var(--bg-page)] px-3 py-6 sm:px-6 lg:px-8"
    >
      <div className="w-full max-w-5xl overflow-hidden rounded-3xl bg-white shadow-2xl md:grid md:grid-cols-[1.05fr_0.95fr]">
        <div className="hidden flex-col justify-between p-8 text-white relative md:flex" style={{ background: "var(--hero-gradient)" }}>
          <div className="absolute top-0 right-8 h-16 w-10" style={{ backgroundColor: "var(--color-accent)" }} />
          <div>
            <Music4 className="mb-4 h-12 w-12 text-rose-100" aria-hidden="true" />
            <h1 className="text-4xl font-bold font-display">Perform Pro</h1>
            <p className="mt-3 text-sm text-cyan-100">
              Intelligent musician task management with AI-driven performance evaluation.
            </p>
          </div>
          <p className="text-xs text-cyan-100/90">Secure role-based access for musicians and administrators.</p>
        </div>

        <div className="p-4 sm:p-6 md:p-8">
          {/* Brand header */}
          <div className="mb-6 text-center">
            <div className="mb-3 flex justify-center md:hidden">
              <Music4 className="h-14 w-14" style={{ color: "var(--color-accent)" }} aria-hidden="true" />
            </div>
            <h1 className="text-2xl font-bold font-display sm:text-3xl" style={{ color: "var(--color-primary)" }}>
              Perform Pro
            </h1>
            <p className="mt-2 text-sm text-gray-500">AI-powered performance scoring</p>
          </div>

          <h2 className="mb-6 text-center text-xl font-semibold" style={{ color: "var(--color-primary)" }}>
            Sign in to your account
          </h2>
          <form className="space-y-5" onSubmit={handleSubmit}>
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
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 sm:text-sm"
                style={{ "--tw-ring-color": "var(--color-accent)" } as React.CSSProperties}
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
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 sm:text-sm"
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
                MFA code <span className="text-gray-400">(optional)</span>
              </label>
              <input
                id="login-totp"
                name="totpCode"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 sm:text-sm"
                placeholder="6-digit code"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
              />
            </div>

            {error && (
              <div className="text-red-600 text-sm text-center bg-red-50 rounded-lg px-4 py-2">{error}</div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2.5 px-4 rounded-lg text-sm font-semibold text-white transition disabled:opacity-50"
              style={{ backgroundColor: isLoading ? "#991b1b" : "var(--color-accent)" }}
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </button>

            <div className="flex justify-between text-sm">
              <Link to="/forgot-password" className="hover:underline" style={{ color: "var(--color-accent)" }}>
                Forgot password?
              </Link>
              <Link to="/register" className="hover:underline" style={{ color: "var(--color-accent)" }}>
                Create account
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
