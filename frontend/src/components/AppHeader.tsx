import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

type NavItem = {
  to: string;
  label: string;
};

const navItemsByRole: Record<string, NavItem[]> = {
  admin: [
    { to: "/", label: "Dashboard" },
    { to: "/profile", label: "Profile" },
    { to: "/admin", label: "Admin Panel" },
    { to: "/evaluations", label: "Evaluations" },
    { to: "/assignments", label: "Assignments" },
    { to: "/performances/upload", label: "Upload" },
  ],
  evaluator: [
    { to: "/", label: "Dashboard" },
    { to: "/profile", label: "Profile" },
    { to: "/evaluations", label: "Evaluations" },
    { to: "/assignments", label: "Assignments" },
  ],
  musician: [
    { to: "/", label: "Dashboard" },
    { to: "/profile", label: "Profile" },
    { to: "/assignments", label: "Assignments" },
    { to: "/performances/upload", label: "Upload" },
    { to: "/evaluations", label: "Evaluations" },
  ],
};

interface AppHeaderProps {
  title: string;
  subtitle?: string;
}

const AppHeader: React.FC<AppHeaderProps> = ({ title, subtitle }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navItems = navItemsByRole[user?.role || ""] || [{ to: "/", label: "Dashboard" }];

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
              {user?.role ? (
                <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium capitalize text-indigo-700">
                  {user.role}
                </span>
              ) : null}
            </div>
            {subtitle ? <p className="mt-1 text-sm text-gray-600">{subtitle}</p> : null}
          </div>

          <div className="flex flex-col gap-3 lg:items-end">
            <div className="flex flex-wrap gap-2">
              {navItems.map((item) => {
                const active = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`rounded-md px-3 py-2 text-sm font-medium transition ${
                      active
                        ? "bg-indigo-600 text-white"
                        : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
            <button
              type="button"
              onClick={logout}
              className="self-start text-sm font-medium text-gray-700 hover:text-gray-900 lg:self-end"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default AppHeader;
