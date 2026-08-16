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
  // Nav links are derived from the user's role rather than checked per-route, keeping the
  // header in sync with backend RBAC (admin vs musician) without duplicating access rules here.
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
  // Normalize role to lowercase to tolerate backend role casing (e.g. "ADMIN" / "admin")
  const roleKey = user?.role?.toLowerCase() || "";
  const navItems = navItemsByRole[roleKey] || [
    { to: "/", label: "Dashboard", Icon: LayoutDashboard },
  ];

  return (
    <nav
      className="shadow-lg border-b border-white/10"
      style={{ background: "linear-gradient(90deg, #0f3444 0%, #123f52 100%)" }}
    >
      <div className="mx-auto max-w-7xl px-3 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 py-3 sm:py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2">
              <Music4
                className="h-6 w-6 shrink-0 text-amber-300"
                aria-hidden="true"
              />
              <div>
                <h1 className="text-base font-bold leading-tight text-white sm:text-lg">
                  {title}
                </h1>
                {subtitle ? (
                  <p className="text-[11px] text-amber-300 sm:text-xs">
                    {subtitle}
                  </p>
                ) : null}
              </div>
            </div>
            {user?.role ? (
              <span
                className="rounded-full px-2.5 py-0.5 text-[11px] font-semibold capitalize text-white sm:text-xs"
                style={{ backgroundColor: "var(--color-accent)" }}
              >
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
                    className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition sm:px-3 sm:text-sm ${
                      active
                        ? "text-white"
                        : "text-slate-300 hover:bg-slate-700 hover:text-white"
                    }`}
                    style={
                      active
                        ? { backgroundColor: "var(--color-accent)" }
                        : undefined
                    }
                  >
                    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
                      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                      <span>{item.label}</span>
                    </span>
                  </Link>
                );
              })}
            </div>
            <button
              type="button"
              onClick={logout}
              className="self-start text-xs font-medium text-slate-300 transition hover:text-white lg:self-end"
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
