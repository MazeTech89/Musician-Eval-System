import React from "react";
import {
  BarChart3,
  LayoutDashboard,
  LogOut,
  Music4,
  ShieldCheck,
  Trophy,
  Upload,
  UserCircle2,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

type NavItem = {
  to: string;
  label: string;
  Icon: LucideIcon;
};

const navItemsByRole: Record<string, NavItem[]> = {
  admin: [
    { to: "/", label: "Dashboard", Icon: LayoutDashboard },
    { to: "/admin", label: "Users", Icon: Users },
    { to: "/reference-upload", label: "Reference Upload", Icon: Upload },
    { to: "/musician-results", label: "Results", Icon: BarChart3 },
    { to: "/recommendations", label: "Rankings", Icon: Trophy },
  ],
  musician: [
    { to: "/", label: "Dashboard", Icon: LayoutDashboard },
    { to: "/profile", label: "Profile", Icon: UserCircle2 },
    { to: "/assignments", label: "Tasks", Icon: ShieldCheck },
    { to: "/performances/upload", label: "Upload", Icon: Upload },
    { to: "/evaluations", label: "My Scores", Icon: BarChart3 },
  ],
};

interface AppHeaderProps {
  title: string;
  subtitle?: string;
}

const AppHeader: React.FC<AppHeaderProps> = ({ title, subtitle }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navItems = navItemsByRole[user?.role || ""] || [
    { to: "/", label: "Dashboard", Icon: LayoutDashboard },
  ];

  return (
    <nav className="bg-stage-900 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Music4 className="h-6 w-6 text-amber-300" aria-hidden="true" />
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
                const Icon = item.Icon;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                      active
                        ? 'bg-amber-500 text-white'
                        : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                    }`}
                  >
                    <span className="inline-flex items-center gap-1.5">
                      <Icon className="h-4 w-4" aria-hidden="true" />
                      <span>{item.label}</span>
                    </span>
                  </Link>
                );
              })}
            </div>
            <button
              type="button"
              onClick={logout}
              className="self-start text-xs font-medium text-slate-400 hover:text-amber-300 transition lg:self-end"
            >
              <span className="inline-flex items-center gap-1">
                <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Sign out</span>
              </span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default AppHeader;
