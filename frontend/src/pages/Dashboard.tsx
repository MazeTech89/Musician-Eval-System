import React from "react";
import { Link } from "react-router-dom";
import AppHeader from "../components/AppHeader";
import { useAuth } from "../contexts/AuthContext";

type JourneyAction = {
  title: string;
  description: string;
  to: string;
  cta: string;
};

type JourneyPlan = {
  intro: string;
  steps: string[];
  actions: JourneyAction[];
};

const journeyByRole: Record<string, JourneyPlan> = {
  admin: {
    intro: "Admin journey: profile first, then create assignments and review results. Start with the highlighted card below.",
    steps: [
      "1. Open your profile to confirm security settings and MFA.",
      "2. Go to the Admin Panel to manage users, roles, and account access.",
      "3. Use Evaluations to create reference tracks, create assignments, and review submissions.",
      "4. Use Assignments to inspect active assignment activity and scoring history.",
    ],
    actions: [
      {
        title: "Admin Panel",
        description: "Manage users and system access",
        to: "/admin",
        cta: "Open Admin Panel",
      },
      {
        title: "Evaluations",
        description: "Create reference tracks, assignments, and reviews",
        to: "/evaluations",
        cta: "Go to Evaluations",
      },
      {
        title: "Assignments",
        description: "Review active assignments and submissions",
        to: "/assignments",
        cta: "Open Assignments",
      },
      {
        title: "Profile",
        description: "Update password, MFA, and account details",
        to: "/profile",
        cta: "View Profile",
      },
    ],
  },
  evaluator: {
    intro: "Evaluator journey: profile first, then score performances and track your work. Start with the highlighted card below.",
    steps: [
      "1. Open your profile to confirm security settings and MFA.",
      "2. Go to Evaluations to review performances and create new evaluations.",
      "3. Use Assignments to inspect reference-backed workflows and submission history.",
      "4. Return to your dashboard to continue reviewing the next item.",
    ],
    actions: [
      {
        title: "Evaluations",
        description: "Review performances and create evaluations",
        to: "/evaluations",
        cta: "Start Evaluating",
      },
      {
        title: "Assignments",
        description: "Inspect assignment-backed submissions and reference tracks",
        to: "/assignments",
        cta: "Open Assignments",
      },
      {
        title: "Profile",
        description: "Update password, MFA, and account details",
        to: "/profile",
        cta: "View Profile",
      },
    ],
  },
  musician: {
    intro: "Musician journey: profile first, then find your assignment, upload, and review feedback. Start with the highlighted card below.",
    steps: [
      "1. Open your profile to confirm security settings and MFA.",
      "2. Go to Assignments to see what you need to record and submit.",
      "3. Upload your performance from the assignment flow or the direct upload page.",
      "4. Check Evaluations after scoring to review your feedback and history.",
    ],
    actions: [
      {
        title: "Assignments",
        description: "View active assignments and submit performances",
        to: "/assignments",
        cta: "Open Assignments",
      },
      {
        title: "Upload Performance",
        description: "Direct upload shortcut for a performance file",
        to: "/performances/upload",
        cta: "Upload Now",
      },
      {
        title: "Evaluations",
        description: "View feedback and scoring history",
        to: "/evaluations",
        cta: "View Evaluations",
      },
      {
        title: "Profile",
        description: "Update password, MFA, and account details",
        to: "/profile",
        cta: "View Profile",
      },
    ],
  },
};

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const journey = journeyByRole[user?.role || ""] || {
    intro: "Welcome to the Musician Evaluation System.",
    steps: [],
    actions: [],
  };
  const primaryAction = journey.actions[0];
  const secondaryActions = journey.actions.slice(1);

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader title="Musician Evaluation System" subtitle={`Welcome, ${user?.first_name}!`} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h2>
            <p className="text-gray-600">{journey.intro}</p>
          </section>

          {journey.steps.length > 0 ? (
            <section className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">How to use the app</h3>
              <ol className="space-y-3">
                {journey.steps.map((step, index) => (
                  <li key={step} className="flex gap-3">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
                      {index + 1}
                    </span>
                    <span className="pt-1 text-gray-700">{step}</span>
                  </li>
                ))}
              </ol>
            </section>
          ) : null}

          <section>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Next actions</h3>
            {primaryAction ? (
              <div className="bg-white p-6 rounded-lg shadow border border-indigo-200 mb-6">
                <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600 mb-2">
                  Start here
                </p>
                <h4 className="text-lg font-semibold mb-2 text-gray-900">{primaryAction.title}</h4>
                <p className="text-gray-600 mb-4">{primaryAction.description}</p>
                <Link to={primaryAction.to} className="text-indigo-600 hover:text-indigo-500">
                  {primaryAction.cta}
                </Link>
              </div>
            ) : null}
            {secondaryActions.length > 0 ? (
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
                {secondaryActions.map((action) => (
                  <div key={action.title} className="bg-white p-6 rounded-lg shadow">
                    <h4 className="text-lg font-semibold mb-2 text-gray-900">{action.title}</h4>
                    <p className="text-gray-600 mb-4">{action.description}</p>
                    <Link to={action.to} className="text-indigo-600 hover:text-indigo-500">
                      {action.cta}
                    </Link>
                  </div>
                ))}
              </div>
            ) : null}
          </section>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
