import React from "react";
import { useAuth } from "../contexts/AuthContext";
import { Link } from "react-router-dom";

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  const getDashboardContent = () => {
    switch (user?.role) {
      case "admin":
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">User Management</h3>
              <p className="text-gray-600 mb-4">
                Manage system users and roles
              </p>
              <Link
                to="/admin"
                className="text-indigo-600 hover:text-indigo-500"
              >
                Go to Admin Panel
              </Link>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">Evaluations</h3>
              <p className="text-gray-600 mb-4">View all evaluations</p>
              <Link
                to="/evaluations"
                className="text-indigo-600 hover:text-indigo-500"
              >
                View Evaluations
              </Link>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">Reports</h3>
              <p className="text-gray-600 mb-4">System reports and analytics</p>
              <span className="text-gray-400">Coming soon</span>
            </div>
          </div>
        );
      case "evaluator":
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">
                Pending Evaluations
              </h3>
              <p className="text-gray-600 mb-4">
                Review submitted performances
              </p>
              <Link
                to="/evaluations"
                className="text-indigo-600 hover:text-indigo-500"
              >
                Start Evaluating
              </Link>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">My Evaluations</h3>
              <p className="text-gray-600 mb-4">View your evaluation history</p>
              <span className="text-gray-400">Coming soon</span>
            </div>
          </div>
        );
      case "musician":
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">Submit Performance</h3>
              <p className="text-gray-600 mb-4">
                Upload your musical performance
              </p>
              <span className="text-gray-400">Coming soon</span>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">My Evaluations</h3>
              <p className="text-gray-600 mb-4">
                View feedback on your performances
              </p>
              <Link
                to="/evaluations"
                className="text-indigo-600 hover:text-indigo-500"
              >
                View Evaluations
              </Link>
            </div>
          </div>
        );
      default:
        return (
          <div className="text-center">
            <p>Welcome to the Musician Evaluation System!</p>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Musician Evaluation System
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">
                Welcome, {user?.first_name}!
              </span>
              <Link
                to="/profile"
                className="text-indigo-600 hover:text-indigo-500"
              >
                Profile
              </Link>
              <button
                onClick={logout}
                className="text-gray-700 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>
          {getDashboardContent()}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
