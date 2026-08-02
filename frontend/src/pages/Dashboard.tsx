import React from "react";
import { Link } from "react-router-dom";
import AppHeader from "../components/AppHeader";
import { useAuth } from "../contexts/AuthContext";

type JourneyAction = {
  title: string;
  description: string;
  to: string;
  cta: string;
  icon: string;
};

type JourneyPlan = {
  intro: string;
  actions: JourneyAction[];
};

const journeyByRole: Record<string, JourneyPlan> = {
  admin: {
    intro: "Manage your musicians, create performance tasks, upload reference audio, and view AI-generated rankings.",
    actions: [
      { title: "User Management", description: "Manage user accounts and assign roles", to: "/admin", cta: "Open Admin Panel", icon: "??" },
      { title: "Evaluations", description: "Create reference tracks and review submissions", to: "/evaluations", cta: "Go to Evaluations", icon: "??" },
      { title: "Tasks & Assignments", description: "Create tasks and upload reference audio per task", to: "/assignments", cta: "Open Tasks", icon: "??" },
      { title: "Rankings", description: "See the best musician per task based on AI scores", to: "/recommendations", cta: "View Rankings", icon: "??" },
      { title: "Profile", description: "Update your account details and security settings", to: "/profile", cta: "View Profile", icon: "??" },
    ],
  },
  musician: {
    intro: "Find your assigned tasks, submit your performances, and track your progress and scores.",
    actions: [
      { title: "My Tasks", description: "View active assignments and submit performances", to: "/assignments", cta: "Open Tasks", icon: "??" },
      { title: "Upload Performance", description: "Upload your recording to be scored by the AI", to: "/performances/upload", cta: "Upload Now", icon: "??" },
      { title: "My Scores", description: "View your evaluation history and feedback breakdown", to: "/evaluations", cta: "View Scores", icon: "??" },
      { title: "Profile", description: "Update your instrument, skill level, and availability", to: "/profile", cta: "Edit Profile", icon: "??" },
    ],
  },
};

const notePositions = [
  { top: "8%", left: "3%", char: "?" },
  { top: "20%", left: "90%", char: "?" },
  { top: "60%", left: "95%", char: "?" },
  { top: "80%", left: "2%", char: "??" },
];

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const journey = journeyByRole[user?.role || ""] || {
    intro: "Welcome to the Musician Evaluation System.",
    actions: [],
  };
  const [primary, ...secondary] = journey.actions;

  return (
    <div className="min-h-screen staff-bg" style={{ backgroundColor: "var(--bg-page)" }}>
      {notePositions.map((n) => (
        <span key={n.char} className="note-float" style={{ top: n.top, left: n.left }}>
          {n.char}
        </span>
      ))}

      <AppHeader title="Musician Evaluation System" subtitle={`Welcome back, ${user?.first_name || user?.username}!`} />

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 relative">
        {/* Hero card */}
        <div
          className="rounded-2xl p-8 mb-8 text-white relative overflow-hidden"
          style={{ background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%)" }}
        >
          <span className="text-5xl absolute right-8 top-6 opacity-20 pointer-events-none select-none">??</span>
          <h2 className="text-3xl font-bold mb-2 font-display">Dashboard</h2>
          <p className="text-indigo-200 max-w-xl">{journey.intro}</p>
        </div>

        {/* Primary action */}
        {primary ? (
          <div className="mb-8">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "var(--color-accent)" }}>
              ? Start here
            </p>
            <Link
              to={primary.to}
              className="music-card flex items-start gap-5 bg-white rounded-2xl p-6 shadow-md border-l-4"
              style={{ borderLeftColor: "var(--color-accent)" }}
            >
              <span className="text-4xl">{primary.icon}</span>
              <div>
                <h3 className="text-xl font-bold mb-1" style={{ color: "var(--color-primary)" }}>
                  {primary.title}
                </h3>
                <p className="text-gray-500 mb-3">{primary.description}</p>
                <span
                  className="inline-block rounded-full px-4 py-1.5 text-sm font-semibold text-white"
                  style={{ backgroundColor: "var(--color-accent)" }}
                >
                  {primary.cta} ?
                </span>
              </div>
            </Link>
          </div>
        ) : null}

        {/* Secondary actions */}
        {secondary.length > 0 ? (
          <>
            <p className="text-xs font-bold uppercase tracking-widest mb-3 text-gray-400">More actions</p>
            <div className="grid gap-5 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
              {secondary.map((action) => (
                <Link
                  key={action.to}
                  to={action.to}
                  className="music-card flex items-start gap-4 bg-white rounded-2xl p-5 shadow-sm hover:shadow-md"
                >
                  <span className="text-3xl mt-0.5">{action.icon}</span>
                  <div>
                    <h4 className="font-semibold mb-1" style={{ color: "var(--color-primary)" }}>
                      {action.title}
                    </h4>
                    <p className="text-sm text-gray-500 mb-2">{action.description}</p>
                    <span className="text-sm font-medium" style={{ color: "var(--color-accent)" }}>
                      {action.cta} ?
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
};

export default Dashboard;