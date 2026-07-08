import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";

interface FormData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: string;
}

interface FieldErrors {
  username?: string;
  email?: string;
  password?: string;
  first_name?: string;
  last_name?: string;
  role?: string;
  general?: string;
}

interface PasswordStrength {
  score: number; // 0-4
  message: string;
  color: string;
}

const Register: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    role: "musician",
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [passwordStrength, setPasswordStrength] =
    useState<PasswordStrength | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const calculatePasswordStrength = (pass: string): PasswordStrength => {
    let score = 0;

    if (pass.length >= 8) score++;
    if (pass.length >= 12) score++;
    if (/[A-Z]/.test(pass)) score++;
    if (/[0-9]/.test(pass)) score++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pass)) score++;

    const messages = [
      { score: 0, message: "Very weak", color: "text-red-600" },
      { score: 1, message: "Weak", color: "text-red-500" },
      { score: 2, message: "Fair", color: "text-yellow-600" },
      { score: 3, message: "Good", color: "text-blue-600" },
      { score: 4, message: "Strong", color: "text-green-600" },
    ];

    const strength = messages[Math.min(score, 4)];
    return { score, message: strength.message, color: strength.color };
  };

  const validateField = (name: string, value: string): string | undefined => {
    switch (name) {
      case "username":
        if (!value.trim()) return "Username is required";
        if (value.length < 3) return "Username must be at least 3 characters";
        if (value.length > 50) return "Username must not exceed 50 characters";
        if (!/^[a-zA-Z0-9_-]+$/.test(value))
          return "Username can only contain letters, numbers, underscores, and hyphens";
        return undefined;

      case "email":
        if (!value.trim()) return "Email is required";
        if (!value.includes("@")) return "Please enter a valid email address";
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))
          return "Please enter a valid email address";
        return undefined;

      case "password":
        if (!value) return "Password is required";
        if (value.length < 8) return "Password must be at least 8 characters";
        if (!/[A-Z]/.test(value))
          return "Password must contain at least one uppercase letter";
        if (!/[0-9]/.test(value))
          return "Password must contain at least one number";
        return undefined;

      case "first_name":
        if (!value.trim()) return "First name is required";
        if (value.length > 100)
          return "First name must not exceed 100 characters";
        return undefined;

      case "last_name":
        if (!value.trim()) return "Last name is required";
        if (value.length > 100)
          return "Last name must not exceed 100 characters";
        return undefined;

      case "role":
        if (!value) return "Please select a role";
        return undefined;

      default:
        return undefined;
    }
  };

  const validateForm = (): boolean => {
    const errors: FieldErrors = {};

    Object.keys(formData).forEach((key) => {
      const error = validateField(key, formData[key as keyof FormData]);
      if (error) {
        errors[key as keyof FieldErrors] = error;
      }
    });

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });

    // Real-time validation
    const error = validateField(name, value);
    setFieldErrors({
      ...fieldErrors,
      [name]: error,
    });

    // Calculate password strength
    if (name === "password") {
      if (value) {
        setPasswordStrength(calculatePasswordStrength(value));
      } else {
        setPasswordStrength(null);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await api.post("/auth/register", formData);
      // Navigate to success page with registration details
      navigate("/registration-success", {
        state: {
          username: formData.username,
          email: formData.email,
        },
      });
    } catch (err: unknown) {
      console.error("Registration failed", err);
      let errorMessage = "Registration failed";

      // Extract error details from API response
      if (err instanceof Error && "response" in err) {
        const response = (err as any).response;

        // Handle 422 Pydantic validation errors (array of field errors)
        if (response?.status === 422 && Array.isArray(response?.data?.detail)) {
          const details = response.data.detail;
          if (details.length > 0) {
            const firstError = details[0];
            const fieldName = Array.isArray(firstError.loc)
              ? firstError.loc[firstError.loc.length - 1]
              : "unknown";
            errorMessage = `${fieldName}: ${firstError.msg}`;
          }
        }
        // Handle 400/422 errors with detail as string
        else if (response?.data?.detail) {
          errorMessage = String(response.data.detail);
        }
        // Handle generic error message
        else if (response?.data?.message) {
          errorMessage = String(response.data.message);
        }
        // Handle errors array
        else if (Array.isArray(response?.data?.errors)) {
          errorMessage = response.data.errors
            .map((e: any) => e.msg || e)
            .join("; ");
        }
      }

      setFieldErrors({ general: errorMessage });
    } finally {
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
          {fieldErrors.general && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-red-800 text-sm">{fieldErrors.general}</div>
            </div>
          )}

          <div className="space-y-4">
            {/* Username Field */}
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-gray-700"
              >
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                className={`appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm mt-1 ${
                  fieldErrors.username
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300"
                }`}
                placeholder="Letters, numbers, underscore, hyphen only"
                value={formData.username}
                onChange={handleChange}
              />
              {fieldErrors.username && (
                <p className="mt-1 text-sm text-red-600">
                  {fieldErrors.username}
                </p>
              )}
              {formData.username && !fieldErrors.username && (
                <p className="mt-1 text-sm text-green-600">✓ Valid</p>
              )}
            </div>

            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                className={`appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm mt-1 ${
                  fieldErrors.email
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300"
                }`}
                placeholder="your@email.com"
                value={formData.email}
                onChange={handleChange}
              />
              {fieldErrors.email && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.email}</p>
              )}
              {formData.email && !fieldErrors.email && (
                <p className="mt-1 text-sm text-green-600">✓ Valid</p>
              )}
            </div>

            {/* First Name Field */}
            <div>
              <label
                htmlFor="first_name"
                className="block text-sm font-medium text-gray-700"
              >
                First Name
              </label>
              <input
                id="first_name"
                name="first_name"
                type="text"
                className={`appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm mt-1 ${
                  fieldErrors.first_name
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300"
                }`}
                placeholder="Your first name"
                value={formData.first_name}
                onChange={handleChange}
              />
              {fieldErrors.first_name && (
                <p className="mt-1 text-sm text-red-600">
                  {fieldErrors.first_name}
                </p>
              )}
            </div>

            {/* Last Name Field */}
            <div>
              <label
                htmlFor="last_name"
                className="block text-sm font-medium text-gray-700"
              >
                Last Name
              </label>
              <input
                id="last_name"
                name="last_name"
                type="text"
                className={`appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm mt-1 ${
                  fieldErrors.last_name
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300"
                }`}
                placeholder="Your last name"
                value={formData.last_name}
                onChange={handleChange}
              />
              {fieldErrors.last_name && (
                <p className="mt-1 text-sm text-red-600">
                  {fieldErrors.last_name}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                className={`appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm mt-1 ${
                  fieldErrors.password
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300"
                }`}
                placeholder="Min 8 chars, uppercase, number"
                value={formData.password}
                onChange={handleChange}
              />
              {fieldErrors.password && (
                <p className="mt-1 text-sm text-red-600">
                  {fieldErrors.password}
                </p>
              )}
              {passwordStrength && !fieldErrors.password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-700">
                      Password Strength:
                    </span>
                    <span
                      className={`text-xs font-bold ${passwordStrength.color}`}
                    >
                      {passwordStrength.message}
                    </span>
                  </div>
                  <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        passwordStrength.score === 0
                          ? "w-1/5 bg-red-600"
                          : passwordStrength.score === 1
                            ? "w-2/5 bg-orange-500"
                            : passwordStrength.score === 2
                              ? "w-3/5 bg-yellow-500"
                              : passwordStrength.score === 3
                                ? "w-4/5 bg-blue-500"
                                : "w-full bg-green-500"
                      }`}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Role Field */}
            <div>
              <label
                htmlFor="role"
                className="block text-sm font-medium text-gray-700"
              >
                Role
              </label>
              <select
                id="role"
                name="role"
                className={`appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm mt-1 ${
                  fieldErrors.role
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300"
                }`}
                value={formData.role}
                onChange={handleChange}
              >
                <option value="">Select a role</option>
                <option value="musician">Musician</option>
                <option value="evaluator">Evaluator</option>
              </select>
              {fieldErrors.role && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.role}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={
                isLoading ||
                Object.keys(fieldErrors).some(
                  (key) => fieldErrors[key as keyof FieldErrors],
                )
              }
              className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? "Creating account..." : "Create account"}
            </button>
          </div>

          <div className="text-center">
            <Link
              to="/login"
              className="text-indigo-600 hover:text-indigo-500 text-sm"
            >
              Already have an account? Sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
