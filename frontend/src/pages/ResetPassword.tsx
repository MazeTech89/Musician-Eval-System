import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "../api/axios";
import {
  getApiErrorMessage,
  validatePassword,
  validateRequired,
} from "../utils/form";

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState(searchParams.get("token") ?? "");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    // Validate all fields client-side before calling the reset-confirm endpoint
    const tokenError = validateRequired(token, "Reset token");
    const passwordError = validatePassword(password);
    const confirmError = validateRequired(confirmPassword, "Confirm password");

    if (tokenError) {
      setError(tokenError);
      return;
    }
    if (passwordError) {
      setError(passwordError);
      return;
    }
    if (confirmError) {
      setError(confirmError);
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError("");
    setMessage("");
    setIsSubmitting(true);

    try {
      await api.post("/auth/password-reset/confirm", {
        token,
        new_password: password,
      });
      setMessage(
        "Your password has been reset successfully. You can now sign in.",
      );
      setPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Unable to reset password."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create a new password
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="password-reset-token"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Reset token
              </label>
              <input
                id="password-reset-token"
                type="text"
                required
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Paste your reset token"
              />
            </div>
            <div>
              <label
                htmlFor="password-reset-new"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                New password
              </label>
              <input
                id="password-reset-new"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="At least 8 characters"
              />
            </div>
            <div>
              <label
                htmlFor="password-reset-confirm"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Confirm new password
              </label>
              <input
                id="password-reset-confirm"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Re-enter your password"
              />
            </div>
          </div>

          {error ? (
            <p className="text-sm text-red-600 text-center">{error}</p>
          ) : null}
          {message ? (
            <p className="text-sm text-green-600 text-center">{message}</p>
          ) : null}

          <button
            type="submit"
            disabled={isSubmitting}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
          >
            {isSubmitting ? "Updating..." : "Set new password"}
          </button>

          <div className="text-center">
            <Link to="/login" className="text-indigo-600 hover:text-indigo-500">
              Back to sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;
