import React from 'react';
import { Link } from 'react-router-dom';
import AppHeader from '../components/AppHeader';
import { useAuth } from '../contexts/AuthContext';

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
    intro: 'Upload reference audio per task, view AI-scored musician results, and manage user accounts.',
    actions: [
      { title: 'Reference Upload', description: 'Upload reference audio and create tasks for musicians', to: '/reference-upload', cta: 'Open Upload', icon: '\U0001F3B5' },
      { title: 'Musician Results', description: 'View all musicians with their AI-generated performance scores', to: '/musician-results', cta: 'View Results', icon: '\U0001F4CA' },
      { title: 'Rankings', description: 'See the best musician per task based on AI scores', to: '/recommendations', cta: 'View Rankings', icon: '\U0001F3C6' },
      { title: 'User Management', description: 'Manage user accounts and assign roles', to: '/admin', cta: 'Open Admin Panel', icon: '\u2699\uFE0F' },
    ],
  },
  musician: {
    intro: 'Find your assigned tasks, submit your performances, and track your progress and scores.',
    actions: [
      { title: 'My Tasks', description: 'View active assignments and submit performances', to: '/assignments', cta: 'Open Tasks', icon: '\U0001F3AF' },
      { title: 'Upload Performance', description: 'Upload your recording to be scored by the AI', to: '/performances/upload', cta: 'Upload Now', icon: '\U0001F3A4' },
      { title: 'My Scores', description: 'View your evaluation history and feedback breakdown', to: '/evaluations', cta: 'View Scores', icon: '\U0001F4CA' },
      { title: 'Profile', description: 'Update your instrument, skill level, and availability', to: '/profile', cta: 'Edit Profile', icon: '\U0001F464' },
    ],
  },
};

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const journey = journeyByRole[user?.role || ''] || {
    intro: 'Welcome to the Musician Evaluation System.',
    actions: [],
  };
  const [primary, ...secondary] = journey.actions;

  return (
    <div className="min-h-screen staff-bg" style={{ backgroundColor: 'var(--bg-page)' }}>
      <AppHeader title="Musician Evaluation System" subtitle={`Welcome back, ${user?.first_name || user?.username}!`} />

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 relative">
        <div
          className="rounded-2xl p-8 mb-8 text-white relative overflow-hidden"
          style={{ background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%)' }}
        >
          <span className="text-5xl absolute right-8 top-6 opacity-20 pointer-events-none select-none">\U0001F3BC</span>
          <h2 className="text-3xl font-bold mb-2 font-display">Dashboard</h2>
          <p className="text-indigo-200 max-w-xl">{journey.intro}</p>
        </div>

        {primary ? (
          <div className="mb-8">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: 'var(--color-accent)' }}>
              \u2605 Start here
            </p>
            <Link
              to={primary.to}
              className="music-card flex items-start gap-5 bg-white rounded-2xl p-6 shadow-md border-l-4"
              style={{ borderLeftColor: 'var(--color-accent)' }}
            >
              <span className="text-4xl">{primary.icon}</span>
              <div>
                <h3 className="text-xl font-bold mb-1" style={{ color: 'var(--color-primary)' }}>
                  {primary.title}
                </h3>
                <p className="text-gray-500 mb-3">{primary.description}</p>
                <span
                  className="inline-block rounded-full px-4 py-1.5 text-sm font-semibold text-white"
                  style={{ backgroundColor: 'var(--color-accent)' }}
                >
                  {primary.cta} \u2192
                </span>
              </div>
            </Link>
          </div>
        ) : null}

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
                    <h4 className="font-semibold mb-1" style={{ color: 'var(--color-primary)' }}>
                      {action.title}
                    </h4>
                    <p className="text-sm text-gray-500 mb-2">{action.description}</p>
                    <span className="text-sm font-medium" style={{ color: 'var(--color-accent)' }}>
                      {action.cta} \u2192
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
