import React from "react";
import { Home, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

interface PageNavProps {
  title: string;
  showBackButton?: boolean;
  backTo?: string;
}

/**
 * PageNav provides consistent navigation with a back button and home button
 * on every page for easy access to dashboard for both admin and musician roles
 */
const PageNav: React.FC<PageNavProps> = ({
  title,
  showBackButton = false,
  backTo = "/",
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          {showBackButton && (
            <button
              type="button"
              onClick={() => navigate(backTo)}
              className="inline-flex items-center gap-2 rounded-md bg-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-300"
              aria-label="Go back"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              <span>Back</span>
            </button>
          )}
          <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
        </div>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-2 rounded-md bg-indigo-100 px-3 py-2 text-sm font-medium text-indigo-700 transition hover:bg-indigo-200"
          aria-label="Go to dashboard"
          title="Return to Dashboard"
        >
          <Home className="h-4 w-4" aria-hidden="true" />
          <span className="hidden sm:inline">Dashboard</span>
        </button>
      </div>
      {user && (
        <p className="mt-2 text-sm text-gray-500 capitalize">
          Viewing as: <span className="font-semibold">{user.role}</span>
        </p>
      )}
    </div>
  );
};

export default PageNav;
