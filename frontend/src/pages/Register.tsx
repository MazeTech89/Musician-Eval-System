import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import {
  getApiErrorMessage,
  validateEmail,
  validateMinLength,
  validatePassword,
  validateRequired,
} from "../utils/form";

const Register: React.FC = () => {
  // Registration form captures identity, optional musician profile fields, and role.
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    first_name: "",
    last_name: "",
    instrument_type: "",
    skill_level: "",
    availability: "",
    role: "musician",
  });
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  // Generic form field updater used by all controlled inputs/selects.
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Validate all required fields first so API calls only run with clean input.
    const nextFieldErrors: Record<string, string> = {};

    const usernameError = validateMinLength(formData.username, "Username", 3);
    const emailError = validateEmail(formData.email);
    const firstNameError = validateRequired(formData.first_name, "First name");
    const lastNameError = validateRequired(formData.last_name, "Last name");
    const passwordError = validatePassword(formData.password);
    const confirmPasswordError = validateRequired(
      formData.confirmPassword,
      "Confirm password",
    );

    if (usernameError) {
      nextFieldErrors.username = usernameError;
    }
    if (emailError) {
      nextFieldErrors.email = emailError;
    }
    if (firstNameError) {
      nextFieldErrors.first_name = firstNameError;
    }
    if (lastNameError) {
      nextFieldErrors.last_name = lastNameError;
    }
    if (passwordError) {
      nextFieldErrors.password = passwordError;
    }
    if (confirmPasswordError) {
      nextFieldErrors.confirmPassword = confirmPasswordError;
    } else if (formData.password !== formData.confirmPassword) {
      nextFieldErrors.confirmPassword = "Passwords do not match.";
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
      const registrationData = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
        instrument_type: formData.instrument_type,
        skill_level: formData.skill_level,
        availability: formData.availability,
        role: formData.role,
      };
      await api.post("/auth/register", {
        ...registrationData,
        instrument_type: registrationData.instrument_type || undefined,
        skill_level: registrationData.skill_level || undefined,
        availability: registrationData.availability || undefined,
      });
      navigate("/login");
    } catch (err: unknown) {
      console.error("Registration failed", err);
      setError(getApiErrorMessage(err, "Registration failed"));
    } finally {
      // Reset loading state regardless of success/failure to re-enable the submit button.
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="register-username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                id="register-username"
                name="username"
                type="text"
                required
                minLength={3}
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Username"
                value={formData.username}
                onChange={(e) => {
                  handleChange(e);
                  setFieldErrors((current) => ({ ...current, username: "" }));
                }}
              />
              {fieldErrors.username ? <p className="mt-1 text-sm text-red-600">{fieldErrors.username}</p> : null}
            </div>
            <div>
              <label htmlFor="register-email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="register-email"
                name="email"
                type="email"
                required
                autoComplete="email"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => {
                  handleChange(e);
                  setFieldErrors((current) => ({ ...current, email: "" }));
                }}
              />
              {fieldErrors.email ? <p className="mt-1 text-sm text-red-600">{fieldErrors.email}</p> : null}
            </div>
            <div>
              <label htmlFor="register-first-name" className="block text-sm font-medium text-gray-700 mb-1">
                First name
              </label>
              <input
                id="register-first-name"
                name="first_name"
                type="text"
                required
                autoComplete="given-name"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="First Name"
                value={formData.first_name}
                onChange={(e) => {
                  handleChange(e);
                  setFieldErrors((current) => ({ ...current, first_name: "" }));
                }}
              />
              {fieldErrors.first_name ? (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.first_name}</p>
              ) : null}
            </div>
            <div>
              <label htmlFor="register-last-name" className="block text-sm font-medium text-gray-700 mb-1">
                Last name
              </label>
              <input
                id="register-last-name"
                name="last_name"
                type="text"
                required
                autoComplete="family-name"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Last Name"
                value={formData.last_name}
                onChange={(e) => {
                  handleChange(e);
                  setFieldErrors((current) => ({ ...current, last_name: "" }));
                }}
              />
              {fieldErrors.last_name ? <p className="mt-1 text-sm text-red-600">{fieldErrors.last_name}</p> : null}
            </div>
            <div>
              <label
                htmlFor="register-instrument-type"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Instrument type (optional)
              </label>
              <input
                id="register-instrument-type"
                name="instrument_type"
                type="text"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="e.g. Piano, Guitar, Violin"
                value={formData.instrument_type}
                onChange={handleChange}
              />
            </div>
            <div>
              <label
                htmlFor="register-skill-level"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Skill level (optional)
              </label>
              <select
                id="register-skill-level"
                name="skill_level"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                value={formData.skill_level}
                onChange={handleChange}
              >
                <option value="">Select skill level</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="expert">Expert</option>
              </select>
            </div>
            <div>
              <label
                htmlFor="register-availability"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Availability (optional)
              </label>
              <textarea
                id="register-availability"
                name="availability"
                rows={3}
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="e.g. Weekday evenings, weekends"
                value={formData.availability}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="register-role" className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                id="register-role"
                name="role"
                required
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                value={formData.role}
                onChange={handleChange}
              >
                <option value="musician">Musician</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div>
              <label htmlFor="register-password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="register-password"
                name="password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="At least 8 characters"
                value={formData.password}
                onChange={(e) => {
                  handleChange(e);
                  setFieldErrors((current) => ({ ...current, password: "" }));
                }}
              />
              <p className="mt-1 text-xs text-gray-500">Password must be at least 8 characters long.</p>
              {fieldErrors.password ? <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p> : null}
            </div>
            <div>
              <label htmlFor="register-confirm-password" className="block text-sm font-medium text-gray-700 mb-1">
                Confirm password
              </label>
              <input
                id="register-confirm-password"
                name="confirmPassword"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Re-enter your password"
                value={formData.confirmPassword}
                onChange={(e) => {
                  handleChange(e);
                  setFieldErrors((current) => ({ ...current, confirmPassword: "" }));
                }}
              />
              {fieldErrors.confirmPassword ? (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.confirmPassword}</p>
              ) : null}
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
              {isLoading ? "Creating account..." : "Create account"}
            </button>
          </div>

          <div className="text-center">
            <Link to="/login" className="text-indigo-600 hover:text-indigo-500">
              Already have an account? Sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
