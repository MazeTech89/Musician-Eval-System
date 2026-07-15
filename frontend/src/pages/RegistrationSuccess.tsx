import React from "react";
import { useLocation, Link, useNavigate } from "react-router-dom";

interface LocationState {
  username?: string;
  email?: string;
}

const RegistrationSuccess: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = (location.state as LocationState) || {};

  // If user navigates directly here without registration data, redirect to register
  React.useEffect(() => {
    if (!state.username && !state.email) {
      navigate("/register");
    }
  }, [state, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Success Icon */}
        <div className="flex justify-center">
          <div className="relative">
            <div className="absolute inset-0 animate-pulse bg-green-200 rounded-full"></div>
            <div className="relative flex items-center justify-center w-20 h-20 bg-green-500 rounded-full">
              <svg
                className="w-10 h-10 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-extrabold text-gray-900">
            Registration Complete!
          </h2>

          <p className="text-gray-600 text-sm">
            Your account has been successfully created. You're all set to start
            using the Musician Evaluation System.
          </p>

          {/* Account Details */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6 space-y-2">
            {state.username && (
              <div className="text-left">
                <p className="text-xs font-semibold text-gray-500 uppercase">
                  Username
                </p>
                <p className="text-sm text-gray-900 font-medium">
                  {state.username}
                </p>
              </div>
            )}
            {state.email && (
              <div className="text-left">
                <p className="text-xs font-semibold text-gray-500 uppercase">
                  Email
                </p>
                <p className="text-sm text-gray-900 font-medium break-all">
                  {state.email}
                </p>
              </div>
            )}
          </div>

          {/* Next Steps */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-6">
            <p className="text-xs font-semibold text-amber-800 uppercase mb-2">
              Next Steps
            </p>
            <ul className="text-sm text-amber-900 space-y-1 text-left">
              <li className="flex items-start">
                <span className="text-amber-600 font-bold mr-2">1.</span>
                <span>Click the button below to log in to your account</span>
              </li>
              <li className="flex items-start">
                <span className="text-amber-600 font-bold mr-2">2.</span>
                <span>Complete your profile with additional information</span>
              </li>
              <li className="flex items-start">
                <span className="text-amber-600 font-bold mr-2">3.</span>
                <span>Start submitting performances or evaluations</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3 mt-8">
          <Link
            to="/login"
            className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            Proceed to Login
          </Link>

          <Link
            to="/register"
            className="w-full flex justify-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            Create Another Account
          </Link>
        </div>

        {/* Footer */}
        <div className="text-center pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-indigo-600 hover:text-indigo-500 font-medium"
            >
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegistrationSuccess;
