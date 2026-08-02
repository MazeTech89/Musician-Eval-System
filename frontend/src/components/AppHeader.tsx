import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

type NavItem = {
  to: string;
  label: string;
};

const navItemsByRole: Record<string, NavItem[]> = {
  admin: [
    { to: "/", label: "?? Dashboard" },
    { to: "/profile", label: "?? Profile" },
    { to: "/admin", label: "?? Users" },
    { to: "/evaluations", label: "?? Evaluations" },
    { to: "/assignments", label: "?? Tasks" },
    { to: "/recommendations", label: "?? Rankings" },
  ],
  musician: [
    { to: "/", label: "?? Dashboard" },
    { to: "/profile", label: "?? Profile" },
    { to: "/assignments", label: "?? Tasks" },
    { to: "/performances/upload", label: "?? Upload" },
    { to: "/evaluations", label: "?? My Scores" },
  ],
};

interface AppHeaderProps {
  title: string;
  subtitle?: string;
}

const AppHeader: React.FC<AppHeaderProps> = ({ title, subtitle }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navItems = navItemsByRole[user?.role || ""] || [{ to: "/", label: "?? Dashboard" }];

  return (
    <nav className="bg-stage-900 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-2xl" aria-hidden="true">??</span>
              <div>
                <h1 className="text-lg font-bold text-white leading-tight">{title}</h1>
                {subtitle ? <p className="text-xs text-amber-300">{subtitle}</p> : null}
              </div>
            </div>
            {user?.role ? (
              <span className="rounded-full bg-amber-500 px-2.5 py-0.5 text-xs font-semibold capitalize text-white">
                {user.role}
              </span>
            ) : null}
          </div>

          <div className="flex flex-col gap-3 lg:items-end">
            <div className="flex flex-wrap gap-1.5">
              {navItems.map((item) => {
                const active = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                      active
                        ? "bg-amber-500 text-white"
                        : "text-slate-300 hover:bg-slate-700 hover:text-white"
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
              className="self-start text-xs font-medium text-slate-400 hover:text-amber-300 transition lg:self-end"
            >
              ? Sign out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default AppHeader;